from pathlib import Path

p=Path('app.py')
s=p.read_text(encoding='utf-8')

# Insere helper visual usando apenas Meta e Projeção já existentes no sistema.
marker='def seller_kpi_card(label,value,sub,cls):\n'
helper='''def projection_status_visual(projected_ratio, meta_value=None, projection_value=None):
    try:
        if meta_value in (None, 0, "") or projection_value in (None, ""):
            return "🙂", "AGUARDANDO DADOS"
        ratio=float(projected_ratio)
        if ratio != ratio or ratio < 0:  # NaN ou inválido
            return "🙂", "AGUARDANDO DADOS"
    except (TypeError, ValueError, ZeroDivisionError):
        return "🙂", "AGUARDANDO DADOS"

    if ratio < 0.40:return "😭", "MUITO ABAIXO"
    if ratio < 0.60:return "😟", "ATENÇÃO"
    if ratio < 0.80:return "😐", "PRECISA ACELERAR"
    if ratio < 0.90:return "🙂", "BOM RITMO"
    if ratio < 1.00:return "😄", "QUASE LÁ!"
    if ratio < 1.20:return "😎", "META NO CAMINHO!"
    return "🤩", "VOANDO!"


def projection_status_card(emoji,message):
    return (
        '<div class="seller-kpi projection-status">'
        f'<div class="projection-status-emoji">{emoji}</div>'
        f'<div class="projection-status-message">{html.escape(str(message))}</div>'
        '</div>'
    )

'''
if 'def projection_status_visual(' not in s:
    if marker not in s: raise SystemExit('marker seller_kpi_card não encontrado')
    s=s.replace(marker,helper+marker,1)

# Usa o percentual projetado já existente na função, sem exibir nenhum número adicional.
old='''    commercial_html=''.join(seller_kpi_card(*item) for item in commercial)
    awards_html=''.join(seller_kpi_card(*item) for item in awards)
'''
new='''    status_emoji,status_message=projection_status_visual(meta_pct,x.get("meta_individual"),x.get("projecao"))
    commercial_html=''.join(seller_kpi_card(*item) for item in commercial)+projection_status_card(status_emoji,status_message)
    awards_html=''.join(seller_kpi_card(*item) for item in awards)
'''
if old not in s: raise SystemExit('bloco commercial_html não encontrado')
s=s.replace(old,new,1)

# CSS mínimo, reaproveitando o mesmo card/base visual já existente.
css='''
.projection-status{display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;background:white;border:1px solid var(--line);box-shadow:none;min-height:100%}.projection-status-emoji{font-size:2.25rem;line-height:1;margin:1px 0 8px}.projection-status-message{font-size:.70rem;line-height:1.15;font-weight:900;letter-spacing:.035em;color:#475569;text-align:center;word-break:normal;overflow-wrap:break-word}
@media(max-width:560px){.projection-status{padding:9px 7px!important;min-height:82px}.projection-status-emoji{font-size:1.8rem;margin-bottom:6px}.projection-status-message{font-size:.58rem;line-height:1.12}}
'''
if '.projection-status{' not in s:
    s=s.replace('</style>',css+'\n</style>',1)

p.write_text(s,encoding='utf-8')
