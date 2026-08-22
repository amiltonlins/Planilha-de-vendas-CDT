from pathlib import Path

app=Path('app.py')
text=app.read_text(encoding='utf-8')

# Nomenclatura visível
repls={
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
}
for a,b in repls.items(): text=text.replace(a,b)

# menu visível
text=text.replace('areas=["VISÃO GERAL","VENDEDORES","SEMANAL","PREMIAÇÕES","GESTÃO"]','areas=["VISÃO GERAL","VENDEDORES","SEMANAL","PREMIAÇÕES","GESTÃO"]')
text=text.replace('elif area=="COMISSÕES":','elif area=="PREMIAÇÕES":')

# helpers executivos antes do ranking
marker='def ranking_html(ranking):\n'
helpers='''def executive_kpis_html(cfg,total,projection,neo,team):\n    meta=cfg["meta_empresa"]\n    ating=total/meta if meta else 0\n    faltam=max(0,meta-total)\n    neo_pct=neo/total if total else 0\n    zeros=sum(x["zeros"] for x in team)\n    return f'''<div class="exec-grid">\n      <div class="exec-card hero"><small>VENDAS REALIZADAS</small><strong>{total}</strong><span>Resultado atual</span></div>\n      <div class="exec-card"><small>META DO MÊS</small><strong>{meta}</strong><span>Objetivo comercial</span></div>\n      <div class="exec-card projection"><small>PROJEÇÃO</small><strong>{projection}</strong><span>Fechamento estimado</span></div>\n      <div class="exec-card attainment"><small>% DA META</small><strong>{pct(ating)}</strong><span>Atingimento atual</span></div>\n      <div class="exec-card secondary"><small>FALTAM PARA META</small><strong>{faltam}</strong><span>Vendas necessárias</span></div>\n      <div class="exec-card secondary"><small>VENDAS NEO</small><strong>{neo}</strong><span>{pct(neo_pct)} do total</span></div>\n      <div class="exec-card secondary"><small>% NEO</small><strong>{pct(neo_pct)}</strong><span>Participação</span></div>\n      <div class="exec-card secondary critical"><small>ZEROS</small><strong>{zeros}</strong><span>Dias sem venda</span></div>\n    </div>'''\n\ndef seller_kpis_html(x):\n    meta_pct=x["projecao"]/x["meta_individual"] if x["meta_individual"] else 0\n    status,color,_=performance(x["media"])\n    items=[\n      ("VENDAS",x["vendas"],"Produção","primary"),\n      ("PROJEÇÃO",x["projecao"],f'Meta {x["meta_individual"]}',"level2"),\n      ("MÉDIA/DIA",f'{x["media"]:.2f}',f'{x["dias"]} dias',"level2"),\n      ("% META",pct(meta_pct),status,"level2"),\n      ("ZEROS",x["zeros"],f'Semana {x["zeros_semana"]}',"level3"),\n      ("NEO",x["neo"],"Neoenergia","level3"),\n      ("% NEO",pct(x["neo_pct"]),"Participação","level3"),\n      ("PREMIAÇÃO ATUAL",money(x["base"]),"Já acumulada","primary"),\n      ("PREMIAÇÃO PROJETADA",money(x["comissao_proj"]),"Base projetada","level2"),\n      ("BÔNUS NEO PROJETADO",money(x["bonus_neo_proj"]),"Projeção","level3"),\n      ("BÔNUS (SE) 100% ADIM",money(x["bonus_adim_proj"]),"Condicional","level3"),\n      ("SEMANAIS",money(x["premio_total"]),"Acumulado semanal","level3"),\n      ("TOTAL VARIÁVEL PROJETADO",money(x["total_variavel_proj"]),"Fechamento estimado","primary total"),\n    ]\n    cards=''.join(f'<div class="seller-kpi {cls}"><small>{html.escape(str(label))}</small><strong>{html.escape(str(value))}</strong><span>{html.escape(str(sub))}</span></div>' for label,value,sub,cls in items)\n    return f'<div class="seller-groups"><div class="seller-group-title">DESEMPENHO COMERCIAL</div><div class="seller-kpi-grid">{cards[:0]}'+''.join(f'<div class="seller-kpi {cls}"><small>{html.escape(str(label))}</small><strong>{html.escape(str(value))}</strong><span>{html.escape(str(sub))}</span></div>' for label,value,sub,cls in items[:7])+f'</div><div class="seller-group-title award">PREMIAÇÃO</div><div class="seller-kpi-grid award-grid">'+''.join(f'<div class="seller-kpi {cls}"><small>{html.escape(str(label))}</small><strong>{html.escape(str(value))}</strong><span>{html.escape(str(sub))}</span></div>' for label,value,sub,cls in items[7:])+'</div></div>'\n\n'''
text=text.replace(marker,helpers+marker,1)

