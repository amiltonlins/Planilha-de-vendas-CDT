from pathlib import Path
import re

path=Path('app.py')
s=path.read_text(encoding='utf-8')

# Reutiliza exatamente a mesma definição de semanas já existente no motor de cálculos.
s=s.replace('from gerar_painel import ROOT, build_sheets, summarize, tier_value, write_xlsx',
            'from gerar_painel import ROOT, build_sheets, summarize, tier_value, write_xlsx, month_weeks',1)

helpers=r'''

def weekly_current_index(cfg,max_weeks,today=None):
    """Índice visual da semana atual sem alterar a regra de cálculo das semanas."""
    today=today or date.today()
    ranges=month_weeks(int(cfg["ano"]),int(cfg["mes"]))[:max_weeks]
    if not ranges:return 0
    if today.year==int(cfg["ano"]) and today.month==int(cfg["mes"]):
        return next((i for i,(a,b) in enumerate(ranges) if a<=today<=b),max_weeks-1)
    # Competência histórica/futura: usa a data de referência apenas para escolher a aba,
    # sem interferir em nenhum cálculo de vendas ou premiação.
    ref_day=max(1,min(int(cfg.get("dia_referencia",1) or 1),ranges[-1][1].day))
    ref=date(int(cfg["ano"]),int(cfg["mes"]),ref_day)
    return next((i for i,(a,b) in enumerate(ranges) if a<=ref<=b),max_weeks-1)

def weekly_tiers(cfg):
    return sorted(cfg.get("premiacao_semanal",[]),key=lambda x:int(x.get("vendas",0)))

def weekly_game_level(sales,cfg):
    tiers=weekly_tiers(cfg)
    conquered=[i for i,t in enumerate(tiers) if sales>=int(t.get("vendas",0)) and float(t.get("premio",0) or 0)>0]
    if not conquered:return 0
    idx=conquered[-1]
    if len(tiers)<=1:return 1
    # Escala proporcional 1..6; primeira faixa=1 e maior faixa=6.
    return max(1,min(6,1+int(idx*5/(len(tiers)-1))))

def weekly_next_goal(sales,cfg):
    tiers=weekly_tiers(cfg)
    nxt=next((t for t in tiers if int(t.get("vendas",0))>sales),None)
    if not nxt:return None
    target=int(nxt.get("vendas",0)); prize=float(nxt.get("premio",0) or 0)
    return {"target":target,"missing":max(0,target-sales),"prize":prize}

def weekly_week_labels(cfg,max_weeks,current_index):
    labels=[]
    for i in range(max_weeks):
        if i<current_index: labels.append(f"✓ SEMANA {i+1}")
        elif i==current_index: labels.append(f"● SEMANA {i+1} — ATUAL")
        else: labels.append(f"SEMANA {i+1}")
    return labels

def weekly_rank_gamified_html(team,week_index,cfg,is_current):
    ranked=sorted(team,key=lambda x:((x.get("semanas",[])[week_index] if week_index<len(x.get("semanas",[])) else 0),(x.get("premios",[])[week_index] if week_index<len(x.get("premios",[])) else 0)),reverse=True)
    rows=[]
    for pos,x in enumerate(ranked,1):
        sales=int(x.get("semanas",[])[week_index] if week_index<len(x.get("semanas",[])) else 0)
        prize=float(x.get("premios",[])[week_index] if week_index<len(x.get("premios",[])) else 0)
        level=weekly_game_level(sales,cfg) if prize>0 else 0
        emojis='🤑'*level
        target=''
        if is_current:
            nxt=weekly_next_goal(sales,cfg)
            if nxt:
                target=f'<div class="weekly-target">🎯 Faltam <b>{nxt["missing"]}</b> vendas para <b>{money(nxt["prize"])}</b></div>'
            else:
                target='<div class="weekly-target max">🏆 Maior premiação atingida</div>'
        rows.append(
            '<div class="weekly-game-card">'
            f'<div class="weekly-game-head"><span class="weekly-pos">{pos}º</span><b>{html.escape(str(x.get("vendedor","")))}</b><span class="weekly-money-emoji">{emojis}</span></div>'
            f'<div class="weekly-game-main"><div><strong>{sales}</strong><small>VENDAS</small></div><div class="weekly-prize"><strong>{money(prize)}</strong><small>SEMANAL</small></div></div>'
            f'{target}</div>'
        )
    return '<div class="weekly-game-list">'+''.join(rows)+'</div>'

def weekly_management_table_html(team,max_weeks):
    heads=['VENDEDOR']
    for i in range(max_weeks):heads += [f'S{i+1} VENDAS',f'S{i+1} VALOR']
    rows=[]
    for x in sorted(team,key=lambda z:normalize_text(z.get("vendedor",""))):
        cells=[html.escape(str(x.get("vendedor","")))]
        for i in range(max_weeks):
            qty=x.get("semanas",[])[i] if i<len(x.get("semanas",[])) else 0
            prize=x.get("premios",[])[i] if i<len(x.get("premios",[])) else 0
            cells += [str(qty),money(prize)]
        rows.append('<tr>'+''.join(f'<td>{c}</td>' for c in cells)+'</tr>')
    return '<div class="weekly-management-table"><table><thead><tr>'+''.join(f'<th>{h}</th>' for h in heads)+'</tr></thead><tbody>'+''.join(rows)+'</tbody></table></div>'
'''

