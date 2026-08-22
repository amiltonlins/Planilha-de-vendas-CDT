from pathlib import Path

path=Path('app.py')
s=path.read_text(encoding='utf-8')

start=s.index('def channel_summary_html(channels,total):')
end=s.index('\ndef projection_status_visual',start)
new_helpers=r'''def channel_summary_html(channels,total):
    items=(("VENDEDORES FRANQUIA",channels.get("VENDEDORES FRANQUIA",0),"👥","blue"),("CANAL NACIONAL",channels.get("CANAL NACIONAL",0),"🌐","green"))
    cards=[]
    for name,value,icon,tone in items:
        share=value/total if total else 0
        cards.append(f'<div class="pc-channel-card {tone}"><div class="pc-channel-icon">{icon}</div><div class="pc-channel-content"><span>{name}</span><strong>{value}</strong><small>{pct(share)} do total</small><div class="pc-channel-track"><i style="width:{min(100,max(0,share*100)):.1f}%"></i></div></div></div>')
    return '<div class="pc-channel-row">'+''.join(cards)+'</div>'

def team_performance_metrics(summary,team_name,goal):
    local=[]
    for item in summary:
        category=normalize_text(item.get("categoria",""))
        if item.get("equipe")==team_name and item.get("pertence_franquia",True) and category not in {"website","adm","freelance","canal nacional"}:
            local.append(item)
    sales=sum(int(x.get("vendas",0) or 0) for x in local)
    projection=sum(int(x.get("projecao",0) or 0) for x in local)
    elapsed=max((int(x.get("dias",0) or 0) for x in local),default=0)
    planned=max((int(x.get("dias_previstos",0) or 0) for x in local),default=0)
    average=sales/elapsed if elapsed else 0
    missing=max(0,int(goal or 0)-sales)
    remaining=max(0,planned-elapsed)
    needed=missing/remaining if remaining else 0
    attainment=sales/int(goal or 0) if int(goal or 0)>0 else 0
    return {"sales":sales,"projection":projection,"elapsed":elapsed,"planned":planned,"average":average,"missing":missing,"remaining":remaining,"needed":needed,"attainment":attainment}

def team_performance_card_html(title,goal,metrics,tone="internal"):
    width=min(100,max(0,metrics["attainment"]*100))
    return f'''<div class="pc-team-card {tone}"><div class="pc-team-head"><div class="pc-team-title"><span class="pc-team-icon">👥</span><b>{html.escape(title.upper())}</b></div><div class="pc-team-goal">◎ <span>Meta: <b>{int(goal or 0)}</b></span></div></div><div class="pc-team-main"><div class="pc-team-sales"><strong>{metrics["sales"]}</strong><span>VENDAS</span></div><div class="pc-team-progress"><b>{pct(metrics["attainment"])}</b><span>da meta</span><div class="pc-team-track"><i style="width:{width:.1f}%"></i></div></div></div><div class="pc-team-stats"><div><span>MÉDIA DIA</span><strong>{metrics["average"]:.1f}</strong><small>vendas/dia</small></div><div><span>PROJEÇÃO</span><strong>{metrics["projection"]}</strong><small>vendas</small></div><div><span>FALTAM PARA META</span><strong>{metrics["missing"]}</strong><small>vendas</small></div><div><span>NECESSÁRIO POR DIA</span><strong>{metrics["needed"]:.1f}</strong><small>vendas/dia</small></div></div></div>'''

def production_channel_dashboard_html(channels,total,summary,cfg,data_until,updated):
    internal_goal=int(cfg.get("meta_equipe_interna",0) or 0); external_goal=int(cfg.get("meta_equipe_externa",0) or 0)
    internal=team_performance_metrics(summary,"Equipe Interna",internal_goal); external=team_performance_metrics(summary,"Equipe Externa",external_goal)
    elapsed=max(internal["elapsed"],external["elapsed"]); planned=max(internal["planned"],external["planned"])
    first=date(cfg["ano"],cfg["mes"],1)
    return f'''<div class="pc-dashboard">{channel_summary_html(channels,total)}<div class="pc-team-grid">{team_performance_card_html("Equipe Interna",internal_goal,internal,"internal")}{team_performance_card_html("Equipe Externa",external_goal,external,"external")}</div><div class="pc-footer"><div><b>▣ Período considerado:</b> {first:%d/%m/%Y} até {data_until:%d/%m/%Y}<small>Dias trabalhados: {elapsed} de {planned}</small></div><div>As metas das equipes são independentes<small>da meta do mês da empresa.</small></div><div><b>⟳ Atualizado em:</b> {updated:%d/%m/%Y %H:%M}<small>Atualização automática</small></div></div></div>'''
'''
s=s[:start]+new_helpers+s[end:]

start=s.index("        st.markdown('<div class=\"section\">Produção por canal</div>'")
end=s.index('        render_general_report(',start)
new_block='''        st.markdown('<div class="section">Produção por canal</div>',unsafe_allow_html=True); channels={name:0 for name in ("VENDEDORES FRANQUIA","CANAL NACIONAL")}\n        for item in summary:\n            name=channel_name(item)\n            if name in channels:channels[name]+=item["vendas"]\n        st.markdown(production_channel_dashboard_html(channels,total,summary,cfg,data_until,updated),unsafe_allow_html=True)\n'''
s=s[:start]+new_block+s[end:]

