from pathlib import Path

p=Path('app.py')
s=p.read_text(encoding='utf-8')

# Remove a sugestão de nome da tela de autenticação, preservando toda a lógica de login.
s=s.replace('placeholder="Ex.: Magda Alexandra"','placeholder=""')

mobile_css=r'''
/* AJUSTE FINAL — EXCLUSIVAMENTE RANKING MOBILE. Desktop permanece intocado. */
@media(max-width:560px){
  /* reduz altura pelo layout, não pela perda de legibilidade */
  .rank-card{border-radius:11px!important}
  .rank-row{grid-template-columns:25px minmax(0,1fr)!important;gap:3px!important;padding:3px 1px!important}
  .rank-pos{font-size:.76rem!important;line-height:1!important}
  .rank-name{display:block!important;width:100%!important;min-width:0!important;box-sizing:border-box!important;padding:6px 7px!important;border-radius:9px!important;gap:0!important}
  .rank-seller{padding:0!important}
  .rank-mobile-head{display:flex!important;align-items:center!important;justify-content:space-between!important;gap:5px!important;margin:0 0 4px!important;min-height:24px!important}
  .rank-mobile-head>div:first-child{min-width:0!important;flex:1!important}
  .rank-seller b{font-size:.82rem!important;line-height:1.02!important;font-weight:900!important;white-space:nowrap!important;overflow:hidden!important;text-overflow:ellipsis!important}
  .rank-seller small{font-size:.52rem!important;line-height:1!important;margin-top:2px!important}
  .rank-mobile-status{display:flex!important;flex-direction:row!important;align-items:center!important;justify-content:flex-end!important;gap:3px!important;min-width:0!important;max-width:34%!important;text-align:right!important}
  .rank-mobile-status strong{font-size:1.02rem!important;line-height:1!important}
  .rank-mobile-status small{font-size:.42rem!important;line-height:1!important;margin:0!important;font-weight:850!important;white-space:nowrap!important;overflow:hidden!important;text-overflow:ellipsis!important;color:rgba(255,255,255,.94)!important}

  /* 12 colunas permitem concentrar todas as informações em 3 linhas compactas. */
  .rank-inside{display:grid!important;grid-template-columns:repeat(12,minmax(0,1fr))!important;gap:2px!important;align-items:stretch!important}
  .rank-inside span{min-width:0!important;min-height:25px!important;padding:2px 2px!important;border-left:0!important;border-radius:5px!important;background:rgba(255,255,255,.065)!important;box-sizing:border-box!important;text-align:center!important}
  .rank-inside strong{font-size:.66rem!important;line-height:1!important;font-weight:850!important;white-space:nowrap!important;overflow:hidden!important;text-overflow:ellipsis!important;max-width:100%!important}
  .rank-inside small{font-size:.34rem!important;line-height:1!important;margin-top:2px!important;letter-spacing:0!important;white-space:nowrap!important;overflow:hidden!important;text-overflow:ellipsis!important}

  /* LINHA 1 — prioridade máxima: Vendas, Projeção, Premiação atual e projetada. */
  .rank-inside span:nth-child(1),
  .rank-inside span:nth-child(2),
  .rank-inside span:nth-child(8),
  .rank-inside span:nth-child(9){grid-column:span 3!important;grid-row:1!important;min-height:34px!important;background:rgba(15,23,42,.20)!important}
  .rank-inside span:nth-child(1) strong,
  .rank-inside span:nth-child(2) strong{font-size:1.04rem!important;font-weight:950!important}
  .rank-inside span:nth-child(8) strong,
  .rank-inside span:nth-child(9) strong{font-size:.78rem!important;font-weight:950!important}
  .rank-inside span:nth-child(1) small,
  .rank-inside span:nth-child(2) small,
  .rank-inside span:nth-child(8) small,
  .rank-inside span:nth-child(9) small{font-size:.36rem!important;font-weight:850!important}

  /* LINHA 2 — ritmo, meta, Neo e total variável. */
  .rank-inside span:nth-child(13){grid-column:span 4!important;grid-row:2!important;min-height:29px!important;background:rgba(15,23,42,.25)!important}
  .rank-inside span:nth-child(13) strong{font-size:.78rem!important;font-weight:950!important}
  .rank-inside span:nth-child(3),
  .rank-inside span:nth-child(5),
  .rank-inside span:nth-child(6),
  .rank-inside span:nth-child(7){grid-column:span 2!important;grid-row:2!important;min-height:29px!important}
  .rank-inside span:nth-child(6),.rank-inside span:nth-child(7){background:rgba(255,255,255,.13)!important}
  .rank-inside span:nth-child(6) strong,.rank-inside span:nth-child(7) strong{font-size:.72rem!important}

  /* LINHA 3 — complementares financeiros e zeros, sem esconder nenhum dado. */
  .rank-inside span:nth-child(4){grid-column:span 2!important;grid-row:3!important;min-height:26px!important}
  .rank-inside span:nth-child(10){grid-column:span 3!important;grid-row:3!important;min-height:26px!important}
  .rank-inside span:nth-child(11){grid-column:span 4!important;grid-row:3!important;min-height:26px!important}
  .rank-inside span:nth-child(12){grid-column:span 3!important;grid-row:3!important;min-height:26px!important}

  /* Status separado do desktop não ocupa espaço no mobile; emoji/status já estão no cabeçalho. */
  .rank-inside .desktop-status{display:none!important}
}

@media(max-width:350px){
  .rank-row{grid-template-columns:23px minmax(0,1fr)!important}
  .rank-name{padding:5px 6px!important}
  .rank-seller b{font-size:.76rem!important}
  .rank-inside strong{font-size:.61rem!important}
  .rank-inside span:nth-child(1) strong,.rank-inside span:nth-child(2) strong{font-size:.96rem!important}
  .rank-inside span:nth-child(8) strong,.rank-inside span:nth-child(9) strong,.rank-inside span:nth-child(13) strong{font-size:.70rem!important}
}
'''

if 'AJUSTE FINAL — EXCLUSIVAMENTE RANKING MOBILE' not in s:
    marker='</style>"""'
    if marker not in s:
        raise SystemExit('Fechamento do CSS não encontrado')
    s=s.replace(marker,mobile_css+'\n'+marker,1)

p.write_text(s,encoding='utf-8')
