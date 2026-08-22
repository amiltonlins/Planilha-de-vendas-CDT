from pathlib import Path

p=Path('app.py')
s=p.read_text(encoding='utf-8')

# 1) Ranking mobile nativo: mantém o ranking desktop exatamente como está e evita reload/segunda autenticação.
marker='def daily_series(rows,cfg,data_until):\n'
insert='''def mobile_ranking_metrics_html(x):
    meta_pct=x["projecao"]/x["meta_individual"] if x["meta_individual"] else 0
    return (
        '<div class="mobile-rank-metrics">'
        f'<span class="m-main"><strong>{x["vendas"]}</strong><small>VENDAS</small></span>'
        f'<span class="m-main"><strong>{x["projecao"]}</strong><small>PROJEÇÃO</small></span>'
        f'<span class="m-rhythm"><strong>{x["media"]:.2f}</strong><small>MÉDIA/DIA</small></span>'
        f'<span class="m-rhythm"><strong>{x["zeros"]}</strong><small>ZEROS</small></span>'
        f'<span class="m-rhythm"><strong>{pct(meta_pct)}</strong><small>% META</small></span>'
        f'<span class="m-neo"><strong>{x["neo"]}</strong><small>NEO</small></span>'
        f'<span class="m-neo"><strong>{pct(x["neo_pct"])}</strong><small>% NEO</small></span>'
        f'<span class="m-award"><strong>{money(x["base"])}</strong><small>PREMIAÇÃO ATUAL</small></span>'
        f'<span class="m-award"><strong>{money(x["comissao_proj"])}</strong><small>PREMIAÇÃO PROJ.</small></span>'
        f'<span class="m-award"><strong>{money(x["bonus_neo_proj"])}</strong><small>BÔNUS NEO PROJ.</small></span>'
        f'<span class="m-award"><strong>{money(x["bonus_adim_proj"])}</strong><small>BÔNUS (SE) 100% ADIM</small></span>'
        f'<span class="m-award m-weekly"><strong>{money(x["premio_total"])}</strong><small>SEMANAIS</small></span>'
        f'<span class="m-total"><strong>{money(x["total_variavel_proj"])}</strong><small>TOTAL VAR. PROJ.</small></span>'
        '</div>'
    )

def render_mobile_ranking(st,ranking):
    medals=("🥇","🥈","🥉")
    if not ranking:
        st.markdown('<div class="empty-bi">Nenhum vendedor local ativo para exibir no ranking.</div>',unsafe_allow_html=True)
        return
    for i,x in enumerate(ranking):
        _,color,_=performance(x["media"])
        medal=medals[i] if i<3 else f"{i+1}º"
        meta_pct=x["projecao"]/x["meta_individual"] if x["meta_individual"] else 0
        status_emoji,status_message=projection_status_visual(meta_pct,x.get("meta_individual"),x.get("projecao"))
        key=f"mobile_rank_card_{i}"
        st.markdown(
            f'<style>.st-key-{key}{{background:{color};border-radius:12px;padding:8px 9px 9px;margin:0 0 7px;box-shadow:0 2px 8px rgba(15,23,42,.10);color:white}}'
            f'.st-key-{key} .stButton button{{background:transparent!important;border:0!important;color:white!important;min-height:0!important;padding:0!important;box-shadow:none!important;justify-content:flex-start!important;text-align:left!important;font-size:.82rem!important;font-weight:900!important;line-height:1.08!important}}'
            f'.st-key-{key} .stButton button:hover{{background:transparent!important;color:white!important}}</style>',
            unsafe_allow_html=True,
        )
        with st.container(key=key):
            left,right=st.columns([5,2],vertical_alignment="center")
            with left:
                st.markdown(f'<div class="mobile-rank-position">{medal}</div>',unsafe_allow_html=True)
                if st.button(x["vendedor"],key=f"open_mobile_seller_{i}",use_container_width=True):
                    st.session_state.seller_detail=x["vendedor"]
                    st.rerun()
                st.markdown(f'<div class="mobile-rank-team">{html.escape(x.get("equipe","Equipe Interna"))}</div>',unsafe_allow_html=True)
            with right:
                st.markdown(f'<div class="mobile-rank-status-native"><strong>{status_emoji}</strong><small>{html.escape(status_message)}</small></div>',unsafe_allow_html=True)
            st.markdown(mobile_ranking_metrics_html(x),unsafe_allow_html=True)

'''
if 'def render_mobile_ranking(' not in s:
    if marker not in s:raise SystemExit('ponto de inserção do ranking mobile não encontrado')
    s=s.replace(marker,insert+marker,1)

