#!/usr/bin/env python3
"""Camada de interação sobre o núcleo existente do painel."""
# Redeploy marker: versão estável sem interceptação global de st.markdown.
import copy
import html
import inspect
import math
from urllib.parse import quote
import app_core as _core

# Load both sectors at startup so Streamlit watches their source files even
# when the session starts on the login screen or the Commercial dashboard.
import conciliacao as _conciliacao_data
import conciliacao_visual as _conciliacao_visual
import conciliacao_ui as _conciliacao_ui
import online_commercial as _online_commercial

# O link share.google é uma página de compartilhamento, não um arquivo PNG direto.
# Usamos uma URL direta de PNG para garantir que a logo carregue no navegador.
_online_commercial.ACCESS_LOGO_URL = "https://www.todosbensprotegidos.com.br/Imagens/logo-cartao-todos.png"

# O Streamlit não garante que sitecustomize.py do repositório seja importado
# automaticamente no boot. Fazemos a carga explícita antes de instalar os hooks
# do Comercial, garantindo o mesmo seletor semanal no Comercial e Conciliação.
import sitecustomize as _sitecustomize
_sitecustomize._install_week_selector_standard()

_original_team_card_html = _core.team_performance_card_html
_original_render_management = _core.render_management


def _merge_registry_preserving_sellers(base, current):
    """Importação nunca altera configurações administrativas já persistidas."""
    cfg = copy.deepcopy(base)
    if current is not None:
        cfg.update(copy.deepcopy(current))
        cfg["vendedores"] = copy.deepcopy(current.get("vendedores", []))
    else:
        cfg["vendedores"] = copy.deepcopy(base.get("vendedores", []))
    return cfg


def _prepare_config_preserving_sellers(base, rows, month, year):
    """Preserva vendedores existentes exatamente como estão e adiciona apenas nomes novos, inativos."""
    cfg = copy.deepcopy(base)
    cfg["mes"], cfg["ano"] = month, year
    sellers = copy.deepcopy(cfg.get("vendedores", []))
    existing = {
        _core.normalize_text(seller.get("vendedor", "")): seller
        for seller in sellers
        if _core.normalize_text(seller.get("vendedor", ""))
    }

    grouped = {}
    for row in rows:
        key = _core.normalize_text(row.get("vendedor", ""))
        if key:
            grouped.setdefault(key, []).append(row)

    for key in sorted(grouped):
        if key in existing:
            continue

        group = grouped[key]
        sample = group[0]
        variants = {}
        for item in group:
            raw = str(item.get("vendedor", "")).strip()
            if raw:
                variants[raw] = variants.get(raw, 0) + 1
        name = max(variants, key=lambda value: (variants[value], len(value))) if variants else str(sample.get("vendedor", "")).strip()

        inferred_category = next(
            (label for label in ("Website", "ADM", "Freelance") if _core.normalize_text(label) in key),
            "Vendedor",
        )
        inferred_team = _core.normalized_team(
            None,
            {"setor": sample.get("setor", "NÃO INFORMADO"), "categoria": inferred_category},
        )

        new_seller = {
            "vendedor": name,
            "setor": sample.get("setor", "NÃO INFORMADO"),
            "equipe": inferred_team,
            "categoria": inferred_category,
            "pertence_franquia": False,
            "classificado": False,
            "ativo": False,
            "experiencia": False,
            "meta_individual": int(cfg.get("meta_padrao_vendedor", 70) or 70),
            "trabalha_sabado": True,
            "trabalha_domingo": False,
            "data_inicio": f"{year}-01-01",
            "data_desligamento": "",
            "folgas": [],
        }
        sellers.append(new_seller)
        existing[key] = new_seller

    cfg["vendedores"] = sellers
    return cfg


def _render_management_full_tables(*args, **kwargs):
    """Mantém Relatório Geral e tabela detalhada de Premiações visíveis."""
    import streamlit as st

    if st.query_params.get("team"):
        try:
            del st.query_params["team"]
        except KeyError:
            pass

    return _original_render_management(*args, **kwargs)


def _clickable_team_card(title, goal, metrics, tone="internal", performance_counts=None):
    """Mantém o card original como item direto do grid e adiciona clique sem quebrar o layout."""
    card = _original_team_card_html(title, goal, metrics, tone, performance_counts)
    return (
        f'<a href="?team={quote(str(title))}" target="_self" '
        f'style="display:contents;color:inherit;text-decoration:none" '
        f'aria-label="Abrir detalhamento de {html.escape(str(title), quote=True)}">{card}</a>'
    )