new_css=r'''
.pc-dashboard{background:#fff;border:1px solid #E2E8F0;border-radius:15px;padding:16px;box-shadow:0 4px 18px rgba(15,23,42,.045)}.pc-channel-row{display:grid;grid-template-columns:repeat(2,minmax(0,350px));gap:12px;margin-bottom:16px}.pc-channel-card{display:flex;align-items:center;gap:12px;background:#F8FAFC;border:1px solid #DCE4EF;border-radius:12px;padding:12px 14px;min-width:0}.pc-channel-icon{width:42px;height:42px;border-radius:50%;display:flex;align-items:center;justify-content:center;background:#E8EEFF;font-size:1.2rem;flex:0 0 auto}.pc-channel-card.green .pc-channel-icon{background:#E8F7ED}.pc-channel-content{flex:1;min-width:0}.pc-channel-content span{display:block;font-size:.62rem;font-weight:900;color:#52627B;letter-spacing:.045em}.pc-channel-content strong{display:block;font-size:1.65rem;line-height:1.05;color:#101828;margin:5px 0 3px}.pc-channel-content small{font-size:.67rem;color:#7C8DA8}.pc-channel-track{height:5px;background:#E5E7EB;border-radius:99px;margin-top:8px;overflow:hidden}.pc-channel-track i{display:block;height:100%;border-radius:99px;background:#4F6FE8}.pc-channel-card.green .pc-channel-track i{background:#2E9D55}.pc-team-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}.pc-team-card{border:1px solid #E2E8F0;border-top:3px solid #6D4BC3;border-radius:13px;padding:14px;background:#fff;min-width:0}.pc-team-card.external{border-top-color:#24974B}.pc-team-head{display:flex;align-items:center;justify-content:space-between;gap:12px}.pc-team-title{display:flex;align-items:center;gap:9px;color:#6844B8;font-size:.78rem}.pc-team-card.external .pc-team-title{color:#248B45}.pc-team-icon{display:inline-flex;width:33px;height:33px;align-items:center;justify-content:center;border-radius:50%;background:#F1ECFA}.pc-team-card.external .pc-team-icon{background:#E7F5EC}.pc-team-goal{font-size:.71rem;color:#6844B8;white-space:nowrap}.pc-team-card.external .pc-team-goal{color:#248B45}.pc-team-main{display:grid;grid-template-columns:1fr .75fr;align-items:center;gap:18px;padding:15px 4px 14px;border-bottom:1px solid #E8EDF4}.pc-team-sales{display:flex;align-items:flex-end;gap:10px}.pc-team-sales strong{font-size:2.75rem;line-height:.92;color:#101828;font-weight:950}.pc-team-sales span{font-size:.64rem;font-weight:900;color:#5E6B82;padding-bottom:5px}.pc-team-progress{text-align:right}.pc-team-progress b{font-size:.82rem;color:#6844B8}.pc-team-card.external .pc-team-progress b{color:#248B45}.pc-team-progress span{font-size:.66rem;color:#64748B;margin-left:4px}.pc-team-track{height:6px;background:#E8EBF0;border-radius:99px;margin-top:9px;overflow:hidden}.pc-team-track i{display:block;height:100%;background:#6D4BC3;border-radius:99px}.pc-team-card.external .pc-team-track i{background:#24974B}.pc-team-stats{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));padding-top:13px}.pc-team-stats>div{text-align:center;padding:0 8px;border-right:1px solid #E2E8F0;min-width:0}.pc-team-stats>div:last-child{border-right:0}.pc-team-stats span{display:block;font-size:.55rem;font-weight:900;color:#52627B;white-space:nowrap}.pc-team-stats strong{display:block;font-size:1.32rem;color:#6844B8;margin:7px 0 2px}.pc-team-card.external .pc-team-stats strong{color:#248B45}.pc-team-stats small{font-size:.58rem;color:#7788A2}.pc-footer{display:grid;grid-template-columns:1.15fr 1fr 1fr;gap:18px;margin-top:14px;padding:11px 14px;background:#F8FAFC;border:1px solid #E2E8F0;border-radius:11px;font-size:.66rem;color:#334155}.pc-footer small{display:block;margin-top:3px;color:#718096}@media(max-width:700px){.pc-dashboard{padding:10px}.pc-channel-row{grid-template-columns:1fr 1fr;gap:7px;margin-bottom:10px}.pc-channel-card{padding:9px}.pc-channel-icon{display:none}.pc-channel-content strong{font-size:1.35rem}.pc-team-grid{grid-template-columns:1fr;gap:9px}.pc-team-card{padding:11px}.pc-team-sales strong{font-size:2.2rem}.pc-team-stats span{white-space:normal;font-size:.49rem}.pc-team-stats strong{font-size:1.12rem}.pc-footer{grid-template-columns:1fr;gap:7px;font-size:.60rem}.pc-footer>div:nth-child(2){display:none}}@media(max-width:360px){.pc-team-stats{grid-template-columns:repeat(2,1fr);row-gap:10px}.pc-team-stats>div:nth-child(2){border-right:0}}
'''
marker='</style>"""'; pos=s.find(marker)
if pos==-1:raise SystemExit('CSS principal não encontrado')
s=s[:pos]+new_css+s[pos:]
path.write_text(s,encoding='utf-8')
