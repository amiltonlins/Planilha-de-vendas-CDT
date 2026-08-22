from pathlib import Path
import re

p=Path('app.py')
s=p.read_text(encoding='utf-8')

# 1) Autenticação: primeiro + segundo nome, com aliases conhecidos.
pattern=re.compile(r'FIXED_DASHBOARD_USERS=.*?def validate_xlsx_bytes',re.S)
replacement='''FIXED_DASHBOARD_USERS={
    "Amilton Lins":("amilton lins","hamilton lins"),
    "Sheyla Santos":("sheyla santos","sheila santos"),
    "Joice Larissa":("joice larissa","joyce larissa"),
    "Rafael Salgado":("rafael salgado","raphael salgado"),
}

def first_name(value):
    return str(value or "").strip().split()[0] if str(value or "").strip() else ""

def first_two_names(value):
    parts=str(value or "").strip().split()
    return " ".join(parts[:2]) if len(parts)>=2 else ""

def authorized_dashboard_users(cfg):
    identities={}
    for display,aliases in FIXED_DASHBOARD_USERS.items():
        for alias in aliases:
            identities[normalize_text(alias)]={"display":display,"full":display,"fixed":True}
    for seller in cfg.get("vendedores",[]):
        if not seller.get("ativo",False):continue
        full=str(seller.get("vendedor","")).strip()
        key=normalize_text(first_two_names(full))
        if not key:continue
        identities.setdefault(key,{"display":first_two_names(full),"full":full,"fixed":False})
    return identities

def authenticate_dashboard_name(cfg,provided_first,provided_full=""):
    candidate=(provided_full or provided_first or "").strip()
    key=normalize_text(first_two_names(candidate))
    if not key:return None,"invalid"
    selected=authorized_dashboard_users(cfg).get(key)
    return (selected["display"],"ok") if selected else (None,"invalid")

def is_mobile_client(st):
    try:
        ua=str(st.context.headers.get("User-Agent","")).lower()
    except Exception:
        return False
    return any(token in ua for token in ("iphone","ipad","ipod","android","mobile"))

def validate_xlsx_bytes'''
s,n=pattern.subn(replacement,s,count=1)
if n!=1:raise SystemExit('bloco de autenticação não encontrado')

# 2) Login visual: um único campo pedindo primeiro e segundo nome.
old='''    st.markdown('<div class="login-shell"><div class="login-card"><div class="login-brand">PAINEL COMERCIAL — AFOGADOS</div><div class="login-title">Acesso ao painel</div><div class="login-sub">Informe seu primeiro nome para continuar.</div></div></div>',unsafe_allow_html=True)
    duplicate=st.session_state.get("login_duplicate_first","")
    with st.form("dashboard_login",clear_on_submit=False):
        first=st.text_input("Primeiro nome",value=duplicate or "",placeholder="Digite seu primeiro nome")
        full=st.text_input("Nome completo",placeholder="Digite seu nome completo",help="Solicitado somente quando existe mais de uma pessoa ativa com o mesmo primeiro nome") if duplicate else ""
        submitted=st.form_submit_button("ENTRAR",use_container_width=True)
    if submitted:
        display,status=authenticate_dashboard_name(cfg,first,full)
        if status=="duplicate":
            st.session_state.login_duplicate_first=first.strip()
            st.rerun()
        elif status=="ok":
            st.session_state.dashboard_autenticado=True
            st.session_state.dashboard_usuario=display
            st.session_state.pop("login_duplicate_first",None)
            st.rerun()
        else:
            st.error("Usuário não autorizado.")
'''
new='''    st.markdown('<div class="login-shell"><div class="login-card"><div class="login-brand">PAINEL COMERCIAL — AFOGADOS</div><div class="login-title">Acesso ao painel</div><div class="login-sub">Informe seu primeiro e segundo nome para continuar.</div></div></div>',unsafe_allow_html=True)
    with st.form("dashboard_login",clear_on_submit=False):
        name=st.text_input("Primeiro e segundo nome",placeholder="Ex.: Magda Alexandra")
        submitted=st.form_submit_button("ENTRAR",use_container_width=True)
    if submitted:
        display,status=authenticate_dashboard_name(cfg,name)
        if status=="ok":
            st.session_state.dashboard_autenticado=True
            st.session_state.dashboard_usuario=display
            st.rerun()
        else:
            st.error("Usuário não autorizado. Informe o primeiro e o segundo nome cadastrados.")
'''
if old not in s:raise SystemExit('render_login atual não encontrado')
s=s.replace(old,new,1)

