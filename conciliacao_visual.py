"""Shared Conciliação presentation rules for the screen and PNG exports."""
import html
import io
from decimal import Decimal

PALETTE = {
    "red": ("🔴", "#B91C1C", "#FFFFFF"),
    "orange": ("🟠", "#C2410C", "#FFFFFF"),
    "yellow": ("🟡", "#FACC15", "#172033"),
    "green": ("🟢", "#15803D", "#FFFFFF"),
    "blue": ("🔵", "#1D4ED8", "#FFFFFF"),
}


def money(value):
    return "R$ " + f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def integer(value):
    return f"{value:,.0f}".replace(",", ".")


def percentage(value):
    return f"{value:.1f}".rstrip("0").rstrip(".").replace(".", ",") + "%"


def daily_color(qias):
    return "blue" if qias >= 30 else "green" if qias >= 25 else "yellow" if qias >= 20 else "orange" if qias >= 15 else "red"


def projection_color(projected, goal):
    if goal <= 0:
        return "red"
    percent = Decimal(projected) * 100 / Decimal(goal)
    return "blue" if percent >= 101 else "green" if percent >= 100 else "yellow" if percent >= 75 else "orange" if percent >= 50 else "red"


def row_metrics(row, view):
    if view == "VISÃO GERAL":
        return [
            ("QIAs", integer(row["qias"])), ("% META QIAs", percentage(Decimal(row["qias"])*100/row["qias_goal"]) if row.get("qias_goal") else "—"), ("PROJEÇÃO QIAs", integer(row["qias_projection"])),
            ("TROCAS", integer(row["changes"])), ("% META TROCAS", percentage(Decimal(row["changes"])*100/row["changes_goal"]) if row.get("changes_goal") else "—"), ("PROJEÇÃO TROCAS", integer(row["changes_projection"])),
            ("CAIXA", money(row["cash"])), ("CRÉDITO", integer(row["credit"])), ("NEOENERGIA", integer(row["neo"])),
            ("TICKET MÉDIO", money(row["ticket"])), ("% META PROJETADA", percentage(row["goal_percent"])),
            ("MENSAL ATUAL", money(row["monthly_award"])), ("SEMANAIS CONQUISTADAS", money(row["weekly_award"])),
            ("MENSAL PROJETADA", money(row["projected_award"])), ("TOTAL PROJETADO", money(row["commission_projection"])),
        ]
    metrics = [("QIAs", integer(row["qias"])), ("TROCAS", integer(row["changes"])),
               ("CRÉDITO", integer(row["credit"])), ("NEOENERGIA", integer(row["neo"])),
               ("TICKET MÉDIO", money(row["ticket"])), ("CAIXA", money(row["cash"]))]
    if view == "DIÁRIO":
        metrics += [("QIAs NA SEMANA", integer(row.get("week_qias", 0))),
                    ("QIAs NO MÊS", integer(row.get("month_qias", 0)))]
    else:
        metrics += [("PROJEÇÃO QIAs", integer(row["qias_projection"])),
                    ("PROJEÇÃO TROCAS", integer(row["changes_projection"])),
                    ("PRÊMIO CONQUISTADO", money(row.get("closed_award", 0))),
                    ("PRÊMIO PROJETADO", money(row["award"])),
                    ("FAIXA ATUAL", str(row["tier"]) + "ª" if row["tier"] else "—"),
                    ("FAIXA PROJETADA", str(row["projected_tier"]) + "ª" if row["projected_tier"] else "—")]
    return metrics


