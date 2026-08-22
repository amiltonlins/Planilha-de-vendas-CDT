from pathlib import Path

p=Path('app.py')
s=p.read_text(encoding='utf-8')

old='''def merge_registry(base,current):\n    # A planilha importada é a fonte de verdade para a existência de vendedores.\n    # Não reintroduzir vendedores pré-cadastrados do config base na operação diária.\n    # As configurações administrativas já persistidas continuam sendo preservadas.\n    cfg=copy.deepcopy(current or base)\n    if current is not None:\n        cfg["vendedores"]=copy.deepcopy(current.get("vendedores",[]))\n    return cfg\n'''
new='''def merge_registry(base,current):\n    # A planilha importada é a fonte de verdade para a existência de vendedores.\n    # Não reintroduzir vendedores pré-cadastrados do config base na operação diária.\n    # As configurações administrativas já persistidas continuam sendo preservadas.\n    cfg=copy.deepcopy(current or base)\n    if current is not None:\n        cfg["vendedores"]=copy.deepcopy(current.get("vendedores",[]))\n    # Migração de compatibilidade: versões anteriores podiam deixar um vendedor\n    # ATIVO com categoria "Canal Nacional". Nesse estado ele ficava invisível no\n    # ranking porque a elegibilidade exige vendedor ativo + franquia + categoria local.\n    # Se o gestor marcou o vendedor para exibir no Dashboard/Ranking, essa intenção\n    # administrativa prevalece e o cadastro é normalizado como vendedor da franquia.\n    for seller in cfg.get("vendedores",[]):\n        if seller.get("ativo",False):\n            seller["pertence_franquia"]=True\n            if normalize_text(seller.get("categoria")) in {"canal nacional",""}:\n                seller["categoria"]="Vendedor"\n    return cfg\n'''
if old not in s: raise SystemExit('merge_registry block not found')
s=s.replace(old,new,1)

old='''                if seller["ativo"] and not seller.get("pertence_franquia",False):\n                    seller["pertence_franquia"]=True\n                    if normalize_text(seller.get("categoria")) in {"canal nacional",""}:seller["categoria"]="Vendedor"\n                seller["classificado"]=True\n'''
new='''                if seller["ativo"]:\n                    seller["pertence_franquia"]=True\n                    if normalize_text(seller.get("categoria")) in {"canal nacional",""}:seller["categoria"]="Vendedor"\n                seller["classificado"]=True\n'''
if old not in s: raise SystemExit('management active block not found')
s=s.replace(old,new,1)

p.write_text(s,encoding='utf-8')
