from pathlib import Path
import re

app=Path('app.py')
text=app.read_text(encoding='utf-8')

# 1) Nomenclatura visível; campos internos permanecem intactos.
for old,new in {
    'COMISSÃO ATUAL':'PREMIAÇÃO ATUAL',
    'COMISSÃO PROJETADA':'PREMIAÇÃO PROJETADA',
    'COMISSÃO PROJ.':'PREMIAÇÃO PROJ.',
    'COMISSÃO BASE ATUAL':'PREMIAÇÃO BASE ATUAL',
    'Comissão projetada':'Premiação projetada',
    'Comissões e cenários':'Premiações e cenários',
    'COMISSÕES':'PREMIAÇÕES',
    'PRÊMIOS ACUMULADOS':'SEMANAIS ACUMULADOS',
    'PRÊMIOS':'SEMANAIS',
    'Prêmios':'Semanais',
    'Prêmio S':'Semanal S',
    'Premiação acumulada':'Semanais acumulados',
    'BÔNUS ADIM. PROJ.':'BÔNUS (SE) 100% ADIM',
    'Bônus M2 proj.':'BÔNUS (SE) 100% ADIM',
}.items():
    text=text.replace(old,new)
text=text.replace('elif area=="COMISSÕES":','elif area=="PREMIAÇÕES":')

# 2) Helpers executivos.
marker='def ranking_html(ranking):\n'
helpers="""def executive_kpis_html(cfg,total,projection,neo,team):
    meta=cfg["meta_empresa"]
    ating=total/meta if meta else 0
    faltam=max(0,meta-total)
    neo_pct=neo/total if total else 0
    zeros=sum(x["zeros"] for x in team)
    return (
        '<div class="exec-grid">'
        f'<div class="exec-card hero"><small>VENDAS REALIZADAS</small><strong>{total}</strong><span>Resultado atual</span></div>'
        f'<div class="exec-card"><small>META DO MÊS</small><strong>{meta}</strong><span>Objetivo comercial</span></div>'
        f'<div class="exec-card projection"><small>PROJEÇÃO</small><strong>{projection}</strong><span>Fechamento estimado</span></div>'
        f'<div class="exec-card attainment"><small>% DA META</small><strong>{pct(ating)}</strong><span>Atingimento atual</span></div>'
        f'<div class="exec-card secondary"><small>FALTAM PARA META</small><strong>{faltam}</strong><span>Vendas necessárias</span></div>'
        f'<div class="exec-card secondary"><small>VENDAS NEO</small><strong>{neo}</strong><span>{pct(neo_pct)} do total</span></div>'
        f'<div class="exec-card secondary"><small>% NEO</small><strong>{pct(neo_pct)}</strong><span>Participação</span></div>'
        f'<div class="exec-card secondary critical"><small>ZEROS</small><strong>{zeros}</strong><span>Dias sem venda</span></div>'
        '</div>'
    )

def seller_kpi_card(label,value,sub,cls):
    return f'<div class="seller-kpi {cls}"><small>{html.escape(str(label))}</small><strong>{html.escape(str(value))}</strong><span>{html.escape(str(sub))}</span></div>'

def seller_kpis_html(x):
    meta_pct=x["projecao"]/x["meta_individual"] if x["meta_individual"] else 0
    status,_,_=performance(x["media"])
    commercial=[
        ("VENDAS",x["vendas"],"Produção","primary"),
        ("PROJEÇÃO",x["projecao"],f'Meta {x["meta_individual"]}',"level2"),
        ("MÉDIA/DIA",f'{x["media"]:.2f}',f'{x["dias"]} dias',"level2"),
        ("% META",pct(meta_pct),status,"level2"),
        ("ZEROS",x["zeros"],f'Semana {x["zeros_semana"]}',"level3"),
        ("NEO",x["neo"],"Neoenergia","level3"),
        ("% NEO",pct(x["neo_pct"]),"Participação","level3"),
    ]
    awards=[
        ("PREMIAÇÃO ATUAL",money(x["base"]),"Já acumulada","primary"),
        ("PREMIAÇÃO PROJETADA",money(x["comissao_proj"]),"Base projetada","level2"),
        ("BÔNUS NEO PROJETADO",money(x["bonus_neo_proj"]),"Projeção","level3"),
        ("BÔNUS (SE) 100% ADIM",money(x["bonus_adim_proj"]),"Condicional","level3"),
        ("SEMANAIS",money(x["premio_total"]),"Acumulado semanal","level3"),
        ("TOTAL VARIÁVEL PROJETADO",money(x["total_variavel_proj"]),"Fechamento estimado","primary total"),
    ]
    commercial_html=''.join(seller_kpi_card(*item) for item in commercial)
    awards_html=''.join(seller_kpi_card(*item) for item in awards)
    return (
        '<div class="seller-groups">'
        '<div class="seller-group-title">DESEMPENHO COMERCIAL</div>'
        f'<div class="seller-kpi-grid">{commercial_html}</div>'
        '<div class="seller-group-title award">PREMIAÇÃO</div>'
        f'<div class="seller-kpi-grid award-grid">{awards_html}</div>'
        '</div>'
    )

"""
if 'def executive_kpis_html' not in text:
    text=text.replace(marker,helpers+marker,1)

