from pathlib import Path
import re

path=Path('app.py')
text=path.read_text(encoding='utf-8')

new_function=r'''def seller_kpis_html(x):
    meta_value=int(x.get("meta_individual",0) or 0)
    vendas=int(x.get("vendas",0) or 0)
    projecao=int(x.get("projecao",0) or 0)
    meta_pct=projecao/meta_value if meta_value else 0
    classification,color,_=performance(x["media"])
    performance_key=normalize_text(classification)
    status_emoji={"vermelho":"😟","amarelo":"😐","verde":"🙂","azul":"😎"}.get(performance_key,"😟")

    metrics=[
        ("VENDAS",str(vendas),"main"),
        ("PROJEÇÃO",str(projecao),"main"),
        ("MÉDIA/DIA",f'{x["media"]:.2f}',""),
        ("ZEROS",str(x["zeros"]),""),
        ("% META",pct(meta_pct),"main"),
        ("NEO",str(x["neo"]),"neo"),
        ("% NEO",pct(x["neo_pct"]),"neo"),
    ]
    metric_html=''.join(
        f'<div class="seller-rank-metric {tone}"><strong>{value}</strong><small>{label}</small></div>'
        for label,value,tone in metrics
    )
    awards=[
        ("PREMIAÇÃO ATUAL",money(x["base"]),"main"),
        ("PREMIAÇÃO PROJ.",money(x["comissao_proj"]),""),
        ("BÔNUS NEO PROJ.",money(x["bonus_neo_proj"]),""),
        ("BÔNUS (SE) 100% ADIM",money(x["bonus_adim_proj"]),""),
        ("SEMANAIS",money(x["premio_total"]),""),
        ("TOTAL VAR. PROJ.",money(x["total_variavel_proj"]),"total"),
    ]
    award_html=''.join(
        f'<div class="seller-rank-award {tone}"><strong>{value}</strong><small>{label}</small></div>'
        for label,value,tone in awards
    )
    return (
        f'<div class="seller-ranking-popup" style="--seller-performance:{color}">'
        '<div class="seller-ranking-strip">'
        f'<div class="seller-ranking-metrics">{metric_html}</div>'
        f'<div class="seller-ranking-emoji" aria-label="Performance {html.escape(str(classification))}">{status_emoji}</div>'
        '</div>'
        f'<div class="seller-ranking-awards">{award_html}</div>'
        '</div>'
    )
'''

pattern=r'def seller_kpis_html\(x\):\n.*?\n\ndef ranking_html\(ranking,auth_token=""\):'
replacement=new_function+'\n\ndef ranking_html(ranking,auth_token=""):'
updated,count=re.subn(pattern,replacement,text,flags=re.S)
if count!=1:
    raise SystemExit(f'Esperava substituir 1 seller_kpis_html; encontrado: {count}')
text=updated

marker='/* POPUP COMO EXTENSAO DO RANKING - 2026-08 */'
css=r'''
/* POPUP COMO EXTENSAO DO RANKING - 2026-08 */
.seller-ranking-popup{background:var(--seller-performance,#0891B2);border-radius:14px;padding:12px;color:#fff;box-shadow:0 4px 14px rgba(15,23,42,.12);margin:4px 0 8px;overflow:hidden}
.seller-ranking-strip{display:grid;grid-template-columns:minmax(0,1fr) 92px;gap:8px;align-items:stretch}
.seller-ranking-metrics{display:grid;grid-template-columns:repeat(7,minmax(0,1fr));min-width:0}
.seller-rank-metric{min-width:0;text-align:center;padding:8px 7px;border-left:1px solid rgba(255,255,255,.22);display:flex;flex-direction:column;justify-content:center}
.seller-rank-metric:first-child{border-left:0}
.seller-rank-metric strong,.seller-rank-award strong{display:block;color:#fff;font-size:1.18rem;font-weight:950;line-height:1.05;white-space:nowrap}
.seller-rank-metric.main strong{font-size:1.35rem}
.seller-rank-metric small,.seller-rank-award small{display:block;color:rgba(255,255,255,.88);font-size:.48rem;font-weight:900;line-height:1.15;margin-top:5px;letter-spacing:.02em}
.seller-rank-metric.neo{background:rgba(255,255,255,.12);margin:2px;border-radius:8px;border-left:0}
.seller-ranking-emoji{display:flex;align-items:center;justify-content:center;background:rgba(255,255,255,.14);border-radius:9px;font-size:2rem;min-width:0}
.seller-ranking-awards{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));margin-top:7px;background:rgba(3,19,45,.16);border-radius:9px;overflow:hidden}
.seller-rank-award{min-width:0;text-align:center;padding:9px 7px;border-left:1px solid rgba(255,255,255,.18)}
.seller-rank-award:first-child{border-left:0}
.seller-rank-award strong{font-size:1rem}
.seller-rank-award.main,.seller-rank-award.total{background:rgba(3,19,45,.26)}
.seller-rank-award.total strong{font-size:1.12rem}

@media(max-width:700px){
  [data-testid="stDialog"] .seller-ranking-popup{padding:7px;border-radius:10px;margin:2px 0 5px}
  [data-testid="stDialog"] .seller-ranking-strip{grid-template-columns:minmax(0,1fr) 54px;gap:5px}
  [data-testid="stDialog"] .seller-ranking-metrics{grid-template-columns:repeat(4,minmax(0,1fr));gap:0}
  [data-testid="stDialog"] .seller-rank-metric{padding:6px 3px;border-bottom:1px solid rgba(255,255,255,.14)}
  [data-testid="stDialog"] .seller-rank-metric:nth-child(5){border-left:0}
  [data-testid="stDialog"] .seller-rank-metric strong{font-size:.82rem;white-space:normal}
  [data-testid="stDialog"] .seller-rank-metric.main strong{font-size:.94rem}
  [data-testid="stDialog"] .seller-rank-metric small{font-size:.38rem;margin-top:3px}
  [data-testid="stDialog"] .seller-ranking-emoji{font-size:1.45rem}
  [data-testid="stDialog"] .seller-ranking-awards{grid-template-columns:repeat(3,minmax(0,1fr));margin-top:5px}
  [data-testid="stDialog"] .seller-rank-award{padding:6px 4px;border-bottom:1px solid rgba(255,255,255,.14)}
  [data-testid="stDialog"] .seller-rank-award:nth-child(4){border-left:0}
  [data-testid="stDialog"] .seller-rank-award strong{font-size:.72rem;white-space:normal}
  [data-testid="stDialog"] .seller-rank-award.total strong{font-size:.78rem}
  [data-testid="stDialog"] .seller-rank-award small{font-size:.36rem;margin-top:3px}
}
'''
if marker not in text:
    pos=text.rfind('</style>')
    if pos<0:
        raise SystemExit('Não encontrei </style> no CSS principal')
    text=text[:pos]+css+'\n'+text[pos:]

path.write_text(text,encoding='utf-8')
print('Popup alinhado visualmente ao card do ranking, sem alterar calculos.')
