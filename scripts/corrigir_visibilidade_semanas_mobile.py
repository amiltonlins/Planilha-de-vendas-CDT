from pathlib import Path

path=Path('app.py')
text=path.read_text(encoding='utf-8')
marker='''/* POPUP EXECUTIVO DO VENDEDOR - 2026-08 */'''
css='''
/* CORREÇÃO VISIBILIDADE DO SELETOR SEMANAL MOBILE - 2026-08 */
@media(max-width:700px){
  .st-key-dashboard_view_controls .st-key-week_nav_buttons{
    width:100%!important;
    max-width:100%!important;
    min-width:0!important;
    overflow-x:auto!important;
    overflow-y:hidden!important;
    box-sizing:border-box!important;
    -webkit-overflow-scrolling:touch!important;
    scrollbar-width:none!important;
  }
  .st-key-dashboard_view_controls .st-key-week_nav_buttons::-webkit-scrollbar{display:none!important;}
  .st-key-dashboard_view_controls .st-key-week_nav_buttons [data-testid="stHorizontalBlock"]{
    display:flex!important;
    flex-direction:row!important;
    flex-wrap:nowrap!important;
    justify-content:flex-start!important;
    align-items:center!important;
    width:auto!important;
    min-width:0!important;
    max-width:none!important;
    gap:1px!important;
    overflow:visible!important;
    box-sizing:border-box!important;
  }
  .st-key-dashboard_view_controls .st-key-week_nav_buttons [data-testid="column"]{
    flex:0 0 26px!important;
    width:26px!important;
    min-width:26px!important;
    max-width:26px!important;
    padding:0!important;
    margin:0!important;
  }
  .st-key-dashboard_view_controls .st-key-week_nav_buttons .stButton,
  .st-key-dashboard_view_controls .st-key-week_nav_buttons .stButton>div{
    width:26px!important;
    min-width:26px!important;
    max-width:26px!important;
    margin:0!important;
    padding:0!important;
  }
  .st-key-dashboard_view_controls .st-key-week_nav_buttons .stButton button{
    width:26px!important;
    min-width:26px!important;
    max-width:26px!important;
    height:25px!important;
    min-height:25px!important;
    padding:0 1px!important;
    margin:0!important;
    font-size:.50rem!important;
    line-height:1!important;
    box-sizing:border-box!important;
  }
}

'''
if marker not in text:
    raise SystemExit('Marcador CSS não encontrado')
text=text.replace(marker,css+marker,1)
path.write_text(text,encoding='utf-8')
print('Seletor semanal mobile ajustado para exibir todas as semanas via rolagem interna.')
# trigger workflow
