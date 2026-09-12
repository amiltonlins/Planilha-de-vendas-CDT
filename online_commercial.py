#!/usr/bin/env python3
"""Sincroniza o Painel Comercial com a aba VENDAS e instala ajustes de acesso/UI."""
from __future__ import annotations

import base64
import hmac
import inspect
import os
import re
import time
from datetime import timedelta
from urllib.request import Request, urlopen

import streamlit as st

DEFAULT_SHEET_ID = "14uhlJmDA3UeTZb7sZ3zu-Fovr8utzQbFcpU8LEbuKXE"
DEFAULT_GID = "56831808"  # aba VENDAS
SOURCE_NAME = "google_sheets_vendas.csv"
SELECTOR_VERSION = "2026-09-12-commercial-dates-v4"
ACCESS_CODE = os.environ.get("PAINEL_ACCESS_CODE", "resultados")
ACCESS_SESSION_USER = "Painel de Resultados"
ACCESS_LOGO_URL = "https://share.google/eNhOIxBCCPNSKbiUE"


@st.cache_data(ttl=120, show_spinner=False)
def _download_csv(sheet_id: str, gid: str) -> bytes:
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
    request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(request, timeout=20) as response:
        data = response.read()
        content_type = str(response.headers.get("Content-Type", "")).lower()
    sample = data[:800].lower()
    if not data:
        raise RuntimeError("A planilha online retornou um arquivo vazio.")
    if "text/html" in content_type or b"<html" in sample or b"accounts.google.com" in sample:
        raise RuntimeError("A aba VENDAS não está acessível para leitura anônima.")
    return data


def _signature(rows, days):
    day_set = set(days)
    return sorted((
        row.get("data_venda").isoformat() if hasattr(row.get("data_venda"), "isoformat") else str(row.get("data_venda", "")),
        str(row.get("id_venda", "")), str(row.get("vendedor", "")), str(row.get("neoenergia", "")),
    ) for row in rows if row.get("data_venda") in day_set)


def _prepare_online_rows(core, base):
    sheet_id = os.environ.get("PAINEL_GOOGLE_SHEET_ID", DEFAULT_SHEET_ID).strip()
    gid = os.environ.get("PAINEL_GOOGLE_SHEET_GID", DEFAULT_GID).strip()
    raw_rows = core.rows_from_csv(_download_csv(sheet_id, gid))
    if not raw_rows:
        raise RuntimeError("A aba VENDAS não possui registros para sincronizar.")
    mapping = core.detect_columns(raw_rows[0].keys())
    date_column = mapping.get("data_venda")
    today = core.datetime.now(core.RECIFE_TZ).date().isoformat()
    inferred_dates = 0
    if date_column:
        for row in raw_rows:
            raw_value = str(row.get(date_column, "") or "").strip()
            if not raw_value or ("#" in raw_value and raw_value.replace("#", "").strip() == ""):
                row[date_column] = today
                inferred_dates += 1
    incoming, _ = core.canonicalize(raw_rows, base)
    return incoming, inferred_dates


def _full_week_ranges(core, year, month):
    """Converte os blocos da competência para semanas completas (segunda a domingo)."""
    ranges = []
    for start, _end in core.month_weeks(int(year), int(month)):
        monday = start - timedelta(days=start.weekday())
        ranges.append((monday, monday + timedelta(days=6)))
    return ranges


