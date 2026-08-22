from pathlib import Path


def replace_once(text, old, new, label):
    if old not in text:
        raise SystemExit(f"Trecho não encontrado: {label}")
    return text.replace(old, new, 1)

# ---------------- gerar_painel.py ----------------
p = Path("gerar_painel.py")
t = p.read_text(encoding="utf-8")

t = replace_once(
    t,
    '        item.update({"cenario_projetado":projected_scenario,"taxa_proj":projected_rate,"base_proj":projected_base,"comissao_proj":projected_base+projected_neo+projected_adim+item["premio_total"]})',
    '        item.update({"cenario_projetado":projected_scenario,"taxa_proj":projected_rate,"base_proj":projected_base,"comissao_proj":projected_base,"bonus_neo_proj":projected_neo,"bonus_adim_proj":projected_adim,"total_variavel_proj":projected_base+projected_neo+projected_adim+item["premio_total"]})',
    "campos projetados",
)

t = replace_once(
    t,
    '    report_summary=[x for x in summary if x.get("elegivel_individual",True)]; sheets=[]; n=len(report_summary)+4; week_count=max((len(x["semanas"]) for x in report_summary),default=5)',
    '    report_summary=sorted([x for x in summary if x.get("elegivel_individual",True)],key=lambda x:(x["vendas"],x["projecao"]),reverse=True); sheets=[]; n=len(report_summary)+4; week_count=max((len(x["semanas"]) for x in report_summary),default=5)',
    "ordenacao relatorio excel",
)

t = replace_once(
    t,
    '("COMISSÃO PROJETADA",sum(x["comissao_proj"] for x in summary),15),("PRÊMIOS ACUMULADOS",sum(x["premio_total"] for x in summary),15)',
    '("COMISSÃO PROJETADA",sum(x["comissao_proj"] for x in summary),15),("TOTAL VAR. PROJETADO",sum(x["total_variavel_proj"] for x in summary),15),("PRÊMIOS ACUMULADOS",sum(x["premio_total"] for x in summary),15)',
    "kpi total projetado excel",
)

t = replace_once(
    t,
    '    comm=Sheet("COMISSOES",{1:24,**{i:18 for i in range(2,14)}},freeze="A5",autofilter=f"A4:M{n}"); title(comm,"COMISSÕES E REMUNERAÇÃO",f"Cenário oficial: {\'empresa >= 1.000\' if official==\'maior_ou_igual_1000\' else \'empresa < 1.000\'}","M"); comm.add([]); header(comm,["Vendedor","Vendas","Mínimo","R$/venda","Base","Bônus Neo","Bônus adimpl.","Prêmios","Total","Projetada","Próxima faixa","Faltam","Ganho adicional"])\n    for x in report_summary: comm.add([x["vendedor"],x["vendas"],x["minimo"],x["taxa"],x["base"],x["bonus_neo"],x["bonus_adim"],x["premio_total"],x["total"],x["comissao_proj"],x["proxima"],x["faltam_proxima"],x["ganho_proxima"]],{i:5 for i in range(4,11)}|{13:5})\n    comm.color_scale(f"I5:I{n}"); sheets.append(comm)',
    '    comm=Sheet("COMISSOES",{1:24,**{i:18 for i in range(2,17)}},freeze="A5",autofilter=f"A4:P{n}"); title(comm,"COMISSÕES E REMUNERAÇÃO",f"Cenário oficial: {\'empresa >= 1.000\' if official==\'maior_ou_igual_1000\' else \'empresa < 1.000\'}","P"); comm.add([]); header(comm,["Vendedor","Vendas","Mínimo","R$/venda","Base atual","Bônus Neo atual","Bônus adimpl. atual","Prêmios acumulados","Total atual","Comissão projetada","Bônus Neo proj.","Bônus adimpl. proj.","Total variável projetado","Próxima faixa","Faltam","Ganho adicional"])\n    for x in report_summary: comm.add([x["vendedor"],x["vendas"],x["minimo"],x["taxa"],x["base"],x["bonus_neo"],x["bonus_adim"],x["premio_total"],x["total"],x["comissao_proj"],x["bonus_neo_proj"],x["bonus_adim_proj"],x["total_variavel_proj"],x["proxima"],x["faltam_proxima"],x["ganho_proxima"]],{i:5 for i in range(4,14)}|{16:5})\n    comm.color_scale(f"I5:I{n}"); sheets.append(comm)',
    "aba comissoes excel",
)

