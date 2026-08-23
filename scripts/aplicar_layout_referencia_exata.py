from pathlib import Path

path=Path('app.py')
s=path.read_text(encoding='utf-8')

old='''    # Cabeçalho visual compacto: somente identidade e unidade.
    with st.container(key="cdt_top_header"):
        header_left,header_right=st.columns([7.8,2.2],vertical_alignment="center")
        with header_left:
            st.markdown('<div class="cdt-brandline">CARTÃO DE TODOS</div><div class="cdt-title">PAINEL COMERCIAL</div>',unsafe_allow_html=True)
        with header_right:
            st.markdown('<div class="cdt-unit-emphasis">AFOGADOS</div>',unsafe_allow_html=True)

    if st.session_state.area=="GESTÃO":
        render_management(st,base,rows,cfg,metadata)
        return

    # Uma única faixa compacta reúne abas, atualização, competência, semanas e conta.
    max_top_weeks=max(1,len(month_weeks(int(cfg["ano"]),int(cfg["mes"]))))
    current_top_week=weekly_current_index(cfg,max_top_weeks)
    week_labels=weekly_week_labels(cfg,max_top_weeks,current_top_week)
    weekly_state_key=f'weekly_top_selector_{cfg["ano"]}_{cfg["mes"]}_{current_top_week}'
    remembered_week=st.session_state.get("weekly_selected_label")
    default_week=remembered_week if remembered_week in week_labels else week_labels[current_top_week]

    with st.container(key="compact_top_strip"):
        nav_col,update_col,month_col,weeks_col,account_col=st.columns([2.0,2.2,1.2,3.7,.9],vertical_alignment="center")
        with nav_col:
            selected_area=st.segmented_control("Navegação",areas,default=st.session_state.area,key="top_nav_area",label_visibility="collapsed")
        with update_col:
            st.markdown(f'<div class="compact-top-text">{html.escape(update_text)}</div>',unsafe_allow_html=True)
        with month_col:
            st.markdown(f'<div class="compact-top-month">{html.escape(competence_text)}</div>',unsafe_allow_html=True)
        with weeks_col:
            selected_week=st.segmented_control("Semanas",week_labels,default=default_week,key=weekly_state_key,label_visibility="collapsed") or default_week
            st.session_state["weekly_selected_label"]=selected_week
        with account_col:
            with st.popover("Conta",use_container_width=True):
                st.caption(user_name_raw)
                if management_available and st.button("Gestão",key="cdt_menu_management",use_container_width=True):
                    st.session_state.area="GESTÃO"
                    st.rerun()
                if st.button("Sair",key="cdt_menu_logout",use_container_width=True):
                    for key in ("dashboard_autenticado","dashboard_usuario","dashboard_auth_token","seller_detail","gestor_autenticado","login_duplicate_first"):
                        st.session_state.pop(key,None)
                    st.session_state.area="VISÃO GERAL"
                    st.query_params.clear()
                    st.rerun()
'''

new='''    # Topo unificado conforme a referência visual, sem alterar dados ou regras.
    max_top_weeks=max(1,len(month_weeks(int(cfg["ano"]),int(cfg["mes"]))))
    current_top_week=weekly_current_index(cfg,max_top_weeks)
    week_labels=weekly_week_labels(cfg,max_top_weeks,current_top_week)
    weekly_state_key=f'weekly_top_selector_{cfg["ano"]}_{cfg["mes"]}_{current_top_week}'
    remembered_week=st.session_state.get("weekly_selected_label")
    default_week=remembered_week if remembered_week in week_labels else week_labels[current_top_week]

    with st.container(key="cdt_top_header"):
        header_left,header_account=st.columns([7.7,2.3],vertical_alignment="top")
        with header_left:
            st.markdown(
                '<div class="cdt-brandline">CARTÃO DE TODOS</div>'
                '<div class="cdt-title">PAINEL COMERCIAL</div>'
                '<div class="cdt-unit-emphasis">AFOGADOS</div>',
                unsafe_allow_html=True
            )
        with header_account:
            account_label=f"◉ {user_name_raw} ⌄"
            with st.popover(account_label,use_container_width=True):
                st.caption(user_name_raw)
                if management_available and st.button("Gestão",key="cdt_menu_management",use_container_width=True):
                    st.session_state.area="GESTÃO"
                    st.rerun()
                if st.button("Sair",key="cdt_menu_logout",use_container_width=True):
                    for key in ("dashboard_autenticado","dashboard_usuario","dashboard_auth_token","seller_detail","gestor_autenticado","login_duplicate_first"):
                        st.session_state.pop(key,None)
                    st.session_state.area="VISÃO GERAL"
                    st.query_params.clear()
                    st.rerun()

        if st.session_state.area!="GESTÃO":
            with st.container(key="header_control_strip"):
                nav_col,update_col,month_col,weeks_col=st.columns([2.35,2.45,1.55,3.65],vertical_alignment="center")
                with nav_col:
                    selected_area=st.segmented_control("Navegação",areas,default=st.session_state.area,key="top_nav_area",label_visibility="collapsed")
                with update_col:
                    st.markdown(f'<div class="header-meta header-update"><span class="header-meta-icon">◷</span>{html.escape(update_text)}</div>',unsafe_allow_html=True)
                with month_col:
                    st.markdown(f'<div class="header-meta header-month"><span class="header-meta-icon">▦</span>{html.escape(competence_text)}</div>',unsafe_allow_html=True)
                with weeks_col:
                    selected_week=st.segmented_control("Semanas",week_labels,default=default_week,key=weekly_state_key,label_visibility="collapsed") or default_week
                    st.session_state["weekly_selected_label"]=selected_week
        else:
            selected_area="GESTÃO"
            selected_week=default_week

    if st.session_state.area=="GESTÃO":
        render_management(st,base,rows,cfg,metadata)
        return
'''

