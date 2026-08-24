from pathlib import Path
import re

path=Path('app.py')
text=path.read_text(encoding='utf-8')

# Substitui o card da equipe sem tocar nos cálculos existentes.
card_pattern=r'def team_performance_card_html\(title,goal,metrics,tone="internal"\):\n.*?\n\ndef production_channel_dashboard_html'
card_replacement="""def team_performance_distribution(items,team_name):
    counts={k:0 for k in (\"Azul\",\"Verde\",\"Amarelo\",\"Vermelho\")}
    for item in items:
        if item.get(\"equipe\")!=team_name:
            continue
        classification=performance(item.get(\"media\",0))[0]
        if classification in counts:
            counts[classification]+=1
    return counts


def team_performance_distribution_html(counts):
    colors=((\"Azul\",\"#0891B2\"),(\"Verde\",\"#16A34A\"),(\"Amarelo\",\"#F59E0B\"),(\"Vermelho\",\"#DC2626\"))
    parts=''.join(
        f'<span class=\"pc-team-perf-item\"><i style=\"background:{color}\"></i><b>{counts.get(label,0)}</b></span>'
        for label,color in colors
    )
    return f'<div class=\"pc-team-performance\"><small>PERFORMANCE DA EQUIPE</small><div>{parts}</div></div>'


def team_performance_card_html(title,goal,metrics,tone=\"internal\",performance_counts=None):
    width=min(100,max(0,metrics[\"attainment\"]*100))
    perf_html=team_performance_distribution_html(performance_counts or {})
    return f'''<div class=\"pc-team-card {tone}\"><div class=\"pc-team-head\"><div class=\"pc-team-title\"><b>{html.escape(title.upper())}</b></div><div class=\"pc-team-goal\"><span>META</span><b>{int(goal or 0)}</b></div></div><div class=\"pc-team-main\"><div class=\"pc-team-sales\"><strong>{metrics[\"sales\"]}</strong><span>VENDAS</span></div><div class=\"pc-team-progress\"><b>{pct(metrics[\"attainment\"])}</b><span>DA META</span><div class=\"pc-team-track\"><i style=\"width:{width:.1f}%\"></i></div></div></div><div class=\"pc-team-stats\"><div><span>MÉDIA/DIA</span><strong>{metrics[\"average\"]:.1f}</strong></div><div><span>PROJEÇÃO</span><strong>{metrics[\"projection\"]}</strong></div><div><span>FALTAM</span><strong>{metrics[\"missing\"]}</strong></div><div><span>NECESSÁRIO/DIA</span><strong>{metrics[\"needed\"]:.1f}</strong></div></div>{perf_html}</div>'''


def production_channel_dashboard_html"""
text,count=re.subn(card_pattern,card_replacement,text,flags=re.S)
if count!=1:
    raise SystemExit(f'Falha ao substituir card de equipe: {count}')

# Produção por canal: remove apenas a apresentação dos blocos Vendedores Franquia/Canal Nacional.
prod_pattern=r'def production_channel_dashboard_html\(channels,total,summary,cfg,data_until,updated\):\n.*?\n\ndef weekly_rank_html'
prod_replacement="""def production_channel_dashboard_html(channels,total,summary,cfg,data_until,updated,visible_team=None):
    internal_goal=int(cfg.get(\"meta_equipe_interna\",0) or 0); external_goal=int(cfg.get(\"meta_equipe_externa\",0) or 0)
    internal=team_performance_metrics(summary,\"Equipe Interna\",internal_goal); external=team_performance_metrics(summary,\"Equipe Externa\",external_goal)
    visible_team=visible_team or []
    internal_perf=team_performance_distribution(visible_team,\"Equipe Interna\")
    external_perf=team_performance_distribution(visible_team,\"Equipe Externa\")
    return f'''<div class=\"pc-dashboard pc-dashboard-teams-only\"><div class=\"pc-team-grid\">{team_performance_card_html(\"Equipe Interna\",internal_goal,internal,\"internal\",internal_perf)}{team_performance_card_html(\"Equipe Externa\",external_goal,external,\"external\",external_perf)}</div></div>'''


def weekly_rank_html"""
text,count=re.subn(prod_pattern,prod_replacement,text,flags=re.S)
if count!=1:
    raise SystemExit(f'Falha ao substituir produção por canal: {count}')

# Remove o painel independente de distribuição e reutiliza o mesmo team já elegível/visível do ranking.
old_counts='''        counts={k:0 for k in ("Azul","Verde","Amarelo","Vermelho")}\n        for x in team:counts[performance(x["media"])[0]]+=1\n'''
if old_counts not in text:
    raise SystemExit('Contagem antiga de performance não encontrada')
text=text.replace(old_counts,'',1)
old_render='''        st.markdown(production_channel_dashboard_html(channels,total,summary,cfg,data_until,updated),unsafe_allow_html=True)\n        st.markdown('<div class="section perf-section-compact">Distribuição de performance</div>',unsafe_allow_html=True)\n        st.markdown(performance_summary_html(counts),unsafe_allow_html=True)'''
new_render='''        st.markdown(production_channel_dashboard_html(channels,total,summary,cfg,data_until,updated,team),unsafe_allow_html=True)'''
if old_render not in text:
    raise SystemExit('Renderização antiga de produção/performance não encontrada')
text=text.replace(old_render,new_render,1)

# Injeta o último CSS do render para vencer regras antigas que ainda reservavam espaço superior.
anchor='    with st.container(key="cdt_top_header"):\n'
css='''    st.markdown("""<style>
/* AJUSTE ESTRUTURAL FINAL DE TOPO + PERFORMANCE POR EQUIPE - 2026-08 */
html,body{margin:0!important;padding:0!important}
[data-testid="stAppViewContainer"],
[data-testid="stAppViewContainer"]>.main,
[data-testid="stMain"],
[data-testid="stMainBlockContainer"],
[data-testid="stAppViewBlockContainer"],
section.main,
section.main>div,
.block-container{margin-top:0!important;padding-top:.30rem!important;min-height:0!important}
[data-testid="stHeader"]{height:0!important;min-height:0!important;max-height:0!important;margin:0!important;padding:0!important}
@media(max-width:900px){
  [data-testid="stMainBlockContainer"],[data-testid="stAppViewBlockContainer"],section.main>div,.block-container{padding-top:.15rem!important}
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
  .pc-team-perf-item{gap:3px}.pc-team-perf-item i{width:7px;height:7px}.pc-team-perf-item b{font-size:.68rem}
}
@media(max-width:360px){.pc-team-performance{align-items:flex-start;flex-direction:column;gap:5px}}
</style>""",unsafe_allow_html=True)

'''
if anchor not in text:
    raise SystemExit('Âncora do cabeçalho não encontrada')
if 'AJUSTE ESTRUTURAL FINAL DE TOPO + PERFORMANCE POR EQUIPE - 2026-08' not in text:
    text=text.replace(anchor,css+anchor,1)

path.write_text(text,encoding='utf-8')
print('Ajustes aplicados com sucesso.')
