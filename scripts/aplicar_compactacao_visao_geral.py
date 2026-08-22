from pathlib import Path

path=Path('app.py')
s=path.read_text(encoding='utf-8')

old='''def executive_kpis_html(cfg,total,projection,neo,team):\n    meta=cfg["meta_empresa"]\n    ating=total/meta if meta else 0\n    faltam=max(0,meta-total)\n    neo_pct=neo/total if total else 0\n    zeros=sum(x["zeros"] for x in team)\n    return (\n        '<div class="exec-grid">'\n        f'<div class="exec-card hero"><small>VENDAS REALIZADAS</small><strong>{total}</strong><span>Resultado atual</span></div>'\n        f'<div class="exec-card"><small>META DO MÊS</small><strong>{meta}</strong><span>Objetivo comercial</span></div>'\n        f'<div class="exec-card projection"><small>PROJEÇÃO</small><strong>{projection}</strong><span>Fechamento estimado</span></div>'\n        f'<div class="exec-card attainment"><small>% DA META</small><strong>{pct(ating)}</strong><span>Atingimento atual</span></div>'\n        f'<div class="exec-card secondary"><small>FALTAM PARA META</small><strong>{faltam}</strong><span>Vendas necessárias</span></div>'\n        f'<div class="exec-card secondary"><small>VENDAS NEO</small><strong>{neo}</strong><span>{pct(neo_pct)} do total</span></div>'\n        f'<div class="exec-card secondary"><small>% NEO</small><strong>{pct(neo_pct)}</strong><span>Participação</span></div>'\n        '</div>'\n    )\n'''
new='''def executive_kpis_html(cfg,total,projection,neo,team):\n    meta=cfg["meta_empresa"]\n    ating=total/meta if meta else 0\n    faltam=max(0,meta-total)\n    neo_pct=neo/total if total else 0\n    return (\n        '<div class="exec-compact-grid">'\n        '<div class="exec-compact-card exec-performance">'\n        '<div class="exec-compact-title">DESEMPENHO DE VENDAS</div>'\n        '<div class="exec-performance-values">'\n        f'<div class="exec-main-value"><small>VENDAS</small><strong>{total}</strong></div>'\n        f'<div><small>PROJEÇÃO</small><strong>{projection}</strong></div>'\n        f'<div><small>% META</small><strong>{pct(ating)}</strong></div>'\n        '</div></div>'\n        '<div class="exec-compact-card exec-goal">'\n        '<div class="exec-compact-title">META</div>'\n        '<div class="exec-pair-values">'\n        f'<div><small>META DO MÊS</small><strong>{meta}</strong></div>'\n        f'<div><small>FALTAM</small><strong>{faltam}</strong></div>'\n        '</div></div>'\n        '<div class="exec-compact-card exec-energy">'\n        '<div class="exec-compact-title">ENERGIA / NEO</div>'\n        '<div class="exec-pair-values">'\n        f'<div><small>VENDAS NEO</small><strong>{neo}</strong></div>'\n        f'<div><small>% NEO</small><strong>{pct(neo_pct)}</strong></div>'\n        '</div></div>'\n        '</div>'\n    )\n'''
if old not in s:
    raise SystemExit('executive_kpis_html antigo não localizado')
s=s.replace(old,new,1)

old_render='''    if area=="VISÃO GERAL":\n        st.markdown(executive_kpis_html(cfg,total,projection,neo,team),unsafe_allow_html=True)\n        st.markdown('<div class="section">Distribuição de performance</div>',unsafe_allow_html=True); counts={k:0 for k in ("Azul","Verde","Amarelo","Vermelho")}\n        for x in team:counts[performance(x["media"])[0]]+=1\n        st.markdown(performance_summary_html(counts),unsafe_allow_html=True)\n        st.markdown('<div class="section">Ranking da equipe</div>',unsafe_allow_html=True)\n'''
new_render='''    if area=="VISÃO GERAL":\n        st.markdown(executive_kpis_html(cfg,total,projection,neo,team),unsafe_allow_html=True)\n        counts={k:0 for k in ("Azul","Verde","Amarelo","Vermelho")}\n        for x in team:counts[performance(x["media"])[0]]+=1\n        st.markdown('<div class="section">Ranking da equipe</div>',unsafe_allow_html=True)\n'''
if old_render not in s:
    raise SystemExit('bloco inicial VISÃO GERAL não localizado')
s=s.replace(old_render,new_render,1)

