from pathlib import Path

p=Path('app.py')
s=p.read_text(encoding='utf-8')
old='''        f'<a class="top-nav-item {"active" if item==area else ""}" href="?area={urllib.parse.quote(item)}">{html.escape(item)}</a>'\n'''
new='''        f'<a class="top-nav-item {"active" if item==area else ""}" href="?area={urllib.parse.quote(item)}" target="_self">{html.escape(item)}</a>'\n'''
if old not in s:
    raise SystemExit('link da navegação superior não encontrado')
s=s.replace(old,new,1)
p.write_text(s,encoding='utf-8')