def ranking_html(rows, view):
    result = []
    priority = ("QIAs", "% META QIAs", "PROJEÇÃO QIAs", "TROCAS", "% META TROCAS", "PROJEÇÃO TROCAS")
    for index, row in enumerate(rows, 1):
        emoji, color, ink = PALETTE[row["color"]]
        metrics = row_metrics(row, view)
        def fields(items):
            return ''.join(f'<span><strong>{html.escape(value)}</strong><small>{label}</small></span>' for label, value in items)
        primary = [(label, dict(metrics)[label]) for label in priority if label in dict(metrics)]
        secondary = [(label, value) for label, value in metrics if label not in priority]
        regime = ''.join(f'<span><small>{label}</small><b>{integer(row[label])}</b><em>Ticket Médio {money(row.get("regime_tickets", {}).get(label, 0))}</em></span>' for label in ("NR", "1 A 3", "4 A 6"))
        goal = f'Meta individual: {integer(row["qias_goal"])} QIAs' if "qias_goal" in row else ""
        warning = ' · Caixa e ticket parciais' if row.get("cash_invalid") else ''
        result.append(f'<article class="conc-rank-row" style="--tone:{color};--ink:{ink}">'
                      f'<div class="conc-person"><b>{index}º · {html.escape(row["name"])}</b><span>{emoji}</span></div>'
                      f'<div class="conc-indicators conc-primary">{fields(primary)}</div>'
                      f'<div class="conc-breakdown">{regime}</div>'
                      f'<div class="conc-indicators conc-secondary">{fields(secondary)}</div>'
                      f'<div class="conc-regime">{goal}{warning}</div></article>')
    return '<div class="conc-ranking" translate="no">' + ''.join(result) + '</div>'


def summary_html(totals, summary, goals, monthly=True):
    def fields(values):
        return ''.join(f'<div><small>{label}</small><strong>{html.escape(value)}</strong></div>' for label, value in values)
    results = [("QIAs REALIZADOS", integer(totals["qias"])), ("TROCAS REALIZADAS", integer(totals["changes"]))]
    if monthly:
        results += [("PROJEÇÃO QIAs", integer(sum(r["qias_projection"] for r in summary))),
                    ("PROJEÇÃO TROCAS", integer(sum(r["changes_projection"] for r in summary)))]
    goals_values = []
    for key, label in (("qias", "QIAs"), ("changes", "TROCAS")):
        goal = goals.get(key, 0)
        goals_values.append((f"META {label}", integer(goal) if goal else "Não definida"))
        results.append((f"% META {label}", percentage(Decimal(totals[key])*100/goal) if goal else "—"))
    values = dict(results)
    order = ["QIAs REALIZADOS", "% META QIAs"]
    if monthly:
        order += ["PROJEÇÃO QIAs"]
    order += ["TROCAS REALIZADAS", "% META TROCAS"]
    if monthly:
        order += ["PROJEÇÃO TROCAS"]
    results = [(label, values[label]) for label in order] + [("TICKET MÉDIO GERAL", money(totals["ticket"]))]
    return ('<div class="exec-compact-grid conc-summary" translate="no">'
            '<div class="exec-compact-card exec-performance"><div class="exec-compact-title">DESEMPENHO GERAL</div>'
            f'<div class="exec-performance-values conc-performance-values">{fields(results)}</div></div>'
            '<div class="exec-compact-card"><div class="exec-compact-title">METAS MENSAIS GERAIS</div>'
            f'<div class="conc-summary-values">{fields(goals_values)}</div></div></div>')


def regimes_html(totals):
    return '<div class="conc-regimes">' + ''.join(
        f'<div><small>{label}</small><b>{integer(totals[label])} QIAs</b><span>'
        f'{percentage(Decimal(totals[label])*100/totals["qias"]) if totals["qias"] else "0%"}</span><em>Ticket Médio <b>{money(totals.get("regime_tickets", {}).get(label, 0))}</b></em></div>'
        for label in ("NR", "1 A 3", "4 A 6")) + '</div>'