# CSS executivo e mobile
css_insert='''\n.exec-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin:8px 0 14px}.exec-card{background:white;border:1px solid var(--line);border-radius:14px;padding:14px 16px;box-shadow:0 2px 10px rgba(15,23,42,.05);min-width:0}.exec-card small{display:block;font-size:.64rem;font-weight:900;letter-spacing:.055em;color:#64748B}.exec-card strong{display:block;font-size:1.8rem;line-height:1.05;margin-top:7px;color:#0F172A;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.exec-card span{display:block;font-size:.67rem;color:#94A3B8;margin-top:5px}.exec-card.hero{grid-column:span 2;background:linear-gradient(120deg,#0F172A,#172554);border-color:#172554}.exec-card.hero small,.exec-card.hero strong,.exec-card.hero span{color:white}.exec-card.hero strong{font-size:2.35rem}.exec-card.projection{border-top:4px solid #F59E0B}.exec-card.attainment{border-top:4px solid #22C55E}.exec-card.critical{border-top:4px solid #EF4444}.seller-groups{margin-top:12px}.seller-group-title{font-size:.72rem;font-weight:900;letter-spacing:.08em;color:#475569;margin:14px 0 7px}.seller-group-title.award{margin-top:18px}.seller-kpi-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:9px}.seller-kpi{background:white;border:1px solid var(--line);border-radius:12px;padding:12px;min-width:0}.seller-kpi small{display:block;font-size:.59rem;font-weight:900;color:#64748B;letter-spacing:.035em}.seller-kpi strong{display:block;font-size:1.2rem;color:#0F172A;margin-top:7px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.seller-kpi span{display:block;font-size:.63rem;color:#94A3B8;margin-top:4px}.seller-kpi.primary{background:#0F172A;border-color:#0F172A}.seller-kpi.primary small,.seller-kpi.primary strong,.seller-kpi.primary span{color:white}.seller-kpi.primary strong{font-size:1.55rem}.seller-kpi.total{background:linear-gradient(120deg,#0F172A,#172554)}\n@media(max-width:900px){.exec-grid{grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}.exec-card.hero{grid-column:span 2}.exec-card.hero strong{font-size:2rem}.seller-kpi-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.rank-inside{grid-template-columns:repeat(2,minmax(0,1fr))}.rank-name{grid-template-columns:1fr}.rank-inside strong{white-space:normal;overflow-wrap:anywhere}.report{font-size:.68rem}}\n@media(max-width:560px){.block-container{padding:.45rem!important}.bi-topbar{border-radius:10px;padding:12px}.exec-grid{grid-template-columns:repeat(2,minmax(0,1fr));gap:7px}.exec-card{padding:11px 10px;border-radius:11px}.exec-card.hero{grid-column:span 2}.exec-card strong{font-size:1.35rem}.exec-card.hero strong{font-size:1.9rem}.exec-card small{font-size:.56rem}.exec-card span{font-size:.58rem}.seller-kpi-grid{grid-template-columns:repeat(2,minmax(0,1fr));gap:7px}.seller-kpi{padding:10px 9px}.seller-kpi strong{font-size:1.05rem}.seller-kpi.primary strong{font-size:1.3rem}.rank-row{grid-template-columns:34px minmax(0,1fr)!important;padding:6px 2px!important}.rank-pos{font-size:.8rem}.rank-name{padding:9px!important;gap:8px!important}.rank-inside{grid-template-columns:repeat(2,minmax(0,1fr))!important}.rank-inside span{min-width:0}.rank-inside strong{font-size:.86rem!important;white-space:normal!important;overflow-wrap:anywhere}.rank-inside .neo-highlight strong{font-size:1.05rem!important}.rank-seller b{white-space:normal!important}.metric strong{white-space:normal;overflow-wrap:anywhere}.stDownloadButton button{width:100%}}\n'''
text=text.replace('</style>',''+css_insert+'\n</style>',1)

