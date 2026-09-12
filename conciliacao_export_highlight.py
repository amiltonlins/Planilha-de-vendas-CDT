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
    summary_h = 116
    columns_h = 54
    row_h = 96
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
        middle = (left + right) // 2
        draw.rounded_rectangle((left, summary_top, right, summary_top + 82), radius=12, fill="#FFFFFF", outline="#DDE5EE", width=1)
        draw.text((left + card_w * 0.27, summary_top + 13), label, font=_daily_font(15, True), fill="#64748B", anchor="ma")
        draw.text((left + card_w * 0.27, summary_top + 39), value, font=_daily_font(31, True), fill="#172033", anchor="ma")
        draw.line((middle, summary_top + 13, middle, summary_top + 69), fill="#E2E8F0", width=2)
        draw.text((left + card_w * 0.75, summary_top + 13), "PROJEÇÃO", font=_daily_font(15, True), fill="#075B35", anchor="ma")
        draw.text((left + card_w * 0.75, summary_top + 39), projection, font=_daily_font(31, True), fill="#075B35", anchor="ma")

    columns_top = header_h + summary_h
    draw.rectangle((32, columns_top, width - 32, columns_top + columns_h), fill="#E9EFF5")
    columns = (
        (56, "POS.", "la"),
        (128, "CONCILIADOR", "la"),
        (500, "STATUS", "ma"),
        (610, "QIAs HOJE", "ma"),
        (720, "PROJEÇÃO", "ma"),
        (840, "TROCAS HOJE", "ma"),
        (970, "PROJEÇÃO", "ma"),
    )
    for x, label, anchor in columns:
        draw.text((x, columns_top + 17), label, font=_daily_font(15, True), fill="#536176", anchor=anchor)

    status_emoji = {
        "Azul": "🔵",
        "Verde": "🟢",
        "Amarelo": "🟡",
        "Laranja": "🟠",
        "Vermelho": "🔴",
    }

    y = columns_top + columns_h
    for pos, item in enumerate(rows, 1):
        classification, fill = _classification(item)
        text_fill = "#172033" if classification == "Amarelo" else "#FFFFFF"
        projection_fill = "#7A4600" if classification == "Amarelo" else "#FFFFFF"

        draw.rounded_rectangle((32, y + 4, width - 32, y + row_h - 7), radius=16, fill=fill)
        _draw_daily_ordinal(draw, 72, y + 44, pos, text_fill)
        name_font = _daily_font(23, True)
        name = _fit_image_text(draw, item.get("name", ""), name_font, 325)
        draw.text((128, y + 29), name, font=name_font, fill=text_fill)

        qias = item.get("qias", 0)
        changes = item.get("changes", 0)
        qias_projection = _daily_projection(qias, period, synced_at)
        changes_projection = _daily_projection(changes, period, synced_at)

        draw.text((500, y + 26), status_emoji.get(classification, "⚪"), font=_daily_font(27, True), fill=text_fill, anchor="ma")
        draw.text((610, y + 28), _integer(qias), font=_daily_font(30, True), fill=text_fill, anchor="ma")
        draw.text((720, y + 28), _integer(qias_projection), font=_daily_font(30, True), fill=projection_fill, anchor="ma")
        draw.text((840, y + 28), _integer(changes), font=_daily_font(30, True), fill=text_fill, anchor="ma")
        draw.text((970, y + 28), _integer(changes_projection), font=_daily_font(30, True), fill=projection_fill, anchor="ma")
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