def _active_team_sellers(cfg, team_name):
    blocked = {"website", "adm", "freelance", "canal nacional"}
    return [
        seller
        for seller in cfg.get("vendedores", [])
        if seller.get("ativo", False)
        and seller.get("equipe") == team_name
        and seller.get("pertence_franquia", True)
        and _core.normalize_text(seller.get("categoria", "")) not in blocked
    ]


def _popup_css():
    return """<style>
.team-dialog-shell{display:flex;flex-direction:column;gap:10px}.team-goal-hero{background:linear-gradient(120deg,#0F172A,#172554);color:#fff;border-radius:14px;padding:15px 16px}.team-goal-hero small{display:block;font-size:.60rem;font-weight:900;letter-spacing:.08em;color:#CBD5E1}.team-goal-hero strong{display:block;font-size:2.45rem;line-height:1;margin-top:7px;font-weight:950}.team-goal-hero span{display:block;margin-top:6px;font-size:.66rem;color:#E2E8F0}.team-dialog-kpis{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:7px}.team-dialog-kpi{background:#F8FAFC;border:1px solid #E2E8F0;border-radius:10px;padding:10px;min-width:0}.team-dialog-kpi small{display:block;font-size:.53rem;color:#64748B;font-weight:900}.team-dialog-kpi strong{display:block;font-size:1.28rem;color:#0F172A;font-weight:950;margin-top:5px}.team-dialog-kpi.needed{background:#FFF7ED;border-color:#FED7AA}.team-dialog-kpi.needed strong{font-size:1.5rem;color:#9A3412}.team-capacity{background:#F8FAFC;border:1px solid #CBD5E1;border-radius:12px;padding:11px 12px}.team-capacity-title{font-size:.59rem;font-weight:950;letter-spacing:.07em;color:#475569;margin-bottom:8px}.team-capacity-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:6px}.team-capacity-grid>div{background:#fff;border:1px solid #E2E8F0;border-radius:9px;padding:8px;text-align:center}.team-capacity-grid small{display:block;font-size:.49rem;font-weight:900;color:#64748B}.team-capacity-grid strong{display:block;font-size:1.28rem;margin-top:4px;color:#0F172A}.team-capacity-note{font-size:.58rem;color:#64748B;margin-top:7px;line-height:1.35}.team-perf-popup{display:flex;align-items:center;gap:9px;flex-wrap:wrap;background:#fff;border:1px solid #E2E8F0;border-radius:10px;padding:8px 10px}.team-perf-popup small{font-size:.52rem;font-weight:900;color:#64748B}.team-perf-popup span{font-size:.70rem;font-weight:900;color:#334155}@media(max-width:700px){[data-testid="stDialog"] .team-dialog-shell{gap:6px!important}[data-testid="stDialog"] .team-goal-hero{padding:10px 11px!important}[data-testid="stDialog"] .team-goal-hero strong{font-size:1.85rem!important}[data-testid="stDialog"] .team-dialog-kpis{grid-template-columns:repeat(2,minmax(0,1fr))!important;gap:5px!important}[data-testid="stDialog"] .team-dialog-kpi{padding:7px!important}[data-testid="stDialog"] .team-dialog-kpi strong{font-size:1rem!important}[data-testid="stDialog"] .team-capacity{padding:8px!important}[data-testid="stDialog"] .team-capacity-grid>div{padding:6px 4px!important}[data-testid="stDialog"] .team-capacity-grid strong{font-size:.96rem!important}}
</style>"""


