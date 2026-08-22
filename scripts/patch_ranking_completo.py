from pathlib import Path

p=Path('app.py')
text=p.read_text(encoding='utf-8')

start=text.index('def ranking_html(ranking):')
end=text.index('\ndef daily_series',start)
new_ranking='''def ranking_html(ranking):
    medals=("🥇","🥈","🥉")
    rows=[]
    for i,x in enumerate(ranking):
        _,color,_=performance(x["media"])
        medal=medals[i] if i<3 else f"{i+1}º"
        meta_pct=x["projecao"]/x["meta_individual"] if x["meta_individual"] else 0
        rows.append(
            f'<div class="rank-row"><div class="rank-pos">{medal}</div>'
            f'<div class="rank-name" style="background:{color}">'
            f'<div class="rank-seller"><b>{html.escape(x["vendedor"])}</b><small>{html.escape(x["setor"])}</small></div>'
            f'<div class="rank-inside">'
            f'<span class="main-kpi"><strong>{x["vendas"]}</strong><small>VENDAS</small></span>'
            f'<span class="main-kpi"><strong>{x["projecao"]}</strong><small>PROJEÇÃO</small></span>'
            f'<span><strong>{x["media"]:.2f}</strong><small>MÉDIA/DIA</small></span>'
            f'<span><strong>{x["zeros"]}</strong><small>ZEROS</small></span>'
            f'<span><strong>{pct(meta_pct)}</strong><small>% META</small></span>'
            f'<span class="neo-highlight"><strong>{x["neo"]}</strong><small>NEO</small></span>'
            f'<span class="neo-highlight"><strong>{pct(x["neo_pct"])}</strong><small>% NEO</small></span>'
            f'<span><strong>{money(x["base"])}</strong><small>COMISSÃO ATUAL</small></span>'
            f'<span><strong>{money(x["comissao_proj"])}</strong><small>COMISSÃO PROJ.</small></span>'
            f'<span><strong>{money(x["bonus_neo_proj"])}</strong><small>BÔNUS NEO PROJ.</small></span>'
            f'<span><strong>{money(x["bonus_adim_proj"])}</strong><small>BÔNUS ADIM. PROJ.</small></span>'
            f'<span><strong>{money(x["premio_total"])}</strong><small>PRÊMIOS</small></span>'
            f'<span class="total-highlight"><strong>{money(x["total_variavel_proj"])}</strong><small>TOTAL VAR. PROJ.</small></span>'
            f'</div></div></div>'
        )
    return '<div class="rank-card">'+''.join(rows)+'</div>' if rows else '<div class="empty-bi">Nenhum vendedor local ativo para exibir no ranking.</div>'
'''
text=text[:start]+new_ranking+text[end:]

