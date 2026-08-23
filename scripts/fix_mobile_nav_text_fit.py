from pathlib import Path

p = Path('app.py')
s = p.read_text(encoding='utf-8')
needle = '    st.markdown("""<style>\n/* CORRECAO ESTRUTURAL FINAL DOS CONTROLES MOBILE.'
if needle not in s:
    raise SystemExit('Bloco mobile alvo nao encontrado')

css = '''    st.markdown("""<style>\n/* Ajuste cirurgico: somente mobile. Mantem as duas colunas e faz o conteudo caber dentro dos botoes. */\n@media(max-width:600px){\n  .st-key-top_nav_buttons [data-testid="stHorizontalBlock"]{\n    grid-template-columns:minmax(0,1fr) minmax(0,1fr)!important;\n    width:100%!important;max-width:100%!important;overflow:visible!important;\n    box-sizing:border-box!important;\n  }\n  .st-key-top_nav_buttons [data-testid="column"],\n  .st-key-top_nav_buttons .stButton,\n  .st-key-top_nav_buttons .stButton > div{\n    min-width:0!important;max-width:100%!important;width:100%!important;box-sizing:border-box!important;\n  }\n  .st-key-top_nav_buttons .stButton button{\n    width:100%!important;max-width:100%!important;min-width:0!important;box-sizing:border-box!important;\n    padding-left:4px!important;padding-right:4px!important;overflow:hidden!important;\n  }\n  .st-key-top_nav_buttons .stButton button p{\n    margin:0!important;max-width:100%!important;min-width:0!important;\n    font-size:clamp(.54rem,2.7vw,.64rem)!important;line-height:1!important;\n    white-space:nowrap!important;overflow:hidden!important;text-overflow:clip!important;\n  }\n}\n</style>""",unsafe_allow_html=True)\n'''

s = s.replace(needle, css + needle, 1)
p.write_text(s, encoding='utf-8')
print('Ajuste mobile inserido sem alterar regras desktop.')
