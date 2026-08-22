from pathlib import Path

# Corrige a identidade dos vendedores de forma normalizada para que variações de
# caixa, acento ou espaços não dividam as vendas de uma mesma pessoa.

app = Path('app.py')
s = app.read_text(encoding='utf-8')

old = '''def prepare_config(base,rows,month,year):
    cfg=copy.deepcopy(base); cfg["mes"],cfg["ano"]=month,year
    existing={normalize_text(x["vendedor"]):x for x in cfg.get("vendedores",[])}; sellers=[]
    for name in sorted({x["vendedor"] for x in rows},key=normalize_text):
        sample=next(x for x in rows if x["vendedor"]==name); old=existing.get(normalize_text(name),{})
        inferred=next((label for label in ("Website","ADM","Freelance") if normalize_text(label) in normalize_text(name)),sample["categoria"])
        registered=bool(old); belongs=old.get("pertence_franquia",registered)
        category=old.get("categoria",inferred if registered else "Canal Nacional")
        team_value=normalized_team(old.get("equipe"),old or {"setor":sample["setor"],"categoria":category})
        sellers.append({"vendedor":name,"setor":old.get("setor",sample["setor"]),"equipe":team_value,"categoria":category,
            "pertence_franquia":belongs,"classificado":old.get("classificado",registered),"ativo":old.get("ativo",registered),
            "experiencia":old.get("experiencia",False),"meta_individual":old.get("meta_individual",70),
            "trabalha_sabado":old.get("trabalha_sabado",True),"trabalha_domingo":old.get("trabalha_domingo",False),
            "data_inicio":old.get("data_inicio",f"{year}-01-01"),"data_desligamento":old.get("data_desligamento",""),"folgas":old.get("folgas",[])})
    cfg["vendedores"]=sellers; return cfg
'''

new = '''def prepare_config(base,rows,month,year):
    cfg=copy.deepcopy(base); cfg["mes"],cfg["ano"]=month,year
    existing={normalize_text(x["vendedor"]):x for x in cfg.get("vendedores",[])}; sellers=[]

    # Um mesmo vendedor pode chegar do sistema com diferenças de caixa, acento
    # ou espaços. A configuração precisa ter UMA identidade por nome normalizado.
    grouped={}
    for row in rows:
        key=normalize_text(row.get("vendedor",""))
        if not key:continue
        grouped.setdefault(key,[]).append(row)

    for key in sorted(grouped):
        group=grouped[key]
        sample=group[0]
        previous=existing.get(key,{})
        # Se já existe cadastro, preserva o nome oficial cadastrado; caso contrário
        # usa a grafia mais frequente recebida no relatório.
        if previous.get("vendedor"):
            name=previous["vendedor"]
        else:
            variants={}
            for item in group:
                raw=str(item.get("vendedor","")).strip()
                variants[raw]=variants.get(raw,0)+1
            name=max(variants,key=lambda value:(variants[value],len(value)))
        inferred=next((label for label in ("Website","ADM","Freelance") if normalize_text(label) in key),sample["categoria"])
        registered=bool(previous); belongs=previous.get("pertence_franquia",registered)
        category=previous.get("categoria",inferred if registered else "Canal Nacional")
        team_value=normalized_team(previous.get("equipe"),previous or {"setor":sample["setor"],"categoria":category})
        sellers.append({"vendedor":name,"setor":previous.get("setor",sample["setor"]),"equipe":team_value,"categoria":category,
            "pertence_franquia":belongs,"classificado":previous.get("classificado",registered),"ativo":previous.get("ativo",registered),
            "experiencia":previous.get("experiencia",False),"meta_individual":previous.get("meta_individual",70),
            "trabalha_sabado":previous.get("trabalha_sabado",True),"trabalha_domingo":previous.get("trabalha_domingo",False),
            "data_inicio":previous.get("data_inicio",f"{year}-01-01"),"data_desligamento":previous.get("data_desligamento",""),"folgas":previous.get("folgas",[])})
    cfg["vendedores"]=sellers; return cfg
'''

if old not in s:
    raise SystemExit('prepare_config original não encontrado')
s=s.replace(old,new,1)
app.write_text(s,encoding='utf-8')

painel=Path('gerar_painel.py')
g=painel.read_text(encoding='utf-8')
old2='''    by=defaultdict(list)
    for row in rows:
        if row["data_venda"].year==year and row["data_venda"].month==month and row["data_venda"]<=cutoff: by[row["vendedor"]].append(row)
    total=sum(len(x) for x in by.values()); official="maior_ou_igual_1000" if total>=cfg["limite_cenario_maior"] else "abaixo_1000"
    result=[]
    for seller in cfg["vendedores"]:
        name=seller["vendedor"]; sales=by[name]; qty=len(sales); selling_days={x["data_venda"] for x in sales}
'''
new2='''    by=defaultdict(list)
    for row in rows:
        if row["data_venda"].year==year and row["data_venda"].month==month and row["data_venda"]<=cutoff:
            # A contagem é feita pela identidade normalizada do vendedor. Isso evita
            # perder vendas quando o sistema exporta, por exemplo, DANIELE..., Daniele...
            # ou o mesmo nome com variações de acento/espaçamento.
            key=normalize_seller_name(row.get("vendedor",""))
            if key:by[key].append(row)
    total=sum(len(x) for x in by.values()); official="maior_ou_igual_1000" if total>=cfg["limite_cenario_maior"] else "abaixo_1000"
    result=[]
    for seller in cfg["vendedores"]:
        name=seller["vendedor"]; sales=by[normalize_seller_name(name)]; qty=len(sales); selling_days={x["data_venda"] for x in sales}
'''
if old2 not in g:
    raise SystemExit('bloco summarize original não encontrado')
g=g.replace(old2,new2,1)

marker='''def parse_date(value): return datetime.strptime(value.strip(), "%Y-%m-%d").date()\n'''
helper='''def normalize_seller_name(value):\n    import unicodedata, re\n    text=unicodedata.normalize("NFKD",str(value or "")).encode("ascii","ignore").decode().lower()\n    return re.sub(r"[^a-z0-9]+"," ",text).strip()\n\n'''
if 'def normalize_seller_name(' not in g:
    if marker not in g:raise SystemExit('ponto do helper não encontrado')
    g=g.replace(marker,helper+marker,1)
painel.write_text(g,encoding='utf-8')