# 2) Cabeçalho: remove navegação por links/querystring e usa botões nativos, preservando a sessão.
old='''    action=st.query_params.get("action")
    if action=="logout":
        for key in ("dashboard_autenticado","dashboard_usuario","seller_detail","gestor_autenticado","login_duplicate_first"):
            st.session_state.pop(key,None)
        st.session_state.area="VISÃO GERAL"
        st.query_params.clear()
        st.rerun()
    if action=="management":
        st.session_state.area="GESTÃO"
        try:del st.query_params["action"]
        except KeyError:pass
    user_name=html.escape(str(st.session_state.get("dashboard_usuario") or "Usuário autenticado"))
    st.markdown(
        '<div class="bi-topbar bi-topbar-nav integrated-header">'
        '<div class="bi-brand"><h1>PAINEL COMERCIAL — AFOGADOS</h1><p>Visão executiva de produção, performance, histórico e remuneração variável</p></div>'
        f'<div class="header-account"><span class="header-user">{user_name}</span><div class="header-actions"><a href="?action=management" target="_self">GESTÃO</a><a href="?action=logout" target="_self">SAIR</a></div></div>'
        '</div>',unsafe_allow_html=True
    )
'''
new='''    user_name=html.escape(str(st.session_state.get("dashboard_usuario") or "Usuário autenticado"))
    with st.container(key="integrated_header_native"):
        header_main,header_account=st.columns([6,2],vertical_alignment="center")
        with header_main:
            st.markdown('<div class="native-header-brand"><h1>PAINEL COMERCIAL — AFOGADOS</h1><p>Visão executiva de produção, performance, histórico e remuneração variável</p></div>',unsafe_allow_html=True)
        with header_account:
            st.markdown(f'<div class="native-header-user">{user_name}</div>',unsafe_allow_html=True)
            action_gestao,action_sair=st.columns(2)
            if action_gestao.button("GESTÃO",key="header_management",use_container_width=True):
                st.session_state.area="GESTÃO"
                st.rerun()
            if action_sair.button("SAIR",key="header_logout",use_container_width=True):
                for key in ("dashboard_autenticado","dashboard_usuario","seller_detail","gestor_autenticado","login_duplicate_first"):
                    st.session_state.pop(key,None)
                st.session_state.area="VISÃO GERAL"
                st.query_params.clear()
                st.rerun()
'''
if old not in s:raise SystemExit('cabeçalho atual não encontrado')
s=s.replace(old,new,1)

# 3) Visão geral: desktop permanece no ranking_html atual; mobile usa renderer nativo sem reload.
old='''        ranking=sorted(filtered_team,key=lambda x:(x["vendas"],x["projecao"]),reverse=True); st.markdown(ranking_html(ranking),unsafe_allow_html=True)
'''
new='''        ranking=sorted(filtered_team,key=lambda x:(x["vendas"],x["projecao"]),reverse=True)
        if is_mobile_client(st):render_mobile_ranking(st,ranking)
        else:st.markdown(ranking_html(ranking),unsafe_allow_html=True)
'''
if old not in s:raise SystemExit('renderização atual do ranking não encontrada')
s=s.replace(old,new,1)

# 4) Texto administrativo coerente com a nova classificação de equipes.
s=s.replace('Eles ficam em CANAL NACIONAL até você ativá-los como franquia.','Eles ficam em OUTROS CANAIS até você classificá-los/ativá-los corretamente.')

