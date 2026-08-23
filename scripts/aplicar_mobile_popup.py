from pathlib import Path
import re

path=Path('app.py')
s=path.read_text(encoding='utf-8')
pattern=r'''def seller_kpis_html\(x\):\n.*?\n\ndef ranking_html\(ranking,auth_token=""\):'''
replacement='''def seller_kpis_html(x):
    meta_pct=x["projecao"]/x["meta_individual"] if x["meta_individual"] else 0
    status,_,_=performance(x["media"])
    awards=[
        ("PREMIAÇÃO ATUAL",money(x["base"]),"Já acumulada","primary mobile-duplicate"),
        ("PREMIAÇÃO PROJETADA",money(x["comissao_proj"]),"Base projetada","level2"),
        ("BÔNUS NEO PROJETADO",money(x["bonus_neo_proj"]),"Projeção","level3"),
        ("BÔNUS (SE) 100% ADIM",money(x["bonus_adim_proj"]),"Condicional","level3"),
        ("SEMANAIS",money(x["premio_total"]),"Acumulado semanal","level3"),
        ("TOTAL VARIÁVEL PROJETADO",money(x["total_variavel_proj"]),"Fechamento estimado","primary total mobile-duplicate"),
    ]
    awards_html=''.join(seller_kpi_card(*item) for item in awards)
    mobile_primary=[
        ("VENDAS",x["vendas"],"Produção","primary"),
        ("PREMIAÇÃO ATUAL",money(x["base"]),"Já acumulada","primary"),
        ("PROJEÇÃO",x["projecao"],f'Meta {x["meta_individual"]}',"primary mobile-projection"),
        ("TOTAL VARIÁVEL PROJETADO",money(x["total_variavel_proj"]),"Fechamento estimado","primary total"),
    ]
    mobile_html=''.join(seller_kpi_card(*item) for item in mobile_primary)
    commercial_html=(
        '<div class="seller-commercial-single">'
        '<div class="seller-commercial-title">DESEMPENHO COMERCIAL</div>'
        '<div class="seller-commercial-metrics">'
        f'<div><small>MÉDIA/DIA</small><strong>{x["media"]:.2f}</strong></div>'
        f'<div><small>% META</small><strong>{pct(meta_pct)}</strong></div>'
        f'<div><small>ZEROS</small><strong>{x["zeros"]}</strong></div>'
        f'<div class="seller-commercial-neo"><small>NEOENERGIA</small><strong>{x["neo"]} vendas <span>• {pct(x["neo_pct"])}</span></strong></div>'
        '</div></div>'
    )
    return (
        f'<div class="seller-mobile-primary">{mobile_html}</div>'
        '<div class="seller-groups">'
        f'{commercial_html}'
        '<div class="seller-group-title award">PREMIAÇÃO</div>'
        f'<div class="seller-kpi-grid award-grid">{awards_html}</div>'
        '</div>'
    )


def ranking_html(ranking,auth_token=""):
'''
s2,count=re.subn(pattern,replacement,s,flags=re.S)
if count!=1: raise SystemExit(f'Falha ao localizar seller_kpis_html: {count}')
s=s2
needle='''    st.markdown(CSS,unsafe_allow_html=True)\n'''
override='''    st.markdown(CSS,unsafe_allow_html=True)\n    st.markdown("""<style>\n.exec-performance-values strong,.exec-performance-values .exec-main-value strong{font-size:clamp(2.25rem,3.2vw,3.7rem)!important;font-weight:900!important;line-height:.95!important;letter-spacing:-.035em!important}\n.seller-commercial-single{background:#fff;border:1px solid var(--line);border-radius:12px;padding:12px 14px;margin-top:12px;min-width:0;overflow:hidden}\n.seller-commercial-title{font-size:.72rem;font-weight:900;letter-spacing:.08em;color:#475569;margin:0 0 10px}\n.seller-commercial-metrics{display:grid;grid-template-columns:.9fr .9fr .75fr 1.65fr;align-items:stretch;gap:0;min-width:0}\n.seller-commercial-metrics>div{min-width:0;padding:3px 12px;border-left:1px solid #E2E8F0;display:flex;flex-direction:column;justify-content:center}\n.seller-commercial-metrics>div:first-child{border-left:0;padding-left:0}\n.seller-commercial-metrics small{font-size:.58rem;font-weight:900;letter-spacing:.035em;color:#64748B;white-space:nowrap}\n.seller-commercial-metrics strong{font-size:1.2rem;line-height:1.08;margin-top:6px;color:#0F172A;font-weight:900;white-space:nowrap}\n.seller-commercial-neo strong{font-size:1.32rem;color:#0F172A}\n.seller-commercial-neo strong span{font-size:.92em;font-weight:900}\n@media(max-width:760px){\n.block-container{padding-top:.30rem!important;padding-left:.48rem!important;padding-right:.48rem!important}\n.st-key-cdt_top_header{padding:10px 11px 7px!important;margin-bottom:2px!important}\n.st-key-header_control_strip,.st-key-compact_top_strip{margin-top:1px!important;margin-bottom:3px!important;padding-top:0!important;padding-bottom:1px!important}\n.exec-compact-grid{margin-top:5px!important;margin-bottom:7px!important;gap:6px!important;grid-template-columns:1fr 1fr!important}\n.exec-performance{grid-column:1/-1!important}\n.exec-compact-card{min-height:0!important;height:auto!important;padding:10px 11px!important;border-radius:11px!important}\n.exec-compact-title{margin-bottom:7px!important;font-size:.58rem!important}\n.exec-performance-values{grid-template-columns:repeat(3,minmax(0,1fr))!important;gap:5px!important}\n.exec-performance-values strong,.exec-performance-values .exec-main-value strong{font-size:clamp(1.55rem,7vw,2.1rem)!important;margin-top:5px!important}\n.exec-pair-values{grid-template-columns:repeat(2,minmax(0,1fr))!important;gap:6px!important}\n.exec-pair-values strong{font-size:clamp(1.35rem,6vw,1.9rem)!important;margin-top:4px!important}\n.exec-performance-values small,.exec-pair-values small{font-size:.52rem!important}\n}\n@media(max-width:560px){\n.st-key-cdt_top_header{padding:9px 10px 6px!important;border-radius:16px!important}\n.cdt-brandline{margin-bottom:2px!important}.cdt-title{line-height:1!important}.cdt-unit-emphasis{margin-top:3px!important}\n.exec-compact-grid{gap:5px!important;margin-top:4px!important}.exec-compact-card{padding:9px 9px!important}.exec-compact-title{margin-bottom:6px!important}\n.exec-performance-values strong,.exec-performance-values .exec-main-value strong{font-size:clamp(1.45rem,7.5vw,1.95rem)!important}\n.exec-pair-values strong{font-size:clamp(1.25rem,6.5vw,1.7rem)!important}\ndiv[data-testid="stDialog"] [data-testid="stVerticalBlock"]{gap:.42rem!important}\n.seller-mobile-primary{margin-top:6px!important;gap:6px!important}.seller-mobile-primary .seller-kpi{padding:9px 9px!important}.seller-groups{margin-top:5px!important}\n.seller-commercial-single{padding:10px 9px;margin-top:7px;border-radius:10px}.seller-commercial-title{font-size:.62rem;margin-bottom:7px}\n.seller-commercial-metrics{grid-template-columns:.82fr .82fr .68fr 1.68fr}.seller-commercial-metrics>div{padding:2px 7px}.seller-commercial-metrics>div:first-child{padding-left:0}\n.seller-commercial-metrics small{font-size:.48rem}.seller-commercial-metrics strong{font-size:.92rem;margin-top:4px}.seller-commercial-neo strong{font-size:1rem;white-space:normal;line-height:1.05}\n.seller-group-title.award{margin-top:9px!important;margin-bottom:5px!important}.seller-kpi-grid.award-grid{gap:6px!important}\n}\n@media(max-width:360px){.seller-commercial-metrics{grid-template-columns:.8fr .8fr .65fr 1.75fr}.seller-commercial-metrics>div{padding:2px 5px}.seller-commercial-metrics small{font-size:.43rem}.seller-commercial-metrics strong{font-size:.84rem}.seller-commercial-neo strong{font-size:.91rem}}\n</style>""",unsafe_allow_html=True)\n'''
if needle not in s: raise SystemExit('Ponto CSS não encontrado')
s=s.replace(needle,override,1)
path.write_text(s,encoding='utf-8')
