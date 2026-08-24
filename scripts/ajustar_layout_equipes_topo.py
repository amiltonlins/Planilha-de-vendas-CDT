from pathlib import Path
import re

path=Path('app.py')
text=path.read_text(encoding='utf-8')

# 1) Produção por canal: manter somente os cards de Equipe Interna e Equipe Externa,
# preservando os cálculos existentes e removendo apenas a apresentação dos canais gerais.
old_return='''def production_channel_dashboard_html(channels,total,summary,cfg,data_until,updated):
    internal_goal=int(cfg.get("meta_equipe_interna",0) or 0); external_goal=int(cfg.get("meta_equipe_externa",0) or 0)
    internal=team_performance_metrics(summary,"Equipe Interna",internal_goal); external=team_performance_metrics(summary,"Equipe Externa",external_goal)
    return f'''<div class="pc-dashboard">{channel_summary_html(channels,total)}<div class="pc-team-grid">{team_performance_card_html("Equipe Interna",internal_goal,internal,"internal")}{team_performance_card_html("Equipe Externa",external_goal,external,"external")}</div></div>'''
'''
new_return='''def team_performance_distribution(items,team_name):
    counts={k:0 for k in ("Azul","Verde","Amarelo","Vermelho")}
    for item in items:
        if item.get("equipe")!=team_name:
            continue
        classification=performance(item.get("media",0))[0]
        if classification in counts:
            counts[classification]+=1
    return counts


def team_performance_distribution_html(counts):
    colors=(("Azul","#0891B2"),("Verde","#16A34A"),("Amarelo","#F59E0B"),("Vermelho","#DC2626"))
    parts=''.join(
        f'<span class="pc-team-perf-item"><i style="background:{color}"></i><b>{counts.get(label,0)}</b></span>'
        for label,color in colors
    )
    return f'<div class="pc-team-performance"><small>PERFORMANCE DA EQUIPE</small><div>{parts}</div></div>'


def production_channel_dashboard_html(channels,total,summary,cfg,data_until,updated,visible_team=None):
    internal_goal=int(cfg.get("meta_equipe_interna",0) or 0); external_goal=int(cfg.get("meta_equipe_externa",0) or 0)
    internal=team_performance_metrics(summary,"Equipe Interna",internal_goal); external=team_performance_metrics(summary,"Equipe Externa",external_goal)
    visible_team=visible_team or []
    internal_perf=team_performance_distribution(visible_team,"Equipe Interna")
    external_perf=team_performance_distribution(visible_team,"Equipe Externa")
    return f'''<div class="pc-dashboard pc-dashboard-teams-only"><div class="pc-team-grid">{team_performance_card_html("Equipe Interna",internal_goal,internal,"internal",internal_perf)}{team_performance_card_html("Equipe Externa",external_goal,external,"external",external_perf)}</div></div>'''
'''
if old_return not in text:
    raise SystemExit('Bloco production_channel_dashboard_html esperado não encontrado.')
text=text.replace(old_return,new_return,1)

# 2) Integrar a distribuição de performance no card de cada equipe.
old_card='''def team_performance_card_html(title,goal,metrics,tone="internal"):
    width=min(100,max(0,metrics["attainment"]*100))
    return f'''<div class="pc-team-card {tone}"><div class="pc-team-head"><div class="pc-team-title"><b>{html.escape(title.upper())}</b></div><div class="pc-team-goal"><span>META</span><b>{int(goal or 0)}</b></div></div><div class="pc-team-main"><div class="pc-team-sales"><strong>{metrics["sales"]}</strong><span>VENDAS</span></div><div class="pc-team-progress"><b>{pct(metrics["attainment"])}</b><span>DA META</span><div class="pc-team-track"><i style="width:{width:.1f}%"></i></div></div></div><div class="pc-team-stats"><div><span>MÉDIA/DIA</span><strong>{metrics["average"]:.1f}</strong></div><div><span>PROJEÇÃO</span><strong>{metrics["projection"]}</strong></div><div><span>FALTAM</span><strong>{metrics["missing"]}</strong></div><div><span>NECESSÁRIO/DIA</span><strong>{metrics["needed"]:.1f}</strong></div></div></div>'''
'''
new_card='''def team_performance_card_html(title,goal,metrics,tone="internal",performance_counts=None):
    width=min(100,max(0,metrics["attainment"]*100))
    perf_html=team_performance_distribution_html(performance_counts or {})
    return f'''<div class="pc-team-card {tone}"><div class="pc-team-head"><div class="pc-team-title"><b>{html.escape(title.upper())}</b></div><div class="pc-team-goal"><span>META</span><b>{int(goal or 0)}</b></div></div><div class="pc-team-main"><div class="pc-team-sales"><strong>{metrics["sales"]}</strong><span>VENDAS</span></div><div class="pc-team-progress"><b>{pct(metrics["attainment"])}</b><span>DA META</span><div class="pc-team-track"><i style="width:{width:.1f}%"></i></div></div></div><div class="pc-team-stats"><div><span>MÉDIA/DIA</span><strong>{metrics["average"]:.1f}</strong></div><div><span>PROJEÇÃO</span><strong>{metrics["projection"]}</strong></div><div><span>FALTAM</span><strong>{metrics["missing"]}</strong></div><div><span>NECESSÁRIO/DIA</span><strong>{metrics["needed"]:.1f}</strong></div></div>{perf_html}</div>'''
'''
if old_card not in text:
    raise SystemExit('Bloco team_performance_card_html esperado não encontrado.')