def _install_weekly_commercial_behavior(core):
    """Mantém semana completa, seletor por datas e download semanal corrigido."""
    if not getattr(core, "_weekly_complete_runtime_installed", False):
        original_summarize = core.summarize

        def summarize_with_complete_weeks(rows, cfg):
            result, calendar_days, elapsed_days, official = original_summarize(rows, cfg)
            full_weeks = _full_week_ranges(core, cfg["ano"], cfg["mes"])
            awards = list(cfg.get("premiacao_semanal", []) or [])

            def weekly_award(qty):
                eligible = [
                    float(item.get("premio", 0) or 0)
                    for item in awards
                    if qty >= int(item.get("vendas", 0) or 0)
                ]
                return eligible[-1] if eligible else 0

            rows_by_seller = {}
            for row in rows:
                key = core.normalize_text(row.get("vendedor", ""))
                if key:
                    rows_by_seller.setdefault(key, []).append(row)

            for item in result:
                seller_rows = rows_by_seller.get(core.normalize_text(item.get("vendedor", "")), [])
                weekly_sales = [
                    sum(start <= row.get("data_venda") <= end for row in seller_rows)
                    for start, end in full_weeks
                ]
                item["semanas"] = weekly_sales
                item["premios"] = [
                    weekly_award(qty) if item.get("elegivel_individual", False) else 0
                    for qty in weekly_sales
                ]
            return result, calendar_days, elapsed_days, official

        core.summarize = summarize_with_complete_weeks
        core._weekly_complete_runtime_installed = True

    if not getattr(core, "_weekly_download_complete_period_installed", False):
        original_weekly_png = core.weekly_prize_ranking_png

        def weekly_prize_ranking_png_with_complete_period(team, week_index, cfg):
            original_month_weeks = core.month_weeks

            def complete_month_weeks(year, month):
                ranges = []
                for start, _end in original_month_weeks(int(year), int(month)):
                    monday = start - timedelta(days=start.weekday())
                    ranges.append((monday, monday + timedelta(days=6)))
                return ranges

            core.month_weeks = complete_month_weeks
            try:
                return original_weekly_png(team, week_index, cfg)
            finally:
                core.month_weeks = original_month_weeks

        core.weekly_prize_ranking_png = weekly_prize_ranking_png_with_complete_period
        core._weekly_download_complete_period_installed = True

    if getattr(st, "_commercial_week_dates_selector_version", None) == SELECTOR_VERSION:
        return

    original_button = st.button
    selector_css = """<style>
.st-key-dashboard_view_controls .st-key-week_nav_buttons{width:auto!important;max-width:100%!important;margin:2px 0 0!important;padding:0!important;overflow:visible!important}
.st-key-dashboard_view_controls .st-key-week_nav_buttons [data-testid="stHorizontalBlock"]{display:flex!important;flex-direction:row!important;flex-wrap:nowrap!important;justify-content:flex-start!important;align-items:center!important;width:auto!important;max-width:100%!important;gap:3px!important;overflow:visible!important}
.st-key-dashboard_view_controls .st-key-week_nav_buttons [data-testid="column"]{flex:0 0 58px!important;width:58px!important;min-width:58px!important;max-width:58px!important;margin:0!important;padding:0!important}
.st-key-dashboard_view_controls .st-key-week_nav_buttons .stButton,.st-key-dashboard_view_controls .st-key-week_nav_buttons .stButton>div{width:58px!important;min-width:58px!important;max-width:58px!important;margin:0!important;padding:0!important}
.st-key-dashboard_view_controls .st-key-week_nav_buttons .stButton button{width:58px!important;min-width:58px!important;max-width:58px!important;height:28px!important;min-height:28px!important;max-height:28px!important;margin:0!important;padding:0 4px!important;border-radius:6px!important;background:#fff!important;color:#64748B!important;border:1px solid #D7E0E8!important;box-shadow:none!important;font-size:.62rem!important;font-weight:850!important;line-height:1!important;white-space:nowrap!important;justify-content:center!important}
.st-key-dashboard_view_controls .st-key-week_nav_buttons .stButton button:hover{background:#F8FAFC!important;color:#0F172A!important;border-color:#B8C5D1!important}
.st-key-dashboard_view_controls .st-key-week_nav_buttons .stButton button[kind="primary"],.st-key-dashboard_view_controls .st-key-week_nav_buttons [data-testid="stBaseButton-primary"]{background:#075B35!important;color:#fff!important;border-color:#075B35!important;font-weight:950!important}
.week-period-caption{display:none!important;height:0!important;margin:0!important;padding:0!important}
@media(max-width:700px){.st-key-dashboard_view_controls .st-key-week_nav_buttons [data-testid="stHorizontalBlock"]{gap:2px!important}.st-key-dashboard_view_controls .st-key-week_nav_buttons [data-testid="column"],.st-key-dashboard_view_controls .st-key-week_nav_buttons .stButton,.st-key-dashboard_view_controls .st-key-week_nav_buttons .stButton>div,.st-key-dashboard_view_controls .st-key-week_nav_buttons .stButton button{width:55px!important;min-width:55px!important;max-width:55px!important;flex-basis:55px!important}.st-key-dashboard_view_controls .st-key-week_nav_buttons .stButton button{height:27px!important;min-height:27px!important;max-height:27px!important;padding:0 3px!important;border-radius:5px!important;font-size:.58rem!important}}
</style>"""

    def standardized_button(label, *args, **kwargs):
        key = str(kwargs.get("key") or "")
        match = re.fullmatch(r"week_btn_(\d+)", key)
        if not match:
            return original_button(label, *args, **kwargs)
        index = int(match.group(1))
        caller = inspect.currentframe().f_back
        cfg = caller.f_locals.get("cfg") if caller is not None else None
        period = None
        if isinstance(cfg, dict):
            try:
                ranges = core.month_weeks(int(cfg["ano"]), int(cfg["mes"]))
                period = ranges[index] if 0 <= index < len(ranges) else None
            except Exception:
                period = None
        button_label = f"{period[0].day:02d}–{period[1].day:02d}" if period else str(label)
        st.markdown(selector_css, unsafe_allow_html=True)
        return original_button(button_label, *args, **kwargs)

    st.button = standardized_button
    st._commercial_week_dates_selector_installed = True
    st._commercial_week_dates_selector_version = SELECTOR_VERSION
    st._weekly_commercial_selector_runtime_installed = True


