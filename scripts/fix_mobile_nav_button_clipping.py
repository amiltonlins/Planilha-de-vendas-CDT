from pathlib import Path

p=Path('app.py')
s=p.read_text(encoding='utf-8')

replacements={
    '.st-key-top_nav_buttons > div[data-testid="stVerticalBlock"] > div[data-testid="stHorizontalBlock"]':
    '.st-key-top_nav_buttons > div[data-testid="stHorizontalBlock"]',

    '.st-key-top_nav_buttons > div[data-testid="stVerticalBlock"] > div[data-testid="stHorizontalBlock"] > div[data-testid="column"]':
    '.st-key-top_nav_buttons > div[data-testid="stHorizontalBlock"] > div[data-testid="column"]',

    '.st-key-week_nav_buttons > div[data-testid="stVerticalBlock"] > div[data-testid="stHorizontalBlock"]':
    '.st-key-week_nav_buttons > div[data-testid="stHorizontalBlock"]',

    '.st-key-week_nav_buttons > div[data-testid="stVerticalBlock"] > div[data-testid="stHorizontalBlock"] > div[data-testid="column"]':
    '.st-key-week_nav_buttons > div[data-testid="stHorizontalBlock"] > div[data-testid="column"]',
}

changed=0
# Longer selectors first so they do not get partially consumed by the shorter replacement.
for old,new in sorted(replacements.items(), key=lambda kv: len(kv[0]), reverse=True):
    count=s.count(old)
    if count:
        s=s.replace(old,new)
        changed+=count

if changed < 4:
    raise SystemExit(f'Esperava corrigir pelo menos 4 seletores dos containers chaveados; corrigi {changed}.')

# Reforço estritamente mobile e limitado aos dois componentes. Não altera desktop nem aparência.
marker='MOBILE NAV BUTTON CLIP FIX'
if marker not in s:
    needle='    base=json.loads((ROOT/"config.json").read_text(encoding="utf-8"))\n'
    if needle not in s:
        raise SystemExit('Ponto de inserção do CSS final não encontrado.')
    css='''    st.markdown("""<style>\n/* MOBILE NAV BUTTON CLIP FIX — somente fluxo/largura; visual preservado. */\n@media(max-width:600px){\n  .st-key-top_nav_buttons{width:100%!important;min-width:0!important;max-width:100%!important;overflow:visible!important;box-sizing:border-box!important;}\n  .st-key-top_nav_buttons > div[data-testid="stHorizontalBlock"]{\n    display:grid!important;grid-template-columns:minmax(0,1fr) minmax(0,1fr)!important;\n    gap:6px!important;width:100%!important;min-width:0!important;max-width:100%!important;box-sizing:border-box!important;\n  }\n  .st-key-top_nav_buttons > div[data-testid="stHorizontalBlock"] > div[data-testid="column"]{\n    width:100%!important;min-width:0!important;max-width:100%!important;margin:0!important;padding:0!important;box-sizing:border-box!important;\n  }\n  .st-key-top_nav_buttons .stButton,.st-key-top_nav_buttons .stButton button{width:100%!important;min-width:0!important;max-width:100%!important;box-sizing:border-box!important;}\n  .st-key-top_nav_buttons .stButton button{white-space:nowrap!important;overflow:visible!important;text-overflow:clip!important;padding-left:6px!important;padding-right:6px!important;}\n\n  .st-key-week_nav_buttons{width:100%!important;min-width:0!important;max-width:100%!important;overflow-x:auto!important;overflow-y:hidden!important;box-sizing:border-box!important;scrollbar-width:none!important;}\n  .st-key-week_nav_buttons::-webkit-scrollbar{display:none!important;}\n  .st-key-week_nav_buttons > div[data-testid="stHorizontalBlock"]{\n    display:flex!important;flex-wrap:nowrap!important;gap:3px!important;width:max-content!important;min-width:100%!important;max-width:none!important;box-sizing:border-box!important;\n  }\n  .st-key-week_nav_buttons > div[data-testid="stHorizontalBlock"] > div[data-testid="column"]{\n    flex:1 0 44px!important;width:auto!important;min-width:44px!important;max-width:none!important;margin:0!important;padding:0!important;box-sizing:border-box!important;\n  }\n  .st-key-week_nav_buttons .stButton,.st-key-week_nav_buttons .stButton button{width:100%!important;min-width:0!important;box-sizing:border-box!important;}\n  .st-key-week_nav_buttons .stButton button{white-space:nowrap!important;overflow:visible!important;text-overflow:clip!important;}\n}\n</style>""",unsafe_allow_html=True)\n'''
    s=s.replace(needle,css+needle,1)

p.write_text(s,encoding='utf-8')
print(f'{changed} seletores corrigidos; patch mobile aplicado.')