STYLE = """<style>
.conc-summary.exec-compact-grid{display:grid;grid-template-columns:2.4fr 1fr!important;gap:9px!important;margin:6px 0 10px!important;align-items:start!important}
.conc-summary .exec-compact-card{min-height:0!important;padding:10px 12px!important;border-radius:12px!important}
.conc-summary .exec-compact-title{font-size:.58rem!important;line-height:1.1!important;margin-bottom:8px!important}
.conc-summary .conc-performance-values{display:grid!important;grid-template-columns:repeat(4,minmax(0,1fr))!important;gap:9px 12px!important}
.conc-summary .conc-performance-values small{display:block;font-size:.52rem!important;line-height:1.15!important;color:#E2E8F0!important;white-space:normal!important}
.conc-summary .conc-performance-values strong{display:block;font-size:1.25rem!important;line-height:1.1!important;margin-top:4px!important;color:#fff!important}
.conc-summary .conc-performance-values>div:nth-child(1) strong,.conc-summary .conc-performance-values>div:nth-child(3) strong{font-size:1.55rem!important}
.conc-summary-values{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}
.conc-summary-values small{display:block;font-size:.52rem!important;color:#64748b}
.conc-summary-values strong{display:block;font-size:1.22rem!important;line-height:1.1!important;margin-top:4px;white-space:nowrap}
.conc-regimes{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:6px;margin:6px 0 10px}
.conc-regimes>div{background:#fff;border:1px solid #e2e8f0;border-radius:9px;padding:6px 9px;display:flex;flex-wrap:wrap;align-items:center;gap:4px 8px}
.conc-regimes small{color:#64748b;font-weight:800;font-size:.62rem!important}.conc-regimes b{font-size:.78rem!important}.conc-regimes span{margin-left:auto;color:#64748b;font-size:.65rem!important}
.conc-rank-row{border-radius:14px;background:var(--tone);color:var(--ink);padding:9px 12px;margin:8px 0;box-shadow:0 2px 7px #0f172a18}
.conc-person{display:flex;justify-content:space-between;align-items:center;gap:8px;margin-bottom:5px;font-size:.84rem!important}
.conc-person b{font-size:inherit!important}
.conc-indicators{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:5px}
.conc-indicators span{border-left:1px solid currentColor;text-align:center;padding:3px;min-width:0;display:flex;flex-direction:column;justify-content:center}
.conc-indicators strong{font-size:.85rem!important;font-weight:800;line-height:1.15!important;white-space:nowrap}
.conc-indicators small{font-size:.52rem!important;line-height:1.15!important;margin-top:3px;color:inherit!important}
.conc-primary{grid-template-columns:repeat(4,minmax(0,1fr));margin:5px 0}
.conc-primary span:nth-child(1) strong{font-size:1.65rem!important}
.conc-primary span:nth-child(2) strong{font-size:1.4rem!important}
.conc-primary span:nth-child(3) strong{font-size:1.2rem!important}
.conc-primary span:nth-child(4) strong{font-size:1.05rem!important}
.conc-breakdown{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:6px;margin:6px 0}
.conc-breakdown span{background:#ffffff20;border:1px solid #ffffff50;border-radius:7px;padding:5px 8px;display:flex;flex-wrap:wrap;justify-content:space-between;align-items:center;gap:3px}
.conc-breakdown small{font-size:.62rem!important;font-weight:700}.conc-breakdown b{font-size:.9rem!important}
.conc-breakdown em,.conc-regimes em{font-style:normal;flex-basis:100%;font-size:.62rem!important;line-height:1.25!important}.conc-regimes em{color:#475569}
.conc-regime{font-size:.58rem;padding-top:5px;margin-top:5px;border-top:1px solid currentColor}
.st-key-conc_refresh button{background:transparent!important;color:#64748b!important;border:0!important;min-height:26px!important;padding:0 5px!important}.st-key-conc_refresh button p{font-size:.68rem!important}
@media(max-width:700px){
.conc-summary.exec-compact-grid{grid-template-columns:1fr!important;gap:6px!important}
.conc-summary .exec-performance{grid-column:auto!important}
.conc-summary .exec-compact-card{padding:8px 9px!important}
.conc-summary .conc-performance-values{grid-template-columns:repeat(2,minmax(0,1fr))!important;gap:7px 12px!important}
.conc-summary .conc-performance-values strong{font-size:1.1rem!important}
.conc-summary .conc-performance-values>div:nth-child(1) strong,.conc-summary .conc-performance-values>div:nth-child(3) strong{font-size:1.3rem!important}
.conc-rank-row{padding:8px;margin:6px 0}.conc-person{font-size:.76rem!important}
.conc-indicators{grid-template-columns:repeat(3,minmax(0,1fr))}.conc-primary{grid-template-columns:repeat(4,minmax(0,1fr))}
.conc-primary span:nth-child(1) strong{font-size:1.35rem!important}.conc-primary span:nth-child(2) strong{font-size:1.2rem!important}.conc-primary span:nth-child(3) strong{font-size:1.05rem!important}.conc-primary span:nth-child(4) strong{font-size:.95rem!important}
.conc-indicators strong{font-size:.76rem!important}.conc-indicators small{font-size:.48rem!important}
.conc-breakdown span{padding:5px}.conc-breakdown em{font-size:.56rem!important}
.conc-regimes>div{padding:6px;gap:4px}.conc-regimes span{margin:0}.conc-regimes b{font-size:.72rem!important}
}

.conc-summary .conc-performance-values{grid-template-columns:repeat(3,minmax(0,1fr))!important;gap:8px 12px!important}
.conc-summary .conc-performance-values>div:last-child{grid-column:1/-1}
.conc-summary .conc-performance-values strong{font-size:1.42rem!important;line-height:1.02!important}
.conc-summary .conc-performance-values>div:nth-child(1) strong,.conc-summary .conc-performance-values>div:nth-child(3) strong{font-size:1.42rem!important}
.conc-summary .conc-performance-values small{font-size:.52rem!important}
.conc-rank-row{padding:7px 10px;margin:6px 0}
.conc-primary{grid-template-columns:repeat(6,minmax(0,1fr));margin:3px 0;gap:4px}
.conc-primary span:nth-child(n) strong{font-size:1rem!important}
.conc-primary small{font-size:.49rem!important}
.conc-secondary{grid-template-columns:repeat(9,minmax(0,1fr));gap:4px}
.conc-secondary strong{font-size:.75rem!important}.conc-secondary small{font-size:.46rem!important}
.conc-breakdown{margin:4px 0;gap:4px}.conc-breakdown span{padding:4px 7px;justify-content:flex-start;gap:6px}
.conc-breakdown em{flex-basis:auto;margin-left:auto;font-size:.6rem!important}.conc-breakdown b{font-size:.8rem!important}
@media(max-width:700px){
.conc-summary .conc-performance-values{grid-template-columns:repeat(3,minmax(0,1fr))!important;gap:7px!important}
.conc-summary .conc-performance-values strong,.conc-summary .conc-performance-values>div:nth-child(1) strong,.conc-summary .conc-performance-values>div:nth-child(3) strong{font-size:1.14rem!important}
.conc-summary .conc-performance-values small{font-size:.45rem!important}
.conc-primary{grid-template-columns:repeat(3,minmax(0,1fr))}.conc-primary span:nth-child(n) strong{font-size:1.02rem!important}
.conc-secondary{grid-template-columns:repeat(3,minmax(0,1fr))}.conc-secondary strong{font-size:.72rem!important}
.conc-breakdown em{flex-basis:100%;margin:0;font-size:.56rem!important}
}
</style>"""


