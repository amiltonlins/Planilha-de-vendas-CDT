from pathlib import Path

p=Path('app.py')
s=p.read_text(encoding='utf-8')

# Remove o status visual da tela individual do vendedor.
s=s.replace('''    status_emoji,status_message=projection_status_visual(meta_pct,x.get("meta_individual"),x.get("projecao"))\n    commercial_html=''.join(seller_kpi_card(*item) for item in commercial)+projection_status_card(status_emoji,status_message)\n''','''    commercial_html=''.join(seller_kpi_card(*item) for item in commercial)\n''',1)

# Insere o status visual dentro do ranking da página principal.
old='''        meta_pct=x["projecao"]/x["meta_individual"] if x["meta_individual"] else 0\n        rows.append(\n'''
new='''        meta_pct=x["projecao"]/x["meta_individual"] if x["meta_individual"] else 0\n        status_emoji,status_message=projection_status_visual(meta_pct,x.get("meta_individual"),x.get("projecao"))\n        rows.append(\n'''
if old not in s:
    raise SystemExit('ponto de cálculo do ranking não encontrado')
s=s.replace(old,new,1)

old='''            f'<span class="neo-highlight"><strong>{pct(x["neo_pct"])}</strong><small>% NEO</small></span>'\n            f'<span><strong>{money(x["base"])}</strong><small>PREMIAÇÃO ATUAL</small></span>'\n'''
new='''            f'<span class="neo-highlight"><strong>{pct(x["neo_pct"])}</strong><small>% NEO</small></span>'\n            f'<span class="rank-projection-status"><strong class="rank-status-emoji">{status_emoji}</strong><small>{html.escape(status_message)}</small></span>'\n            f'<span><strong>{money(x["base"])}</strong><small>PREMIAÇÃO ATUAL</small></span>'\n'''
if old not in s:
    raise SystemExit('ponto de inserção no ranking não encontrado')
s=s.replace(old,new,1)

css='''\n.rank-inside .rank-projection-status{background:rgba(255,255,255,.12);border-radius:8px;border-left:0}.rank-inside .rank-projection-status .rank-status-emoji{font-size:1.7rem;line-height:1}.rank-inside .rank-projection-status small{font-size:.52rem;font-weight:900;line-height:1.05;text-align:center}\n@media(max-width:720px){.rank-inside .rank-projection-status{grid-column:span 2!important}.rank-inside .rank-projection-status .rank-status-emoji{font-size:1.45rem!important}.rank-inside .rank-projection-status small{font-size:.46rem!important;line-height:1.05!important}}\n'''
if '.rank-projection-status{' not in s:
    s=s.replace('</style>',css+'\n</style>',1)

p.write_text(s,encoding='utf-8')
