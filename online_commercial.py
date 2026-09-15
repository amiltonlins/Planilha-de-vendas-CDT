#!/usr/bin/env python3
"""Sincroniza o Painel Comercial com a aba VENDAS e instala ajustes de acesso/UI."""
from __future__ import annotations
import base64,hmac,inspect,os,re,time
from datetime import timedelta
from urllib.request import Request,urlopen
import streamlit as st
DEFAULT_SHEET_ID="14uhlJmDA3UeTZb7sZ3zu-Fovr8utzQbFcpU8LEbuKXE"; DEFAULT_GID="56831808"; SOURCE_NAME="google_sheets_vendas.csv"; SELECTOR_VERSION="2026-09-12-commercial-dates-v4"
ACCESS_CODE=os.environ.get("PAINEL_ACCESS_CODE","resultados"); ACCESS_SESSION_USER="Painel de Resultados"; ACCESS_SESSION_VERSION="results-code-v2-20260915"; ACCESS_LOGO_URL="https://share.google/eNhOIxBCCPNSKbiUE"; AUTO_REFRESH_SECONDS=60

def _download_csv(sheet_id,gid):
    url=f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}&_={time.time_ns()}"; request=Request(url,headers={"User-Agent":"Mozilla/5.0","Cache-Control":"no-cache, no-store, max-age=0","Pragma":"no-cache"})
    with urlopen(request,timeout=20) as response:data=response.read(); content_type=str(response.headers.get("Content-Type","")).lower()
    if not data:raise RuntimeError("A planilha online retornou um arquivo vazio.")
    if "text/html" in content_type or b"<html" in data[:800].lower() or b"accounts.google.com" in data[:800].lower():raise RuntimeError("A aba VENDAS não está acessível para leitura anônima.")
    return data

def _signature(rows,days):
    day_set=set(days); return sorted((row.get("data_venda").isoformat() if hasattr(row.get("data_venda"),"isoformat") else str(row.get("data_venda","")),str(row.get("id_venda","")),str(row.get("vendedor","")),str(row.get("neoenergia",""))) for row in rows if row.get("data_venda") in day_set)

def _prepare_online_rows(core,base):
    raw=core.rows_from_csv(_download_csv(os.environ.get("PAINEL_GOOGLE_SHEET_ID",DEFAULT_SHEET_ID).strip(),os.environ.get("PAINEL_GOOGLE_SHEET_GID",DEFAULT_GID).strip()))
    if not raw:raise RuntimeError("A aba VENDAS não possui registros para sincronizar.")
    col=core.detect_columns(raw[0].keys()).get("data_venda"); today=core.datetime.now(core.RECIFE_TZ).date().isoformat(); inferred=0
    if col:
        for row in raw:
            value=str(row.get(col,"") or "").strip()
            if not value or ("#" in value and value.replace("#","").strip()==""):row[col]=today; inferred+=1
    incoming,_=core.canonicalize(raw,base); return incoming,inferred

def _full_week_ranges(core,year,month):
    out=[]
    for start,_ in core.month_weeks(int(year),int(month)):
        monday=start-timedelta(days=start.weekday()); out.append((monday,monday+timedelta(days=6)))
    return out

def _install_daily_current_date(core):
    if getattr(core,"_daily_current_date_runtime_installed",False):return
    original=core.daily_ranking_rows
    def current(team,rows,cfg,reference_day=None):
        day=reference_day or core.datetime.now(core.RECIFE_TZ).date(); effective=dict(cfg)
        if day.year==int(cfg["ano"]) and day.month==int(cfg["mes"]):effective["dia_referencia"]=day.day
        return original(team,rows,effective,day)
    core.daily_ranking_rows=current; core._daily_current_date_runtime_installed=True