p.write_text(t, encoding="utf-8")

# ---------------- app.py ----------------
p = Path("app.py")
t = p.read_text(encoding="utf-8")

t = replace_once(
    t,
    '''def ranking_html(ranking):\n    medals=("🥇","🥈","🥉")\n    rows=[]\n    for i,x in enumerate(ranking[:8]):\n        status,color,_=performance(x["projecao"],x["meta_individual"])\n        medal=medals[i] if i<3 else f"{i+1}º"\n        rows.append(\n            f'<div class="rank-row"><div class="rank-pos">{medal}</div>'\n            f'<div class="rank-name"><b>{html.escape(x["vendedor"])}</b><small>{html.escape(x["setor"])}</small></div>'\n            f'<div class="rank-kpi"><b>{x["vendas"]}</b><small>vendas</small></div>'\n            f'<div class="rank-kpi"><b>{x["neo"]}</b><small>NEO</small></div>'\n            f'<div class="rank-kpi"><b>{pct(x["neo_pct"])}</b><small>% NEO</small></div>'\n            f'<div class="rank-status" style="color:{color};background:{color}16;border-color:{color}44">{status}</div></div>'\n        )\n    return '<div class="rank-card">'+''.join(rows)+'</div>' if rows else '<div class="empty-bi">Nenhum vendedor local ativo para exibir no ranking.</div>'\n''',
    '''def ranking_html(ranking):\n    medals=("🥇","🥈","🥉")\n    rows=[]\n    for i,x in enumerate(ranking[:8]):\n        _,color,_=performance(x["projecao"],x["meta_individual"])\n        medal=medals[i] if i<3 else f"{i+1}º"\n        rows.append(\n            f'<div class="rank-row"><div class="rank-pos">{medal}</div>'\n            f'<div class="rank-name" style="background:{color}"><b>{html.escape(x["vendedor"])}</b><small>{html.escape(x["setor"])}</small></div>'\n            f'<div class="rank-kpi"><b>{x["vendas"]}</b><small>vendas</small></div>'\n            f'<div class="rank-kpi"><b>{x["projecao"]}</b><small>projeção</small></div>'\n            f'<div class="rank-kpi"><b>{x["neo"]}</b><small>NEO</small></div>'\n            f'<div class="rank-kpi"><b>{pct(x["neo_pct"])}</b><small>% NEO</small></div></div>'\n        )\n    return '<div class="rank-card">'+''.join(rows)+'</div>' if rows else '<div class="empty-bi">Nenhum vendedor local ativo para exibir no ranking.</div>'\n''',
    "ranking",
)