if old not in s:
    raise SystemExit('Bloco atual do topo não encontrado; patch abortado com segurança.')
s=s.replace(old,new,1)

# Textos visuais dos três cards, preservando integralmente os valores/calculos.
s=s.replace('<div class="exec-compact-title">DESEMPENHO DE VENDAS</div>\n        \'<div class="exec-performance-values">\'\n        f\'<div class="exec-main-value"><small>VENDAS</small><strong>{total}</strong></div>\'',
            '<div class="exec-compact-title">DESEMPENHO DE VENDAS</div>\n        \'<div class="exec-performance-values">\'\n        f\'<div class="exec-main-value"><small>REALIZADAS</small><strong>{total}</strong></div>\'',1)
s=s.replace('f\'<div><small>% META</small><strong>{pct(ating)}</strong></div>\'', 'f\'<div><small>% DA META</small><strong>{pct(ating)}</strong></div>\'',1)
s=s.replace('<div class="exec-compact-title">META</div>', '<div class="exec-compact-title">METAS DO MÊS</div>',1)
s=s.replace('<div class="exec-compact-title">ENERGIA / NEO</div>', '<div class="exec-compact-title">NEOENERGIA</div>',1)
s=s.replace('f\'<div><small>VENDAS NEO</small><strong>{neo}</strong></div>\'', 'f\'<div><small>VENDAS</small><strong>{neo}</strong></div>\'',1)

