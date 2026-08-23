from pathlib import Path

p=Path('app.py')
s=p.read_text(encoding='utf-8')
anchor='    base=json.loads((ROOT/"config.json").read_text(encoding="utf-8"))\n'
if anchor not in s:
    raise SystemExit('Ponto de inserção não encontrado; abortando.')

css=r'''
    st.markdown("""<style>
/* Ajuste MOBILE: remover espaço vazio superior e fazer todas as semanas caberem sem rolagem. Desktop intocado. */
@media(max-width:700px){
  /* Elimina a faixa vazia criada pelo espaçamento superior padrão do Streamlit no mobile. */
  [data-testid="stAppViewContainer"] > .main,
  [data-testid="stAppViewContainer"] section.main,
  [data-testid="stMain"],
  .stMain{
    padding-top:0!important;
    margin-top:0!important;
  }
  [data-testid="stMainBlockContainer"],
  .main .block-container,
  .block-container{
    padding-top:.35rem!important;
    margin-top:0!important;
  }
  .st-key-cdt_top_header{
    margin-top:0!important;
  }

  /* Seletor de semanas: todas as semanas cabem na largura disponível, sem scroll horizontal. */
  .st-key-dashboard_view_controls .st-key-week_nav_buttons{
    width:100%!important;
    max-width:100%!important;
    min-width:0!important;
    overflow:visible!important;
    margin:1px 0 0!important;
    padding:0!important;
  }
  .st-key-dashboard_view_controls .st-key-week_nav_buttons [data-testid="stHorizontalBlock"]{
    display:flex!important;
    flex-direction:row!important;
    flex-wrap:nowrap!important;
    width:100%!important;
    min-width:0!important;
    max-width:100%!important;
    gap:2px!important;
    overflow:visible!important;
  }
  .st-key-dashboard_view_controls .st-key-week_nav_buttons [data-testid="column"]{
    flex:1 1 0!important;
    width:auto!important;
    min-width:0!important;
    max-width:none!important;
    padding:0!important;
  }
  .st-key-dashboard_view_controls .st-key-week_nav_buttons .stButton,
  .st-key-dashboard_view_controls .st-key-week_nav_buttons .stButton>div{
    width:100%!important;
    min-width:0!important;
  }
  .st-key-dashboard_view_controls .st-key-week_nav_buttons .stButton button{
    width:100%!important;
    min-width:0!important;
    max-width:100%!important;
    height:22px!important;
    min-height:22px!important;
    padding:0 1px!important;
    border-radius:4px!important;
    font-size:clamp(.43rem,1.9vw,.50rem)!important;
    line-height:1!important;
    white-space:nowrap!important;
    overflow:hidden!important;
    text-overflow:clip!important;
  }
  .st-key-dashboard_view_controls .st-key-week_nav_buttons .stButton button p,
  .st-key-dashboard_view_controls .st-key-week_nav_buttons .stButton button span{
    margin:0!important;
    padding:0!important;
    white-space:nowrap!important;
    font:inherit!important;
    line-height:1!important;
  }
}
@media(max-width:390px){
  [data-testid="stMainBlockContainer"],.main .block-container,.block-container{padding-top:.22rem!important;}
  .st-key-dashboard_view_controls .st-key-week_nav_buttons [data-testid="stHorizontalBlock"]{gap:1px!important;}
  .st-key-dashboard_view_controls .st-key-week_nav_buttons .stButton button{
    height:21px!important;min-height:21px!important;font-size:clamp(.40rem,1.8vw,.47rem)!important;
  }
}
</style>""",unsafe_allow_html=True)
'''

s=s.replace(anchor,css+anchor,1)
p.write_text(s,encoding='utf-8')
print('Ajuste mobile aplicado: topo sem espaço vazio e semanas sem rolagem horizontal.')