t = replace_once(
    t,
    '.rank-row{display:grid;grid-template-columns:54px minmax(180px,1.5fr) 90px 75px 90px 105px;align-items:center;gap:8px;padding:10px 13px;border-bottom:1px solid #EEF2F7}.rank-row:last-child{border-bottom:0}.rank-pos{font-weight:900;text-align:center}.rank-name{display:flex;flex-direction:column;min-width:0}.rank-name b{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-size:.81rem}.rank-name small,.rank-kpi small{font-size:.62rem;color:#94A3B8}.rank-kpi{display:flex;flex-direction:column;text-align:center}.rank-kpi b{font-size:.87rem}.rank-status{font-size:.68rem;font-weight:800;text-align:center;border:1px solid;border-radius:999px;padding:4px 7px}',
    '.rank-row{display:grid;grid-template-columns:54px minmax(190px,1.55fr) 82px 82px 72px 88px;align-items:center;gap:8px;padding:9px 13px;border-bottom:1px solid #EEF2F7}.rank-row:last-child{border-bottom:0}.rank-pos{font-weight:900;text-align:center}.rank-name{display:flex;flex-direction:column;min-width:0;padding:8px 10px;border-radius:9px;color:white;box-shadow:0 2px 7px rgba(15,23,42,.10)}.rank-name b{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-size:.81rem}.rank-name small{font-size:.62rem;color:rgba(255,255,255,.82)}.rank-kpi small{font-size:.62rem;color:#94A3B8}.rank-kpi{display:flex;flex-direction:column;text-align:center}.rank-kpi b{font-size:.87rem}',
    "css ranking",
)

t = replace_once(
    t,
    '@media(max-width:1100px){.block-container{padding:.7rem}.rank-row{grid-template-columns:45px minmax(150px,1fr) 70px 65px 80px}.metric strong{font-size:1.35rem}}',
    '@media(max-width:1100px){.block-container{padding:.7rem}.rank-row{grid-template-columns:45px minmax(150px,1fr) 65px 68px 60px 75px}.metric strong{font-size:1.35rem}}',
    "css responsive ranking",
)

t = replace_once(
    t,
    '        st.markdown(\'<div class="section">Relatório geral da equipe</div>\',unsafe_allow_html=True); cols=[("setor","SETOR"),("vendedor","VENDEDOR"),("vendas","TOTAL"),("projecao","PROJEÇÃO"),("media","MÉDIA"),("zeros","ZEROS"),("meta_pct","% META"),("neo","NEO"),("neo_pct_fmt","% NEO"),("base_fmt","COMISSÃO ATUAL"),("proj_fmt","COMISSÃO PROJETADA")]+[(d.day,str(d.day)) for d in all_days]; display=[]\n        for x in team:display.append(x|{"media":f\'{x["media"]:.2f}\',"meta_pct":pct(x["projecao"]/x["meta_individual"] if x["meta_individual"] else 0),"neo_pct_fmt":pct(x["neo_pct"]),"base_fmt":money(x["base"]),"proj_fmt":money(x["comissao_proj"])})',
    '        st.markdown(\'<div class="section">Relatório geral da equipe</div>\',unsafe_allow_html=True); cols=[("setor","SETOR"),("vendedor","VENDEDOR"),("vendas","TOTAL"),("projecao","PROJEÇÃO"),("media","MÉDIA"),("zeros","ZEROS"),("meta_pct","% META"),("neo","NEO"),("neo_pct_fmt","% NEO"),("base_fmt","COMISSÃO ATUAL"),("proj_fmt","COMISSÃO PROJETADA"),("neo_proj_fmt","BÔNUS NEO PROJ."),("adim_proj_fmt","BÔNUS ADIM. PROJ."),("premio_fmt","PRÊMIOS"),("total_proj_fmt","TOTAL VAR. PROJ.")]+[(d.day,str(d.day)) for d in all_days]; display=[]\n        for x in sorted(team,key=lambda x:(x["vendas"],x["projecao"]),reverse=True):display.append(x|{"media":f\'{x["media"]:.2f}\',"meta_pct":pct(x["projecao"]/x["meta_individual"] if x["meta_individual"] else 0),"neo_pct_fmt":pct(x["neo_pct"]),"base_fmt":money(x["base"]),"proj_fmt":money(x["comissao_proj"]),"neo_proj_fmt":money(x["bonus_neo_proj"]),"adim_proj_fmt":money(x["bonus_adim_proj"]),"premio_fmt":money(x["premio_total"]),"total_proj_fmt":money(x["total_variavel_proj"])})',
    "relatorio geral web",
)

