from pathlib import Path

p = Path('app.py')
s = p.read_text(encoding='utf-8')

nav_anchor = '''  .st-key-top_nav_buttons .stButton button{\n    width:100%!important;min-width:0!important;max-width:none!important;height:38px!important;min-height:38px!important;\n    margin:0!important;padding:0 8px!important;border-radius:0!important;font-size:.64rem!important;font-weight:850!important;\n    white-space:nowrap!important;justify-content:center!important;box-shadow:none!important;\n  }'''
nav_replacement = nav_anchor + '''\n  .st-key-top_nav_buttons .stButton button p,\n  .st-key-top_nav_buttons .stButton button span{\n    max-width:100%!important;margin:0!important;font-size:.64rem!important;line-height:1!important;\n    white-space:nowrap!important;overflow:visible!important;text-overflow:clip!important;letter-spacing:-.01em!important;\n  }'''

week_anchor = '''  .st-key-week_nav_buttons .stButton button{\n    width:100%!important;min-width:44px!important;max-width:none!important;height:34px!important;min-height:34px!important;\n    margin:0!important;padding:0 4px!important;border-radius:0!important;font-size:.56rem!important;font-weight:850!important;\n    white-space:nowrap!important;justify-content:center!important;box-shadow:none!important;\n  }'''
week_replacement = week_anchor + '''\n  .st-key-week_nav_buttons .stButton button p,\n  .st-key-week_nav_buttons .stButton button span{\n    max-width:100%!important;margin:0!important;font-size:.56rem!important;line-height:1!important;\n    white-space:nowrap!important;overflow:visible!important;text-overflow:clip!important;\n  }'''

if nav_anchor not in s:
    raise SystemExit('Regra dos botoes Visao Geral/Semanal nao encontrada; abortando para nao alterar outra area.')
if week_anchor not in s:
    raise SystemExit('Regra dos botoes semanais nao encontrada; abortando para nao alterar outra area.')

s = s.replace(nav_anchor, nav_replacement, 1)
s = s.replace(week_anchor, week_replacement, 1)

# Em telas estreitas, force tambem o texto interno a acompanhar o tamanho ja definido para o botao.
small_anchor = '''@media(max-width:390px){\n  .st-key-top_nav_area [data-testid="stSegmentedControl"] button{font-size:.61rem!important;padding:0 5px!important;}'''
if small_anchor in s:
    s = s.replace(small_anchor, '''@media(max-width:390px){\n  .st-key-top_nav_area [data-testid="stSegmentedControl"] button{font-size:.61rem!important;padding:0 5px!important;}\n  .st-key-top_nav_buttons .stButton button p,.st-key-top_nav_buttons .stButton button span{font-size:.59rem!important;letter-spacing:-.015em!important;}''', 1)

p.write_text(s, encoding='utf-8')
print('Texto interno dos botoes mobile ajustado sem alterar desktop nem estrutura dos controles.')
