from pathlib import Path

path=Path('app.py')
s=path.read_text(encoding='utf-8')

old_header='''    with st.container(key="cdt_top_header"):\n        header_main,header_menu=st.columns([8.6,1.0],vertical_alignment="center")\n        with header_main:\n            st.markdown(\n                '<div class="cdt-brandline">Cartão de TODOS</div>'\n                '<div class="cdt-title">PAINEL COMERCIAL</div>'\n                '<div class="cdt-unit">Afogados</div>'\n                f'<div class="cdt-session"><span aria-hidden="true">👤</span><span class="cdt-session-name">{user_name}</span></div>',\n                unsafe_allow_html=True\n            )\n        with header_menu:\n            with st.popover("⋮",use_container_width=True):\n                st.markdown(f'<div class="cdt-menu-user">👤 {user_name}</div>',unsafe_allow_html=True)\n                if management_available and st.button("⚙ Gestão",key="cdt_menu_management",use_container_width=True):\n                    st.session_state.area="GESTÃO"\n                    st.rerun()\n                if st.button("↪ Sair",key="cdt_menu_logout",use_container_width=True):\n                    for key in ("dashboard_autenticado","dashboard_usuario","dashboard_auth_token","seller_detail","gestor_autenticado","login_duplicate_first"):\n                        st.session_state.pop(key,None)\n                    st.session_state.area="VISÃO GERAL"\n                    st.query_params.clear()\n                    st.rerun()\n'''
new_header='''    with st.container(key="cdt_top_header"):\n        header_main,header_account=st.columns([7.5,2.5],vertical_alignment="center")\n        with header_main:\n            st.markdown(\n                '<div class="cdt-brandline">Cartão de TODOS</div>'\n                '<div class="cdt-title">PAINEL COMERCIAL</div>'\n                '<div class="cdt-unit">Afogados</div>',\n                unsafe_allow_html=True\n            )\n        with header_account:\n            account_label=f"◉ {user_name_raw}  ▾"\n            with st.popover(account_label,use_container_width=True):\n                if management_available and st.button("⚙ Gestão",key="cdt_menu_management",use_container_width=True):\n                    st.session_state.area="GESTÃO"\n                    st.rerun()\n                if st.button("↪ Sair",key="cdt_menu_logout",use_container_width=True):\n                    for key in ("dashboard_autenticado","dashboard_usuario","dashboard_auth_token","seller_detail","gestor_autenticado","login_duplicate_first"):\n                        st.session_state.pop(key,None)\n                    st.session_state.area="VISÃO GERAL"\n                    st.query_params.clear()\n                    st.rerun()\n'''
if old_header not in s:
    raise SystemExit('Bloco atual do cabeçalho não localizado')
s=s.replace(old_header,new_header,1)

css=r'''
/* Conta/sessão agrupada no cabeçalho — UI/UX apenas. */
.st-key-cdt_top_header [data-testid="stHorizontalBlock"]{align-items:center!important}
.st-key-cdt_top_header [data-testid="stPopover"]{display:flex!important;justify-content:flex-end!important;width:100%!important}
.st-key-cdt_top_header [data-testid="stPopover"]>button{width:auto!important;max-width:100%!important;min-width:0!important;height:34px!important;min-height:34px!important;padding:0 10px!important;border-radius:9px!important;background:rgba(255,255,255,.11)!important;border:1px solid rgba(255,255,255,.20)!important;color:#fff!important;font-size:.68rem!important;font-weight:800!important;line-height:1!important;box-shadow:none!important;white-space:nowrap!important;overflow:hidden!important;text-overflow:ellipsis!important;justify-content:flex-end!important}
.st-key-cdt_top_header [data-testid="stPopover"]>button:hover{background:rgba(255,255,255,.18)!important;border-color:rgba(255,255,255,.28)!important}
div[data-testid="stPopoverBody"]{min-width:155px!important;max-width:220px!important;border-radius:10px!important;box-shadow:0 10px 28px rgba(15,23,42,.16)!important;padding:5px!important}
div[data-testid="stPopoverBody"] .stButton{margin:0!important}
div[data-testid="stPopoverBody"] .stButton button{min-height:34px!important;padding:6px 9px!important;border-radius:7px!important;background:transparent!important;color:#334155!important;border:0!important;font-size:.72rem!important;font-weight:800!important;justify-content:flex-start!important;box-shadow:none!important}
div[data-testid="stPopoverBody"] .stButton button:hover{background:#F1F5F9!important;color:#075B35!important}
@media(max-width:700px){
 .st-key-cdt_top_header [data-testid="stHorizontalBlock"]{gap:.35rem!important}
 .st-key-cdt_top_header [data-testid="column"]:first-child{min-width:0!important}
 .st-key-cdt_top_header [data-testid="column"]:last-child{min-width:112px!important;max-width:46%!important}
 .st-key-cdt_top_header [data-testid="stPopover"]>button{height:31px!important;min-height:31px!important;padding:0 8px!important;font-size:.60rem!important;max-width:100%!important}
}
@media(max-width:430px){
 .st-key-cdt_top_header [data-testid="stHorizontalBlock"]{align-items:flex-start!important}
 .st-key-cdt_top_header [data-testid="column"]:last-child{min-width:105px!important;max-width:48%!important}
 .st-key-cdt_top_header [data-testid="stPopover"]>button{font-size:.57rem!important;padding:0 7px!important}
}
@media(max-width:340px){
 .st-key-cdt_top_header [data-testid="column"]:last-child{min-width:96px!important;max-width:47%!important}
 .st-key-cdt_top_header [data-testid="stPopover"]>button{font-size:.54rem!important;padding:0 6px!important}
}
'''
if '/* Conta/sessão agrupada no cabeçalho — UI/UX apenas. */' not in s:
    s=s.replace('\n</style>"""',css+'\n</style>"""',1)

path.write_text(s,encoding='utf-8')
