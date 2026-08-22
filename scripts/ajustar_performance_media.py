from pathlib import Path

# Migração visual: performance baseada em média diária.
app_path=Path('app.py')
text=app_path.read_text(encoding='utf-8')

old='''def performance(projected,target):\n    ratio=projected/target if target else 0\n    if ratio>=1.5:return "Azul","#0891B2","cyan"\n    if ratio>=1:return "Verde","#16A34A","green"\n    if ratio>=.7:return "Amarelo","#F59E0B","yellow"\n    return "Vermelho","#DC2626","red"'''
new='''def performance(media):\n    media=float(media or 0)\n    if media>=2.0:return "Azul","#0891B2","cyan"\n    if media>=1.5:return "Verde","#16A34A","green"\n    if media>=1.0:return "Amarelo","#F59E0B","yellow"\n    return "Vermelho","#DC2626","red"'''
if old not in text: raise SystemExit('Bloco performance não encontrado')
text=text.replace(old,new)

start=text.index('def ranking_html(ranking):')
end=text.index('\ndef daily_series',start)
ranking='''def ranking_html(ranking):\n    medals=("🥇","🥈","🥉")\n    rows=[]\n    for i,x in enumerate(ranking[:8]):\n        _,color,_=performance(x["media"])\n        medal=medals[i] if i<3 else f"{i+1}º"\n        rows.append(\n            f'<div class="rank-row"><div class="rank-pos">{medal}</div>'\n            f'<div class="rank-name" style="background:{color}">'\n            f'<div class="rank-seller"><b>{html.escape(x["vendedor"])}</b><small>{html.escape(x["setor"])}</small></div>'\n            f'<div class="rank-inside"><span><strong>{x["vendas"]}</strong><small>VENDAS</small></span>'\n            f'<span><strong>{x["projecao"]}</strong><small>PROJEÇÃO</small></span>'\n            f'<span class="neo-highlight"><strong>{x["neo"]}</strong><small>NEO</small></span>'\n            f'<span><strong>{pct(x["neo_pct"])}</strong><small>% NEO</small></span>'\n            f'<span><strong>{x["media"]:.2f}</strong><small>MÉDIA/DIA</small></span></div></div></div>'\n        )\n    return '<div class="rank-card">'+''.join(rows)+'</div>' if rows else '<div class="empty-bi">Nenhum vendedor local ativo para exibir no ranking.</div>'\n'''
text=text[:start]+ranking+text[end:]

text=text.replace('.rank-row{display:grid;grid-template-columns:54px minmax(190px,1.55fr) 82px 82px 72px 88px;align-items:center;gap:8px;padding:9px 13px;border-bottom:1px solid #EEF2F7}', '.rank-row{display:grid;grid-template-columns:54px 1fr;align-items:center;gap:10px;padding:9px 13px;border-bottom:1px solid #EEF2F7}')
text=text.replace('.rank-name{display:flex;flex-direction:column;min-width:0;padding:8px 10px;border-radius:9px;color:white;box-shadow:0 2px 7px rgba(15,23,42,.10)}.rank-name b{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-size:.81rem}.rank-name small{font-size:.62rem;color:rgba(255,255,255,.82)}.rank-kpi small{font-size:.62rem;color:#94A3B8}.rank-kpi{display:flex;flex-direction:column;text-align:center}.rank-kpi b{font-size:.87rem}', '.rank-name{display:grid;grid-template-columns:minmax(210px,1.3fr) 2.2fr;align-items:center;gap:14px;min-width:0;padding:10px 12px;border-radius:10px;color:white;box-shadow:0 2px 7px rgba(15,23,42,.10)}.rank-seller{display:flex;flex-direction:column;min-width:0}.rank-seller b{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-size:.92rem}.rank-seller small{font-size:.65rem;color:rgba(255,255,255,.82)}.rank-inside{display:grid;grid-template-columns:repeat(5,minmax(72px,1fr));gap:8px;align-items:center}.rank-inside span{display:flex;flex-direction:column;align-items:center;padding:4px 6px;border-left:1px solid rgba(255,255,255,.25)}.rank-inside strong{font-size:1.2rem;line-height:1;font-weight:900}.rank-inside small{font-size:.58rem;color:rgba(255,255,255,.84);margin-top:4px}.rank-inside .neo-highlight strong{font-size:1.55rem;text-shadow:0 1px 2px rgba(0,0,0,.18)}')
text=text.replace('@media(max-width:1100px){.block-container{padding:.7rem}.rank-row{grid-template-columns:45px minmax(150px,1fr) 65px 68px 60px 75px}.metric strong{font-size:1.35rem}}', '@media(max-width:1100px){.block-container{padding:.7rem}.rank-row{grid-template-columns:45px 1fr}.rank-name{grid-template-columns:1fr}.rank-inside{grid-template-columns:repeat(5,1fr)}.metric strong{font-size:1.35rem}}')

