from pathlib import Path
import re

path=Path('app.py')
s=path.read_text(encoding='utf-8')

css=r'''
/* Cabeçalho CDT — alteração restrita ao topo/navegação. */
.st-key-cdt_top_header{background:linear-gradient(112deg,#075B35,#0B7A43);border-radius:13px;padding:11px 14px!important;margin:0 0 5px!important;box-shadow:0 7px 22px rgba(7,91,53,.16)}
.st-key-cdt_top_header [data-testid="stHorizontalBlock"]{align-items:center!important;gap:.45rem!important}
.cdt-brandline{font-size:.60rem;font-weight:900;letter-spacing:.10em;text-transform:uppercase;color:#BDF28B;margin-bottom:2px}
.cdt-title{font-size:1.16rem;font-weight:950;line-height:1.03;letter-spacing:-.015em;color:#fff}
.cdt-unit{font-size:.70rem;font-weight:700;color:#DCEFE4;margin-top:2px}
.cdt-session{display:flex;align-items:center;gap:6px;margin-top:7px;min-width:0;color:#EAF7EF;font-size:.68rem;font-weight:750}
.cdt-session-name{display:block;max-width:100%;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.st-key-cdt_top_header [data-testid="stPopover"]{display:flex;justify-content:flex-end}
.st-key-cdt_top_header [data-testid="stPopover"]>button{width:38px!important;min-width:38px!important;height:34px!important;min-height:34px!important;padding:0!important;border-radius:9px!important;background:rgba(255,255,255,.12)!important;border:1px solid rgba(255,255,255,.22)!important;color:#fff!important;font-size:1.25rem!important;box-shadow:none!important}
.st-key-cdt_top_header [data-testid="stPopover"]>button:hover{background:rgba(255,255,255,.20)!important}
div[data-testid="stPopoverBody"]{border-radius:11px!important}
div[data-testid="stPopoverBody"] .cdt-menu-user{font-size:.70rem;font-weight:850;color:#334155;padding:2px 2px 7px;border-bottom:1px solid #E2E8F0;margin-bottom:5px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
div[data-testid="stPopoverBody"] .stButton button{background:transparent!important;color:#334155!important;border:0!important;justify-content:flex-start!important;min-height:34px!important;padding:5px 7px!important;font-size:.72rem!important;box-shadow:none!important}
div[data-testid="stPopoverBody"] .stButton button:hover{background:#F1F5F9!important;color:#075B35!important}
.st-key-top_nav_area{margin:-1px 0 0!important}
.st-key-top_nav_area [data-testid="stSegmentedControl"]{background:transparent!important;border:0!important;padding:0!important;min-height:36px!important}
.st-key-top_nav_area [data-testid="stSegmentedControl"]>div{gap:18px!important;border:0!important;background:transparent!important;padding:0 4px!important}
.st-key-top_nav_area [data-testid="stSegmentedControl"] button{background:transparent!important;border:0!important;border-bottom:3px solid transparent!important;border-radius:0!important;color:#64748B!important;min-height:35px!important;padding:6px 5px 5px!important;font-size:.70rem!important;font-weight:850!important;box-shadow:none!important}
.st-key-top_nav_area [data-testid="stSegmentedControl"] button[aria-pressed="true"]{color:#075B35!important;border-bottom-color:#67D443!important;font-weight:950!important}
.cdt-update{font-size:.62rem;color:#64748B;font-weight:650;margin:1px 3px 5px;line-height:1.2}
@media(max-width:560px){
 .block-container{padding-top:.35rem!important}
 .st-key-cdt_top_header{padding:9px 10px!important;border-radius:11px;margin-bottom:3px!important}
 .st-key-cdt_top_header [data-testid="stHorizontalBlock"]{gap:.2rem!important}
 .cdt-brandline{font-size:.50rem;margin-bottom:1px}
 .cdt-title{font-size:.98rem}
 .cdt-unit{font-size:.61rem;margin-top:1px}
 .cdt-session{font-size:.60rem;margin-top:5px;gap:4px}
 .st-key-cdt_top_header [data-testid="stPopover"]>button{width:34px!important;min-width:34px!important;height:31px!important;min-height:31px!important;font-size:1.12rem!important}
 .st-key-top_nav_area [data-testid="stSegmentedControl"]{min-height:32px!important}
 .st-key-top_nav_area [data-testid="stSegmentedControl"]>div{gap:13px!important}
 .st-key-top_nav_area [data-testid="stSegmentedControl"] button{min-height:31px!important;font-size:.64rem!important;padding:4px 4px 4px!important}
 .cdt-update{font-size:.56rem;margin:0 2px 4px}
}
@media(max-width:340px){
 .cdt-title{font-size:.91rem}.cdt-session-name{max-width:205px}.st-key-top_nav_area [data-testid="stSegmentedControl"]>div{gap:8px!important}
}
'''
if '/* Cabeçalho CDT — alteração restrita ao topo/navegação. */' not in s:
    s=s.replace('\n</style>"""',css+'\n</style>"""',1)