text=text.replace(old_card,new_card,1)

# 3) Remover painel independente de performance e passar a equipe visível para os cards.
old_view='''        counts={k:0 for k in ("Azul","Verde","Amarelo","Vermelho")}
        for x in team:counts[performance(x["media"])[0]]+=1
        st.markdown('<div class="section">Ranking da equipe</div>',unsafe_allow_html=True)'''
new_view='''        st.markdown('<div class="section">Ranking da equipe</div>',unsafe_allow_html=True)'''
if old_view not in text:
    raise SystemExit('Bloco de contagem independente de performance não encontrado.')
text=text.replace(old_view,new_view,1)

old_channel='''        st.markdown(production_channel_dashboard_html(channels,total,summary,cfg,data_until,updated),unsafe_allow_html=True)
        st.markdown('<div class="section perf-section-compact">Distribuição de performance</div>',unsafe_allow_html=True)
        st.markdown(performance_summary_html(counts),unsafe_allow_html=True)'''
new_channel='''        st.markdown(production_channel_dashboard_html(channels,total,summary,cfg,data_until,updated,team),unsafe_allow_html=True)'''
if old_channel not in text:
    raise SystemExit('Renderização antiga de Produção/Performance não encontrada.')
text=text.replace(old_channel,new_channel,1)

# 4) CSS final: reduzir estruturalmente o espaço superior e compactar cards por equipe.
# O CSS é injetado imediatamente antes do cabeçalho, ficando depois dos estilos antigos.
anchor='''    with st.container(key="cdt_top_header"):
'''
final_css=r'''    st.markdown("""<style>
/* AJUSTE FINAL ESTRUTURAL DE TOPO + PERFORMANCE POR EQUIPE - 2026-08 */
html,body{margin:0!important;padding:0!important}
[data-testid="stAppViewContainer"],
[data-testid="stAppViewContainer"]>.main,
[data-testid="stMain"],
[data-testid="stMainBlockContainer"],
[data-testid="stAppViewBlockContainer"],
section.main,
section.main>div,
.block-container{
  margin-top:0!important;
  padding-top:.35rem!important;
  min-height:0!important;
}
@media(max-width:900px){
  [data-testid="stMainBlockContainer"],
  [data-testid="stAppViewBlockContainer"],
  section.main>div,
  .block-container{padding-top:.18rem!important}
}
.pc-dashboard-teams-only{padding:10px 12px!important}
.pc-dashboard-teams-only .pc-team-grid{margin:0!important}
.pc-team-performance{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-top:10px;padding-top:9px;border-top:1px solid #E8EDF4}
.pc-team-performance>small{font-size:.56rem;font-weight:850;letter-spacing:.035em;color:#64748B;white-space:nowrap}
.pc-team-performance>div{display:flex;align-items:center;gap:10px}
.pc-team-perf-item{display:inline-flex;align-items:center;gap:4px;color:#334155}
.pc-team-perf-item i{display:inline-block;width:8px;height:8px;border-radius:50%;flex:none}
.pc-team-perf-item b{font-size:.74rem;font-weight:900;line-height:1}
@media(max-width:700px){
  .pc-dashboard-teams-only{padding:8px!important}
  .pc-team-performance{margin-top:8px;padding-top:7px;gap:6px}
  .pc-team-performance>small{font-size:.49rem}
  .pc-team-performance>div{gap:7px}
  .pc-team-perf-item{gap:3px}
  .pc-team-perf-item i{width:7px;height:7px}
  .pc-team-perf-item b{font-size:.68rem}
}
@media(max-width:360px){
  .pc-team-performance{align-items:flex-start;flex-direction:column;gap:5px}
}
</style>""",unsafe_allow_html=True)

'''
if anchor not in text:
    raise SystemExit('Âncora do cabeçalho não encontrada para CSS final.')
if 'AJUSTE FINAL ESTRUTURAL DE TOPO + PERFORMANCE POR EQUIPE - 2026-08' not in text:
    text=text.replace(anchor,final_css+anchor,1)

path.write_text(text,encoding='utf-8')
print('Layout de topo, produção por canal e performance por equipe ajustados.')
