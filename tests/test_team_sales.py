from app import team_sales_totals


def test_team_sales_includes_hidden_and_excludes_other_channels():
    summary=[
        {"vendedor":"A","vendas":10,"categoria":"Vendedor"},
        {"vendedor":"B","vendas":20,"categoria":"Vendedor"},
        {"vendedor":"C","vendas":30,"categoria":"Vendedor"},
        {"vendedor":"SITE","vendas":40,"categoria":"Website"},
    ]
    cfg={"vendedores":[
        {"vendedor":"A","equipe":"Equipe Interna","pertence_franquia":True,"categoria":"Vendedor","ativo":True},
        {"vendedor":"B","equipe":"Equipe Interna","pertence_franquia":True,"categoria":"Vendedor","ativo":False},
        {"vendedor":"C","equipe":"Equipe Externa","pertence_franquia":True,"categoria":"Vendedor","ativo":True},
        {"vendedor":"SITE","equipe":"Outros Canais","pertence_franquia":True,"categoria":"Website","ativo":True},
    ]}
    assert team_sales_totals(summary,cfg)=={"Equipe Interna":30,"Equipe Externa":30}
