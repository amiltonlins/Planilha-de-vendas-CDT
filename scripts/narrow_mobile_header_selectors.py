from pathlib import Path
p=Path('app.py')
s=p.read_text(encoding='utf-8')
repls={
'''  .st-key-header_control_strip [data-testid="stHorizontalBlock"]{
    display:grid!important;grid-template-columns:minmax(0,1fr) minmax(0,1fr)!important;
    gap:6px 8px!important;align-items:center!important;width:100%!important;flex-wrap:unset!important;
  }''':'''  .st-key-header_control_strip > div[data-testid="stVerticalBlock"] > div[data-testid="stHorizontalBlock"]{
    display:grid!important;grid-template-columns:minmax(0,1fr) minmax(0,1fr)!important;
    gap:6px 8px!important;align-items:center!important;width:100%!important;flex-wrap:unset!important;
  }''',
'''  .st-key-header_control_strip [data-testid="column"]{
    width:100%!important;max-width:none!important;min-width:0!important;flex:none!important;
  }''':'''  .st-key-header_control_strip > div[data-testid="stVerticalBlock"] > div[data-testid="stHorizontalBlock"] > div[data-testid="column"]{
    width:100%!important;max-width:none!important;min-width:0!important;flex:none!important;
  }''',
'''  .st-key-header_control_strip [data-testid="column"]:nth-child(4){grid-column:1 / -1!important;grid-row:3!important;overflow:hidden!important;}''':'''  .st-key-header_control_strip > div[data-testid="stVerticalBlock"] > div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(4){grid-column:1 / -1!important;grid-row:3!important;overflow:hidden!important;}'''
}
count=0
for a,b in repls.items():
    if a in s:
        s=s.replace(a,b)
        count+=1
if count!=3:
    raise SystemExit(f'Esperava corrigir 3 seletores; corrigi {count}. Abortando.')
p.write_text(s,encoding='utf-8')
print('3 seletores restantes restringidos ao container externo.')
