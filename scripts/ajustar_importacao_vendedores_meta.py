from pathlib import Path

path=Path('app.py')
text=path.read_text(encoding='utf-8')

old='''            cfg=prepare_config(merge_registry(base,current_cfg),month_rows,ref.month,ref.year)
            cfg["dia_referencia"]=max(x["data_venda"].day for x in month_rows); source=uploaded.name
'''
new='''            # A importação atualiza vendas, mas o cadastro administrativo existente é a fonte de verdade.
            # prepare_config apenas acrescenta nomes novos encontrados no relatório e preserva os campos
            # dos vendedores já configurados (equipe, ativo, categoria, vínculo e meta).
            preserved_cfg=merge_registry(base,current_cfg)
            cfg=prepare_config(preserved_cfg,month_rows,ref.month,ref.year)
            cfg["meta_padrao_vendedor"]=int(preserved_cfg.get("meta_padrao_vendedor",70) or 70)
            cfg["dia_referencia"]=max(x["data_venda"].day for x in month_rows); source=uploaded.name
'''
if old not in text: raise SystemExit('Bloco de configuração pós-importação não encontrado')
text=text.replace(old,new,1)

old='''            "experiencia":previous.get("experiencia",False),"meta_individual":previous.get("meta_individual",70),
'''
new='''            "experiencia":previous.get("experiencia",False),"meta_individual":previous.get("meta_individual",int(cfg.get("meta_padrao_vendedor",70) or 70)),
'''
if old not in text: raise SystemExit('Default de meta do vendedor não encontrado')
text=text.replace(old,new,1)

start=text.find('    with st.form("gestao_config"):')
end=text.find('    st.markdown("#### RELATÓRIO GERAL DA EQUIPE")',start)
if start<0 or end<0: raise SystemExit('Gestão de vendedores não encontrada')
new_management='''    with st.form("gestao_config"):
        st.markdown("#### GESTÃO DE VENDEDORES")
        st.caption("Configurações já salvas são preservadas nas próximas importações. Vendedores novos aparecem abaixo para configuração.")
        st.markdown("""<style>
/* GESTÃO DE VENDEDORES EM LINHAS COMPACTAS - somente layout */
.st-key-seller_management_header{margin:.15rem 0 .05rem!important}
[class*="st-key-seller_line_"]{border-bottom:1px solid #E2E8F0!important;margin:0!important;padding:2px 0!important}
[class*="st-key-seller_line_"] [data-testid="stHorizontalBlock"]{align-items:center!important;gap:.35rem!important}
[class*="st-key-seller_line_"] [data-testid="stMarkdownContainer"] p{margin:0!important;line-height:1.05!important;font-size:.76rem!important}
[class*="st-key-seller_line_"] [data-testid="stSelectbox"],
[class*="st-key-seller_line_"] [data-testid="stCheckbox"]{margin:0!important;padding:0!important}
[class*="st-key-seller_line_"] [data-baseweb="select"]>div{min-height:30px!important;height:30px!important;font-size:.72rem!important}
[class*="st-key-seller_line_"] label{font-size:.64rem!important;margin:0!important}
@media(max-width:700px){
 [class*="st-key-seller_line_"] [data-testid="stHorizontalBlock"]{display:grid!important;grid-template-columns:minmax(0,1fr) 70px!important;gap:3px 6px!important}
 [class*="st-key-seller_line_"] [data-testid="column"]{width:100%!important;min-width:0!important;max-width:none!important}
 [class*="st-key-seller_line_"] [data-testid="column"]:nth-child(3){grid-column:1!important}
 [class*="st-key-seller_line_"] [data-testid="column"]:nth-child(4){grid-column:2!important}
}
</style>""",unsafe_allow_html=True)

        # Um único valor administrativo é aplicado igualmente a todos os vendedores ativos.
        default_meta=int(cfg.get("meta_padrao_vendedor",next((x.get("meta_individual",70) for x in cfg.get("vendedores",[]) if x.get("ativo",False)),70)) or 70)
        meta_col,meta_note=st.columns([1.2,3.8],vertical_alignment="bottom")
        meta_padrao=int(meta_col.number_input("META MENSAL POR VENDEDOR",min_value=0,value=default_meta,step=1,key="gestao_meta_padrao_vendedor"))
        meta_note.caption("Ao salvar, este mesmo valor será aplicado a todos os vendedores ativos. Não é dividido entre a equipe.")
        cfg["meta_padrao_vendedor"]=meta_padrao

        with st.container(key="seller_management_header"):
            h1,h2,h3,h4=st.columns([3.6,.8,2.0,1.55],vertical_alignment="center")
            h1.markdown("**VENDEDOR**"); h2.markdown("**VENDAS**"); h3.markdown("**EQUIPE**"); h4.markdown("**DASHBOARD / RANKING**")

        for i,seller in enumerate(cfg["vendedores"]):
            key=normalize_text(seller.get("vendedor","")); qty=sales_by_seller.get(key,0)
            with st.container(key=f"seller_line_{i}"):
                name_col,sales_col,team_col,active_col=st.columns([3.6,.8,2.0,1.55],vertical_alignment="center")
                name_col.markdown(f'**{html.escape(str(seller["vendedor"]))}**',unsafe_allow_html=True)
                sales_col.markdown(f'**{qty}**')
                current_team=normalized_team(seller.get("equipe"),seller)
                seller["equipe"]=team_col.selectbox("Equipe",TEAM_OPTIONS,index=TEAM_OPTIONS.index(current_team),key=f"geq{i}",label_visibility="collapsed")
                was_active=bool(seller.get("ativo",False))
                seller["ativo"]=active_col.checkbox("Exibir",was_active,key=f"gat{i}")
                if seller["ativo"]:
                    seller["pertence_franquia"]=True
                    seller["meta_individual"]=meta_padrao
                    if normalize_text(seller.get("categoria")) in {"canal nacional",""}:seller["categoria"]="Vendedor"
                seller["classificado"]=True
        confirmed=st.form_submit_button("SALVAR CONFIGURAÇÕES",use_container_width=True)

'''
text=text[:start]+new_management+text[end:]

path.write_text(text,encoding='utf-8')
print('Ajustes aplicados.')
