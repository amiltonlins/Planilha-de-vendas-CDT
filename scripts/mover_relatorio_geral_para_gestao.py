from pathlib import Path

# Trigger: aplicar movimentação do Relatório Geral para a Gestão.
path=Path('app.py')
text=path.read_text(encoding='utf-8')

old='''    st.markdown("#### RELATÓRIO GERAL DA EQUIPE")
    try:
        management_summary,management_days,management_elapsed,management_official=summarize(rows,cfg)
        apply_team_labels(management_summary,cfg)
        management_team=regular(management_summary)
        general_book=general_report_xlsx_bytes(management_team,management_days)
        validate_xlsx_bytes(general_book,"RELATORIO GERAL")
        st.download_button("BAIXAR RELATÓRIO GERAL DA EQUIPE (EXCEL)",general_book,"Relatorio_Geral_Equipe_Afogados.xlsx","application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",use_container_width=True,key="gestao_download_relatorio_geral")
    except Exception as exc:
        st.error(f"Não foi possível gerar o Relatório Geral em Excel: {exc}")
'''
new='''    st.markdown("#### RELATÓRIO GERAL DA EQUIPE")
    try:
        management_summary,management_days,management_elapsed,management_official=summarize(rows,cfg)
        apply_team_labels(management_summary,cfg)
        management_team=regular(management_summary)
        management_cols=[("equipe","EQUIPE"),("vendedor","VENDEDOR"),("vendas","TOTAL"),("projecao","PROJEÇÃO"),("media","MÉDIA"),("zeros","ZEROS"),("meta_pct","% META"),("neo","NEO"),("neo_pct_fmt","% NEO"),("base_fmt","PREMIAÇÃO ATUAL"),("proj_fmt","PREMIAÇÃO PROJETADA"),("neo_proj_fmt","BÔNUS NEO PROJ."),("adim_proj_fmt","BÔNUS (SE) 100% ADIM"),("premio_fmt","SEMANAIS"),("total_proj_fmt","TOTAL VAR. PROJ.")]+[(d.day,str(d.day)) for d in management_days]
        management_display=general_report_display(management_team)
        management_color=lambda x:performance(x["media"])[1]
        st.markdown(table_html(management_display,management_cols,management_color,True),unsafe_allow_html=True)
        general_book=general_report_xlsx_bytes(management_team,management_days)
        validate_xlsx_bytes(general_book,"RELATORIO GERAL")
        st.download_button("BAIXAR RELATÓRIO GERAL DA EQUIPE (EXCEL)",general_book,"Relatorio_Geral_Equipe_Afogados.xlsx","application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",use_container_width=True,key="gestao_download_relatorio_geral")
    except Exception as exc:
        st.error(f"Não foi possível gerar o Relatório Geral da Equipe: {exc}")
'''
if old not in text:
    raise SystemExit('Bloco do relatório geral na Gestão não encontrado')
text=text.replace(old,new,1)

old_call='''        render_general_report(st,team,rows,cfg,summary,all_days,elapsed,official,color)\n'''
if old_call not in text:
    raise SystemExit('Chamada do relatório geral na Visão Geral não encontrada')
text=text.replace(old_call,'',1)

path.write_text(text,encoding='utf-8')
print('Relatório Geral movido para a Gestão com tabela + Excel; removido da Visão Geral.')
