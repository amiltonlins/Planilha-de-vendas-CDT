from pathlib import Path
import re

path=Path('app.py')
text=path.read_text(encoding='utf-8')

new_function=r'''def seller_kpis_html(x):
    meta_value=int(x.get("meta_individual",0) or 0)
    vendas=int(x.get("vendas",0) or 0)
    projecao=int(x.get("projecao",0) or 0)
    meta_pct=projecao/meta_value if meta_value else 0
    faltam=max(0,meta_value-vendas)

    result_html=(
        '<div class="seller-result-card">'
        '<div class="seller-result-title">RESULTADO COMERCIAL</div>'
        '<div class="seller-result-main">'
        f'<div class="seller-result-kpi hero"><small>VENDAS</small><strong>{vendas}</strong></div>'
        f'<div class="seller-result-kpi"><small>PROJEÇÃO</small><strong>{projecao}</strong></div>'
        f'<div class="seller-result-kpi"><small>% META</small><strong>{pct(meta_pct)}</strong></div>'
        '</div>'
        '<div class="seller-result-secondary">'
        f'<div><small>META</small><strong>{meta_value}</strong></div>'
        f'<div><small>FALTAM</small><strong>{faltam}</strong></div>'
        '</div>'
        '</div>'
    )

    commercial_html=(
        '<div class="seller-commercial-single seller-commercial-refined">'
        '<div class="seller-commercial-title">DESEMPENHO COMERCIAL</div>'
        '<div class="seller-commercial-metrics">'
        f'<div><small>MÉDIA/DIA</small><strong>{x["media"]:.2f}</strong></div>'
        f'<div><small>ZEROS</small><strong>{x["zeros"]}</strong></div>'
        f'<div class="seller-commercial-neo"><small>NEOENERGIA</small><strong>{x["neo"]} vendas <span>• {pct(x["neo_pct"])}</span></strong></div>'
        '</div></div>'
    )

    finance_primary=(
        '<div class="seller-finance-primary">'
        f'{seller_kpi_card("PREMIAÇÃO ATUAL",money(x["base"]),"Já acumulada","primary")}'
        f'{seller_kpi_card("TOTAL VARIÁVEL PROJETADO",money(x["total_variavel_proj"]),"Fechamento estimado","primary total")}'
        '</div>'
    )

    finance_detail=[
        ("PREMIAÇÃO PROJETADA",money(x["comissao_proj"]),"Base projetada","level2"),
        ("SEMANAIS",money(x["premio_total"]),"Acumulado semanal","level3"),
        ("BÔNUS NEO PROJETADO",money(x["bonus_neo_proj"]),"Projeção","level3"),
        ("BÔNUS (SE) 100% ADIM",money(x["bonus_adim_proj"]),"Condicional","level3"),
    ]
    finance_detail_html=''.join(seller_kpi_card(*item) for item in finance_detail)

    return (
        '<div class="seller-executive-popup">'
        f'{result_html}'
        f'{commercial_html}'
        '<div class="seller-group-title award">PREMIAÇÃO</div>'
        f'{finance_primary}'
        '<div class="seller-finance-detail">'
        f'{finance_detail_html}'
        '</div>'
        '</div>'
    )
'''

pattern=r'def seller_kpis_html\(x\):\n.*?\n\ndef ranking_html\(ranking,auth_token=""\):'
replacement=new_function+'\n\ndef ranking_html(ranking,auth_token=""):'
updated,count=re.subn(pattern,replacement,text,flags=re.S)
if count!=1:
    raise SystemExit(f'Esperava substituir 1 seller_kpis_html; encontrado: {count}')
text=updated

