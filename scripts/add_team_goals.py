from pathlib import Path
import json

app_path=Path('app.py')
s=app_path.read_text(encoding='utf-8')

# 1) Helper puro para somar vendas por equipe, sem depender da visibilidade no ranking.
anchor='''def apply_team_labels(summary,cfg):\n    registry={normalize_text(x.get("vendedor")):x for x in cfg.get("vendedores",[])}\n    for item in summary:\n        seller=registry.get(normalize_text(item.get("vendedor")),{})\n        item["equipe"]=normalized_team(seller.get("equipe"),seller)\n    return summary\n\ndef performance(media):\n'''
replacement='''def apply_team_labels(summary,cfg):\n    registry={normalize_text(x.get("vendedor")):x for x in cfg.get("vendedores",[])}\n    for item in summary:\n        seller=registry.get(normalize_text(item.get("vendedor")),{})\n        item["equipe"]=normalized_team(seller.get("equipe"),seller)\n    return summary\n\ndef team_sales_totals(summary,cfg):\n    """Soma vendas por equipe usando a configuração gerencial, inclusive vendedores ocultos."""\n    registry={normalize_text(x.get("vendedor")):x for x in cfg.get("vendedores",[])}\n    totals={"Equipe Interna":0,"Equipe Externa":0}\n    excluded={"website","adm","freelance","canal nacional"}\n    for item in summary:\n        seller=registry.get(normalize_text(item.get("vendedor")),{})\n        if not seller.get("pertence_franquia",False):\n            continue\n        if normalize_text(seller.get("categoria",item.get("categoria",""))) in excluded:\n            continue\n        team=normalized_team(seller.get("equipe"),seller)\n        if team in totals:\n            totals[team]+=int(item.get("vendas",0) or 0)\n    return totals\n\ndef performance(media):\n'''
if anchor not in s:
    raise SystemExit('anchor apply_team_labels não encontrado')
s=s.replace(anchor,replacement,1)

# 2) Menu Gerencial: meta empresa + metas das duas equipes.
anchor='''    # A meta da empresa continua sendo a mesma variável usada por todos os cálculos.\n    # Apenas restauramos o controle gerencial que havia sido removido da interface.\n    cfg["meta_empresa"]=int(st.number_input("Meta do mês",min_value=0,value=int(cfg.get("meta_empresa",0)),step=1,key="gestao_meta_empresa"))\n\n    sales_by_seller={}\n'''
replacement='''    # Metas gerenciais. A meta da empresa mantém a mesma variável já usada nos cálculos;\n    # as metas de equipe são apenas novos parâmetros de acompanhamento visual.\n    meta_col1,meta_col2,meta_col3=st.columns(3)\n    cfg["meta_empresa"]=int(meta_col1.number_input("Meta do mês",min_value=0,value=int(cfg.get("meta_empresa",0)),step=1,key="gestao_meta_empresa"))\n    cfg["meta_equipe_interna"]=int(meta_col2.number_input("Meta Equipe Interna",min_value=0,value=int(cfg.get("meta_equipe_interna",0)),step=1,key="gestao_meta_equipe_interna"))\n    cfg["meta_equipe_externa"]=int(meta_col3.number_input("Meta Equipe Externa",min_value=0,value=int(cfg.get("meta_equipe_externa",0)),step=1,key="gestao_meta_equipe_externa"))\n\n    sales_by_seller={}\n'''
if anchor not in s:
    raise SystemExit('anchor metas gestão não encontrado')
s=s.replace(anchor,replacement,1)