# 5) CSS: ranking mobile em blocos lógicos, cabeçalho nativo integrado e correção real do overflow do dialog.
css='''
/* Cabeçalho integrado com ações nativas: evita reload e preserva sessão autenticada. */
.st-key-integrated_header_native{background:linear-gradient(110deg,#0F172A,#172554);color:white;border-radius:14px;padding:15px 18px;margin:0 0 10px;box-shadow:0 8px 30px rgba(15,23,42,.12)}
.st-key-integrated_header_native .native-header-brand h1{font-size:1.42rem;margin:0;font-weight:800;letter-spacing:-.02em;color:white}.st-key-integrated_header_native .native-header-brand p{margin:4px 0 0;color:#CBD5E1;font-size:.78rem}.native-header-user{text-align:right;color:#E2E8F0;font-size:.72rem;font-weight:850;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin-bottom:5px}.st-key-integrated_header_native .stButton button{min-height:32px!important;padding:0 8px!important;background:transparent!important;border:1px solid rgba(255,255,255,.25)!important;color:white!important;font-size:.62rem!important;font-weight:900!important}.st-key-integrated_header_native .stButton button:hover{background:rgba(255,255,255,.10)!important;color:white!important}

/* Ranking mobile: organização específica, sem tocar no ranking desktop. */
.mobile-rank-position{font-size:.72rem;font-weight:900;color:white;margin-bottom:2px}.mobile-rank-team{font-size:.52rem;font-weight:700;color:rgba(255,255,255,.84);margin-top:2px;text-transform:uppercase}.mobile-rank-status-native{display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;color:white}.mobile-rank-status-native strong{font-size:1.45rem;line-height:1}.mobile-rank-status-native small{font-size:.44rem;line-height:1.05;font-weight:900;color:rgba(255,255,255,.94);margin-top:3px}.mobile-rank-metrics{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:4px;margin-top:7px}.mobile-rank-metrics span{display:flex;flex-direction:column;align-items:center;justify-content:center;min-width:0;min-height:40px;padding:4px 3px;border-radius:7px;background:rgba(255,255,255,.07);text-align:center;box-sizing:border-box}.mobile-rank-metrics strong{font-size:.74rem;line-height:1.05;color:white;font-weight:900;max-width:100%;overflow-wrap:anywhere}.mobile-rank-metrics small{font-size:.40rem;line-height:1.05;color:rgba(255,255,255,.84);font-weight:800;margin-top:3px}.mobile-rank-metrics .m-main{grid-column:span 3;min-height:50px;background:rgba(15,23,42,.19)}.mobile-rank-metrics .m-main strong{font-size:1.16rem}.mobile-rank-metrics .m-rhythm{grid-column:span 2}.mobile-rank-metrics .m-neo{grid-column:span 3;background:rgba(255,255,255,.13)}.mobile-rank-metrics .m-neo strong{font-size:.9rem}.mobile-rank-metrics .m-award{grid-column:span 3}.mobile-rank-metrics .m-weekly{grid-column:span 6}.mobile-rank-metrics .m-total{grid-column:span 6;min-height:47px;background:rgba(15,23,42,.24)}.mobile-rank-metrics .m-total strong{font-size:1.02rem}

@media(max-width:560px){
.st-key-integrated_header_native{padding:10px 11px;border-radius:10px}.st-key-integrated_header_native [data-testid="stHorizontalBlock"]{gap:.45rem!important}.st-key-integrated_header_native .native-header-brand h1{font-size:.93rem!important;line-height:1.08}.st-key-integrated_header_native .native-header-brand p{display:none}.native-header-user{font-size:.56rem;margin-bottom:4px;max-width:100%}.st-key-integrated_header_native .stButton button{min-height:27px!important;padding:0 5px!important;font-size:.50rem!important}

/* Dialog: dimensionamento real, sem elementos forçando largura maior que a viewport. */
[data-testid="stDialog"] [role="dialog"]{box-sizing:border-box!important;width:calc(100vw - 16px)!important;max-width:calc(100vw - 16px)!important;min-width:0!important;max-height:94dvh!important;margin:3dvh auto!important}
[data-testid="stDialog"] [role="dialog"]>div{box-sizing:border-box!important;width:100%!important;max-width:100%!important;min-width:0!important;max-height:94dvh!important;overflow-y:auto!important;padding:.58rem!important}
[data-testid="stDialog"] [role="dialog"] *,[data-testid="stDialog"] .seller-mobile-primary,[data-testid="stDialog"] .seller-kpi-grid,[data-testid="stDialog"] .seller-kpi,[data-testid="stDialog"] .seller-dialog-meta{box-sizing:border-box!important;min-width:0!important;max-width:100%!important}
[data-testid="stDialog"] .seller-mobile-primary{width:100%!important;grid-template-columns:repeat(2,minmax(0,1fr))!important;gap:5px!important;margin:0 0 6px!important}
[data-testid="stDialog"] .seller-kpi-grid{width:100%!important;grid-template-columns:repeat(2,minmax(0,1fr))!important;gap:5px!important}
[data-testid="stDialog"] .seller-kpi{width:100%!important;padding:7px 6px!important;border-radius:9px!important}
[data-testid="stDialog"] .seller-kpi strong{font-size:clamp(.76rem,3.25vw,.91rem)!important;line-height:1.06!important;white-space:normal!important;overflow-wrap:anywhere!important;word-break:normal!important}
[data-testid="stDialog"] .seller-mobile-primary .seller-kpi strong{font-size:clamp(.98rem,4.4vw,1.18rem)!important}
[data-testid="stDialog"] .seller-kpi small{font-size:.46rem!important;line-height:1.05!important}.seller-dialog-meta{width:100%!important;margin:-2px 0 5px!important;padding:5px 7px!important}.seller-group-title{margin:6px 0 4px!important}
}
@media(max-width:340px){[data-testid="stDialog"] [role="dialog"]{width:calc(100vw - 12px)!important;max-width:calc(100vw - 12px)!important}[data-testid="stDialog"] .seller-kpi-grid,[data-testid="stDialog"] .seller-mobile-primary{gap:4px!important}[data-testid="stDialog"] .seller-kpi{padding:6px 5px!important}.mobile-rank-metrics strong{font-size:.70rem}.mobile-rank-metrics small{font-size:.38rem}}
'''
# Remove regra conflitante que reabria overflow horizontal do dialog no final do CSS.
conflict='''@media(max-width:560px){
[data-testid="stDialog"] [role="dialog"]{overflow-x:visible!important}
[data-testid="stDialog"] [role="dialog"]>div{overflow-x:visible!important}
}
'''
s=s.replace(conflict,'')
if 'mobile-rank-metrics{display:grid' not in s:
    s=s.replace('</style>"""',css+'\n</style>"""',1)

p.write_text(s,encoding='utf-8')