marker='/* POPUP EXECUTIVO DO VENDEDOR - 2026-08 */'
css=r'''
/* POPUP EXECUTIVO DO VENDEDOR - 2026-08 */
.seller-executive-popup{display:flex;flex-direction:column;gap:10px;margin-top:2px}
.seller-result-card{background:linear-gradient(120deg,#0F172A,#172554);color:#fff;border-radius:14px;padding:14px 16px;box-shadow:0 4px 16px rgba(15,23,42,.12)}
.seller-result-title,.seller-commercial-title{font-size:.66rem;font-weight:900;letter-spacing:.075em;text-transform:uppercase}
.seller-result-title{color:#E2E8F0;margin-bottom:10px}
.seller-result-main{display:grid;grid-template-columns:1.15fr 1fr 1fr;gap:8px}
.seller-result-kpi{min-width:0;border-left:1px solid rgba(255,255,255,.20);padding:2px 12px}
.seller-result-kpi:first-child{border-left:0;padding-left:0}
.seller-result-kpi small,.seller-result-secondary small{display:block;color:#CBD5E1;font-size:.58rem;font-weight:850;letter-spacing:.045em}
.seller-result-kpi strong{display:block;color:#fff;font-size:1.7rem;line-height:1.05;margin-top:5px;font-weight:950;white-space:nowrap}
.seller-result-kpi.hero strong{font-size:2.05rem}
.seller-result-secondary{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:10px;padding-top:9px;border-top:1px solid rgba(255,255,255,.15)}
.seller-result-secondary>div{display:flex;align-items:baseline;gap:8px}
.seller-result-secondary strong{font-size:1.05rem;color:#fff}
.seller-commercial-refined{margin:0!important}
.seller-commercial-refined .seller-commercial-metrics{grid-template-columns:1fr .8fr 1.55fr!important}
.seller-finance-primary{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.seller-finance-primary .seller-kpi{min-height:112px}
.seller-finance-primary .seller-kpi strong{font-size:1.55rem}
.seller-finance-detail{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:8px}
.seller-finance-detail .seller-kpi{min-height:88px;padding:11px 12px}
.seller-finance-detail .seller-kpi strong{font-size:1.05rem}

@media(max-width:560px){
  [data-testid="stDialog"] .seller-executive-popup{gap:6px!important}
  [data-testid="stDialog"] .seller-result-card{padding:9px 10px!important;border-radius:10px!important}
  [data-testid="stDialog"] .seller-result-title{font-size:.52rem!important;margin-bottom:6px!important}
  [data-testid="stDialog"] .seller-result-main{grid-template-columns:repeat(3,minmax(0,1fr))!important;gap:3px!important}
  [data-testid="stDialog"] .seller-result-kpi{padding:1px 6px!important}
  [data-testid="stDialog"] .seller-result-kpi:first-child{padding-left:0!important}
  [data-testid="stDialog"] .seller-result-kpi small,[data-testid="stDialog"] .seller-result-secondary small{font-size:.43rem!important}
  [data-testid="stDialog"] .seller-result-kpi strong{font-size:1.02rem!important;margin-top:3px!important;white-space:normal!important}
  [data-testid="stDialog"] .seller-result-kpi.hero strong{font-size:1.2rem!important}
  [data-testid="stDialog"] .seller-result-secondary{margin-top:6px!important;padding-top:5px!important;gap:4px!important}
  [data-testid="stDialog"] .seller-result-secondary>div{gap:4px!important}
  [data-testid="stDialog"] .seller-result-secondary strong{font-size:.8rem!important}
  [data-testid="stDialog"] .seller-commercial-refined{padding:8px!important}
  [data-testid="stDialog"] .seller-commercial-refined .seller-commercial-title{font-size:.5rem!important;margin-bottom:5px!important}
  [data-testid="stDialog"] .seller-commercial-refined .seller-commercial-metrics{grid-template-columns:.8fr .65fr 1.55fr!important;gap:0!important}
  [data-testid="stDialog"] .seller-commercial-refined .seller-commercial-metrics>div{padding:2px 6px!important}
  [data-testid="stDialog"] .seller-commercial-refined small{font-size:.42rem!important}
  [data-testid="stDialog"] .seller-commercial-refined strong{font-size:.82rem!important;white-space:normal!important}
  [data-testid="stDialog"] .seller-commercial-refined .seller-commercial-neo strong{font-size:.78rem!important}
  [data-testid="stDialog"] .seller-group-title.award{font-size:.52rem!important;margin:2px 0 3px!important}
  [data-testid="stDialog"] .seller-finance-primary{grid-template-columns:1fr 1fr!important;gap:5px!important}
  [data-testid="stDialog"] .seller-finance-primary .seller-kpi{min-height:66px!important;padding:7px!important}
  [data-testid="stDialog"] .seller-finance-primary .seller-kpi strong{font-size:.98rem!important}
  [data-testid="stDialog"] .seller-finance-detail{grid-template-columns:repeat(2,minmax(0,1fr))!important;gap:4px!important}
  [data-testid="stDialog"] .seller-finance-detail .seller-kpi{min-height:50px!important;padding:6px!important}
  [data-testid="stDialog"] .seller-finance-detail .seller-kpi strong{font-size:.76rem!important}
  [data-testid="stDialog"] .seller-finance-detail .seller-kpi small{font-size:.4rem!important}
  [data-testid="stDialog"] .seller-finance-detail .seller-kpi span{font-size:.4rem!important;margin-top:2px!important}
}
'''
if marker not in text:
    pos=text.rfind('</style>')
    if pos<0:
        raise SystemExit('Não encontrei </style> no CSS principal')
    text=text[:pos]+css+'\n'+text[pos:]

path.write_text(text,encoding='utf-8')
print('Popup executivo do vendedor aplicado com sucesso.')