# Insere as novas funções imediatamente antes do login. As antigas continuam intocadas,
# mas esta camada passa a ser a única usada pela nova experiência SEMANAL.
if 'def weekly_rank_gamified_html' not in s:
    s=s.replace('\ndef render_login(st,cfg):',helpers+'\n\ndef render_login(st,cfg):',1)

weekly_css=r'''
.weekly-game-list{display:grid;gap:7px;margin:9px 0 12px}.weekly-game-card{background:#fff;border:1px solid var(--line);border-radius:12px;padding:10px 12px;box-shadow:0 2px 8px rgba(15,23,42,.035)}.weekly-game-head{display:grid;grid-template-columns:34px minmax(0,1fr) auto;align-items:center;gap:7px}.weekly-game-head b{font-size:.78rem;color:#334155;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.weekly-pos{font-size:.72rem;font-weight:950;color:#64748B}.weekly-money-emoji{font-size:1rem;white-space:nowrap;letter-spacing:-1px}.weekly-game-main{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:6px}.weekly-game-main>div{display:flex;align-items:baseline;gap:6px;background:#F8FAFC;border-radius:8px;padding:6px 8px}.weekly-game-main strong{font-size:1.28rem;line-height:1;color:#0F172A;font-weight:950}.weekly-game-main small{font-size:.52rem;color:#64748B;font-weight:900}.weekly-prize strong{font-size:1.04rem}.weekly-target{margin-top:6px;padding:5px 8px;border-radius:7px;background:#FFF7ED;color:#9A3412;font-size:.64rem;font-weight:750}.weekly-target.max{background:#ECFDF5;color:#166534}.weekly-management-table{overflow:auto;max-height:470px;border:1px solid var(--line);border-radius:10px;background:#fff}.weekly-management-table table{border-collapse:collapse;width:100%;white-space:nowrap;font-size:.68rem}.weekly-management-table th{position:sticky;top:0;background:#0F172A;color:#fff;padding:7px 8px;font-size:.60rem;z-index:1}.weekly-management-table td{padding:6px 8px;border-bottom:1px solid #EEF2F7;border-right:1px solid #EEF2F7;text-align:center}.weekly-management-table td:first-child{text-align:left;font-weight:800;color:#334155}@media(max-width:560px){.weekly-game-list{gap:5px}.weekly-game-card{padding:7px 8px;border-radius:10px}.weekly-game-head{grid-template-columns:27px minmax(0,1fr) auto;gap:5px}.weekly-game-head b{font-size:.72rem}.weekly-pos{font-size:.64rem}.weekly-money-emoji{font-size:.84rem}.weekly-game-main{gap:5px;margin-top:4px}.weekly-game-main>div{padding:5px 6px}.weekly-game-main strong{font-size:1.12rem}.weekly-prize strong{font-size:.94rem}.weekly-game-main small{font-size:.46rem}.weekly-target{font-size:.57rem;margin-top:4px;padding:4px 6px}}
'''
if '.weekly-game-list{' not in s:
    s=s.replace('\n</style>"""',weekly_css+'\n</style>"""',1)

