from pathlib import Path

p=Path('app.py')
s=p.read_text(encoding='utf-8')

old='''    st.markdown("#### PERÍODO DE REFERÊNCIA")\n    month_names=("Janeiro","Fevereiro","Março","Abril","Maio","Junho","Julho","Agosto","Setembro","Outubro","Novembro","Dezembro")\n    st.info(f'{month_names[int(cfg["mes"])-1]} / {cfg["ano"]} · cálculos de dias, semanas e projeções continuam usando a lógica atual do sistema.')\n\n    sales_by_seller={}\n'''
new='''    st.markdown("#### PERÍODO DE REFERÊNCIA")\n    month_names=("Janeiro","Fevereiro","Março","Abril","Maio","Junho","Julho","Agosto","Setembro","Outubro","Novembro","Dezembro")\n    st.info(f'{month_names[int(cfg["mes"])-1]} / {cfg["ano"]} · cálculos de dias, semanas e projeções continuam usando a lógica atual do sistema.')\n\n    # A meta da empresa continua sendo a mesma variável usada por todos os cálculos.\n    # Apenas restauramos o controle gerencial que havia sido removido da interface.\n    cfg["meta_empresa"]=int(st.number_input("Meta do mês",min_value=0,value=int(cfg.get("meta_empresa",0)),step=1,key="gestao_meta_empresa"))\n\n    sales_by_seller={}\n'''
if old not in s:
    raise SystemExit('bloco de período/meta não encontrado')
s=s.replace(old,new,1)

old='''        registered=bool(previous)\n        # Vendedor novo nasce apenas como identificado pela planilha. As decisões\n        # administrativas de equipe/visibilidade vêm depois e não filtram suas vendas.\n        belongs=previous.get("pertence_franquia",False)\n        category=previous.get("categoria",inferred if registered else "Vendedor")\n        team_value=normalized_team(previous.get("equipe"),previous or {"setor":sample["setor"],"categoria":category})\n        sellers.append({"vendedor":name,"setor":previous.get("setor",sample["setor"]),"equipe":team_value,"categoria":category,\n            "pertence_franquia":belongs,"classificado":previous.get("classificado",registered),"ativo":previous.get("ativo",registered),\n'''
new='''        registered=bool(previous)\n        # Vendedor novo nasce apenas como identificado pela planilha. As decisões\n        # administrativas de equipe/visibilidade vêm depois e não filtram suas vendas.\n        belongs=previous.get("pertence_franquia",False)\n        category=previous.get("categoria",inferred if registered else "Vendedor")\n        team_value=normalized_team(previous.get("equipe"),previous or {"setor":sample["setor"],"categoria":category})\n        # Compatibilidade com cadastros antigos: quando o estado persistido foi perdido\n        # em um redeploy, recuperamos somente vendedores conhecidos no config base.\n        # Isso não cria vendas nem altera cálculos; apenas restaura a intenção de exibição.\n        fallback_base=next((x for x in BASE_SELLER_DEFAULTS if normalize_text(x.get("vendedor"))==key),{})\n        active_default=bool(fallback_base.get("ativo",False)) if not registered else False\n        franchise_default=bool(fallback_base.get("pertence_franquia",False)) if not registered else False\n        if not registered and fallback_base:\n            belongs=franchise_default\n            category=fallback_base.get("categoria",category)\n            team_value=normalized_team(fallback_base.get("equipe"),fallback_base)\n        sellers.append({"vendedor":name,"setor":previous.get("setor",sample["setor"]),"equipe":team_value,"categoria":category,\n            "pertence_franquia":belongs,"classificado":previous.get("classificado",registered or bool(fallback_base)),"ativo":previous.get("ativo",active_default if fallback_base else registered),\n'''
if old not in s:
    raise SystemExit('bloco de defaults do vendedor não encontrado')
s=s.replace(old,new,1)

old='''PUBLISHED_PATH=Path(os.environ.get("PAINEL_DATA_PATH",ROOT/"data"/"dados_publicados.json"))\nALIASES={\n'''
new='''PUBLISHED_PATH=Path(os.environ.get("PAINEL_DATA_PATH",ROOT/"data"/"dados_publicados.json"))\nBASE_SELLER_DEFAULTS=[]\nALIASES={\n'''
if old not in s:
    raise SystemExit('PUBLISHED_PATH não encontrado')
s=s.replace(old,new,1)

old='''    base=json.loads((ROOT/"config.json").read_text(encoding="utf-8"))\n    try:rows,cfg,metadata=load_published(base)\n'''
new='''    base=json.loads((ROOT/"config.json").read_text(encoding="utf-8"))\n    global BASE_SELLER_DEFAULTS\n    BASE_SELLER_DEFAULTS=copy.deepcopy(base.get("vendedores",[]))\n    try:rows,cfg,metadata=load_published(base)\n'''
if old not in s:
    raise SystemExit('render_app base config não encontrado')
s=s.replace(old,new,1)

p.write_text(s,encoding='utf-8')
