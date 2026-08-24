#!/usr/bin/env python3
"""Camada de UI: Relatório Geral na Gestão + detalhamento executivo das equipes."""
import html
import math
import app_core as _core

_original_general_report_xlsx = _core.general_report_xlsx_bytes


def _management_general_report_xlsx(team, all_days):
    """Na Gestão, exibe a tabela completa antes de gerar o mesmo Excel já existente."""
    import streamlit as st

    columns = [
        ("equipe", "EQUIPE"), ("vendedor", "VENDEDOR"), ("vendas", "TOTAL"),
        ("projecao", "PROJEÇÃO"), ("media", "MÉDIA"), ("zeros", "ZEROS"),
        ("meta_pct", "% META"), ("neo", "NEO"), ("neo_pct_fmt", "% NEO"),
        ("base_fmt", "PREMIAÇÃO ATUAL"), ("proj_fmt", "PREMIAÇÃO PROJETADA"),
        ("neo_proj_fmt", "BÔNUS NEO PROJ."), ("adim_proj_fmt", "BÔNUS (SE) 100% ADIM"),
        ("premio_fmt", "SEMANAIS"), ("total_proj_fmt", "TOTAL VAR. PROJ."),
    ] + [(day.day, str(day.day)) for day in all_days]
    display = _core.general_report_display(team)
    row_color = lambda item: _core.performance(item["media"])[1]
    st.markdown(_core.table_html(display, columns, row_color, True), unsafe_allow_html=True)
    return _original_general_report_xlsx(team, all_days)


_core.general_report_xlsx_bytes = _management_general_report_xlsx
_core.render_general_report = lambda *args, **kwargs: None