# 3) No mobile, não exige autenticação do dashboard. Gestão continua protegida pela senha própria.
old='''    if not st.session_state.get("dashboard_autenticado",False):
        render_login(st,cfg)
        return
'''
new='''    mobile_client=is_mobile_client(st)
    if not mobile_client and not st.session_state.get("dashboard_autenticado",False):
        render_login(st,cfg)
        return
    if mobile_client and not st.session_state.get("dashboard_usuario"):
        st.session_state.dashboard_usuario="Acesso mobile"
'''
if old not in s:raise SystemExit('gate de autenticação do dashboard não encontrado')
s=s.replace(old,new,1)

# 4) Dialog: remove cartão duplicado de cabeçalho e deixa somente linha compacta de contexto.
old='''        status,c,_=performance(x["media"])
        st.markdown(f'<div class="bi-panel" style="border-left:5px solid {c}"><b>{html.escape(x["vendedor"])}</b><br><span style="color:#64748B;font-size:.75rem">{html.escape(x["setor"])} · Performance {status}</span></div>',unsafe_allow_html=True)
        st.markdown(seller_kpis_html(x),unsafe_allow_html=True)
'''
new='''        status,c,_=performance(x["media"])
        st.markdown(f'<div class="seller-dialog-meta" style="--seller-color:{c}"><span>{html.escape(x["setor"])}</span><b>Performance {status}</b></div>',unsafe_allow_html=True)
        st.markdown(seller_kpis_html(x),unsafe_allow_html=True)
'''
if old not in s:raise SystemExit('cabeçalho do dialog não encontrado')
s=s.replace(old,new,1)

# 5) CSS compacto específico para o popup mobile.
css='''
.seller-dialog-meta{display:flex;align-items:center;justify-content:space-between;gap:8px;margin:-4px 0 8px;padding:7px 10px;border-radius:9px;background:#F8FAFC;border-left:4px solid var(--seller-color);font-size:.72rem;color:#64748B}.seller-dialog-meta b{color:#334155;font-size:.7rem}
@media(max-width:560px){
[data-testid="stDialog"] [role="dialog"]{width:calc(100vw - 12px)!important;max-width:calc(100vw - 12px)!important;max-height:94dvh!important;margin:3dvh auto!important;overflow:hidden!important}
[data-testid="stDialog"] [role="dialog"]>div{max-height:94dvh!important;overflow-y:auto!important;padding:.65rem .65rem .8rem!important}
[data-testid="stDialog"] h2{font-size:1.1rem!important;line-height:1.1!important;margin:0 0 .3rem!important}
[data-testid="stDialog"] .seller-dialog-meta{margin:-2px 0 6px;padding:5px 8px;font-size:.62rem}.seller-dialog-meta b{font-size:.62rem}
[data-testid="stDialog"] .seller-mobile-primary{display:grid!important;grid-template-columns:repeat(2,minmax(0,1fr))!important;gap:6px!important;margin:0 0 7px!important}
[data-testid="stDialog"] .seller-mobile-primary .seller-kpi{min-height:70px!important;padding:8px!important;border-radius:10px!important}
[data-testid="stDialog"] .seller-mobile-primary .seller-kpi strong{font-size:1.18rem!important;margin-top:4px!important}
[data-testid="stDialog"] .seller-mobile-primary .seller-kpi small{font-size:.53rem!important;line-height:1.05!important}
[data-testid="stDialog"] .seller-mobile-primary .seller-kpi span{font-size:.54rem!important;margin-top:3px!important}
[data-testid="stDialog"] .seller-groups{margin-top:4px!important}
[data-testid="stDialog"] .seller-group-title{font-size:.61rem!important;margin:7px 0 4px!important;letter-spacing:.05em!important}
[data-testid="stDialog"] .seller-group-title.award{margin-top:8px!important}
[data-testid="stDialog"] .seller-kpi-grid{grid-template-columns:repeat(3,minmax(0,1fr))!important;gap:5px!important}
[data-testid="stDialog"] .seller-kpi-grid .seller-kpi{min-height:52px!important;padding:6px 5px!important;border-radius:9px!important}
[data-testid="stDialog"] .seller-kpi-grid .seller-kpi strong{font-size:.86rem!important;margin-top:3px!important;white-space:normal!important;line-height:1.05!important}
[data-testid="stDialog"] .seller-kpi-grid .seller-kpi small{font-size:.47rem!important;line-height:1.05!important;letter-spacing:.015em!important}
[data-testid="stDialog"] .seller-kpi-grid .seller-kpi span{display:none!important}
[data-testid="stDialog"] .mobile-duplicate{display:none!important}
[data-testid="stDialog"] .stButton{display:none!important}
}
'''
if '.seller-dialog-meta{' not in s:s=s.replace('</style>',css+'\n</style>',1)

p.write_text(s,encoding='utf-8')