# Move a análise detalhada para Gestão, reutilizando exatamente summary/semanas/premios já calculados.
management_anchor='''    st.markdown("#### CONFERÊNCIA DA IMPORTAÇÃO")'''
management_block='''    st.markdown("#### ACOMPANHAMENTO SEMANAL")\n    st.caption(f'Competência: {int(cfg["mes"]):02d}/{cfg["ano"]} · visão analítica gerencial das mesmas semanas e premiações usadas no ranking.')\n    try:\n        if 'management_summary' not in locals():\n            management_summary,management_days,management_elapsed,management_official=summarize(rows,cfg)\n            apply_team_labels(management_summary,cfg)\n            management_team=regular(management_summary)\n        management_max_weeks=max((len(x.get("semanas",[])) for x in management_team),default=0)\n        if management_max_weeks:\n            st.markdown(weekly_management_table_html(management_team,management_max_weeks),unsafe_allow_html=True)\n            management_sellers=[x["vendedor"] for x in sorted(management_team,key=lambda z:normalize_text(z["vendedor"]))]\n            chosen=st.selectbox("Histórico semanal individual",["SELECIONE UM VENDEDOR"]+management_sellers,key="gestao_weekly_seller")\n            if chosen!="SELECIONE UM VENDEDOR":\n                selected=next((x for x in management_team if x["vendedor"]==chosen),None)\n                if selected:st.markdown(weekly_seller_history_html(selected),unsafe_allow_html=True)\n        else:st.caption("Sem dados semanais nesta competência.")\n    except Exception as exc:\n        st.error(f"Não foi possível montar o acompanhamento semanal: {exc}")\n\n'''
if '#### ACOMPANHAMENTO SEMANAL' not in s:
    s=s.replace(management_anchor,management_block+management_anchor,1)

# Substitui apenas o bloco de apresentação SEMANAL. Nenhuma função de cálculo é modificada.
pattern=r'''    elif area=="SEMANAL":\n.*?(?=    elif area=="PREMIAÇÕES":)'''
replacement='''    elif area=="SEMANAL":\n        st.markdown('<div class="section">Acompanhamento semanal</div>',unsafe_allow_html=True)\n        if not team:st.warning("Nenhum vendedor local ativo.");return\n        max_weeks=max(len(x.get("semanas",[])) for x in team)\n        current_index=weekly_current_index(cfg,max_weeks)\n        week_labels=weekly_week_labels(cfg,max_weeks,current_index)\n        selector_key=f'weekly_week_selector_gamified_{cfg["ano"]}_{cfg["mes"]}_{current_index}'\n        selected_week=st.segmented_control("Semana",week_labels,default=week_labels[current_index],key=selector_key,label_visibility="collapsed") or week_labels[current_index]\n        week_index=week_labels.index(selected_week)\n        is_current=(week_index==current_index)\n        if week_index<current_index:\n            st.caption(f'Semana {week_index+1} encerrada · histórico final')\n        elif is_current:\n            st.caption(f'Semana {week_index+1} atual · ranking em andamento')\n        else:\n            st.caption(f'Semana {week_index+1} · período futuro da competência')\n        st.markdown('<div class="section">Ranking da semana</div>',unsafe_allow_html=True)\n        st.markdown(weekly_rank_gamified_html(team,week_index,cfg,is_current),unsafe_allow_html=True)\n'''
s,new_count=re.subn(pattern,replacement,s,count=1,flags=re.S)
if new_count!=1:
    raise SystemExit('Bloco SEMANAL não localizado para substituição')

path.write_text(s,encoding='utf-8')
