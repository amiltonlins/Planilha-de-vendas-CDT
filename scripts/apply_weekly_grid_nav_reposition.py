from pathlib import Path

p = Path('app.py')
s = p.read_text(encoding='utf-8')

start_marker = '    with st.container(key="cdt_top_header"):\n'
end_marker = '\n    if st.session_state.area=="GESTÃO":\n'
start = s.find(start_marker)
if start < 0:
    raise SystemExit('Cabeçalho atual não encontrado; abortando para não alterar outra área.')
end = s.find(end_marker, start)
if end < 0:
    raise SystemExit('Fim do cabeçalho atual não encontrado; abortando.')

replacement = '''    selected_area=st.session_state.area
    selected_week=default_week

    # Cabeçalho institucional: somente identidade + conta. A navegação fica fora do bloco verde.
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

    # Seletor pequeno e discreto imediatamente antes do conteúdo principal.
    if st.session_state.area!="GESTÃO":
        with st.container(key="dashboard_view_controls"):
            nav_col,update_col,month_col,spacer_col=st.columns([2.15,2.05,1.15,4.65],vertical_alignment="center")
            with nav_col:
                with st.container(key="top_nav_buttons"):
                    nav_a,nav_b=st.columns(2,gap="small")
                    with nav_a:
                        if st.button("VISÃO GERAL",key="nav_visao_btn",use_container_width=True,type="primary" if st.session_state.area=="VISÃO GERAL" else "secondary"):
                            selected_area="VISÃO GERAL"
                    with nav_b:
                        if st.button("SEMANAL",key="nav_semanal_btn",use_container_width=True,type="primary" if st.session_state.area=="SEMANAL" else "secondary"):
                            selected_area="SEMANAL"
            with update_col:
                st.markdown(f'<div class="header-meta header-update">{html.escape(update_text)}</div>',unsafe_allow_html=True)
            with month_col:
                st.markdown(f'<div class="header-meta header-month">{html.escape(competence_text)}</div>',unsafe_allow_html=True)
            with spacer_col:
                st.empty()

            # As semanas existem somente na visualização Semanal; em Visão Geral não são renderizadas nem reservam espaço.
            if st.session_state.area=="SEMANAL":
                with st.container(key="week_nav_buttons"):
                    week_cols=st.columns(len(week_labels),gap="small")
                    for week_i,(week_col,week_label) in enumerate(zip(week_cols,week_labels)):
                        with week_col:
                            if st.button(week_label,key=f"week_btn_{week_i}",use_container_width=True,type="primary" if week_label==default_week else "secondary"):
                                selected_week=week_label
                st.session_state["weekly_selected_label"]=selected_week
    else:
        selected_area="GESTÃO"
'''

s = s[:start] + replacement + s[end:]

