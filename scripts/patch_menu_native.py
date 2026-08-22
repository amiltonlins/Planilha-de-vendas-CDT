from pathlib import Path

p=Path('app.py')
s=p.read_text(encoding='utf-8')
old='''    areas=["VISÃO GERAL","VENDEDORES","SEMANAL","PREMIAÇÕES","GESTÃO"]\n    if "area" not in st.session_state:st.session_state.area="VISÃO GERAL"\n    requested=st.query_params.get("area")\n    if requested in areas:st.session_state.area=requested\n    area=st.session_state.area\n    import urllib.parse\n    nav=''.join(\n        f'<a class="top-nav-item {"active" if item==area else ""}" href="?area={urllib.parse.quote(item)}" target="_self">{html.escape(item)}</a>'\n        for item in areas\n    )\n    st.markdown(\n        '<div class="bi-topbar bi-topbar-nav">'\n        '<div class="bi-brand"><h1>PAINEL COMERCIAL — AFOGADOS</h1><p>Visão executiva de produção, performance, histórico e remuneração variável</p></div>'\n        f'<nav class="top-nav">{nav}</nav>'\n        '</div>',unsafe_allow_html=True\n    )\n'''
new='''    areas=["VISÃO GERAL","VENDEDORES","SEMANAL","PREMIAÇÕES","GESTÃO"]\n    if "area" not in st.session_state:st.session_state.area="VISÃO GERAL"\n    st.markdown(\n        '<div class="bi-topbar bi-topbar-nav">'\n        '<div class="bi-brand"><h1>PAINEL COMERCIAL — AFOGADOS</h1><p>Visão executiva de produção, performance, histórico e remuneração variável</p></div>'\n        '</div>',unsafe_allow_html=True\n    )\n    selected_area=st.segmented_control(\n        "Navegação",\n        areas,\n        default=st.session_state.area,\n        key="top_nav_area",\n        label_visibility="collapsed",\n    )\n    if selected_area and selected_area != st.session_state.area:\n        st.session_state.area=selected_area\n        st.rerun()\n    area=st.session_state.area\n'''
if old not in s:
    raise SystemExit('bloco atual da navegação não encontrado')
s=s.replace(old,new,1)

css='''\n/* Navegação nativa: troca apenas a área da aplicação, sem abrir nova página/aba. */\n[data-testid="stSegmentedControl"]{margin-top:-18px;margin-bottom:10px;background:#172554;border-radius:0 0 14px 14px;padding:0 16px 14px}\n[data-testid="stSegmentedControl"] button{color:#CBD5E1!important;border-color:rgba(255,255,255,.16)!important;font-weight:800!important;font-size:.68rem!important}\n[data-testid="stSegmentedControl"] button[aria-pressed="true"]{background:#FFFFFF!important;color:#0F172A!important;border-color:#FFFFFF!important}\n[data-testid="stSegmentedControl"] button:hover{background:rgba(255,255,255,.10)!important;color:white!important}\n@media(max-width:720px){[data-testid="stSegmentedControl"]{padding:0 8px 10px;overflow-x:auto}[data-testid="stSegmentedControl"]>div{min-width:max-content}[data-testid="stSegmentedControl"] button{font-size:.58rem!important;padding-left:8px!important;padding-right:8px!important}}\n'''
if 'Navegação nativa: troca apenas a área' not in s:
    s=s.replace('</style>',css+'\n</style>',1)

p.write_text(s,encoding='utf-8')