def _install_weekly_commercial_behavior(core):
    if not getattr(core,"_weekly_complete_runtime_installed",False):
        original=core.summarize
        def summarize(rows,cfg):
            result,calendar,elapsed,official=original(rows,cfg); weeks=_full_week_ranges(core,cfg["ano"],cfg["mes"]); awards=list(cfg.get("premiacao_semanal",[]) or []); by={}
            for row in rows:
                key=core.normalize_text(row.get("vendedor",""))
                if key:by.setdefault(key,[]).append(row)
            for item in result:
                sr=by.get(core.normalize_text(item.get("vendedor","")),[]); sales=[sum(a<=r.get("data_venda")<=b for r in sr) for a,b in weeks]; item["semanas"]=sales
                item["premios"]=[([float(x.get("premio",0) or 0) for x in awards if q>=int(x.get("vendas",0) or 0)] or [0])[-1] if item.get("elegivel_individual",False) else 0 for q in sales]
            return result,calendar,elapsed,official
        core.summarize=summarize; core._weekly_complete_runtime_installed=True
    if not getattr(core,"_weekly_download_complete_period_installed",False):
        original_png=core.weekly_prize_ranking_png
        def png(team,index,cfg):
            original_weeks=core.month_weeks
            def complete(year,month):return [(s-timedelta(days=s.weekday()),s-timedelta(days=s.weekday())+timedelta(days=6)) for s,_ in original_weeks(int(year),int(month))]
            core.month_weeks=complete
            try:return original_png(team,index,cfg)
            finally:core.month_weeks=original_weeks
        core.weekly_prize_ranking_png=png; core._weekly_download_complete_period_installed=True
    if getattr(st,"_commercial_week_dates_selector_version",None)==SELECTOR_VERSION:return
    original_button=st.button
    def button(label,*args,**kwargs):
        match=re.fullmatch(r"week_btn_(\d+)",str(kwargs.get("key") or ""))
        if not match:return original_button(label,*args,**kwargs)
        caller=inspect.currentframe().f_back; cfg=caller.f_locals.get("cfg") if caller else None; period=None; index=int(match.group(1))
        if isinstance(cfg,dict):
            try:ranges=core.month_weeks(int(cfg["ano"]),int(cfg["mes"])); period=ranges[index] if index<len(ranges) else None
            except Exception:pass
        st.markdown('<style>.week-period-caption{display:none!important}</style>',unsafe_allow_html=True); return original_button(f"{period[0].day:02d}–{period[1].day:02d}" if period else str(label),*args,**kwargs)
    st.button=button; st._commercial_week_dates_selector_version=SELECTOR_VERSION

def _install_refresh_button():
    if getattr(st,"_cdt_commercial_refresh_installed",False):return
    original=st.columns; target=[2.15,2.05,1.15,4.65]
    def columns(spec,*args,**kwargs):
        caller=inspect.currentframe().f_back
        if not (isinstance(spec,(list,tuple)) and list(spec)==target and caller and caller.f_code.co_name=="render_app" and str(caller.f_code.co_filename).endswith("app_core.py")):return original(spec,*args,**kwargs)
        cols=original([2.15,2.05,1.25,1.15,3.40],*args,**kwargs)
        with cols[2]:
            if st.button("↻ Atualizar dados",key="commercial_refresh",help="Consultar novamente os resultados da planilha"):st.session_state["commercial_force_refresh"]=True; st.rerun()
        return cols[0],cols[1],cols[3],cols[4]
    st.columns=columns; st._cdt_commercial_refresh_installed=True

def _install_auto_refresh():
    if not st.session_state.get("dashboard_autenticado",False):return
    try:
        import streamlit.components.v1 as components; components.html(f'<script>setTimeout(function(){{try{{window.parent.location.reload();}}catch(e){{window.location.reload();}}}},{AUTO_REFRESH_SECONDS*1000});</script>',height=0)
    except Exception:pass

def _normalize_access_code(value):return str(value or "").strip().casefold()