def _install_refresh_button():
    """Insere o botão de atualização manual no bloco de controles do Comercial."""
    if getattr(st, "_cdt_commercial_refresh_installed", False):
        return
    original_columns = st.columns
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
        cols = original_columns([2.15, 2.05, 1.25, 1.15, 3.40], *args, **kwargs)
        with cols[2]:
            st.markdown("""<style>
.st-key-dashboard_view_controls div[data-testid="column"]:nth-child(3) div[data-testid="stButton"] button,.st-key-dashboard_view_controls div[data-testid="column"]:nth-child(3) button[data-testid^="stBaseButton"]{background:transparent!important;border:none!important;outline:none!important;box-shadow:none!important;color:#64748B!important;min-height:27px!important;height:27px!important;padding:0 7px!important;font-size:.57rem!important;font-weight:800!important;white-space:nowrap!important}
.st-key-dashboard_view_controls div[data-testid="column"]:nth-child(3) div[data-testid="stButton"] button:hover,.st-key-dashboard_view_controls div[data-testid="column"]:nth-child(3) div[data-testid="stButton"] button:focus,.st-key-dashboard_view_controls div[data-testid="column"]:nth-child(3) div[data-testid="stButton"] button:active{background:transparent!important;border:none!important;outline:none!important;box-shadow:none!important;color:#075B35!important}
</style>""", unsafe_allow_html=True)
            if st.button("↻ Atualizar dados", key="commercial_refresh", help="Consultar novamente os resultados da planilha"):
                st.session_state["commercial_force_refresh"] = True
                st.rerun()
        return cols[0], cols[1], cols[3], cols[4]

    st.columns = commercial_columns
    st._cdt_commercial_refresh_installed = True


def _normalize_access_code(value: str) -> str:
    """Remove apenas espaços externos e ignora caixa; não corrige conteúdo interno."""
    return str(value or "").strip().casefold()