def _open_team_dialog_if_requested():
    import streamlit as st

    if st.session_state.get("gestor_autenticado", False):
        if st.query_params.get("team"):
            try:
                del st.query_params["team"]
            except KeyError:
                pass
        return

    requested = st.query_params.get("team")
    if requested not in ("Equipe Interna", "Equipe Externa") or not st.session_state.get("dashboard_autenticado", False):
        return
    try:
        base = _core.json.loads((_core.ROOT / "config.json").read_text(encoding="utf-8"))
        rows, cfg, _ = _core.load_published(base)
        summary, _, _, _ = _core.summarize(rows, cfg)
        _core.apply_team_labels(summary, cfg)
        team = _core.regular(summary)
    except Exception as exc:
        st.error(f"Não foi possível abrir o detalhamento da equipe: {exc}")
        return

    team_name = requested
    goal = int(cfg.get("meta_equipe_interna" if team_name == "Equipe Interna" else "meta_equipe_externa", 0) or 0)
    metrics = _core.team_performance_metrics(summary, team_name, goal)
    active_count = len(_active_team_sellers(cfg, team_name))
    headcount_ideal = math.ceil(goal / 40) if goal > 0 else 0
    hires_needed = max(0, headcount_ideal - active_count)
    distribution = _core.team_performance_distribution(team, team_name)
    sellers = sorted(
        [x for x in team if x.get("equipe") == team_name],
        key=lambda x: (int(x.get("vendas", 0) or 0), int(x.get("projecao", 0) or 0)),
        reverse=True,
    )

    @st.dialog(team_name, width="large")
    def _dialog():
        st.markdown(_popup_css(), unsafe_allow_html=True)
        st.markdown(
            '<div class="team-dialog-shell"><div class="team-goal-hero"><small>META DA EQUIPE</small>'
            + f'<strong>{goal}</strong><span>{html.escape(team_name)} · referência: 40 vendas/vendedor/mês</span></div><div class="team-dialog-kpis">'
            + f'<div class="team-dialog-kpi"><small>VENDAS REALIZADAS</small><strong>{metrics["sales"]}</strong></div><div class="team-dialog-kpi"><small>% DA META</small><strong>{_core.pct(metrics["attainment"])}</strong></div><div class="team-dialog-kpi"><small>FALTAM PARA META</small><strong>{metrics["missing"]}</strong></div><div class="team-dialog-kpi needed"><small>PRECISA FAZER / DIA</small><strong>{metrics["needed"]:.1f}</strong></div><div class="team-dialog-kpi"><small>PROJEÇÃO</small><strong>{metrics["projection"]}</strong></div><div class="team-dialog-kpi"><small>MÉDIA / DIA</small><strong>{metrics["average"]:.1f}</strong></div><div class="team-dialog-kpi"><small>DIAS TRABALHADOS</small><strong>{metrics["elapsed"]}</strong></div><div class="team-dialog-kpi"><small>DIAS RESTANTES</small><strong>{metrics["remaining"]}</strong></div></div><div class="team-capacity"><div class="team-capacity-title">CAPACIDADE DA EQUIPE</div><div class="team-capacity-grid"><div><small>HEADCOUNT IDEAL</small><strong>{headcount_ideal}</strong></div><div><small>ATIVOS</small><strong>{active_count}</strong></div><div><small>NECESSÁRIO CONTRATAR</small><strong>{hires_needed}</strong></div></div><div class="team-capacity-note">Para uma meta de {goal} vendas, considerando 40 vendas por vendedor/mês, a equipe precisa de aproximadamente {headcount_ideal} vendedores ativos.</div></div><div class="team-perf-popup"><small>PERFORMANCE DA EQUIPE</small><span>🔵 {distribution.get("Azul",0)}</span><span>🟢 {distribution.get("Verde",0)}</span><span>🟡 {distribution.get("Amarelo",0)}</span><span>🔴 {distribution.get("Vermelho",0)}</span></div></div>',
            unsafe_allow_html=True,
        )
        st.markdown("##### RESULTADO POR VENDEDOR")
        seller_rows = []
        for item in sellers:
            meta = int(item.get("meta_individual", 0) or 0)
            realized = int(item.get("vendas", 0) or 0)
            seller_rows.append(
                {
                    "Vendedor": item.get("vendedor", ""),
                    "Vendas": realized,
                    "Média/dia": round(float(item.get("media", 0) or 0), 2),
                    "Projeção": int(item.get("projecao", 0) or 0),
                    "% meta": round(realized / meta * 100, 1) if meta else 0.0,
                }
            )
        if seller_rows:
            st.dataframe(seller_rows, use_container_width=True, hide_index=True, height=min(330, 40 + len(seller_rows) * 35))
        else:
            st.caption("Nenhum vendedor ativo nesta equipe.")
        if st.button("FECHAR", key=f"close_team_dialog_{_core.normalize_text(team_name)}", use_container_width=True):
            try:
                del st.query_params["team"]
            except KeyError:
                pass
            st.rerun()

    _dialog()


