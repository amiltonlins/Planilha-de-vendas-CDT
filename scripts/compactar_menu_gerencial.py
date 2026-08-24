from pathlib import Path

path = Path('app.py')
text = path.read_text(encoding='utf-8')

old_sellers = '''        for i,seller in enumerate(cfg["vendedores"]):
            key=normalize_text(seller.get("vendedor","")); qty=sales_by_seller.get(key,0)
            with st.container(border=True):
                left,mid,right=st.columns([3.0,2.0,1.5])
                left.markdown(f'**{seller["vendedor"]}**')
                left.caption(f'{qty} venda(s) reconhecida(s) no mês')
                current_team=normalized_team(seller.get("equipe"),seller)
                seller["equipe"]=mid.selectbox("Equipe",TEAM_OPTIONS,index=TEAM_OPTIONS.index(current_team),key=f"geq{i}")
                was_active=bool(seller.get("ativo",False))
                seller["ativo"]=right.checkbox("Exibir no Dashboard/Ranking",was_active,key=f"gat{i}")
                if seller["ativo"]:
                    seller["pertence_franquia"]=True
                    if normalize_text(seller.get("categoria")) in {"canal nacional",""}:seller["categoria"]="Vendedor"
                seller["classificado"]=True
'''
new_sellers = '''        st.markdown("""<style>
/* MENU GERENCIAL COMPACTO - somente apresentação */
[class*="st-key-seller_grid_row_"]{margin-bottom:.25rem!important}
[class*="st-key-seller_grid_row_"] [data-testid="stVerticalBlockBorderWrapper"]{padding:.15rem!important}
[class*="st-key-seller_grid_row_"] [data-testid="stVerticalBlock"]{gap:.20rem!important}
[class*="st-key-seller_grid_row_"] [data-testid="stMarkdownContainer"] p{margin-bottom:.05rem!important;line-height:1.12!important}
[class*="st-key-seller_grid_row_"] [data-testid="stCaptionContainer"]{margin-top:-.15rem!important;margin-bottom:.05rem!important}
[class*="st-key-seller_grid_row_"] [data-testid="stSelectbox"] label,
[class*="st-key-seller_grid_row_"] [data-testid="stCheckbox"] label{font-size:.70rem!important}
[class*="st-key-seller_grid_row_"] [data-baseweb="select"]>div{min-height:34px!important;height:34px!important}
@media(max-width:700px){
  [class*="st-key-seller_grid_row_"] [data-testid="stHorizontalBlock"]{display:block!important}
  [class*="st-key-seller_grid_row_"] [data-testid="column"]{width:100%!important;min-width:100%!important;max-width:100%!important;margin-bottom:.35rem!important}
}
</style>""",unsafe_allow_html=True)
        sellers_list=list(enumerate(cfg["vendedores"]))
        for row_start in range(0,len(sellers_list),3):
            with st.container(key=f"seller_grid_row_{row_start//3}"):
                seller_cols=st.columns(3,gap="small")
                for offset,(i,seller) in enumerate(sellers_list[row_start:row_start+3]):
                    key=normalize_text(seller.get("vendedor","")); qty=sales_by_seller.get(key,0)
                    with seller_cols[offset]:
                        with st.container(border=True):
                            st.markdown(f'**{seller["vendedor"]}**')
                            st.caption(f'{qty} venda(s) no mês')
                            current_team=normalized_team(seller.get("equipe"),seller)
                            seller["equipe"]=st.selectbox("Equipe",TEAM_OPTIONS,index=TEAM_OPTIONS.index(current_team),key=f"geq{i}")
                            was_active=bool(seller.get("ativo",False))
                            seller["ativo"]=st.checkbox("Exibir no Dashboard/Ranking",was_active,key=f"gat{i}")
                            if seller["ativo"]:
                                seller["pertence_franquia"]=True
                                if normalize_text(seller.get("categoria")) in {"canal nacional",""}:seller["categoria"]="Vendedor"
                            seller["classificado"]=True
'''
if old_sellers not in text:
    raise SystemExit('Bloco de Gestão de Vendedores não encontrado')
text = text.replace(old_sellers, new_sellers, 1)

start = text.find('    st.markdown("#### ACOMPANHAMENTO SEMANAL")')
end_marker = '    st.markdown("#### PREMIAÇÕES E CENÁRIOS")'
end = text.find(end_marker, start)
if start < 0 or end < 0:
    raise SystemExit('Bloco de acompanhamento semanal não encontrado')