# 3) Ranking: nomenclatura e destaque.
text=text.replace('<small>COMISSÃO ATUAL</small>','<small>PREMIAÇÃO ATUAL</small>')
text=text.replace('<small>COMISSÃO PROJ.</small>','<small>PREMIAÇÃO PROJ.</small>')
text=text.replace('<small>PRÊMIOS</small>','<small>SEMANAIS</small>')
text=text.replace('<small>BÔNUS ADIM. PROJ.</small>','<small>BÔNUS (SE) 100% ADIM</small>')

# 4) CSS BI + mobile específico.
css_insert="""
.exec-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin:8px 0 14px}.exec-card{background:white;border:1px solid var(--line);border-radius:14px;padding:14px 16px;box-shadow:0 2px 10px rgba(15,23,42,.05);min-width:0}.exec-card small{display:block;font-size:.64rem;font-weight:900;letter-spacing:.055em;color:#64748B}.exec-card strong{display:block;font-size:1.8rem;line-height:1.05;margin-top:7px;color:#0F172A;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.exec-card span{display:block;font-size:.67rem;color:#94A3B8;margin-top:5px}.exec-card.hero{grid-column:span 2;background:linear-gradient(120deg,#0F172A,#172554);border-color:#172554}.exec-card.hero small,.exec-card.hero strong,.exec-card.hero span{color:white}.exec-card.hero strong{font-size:2.35rem}.exec-card.projection{border-top:4px solid #F59E0B}.exec-card.attainment{border-top:4px solid #22C55E}.exec-card.critical{border-top:4px solid #EF4444}.seller-groups{margin-top:12px}.seller-group-title{font-size:.72rem;font-weight:900;letter-spacing:.08em;color:#475569;margin:14px 0 7px}.seller-group-title.award{margin-top:18px}.seller-kpi-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:9px}.seller-kpi{background:white;border:1px solid var(--line);border-radius:12px;padding:12px;min-width:0}.seller-kpi small{display:block;font-size:.59rem;font-weight:900;color:#64748B;letter-spacing:.035em}.seller-kpi strong{display:block;font-size:1.2rem;color:#0F172A;margin-top:7px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.seller-kpi span{display:block;font-size:.63rem;color:#94A3B8;margin-top:4px}.seller-kpi.primary{background:#0F172A;border-color:#0F172A}.seller-kpi.primary small,.seller-kpi.primary strong,.seller-kpi.primary span{color:white}.seller-kpi.primary strong{font-size:1.55rem}.seller-kpi.total{background:linear-gradient(120deg,#0F172A,#172554)}
@media(max-width:900px){.exec-grid{grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}.exec-card.hero{grid-column:span 2}.exec-card.hero strong{font-size:2rem}.seller-kpi-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.rank-inside{grid-template-columns:repeat(2,minmax(0,1fr))}.rank-name{grid-template-columns:1fr}.rank-inside strong{white-space:normal;overflow-wrap:anywhere}.report{font-size:.68rem}}
@media(max-width:560px){.block-container{padding:.45rem!important}.bi-topbar{border-radius:10px;padding:12px}.exec-grid{grid-template-columns:repeat(2,minmax(0,1fr));gap:7px}.exec-card{padding:11px 10px;border-radius:11px}.exec-card.hero{grid-column:span 2}.exec-card strong{font-size:1.35rem}.exec-card.hero strong{font-size:1.9rem}.exec-card small{font-size:.56rem}.exec-card span{font-size:.58rem}.seller-kpi-grid{grid-template-columns:repeat(2,minmax(0,1fr));gap:7px}.seller-kpi{padding:10px 9px}.seller-kpi strong{font-size:1.05rem}.seller-kpi.primary strong{font-size:1.3rem}.rank-row{grid-template-columns:34px minmax(0,1fr)!important;padding:6px 2px!important}.rank-pos{font-size:.8rem}.rank-name{padding:9px!important;gap:8px!important}.rank-inside{grid-template-columns:repeat(2,minmax(0,1fr))!important}.rank-inside span{min-width:0}.rank-inside strong{font-size:.86rem!important;white-space:normal!important;overflow-wrap:anywhere}.rank-inside .neo-highlight strong{font-size:1.05rem!important}.rank-seller b{white-space:normal!important}.metric strong{white-space:normal;overflow-wrap:anywhere}.stDownloadButton button{width:100%}}
"""
if '.exec-grid{' not in text:
    text=text.replace('</style>',css_insert+'\n</style>',1)