old=r'''    user_name=html.escape(str(st.session_state.get("dashboard_usuario") or "Usuário autenticado"))
    auth_token=st.session_state.get("dashboard_auth_token") or incoming_token or ""
    management_href=f'?auth={html.escape(str(auth_token),quote=True)}&action=management' if auth_token else '?action=management'
    logout_href=f'?auth={html.escape(str(auth_token),quote=True)}&action=logout' if auth_token else '?action=logout'
    st.markdown(
        '<div class="bi-topbar bi-topbar-nav integrated-header">'
        '<div class="bi-brand"><h1>PAINEL COMERCIAL — AFOGADOS</h1><p>Visão executiva de produção, performance, histórico e remuneração variável</p></div>'
        f'<div class="header-account"><span class="header-user">{user_name}</span><div class="header-actions"><a href="{management_href}" target="_self">GESTÃO</a><a href="{logout_href}" target="_self">SAIR</a></div></div>'
        '</div>',unsafe_allow_html=True
    )
    if st.session_state.area=="GESTÃO":
        render_management(st,base,rows,cfg,metadata)
        return
    selected_area=st.segmented_control("Navegação",areas,default=st.session_state.area,key="top_nav_area",label_visibility="collapsed")
    if selected_area and selected_area != st.session_state.area:
        st.session_state.area=selected_area
        st.rerun()
    area=st.session_state.area
    try:summary,all_days,elapsed,official=summarize(rows,cfg); apply_team_labels(summary,cfg)
    except Exception as exc:st.error(f"Falha ao processar relatório: {exc}");return
    data_until=max((x["data_venda"] for x in rows if x["data_venda"].year==cfg["ano"] and x["data_venda"].month==cfg["mes"]),default=date(cfg["ano"],cfg["mes"],1)); updated=datetime.fromisoformat(metadata["atualizado_em"])
    st.caption(f"Última atualização: {updated:%d/%m/%Y às %H:%M}  •  Dados acumulados até: {data_until:%d/%m/%Y}  •  Competência: {cfg['mes']:02d}/{cfg['ano']}")
'''

new=r'''    user_name_raw=str(st.session_state.get("dashboard_usuario") or "Usuário autenticado")
    user_name=html.escape(user_name_raw)
    auth_token=st.session_state.get("dashboard_auth_token") or incoming_token or ""
    management_available=bool(manager_password(st))
    with st.container(key="cdt_top_header"):
        header_main,header_menu=st.columns([8.6,1.0],vertical_alignment="center")
        with header_main:
            st.markdown(
                '<div class="cdt-brandline">Cartão de TODOS</div>'
                '<div class="cdt-title">PAINEL COMERCIAL</div>'
                '<div class="cdt-unit">Afogados</div>'
                f'<div class="cdt-session"><span aria-hidden="true">👤</span><span class="cdt-session-name">{user_name}</span></div>',
                unsafe_allow_html=True
            )
        with header_menu:
            with st.popover("⋮",use_container_width=True):
                st.markdown(f'<div class="cdt-menu-user">👤 {user_name}</div>',unsafe_allow_html=True)
                if management_available and st.button("⚙ Gestão",key="cdt_menu_management",use_container_width=True):
                    st.session_state.area="GESTÃO"
                    st.rerun()
                if st.button("↪ Sair",key="cdt_menu_logout",use_container_width=True):
                    for key in ("dashboard_autenticado","dashboard_usuario","dashboard_auth_token","seller_detail","gestor_autenticado","login_duplicate_first"):
                        st.session_state.pop(key,None)
                    st.session_state.area="VISÃO GERAL"
                    st.query_params.clear()
                    st.rerun()
    if st.session_state.area=="GESTÃO":
        render_management(st,base,rows,cfg,metadata)
        return
    selected_area=st.segmented_control("Navegação",areas,default=st.session_state.area,key="top_nav_area",label_visibility="collapsed")
    if selected_area and selected_area != st.session_state.area:
        st.session_state.area=selected_area
        st.rerun()
    area=st.session_state.area
    try:summary,all_days,elapsed,official=summarize(rows,cfg); apply_team_labels(summary,cfg)
    except Exception as exc:st.error(f"Falha ao processar relatório: {exc}");return
    data_until=max((x["data_venda"] for x in rows if x["data_venda"].year==cfg["ano"] and x["data_venda"].month==cfg["mes"]),default=date(cfg["ano"],cfg["mes"],1)); updated=datetime.fromisoformat(metadata["atualizado_em"])
    month_names=("Janeiro","Fevereiro","Março","Abril","Maio","Junho","Julho","Agosto","Setembro","Outubro","Novembro","Dezembro")
    today=date.today()
    update_text=f"Atualizado hoje, {updated:%H:%M}" if updated.date()==today else f"Atualizado {updated:%d/%m}, {updated:%H:%M}"
    if data_until!=updated.date():update_text+=f" • Dados até {data_until:%d/%m}"
    update_text+=f" • {month_names[int(cfg['mes'])-1]}/{cfg['ano']}"
    st.markdown(f'<div class="cdt-update">{html.escape(update_text)}</div>',unsafe_allow_html=True)
'''
if old not in s:
    raise SystemExit('Bloco atual de cabeçalho/navegação não localizado')
s=s.replace(old,new,1)
path.write_text(s,encoding='utf-8')
