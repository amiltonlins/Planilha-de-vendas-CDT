from pathlib import Path

p=Path('app.py')
s=p.read_text(encoding='utf-8')

old='''    commercial_html=''.join(seller_kpi_card(*item) for item in commercial)\n    awards_html=''.join(seller_kpi_card(*item) for item in awards)\n    return (\n        '<div class="seller-groups">'\n        '<div class="seller-group-title">DESEMPENHO COMERCIAL</div>'\n        f'<div class="seller-kpi-grid">{commercial_html}</div>'\n        '<div class="seller-group-title award">PREMIAÇÃO</div>'\n        f'<div class="seller-kpi-grid award-grid">{awards_html}</div>'\n        '</div>'\n    )\n'''
new='''    commercial_html=''.join(seller_kpi_card(*item) for item in commercial)\n    awards_html=''.join(seller_kpi_card(*item) for item in awards)\n    mobile_primary=[\n        ("VENDAS",x["vendas"],"Produção","primary"),\n        ("PREMIAÇÃO ATUAL",money(x["base"]),"Já acumulada","primary"),\n        ("PROJEÇÃO",x["projecao"],f'Meta {x["meta_individual"]}',"primary mobile-projection"),\n        ("TOTAL VARIÁVEL PROJETADO",money(x["total_variavel_proj"]),"Fechamento estimado","primary total"),\n    ]\n    mobile_html=''.join(seller_kpi_card(*item) for item in mobile_primary)\n    return (\n        f'<div class="seller-mobile-primary">{mobile_html}</div>'\n        '<div class="seller-groups">'\n        '<div class="seller-group-title">DESEMPENHO COMERCIAL</div>'\n        f'<div class="seller-kpi-grid">{commercial_html}</div>'\n        '<div class="seller-group-title award">PREMIAÇÃO</div>'\n        f'<div class="seller-kpi-grid award-grid">{awards_html}</div>'\n        '</div>'\n    )\n'''
if old not in s: raise SystemExit('seller_kpis_html alvo não encontrado')
s=s.replace(old,new,1)

# Mark desktop duplicates so they can disappear only on mobile.
s=s.replace('(\"VENDAS\",x[\"vendas\"],\"Produção\",\"primary\"),','(\"VENDAS\",x[\"vendas\"],\"Produção\",\"primary mobile-duplicate\"),',1)
s=s.replace('(\"PROJEÇÃO\",x[\"projecao\"],f\'Meta {x[\"meta_individual\"]}\',\"level2\"),','(\"PROJEÇÃO\",x[\"projecao\"],f\'Meta {x[\"meta_individual\"]}\',\"level2 mobile-duplicate\"),',1)
s=s.replace('(\"PREMIAÇÃO ATUAL\",money(x[\"base\"]),\"Já acumulada\",\"primary\"),','(\"PREMIAÇÃO ATUAL\",money(x[\"base\"]),\"Já acumulada\",\"primary mobile-duplicate\"),',1)
s=s.replace('(\"TOTAL VARIÁVEL PROJETADO\",money(x[\"total_variavel_proj\"]),\"Fechamento estimado\",\"primary total\"),','(\"TOTAL VARIÁVEL PROJETADO\",money(x[\"total_variavel_proj\"]),\"Fechamento estimado\",\"primary total mobile-duplicate\"),',1)

css='''.seller-mobile-primary{display:none}\n@media(max-width:560px){.seller-mobile-primary{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:7px;margin-top:12px}.seller-kpi-grid .mobile-duplicate{display:none}.seller-mobile-primary .seller-kpi{min-width:0}.seller-mobile-primary .seller-kpi strong{white-space:normal;overflow-wrap:anywhere}.seller-groups{margin-top:8px}}\n'''
if '.seller-mobile-primary{display:none}' not in s:
    s=s.replace('</style>',css+'\n</style>',1)

p.write_text(s,encoding='utf-8')