# 5) Topo executivo. Remove de fato o gráfico Evolução comercial/mensal.
pattern=re.compile(r'''        cards\(st,\[\(\"META DO MÊS\".*?\]\)\n        left,right=st\.columns\(\[1\.7,1\],gap=\"small\"\)\n        with left:\n            st\.markdown\('<div class=\"section\">Evolução comercial</div>'.*?\n        with right:\n            st\.markdown\('<div class=\"section\">Distribuição de performance</div>'.*?cards\(st,\[\(k\.upper\(\),v,tones\[k\],\"vendedores\"\) for k,v in counts\.items\(\)\],2\)\n''',re.S)
replacement='''        st.markdown(executive_kpis_html(cfg,total,projection,neo,team),unsafe_allow_html=True)\n        st.markdown('<div class="section">Distribuição de performance</div>',unsafe_allow_html=True); counts={k:0 for k in ("Azul","Verde","Amarelo","Vermelho")}\n        for x in team:counts[performance(x["media"])[0]]+=1\n        tones={"Azul":"cyan","Verde":"green","Amarelo":"yellow","Vermelho":"red"}; cards(st,[(k.upper(),v,tones[k],"vendedores") for k,v in counts.items()],4)\n'''
text,n=pattern.subn(replacement,text,count=1)
if n!=1: raise SystemExit('bloco do topo executivo não encontrado')

# 6) Vendedor individual: dois grupos e hierarquia.
pattern=re.compile(r'''        cards\(st,\[\(\"VENDAS\".*?\]\)\n        st\.markdown\('<div class=\"section\">Relatório geral da equipe</div>''',re.S)
text,n=pattern.subn('        st.markdown(seller_kpis_html(x),unsafe_allow_html=True)\n        st.markdown(\'<div class="section">Relatório geral da equipe</div>\'',text,count=1)
if n!=1: raise SystemExit('bloco de indicadores do vendedor não encontrado')

app.write_text(text,encoding='utf-8')

# 7) Projeção de ADIM: 100% apenas para projeção; premiação atual segue real.
gen=Path('gerar_painel.py')
g=gen.read_text(encoding='utf-8')
old='projected_adim=projected_base*cfg["bonus_adimplencia"]["percentual_bonus"] if item["adim_elegivel"] else 0'
new='projected_adim=projected_base*cfg["bonus_adimplencia"]["percentual_bonus"] if item["elegivel_individual"] else 0'
if old not in g: raise SystemExit('regra projected_adim não encontrada')
g=g.replace(old,new,1)
# Apenas textos visíveis em relatórios/Excel; chaves internas sem acento não são tocadas.
for old,new in {
    'COMISSÃO':'PREMIAÇÃO','Comissão':'Premiação','comissão':'premiação',
    'PRÊMIOS':'SEMANAIS','Prêmios':'Semanais','prêmios':'semanais',
    'BÔNUS ADIM. PROJ.':'BÔNUS (SE) 100% ADIM',
}.items():
    g=g.replace(old,new)
gen.write_text(g,encoding='utf-8')
