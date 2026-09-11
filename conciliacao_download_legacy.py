"""Renderer legado do PNG da Conciliação, preservando a visualização atual do painel."""
import io
from decimal import Decimal


def ranking_png(rows, view, period, totals, goals, synced_at):
    from pathlib import Path
    from PIL import Image, ImageDraw, ImageFont
    from app_core import _draw_daily_brand, _fit_image_text, _draw_daily_status_icon, _draw_daily_ordinal
    from conciliacao_visual_screen import PALETTE, daily_color, integer, money, percentage, row_metrics

    title = {
        "VISÃO GERAL": "RANKING GERAL · CONCILIAÇÃO",
        "DIÁRIO": "RANKING DIÁRIO · CONCILIAÇÃO",
        "SEMANAL": "RANKING SEMANAL · CONCILIAÇÃO",
    }.get(view, "RANKING · CONCILIAÇÃO")

    def font(size, bold=False):
        path = Path(__file__).resolve().parent / "assets" / "fonts" / ("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf")
        return ImageFont.truetype(str(path), size)

    count = len(row_metrics(rows[0], view)) if rows else 8
    grid_rows = (count + 3) // 4
    row_height = 138 + grid_rows * 82
    team_height = 208
    image = Image.new("RGB", (1080, 220 + team_height + max(1, len(rows)) * (row_height + 14)), "#F1F5F9")
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((16, 10, 1064, 151), radius=24, fill="#064E3B")
    _draw_daily_brand(draw, 38, 23)
    draw.text((38, 73), title, font=font(30, True), fill="white")
    draw.text((38, 117), period, font=font(23), fill="white")

    draw.rounded_rectangle((16, 167, 1064, 359), radius=20, fill="#172554")
    draw.text((38, 181), "RESULTADO DA EQUIPE NO DIA" if view == "DIÁRIO" else "RESULTADO GERAL DA EQUIPE", font=font(22, True), fill="white")
    team = [("QIAs", integer(totals["qias"])), ("TROCAS", integer(totals["changes"])),
            ("CAIXA", money(totals["cash"])), ("TICKET MÉDIO", money(totals["ticket"]))]
    if view == "VISÃO GERAL":
        team += [("PROJEÇÃO QIAs", integer(sum(r["qias_projection"] for r in rows))),
                 ("PROJEÇÃO TROCAS", integer(sum(r["changes_projection"] for r in rows)))]
        for key, label in (("qias", "QIAs"), ("changes", "TROCAS")):
            goal = (goals or {}).get(key, 0)
            team.append((f"% META {label}", percentage(Decimal(totals[key]) * 100 / goal) if goal else "—"))
    else:
        team += [("CRÉDITO", integer(totals["credit"])), ("NEOENERGIA", integer(totals["neo"])),
                 ("NR", integer(totals["NR"])), ("1 A 3 / 4 A 6", f'{integer(totals["1 A 3"])} / {integer(totals["4 A 6"])}')]
    for j, (label, value) in enumerate(team):
        x, y = 38 + (j % 4) * 254, 220 + (j // 4) * 65
        draw.text((x, y), _fit_image_text(draw, value, font(27, True), 240), font=font(27, True), fill="white")
        draw.text((x, y + 33), label, font=font(16), fill="#CBD5E1")

    for i, row in enumerate(rows):
        y = 167 + team_height + i * (row_height + 14)
        _, color, ink = PALETTE[row.get("color", daily_color(row["qias"]))]
        draw.rounded_rectangle((16, y, 1064, y + row_height), radius=24, fill=color)
        name = _fit_image_text(draw, row["name"], font(31, True), 875)
        _draw_daily_ordinal(draw, 48, y + 34, i + 1, ink)
        draw.text((82, y + 15), name, font=font(31, True), fill=ink)
        _draw_daily_status_icon(draw, 1020, y + 36, {"blue":"Azul","green":"Verde","yellow":"Amarelo","orange":"Laranja","red":"Vermelho"}[row.get("color", daily_color(row["qias"]))])
        for j, (label, value) in enumerate(row_metrics(row, view)):
            x, top = 38 + (j % 4) * 254, y + 64 + (j // 4) * 82
            if j % 4:
                draw.line((x - 12, top + 2, x - 12, top + 59), fill=ink, width=1)
            value_font = font(42 if j == 0 else 36 if j == 1 else 27, True)
            fitted = _fit_image_text(draw, value, value_font, 232)
            draw.text((x, top), fitted, font=value_font, fill=ink)
            label_font = font(18)
            if draw.textlength(label, font=label_font) > 238:
                label_font = font(15)
            draw.text((x, top + 40), label, font=label_font, fill=ink)
        for k, label in enumerate(("NR", "1 A 3", "4 A 6")):
            x = 38 + k * 338
            draw.rounded_rectangle((x, y + row_height - 70, x + 324, y + row_height - 10), radius=8, outline=ink, width=1)
            draw.text((x + 12, y + row_height - 66), label, font=font(19), fill=ink)
            draw.text((x + 306, y + row_height - 66), integer(row[label]), font=font(23, True), fill=ink, anchor="ra")
            draw.text((x + 12, y + row_height - 35), "Ticket Médio " + money(row.get("regime_tickets", {}).get(label, 0)), font=font(17), fill=ink)
    if not rows:
        draw.text((40, 205 + team_height), "Nenhum conciliador habilitado.", font=font(28), fill="#475569")
    footer = f"Atualizado em {synced_at:%d/%m/%Y %H:%M}"
    if any(r.get("cash_invalid") for r in rows):
        footer += " · Caixa e Ticket Médio parciais"
    draw.text((26, image.height - 34), footer, font=font(20), fill="#475569")
    output = io.BytesIO()
    image.save(output, "PNG")
    return output.getvalue()