css='''

/* REFERÊNCIA VISUAL 22/08/2026 — somente layout/CSS do topo e KPIs. */
.st-key-cdt_top_header{
  background:linear-gradient(135deg,#075B35 0%,#08763F 68%,#0A7E43 100%)!important;
  border:1px solid rgba(5,96,55,.35)!important;
  border-radius:28px!important;
  padding:28px 36px 22px!important;
  margin:4px 0 30px!important;
  box-shadow:0 12px 28px rgba(7,91,53,.16)!important;
  overflow:visible!important;
}
.st-key-cdt_top_header [data-testid="stHorizontalBlock"]{gap:18px!important}
.cdt-brandline{font-size:.88rem!important;line-height:1!important;font-weight:950!important;letter-spacing:.01em!important;color:#7FE044!important;margin:0 0 13px!important;text-transform:uppercase!important}
.cdt-title{font-size:2.18rem!important;line-height:1!important;font-weight:950!important;letter-spacing:-.025em!important;color:#fff!important;margin:0!important}
.cdt-unit-emphasis{font-size:1.42rem!important;line-height:1!important;font-weight:950!important;color:#7FE044!important;text-align:left!important;margin-top:18px!important;letter-spacing:-.015em!important}
.st-key-cdt_top_header [data-testid="stPopover"]{display:flex!important;justify-content:flex-end!important;width:100%!important}
.st-key-cdt_top_header [data-testid="stPopover"]>button{
  width:auto!important;min-width:180px!important;max-width:100%!important;height:54px!important;min-height:54px!important;
  padding:0 18px!important;border-radius:15px!important;background:#0E1730!important;border:1px solid rgba(255,255,255,.08)!important;
  color:#fff!important;font-size:.91rem!important;font-weight:850!important;box-shadow:0 5px 14px rgba(3,12,27,.18)!important;
  white-space:nowrap!important;overflow:hidden!important;text-overflow:ellipsis!important;
}
.st-key-header_control_strip{margin-top:52px!important;padding:0!important;background:transparent!important}
.st-key-header_control_strip [data-testid="stHorizontalBlock"]{align-items:center!important;gap:18px!important}
.st-key-header_control_strip [data-testid="stSegmentedControl"]{background:#fff!important;border:1px solid rgba(255,255,255,.45)!important;border-radius:13px!important;padding:0!important;min-height:52px!important;overflow:hidden!important;box-shadow:0 4px 12px rgba(0,0,0,.06)!important}
.st-key-header_control_strip [data-testid="stSegmentedControl"]>div{gap:0!important;background:transparent!important;border:0!important;padding:0!important;width:100%!important}
.st-key-header_control_strip [data-testid="stSegmentedControl"] button{background:#fff!important;color:#182033!important;border:0!important;border-right:1px solid #D9DEE7!important;border-radius:0!important;min-height:52px!important;padding:0 16px!important;font-size:.83rem!important;font-weight:700!important;box-shadow:none!important;white-space:nowrap!important}
.st-key-header_control_strip [data-testid="stSegmentedControl"] button:last-child{border-right:0!important}
.st-key-header_control_strip .st-key-top_nav_area [data-testid="stSegmentedControl"] button[aria-pressed="true"]{background:#fff!important;color:#EF3E38!important;box-shadow:inset 0 0 0 1.5px #F45A55!important;font-weight:850!important}
.st-key-header_control_strip [data-testid="column"]:nth-child(4) [data-testid="stSegmentedControl"] button[aria-pressed="true"]{background:#FFF1F0!important;color:#EF3E38!important;box-shadow:inset 0 0 0 1.5px #F45A55!important;font-weight:900!important}
.header-meta{display:flex;align-items:center;gap:9px;color:#fff;font-size:.82rem;font-weight:800;line-height:1.1;white-space:nowrap;padding:0 6px}
.header-meta-icon{font-size:1.18rem;line-height:1;color:#fff;font-weight:900}
.header-month{font-weight:900}

/* Três cards executivos na proporção da referência. */
.exec-compact-grid{grid-template-columns:1.42fr 1fr 1fr!important;gap:22px!important;margin:0 2px 22px!important}
.exec-compact-card{border-radius:23px!important;padding:28px 30px!important;min-height:210px!important;box-shadow:0 8px 20px rgba(15,23,42,.07)!important}
.exec-performance{background:linear-gradient(135deg,#0C1835,#173466)!important;border:1px solid #193C79!important}
.exec-goal{border:1px solid #E3E7EE!important;border-top:5px solid #F59E0B!important}
.exec-energy{border:1px solid #E3E7EE!important;border-top:5px solid #149BDE!important}
.exec-compact-title{font-size:.92rem!important;line-height:1!important;margin-bottom:34px!important;color:#65728B!important;font-weight:900!important;letter-spacing:.01em!important}
.exec-performance .exec-compact-title{color:#fff!important}
.exec-performance-values,.exec-pair-values{align-items:end!important;gap:18px!important}
.exec-performance-values small,.exec-pair-values small{font-size:.72rem!important;line-height:1!important;font-weight:850!important;letter-spacing:.01em!important;color:#69758E!important}
.exec-performance-values strong{font-size:1.72rem!important;line-height:1!important;margin-top:17px!important}
.exec-performance-values .exec-main-value strong{font-size:1.72rem!important}
.exec-pair-values strong{font-size:1.70rem!important;line-height:1!important;margin-top:17px!important;color:#111A31!important}

@media(max-width:900px){
 .st-key-cdt_top_header{border-radius:18px!important;padding:18px 18px 14px!important;margin-bottom:16px!important}
 .cdt-brandline{font-size:.65rem!important;margin-bottom:8px!important}.cdt-title{font-size:1.55rem!important}.cdt-unit-emphasis{font-size:1.04rem!important;margin-top:10px!important}
 .st-key-cdt_top_header [data-testid="stPopover"]>button{min-width:145px!important;height:42px!important;min-height:42px!important;font-size:.72rem!important;padding:0 12px!important}
 .st-key-header_control_strip{margin-top:28px!important}
 .st-key-header_control_strip [data-testid="stHorizontalBlock"]{display:flex!important;flex-wrap:wrap!important;gap:7px 8px!important}
 .st-key-header_control_strip [data-testid="column"]:nth-child(1){flex:1 1 40%!important}.st-key-header_control_strip [data-testid="column"]:nth-child(2){flex:1 1 52%!important}
 .st-key-header_control_strip [data-testid="column"]:nth-child(3){flex:0 0 31%!important}.st-key-header_control_strip [data-testid="column"]:nth-child(4){flex:1 1 65%!important;overflow:hidden!important}
 .st-key-header_control_strip [data-testid="stSegmentedControl"]{min-height:42px!important;border-radius:10px!important}
 .st-key-header_control_strip [data-testid="stSegmentedControl"] button{min-height:42px!important;font-size:.67rem!important;padding:0 10px!important}
 .header-meta{font-size:.66rem!important;gap:6px!important;padding:0 2px!important}.header-meta-icon{font-size:.92rem!important}
 .exec-compact-grid{grid-template-columns:1fr 1fr!important;gap:8px!important;margin:0 0 12px!important}
 .exec-performance{grid-column:1/-1!important}
 .exec-compact-card{min-height:132px!important;padding:16px 16px!important;border-radius:15px!important}
 .exec-compact-title{font-size:.64rem!important;margin-bottom:18px!important}
 .exec-performance-values small,.exec-pair-values small{font-size:.54rem!important}
 .exec-performance-values strong,.exec-performance-values .exec-main-value strong,.exec-pair-values strong{font-size:1.28rem!important;margin-top:9px!important}
}
@media(max-width:430px){
 .block-container{padding-top:.25rem!important;padding-left:.55rem!important;padding-right:.55rem!important}
 .st-key-cdt_top_header{padding:14px 13px 11px!important;border-radius:15px!important;margin-top:1px!important;margin-bottom:10px!important}
 .st-key-cdt_top_header [data-testid="stHorizontalBlock"]{gap:6px!important}
 .cdt-brandline{font-size:.52rem!important}.cdt-title{font-size:1.18rem!important}.cdt-unit-emphasis{font-size:.86rem!important;margin-top:8px!important}
 .st-key-cdt_top_header [data-testid="column"]:last-child{min-width:112px!important;max-width:43%!important}
 .st-key-cdt_top_header [data-testid="stPopover"]>button{min-width:0!important;width:100%!important;height:36px!important;min-height:36px!important;font-size:.60rem!important;padding:0 8px!important;border-radius:10px!important}
 .st-key-header_control_strip{margin-top:18px!important}
 .st-key-header_control_strip [data-testid="stHorizontalBlock"]{gap:5px 6px!important}
 .st-key-header_control_strip [data-testid="column"]:nth-child(1){flex-basis:100%!important}.st-key-header_control_strip [data-testid="column"]:nth-child(2){flex-basis:58%!important}.st-key-header_control_strip [data-testid="column"]:nth-child(3){flex-basis:36%!important}.st-key-header_control_strip [data-testid="column"]:nth-child(4){flex-basis:100%!important}
 .st-key-header_control_strip [data-testid="stSegmentedControl"]{min-height:36px!important;border-radius:9px!important}
 .st-key-header_control_strip [data-testid="stSegmentedControl"] button{min-height:36px!important;font-size:.60rem!important;padding:0 7px!important}
 .header-meta{font-size:.57rem!important}.header-meta-icon{font-size:.80rem!important}
 .exec-compact-card{min-height:112px!important;padding:13px 12px!important;border-radius:13px!important}
 .exec-compact-title{font-size:.55rem!important;margin-bottom:13px!important}
 .exec-performance-values{grid-template-columns:1.1fr 1fr 1fr!important;gap:6px!important}.exec-pair-values{gap:5px!important}
 .exec-performance-values small,.exec-pair-values small{font-size:.45rem!important}
 .exec-performance-values strong,.exec-performance-values .exec-main-value strong,.exec-pair-values strong{font-size:1.05rem!important;margin-top:7px!important}
}
'''
marker='\n</style>"""'
if marker not in s:
    raise SystemExit('Fim do CSS não encontrado.')
s=s.replace(marker,css+marker,1)
path.write_text(s,encoding='utf-8')
