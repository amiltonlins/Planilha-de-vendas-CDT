from pathlib import Path

p=Path('app.py')
s=p.read_text(encoding='utf-8')

# Os containers com key do Streamlit recebem a classe st-key-* no próprio
# stVerticalBlock. Por isso o stHorizontalBlock das colunas é filho direto.
# Corrigimos somente seletores mobile dos dois grupos de botões.
replacements={
    '.st-key-top_nav_buttons [data-testid="stHorizontalBlock"]':
    '.st-key-top_nav_buttons > div[data-testid="stHorizontalBlock"]',
    '.st-key-week_nav_buttons [data-testid="stHorizontalBlock"]':
    '.st-key-week_nav_buttons > div[data-testid="stHorizontalBlock"]',
}

changed=0
for old,new in replacements.items():
    count=s.count(old)
    if count:
        s=s.replace(old,new)
        changed+=count

if changed < 2:
    raise SystemExit(f'Esperava restringir pelo menos 2 seletores dos botões mobile; corrigi {changed}.')

marker='MOBILE NAV BUTTON CLIP FIX'
if marker not in s:
    needle='    base=json.loads((ROOT/"config.json").read_text(encoding="utf-8"))\n'
    if needle not in s:
        raise SystemExit('Ponto de inserção do CSS final não encontrado.')
    css='''    st.markdown("""<style>\n/* MOBILE NAV BUTTON CLIP FIX — somente mobile; desktop intocado. */\n@media(max-width:600px){\n  /* O componente principal ocupa exatamente a largura da coluna real. */\n  .st-key-top_nav_buttons{width:100%!important;min-width:0!important;max-width:100%!important;box-sizing:border-box!important;overflow:visible!important;}\n  .st-key-top_nav_buttons > div[data-testid="stHorizontalBlock"]{\n    display:grid!important;grid-template-columns:minmax(0,1fr) minmax(0,1fr)!important;\n    gap:6px!important;width:100%!important;min-width:0!important;max-width:100%!important;box-sizing:border-box!important;\n  }\n  .st-key-top_nav_buttons > div[data-testid="stHorizontalBlock"] > div[data-testid="column"]{\n    width:100%!important;min-width:0!important;max-width:100%!important;margin:0!important;padding:0!important;box-sizing:border-box!important;\n  }\n  .st-key-top_nav_buttons .stButton{width:100%!important;min-width:0!important;max-width:100%!important;margin:0!important;box-sizing:border-box!important;}\n  .st-key-top_nav_buttons .stButton button{\n    width:100%!important;min-width:0!important;max-width:100%!important;box-sizing:border-box!important;\n    white-space:nowrap!important;overflow:hidden!important;text-overflow:clip!important;padding-left:4px!important;padding-right:4px!important;\n  }\n\n  /* Semanas permanecem no mesmo visual, apenas sem quebra/corte. */\n  .st-key-week_nav_buttons{width:100%!important;min-width:0!important;max-width:100%!important;overflow-x:auto!important;overflow-y:hidden!important;box-sizing:border-box!important;scrollbar-width:none!important;}\n  .st-key-week_nav_buttons::-webkit-scrollbar{display:none!important;}\n  .st-key-week_nav_buttons > div[data-testid="stHorizontalBlock"]{\n    display:flex!important;flex-direction:row!important;flex-wrap:nowrap!important;gap:3px!important;\n    width:max-content!important;min-width:100%!important;max-width:none!important;box-sizing:border-box!important;\n  }\n  .st-key-week_nav_buttons > div[data-testid="stHorizontalBlock"] > div[data-testid="column"]{\n    flex:1 0 44px!important;width:auto!important;min-width:44px!important;max-width:none!important;margin:0!important;padding:0!important;box-sizing:border-box!important;\n  }\n  .st-key-week_nav_buttons .stButton{width:100%!important;min-width:0!important;margin:0!important;}\n  .st-key-week_nav_buttons .stButton button{width:100%!important;min-width:0!important;box-sizing:border-box!important;white-space:nowrap!important;overflow:hidden!important;text-overflow:clip!important;}\n}\n</style>""",unsafe_allow_html=True)\n'''
    s=s.replace(needle,css+needle,1)

p.write_text(s,encoding='utf-8')
print(f'{changed} seletores restringidos; correção mobile aplicada.')
