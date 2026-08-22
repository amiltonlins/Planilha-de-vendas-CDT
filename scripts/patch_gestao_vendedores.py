from pathlib import Path

p=Path('app.py')
s=p.read_text(encoding='utf-8')

old='''def merge_registry(base,current):\n    cfg=copy.deepcopy(current or base)\n    known={normalize_text(x["vendedor"]):x for x in cfg.get("vendedores",[])}\n    for seller in base.get("vendedores",[]):\n        key=normalize_text(seller["vendedor"])\n        if key not in known or not known[key].get("classificado",False):known[key]=copy.deepcopy(seller)\n    cfg["vendedores"]=list(known.values())\n    return cfg\n'''
new='''def merge_registry(base,current):\n    # A planilha importada é a fonte de verdade para a existência de vendedores.\n    # Não reintroduzir vendedores pré-cadastrados do config base na operação diária.\n    # As configurações administrativas já persistidas continuam sendo preservadas.\n    cfg=copy.deepcopy(current or base)\n    if current is not None:\n        cfg["vendedores"]=copy.deepcopy(current.get("vendedores",[]))\n    return cfg\n'''
if old not in s: raise SystemExit('merge_registry original não encontrado')
s=s.replace(old,new,1)

old='''        registered=bool(previous); belongs=previous.get("pertence_franquia",registered)\n        category=previous.get("categoria",inferred if registered else "Canal Nacional")\n'''
new='''        registered=bool(previous)\n        # Vendedor novo nasce apenas como identificado pela planilha. As decisões\n        # administrativas de equipe/visibilidade vêm depois e não filtram suas vendas.\n        belongs=previous.get("pertence_franquia",False)\n        category=previous.get("categoria",inferred if registered else "Vendedor")\n'''
if old not in s: raise SystemExit('defaults de vendedor não encontrados')
s=s.replace(old,new,1)

start=s.index('    with st.form("gestao_config"):\n')
end=s.index('    if confirmed:\n',start)
replacement='''    st.markdown("#### PERÍODO DE REFERÊNCIA")\n    month_names=("Janeiro","Fevereiro","Março","Abril","Maio","Junho","Julho","Agosto","Setembro","Outubro","Novembro","Dezembro")\n    st.info(f'{month_names[int(cfg["mes"])-1]} / {cfg["ano"]} · cálculos de dias, semanas e projeções continuam usando a lógica atual do sistema.')\n\n    sales_by_seller={}\n    for row in month_rows:\n        key=normalize_text(row.get("vendedor",""))\n        if key:sales_by_seller[key]=sales_by_seller.get(key,0)+1\n\n    with st.form("gestao_config"):\n        st.markdown("#### GESTÃO DE VENDEDORES")\n        st.caption("Os vendedores são identificados automaticamente pela planilha. Aqui você define somente a equipe e se aparecem no Dashboard/Ranking.")\n        for i,seller in enumerate(cfg["vendedores"]):\n            key=normalize_text(seller.get("vendedor","")); qty=sales_by_seller.get(key,0)\n            with st.container(border=True):\n                left,mid,right=st.columns([3.0,2.0,1.5])\n                left.markdown(f'**{seller["vendedor"]}**')\n                left.caption(f'{qty} venda(s) reconhecida(s) no mês')\n                current_team=normalized_team(seller.get("equipe"),seller)\n                seller["equipe"]=mid.selectbox("Equipe",TEAM_OPTIONS,index=TEAM_OPTIONS.index(current_team),key=f"geq{i}")\n                was_active=bool(seller.get("ativo",False))\n                seller["ativo"]=right.checkbox("Exibir no Dashboard/Ranking",was_active,key=f"gat{i}")\n                if seller["ativo"] and not seller.get("pertence_franquia",False):\n                    seller["pertence_franquia"]=True\n                    if normalize_text(seller.get("categoria")) in {"canal nacional",""}:seller["categoria"]="Vendedor"\n                seller["classificado"]=True\n        confirmed=st.form_submit_button("SALVAR CONFIGURAÇÕES",use_container_width=True)\n\n    st.markdown("#### CONFERÊNCIA DA IMPORTAÇÃO")\n    audit=[]\n    for seller in cfg["vendedores"]:\n        qty=sales_by_seller.get(normalize_text(seller.get("vendedor","")),0)\n        audit.append({"Vendedor":seller.get("vendedor",""),"Vendas reconhecidas":qty,"Status":"OK"})\n    if audit:st.dataframe(audit,use_container_width=True,hide_index=True)\n'''
s=s[:start]+replacement+s[end:]

p.write_text(s,encoding='utf-8')