weekly_new = '''    st.markdown("#### HISTÓRICO SEMANAL INDIVIDUAL")
    try:
        if 'management_summary' not in locals():
            management_summary,management_days,management_elapsed,management_official=summarize(rows,cfg)
            apply_team_labels(management_summary,cfg)
        management_team=regular(management_summary)
        management_max_weeks=max((len(x.get("semanas",[])) for x in management_team),default=0)
        if management_max_weeks:
            management_sellers=[x["vendedor"] for x in sorted(management_team,key=lambda z:normalize_text(z["vendedor"]))]
            chosen=st.selectbox("Vendedor",["SELECIONE UM VENDEDOR"]+management_sellers,key="gestao_weekly_seller")
            if chosen!="SELECIONE UM VENDEDOR":
                selected=next((x for x in management_team if x["vendedor"]==chosen),None)
                if selected:st.markdown(weekly_seller_history_html(selected),unsafe_allow_html=True)
        else:st.caption("Sem dados semanais nesta competência.")
    except Exception as exc:
        st.error(f"Não foi possível montar o histórico semanal individual: {exc}")

'''
text = text[:start] + weekly_new + text[end:]

conference = '''    st.markdown("#### CONFERÊNCIA DA IMPORTAÇÃO")
    audit=[]
    for seller in cfg["vendedores"]:
        qty=sales_by_seller.get(normalize_text(seller.get("vendedor","")),0)
        audit.append({"Vendedor":seller.get("vendedor",""),"Vendas reconhecidas":qty,"Status":"OK"})
    if audit:st.dataframe(audit,use_container_width=True,hide_index=True)
'''
if conference not in text:
    raise SystemExit('Bloco Conferência da Importação não encontrado')
text = text.replace(conference, '', 1)

old_history = '''        st.caption("Excluir uma importação remove efetivamente as vendas daquele lote e recalcula o dashboard. Importações substituídas permanecem apenas para auditoria.")
        for h in reversed(history[-30:]):
            status=h.get("status","Ativa"); import_id=h.get("importacao_id",""); days=", ".join(h.get("dias",[])); regs=int(h.get("registros_arquivo",0) or 0); sellers_count=int(h.get("vendedores",0) or 0)
            with st.container(border=True):
                a,b,c,d=st.columns([2.1,2.2,1.1,1.1])
                a.markdown(f'**{h.get("arquivo","Importação")}**')
                a.caption(h.get("data_importacao","").replace("T"," "))
                b.markdown(f'**Período:** {days or "—"}')
                b.caption(f'Usuário: {h.get("usuario","") or "—"}')
                c.metric("Vendas",regs); d.metric("Vendedores",sellers_count)
                st.caption(f'Status: **{status}**')
                if status=="Ativa" and import_id:
                    if st.button("EXCLUIR IMPORTAÇÃO",key=f'del_import_{import_id}',type="secondary"):
                        st.session_state["confirm_delete_import_id"]=import_id; st.rerun()
                elif status=="Substituída":
                    st.caption("Esta importação foi substituída por uma importação posterior do mesmo dia e não possui vendas ativas no dashboard.")
                else:
                    st.caption("Importação excluída. Nenhuma venda deste lote permanece ativa.")
'''
new_history = '''        st.caption("Importações recentes. Abra um registro somente quando precisar consultar detalhes ou excluir um lote ativo.")
        for h in reversed(history[-30:]):
            status=h.get("status","Ativa"); import_id=h.get("importacao_id",""); days=", ".join(h.get("dias",[])); regs=int(h.get("registros_arquivo",0) or 0); sellers_count=int(h.get("vendedores",0) or 0)
            imported_at=h.get("data_importacao","").replace("T"," ")
            file_name=h.get("arquivo","Importação")
            summary=f'{file_name} · {imported_at[:16] or "—"} · {regs} vendas · {status}'
            with st.expander(summary,expanded=False):
                a,b=st.columns(2,gap="small")
                a.markdown(f'**Período:** {days or "—"}')
                a.caption(f'Usuário: {h.get("usuario","") or "—"}')
                b.markdown(f'**Vendas:** {regs} · **Vendedores:** {sellers_count}')
                b.caption(f'Status: {status}')
                if status=="Ativa" and import_id:
                    if st.button("EXCLUIR IMPORTAÇÃO",key=f'del_import_{import_id}',type="secondary"):
                        st.session_state["confirm_delete_import_id"]=import_id; st.rerun()
                elif status=="Substituída":
                    st.caption("Substituída por uma importação posterior do mesmo dia; sem vendas ativas no dashboard.")
                else:
                    st.caption("Importação excluída; nenhuma venda deste lote permanece ativa.")
'''
if old_history not in text:
    raise SystemExit('Bloco Histórico de Importações não encontrado')
text = text.replace(old_history, new_history, 1)

path.write_text(text, encoding='utf-8')
print('Menu Gerencial compactado com sucesso.')
