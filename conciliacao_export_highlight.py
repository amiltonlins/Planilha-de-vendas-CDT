"""Export da Conciliação com maior destaque visual para projeções no DIÁRIO."""
import io
from datetime import datetime

from conciliacao_export_reference import (
    ranking_png as _base_ranking_png,
    _daily_projection,
    _integer,
    _classification,
)


def _daily_ranking_png(rows, period, totals, synced_at):
    from PIL import Image, ImageDraw
    from app_core import _daily_font, _draw_daily_brand, _draw_daily_ordinal, _fit_image_text

    width = 1080
    header_h = 190
    summary_h = 128
    columns_h = 54
    row_h = 108
    footer_h = 58
    height = header_h + summary_h + columns_h + max(1, len(rows)) * row_h + footer_h

    image = Image.new("RGB", (width, height), "#F4F7FB")
    draw = ImageDraw.Draw(image)

    draw.rectangle((0, 0, width, header_h), fill="#075B35")
    _draw_daily_brand(draw, 52, 27)
    draw.text((52, 77), "RANKING DIÁRIO · CONCILIAÇÃO", font=_daily_font(42, True), fill="#FFFFFF")
    draw.text((52, 132), period, font=_daily_font(22), fill="#DDF3E8")
    draw.text((width - 52, 40), synced_at.strftime("%H:%M"), font=_daily_font(22, True), fill="#E7F7EE", anchor="ra")

    total_qias = totals.get("qias", 0)
    total_changes = totals.get("changes", 0)
    projected_qias = sum(_daily_projection(r.get("qias", 0), period, synced_at) for r in rows)
    projected_changes = sum(_daily_projection(r.get("changes", 0), period, synced_at) for r in rows)

    summary_top = header_h + 14
    cards = (
        ("QIAs HOJE", _integer(total_qias), _integer(projected_qias)),
        ("TROCAS HOJE", _integer(total_changes), _integer(projected_changes)),
    )
    card_gap = 18
    card_w = (width - 104 - card_gap) // 2
    for idx, (label, value, projection) in enumerate(cards):
        left = 52 + idx * (card_w + card_gap)
        right = left + card_w
        bottom = summary_top + 96
        draw.rounded_rectangle((left, summary_top, right, bottom), radius=14, fill="#FFFFFF", outline="#DDE5EE", width=1)
        draw.text((left + 20, summary_top + 13), label, font=_daily_font(15, True), fill="#64748B")
        draw.text((left + 20, summary_top + 40), value, font=_daily_font(31, True), fill="#172033")
        badge_left = right - 225
        draw.rounded_rectangle((badge_left, summary_top + 15, right - 16, bottom - 15), radius=12, fill="#E8F5EE")
        draw.text(((badge_left + right - 16) // 2, summary_top + 27), "PROJEÇÃO", font=_daily_font(14, True), fill="#075B35", anchor="ma")
        draw.text(((badge_left + right - 16) // 2, summary_top + 50), projection, font=_daily_font(29, True), fill="#075B35", anchor="ma")

    columns_top = header_h + summary_h
    draw.rectangle((32, columns_top, width - 32, columns_top + columns_h), fill="#E9EFF5")
    columns = ((56, "POS.", "la"), (128, "CONCILIADOR", "la"), (660, "QIAs HOJE", "ma"), (895, "TROCAS HOJE", "ma"))
    for x, label, anchor in columns:
        draw.text((x, columns_top + 17), label, font=_daily_font(17, True), fill="#536176", anchor=anchor)

    y = columns_top + columns_h
    for pos, item in enumerate(rows, 1):
        classification, fill = _classification(item)
        text_fill = "#172033" if classification == "Amarelo" else "#FFFFFF"
        badge_fill = "#FFF7E6" if classification == "Amarelo" else "#FFFFFF"
        badge_text = "#8A5200" if classification == "Amarelo" else fill

        draw.rounded_rectangle((32, y + 4, width - 32, y + row_h - 7), radius=16, fill=fill)
        _draw_daily_ordinal(draw, 72, y + 49, pos, text_fill)
        name_font = _daily_font(24, True)
        name = _fit_image_text(draw, item.get("name", ""), name_font, 410)
        draw.text((128, y + 34), name, font=name_font, fill=text_fill)

        qias = item.get("qias", 0)
        changes = item.get("changes", 0)
        qias_projection = _daily_projection(qias, period, synced_at)
        changes_projection = _daily_projection(changes, period, synced_at)

        for center, actual, projection in ((660, qias, qias_projection), (895, changes, changes_projection)):
            draw.text((center - 58, y + 18), _integer(actual), font=_daily_font(29, True), fill=text_fill, anchor="ma")
            left, right = center + 1, center + 92
            draw.rounded_rectangle((left, y + 13, right, y + 83), radius=11, fill=badge_fill)
            draw.text(((left + right) // 2, y + 23), "PROJ.", font=_daily_font(12, True), fill=badge_text, anchor="ma")
            draw.text(((left + right) // 2, y + 45), _integer(projection), font=_daily_font(26, True), fill=badge_text, anchor="ma")
        y += row_h

    if not rows:
        draw.text((52, columns_top + 86), "Nenhum conciliador habilitado.", font=_daily_font(25, True), fill="#64748B")

    try:
        target_day = datetime.strptime(period, "%d/%m/%Y").date()
        schedule = "09H–13H" if target_day.weekday() == 5 else "09H–18H"
    except Exception:
        schedule = "09H–18H"
    draw.text((width // 2, height - 31), f"PROJEÇÃO DO DIA · JORNADA {schedule}", font=_daily_font(16, True), fill="#758397", anchor="ma")
    output = io.BytesIO()
    image.save(output, format="PNG", optimize=True)
    return output.getvalue()


def ranking_png(rows, view, period, totals, goals, synced_at):
    if view == "DIÁRIO":
        return _daily_ranking_png(rows, period, totals, synced_at)
    return _base_ranking_png(rows, view, period, totals, goals, synced_at)