def _install_access_code_login(core):
    """Substitui o acesso nominal por um único código e preserva Gestão separada."""
    if getattr(core, "_results_access_code_login_installed", False):
        return

    original_validate_token = core.validate_dashboard_token

    def validate_dashboard_token(st_module, cfg, token):
        # Mantém compatibilidade com tokens válidos já emitidos anteriormente.
        current = original_validate_token(st_module, cfg, token)
        if current:
            return current
        key = core.auth_signing_key(st_module)
        if not key or not token:
            return None
        try:
            padded = str(token) + "=" * ((4 - len(str(token)) % 4) % 4)
            raw = base64.urlsafe_b64decode(padded.encode("ascii")).decode("utf-8")
            user, expiry_text, sig = raw.rsplit("|", 2)
            if user != ACCESS_SESSION_USER or int(expiry_text) < int(time.time()):
                return None
            payload = f"{user}|{expiry_text}"
            expected = hmac.new(key.encode("utf-8"), payload.encode("utf-8"), "sha256").hexdigest()
            return user if hmac.compare_digest(sig, expected) else None
        except Exception:
            return None

    def render_login(st_module, cfg):
        del cfg  # o acesso ao painel não depende mais de nomes cadastrados
        busy = bool(st_module.session_state.get("results_access_busy", False))
        error = st_module.session_state.pop("results_access_error", "")
        st_module.markdown(
            f"""<style>
[data-testid="stAppViewContainer"]{{background:#F8FAFC}}
.results-login-wrap{{min-height:78vh;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:22px 14px 12px}}
.results-login-logo{{display:block;width:min(220px,52vw);max-height:92px;object-fit:contain;margin:0 auto 18px}}
.results-login-title{{font-size:1.28rem;font-weight:950;letter-spacing:.025em;color:#0F172A;line-height:1.1}}
.results-login-subtitle{{margin-top:5px;font-size:.78rem;font-weight:650;color:#64748B}}
.results-login-spacer{{height:9px}}
.st-key-results_access_form{{width:min(360px,92vw)!important;margin:0 auto!important}}
.st-key-results_access_form [data-testid="stForm"]{{border:0!important;background:transparent!important;padding:0!important}}
.st-key-results_access_form label p{{font-size:.70rem!important;font-weight:850!important;color:#334155!important}}
.st-key-results_access_form input{{height:43px!important;border-radius:9px!important;border:1px solid #CBD5E1!important;background:#FFFFFF!important;text-align:center!important;font-size:.95rem!important;box-shadow:none!important}}
.st-key-results_access_form input:focus{{border-color:#075B35!important;box-shadow:0 0 0 2px rgba(7,91,53,.10)!important}}
.st-key-results_access_form button{{height:41px!important;border-radius:9px!important;background:#075B35!important;color:#fff!important;border:1px solid #075B35!important;font-size:.74rem!important;font-weight:950!important;letter-spacing:.04em!important}}
.results-access-error{{width:min(360px,92vw);margin:7px auto 0;text-align:center;color:#B91C1C;font-size:.69rem;font-weight:800}}
@media(max-width:700px){{.results-login-wrap{{min-height:66vh;padding-top:8vh;justify-content:flex-start}}.results-login-logo{{width:min(190px,55vw);max-height:80px;margin-bottom:15px}}.results-login-title{{font-size:1.12rem}}.st-key-results_access_form{{width:min(340px,92vw)!important}}}}
</style>
<div class="results-login-wrap">
  <img class="results-login-logo" src="{ACCESS_LOGO_URL}" alt="Cartão de TODOS">
  <div class="results-login-title">PAINEL DE RESULTADOS</div>
  <div class="results-login-subtitle">Recife Afogados</div>
  <div class="results-login-spacer"></div>
</div>""",
            unsafe_allow_html=True,
        )
        with st_module.container(key="results_access_form"):
            with st_module.form("dashboard_login_code", clear_on_submit=False, enter_to_submit=True):
                code = st_module.text_input(
                    "Código de acesso",
                    type="password",
                    key="results_access_code",
                    autocomplete="off",
                    placeholder="",
                    disabled=busy,
                )
                submitted = st_module.form_submit_button("ACESSAR", use_container_width=True, disabled=busy)

        if error:
            st_module.markdown(f'<div class="results-access-error">{error}</div>', unsafe_allow_html=True)

        # Foco automático no único campo. O script é isolado e não contém o código válido.
        try:
            import streamlit.components.v1 as components
            components.html(
                """<script>
                setTimeout(function(){
                  try{
                    const p=window.parent.document;
                    const input=p.querySelector('[data-testid="stTextInput"] input');
                    if(input && !input.disabled){ input.focus(); }
                  }catch(e){}
                },120);
                </script>""",
                height=0,
            )
        except Exception:
            pass

        if not submitted:
            return
        if st_module.session_state.get("results_access_busy", False):
            return
        st_module.session_state["results_access_busy"] = True
        normalized = _normalize_access_code(code)
        expected = _normalize_access_code(ACCESS_CODE)
        if not normalized:
            st_module.session_state["results_access_busy"] = False
            st_module.session_state["results_access_error"] = "Informe o código de acesso."
            st_module.rerun()
        if not hmac.compare_digest(normalized, expected):
            st_module.session_state["results_access_busy"] = False
            st_module.session_state["results_access_error"] = "Código de acesso inválido."
            st_module.session_state["results_access_code"] = ""
            st_module.rerun()

        st_module.session_state["dashboard_autenticado"] = True
        st_module.session_state["dashboard_usuario"] = ACCESS_SESSION_USER
        st_module.session_state["results_access_busy"] = False
        token = core.issue_dashboard_token(st_module, ACCESS_SESSION_USER)
        if token:
            st_module.session_state["dashboard_auth_token"] = token
            st_module.query_params["auth"] = token
        st_module.rerun()

    core.validate_dashboard_token = validate_dashboard_token
    core.render_login = render_login
    core._results_access_code_login_installed = True


