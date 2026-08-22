from pathlib import Path
p=Path('app.py')
s=p.read_text(encoding='utf-8')

# Relatório visual usa a nova classificação de equipe.
s=s.replace('cols=[("setor","SETOR"),("vendedor","VENDEDOR")','cols=[("equipe","EQUIPE"),("vendedor","VENDEDOR")',1)

# Opção geral do filtro conforme nomenclatura solicitada.
s=s.replace('("Todas as Equipes",)+TEAM_OPTIONS','("TODAS AS EQUIPES",)+TEAM_OPTIONS',1)
s=s.replace('team_filter=="Todas as Equipes"','team_filter=="TODAS AS EQUIPES"',1)

# Preserva exatamente o empilhamento nome/equipe no desktop e garante que o mobile caiba sem mascarar overflow.
css='''\n.rank-mobile-head>div:first-child{display:flex;flex-direction:column;min-width:0}\n@media(max-width:560px){\n[data-testid="stDialog"] [role="dialog"]{overflow-x:visible!important}\n[data-testid="stDialog"] [role="dialog"]>div{overflow-x:visible!important}\n}\n'''
if '.rank-mobile-head>div:first-child{display:flex;flex-direction:column;min-width:0}' not in s:
    s=s.replace('</style>',css+'\n</style>',1)

p.write_text(s,encoding='utf-8')
