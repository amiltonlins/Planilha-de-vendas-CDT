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


def ranking_png(rows, view, period, totals, goals, synced_at):
    """Gera o PNG da Conciliação reutilizando o mesmo padrão técnico do Painel Comercial."""
    from PIL import Image, ImageDraw
    from app_core import (
        _daily_font,
        _draw_daily_brand,
        _draw_daily_ordinal,
        _draw_daily_status_icon,
        _daily_overlay_color,
        _fit_image_text,
    )

    # Mesmas dimensões, blocos, margens e alturas do export diário comercial.
    width = 1080
    header_h = 270
    teams_h = 142
    columns_h = 62
    row_h = 94
    footer_h = 70
    height = header_h + teams_h + columns_h + max(1, len(rows)) * row_h + footer_h

    image = Image.new("RGB", (width, height), "#F4F7FB")
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, width, header_h), fill="#075B35")

    # Mesmo tratamento de marca do Comercial, inclusive o til desenhado manualmente em CARTÃO.
    _draw_daily_brand(draw, 56, 38)

    titles = {
        "VISÃO GERAL": "RANKING DE CONCILIAÇÃO - GERAL",
        "DIÁRIO": "RANKING DE CONCILIAÇÃO - HOJE",
        "SEMANAL": "RANKING DE CONCILIAÇÃO - SEMANA",
    }
    draw.text((56, 78), titles.get(view, "RANKING DE CONCILIAÇÃO"), font=_daily_font(48, True), fill="#FFFFFF")
    draw.text((width - 56, 48), synced_at.strftime("%d/%m/%Y"), font=_daily_font(27, True), fill="#E7F7EE", anchor="ra")

    # Os três cards do topo mantêm exatamente a mesma geometria do Comercial.
    if view == "VISÃO GERAL":
        cards = (
            ("QIAs DO MÊS", _integer(totals.get("qias", 0))),
            ("TROCAS TOTAL", _integer(totals.get("changes", 0))),
            ("TICKET MÉDIO", _money(totals.get("ticket", 0))),
        )
    elif view == "DIÁRIO":
        cards = (
            ("QIAs HOJE", _integer(totals.get("qias", 0))),
            ("TROCAS HOJE", _integer(totals.get("changes", 0))),
            ("NEO HOJE", _integer(totals.get("neo", 0))),
        )
    else:
        projected_award = sum(float(r.get("award", 0) or 0) for r in rows)
        cards = (
            ("QIAs NA SEMANA", _integer(totals.get("qias", 0))),
            ("TROCAS NA SEMANA", _integer(totals.get("changes", 0))),
            ("PRÊMIO PROJETADO", _money(projected_award)),
        )

    for idx, (label, value) in enumerate(cards):
        left = 56 + idx * 326
        right = left + 300
        fill = "#FFFFFF" if idx < 2 else "#EAF7FD"
        value_color = "#075B35" if idx < 2 else "#0878B9"
        draw.rounded_rectangle((left, 160, right, 244), radius=13, fill=fill)
        draw.text(((left + right) // 2, 178), label, font=_daily_font(18, True), fill="#64748B", anchor="ma")
        draw.text(((left + right) // 2, 205), str(value), font=_daily_font(34 if idx < 2 else 30, True), fill=value_color, anchor="ma")

    # Faixa intermediária: mesma estrutura dos dois cards de equipe do Comercial.
    top = header_h + 22
    bottom = header_h + 116

    # Card 1 — indicadores operacionais da Conciliação.
    left = 56
    right = 522
    draw.rounded_rectangle((left, top, right, bottom), radius=13, fill="#FFFFFF", outline="#DDE5EE", width=2)
    draw.rounded_rectangle((left, top, left + 9, bottom), radius=5, fill="#075B35")
    if view == "SEMANAL":
        card1_title = "RESULTADO DA SEMANA"
        card1_metrics = (
            (right - 205, "QIAs", _integer(totals.get("qias", 0)), "#172033"),
            (right - 120, "TROCAS", _integer(totals.get("changes", 0)), "#172033"),
            (right - 38, "NEO", _integer(totals.get("neo", 0)), "#0878B9"),
        )
    else:
        card1_title = "QIAs POR RÉGUA"
        card1_metrics = (
            (right - 205, "NR", _integer(totals.get("NR", 0)), "#B91C1C"),
            (right - 120, "1 A 3", _integer(totals.get("1 A 3", 0)), "#174BD6"),
            (right - 38, "4 A 6", _integer(totals.get("4 A 6", 0)), "#166534"),
        )
    draw.text((left + 28, top + 17), card1_title, font=_daily_font(19, True), fill="#263349")
    for metric_x, label, value, value_color in card1_metrics:
        draw.text((metric_x, top + 17), label, font=_daily_font(13, True), fill="#748197", anchor="ma")
        draw.text((metric_x, top + 43), str(value), font=_daily_font(29, True), fill=value_color, anchor="ma")

    # Card 2 — metas/premiação, seguindo exatamente a mesma caixa, borda e alinhamentos.
    left = 546
    right = 1022
    draw.rounded_rectangle((left, top, right, bottom), radius=13, fill="#FFFFFF", outline="#DDE5EE", width=2)
    draw.rounded_rectangle((left, top, left + 9, bottom), radius=5, fill="#0EA5E9")
    if view == "VISÃO GERAL":
        weekly = sum(float(r.get("weekly_award", 0) or 0) for r in rows)
        monthly = sum(float(r.get("projected_award", 0) or 0) for r in rows)
        card2_title = "PREMIAÇÃO"
        card2_metrics = (
            (right - 205, "SEMANAL", _money(weekly), "#08733F"),
            (right - 120, "MENSAL", _money(monthly), "#4C1D95"),
            (right - 38, "ATIVOS", _integer(len(rows)), "#172033"),
        )
    elif view == "DIÁRIO":
        card2_title = "TROCAS E TICKET"
        card2_metrics = (
            (right - 205, "CRÉDITO", _integer(totals.get("credit", 0)), "#172033"),
            (right - 120, "NEO", _integer(totals.get("neo", 0)), "#0878B9"),
            (right - 38, "TICKET", _money(totals.get("ticket", 0)), "#172033"),
        )
    else:
        won = sum(float(r.get("earned_award", 0) or 0) for r in rows)
        projected = sum(float(r.get("award", 0) or 0) for r in rows)
        card2_title = "PREMIAÇÃO"
        card2_metrics = (
            (right - 205, "CONQUIST.", _money(won), "#08733F"),
            (right - 120, "PROJET.", _money(projected), "#4C1D95"),
            (right - 38, "ATIVOS", _integer(len(rows)), "#172033"),
        )
    draw.text((left + 28, top + 17), card2_title, font=_daily_font(19, True), fill="#263349")
    for metric_x, label, value, value_color in card2_metrics:
        draw.text((metric_x, top + 17), label, font=_daily_font(13, True), fill="#748197", anchor="ma")
        size = 23 if str(value).startswith("R$") else 29
        draw.text((metric_x, top + 43), str(value), font=_daily_font(size, True), fill=value_color, anchor="ma")

    # Cabeçalho de colunas: mesma posição, altura e tipografia do Comercial.
    columns_top = header_h + teams_h
    draw.rectangle((34, columns_top, width - 34, columns_top + columns_h), fill="#E9EFF5")
    if view == "SEMANAL":
        columns = (
            (58, "POS.", "la"),
            (135, "CONCILIADOR", "la"),
            (615, "STATUS", "ma"),
            (730, "QIAs", "ma"),
            (835, "TROCAS", "ma"),
            (960, "PRÊMIO", "ma"),
        )
    elif view == "DIÁRIO":
        columns = (
            (58, "POS.", "la"),
            (135, "CONCILIADOR", "la"),
            (615, "STATUS", "ma"),
            (730, "QIAs", "ma"),
            (835, "TROCAS", "ma"),
            (960, "NEO HOJE", "ma"),
        )
    else:
        columns = (
            (58, "POS.", "la"),
            (135, "CONCILIADOR", "la"),
            (615, "STATUS", "ma"),
            (730, "QIAs", "ma"),
            (835, "TROCAS", "ma"),
            (960, "NEO", "ma"),
        )
    for x, label, anchor in columns:
        draw.text((x, columns_top + 21), label, font=_daily_font(18, True), fill="#536176", anchor=anchor)

    y = columns_top + columns_h
    for pos, item in enumerate(rows, 1):
        classification, fill = _classification(item)
        text_fill = "#172033" if classification == "Amarelo" else "#FFFFFF"
        muted_fill = "#4B5563" if classification == "Amarelo" else "#E8EEF5"
        draw.rounded_rectangle((34, y, width - 34, y + row_h - 8), radius=18, fill=fill)
        _draw_daily_ordinal(draw, 78, y + 45, pos, text_fill)

        name_font = _daily_font(23, True)
        name = _fit_image_text(draw, item.get("name", ""), name_font, 390)
        draw.text((135, y + 20), name, font=name_font, fill=text_fill)
        if view == "VISÃO GERAL":
            sub = f"Meta: {_integer(item.get('qias_goal', 0))} QIAs · TM {_money(item.get('ticket', 0))}"
        elif view == "DIÁRIO":
            sub = f"{_integer(item.get('week_qias', 0))} na semana · {_integer(item.get('month_qias', 0))} no mês"
        else:
            next_award = _money(item.get("next_award", 0)) if item.get("next_award", 0) else "faixa máxima"
            sub = f"Proj. {_integer(item.get('qias_projection', 0))} QIAs · Próximo: {next_award}"
        sub = _fit_image_text(draw, sub, _daily_font(15), 405)
        draw.text((135, y + 53), sub, font=_daily_font(15), fill=muted_fill)

        _draw_daily_status_icon(draw, 615, y + 46, classification)
        draw.text((730, y + 25), _integer(item.get("qias", 0)), font=_daily_font(36, True), fill=text_fill, anchor="ma")
        draw.text((835, y + 25), _integer(item.get("changes", 0)), font=_daily_font(32, True), fill=text_fill, anchor="ma")

        metric_left, metric_right = 900, 1042
        draw.rounded_rectangle((metric_left, y + 17, metric_right, y + 72), radius=10, fill=_daily_overlay_color(fill))
        if view == "SEMANAL":
            metric = _money(item.get("award", 0))
            metric_font = _daily_font(23, True)
        else:
            metric = _integer(item.get("neo", 0))
            metric_font = _daily_font(31, True)
        draw.text(((metric_left + metric_right) // 2, y + 27), metric, font=metric_font, fill=text_fill, anchor="ma")
        y += row_h

    draw.text((width // 2, height - 39), "PAINEL DE RESULTADOS · CONCILIAÇÃO", font=_daily_font(18, True), fill="#758397", anchor="ma")
    output = io.BytesIO()
    image.save(output, format="PNG", optimize=True)
    return output.getvalue()