text=text.replace('color=lambda x:performance(x["projecao"],x["meta_individual"])[1]', 'color=lambda x:performance(x["media"])[1]')
text=text.replace('counts[performance(x["projecao"],x["meta_individual"])[0]]+=1', 'counts[performance(x["media"])[0]]+=1')
text=text.replace('status,c,tone=performance(x["projecao"],x["meta_individual"])', 'status,c,tone=performance(x["media"])')

old_block='''        left,right=st.columns([1.65,1],gap="small")\n        with left:\n            st.markdown('<div class="section">Ranking da equipe</div>',unsafe_allow_html=True); ranking=sorted(team,key=lambda x:(x["vendas"],x["neo_pct"]),reverse=True); st.markdown(ranking_html(ranking),unsafe_allow_html=True)\n        with right:\n            st.markdown('<div class="section">Realizado x meta</div>',unsafe_allow_html=True); gap=max(0,cfg["meta_empresa"]-total); st.bar_chart({"Vendas":[total,gap]},height=185)\n            st.markdown('<div class="section">Participação NEO</div>',unsafe_allow_html=True); st.bar_chart({"Vendas":[neo,max(0,total-neo)]},height=160)'''
new_block='''        st.markdown('<div class="section">Ranking da equipe</div>',unsafe_allow_html=True); ranking=sorted(team,key=lambda x:(x["vendas"],x["projecao"]),reverse=True); st.markdown(ranking_html(ranking),unsafe_allow_html=True)'''
if old_block not in text: raise SystemExit('Bloco de ranking/gráficos não encontrado')
text=text.replace(old_block,new_block)

needle='''        st.markdown(table_html(display,cols,color,True),unsafe_allow_html=True)'''
replacement='''        st.markdown(table_html(display,cols,color,True),unsafe_allow_html=True)\n        try:\n            with tempfile.TemporaryDirectory() as folder:\n                general_path=Path(folder)/"Relatorio_Geral_Equipe_Afogados.xlsx"\n                general_sheet=next(s for s in build_sheets(rows,cfg,summary,all_days,elapsed,official) if s.name=="RELATORIO GERAL")\n                write_xlsx(general_path,[general_sheet]); general_book=general_path.read_bytes()\n            st.download_button("BAIXAR RELATÓRIO GERAL DA EQUIPE (EXCEL)",general_book,"Relatorio_Geral_Equipe_Afogados.xlsx","application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")\n        except Exception as exc:st.warning(f"Não foi possível gerar o Relatório Geral agora: {exc}")'''
if needle not in text: raise SystemExit('Tabela geral não encontrada')
text=text.replace(needle,replacement,1)

app_path.write_text(text,encoding='utf-8')

p=Path('gerar_painel.py')
g=p.read_text(encoding='utf-8')
old='''    def performance_scale(self, ref, first_row, projection_col="H", target_col="AG"):\n        \"\"\"Colore vendedor/projeção pela proporção entre projeção e meta.\"\"\"\n        self.performance_conditionals.append((ref, first_row, projection_col, target_col))'''
new='''    def performance_scale(self, ref, first_row, average_col="G", target_col=None):\n        \"\"\"Colore a faixa do vendedor pela média diária: <1 vermelho, 1-1,49 amarelo, 1,5-1,99 verde, >=2 azul.\"\"\"\n        self.performance_conditionals.append((ref, first_row, average_col, target_col))'''
if old not in g: raise SystemExit('Método performance_scale não encontrado')
g=g.replace(old,new)
old_rules='''        for ref, first, projection, target in self.performance_conditionals:\n            rules = [\n                (0, f'AND(${target}{first}&gt;0,${projection}{first}&gt;=1.5*${target}{first})'),\n                (1, f'AND(${target}{first}&gt;0,${projection}{first}&gt;=${target}{first},${projection}{first}&lt;1.5*${target}{first})'),\n                (2, f'AND(${target}{first}&gt;0,${projection}{first}&gt;=0.7*${target}{first},${projection}{first}&lt;${target}{first})'),\n                (3, f'AND(${target}{first}&gt;0,${projection}{first}&lt;0.7*${target}{first})'),\n            ]'''
new_rules='''        for ref, first, average_col, _ in self.performance_conditionals:\n            rules = [\n                (0, f'${average_col}{first}&gt;=2'),\n                (1, f'AND(${average_col}{first}&gt;=1.5,${average_col}{first}&lt;2)'),\n                (2, f'AND(${average_col}{first}&gt;=1,${average_col}{first}&lt;1.5)'),\n                (3, f'${average_col}{first}&lt;1'),\n            ]'''
if old_rules not in g: raise SystemExit('Regras condicionais não encontradas')
g=g.replace(old_rules,new_rules)
g=g.replace('general.performance_scale(f"A5:A{n} H5:H{n}",5,target_col=general_end)', 'general.performance_scale(f"A5:A{n}",5,average_col="G")')
g.write_text(g,encoding='utf-8')