def install(core):
    """Sincroniza a fonte online e instala acesso, seletor e atualização manual."""
    original_load_published = core.load_published
    _install_access_code_login(core)
    _install_weekly_commercial_behavior(core)
    _install_refresh_button()

    def load_published_online(base):
        rows, cfg, metadata = original_load_published(base)
        metadata = dict(metadata or {})
        force_refresh = bool(st.session_state.pop("commercial_force_refresh", False))
        if force_refresh:
            _download_csv.clear()
        try:
            incoming, inferred_dates = _prepare_online_rows(core, base)
            imported_days = sorted({row["data_venda"] for row in incoming})
            before = _signature(rows, imported_days)
            merged, imported_days = core.merge_daily_history(rows, incoming)
            after = _signature(merged, imported_days)
            if imported_days:
                latest = max(imported_days)
                cfg = core.prepare_config(core.merge_registry(base, cfg), merged, latest.month, latest.year)
            now = core.datetime.now(core.RECIFE_TZ)
            metadata.update({
                "arquivo": SOURCE_NAME,
                "fonte_online": "Google Sheets · VENDAS",
                "fonte_online_status": "ok",
                "fonte_online_datas_inferidas": inferred_dates,
            })
            if before != after or force_refresh:
                history = metadata.get("historico_importacoes", [])
                core.save_published(merged, cfg, SOURCE_NAME, history, updated_at=now)
                metadata["atualizado_em"] = now.isoformat(timespec="seconds")
            return merged, cfg, metadata
        except Exception as exc:
            metadata["fonte_online"] = "Google Sheets · VENDAS"
            metadata["fonte_online_status"] = "fallback"
            metadata["fonte_online_erro"] = str(exc)
            if force_refresh:
                st.warning("Não foi possível atualizar. Última leitura válida mantida, quando disponível.")
            return rows, cfg, metadata

    core.load_published = load_published_online
