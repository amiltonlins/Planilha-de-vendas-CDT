from pathlib import Path

path=Path('app.py')
s=path.read_text(encoding='utf-8')

# Mantém a mesma lógica de semanas; altera apenas os rótulos para uma forma compacta.
old='''def weekly_week_labels(cfg,max_weeks,current_index):\n    labels=[]\n    for i in range(max_weeks):\n        if i<current_index: labels.append(f"✓ SEMANA {i+1}")\n        elif i==current_index: labels.append(f"● SEMANA {i+1} — ATUAL")\n        else: labels.append(f"SEMANA {i+1}")\n    return labels\n'''
new='''def weekly_week_labels(cfg,max_weeks,current_index):\n    labels=[]\n    for i in range(max_weeks):\n        if i<current_index: labels.append(f"✓ S{i+1}")\n        elif i==current_index: labels.append(f"● S{i+1}")\n        else: labels.append(f"S{i+1}")\n    return labels\n'''
if old not in s:
    raise SystemExit('Função weekly_week_labels não localizada')
s=s.replace(old,new,1)

# Compacta o seletor e remove a legenda redundante abaixo dele.
old_block='''        week_labels=weekly_week_labels(cfg,max_weeks,current_index)\n        selector_key=f'weekly_week_selector_gamified_{cfg["ano"]}_{cfg["mes"]}_{current_index}'\n        selected_week=st.segmented_control("Semana",week_labels,default=week_labels[current_index],key=selector_key,label_visibility="collapsed") or week_labels[current_index]\n        week_index=week_labels.index(selected_week)\n        is_current=(week_index==current_index)\n        if week_index<current_index:\n            st.caption(f'Semana {week_index+1} encerrada · histórico final')\n        elif is_current:\n            st.caption(f'Semana {week_index+1} atual · ranking em andamento')\n        else:\n            st.caption(f'Semana {week_index+1} · período futuro da competência')\n        st.markdown('<div class="section">Ranking da semana</div>',unsafe_allow_html=True)\n'''
new_block='''        week_labels=weekly_week_labels(cfg,max_weeks,current_index)\n        selector_key=f'weekly_week_selector_gamified_{cfg["ano"]}_{cfg["mes"]}_{current_index}'\n        with st.container(key="weekly_week_nav"):\n            selected_week=st.segmented_control("Semana",week_labels,default=week_labels[current_index],key=selector_key,label_visibility="collapsed") or week_labels[current_index]\n            st.markdown(f'<div class="weekly-current-note">ATUAL: S{current_index+1}</div>',unsafe_allow_html=True)\n        week_index=week_labels.index(selected_week)\n        is_current=(week_index==current_index)\n        st.markdown('<div class="section weekly-rank-title">Ranking da semana</div>',unsafe_allow_html=True)\n'''
if old_block not in s:
    raise SystemExit('Bloco do seletor semanal não localizado')
s=s.replace(old_block,new_block,1)

css=r'''
/* Seletor semanal compacto — UI/UX, sem alteração da lógica de semanas. */
.weekly-current-note{display:none}
@media(max-width:700px){
  .st-key-weekly_week_nav{margin:0 0 2px!important;padding:0!important;overflow:hidden!important}
  .st-key-weekly_week_nav [data-testid="stSegmentedControl"]{width:100%!important;min-height:38px!important;overflow-x:auto!important;overflow-y:hidden!important;scrollbar-width:none!important;background:#F1F5F9!important;border:1px solid #E2E8F0!important;border-radius:11px!important;padding:3px!important;box-sizing:border-box!important}
  .st-key-weekly_week_nav [data-testid="stSegmentedControl"]::-webkit-scrollbar{display:none!important}
  .st-key-weekly_week_nav [data-testid="stSegmentedControl"]>div{display:flex!important;flex-wrap:nowrap!important;width:max-content!important;min-width:100%!important;gap:2px!important;background:transparent!important;border:0!important;padding:0!important}
  .st-key-weekly_week_nav [data-testid="stSegmentedControl"] button{flex:1 0 auto!important;min-width:45px!important;min-height:32px!important;height:32px!important;padding:4px 8px!important;border:0!important;border-radius:8px!important;background:transparent!important;color:#64748B!important;font-size:.68rem!important;font-weight:850!important;white-space:nowrap!important;box-shadow:none!important}
  .st-key-weekly_week_nav [data-testid="stSegmentedControl"] button[aria-pressed="true"]{background:#075B35!important;color:#fff!important;font-weight:950!important;box-shadow:0 2px 6px rgba(7,91,53,.18)!important}
  .st-key-weekly_week_nav [data-testid="stSegmentedControl"] button:not([aria-pressed="true"]):hover{background:#E7EFEA!important;color:#075B35!important}
  .weekly-current-note{display:block!important;text-align:right!important;font-size:.48rem!important;line-height:1!important;color:#0B7A43!important;font-weight:900!important;letter-spacing:.05em!important;margin:2px 4px 0!important;height:9px!important}
  .weekly-rank-title{margin-top:5px!important;margin-bottom:5px!important;padding-top:2px!important}
}
@media(max-width:360px){
  .st-key-weekly_week_nav [data-testid="stSegmentedControl"] button{min-width:42px!important;padding:4px 6px!important;font-size:.64rem!important}
}
'''
if '/* Seletor semanal compacto — UI/UX, sem alteração da lógica de semanas. */' not in s:
    s=s.replace('\n</style>"""',css+'\n</style>"""',1)

path.write_text(s,encoding='utf-8')