css = r'''
    st.markdown("""<style>
/* Navegação externa ao cabeçalho + ranking semanal em duas colunas. UI apenas. */
.st-key-dashboard_view_controls{
  margin:2px 0 5px!important;padding:0!important;width:100%!important;
}
.st-key-dashboard_view_controls [data-testid="stHorizontalBlock"]{align-items:center!important;gap:6px!important}
.st-key-dashboard_view_controls [data-testid="column"]{min-width:0!important}
.st-key-dashboard_view_controls .header-meta{font-size:.58rem!important;line-height:1.05!important;color:#64748B!important;font-weight:750!important;white-space:nowrap!important;margin:0!important;padding:0!important}
.st-key-dashboard_view_controls .header-month{font-weight:900!important;color:#334155!important;text-align:left!important}

/* Visão Geral / Semanal: seletor pequeno, sem aparência de card. */
.st-key-dashboard_view_controls .st-key-top_nav_buttons{margin:0!important;padding:0!important}
.st-key-dashboard_view_controls .st-key-top_nav_buttons [data-testid="stHorizontalBlock"]{gap:3px!important}
.st-key-dashboard_view_controls .st-key-top_nav_buttons .stButton button{
  min-height:27px!important;height:27px!important;padding:0 7px!important;border-radius:6px!important;
  background:transparent!important;color:#64748B!important;border:1px solid transparent!important;
  box-shadow:none!important;font-size:.57rem!important;font-weight:800!important;white-space:nowrap!important;
}
.st-key-dashboard_view_controls .st-key-top_nav_buttons .stButton button:hover{background:#F8FAFC!important;color:#0F172A!important}
.st-key-dashboard_view_controls .st-key-top_nav_buttons .stButton button[kind="primary"],
.st-key-dashboard_view_controls .st-key-top_nav_buttons [data-testid="stBaseButton-primary"]{
  background:#F8FAFC!important;color:#075B35!important;border-color:#DDE7E2!important;font-weight:950!important;
}

/* Semanas: somente em Semanal, extremamente compactas e neutras. */
.st-key-dashboard_view_controls .st-key-week_nav_buttons{margin:1px 0 0!important;padding:0!important;width:100%!important;max-width:620px!important}
.st-key-dashboard_view_controls .st-key-week_nav_buttons [data-testid="stHorizontalBlock"]{gap:2px!important;align-items:center!important}
.st-key-dashboard_view_controls .st-key-week_nav_buttons .stButton button{
  min-height:24px!important;height:24px!important;padding:0 5px!important;border-radius:4px!important;
  background:transparent!important;color:#64748B!important;border:0!important;border-bottom:1px solid transparent!important;
  box-shadow:none!important;font-size:.53rem!important;font-weight:750!important;white-space:nowrap!important;
}
.st-key-dashboard_view_controls .st-key-week_nav_buttons .stButton button:hover{background:#F8FAFC!important;color:#0F172A!important}
.st-key-dashboard_view_controls .st-key-week_nav_buttons .stButton button[kind="primary"],
.st-key-dashboard_view_controls .st-key-week_nav_buttons [data-testid="stBaseButton-primary"]{
  color:#0F172A!important;font-weight:950!important;border-bottom:2px solid #075B35!important;background:transparent!important;
}

/* Ranking semanal: 1º|2º, 3º|4º... no desktop, sem mudar ordem ou dados. */
@media(min-width:701px){
  .weekly-game-list{display:grid!important;grid-template-columns:repeat(2,minmax(0,1fr))!important;gap:8px 10px!important;margin:7px 0 12px!important;align-items:stretch!important}
  .weekly-game-card{height:100%!important;min-width:0!important;padding:9px 10px!important;border-radius:10px!important}
  .weekly-game-head{grid-template-columns:30px minmax(0,1fr) auto!important;gap:6px!important}
  .weekly-game-head b{font-size:.74rem!important}
  .weekly-pos{font-size:.68rem!important}
  .weekly-money-emoji{font-size:.90rem!important}
  .weekly-game-main{gap:6px!important;margin-top:5px!important}
  .weekly-game-main>div{padding:5px 7px!important;min-width:0!important}
  .weekly-game-main strong{font-size:1.15rem!important}
  .weekly-prize strong{font-size:.96rem!important}
  .weekly-game-main small{font-size:.48rem!important}
  .weekly-target{margin-top:5px!important;padding:4px 7px!important;font-size:.59rem!important;line-height:1.15!important}
}

/* Mobile continua em uma coluna e controles nunca se sobrepõem. */
@media(max-width:700px){
  .weekly-game-list{grid-template-columns:1fr!important}
  .st-key-dashboard_view_controls{margin:2px 0 4px!important}
  .st-key-dashboard_view_controls > div[data-testid="stHorizontalBlock"],
  .st-key-dashboard_view_controls > [data-testid="stVerticalBlock"] > div[data-testid="stHorizontalBlock"]{
    display:grid!important;grid-template-columns:minmax(0,1fr) minmax(0,1fr)!important;gap:3px 6px!important;width:100%!important;
  }
  .st-key-dashboard_view_controls > div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(1),
  .st-key-dashboard_view_controls > [data-testid="stVerticalBlock"] > div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(1){grid-column:1/-1!important;grid-row:1!important}
  .st-key-dashboard_view_controls > div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(2),
  .st-key-dashboard_view_controls > [data-testid="stVerticalBlock"] > div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(2){grid-column:1!important;grid-row:2!important}
  .st-key-dashboard_view_controls > div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(3),
  .st-key-dashboard_view_controls > [data-testid="stVerticalBlock"] > div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(3){grid-column:2!important;grid-row:2!important}
  .st-key-dashboard_view_controls > div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(4),
  .st-key-dashboard_view_controls > [data-testid="stVerticalBlock"] > div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(4){display:none!important}
  .st-key-dashboard_view_controls .st-key-top_nav_buttons .stButton button{height:26px!important;min-height:26px!important;font-size:.56rem!important;padding:0 5px!important}
  .st-key-dashboard_view_controls .header-meta{font-size:.52rem!important}
  .st-key-dashboard_view_controls .st-key-week_nav_buttons{max-width:100%!important;overflow-x:auto!important;overflow-y:hidden!important;scrollbar-width:none!important}
  .st-key-dashboard_view_controls .st-key-week_nav_buttons::-webkit-scrollbar{display:none!important}
  .st-key-dashboard_view_controls .st-key-week_nav_buttons [data-testid="stHorizontalBlock"]{display:flex!important;flex-wrap:nowrap!important;width:max-content!important;min-width:100%!important;gap:1px!important}
  .st-key-dashboard_view_controls .st-key-week_nav_buttons [data-testid="column"]{flex:1 0 42px!important;min-width:42px!important;width:auto!important}
  .st-key-dashboard_view_controls .st-key-week_nav_buttons .stButton button{height:23px!important;min-height:23px!important;padding:0 3px!important;font-size:.50rem!important}
}
</style>""",unsafe_allow_html=True)
'''

anchor = '    base=json.loads((ROOT/"config.json").read_text(encoding="utf-8"))\n'
if anchor not in s:
    raise SystemExit('Ponto de inserção do CSS não encontrado; abortando.')
s = s.replace(anchor, css + anchor, 1)

p.write_text(s, encoding='utf-8')
print('Navegação reposicionada e ranking semanal desktop em duas colunas; cálculos preservados.')
