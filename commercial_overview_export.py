"""Exporta a Visão Geral do Comercial no mesmo padrão visual do ranking diário."""
import io


def _pct_text(value, goal):
    try:
        return f"{(float(value or 0) / float(goal or 0)) * 100:.0f}%" if float(goal or 0) else "0%"
    except Exception:
        return "0%"


def overview_ranking_png(ranking, cfg, team_filter="TODAS AS EQUIPES"):
    from PIL import Image, ImageDraw
    from app_core import (
        _daily_font,
        _draw_daily_brand,
        _draw_daily_ordinal,
        _draw_daily_status_icon,
        _daily_overlay_color,
        _fit_image_text,
        performance,
        normalize_text,
    )

    rows = list(ranking or [])
    width = 1080
    header_h = 270
    teams_h = 142
    columns_h = 62
    row_h = 96
    footer_h = 70
    height = header_h + teams_h + columns_h + max(1, len(rows)) * row_h + footer_h

    image = Image.new("RGB", (width, height), "#F4F7FB")
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, width, header_h), fill="#075B35")
    _draw_daily_brand(draw, 56, 38)

    filtered = team_filter not in (None, "", "TODAS AS EQUIPES")
    title = "RANKING DE VENDAS - VISAO GERAL" if not filtered else f"RANKING {str(team_filter).upper()} - VISAO GERAL"
    draw.text((56, 78), title, font=_daily_font(42 if filtered else 46, True), fill="#FFFFFF")

    month_names = ("JANEIRO", "FEVEREIRO", "MARCO", "ABRIL", "MAIO", "JUNHO", "JULHO", "AGOSTO", "SETEMBRO", "OUTUBRO", "NOVEMBRO", "DEZEMBRO")
    try:
        competence = f"{month_names[int(cfg.get('mes', 1)) - 1]}/{int(cfg.get('ano', 0))}"
    except Exception:
        competence = "VISAO GERAL"
    draw.text((width - 56, 48), competence, font=_daily_font(27, True), fill="#E7F7EE", anchor="ra")

    total_sales = sum(int(item.get("vendas", 0) or 0) for item in rows)
    total_projection = sum(int(item.get("projecao", 0) or 0) for item in rows)
    total_neo = sum(int(item.get("neo", 0) or 0) for item in rows)
    cards = (("VENDAS REALIZADAS", total_sales), ("PROJECAO", total_projection), ("NEOENERGIA", total_neo))
    for idx, (label, value) in enumerate(cards):
        left = 56 + idx * 326
        right = left + 300
        draw.rounded_rectangle((left, 160, right, 244), radius=13, fill="#FFFFFF" if idx < 2 else "#EAF7FD")
        draw.text(((left + right) // 2, 178), label, font=_daily_font(17, True), fill="#64748B", anchor="ma")
        draw.text(((left + right) // 2, 205), str(value), font=_daily_font(34, True), fill="#075B35" if idx < 2 else "#0878B9", anchor="ma")

    team_names = [str(team_filter)] if filtered else ["Equipe Interna", "Equipe Externa"]
    team_colors = {"Equipe Interna": "#075B35", "Equipe Externa": "#0EA5E9"}
    for idx, team_name in enumerate(team_names):
        subset = [item for item in rows if str(item.get("equipe", "")) == team_name]
        team_sales = sum(int(item.get("vendas", 0) or 0) for item in subset)
        team_projection = sum(int(item.get("projecao", 0) or 0) for item in subset)
        team_neo = sum(int(item.get("neo", 0) or 0) for item in subset)
        left = 56 if filtered else 56 + idx * 490
        right = 1022 if filtered else left + 466
        top = header_h + 22
        bottom = header_h + 116
        tone = team_colors.get(team_name, "#075B35")
        draw.rounded_rectangle((left, top, right, bottom), radius=13, fill="#FFFFFF", outline="#DDE5EE", width=2)
        draw.rounded_rectangle((left, top, left + 9, bottom), radius=5, fill=tone)
        draw.text((left + 28, top + 17), team_name.upper(), font=_daily_font(19, True), fill="#263349")
        metrics = ((right - 205, "VENDAS", team_sales, "#172033"), (right - 120, "PROJ.", team_projection, "#172033"), (right - 38, "NEO", team_neo, "#0878B9"))
        for metric_x, label, value, value_color in metrics:
            draw.text((metric_x, top + 17), label, font=_daily_font(13, True), fill="#748197", anchor="ma")
            draw.text((metric_x, top + 43), str(value), font=_daily_font(29, True), fill=value_color, anchor="ma")

    columns_top = header_h + teams_h
    draw.rectangle((34, columns_top, width - 34, columns_top + columns_h), fill="#E9EFF5")
    columns = ((58, "POS.", "la"), (135, "VENDEDOR", "la"), (585, "STATUS", "ma"), (700, "VENDAS", "ma"), (815, "PROJ.", "ma"), (920, "% META", "ma"), (1010, "NEO", "ma"))
    for x, label, anchor in columns:
        draw.text((x, columns_top + 21), label, font=_daily_font(17, True), fill="#536176", anchor=anchor)

    y = columns_top + columns_h
    for pos, item in enumerate(rows, 1):
        classification, fill, _ = performance(float(item.get("media", 0) or 0))
        text_fill = "#172033" if normalize_text(classification) == "amarelo" else "#FFFFFF"
        muted_fill = "#4B5563" if normalize_text(classification) == "amarelo" else "#E8EEF5"
        draw.rounded_rectangle((34, y, width - 34, y + row_h - 8), radius=18, fill=fill)
        _draw_daily_ordinal(draw, 78, y + 45, pos, text_fill)

        name_font = _daily_font(22, True)
        name = _fit_image_text(draw, item.get("vendedor", ""), name_font, 350)
        draw.text((135, y + 18), name, font=name_font, fill=text_fill)
        draw.text((135, y + 51), str(item.get("equipe", "")), font=_daily_font(16), fill=muted_fill)
        _draw_daily_status_icon(draw, 585, y + 46, classification)

        sales = int(item.get("vendas", 0) or 0)
        projection = int(item.get("projecao", 0) or 0)
        meta = int(item.get("meta_individual", 0) or 0)
        neo = int(item.get("neo", 0) or 0)
        draw.text((700, y + 25), str(sales), font=_daily_font(33, True), fill=text_fill, anchor="ma")
        draw.text((815, y + 25), str(projection), font=_daily_font(31, True), fill=text_fill, anchor="ma")
        draw.text((920, y + 27), _pct_text(projection, meta), font=_daily_font(25, True), fill=text_fill, anchor="ma")
        neo_left, neo_right = 976, 1042
        draw.rounded_rectangle((neo_left, y + 17, neo_right, y + 72), radius=10, fill=_daily_overlay_color(fill))
        draw.text(((neo_left + neo_right) // 2, y + 27), str(neo), font=_daily_font(29, True), fill=text_fill, anchor="ma")
        y += row_h

    if not rows:
        draw.text((56, columns_top + 95), "Nenhum vendedor local ativo.", font=_daily_font(25, True), fill="#64748B")

    draw.text((width // 2, height - 39), "PAINEL DE RESULTADOS · COMERCIAL · AFOGADOS", font=_daily_font(18, True), fill="#758397", anchor="ma")
    output = io.BytesIO()
    image.save(output, format="PNG", optimize=True)
    return output.getvalue()
