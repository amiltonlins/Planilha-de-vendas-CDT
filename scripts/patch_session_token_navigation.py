from pathlib import Path
import re

p=Path('app.py')
s=p.read_text(encoding='utf-8')

# Token assinado apenas para transportar a sessão já autenticada entre navegações internas por link.
s=s.replace('import copy, csv, hmac, html, io, json, os, re, tempfile, unicodedata, zipfile','import base64, copy, csv, hmac, html, io, json, os, re, tempfile, time, unicodedata, zipfile',1)

marker='def validate_xlsx_bytes(data,required_sheet=None):\n'
helpers='''def auth_signing_key(st):\n    try:\n        key=str(st.secrets.get("DASHBOARD_AUTH_KEY","") or st.secrets.get("GESTOR_SENHA",""))\n    except Exception:\n        key=os.environ.get("DASHBOARD_AUTH_KEY","") or os.environ.get("GESTOR_SENHA","")\n    return key\n\ndef issue_dashboard_token(st,user):\n    key=auth_signing_key(st)\n    if not key:return ""\n    expiry=int(time.time())+12*60*60\n    payload=f"{user}|{expiry}"\n    sig=hmac.new(key.encode("utf-8"),payload.encode("utf-8"),"sha256").hexdigest()\n    raw=f"{payload}|{sig}".encode("utf-8")\n    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")\n\ndef validate_dashboard_token(st,cfg,token):\n    key=auth_signing_key(st)\n    if not key or not token:return None\n    try:\n        padded=str(token)+"="*((4-len(str(token))%4)%4)\n        raw=base64.urlsafe_b64decode(padded.encode("ascii")).decode("utf-8")\n        user,expiry_text,sig=raw.rsplit("|",2)\n        if int(expiry_text)<int(time.time()):return None\n        payload=f"{user}|{expiry_text}"\n        expected=hmac.new(key.encode("utf-8"),payload.encode("utf-8"),"sha256").hexdigest()\n        if not hmac.compare_digest(sig,expected):return None\n        allowed={normalize_text(x["display"]) for x in authorized_dashboard_users(cfg).values()}\n        return user if normalize_text(user) in allowed else None\n    except Exception:\n        return None\n\n'''
if 'def issue_dashboard_token(' not in s:
    if marker not in s:raise SystemExit('validate_xlsx_bytes não encontrado')
    s=s.replace(marker,helpers+marker,1)

# Login emite token assinado e mantém usuário real na sessão.
old='''        if status=="ok":\n            st.session_state.dashboard_autenticado=True\n            st.session_state.dashboard_usuario=display\n            st.rerun()'''
new='''        if status=="ok":\n            st.session_state.dashboard_autenticado=True\n            st.session_state.dashboard_usuario=display\n            token=issue_dashboard_token(st,display)\n            if token:\n                st.session_state.dashboard_auth_token=token\n                st.query_params["auth"]=token\n            st.rerun()'''
if old not in s:raise SystemExit('sucesso do login não encontrado')
s=s.replace(old,new,1)

# Ranking recebe token e inclui-o nos links internos, evitando nova autenticação após navegação.
s=s.replace('def ranking_html(ranking):','def ranking_html(ranking,auth_token=""):',1)
old='''            f'<a class="rank-click" href="?seller={html.escape(str(x["vendedor"]),quote=True)}" target="_self">' '''
new='''            f'<a class="rank-click" href="?{("auth="+html.escape(str(auth_token),quote=True)+"&") if auth_token else ""}seller={html.escape(str(x["vendedor"]),quote=True)}" target="_self">' '''
if old not in s:raise SystemExit('link do ranking não encontrado')
s=s.replace(old,new,1)

# Restaura sessão válida antes do gate de autenticação.
old='''    try:rows,cfg,metadata=load_published(base)\n    except Exception as exc:st.error(f"A base publicada não pôde ser carregada: {exc}");return\n    if not st.session_state.get("dashboard_autenticado",False):\n        render_login(st,cfg)\n        return\n'''
new='''    try:rows,cfg,metadata=load_published(base)\n    except Exception as exc:st.error(f"A base publicada não pôde ser carregada: {exc}");return\n    incoming_token=st.query_params.get("auth")\n    if not st.session_state.get("dashboard_autenticado",False) and incoming_token:\n        restored_user=validate_dashboard_token(st,cfg,incoming_token)\n        if restored_user:\n            st.session_state.dashboard_autenticado=True\n            st.session_state.dashboard_usuario=restored_user\n            st.session_state.dashboard_auth_token=incoming_token\n    if not st.session_state.get("dashboard_autenticado",False):\n        render_login(st,cfg)\n        return\n'''
if old not in s:raise SystemExit('gate de autenticação não encontrado')
s=s.replace(old,new,1)

# Logout limpa também o token; Gestão mantém o token no link interno.
s=s.replace('("dashboard_autenticado","dashboard_usuario","seller_detail","gestor_autenticado","login_duplicate_first")','("dashboard_autenticado","dashboard_usuario","dashboard_auth_token","seller_detail","gestor_autenticado","login_duplicate_first")',1)
old='''    user_name=html.escape(str(st.session_state.get("dashboard_usuario") or "Usuário autenticado"))\n    st.markdown(\n        '<div class="bi-topbar bi-topbar-nav integrated-header">'\n        '<div class="bi-brand"><h1>PAINEL COMERCIAL — AFOGADOS</h1><p>Visão executiva de produção, performance, histórico e remuneração variável</p></div>'\n        f'<div class="header-account"><span class="header-user">{user_name}</span><div class="header-actions"><a href="?action=management" target="_self">GESTÃO</a><a href="?action=logout" target="_self">SAIR</a></div></div>'\n        '</div>',unsafe_allow_html=True\n    )'''
new='''    user_name=html.escape(str(st.session_state.get("dashboard_usuario") or "Usuário autenticado"))\n    auth_token=st.session_state.get("dashboard_auth_token") or incoming_token or ""\n    management_href=f'?auth={html.escape(str(auth_token),quote=True)}&action=management' if auth_token else '?action=management'\n    st.markdown(\n        '<div class="bi-topbar bi-topbar-nav integrated-header">'\n        '<div class="bi-brand"><h1>PAINEL COMERCIAL — AFOGADOS</h1><p>Visão executiva de produção, performance, histórico e remuneração variável</p></div>'\n        f'<div class="header-account"><span class="header-user">{user_name}</span><div class="header-actions"><a href="{management_href}" target="_self">GESTÃO</a><a href="?action=logout" target="_self">SAIR</a></div></div>'\n        '</div>',unsafe_allow_html=True\n    )'''
if old not in s:raise SystemExit('header integrado não encontrado')
s=s.replace(old,new,1)

s=s.replace('st.markdown(ranking_html(ranking),unsafe_allow_html=True)','st.markdown(ranking_html(ranking,auth_token),unsafe_allow_html=True)',1)

p.write_text(s,encoding='utf-8')