def ranking_png(rows, title, period, synced_at, view="DIÁRIO", totals=None, goals=None):
    """The daily screen displays these exact bytes, so exporting cannot change its layout."""
    from PIL import Image, ImageDraw
    from app_core import _draw_daily_brand, _fit_image_text, _draw_daily_status_icon, _draw_daily_ordinal
    from PIL import ImageFont
    from pathlib import Path
    def _daily_font(size, bold=False):
        path = Path(__file__).resolve().parent / "assets" / "fonts" / ("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf")
        return ImageFont.truetype(str(path), size)
    count = len(row_metrics(rows[0], view)) if rows else 8
    grid_rows = (count + 3) // 4
    row_height = 138 + grid_rows * 82
    team_height = 208 if totals is not None else 0
    image = Image.new("RGB", (1080, 220 + team_height + max(1, len(rows)) * (row_height + 14)), "#F1F5F9")
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((16, 10, 1064, 151), radius=24, fill="#064E3B")
    _draw_daily_brand(draw, 38, 23)
    draw.text((38, 73), title, font=_daily_font(30, True), fill="white")
    draw.text((38, 117), period, font=_daily_font(23), fill="white")
    if totals is not None:
        draw.rounded_rectangle((16,167,1064,359),radius=20,fill="#172554")
        draw.text((38,181),"RESULTADO DA EQUIPE NO DIA" if view=="DIÁRIO" else "RESULTADO GERAL DA EQUIPE",font=_daily_font(22,True),fill="white")
        team = [("QIAs",integer(totals["qias"])),("TROCAS",integer(totals["changes"])),
                ("CAIXA",money(totals["cash"])),("TICKET MÉDIO",money(totals["ticket"]))]
        if view == "VISÃO GERAL":
            team += [("PROJEÇÃO QIAs",integer(sum(r["qias_projection"] for r in rows))),
                     ("PROJEÇÃO TROCAS",integer(sum(r["changes_projection"] for r in rows)))]
            for key,label in (("qias","QIAs"),("changes","TROCAS")):
                goal=(goals or {}).get(key,0)
                team.append((f"% META {label}",percentage(Decimal(totals[key])*100/goal) if goal else "—"))
        else:
            team += [("CRÉDITO",integer(totals["credit"])),("NEOENERGIA",integer(totals["neo"])),
                     ("NR",integer(totals["NR"])),("1 A 3 / 4 A 6",f'{integer(totals["1 A 3"])} / {integer(totals["4 A 6"])}')]
        for j,(label,value) in enumerate(team):
            x,y=38+(j%4)*254,220+(j//4)*65
            draw.text((x,y),_fit_image_text(draw,value,_daily_font(27,True),240),font=_daily_font(27,True),fill="white")
            draw.text((x,y+33),label,font=_daily_font(16),fill="#CBD5E1")
    for i, row in enumerate(rows):
        y = 167 + team_height + i * (row_height + 14)
        _, color, ink = PALETTE[row.get("color", daily_color(row["qias"]))]
        draw.rounded_rectangle((16,y,1064,y+row_height),radius=24,fill=color)
        name = _fit_image_text(draw, row["name"], _daily_font(31,True), 875)
        _draw_daily_ordinal(draw, 48, y+34, i+1, ink)
        draw.text((82,y+15),name,font=_daily_font(31,True),fill=ink)
        _draw_daily_status_icon(draw, 1020, y+36, {"blue":"Azul","green":"Verde","yellow":"Amarelo","orange":"Laranja","red":"Vermelho"}[row.get("color",daily_color(row["qias"]))])
        for j,(label,value) in enumerate(row_metrics(row,view)):
            x, top = 38+(j%4)*254, y+64+(j//4)*82
            if j%4:
                draw.line((x-12,top+2,x-12,top+59),fill=ink,width=1)
            font = _daily_font(42 if j == 0 else 36 if j == 1 else 27,True)
            fitted = _fit_image_text(draw,value,font,232)
            draw.text((x,top),fitted,font=font,fill=ink)
            label_font = _daily_font(18)
            if draw.textlength(label,font=label_font)>238:
                label_font = _daily_font(15)
            draw.text((x,top+40),label,font=label_font,fill=ink)
        for k, label in enumerate(("NR", "1 A 3", "4 A 6")):
            x = 38 + k * 338
            draw.rounded_rectangle((x,y+row_height-70,x+324,y+row_height-10),radius=8,outline=ink,width=1)
            draw.text((x+12,y+row_height-66),label,font=_daily_font(19),fill=ink)
            draw.text((x+306,y+row_height-66),integer(row[label]),font=_daily_font(23,True),fill=ink,anchor="ra")
            draw.text((x+12,y+row_height-35),"Ticket Médio " + money(row.get("regime_tickets", {}).get(label,0)),font=_daily_font(17),fill=ink)
    if not rows:
        draw.text((40,205+team_height),"Nenhum conciliador habilitado.",font=_daily_font(28),fill="#475569")
    footer = f"Atualizado em {synced_at:%d/%m/%Y %H:%M}"
    if any(r.get("cash_invalid") for r in rows):
        footer += " · Caixa e Ticket Médio parciais"
    draw.text((26,image.height-34),footer,font=_daily_font(20),fill="#475569")
    output=io.BytesIO();image.save(output,"PNG")
    return output.getvalue()