# 3) Produção por canal: acrescenta dois cards de equipe sem remover os atuais.
anchor='''        st.markdown(channel_summary_html(channels,total),unsafe_allow_html=True)\n        render_general_report(st,team,rows,cfg,summary,all_days,elapsed,official,color)\n'''
replacement='''        st.markdown(channel_summary_html(channels,total),unsafe_allow_html=True)\n        team_totals=team_sales_totals(summary,cfg)\n        internal_sales=team_totals["Equipe Interna"]\n        external_sales=team_totals["Equipe Externa"]\n        internal_goal=int(cfg.get("meta_equipe_interna",0) or 0)\n        external_goal=int(cfg.get("meta_equipe_externa",0) or 0)\n        st.markdown(f'''\n        <style>\n        .team-goals-grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;margin-top:12px}}\n        .team-goal-card{{background:#fff;border:1px solid #E2E8F0;border-radius:14px;padding:15px 17px;box-shadow:0 3px 12px rgba(15,23,42,.05);min-width:0}}\n        .team-goal-card .tg-title{{font-size:.70rem;font-weight:900;color:#64748B;letter-spacing:.05em;text-transform:uppercase}}\n        .team-goal-card .tg-main{{display:flex;align-items:flex-end;gap:8px;margin-top:8px}}\n        .team-goal-card .tg-value{{font-size:2rem;font-weight:950;line-height:1;color:#0F172A}}\n        .team-goal-card .tg-label{{font-size:.62rem;font-weight:850;color:#64748B;padding-bottom:3px}}\n        .team-goal-card .tg-meta{{margin-top:9px;padding-top:8px;border-top:1px solid #E2E8F0;font-size:.72rem;font-weight:800;color:#475569}}\n        .team-goal-card .tg-meta b{{font-size:.92rem;color:#0F172A}}\n        @media(max-width:560px){{.team-goals-grid{{grid-template-columns:1fr 1fr;gap:7px}}.team-goal-card{{padding:11px 10px;border-radius:11px}}.team-goal-card .tg-value{{font-size:1.55rem}}.team-goal-card .tg-title{{font-size:.56rem}}.team-goal-card .tg-meta{{font-size:.60rem}}}}\n        @media(max-width:340px){{.team-goals-grid{{grid-template-columns:1fr}}}}\n        </style>\n        <div class="team-goals-grid">\n          <div class="team-goal-card">\n            <div class="tg-title">Equipe Interna</div>\n            <div class="tg-main"><div class="tg-value">{internal_sales}</div><div class="tg-label">VENDAS</div></div>\n            <div class="tg-meta">META <b>{internal_goal}</b></div>\n          </div>\n          <div class="team-goal-card">\n            <div class="tg-title">Equipe Externa</div>\n            <div class="tg-main"><div class="tg-value">{external_sales}</div><div class="tg-label">VENDAS</div></div>\n            <div class="tg-meta">META <b>{external_goal}</b></div>\n          </div>\n        </div>\n        ''',unsafe_allow_html=True)\n        render_general_report(st,team,rows,cfg,summary,all_days,elapsed,official,color)\n'''
if anchor not in s:
    raise SystemExit('anchor produção por canal não encontrado')
s=s.replace(anchor,replacement,1)
app_path.write_text(s,encoding='utf-8')

# 4) Defaults no config, preservando as demais configurações.
cfg_path=Path('config.json')
cfg=json.loads(cfg_path.read_text(encoding='utf-8'))
cfg.setdefault('meta_equipe_interna',0)
cfg.setdefault('meta_equipe_externa',0)
cfg_path.write_text(json.dumps(cfg,ensure_ascii=False,indent=2)+"\n",encoding='utf-8')

# 5) Teste simples da soma de equipes, inclusive vendedor oculto e exclusão de Outros Canais.
tests=Path('tests')
tests.mkdir(exist_ok=True)
Path('tests/test_team_sales.py').write_text('''from app import team_sales_totals\n\n\ndef test_team_sales_includes_hidden_and_excludes_other_channels():\n    summary=[\n        {"vendedor":"A","vendas":10,"categoria":"Vendedor"},\n        {"vendedor":"B","vendas":20,"categoria":"Vendedor"},\n        {"vendedor":"C","vendas":30,"categoria":"Vendedor"},\n        {"vendedor":"SITE","vendas":40,"categoria":"Website"},\n    ]\n    cfg={"vendedores":[\n        {"vendedor":"A","equipe":"Equipe Interna","pertence_franquia":True,"categoria":"Vendedor","ativo":True},\n        {"vendedor":"B","equipe":"Equipe Interna","pertence_franquia":True,"categoria":"Vendedor","ativo":False},\n        {"vendedor":"C","equipe":"Equipe Externa","pertence_franquia":True,"categoria":"Vendedor","ativo":True},\n        {"vendedor":"SITE","equipe":"Outros Canais","pertence_franquia":True,"categoria":"Website","ativo":True},\n    ]}\n    assert team_sales_totals(summary,cfg)=={"Equipe Interna":30,"Equipe Externa":30}\n''',encoding='utf-8')