t = replace_once(
    t,
    '("COMISSÃO PROJETADA",money(x["comissao_proj"]),"yellow",""),("PRÊMIOS",money(x["premio_total"]),"green",""),("TOTAL VARIÁVEL",money(x["total"]),"green","")',
    '("COMISSÃO PROJETADA",money(x["comissao_proj"]),"yellow","Base projetada"),("BÔNUS NEO PROJ.",money(x["bonus_neo_proj"]),"green",""),("BÔNUS ADIM. PROJ.",money(x["bonus_adim_proj"]),"green",""),("PRÊMIOS",money(x["premio_total"]),"green","Acumulados"),("TOTAL VAR. ATUAL",money(x["total"]),"cyan",""),("TOTAL VAR. PROJETADO",money(x["total_variavel_proj"]),"yellow","")',
    "cards vendedor",
)

t = replace_once(
    t,
    '        cards(st,[("CENÁRIO ATUAL","≥ 1.000" if official=="maior_ou_igual_1000" else "< 1.000","cyan",f"{total} vendas"),("CENÁRIO PROJETADO","≥ 1.000" if projected=="maior_ou_igual_1000" else "< 1.000","yellow",f"{projection} vendas"),("COMISSÃO BASE",money(sum(x["base"] for x in team)),"cyan",""),("BÔNUS NEO",money(sum(x["bonus_neo"] for x in team)),"green",""),("BÔNUS ADIM.",money(sum(x["bonus_adim"] for x in team)),"green",""),("PRÊMIOS",money(sum(x["premio_total"] for x in team)),"yellow",""),("TOTAL VARIÁVEL",money(sum(x["total"] for x in team)),"green",""),("TOTAL PROJETADO",money(sum(x["comissao_proj"] for x in team)),"yellow","")])\n        st.dataframe([{"Vendedor":x["vendedor"],"Vendas":x["vendas"],"Mínimo":x["minimo"],"R$/venda":x["taxa"],"Base":x["base"],"Bônus Neo":x["bonus_neo"],"Bônus M2":x["bonus_adim"],"Prêmios":x["premio_total"],"Total":x["total"],"Projetada":x["comissao_proj"]} for x in team],use_container_width=True,hide_index=True)',
    '        cards(st,[("CENÁRIO ATUAL","≥ 1.000" if official=="maior_ou_igual_1000" else "< 1.000","cyan",f"{total} vendas"),("CENÁRIO PROJETADO","≥ 1.000" if projected=="maior_ou_igual_1000" else "< 1.000","yellow",f"{projection} vendas"),("COMISSÃO BASE ATUAL",money(sum(x["base"] for x in team)),"cyan",""),("COMISSÃO PROJETADA",money(sum(x["comissao_proj"] for x in team)),"yellow","Base projetada"),("BÔNUS NEO PROJ.",money(sum(x["bonus_neo_proj"] for x in team)),"green",""),("BÔNUS ADIM. PROJ.",money(sum(x["bonus_adim_proj"] for x in team)),"green",""),("PRÊMIOS ACUMULADOS",money(sum(x["premio_total"] for x in team)),"cyan",""),("TOTAL VAR. PROJETADO",money(sum(x["total_variavel_proj"] for x in team)),"yellow","")])\n        st.dataframe([{"Vendedor":x["vendedor"],"Vendas":x["vendas"],"Projeção":x["projecao"],"Mínimo":x["minimo"],"R$/venda":x["taxa"],"Base atual":x["base"],"Comissão projetada":x["comissao_proj"],"Bônus Neo proj.":x["bonus_neo_proj"],"Bônus M2 proj.":x["bonus_adim_proj"],"Prêmios":x["premio_total"],"Total atual":x["total"],"Total var. projetado":x["total_variavel_proj"]} for x in sorted(team,key=lambda x:(x["vendas"],x["projecao"]),reverse=True)],use_container_width=True,hide_index=True)',
    "pagina comissoes",
)

p.write_text(t, encoding="utf-8")
