from pathlib import Path

path=Path('app.py')
text=path.read_text(encoding='utf-8')
marker='/* SELETOR SEMANAL MOBILE ULTRACOMPACTO - 2026-08-24 */'
anchor='    base=json.loads((ROOT/"config.json").read_text(encoding="utf-8"))\n'
css='''    st.markdown("""<style>
/* SELETOR SEMANAL MOBILE ULTRACOMPACTO - 2026-08-24 */
@media(max-width:700px){
  .st-key-week_nav_buttons{
    width:100%!important;
    min-width:0!important;
    max-width:100%!important;
    margin:0!important;
    padding:0!important;
    overflow-x:auto!important;
    overflow-y:hidden!important;
    scrollbar-width:none!important;
    -webkit-overflow-scrolling:touch!important;
  }
  .st-key-week_nav_buttons::-webkit-scrollbar{display:none!important}
  .st-key-week_nav_buttons>[data-testid="stVerticalBlock"]{gap:0!important;width:auto!important;min-width:0!important}
  .st-key-week_nav_buttons>div[data-testid="stHorizontalBlock"],
  .st-key-week_nav_buttons>[data-testid="stVerticalBlock"]>div[data-testid="stHorizontalBlock"]{
    display:flex!important;
    flex-direction:row!important;
    flex-wrap:nowrap!important;
    justify-content:flex-start!important;
    align-items:center!important;
    gap:2px!important;
    width:max-content!important;
    min-width:0!important;
    max-width:none!important;
    margin:0!important;
    padding:0!important;
  }
  .st-key-week_nav_buttons [data-testid="column"]{
    flex:0 0 31px!important;
    width:31px!important;
    min-width:31px!important;
    max-width:31px!important;
    margin:0!important;
    padding:0!important;
  }
  .st-key-week_nav_buttons .stButton,
  .st-key-week_nav_buttons .stButton>div{
    width:31px!important;
    min-width:31px!important;
    max-width:31px!important;
    margin:0!important;
    padding:0!important;
  }
  .st-key-week_nav_buttons .stButton button{
    width:31px!important;
    min-width:31px!important;
    max-width:31px!important;
    height:28px!important;
    min-height:28px!important;
    margin:0!important;
    padding:0 2px!important;
    border-radius:6px!important;
    font-size:.60rem!important;
    line-height:1!important;
    white-space:nowrap!important;
    overflow:hidden!important;
    box-sizing:border-box!important;
  }
  /* No mobile exibimos somente S1..S6, sem símbolos de semana atual/concluída. */
  .st-key-week_nav_buttons .stButton button p,
  .st-key-week_nav_buttons .stButton button span{
    font-size:0!important;
    line-height:0!important;
    margin:0!important;
    padding:0!important;
  }
  .st-key-week_nav_buttons [data-testid="column"]:nth-child(1) button:after{content:"S1";font-size:.60rem!important;line-height:1!important}
  .st-key-week_nav_buttons [data-testid="column"]:nth-child(2) button:after{content:"S2";font-size:.60rem!important;line-height:1!important}
  .st-key-week_nav_buttons [data-testid="column"]:nth-child(3) button:after{content:"S3";font-size:.60rem!important;line-height:1!important}
  .st-key-week_nav_buttons [data-testid="column"]:nth-child(4) button:after{content:"S4";font-size:.60rem!important;line-height:1!important}
  .st-key-week_nav_buttons [data-testid="column"]:nth-child(5) button:after{content:"S5";font-size:.60rem!important;line-height:1!important}
  .st-key-week_nav_buttons [data-testid="column"]:nth-child(6) button:after{content:"S6";font-size:.60rem!important;line-height:1!important}
}
</style>""",unsafe_allow_html=True)
'''
if marker in text:
    print('Ajuste já aplicado.')
elif anchor not in text:
    raise SystemExit('Âncora não encontrada')
else:
    text=text.replace(anchor,css+anchor,1)
    path.write_text(text,encoding='utf-8')
    print('Seletor semanal mobile compactado.')