# Topo executivo, sem gráfico de evolução
old='''        cards(st,[("META DO MÊS",cfg["meta_empresa"],"yellow","Objetivo comercial"),("VENDAS REALIZADAS",total,"cyan","Histórico acumulado"),("PROJEÇÃO",projection,"yellow","Fechamento estimado"),("% DA META",pct(total/cfg["meta_empresa"] if cfg["meta_empresa"] else 0),"green","Realizado"),("FALTAM PARA META",max(0,cfg["meta_empresa"]-total),"red","Vendas necessárias"),("VENDAS NEO",neo,"cyan","Neoenergia"),("% NEO",pct(neo/total if total else 0),"green","Participação"),("ZEROS",sum(x["zeros"] for x in team),"red","Dias sem venda")])\n        left,right=st.columns([1.7,1],gap="small")\n        with left:\n            st.markdown('<div class="section">Evolução comercial</div>',unsafe_allow_html=True); cumulative,ideal=daily_series(rows,cfg,data_until); st.line_chart({"Realizado acumulado":cumulative,"Ritmo da meta":ideal},height=245)\n        with right:\n            st.markdown('<div class="section">Distribuição de performance</div>',unsafe_allow_html=True); counts={k:0 for k in ("Azul","Verde","Amarelo","Vermelho")}\n            for x in team:counts[performance(x["media"])[0]]+=1\n            tones={"Azul":"cyan","Verde":"green","Amarelo":"yellow","Vermelho":"red"}; cards(st,[(k.upper(),v,tones[k],"vendedores") for k,v in counts.items()],2)\n'''
new='''        st.markdown(executive_kpis_html(cfg,total,projection,neo,team),unsafe_allow_html=True)\n        st.markdown('<div class="section">Distribuição de performance</div>',unsafe_allow_html=True); counts={k:0 for k in ("Azul","Verde","Amarelo","Vermelho")}\n        for x in team:counts[performance(x["media"])[0]]+=1\n        tones={"Azul":"cyan","Verde":"green","Amarelo":"yellow","Vermelho":"red"}; cards(st,[(k.upper(),v,tones[k],"vendedores") for k,v in counts.items()],4)\n'''
if old not in text: raise SystemExit('bloco topo não encontrado')
text=text.replace(old,new,1)

# Vendedor individual: grupos/hierarquia
start='''        cards(st,[("VENDAS",x["vendas"],"cyan",""),("MÉDIA",f'{x["media"]:.2f}',tone,f'{x["dias"]} dias'),("PROJEÇÃO",x["projecao"],tone,f'Meta {x["meta_individual"]}'),("% DA META",pct(x["projecao"]/x["meta_individual"] if x["meta_individual"] else 0),tone,""),("ZEROS",x["zeros"],"red",f'Semana {x["zeros_semana"]}'),("NEO",x["neo"],"cyan",""),("% NEO",pct(x["neo_pct"]),"green",""),("PREMIAÇÃO ATUAL",money(x["base"]),"green",""),("PREMIAÇÃO PROJETADA",money(x["comissao_proj"]),"yellow","Base projetada"),("BÔNUS NEO PROJ.",money(x["bonus_neo_proj"]),"green",""),("BÔNUS (SE) 100% ADIM",money(x["bonus_adim_proj"]),"green",""),("SEMANAIS",money(x["premio_total"]),"green","Acumulados"),("TOTAL VAR. ATUAL",money(x["total"]),"cyan",""),("TOTAL VAR. PROJETADO",money(x["total_variavel_proj"]),"yellow","")])\n'''
if start not in text:
    # tolerate old labels if nomenclature replacement sequence differed
    import re
    text,n=re.subn(r'        cards\(st,\[\(\"VENDAS\".*?\]\)\n', '        st.markdown(seller_kpis_html(x),unsafe_allow_html=True)\n', text, count=1, flags=re.S)
    if n!=1: raise SystemExit('bloco vendedor não encontrado')
else:text=text.replace(start,'        st.markdown(seller_kpis_html(x),unsafe_allow_html=True)\n',1)

# Ranking: textos visíveis específicos
text=text.replace('<small>COMISSÃO ATUAL</small>','<small>PREMIAÇÃO ATUAL</small>')
text=text.replace('<small>COMISSÃO PROJ.</small>','<small>PREMIAÇÃO PROJ.</small>')
text=text.replace('<small>PRÊMIOS</small>','<small>SEMANAIS</small>')
text=text.replace('<small>BÔNUS ADIM. PROJ.</small>','<small>BÔNUS (SE) 100% ADIM</small>')

app.write_text(text,encoding='utf-8')

# Lógica projetada: ADIM integral para projeção, sem mexer na premiação atual
p=Path('gerar_painel.py')
g=p.read_text(encoding='utf-8')
old='projected_adim=projected_base*cfg["bonus_adimplencia"]["percentual_bonus"] if item["adim_elegivel"] else 0'
new='projected_adim=projected_base*cfg["bonus_adimplencia"]["percentual_bonus"] if item["elegivel_individual"] else 0'
if old not in g: raise SystemExit('regra projected_adim não encontrada')
g=g.replace(old,new,1)
# nomenclatura visível no Excel/saídas, preservando chaves internas
for a,b in {
 'COMISSÃO':'PREMIAÇÃO','Comissão':'Premiação','comissão':'premiação',
 'PRÊMIOS':'SEMANAIS','Prêmios':'Semanais','prêmios':'semanais',
 'BÔNUS ADIM. PROJ.':'BÔNUS (SE) 100% ADIM',
}.items():
    # só textos literais de apresentação; as chaves internas não têm acento e não são atingidas
    g=g.replace(a,b)
p.write_text(g,encoding='utf-8')
