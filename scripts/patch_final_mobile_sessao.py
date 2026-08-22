from pathlib import Path

p=Path('app.py')
s=p.read_text(encoding='utf-8')

# Texto administrativo coerente com a classificação por equipes.
s=s.replace('Eles ficam em CANAL NACIONAL até você ativá-los como franquia.','Eles ficam em OUTROS CANAIS até você classificá-los/ativá-los corretamente.')

# Logout também carrega o token assinado apenas para restaurar a sessão e encerrá-la corretamente.
old='''    management_href=f'?auth={html.escape(str(auth_token),quote=True)}&action=management' if auth_token else '?action=management'
    st.markdown(
        '<div class="bi-topbar bi-topbar-nav integrated-header">'
        '<div class="bi-brand"><h1>PAINEL COMERCIAL — AFOGADOS</h1><p>Visão executiva de produção, performance, histórico e remuneração variável</p></div>'
        f'<div class="header-account"><span class="header-user">{user_name}</span><div class="header-actions"><a href="{management_href}" target="_self">GESTÃO</a><a href="?action=logout" target="_self">SAIR</a></div></div>'
        '</div>',unsafe_allow_html=True
    )
'''
new='''    management_href=f'?auth={html.escape(str(auth_token),quote=True)}&action=management' if auth_token else '?action=management'
    logout_href=f'?auth={html.escape(str(auth_token),quote=True)}&action=logout' if auth_token else '?action=logout'
    st.markdown(
        '<div class="bi-topbar bi-topbar-nav integrated-header">'
        '<div class="bi-brand"><h1>PAINEL COMERCIAL — AFOGADOS</h1><p>Visão executiva de produção, performance, histórico e remuneração variável</p></div>'
        f'<div class="header-account"><span class="header-user">{user_name}</span><div class="header-actions"><a href="{management_href}" target="_self">GESTÃO</a><a href="{logout_href}" target="_self">SAIR</a></div></div>'
        '</div>',unsafe_allow_html=True
    )
'''
if old not in s:raise SystemExit('cabeçalho autenticado atual não encontrado')
s=s.replace(old,new,1)

# Remove a regra conflitante que voltava a permitir overflow lateral no dialog mobile.
conflict='''@media(max-width:560px){
[data-testid="stDialog"] [role="dialog"]{overflow-x:visible!important}
[data-testid="stDialog"] [role="dialog"]>div{overflow-x:visible!important}
}
'''
s=s.replace(conflict,'')

# Overrides somente mobile. O HTML/CSS desktop do ranking não é alterado.
css='''
/* Ajustes finais exclusivamente mobile: ordem lógica do ranking e dialog sem overflow. */
@media(max-width:560px){
/* Ranking: 6 colunas virtuais para preservar a sequência Vendas/Projeção -> Ritmo -> Neo -> Premiação -> Total. */
.rank-inside{grid-template-columns:repeat(6,minmax(0,1fr))!important;gap:4px!important}
.rank-inside>span:nth-child(1),.rank-inside>span:nth-child(2){grid-column:span 3!important;min-height:51px!important;background:rgba(15,23,42,.18)!important}
.rank-inside>span:nth-child(1) strong,.rank-inside>span:nth-child(2) strong{font-size:1.16rem!important}
.rank-inside>span:nth-child(3),.rank-inside>span:nth-child(4),.rank-inside>span:nth-child(5){grid-column:span 2!important}
.rank-inside>span:nth-child(6),.rank-inside>span:nth-child(7){grid-column:span 3!important;background:rgba(255,255,255,.13)!important}
.rank-inside>span:nth-child(8),.rank-inside>span:nth-child(9),.rank-inside>span:nth-child(10),.rank-inside>span:nth-child(11){grid-column:span 3!important}
.rank-inside>span:nth-child(12){grid-column:span 6!important}
.rank-inside>span:nth-child(13){grid-column:span 6!important;min-height:48px!important;background:rgba(15,23,42,.24)!important}
.rank-inside>span:nth-child(14){display:none!important}
.rank-inside>span{box-sizing:border-box!important;min-width:0!important;max-width:100%!important}
.rank-inside strong{max-width:100%!important;overflow-wrap:anywhere!important}

/* Dialog do vendedor: o conteúdo é dimensionado para caber de verdade na viewport. */
[data-testid="stDialog"] [role="dialog"]{box-sizing:border-box!important;width:calc(100vw - 16px)!important;max-width:calc(100vw - 16px)!important;min-width:0!important;max-height:94dvh!important;margin:3dvh auto!important}
[data-testid="stDialog"] [role="dialog"]>div{box-sizing:border-box!important;width:100%!important;max-width:100%!important;min-width:0!important;max-height:94dvh!important;overflow-y:auto!important;padding:.58rem!important}
[data-testid="stDialog"] [role="dialog"] *,[data-testid="stDialog"] .seller-mobile-primary,[data-testid="stDialog"] .seller-kpi-grid,[data-testid="stDialog"] .seller-kpi,[data-testid="stDialog"] .seller-dialog-meta{box-sizing:border-box!important;min-width:0!important;max-width:100%!important}
[data-testid="stDialog"] .seller-mobile-primary,[data-testid="stDialog"] .seller-kpi-grid{width:100%!important;grid-template-columns:repeat(2,minmax(0,1fr))!important;gap:5px!important}
[data-testid="stDialog"] .seller-mobile-primary{margin:0 0 6px!important}
[data-testid="stDialog"] .seller-kpi{width:100%!important;padding:7px 6px!important;border-radius:9px!important}
[data-testid="stDialog"] .seller-kpi strong{font-size:clamp(.76rem,3.25vw,.91rem)!important;line-height:1.06!important;white-space:normal!important;overflow-wrap:anywhere!important;word-break:normal!important}
[data-testid="stDialog"] .seller-mobile-primary .seller-kpi strong{font-size:clamp(.98rem,4.4vw,1.18rem)!important}
[data-testid="stDialog"] .seller-kpi small{font-size:.46rem!important;line-height:1.05!important}
[data-testid="stDialog"] .seller-dialog-meta{width:100%!important;margin:-2px 0 5px!important;padding:5px 7px!important}
[data-testid="stDialog"] .seller-group-title{margin:6px 0 4px!important}
}
@media(max-width:340px){
[data-testid="stDialog"] [role="dialog"]{width:calc(100vw - 12px)!important;max-width:calc(100vw - 12px)!important}
[data-testid="stDialog"] .seller-kpi-grid,[data-testid="stDialog"] .seller-mobile-primary{gap:4px!important}
[data-testid="stDialog"] .seller-kpi{padding:6px 5px!important}
.rank-inside strong{font-size:.68rem!important}.rank-inside small{font-size:.38rem!important}
}
'''
if 'Ajustes finais exclusivamente mobile' not in s:
    s=s.replace('</style>"""',css+'\n</style>"""',1)

p.write_text(s,encoding='utf-8')