old_css='.rank-name{display:grid;grid-template-columns:minmax(210px,1.3fr) 2.2fr;align-items:center;gap:14px;min-width:0;padding:10px 12px;border-radius:10px;color:white;box-shadow:0 2px 7px rgba(15,23,42,.10)}.rank-seller{display:flex;flex-direction:column;min-width:0}.rank-seller b{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-size:.92rem}.rank-seller small{font-size:.65rem;color:rgba(255,255,255,.82)}.rank-inside{display:grid;grid-template-columns:repeat(5,minmax(72px,1fr));gap:8px;align-items:center}.rank-inside span{display:flex;flex-direction:column;align-items:center;padding:4px 6px;border-left:1px solid rgba(255,255,255,.25)}.rank-inside strong{font-size:1.2rem;line-height:1;font-weight:900}.rank-inside small{font-size:.58rem;color:rgba(255,255,255,.84);margin-top:4px}.rank-inside .neo-highlight strong{font-size:1.55rem;text-shadow:0 1px 2px rgba(0,0,0,.18)}'
new_css='.rank-name{display:grid;grid-template-columns:minmax(220px,.9fr) 3.6fr;align-items:start;gap:14px;min-width:0;padding:12px;border-radius:10px;color:white;box-shadow:0 2px 7px rgba(15,23,42,.10)}.rank-seller{display:flex;flex-direction:column;min-width:0;padding-top:4px}.rank-seller b{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-size:.94rem}.rank-seller small{font-size:.65rem;color:rgba(255,255,255,.82)}.rank-inside{display:grid;grid-template-columns:repeat(7,minmax(92px,1fr));gap:7px;align-items:stretch}.rank-inside span{display:flex;flex-direction:column;justify-content:center;align-items:center;min-height:54px;padding:5px 7px;border-left:1px solid rgba(255,255,255,.25);text-align:center}.rank-inside strong{font-size:.92rem;line-height:1.08;font-weight:900;white-space:nowrap}.rank-inside small{font-size:.54rem;color:rgba(255,255,255,.84);margin-top:5px}.rank-inside .main-kpi strong{font-size:1.35rem}.rank-inside .neo-highlight{background:rgba(255,255,255,.14);border-radius:8px}.rank-inside .neo-highlight strong{font-size:1.5rem;text-shadow:0 1px 2px rgba(0,0,0,.18)}.rank-inside .total-highlight{background:rgba(15,23,42,.22);border-radius:8px}.rank-inside .total-highlight strong{font-size:1.05rem}'
if old_css not in text: raise SystemExit('CSS do ranking não encontrado')
text=text.replace(old_css,new_css)
text=text.replace('@media(max-width:1100px){.block-container{padding:.7rem}.rank-row{grid-template-columns:45px 1fr}.rank-name{grid-template-columns:1fr}.rank-inside{grid-template-columns:repeat(5,1fr)}.metric strong{font-size:1.35rem}}@media(max-width:720px){.bi-topbar{padding:14px}.bi-topbar h1{font-size:1.05rem}.rank-row{grid-template-columns:42px 1fr}.rank-inside{grid-template-columns:repeat(2,1fr)}.block-container{padding:.5rem}}', '@media(max-width:1250px){.block-container{padding:.7rem}.rank-row{grid-template-columns:45px 1fr}.rank-name{grid-template-columns:1fr}.rank-inside{grid-template-columns:repeat(4,1fr)}.metric strong{font-size:1.35rem}}@media(max-width:720px){.bi-topbar{padding:14px}.bi-topbar h1{font-size:1.05rem}.rank-row{grid-template-columns:38px 1fr;padding:7px 4px}.rank-inside{grid-template-columns:repeat(2,1fr)}.block-container{padding:.5rem}}')

old_general='''        st.markdown('<div class="section">Relatório geral da equipe</div>',unsafe_allow_html=True); cols=[("setor","SETOR"),("vendedor","VENDEDOR"),("vendas","TOTAL"),("projecao","PROJEÇÃO"),("media","MÉDIA"),("zeros","ZEROS"),("meta_pct","% META"),("neo","NEO"),("neo_pct_fmt","% NEO"),("base_fmt","COMISSÃO ATUAL"),("proj_fmt","COMISSÃO PROJETADA"),("neo_proj_fmt","BÔNUS NEO PROJ."),("adim_proj_fmt","BÔNUS ADIM. PROJ."),("premio_fmt","PRÊMIOS"),("total_proj_fmt","TOTAL VAR. PROJ.")]+[(d.day,str(d.day)) for d in all_days]; display=[]
        for x in sorted(team,key=lambda x:(x["vendas"],x["projecao"]),reverse=True):display.append(x|{"media":f'{x["media"]:.2f}',"meta_pct":pct(x["projecao"]/x["meta_individual"] if x["meta_individual"] else 0),"neo_pct_fmt":pct(x["neo_pct"]),"base_fmt":money(x["base"]),"proj_fmt":money(x["comissao_proj"]),"neo_proj_fmt":money(x["bonus_neo_proj"]),"adim_proj_fmt":money(x["bonus_adim_proj"]),"premio_fmt":money(x["premio_total"]),"total_proj_fmt":money(x["total_variavel_proj"])})
        st.markdown(table_html(display,cols,color,True),unsafe_allow_html=True)
        try:
            with tempfile.TemporaryDirectory() as folder:
                general_path=Path(folder)/"Relatorio_Geral_Equipe_Afogados.xlsx"
                general_sheet=next(s for s in build_sheets(rows,cfg,summary,all_days,elapsed,official) if s.name=="RELATORIO GERAL")
                write_xlsx(general_path,[general_sheet]); general_book=general_path.read_bytes()
            st.download_button("BAIXAR RELATÓRIO GERAL DA EQUIPE (EXCEL)",general_book,"Relatorio_Geral_Equipe_Afogados.xlsx","application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        except Exception as exc:st.warning(f"Não foi possível gerar o Relatório Geral agora: {exc}")
'''
if old_general not in text: raise SystemExit('Relatório geral na visão geral não encontrado')
text=text.replace(old_general,'')

