import io
from decimal import Decimal


def _money(value):
    return "R$ " + f"{float(value or 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _integer(value):
    return f"{float(value or 0):,.0f}".replace(",", ".")


def _pct(value, goal):
    try:
        if not goal:
            return 0.0
        return max(0.0, min(100.0, float(Decimal(str(value or 0)) * 100 / Decimal(str(goal)))))
    except Exception:
        return 0.0


def _classification(row):
    color = str(row.get("color", "red")).lower()
    if color == "blue":
        return "Azul", "#0891B2"
    if color == "green":
        return "Verde", "#16A34A"
    if color in {"yellow", "orange"}:
        return "Amarelo", "#F59E0B"
    return "Vermelho", "#DC2626"


def _award_value(item, view):
    if view == "SEMANAL":
        return item.get("award", item.get("weekly_award", 0))
    if view == "VISÃO GERAL":
        return item.get("projected_award", item.get("monthly_award", 0))
    return item.get("weekly_award", item.get("award", 0))


def ranking_png(rows, view, period, totals, goals, synced_at):
    """Gera um PNG compacto da Conciliação, focado apenas nos indicadores essenciais."""
    from PIL import Image, ImageDraw
    from app_core import (
        _daily_font,
        _draw_daily_brand,
        _draw_daily_ordinal,
        _draw_daily_status_icon,
        _daily_overlay_color,
        _fit_image_text,
    )

    width = 1080
    header_h = 205
    summary_h = 112
    columns_h = 54
    row_h = 122 if view == "VISÃO GERAL" else 102
    footer_h = 60
    height = header_h + summary_h + columns_h + max(1, len(rows)) * row_h + footer_h

    image = Image.new("RGB", (width, height), "#F4F7FB")
    draw = ImageDraw.Draw(image)

    # Cabeçalho compacto.
    draw.rectangle((0, 0, width, header_h), fill="#075B35")
    _draw_daily_brand(draw, 52, 28)
    titles = {
        "VISÃO GERAL": "RANKING CONCILIAÇÃO · GERAL",
        "DIÁRIO": "RANKING CONCILIAÇÃO · HOJE",
        "SEMANAL": "RANKING CONCILIAÇÃO · SEMANA",
    }
    draw.text((52, 78), titles.get(view, "RANKING CONCILIAÇÃO"), font=_daily_font(42, True), fill="#FFFFFF")
    draw.text((52, 132), period, font=_daily_font(22), fill="#DDF3E8")
    draw.text((width - 52, 38), synced_at.strftime("%d/%m/%Y %H:%M"), font=_daily_font(22, True), fill="#E7F7EE", anchor="ra")

    # Resumo da equipe: somente quatro indicadores essenciais.
    summary_top = header_h + 16
    card_gap = 14
    card_w = (width - 104 - card_gap * 3) // 4
    summary_cards = (
        ("QIAs", _integer(totals.get("qias", 0))),
        ("TROCAS", _integer(totals.get("changes", 0))),
        ("NEOENERGIA", _integer(totals.get("neo", 0))),
        ("TICKET MÉDIO", _money(totals.get("ticket", 0))),
    )
    for idx, (label, value) in enumerate(summary_cards):
        left = 52 + idx * (card_w + card_gap)
        right = left + card_w
        draw.rounded_rectangle((left, summary_top, right, summary_top + 78), radius=12, fill="#FFFFFF", outline="#DDE5EE", width=1)
        draw.text(((left + right) // 2, summary_top + 15), label, font=_daily_font(15, True), fill="#64748B", anchor="ma")
        size = 27 if str(value).startswith("R$") else 31
        draw.text(((left + right) // 2, summary_top + 41), str(value), font=_daily_font(size, True), fill="#172033", anchor="ma")

    # Cabeçalho das colunas simplificado.
    columns_top = header_h + summary_h
    draw.rectangle((32, columns_top, width - 32, columns_top + columns_h), fill="#E9EFF5")
    columns = (
        (56, "POS.", "la"),
        (128, "CONCILIADOR", "la"),
        (610, "QIAs", "ma"),
        (755, "TROCAS", "ma"),
        (910, "PRÊMIO", "ma"),
    )
    for x, label, anchor in columns:
        draw.text((x, columns_top + 17), label, font=_daily_font(17, True), fill="#536176", anchor=anchor)

    # Ranking: posição, nome, realizado/projeção e prêmio. Na visão geral, réguas em linha discreta.
    y = columns_top + columns_h
    for pos, item in enumerate(rows, 1):
        classification, fill = _classification(item)
        text_fill = "#172033" if classification == "Amarelo" else "#FFFFFF"
        muted_fill = "#4B5563" if classification == "Amarelo" else "#E8EEF5"

        draw.rounded_rectangle((32, y + 4, width - 32, y + row_h - 8), radius=17, fill=fill)
        _draw_daily_ordinal(draw, 72, y + 43, pos, text_fill)

        name_font = _daily_font(23, True)
        name = _fit_image_text(draw, item.get("name", ""), name_font, 390)
        draw.text((128, y + 18), name, font=name_font, fill=text_fill)
        _draw_daily_status_icon(draw, 535, y + 39, classification)

        qias = _integer(item.get("qias", 0))
        qias_proj = _integer(item.get("qias_projection", 0))
        changes = _integer(item.get("changes", 0))
        changes_proj = _integer(item.get("changes_projection", 0))

        draw.text((610, y + 15), qias, font=_daily_font(31, True), fill=text_fill, anchor="ma")
        draw.text((610, y + 51), f"Proj. {qias_proj}", font=_daily_font(14, True), fill=muted_fill, anchor="ma")
        draw.text((755, y + 15), changes, font=_daily_font(29, True), fill=text_fill, anchor="ma")
        draw.text((755, y + 51), f"Proj. {changes_proj}", font=_daily_font(14, True), fill=muted_fill, anchor="ma")

        award = _money(_award_value(item, view))
        metric_left, metric_right = 842, 1018
        draw.rounded_rectangle((metric_left, y + 14, metric_right, y + 70), radius=10, fill=_daily_overlay_color(fill))
        draw.text(((metric_left + metric_right) // 2, y + 28), award, font=_daily_font(22, True), fill=text_fill, anchor="ma")

        if view == "VISÃO GERAL":
            nr = _integer(item.get("NR", 0))
            one_three = _integer(item.get("1 A 3", 0))
            four_six = _integer(item.get("4 A 6", 0))
            ruler = f"NR {nr}   ·   1 a 3 {one_three}   ·   4 a 6 {four_six}"
            draw.text((128, y + 82), ruler, font=_daily_font(15, True), fill=muted_fill)
        else:
            ticket = _money(item.get("ticket", 0))
            draw.text((128, y + 62), f"Ticket médio {ticket}", font=_daily_font(14), fill=muted_fill)

        y += row_h

    if not rows:
        draw.text((52, columns_top + 92), "Nenhum conciliador habilitado.", font=_daily_font(25, True), fill="#64748B")

    draw.text((width // 2, height - 33), "PAINEL DE RESULTADOS · CONCILIAÇÃO", font=_daily_font(17, True), fill="#758397", anchor="ma")
    output = io.BytesIO()
    image.save(output, format="PNG", optimize=True)
    return output.getvalue()