def _install_access_code_login(core):
    if getattr(core,"_results_access_code_login_installed",False):return
    def validate(st_module,cfg,token):
        key=core.auth_signing_key(st_module)
        if not key or not token:return None
        try:
            padded=str(token)+"="*((4-len(str(token))%4)%4); user,expiry,sig=base64.urlsafe_b64decode(padded.encode()).decode().rsplit("|",2)
            if user!=ACCESS_SESSION_USER or int(expiry)<int(time.time()):return None
            expected=hmac.new(key.encode(),f"{user}|{expiry}".encode(),"sha256").hexdigest(); return user if hmac.compare_digest(sig,expected) else None
        except Exception:return None
    def render_login(st_module,cfg):
        busy=bool(st_module.session_state.get("results_access_busy",False)); error=st_module.session_state.pop("results_access_error","")
        st_module.markdown(f'''<style>
[data-testid="stAppViewContainer"]{{background:#F8FAFC!important}}
.results-login-wrap{{display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;margin:0 0 12px;padding:0 14px}}
.results-login-logo{{display:block;width:min(220px,52vw);max-height:82px;object-fit:contain;margin:0 auto 14px}}
.results-login-title{{font-size:1.28rem;font-weight:950;color:#0F172A;line-height:1.1}}
.results-login-subtitle{{margin-top:5px;font-size:.78rem;font-weight:650;color:#64748B}}
.st-key-results_access_form{{width:min(360px,92vw)!important;margin:0 auto!important}}
.st-key-results_access_form [data-testid="stForm"]{{border:0!important;background:transparent!important;padding:0!important}}
.st-key-results_access_form label p{{font-size:.70rem!important;font-weight:850!important;color:#334155!important}}
.st-key-results_access_form input{{height:43px!important;border-radius:9px!important;border:1px solid #CBD5E1!important;background:#fff!important;text-align:center!important;font-size:.95rem!important}}
.st-key-results_access_form button{{height:41px!important;border-radius:9px!important;background:#075B35!important;color:#fff!important;border:1px solid #075B35!important;font-size:.74rem!important;font-weight:950!important}}
.results-access-error{{width:min(360px,92vw);margin:7px auto 0;text-align:center;color:#B91C1C;font-size:.69rem;font-weight:800}}
@media(max-width:700px){{.results-login-logo{{width:min(190px,55vw);max-height:70px}}.results-login-title{{font-size:1.12rem}}}}
</style><div class="results-login-wrap"><img class="results-login-logo" src="{ACCESS_LOGO_URL}" alt="Cartão de TODOS"><div class="results-login-title">PAINEL DE RESULTADOS</div><div class="results-login-subtitle">Recife Afogados</div></div>''',unsafe_allow_html=True)
        with st_module.container(key="results_access_form"):
            with st_module.form("dashboard_login_code",clear_on_submit=False,enter_to_submit=True):
                code=st_module.text_input("Código de acesso",type="password",key="results_access_code",autocomplete="off",placeholder="",disabled=busy); submitted=st_module.form_submit_button("ACESSAR",use_container_width=True,disabled=busy)
        if error:st_module.markdown(f'<div class="results-access-error">{error}</div>',unsafe_allow_html=True)
        if not submitted:return
        normalized=_normalize_access_code(code)
        if not normalized:st_module.session_state["results_access_error"]="Informe o código de acesso."; st_module.rerun()
        if not hmac.compare_digest(normalized,_normalize_access_code(ACCESS_CODE)):st_module.session_state["results_access_error"]="Código de acesso inválido."; st_module.session_state["results_access_code"]=""; st_module.rerun()
        st_module.session_state.dashboard_autenticado=True; st_module.session_state.dashboard_usuario=ACCESS_SESSION_USER; st_module.session_state["dashboard_access_version"]=ACCESS_SESSION_VERSION
        token=core.issue_dashboard_token(st_module,ACCESS_SESSION_USER)
        if token:st_module.session_state.dashboard_auth_token=token; st_module.query_params["auth"]=token
        st_module.rerun()
    core.validate_dashboard_token=validate; core.render_login=render_login; core._results_access_code_login_installed=True

def _invalidate_legacy_session():
    if st.session_state.get("dashboard_access_version")==ACCESS_SESSION_VERSION:return
    if st.session_state.get("dashboard_autenticado",False):
        for key in ("dashboard_autenticado","dashboard_usuario","dashboard_auth_token","gestor_autenticado"):st.session_state.pop(key,None)
        try:
            if "auth" in st.query_params:del st.query_params["auth"]
        except Exception:pass
    st.session_state["dashboard_access_version"]=ACCESS_SESSION_VERSION

def install(core):
    original=core.load_published; _install_access_code_login(core); _invalidate_legacy_session(); _install_daily_current_date(core); _install_weekly_commercial_behavior(core); _install_refresh_button()
    def load(base):
        rows,cfg,metadata=original(base); metadata=dict(metadata or {}); force=bool(st.session_state.pop("commercial_force_refresh",False))
        try:
            incoming,inferred=_prepare_online_rows(core,base); days=sorted({r["data_venda"] for r in incoming}); before=_signature(rows,days); merged,days=core.merge_daily_history(rows,incoming); after=_signature(merged,days)
            if days:
                latest=max(days); cfg=core.prepare_config(core.merge_registry(base,cfg),merged,latest.month,latest.year)
            now=core.datetime.now(core.RECIFE_TZ); metadata.update({"arquivo":SOURCE_NAME,"fonte_online":"Google Sheets · VENDAS","fonte_online_status":"ok","fonte_online_datas_inferidas":inferred})
            if before!=after or force:core.save_published(merged,cfg,SOURCE_NAME,metadata.get("historico_importacoes",[]),updated_at=now); metadata["atualizado_em"]=now.isoformat(timespec="seconds")
            return merged,cfg,metadata
        except Exception as exc:
            metadata.update({"fonte_online":"Google Sheets · VENDAS","fonte_online_status":"fallback","fonte_online_erro":str(exc)})
            if force:st.warning("Não foi possível atualizar. Última leitura válida mantida, quando disponível.")
            return rows,cfg,metadata
    core.load_published=load; _install_auto_refresh()