def _team_popup(st, team_name, goal, metrics, sellers):
    """Popup executivo da equipe. Reutiliza os cálculos existentes e acrescenta headcount gerencial."""
    productivity = 40
    active_count = len(sellers)
    ideal_headcount = math.ceil(int(goal or 0) / productivity) if int(goal or 0) > 0 else 0
    hiring_need = max(0, ideal_headcount - active_count)
    counts = _core.team_performance_distribution(sellers, team_name)

    @st.dialog(f"{team_name} — detalhamento", width="large")
    def show():
        hiring_text = f"{hiring_need} vendedor{'es' if hiring_need != 1 else ''}" if hiring_need else "Equipe suficiente"
        st.markdown(
            f'''<style>
            [data-testid="stDialog"] .team-detail-hero{{background:linear-gradient(120deg,#0F172A,#172554);color:#fff;border-radius:14px;padding:16px;text-align:center;margin-bottom:8px}}
            [data-testid="stDialog"] .team-detail-hero small{{display:block;font-size:.62rem;font-weight:900;letter-spacing:.08em;color:#CBD5E1}}
            [data-testid="stDialog"] .team-detail-hero strong{{display:block;font-size:2.6rem;line-height:1;margin-top:7px;font-weight:950}}
            [data-testid="stDialog"] .team-detail-grid{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:7px;margin:7px 0}}
            [data-testid="stDialog"] .team-detail-kpi{{border:1px solid #E2E8F0;border-radius:10px;padding:9px;background:#fff;min-width:0}}
            [data-testid="stDialog"] .team-detail-kpi small{{display:block;font-size:.52rem;font-weight:900;color:#64748B}}
            [data-testid="stDialog"] .team-detail-kpi strong{{display:block;font-size:1.18rem;color:#0F172A;margin-top:5px;font-weight:950}}
            [data-testid="stDialog"] .team-detail-kpi.needed{{border-top:3px solid #F59E0B}}
            [data-testid="stDialog"] .team-capacity{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:7px;margin:9px 0}}
            [data-testid="stDialog"] .team-hiring{{background:#F8FAFC;border:1px solid #E2E8F0;border-radius:11px;padding:10px}}
            [data-testid="stDialog"] .team-hiring small{{display:block;font-size:.50rem;font-weight:900;color:#64748B}}
            [data-testid="stDialog"] .team-hiring strong{{display:block;font-size:1.05rem;margin-top:5px;color:#0F172A}}
            @media(max-width:700px){{
              [data-testid="stDialog"] .team-detail-hero{{padding:11px}}
              [data-testid="stDialog"] .team-detail-hero strong{{font-size:2rem}}
              [data-testid="stDialog"] .team-detail-grid,[data-testid="stDialog"] .team-capacity{{grid-template-columns:repeat(2,minmax(0,1fr));gap:5px}}
              [data-testid="stDialog"] .team-detail-kpi,[data-testid="stDialog"] .team-hiring{{padding:7px}}
              [data-testid="stDialog"] .team-detail-kpi strong,[data-testid="stDialog"] .team-hiring strong{{font-size:.92rem}}
            }}
            </style>
            <div class="team-detail-hero"><small>META DA EQUIPE</small><strong>{int(goal or 0)}</strong></div>
            <div class="team-detail-grid">
              <div class="team-detail-kpi"><small>VENDAS REALIZADAS</small><strong>{metrics['sales']}</strong></div>
              <div class="team-detail-kpi"><small>FALTAM PARA META</small><strong>{metrics['missing']}</strong></div>
              <div class="team-detail-kpi needed"><small>PRECISA FAZER POR DIA</small><strong>{metrics['needed']:.1f}</strong></div>
              <div class="team-detail-kpi"><small>% DA META</small><strong>{_core.pct(metrics['attainment'])}</strong></div>
              <div class="team-detail-kpi"><small>PROJEÇÃO</small><strong>{metrics['projection']}</strong></div>
              <div class="team-detail-kpi"><small>MÉDIA/DIA</small><strong>{metrics['average']:.1f}</strong></div>
              <div class="team-detail-kpi"><small>DIAS TRABALHADOS</small><strong>{metrics['elapsed']}</strong></div>
              <div class="team-detail-kpi"><small>DIAS RESTANTES</small><strong>{metrics['remaining']}</strong></div>
            </div>
            <div class="team-capacity">
              <div class="team-hiring"><small>PRODUTIVIDADE DE REFERÊNCIA</small><strong>{productivity} vendas/vendedor</strong></div>
              <div class="team-hiring"><small>HEADCOUNT IDEAL</small><strong>{ideal_headcount}</strong></div>
              <div class="team-hiring"><small>VENDEDORES ATIVOS</small><strong>{active_count}</strong></div>
              <div class="team-hiring"><small>NECESSÁRIO CONTRATAR</small><strong>{html.escape(hiring_text)}</strong></div>
            </div>''', unsafe_allow_html=True)

        st.caption(f"Performance: 🔵 {counts.get('Azul',0)}  |  🟢 {counts.get('Verde',0)}  |  🟡 {counts.get('Amarelo',0)}  |  🔴 {counts.get('Vermelho',0)}")
        ordered = sorted(sellers, key=lambda x: (x.get("vendas",0), x.get("projecao",0)), reverse=True)
        rows = []
        for seller in ordered:
            meta = int(seller.get("meta_individual",0) or 0)
            rows.append({
                "VENDEDOR": seller.get("vendedor",""),
                "VENDAS": int(seller.get("vendas",0) or 0),
                "MÉDIA/DIA": round(float(seller.get("media",0) or 0),2),
                "PROJEÇÃO": int(seller.get("projecao",0) or 0),
                "% META": _core.pct((seller.get("projecao",0) or 0)/meta if meta else 0),
            })
        if rows:
            st.dataframe(rows, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum vendedor ativo nesta equipe.")
    show()


def _team_dashboard(channels, total, summary, cfg, data_until, updated, visible_team=None):
    """Mantém os cards atuais e os transforma em entradas clicáveis para o popup."""
    import streamlit as st

    internal_goal = int(cfg.get("meta_equipe_interna",0) or 0)
    external_goal = int(cfg.get("meta_equipe_externa",0) or 0)
    internal = _core.team_performance_metrics(summary,"Equipe Interna",internal_goal)
    external = _core.team_performance_metrics(summary,"Equipe Externa",external_goal)
    visible_team = visible_team or []
    internal_sellers = [x for x in visible_team if x.get("equipe") == "Equipe Interna"]
    external_sellers = [x for x in visible_team if x.get("equipe") == "Equipe Externa"]
    internal_perf = _core.team_performance_distribution(visible_team,"Equipe Interna")
    external_perf = _core.team_performance_distribution(visible_team,"Equipe Externa")

    requested = st.query_params.get("team")
    if requested in ("internal","external"):
        try:
            del st.query_params["team"]
        except KeyError:
            pass
        if requested == "internal":
            _team_popup(st,"Equipe Interna",internal_goal,internal,internal_sellers)
        else:
            _team_popup(st,"Equipe Externa",external_goal,external,external_sellers)

    internal_card = _core.team_performance_card_html("Equipe Interna",internal_goal,internal,"internal",internal_perf)
    external_card = _core.team_performance_card_html("Equipe Externa",external_goal,external,"external",external_perf)
    return (
        '<style>.team-card-link{display:block;color:inherit;text-decoration:none!important;min-width:0}.team-card-link:hover{text-decoration:none!important}.team-card-link .pc-team-card{cursor:pointer;transition:transform .12s ease,box-shadow .12s ease}.team-card-link:hover .pc-team-card{transform:translateY(-1px);box-shadow:0 5px 16px rgba(15,23,42,.10)}</style>'
        '<div class="pc-dashboard pc-dashboard-teams-only"><div class="pc-team-grid">'
        f'<a class="team-card-link" href="?team=internal" target="_self">{internal_card}</a>'
        f'<a class="team-card-link" href="?team=external" target="_self">{external_card}</a>'
        '</div></div>'
    )


_core.production_channel_dashboard_html = _team_dashboard


if __name__ == "__main__":
    _core.render_app()