needle='''        cards(st,[("VENDAS",x["vendas"],"cyan",""),("MÉDIA",f'{x["media"]:.2f}',tone,f'{x["dias"]} dias'),("PROJEÇÃO",x["projecao"],tone,f'Meta {x["meta_individual"]}'),("% DA META",pct(x["projecao"]/x["meta_individual"] if x["meta_individual"] else 0),tone,""),("ZEROS",x["zeros"],"red",f'Semana {x["zeros_semana"]}'),("NEO",x["neo"],"cyan",""),("% NEO",pct(x["neo_pct"]),"green",""),("COMISSÃO ATUAL",money(x["base"]),"green",""),("COMISSÃO PROJETADA",money(x["comissao_proj"]),"yellow","Base projetada"),("BÔNUS NEO PROJ.",money(x["bonus_neo_proj"]),"green",""),("BÔNUS ADIM. PROJ.",money(x["bonus_adim_proj"]),"green",""),("PRÊMIOS",money(x["premio_total"]),"green","Acumulados"),("TOTAL VAR. ATUAL",money(x["total"]),"cyan",""),("TOTAL VAR. PROJETADO",money(x["total_variavel_proj"]),"yellow","")])'''
insert=needle+'''\n        st.markdown('<div class="section">Relatório geral da equipe</div>',unsafe_allow_html=True)\n        cols=[("setor","SETOR"),("vendedor","VENDEDOR"),("vendas","TOTAL"),("projecao","PROJEÇÃO"),("media","MÉDIA"),("zeros","ZEROS"),("meta_pct","% META"),("neo","NEO"),("neo_pct_fmt","% NEO"),("base_fmt","COMISSÃO ATUAL"),("proj_fmt","COMISSÃO PROJETADA"),("neo_proj_fmt","BÔNUS NEO PROJ."),("adim_proj_fmt","BÔNUS ADIM. PROJ."),("premio_fmt","PRÊMIOS"),("total_proj_fmt","TOTAL VAR. PROJ.")]+[(d.day,str(d.day)) for d in all_days]; display=[]\n        for item in sorted(team,key=lambda z:(z["vendas"],z["projecao"]),reverse=True):display.append(item|{"media":f'{item["media"]:.2f}',"meta_pct":pct(item["projecao"]/item["meta_individual"] if item["meta_individual"] else 0),"neo_pct_fmt":pct(item["neo_pct"]),"base_fmt":money(item["base"]),"proj_fmt":money(item["comissao_proj"]),"neo_proj_fmt":money(item["bonus_neo_proj"]),"adim_proj_fmt":money(item["bonus_adim_proj"]),"premio_fmt":money(item["premio_total"]),"total_proj_fmt":money(item["total_variavel_proj"])})\n        st.markdown(table_html(display,cols,color,True),unsafe_allow_html=True)\n        try:\n            with tempfile.TemporaryDirectory() as folder:\n                general_path=Path(folder)/"Relatorio_Geral_Equipe_Afogados.xlsx"\n                general_sheet=next(s for s in build_sheets(rows,cfg,summary,all_days,elapsed,official) if s.name=="RELATORIO GERAL")\n                write_xlsx(general_path,[general_sheet]); general_book=general_path.read_bytes()\n            st.download_button("BAIXAR RELATÓRIO GERAL DA EQUIPE (EXCEL)",general_book,"Relatorio_Geral_Equipe_Afogados.xlsx","application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")\n        except Exception as exc:st.warning(f"Não foi possível gerar o Relatório Geral agora: {exc}")'''
if needle not in text: raise SystemExit('Bloco individual de vendedores não encontrado')
text=text.replace(needle,insert,1)

p.write_text(text,encoding='utf-8')
print('app.py atualizado com ranking completo e relatório geral movido para Vendedores')
