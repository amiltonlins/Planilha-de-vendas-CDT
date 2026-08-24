from pathlib import Path

path=Path('app.py')
text=path.read_text(encoding='utf-8')
marker='''    with st.container(key="cdt_top_header"):
'''
css='''    st.markdown("""<style>
/* CORREÇÃO FINAL DE DISTRIBUIÇÃO DAS SEMANAS NO MOBILE - baseada na validação visual */
@media(max-width:700px){
  .st-key-dashboard_view_controls .st-key-week_nav_buttons{
    width:100%!important;
    max-width:100%!important;
    min-width:0!important;
    overflow-x:auto!important;
    overflow-y:hidden!important;
    box-sizing:border-box!important;
    scrollbar-width:none!important;
    -webkit-overflow-scrolling:touch!important;
  }
  .st-key-dashboard_view_controls .st-key-week_nav_buttons::-webkit-scrollbar{display:none!important;}

  .st-key-dashboard_view_controls .st-key-week_nav_buttons > [data-testid="stVerticalBlock"]{
    width:auto!important;
    max-width:100%!important;
    min-width:0!important;
    overflow:visible!important;
  }

  .st-key-dashboard_view_controls .st-key-week_nav_buttons [data-testid="stHorizontalBlock"]{
    display:flex!important;
    flex-direction:row!important;
    flex-wrap:nowrap!important;
    justify-content:flex-start!important;
    align-items:center!important;
    gap:1px!important;
    width:max-content!important;
    min-width:0!important;
    max-width:none!important;
    overflow:visible!important;
    margin:0!important;
    padding:0!important;
  }

  .st-key-dashboard_view_controls .st-key-week_nav_buttons [data-testid="stHorizontalBlock"] > div[data-testid="column"]{
    flex:0 0 26px!important;
    width:26px!important;
    min-width:26px!important;
    max-width:26px!important;
    margin:0!important;
    padding:0!important;
  }

  .st-key-dashboard_view_controls .st-key-week_nav_buttons [data-testid="column"] > div,
  .st-key-dashboard_view_controls .st-key-week_nav_buttons .stButton,
  .st-key-dashboard_view_controls .st-key-week_nav_buttons .stButton > div{
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
    max-height:25px!important;
    margin:0!important;
    padding:0 1px!important;
    font-size:.50rem!important;
    line-height:1!important;
    justify-content:center!important;
    box-sizing:border-box!important;
  }
}
@media(max-width:390px){
  .st-key-dashboard_view_controls .st-key-week_nav_buttons [data-testid="stHorizontalBlock"] > div[data-testid="column"],
  .st-key-dashboard_view_controls .st-key-week_nav_buttons [data-testid="column"] > div,
  .st-key-dashboard_view_controls .st-key-week_nav_buttons .stButton,
  .st-key-dashboard_view_controls .st-key-week_nav_buttons .stButton > div,
  .st-key-dashboard_view_controls .st-key-week_nav_buttons .stButton button{
    flex-basis:24px!important;
    width:24px!important;
    min-width:24px!important;
    max-width:24px!important;
  }
}
</style>""",unsafe_allow_html=True)

'''
if marker not in text:
    raise SystemExit('Ponto final de CSS antes do cabeçalho não encontrado')
if 'CORREÇÃO FINAL DE DISTRIBUIÇÃO DAS SEMANAS NO MOBILE' not in text:
    text=text.replace(marker,css+marker,1)
path.write_text(text,encoding='utf-8')
print('Espaçamento das semanas corrigido: colunas fixas e agrupadas à esquerda no mobile.')