def _install_login_viewport_fix():
    """Centraliza a tela de acesso em 100dvh e elimina overflow artificial."""
    original_render_login = _core.render_login

    def render_login_without_scroll(st, cfg):
        original_render_login(st, cfg)
        st.markdown("""<style>
html,body{height:100%!important;overflow:hidden!important}
[data-testid="stHeader"]{display:none!important}
[data-testid="stAppViewContainer"],[data-testid="stMain"],.stMain{height:100dvh!important;min-height:100dvh!important;max-height:100dvh!important;overflow:hidden!important}
[data-testid="stMainBlockContainer"],.main .block-container,.block-container{box-sizing:border-box!important;width:100%!important;max-width:100%!important;height:100dvh!important;min-height:100dvh!important;max-height:100dvh!important;margin:0!important;padding:0!important;overflow:hidden!important;display:flex!important;flex-direction:column!important;align-items:center!important;justify-content:center!important}
.results-login-wrap{box-sizing:border-box!important;width:100%!important;min-height:0!important;height:auto!important;margin:0 0 12px!important;padding:0 14px!important;display:flex!important;flex-direction:column!important;align-items:center!important;justify-content:center!important}
.results-login-logo{margin:0 auto 14px!important;max-width:min(220px,52vw)!important;max-height:82px!important}
.results-login-spacer{height:6px!important}
.st-key-results_access_form{box-sizing:border-box!important;width:min(360px,92vw)!important;margin:0 auto!important;padding:0!important}
.results-access-error{margin:7px auto 0!important}
[data-testid="stMainBlockContainer"] iframe{display:block!important;max-height:0!important;margin:0!important;padding:0!important}
@media(max-width:700px){
 [data-testid="stMainBlockContainer"],.main .block-container,.block-container{height:100dvh!important;min-height:100dvh!important;max-height:100dvh!important;padding:0!important;justify-content:center!important}
 .results-login-wrap{min-height:0!important;height:auto!important;margin:0 0 10px!important;padding:0 12px!important;justify-content:center!important}
 .results-login-logo{width:min(185px,54vw)!important;max-height:70px!important;margin-bottom:12px!important}
 .results-login-title{font-size:1.08rem!important}
 .results-login-subtitle{margin-top:4px!important}
 .st-key-results_access_form{width:min(340px,90vw)!important}
}
</style>""", unsafe_allow_html=True)

    _core.render_login = render_login_without_scroll


def _install_commercial_refresh_reference():
    """Usa no Comercial a mesma estrutura nativa [5,1] do Atualizar dados da Conciliação."""
    import streamlit as st

    current_columns = st.columns
    try:
        nonlocals = inspect.getclosurevars(current_columns).nonlocals
        original_columns = nonlocals.get("original_columns", current_columns)
    except Exception:
        original_columns = current_columns

    target = [2.15, 2.05, 1.15, 4.65]

    def commercial_columns(spec, *args, **kwargs):
        caller = inspect.currentframe().f_back
        matches = (
            isinstance(spec, (list, tuple)) and list(spec) == target
            and caller is not None and caller.f_code.co_name == "render_app"
            and str(caller.f_code.co_filename).endswith("app_core.py")
        )
        if not matches:
            return original_columns(spec, *args, **kwargs)

        # A Conciliação usa exatamente st.columns([5,1], vertical_alignment="center")
        # e um st.button nativo dentro da segunda coluna. O Comercial passa a usar
        # a mesma árvore de layout; os quatro controles originais ficam aninhados à esquerda.
        outer_kwargs = dict(kwargs)
        outer_kwargs["vertical_alignment"] = "center"
        content_col, refresh_col = original_columns([5, 1], *args, **outer_kwargs)
        with content_col:
            inner_cols = original_columns(target, *args, **kwargs)
        with refresh_col:
            if st.button("↻ Atualizar dados", key="commercial_refresh", help="Consultar novamente os resultados da planilha"):
                st.session_state["commercial_force_refresh"] = True
                st.rerun()
        return tuple(inner_cols)

    st.columns = commercial_columns


def _install_management_menu_labels():
    """Padroniza apenas a nomenclatura dos dois menus gerenciais."""
    import streamlit as st

    original_button = st.button

    def labeled_button(label, *args, **kwargs):
        key = str(kwargs.get("key") or "")
        if key == "cdt_menu_management":
            label = "Gestão Comercial"
        elif key == "cdt_menu_conc_management":
            label = "Gestão Conciliação"
        return original_button(label, *args, **kwargs)

    st.button = labeled_button


_core.merge_registry = _merge_registry_preserving_sellers
_core.prepare_config = _prepare_config_preserving_sellers

# Relatório Geral e tabela detalhada de Premiações usam a renderização nativa do núcleo.
_core.render_management = _render_management_full_tables
_core.team_performance_card_html = _clickable_team_card
_online_commercial.install(_core)

# Ajustes visuais finais após os hooks do Comercial: não mudam regras, permissões ou cálculos.
_install_login_viewport_fix()
_install_commercial_refresh_reference()
_install_management_menu_labels()

if __name__ == "__main__":
    _core.render_app()
    _open_team_dialog_if_requested()