old_tail='''        st.markdown(production_channel_dashboard_html(channels,total,summary,cfg,data_until,updated),unsafe_allow_html=True)\n        render_general_report(st,team,rows,cfg,summary,all_days,elapsed,official,color)\n'''
new_tail='''        st.markdown(production_channel_dashboard_html(channels,total,summary,cfg,data_until,updated),unsafe_allow_html=True)\n        st.markdown('<div class="section perf-section-compact">Distribuição de performance</div>',unsafe_allow_html=True)\n        st.markdown(performance_summary_html(counts),unsafe_allow_html=True)\n        render_general_report(st,team,rows,cfg,summary,all_days,elapsed,official,color)\n'''
if old_tail not in s:
    raise SystemExit('cauda VISÃO GERAL não localizada')
s=s.replace(old_tail,new_tail,1)

css=r'''
/* Visão Geral compacta — somente layout/agrupamento; cálculos permanecem intactos. */
.exec-compact-grid{display:grid;grid-template-columns:2fr 1fr 1fr;gap:9px;margin:6px 0 10px;align-items:stretch}
.exec-compact-card{background:#fff;border:1px solid var(--line);border-radius:12px;padding:10px 12px;box-shadow:0 2px 9px rgba(15,23,42,.045);min-width:0}
.exec-compact-title{font-size:.58rem;line-height:1;font-weight:900;letter-spacing:.055em;color:#64748B;margin-bottom:8px;text-transform:uppercase}
.exec-performance{background:linear-gradient(120deg,#0F172A,#172554);border-color:#172554;color:#fff}
.exec-performance .exec-compact-title,.exec-performance small,.exec-performance strong{color:#fff}
.exec-performance-values{display:grid;grid-template-columns:1.25fr 1fr 1fr;gap:6px;align-items:end}
.exec-performance-values>div,.exec-pair-values>div{min-width:0}
.exec-performance-values small,.exec-pair-values small{display:block;font-size:.52rem;line-height:1.05;font-weight:850;letter-spacing:.035em;color:#64748B;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.exec-performance-values strong{display:block;font-size:1.42rem;line-height:1.02;margin-top:4px;font-weight:900;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.exec-performance-values .exec-main-value strong{font-size:1.85rem}
.exec-pair-values{display:grid;grid-template-columns:1fr 1fr;gap:7px;align-items:end}
.exec-pair-values strong{display:block;font-size:1.22rem;line-height:1.03;margin-top:4px;color:#0F172A;font-weight:900;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.exec-goal{border-top:3px solid #F59E0B}.exec-energy{border-top:3px solid #0EA5E9}
.perf-section-compact{margin-top:10px!important;margin-bottom:5px!important}
.perf-summary{gap:6px!important;margin:0 0 8px!important}
.perf-chip{min-height:46px!important;padding:6px 9px!important;border-radius:9px!important}
.perf-chip span{font-size:.52rem!important}.perf-chip strong{font-size:1.08rem!important}
@media(max-width:760px){
  .exec-compact-grid{grid-template-columns:1fr 1fr;gap:6px;margin:4px 0 7px}
  .exec-performance{grid-column:1/-1;padding:9px 10px}
  .exec-compact-card{padding:8px 9px;border-radius:10px}
  .exec-compact-title{font-size:.51rem;margin-bottom:6px}
  .exec-performance-values{gap:4px}
  .exec-performance-values small,.exec-pair-values small{font-size:.45rem}
  .exec-performance-values strong{font-size:1.14rem;margin-top:3px}
  .exec-performance-values .exec-main-value strong{font-size:1.48rem}
  .exec-pair-values{gap:4px}
  .exec-pair-values strong{font-size:1rem;margin-top:3px}
  .perf-summary{display:grid!important;grid-template-columns:repeat(2,minmax(0,1fr))!important;gap:4px!important}
  .perf-chip{min-height:39px!important;padding:5px 7px!important}
  .perf-chip strong{font-size:.96rem!important}
}
@media(max-width:340px){
  .exec-performance-values small,.exec-pair-values small{font-size:.41rem}
  .exec-performance-values strong{font-size:1.02rem}.exec-performance-values .exec-main-value strong{font-size:1.34rem}
  .exec-pair-values strong{font-size:.91rem}
}
'''
marker='/* Visão Geral compacta — somente layout/agrupamento; cálculos permanecem intactos. */'
if marker not in s:
    s=s.replace('\n</style>"""',css+'\n</style>"""',1)

path.write_text(s,encoding='utf-8')
