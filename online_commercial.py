#!/usr/bin/env python3
"""Sincroniza o Painel Comercial com a aba VENDAS de uma planilha Google Sheets."""
from __future__ import annotations

import inspect
import os
import re
from datetime import timedelta
from urllib.request import Request, urlopen

import streamlit as st

DEFAULT_SHEET_ID = "14uhlJmDA3UeTZb7sZ3zu-Fovr8utzQbFcpU8LEbuKXE"
DEFAULT_GID = "56831808"  # aba VENDAS
SOURCE_NAME = "google_sheets_vendas.csv"


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
    """Garante a regra semanal completa, seletor e download diretamente no Comercial."""
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

    if getattr(st, "_commercial_week_dates_selector_installed", False):
        return

    original_button = st.button

    selector_css = """<style>
.st-key-dashboard_view_controls .st-key-week_nav_buttons{
  width:auto!important;max-width:100%!important;margin:2px 0 0!important;padding:0!important;overflow:visible!important;
}
.st-key-dashboard_view_controls .st-key-week_nav_buttons [data-testid="stHorizontalBlock"]{
  display:flex!important;flex-direction:row!important;flex-wrap:nowrap!important;justify-content:flex-start!important;align-items:center!important;
  width:auto!important;max-width:100%!important;gap:3px!important;overflow:visible!important;
}
.st-key-dashboard_view_controls .st-key-week_nav_buttons [data-testid="column"]{
  flex:0 0 58px!important;width:58px!important;min-width:58px!important;max-width:58px!important;margin:0!important;padding:0!important;
}
.st-key-dashboard_view_controls .st-key-week_nav_buttons .stButton,
.st-key-dashboard_view_controls .st-key-week_nav_buttons .stButton>div{
  width:58px!important;min-width:58px!important;max-width:58px!important;margin:0!important;padding:0!important;
}
.st-key-dashboard_view_controls .st-key-week_nav_buttons .stButton button{
  width:58px!important;min-width:58px!important;max-width:58px!important;height:28px!important;min-height:28px!important;max-height:28px!important;
  margin:0!important;padding:0 4px!important;border-radius:6px!important;background:#FFFFFF!important;color:#64748B!important;
  border:1px solid #D7E0E8!important;box-shadow:none!important;font-size:.62rem!important;font-weight:850!important;line-height:1!important;
  white-space:nowrap!important;overflow:visible!important;justify-content:center!important;
}
.st-key-dashboard_view_controls .st-key-week_nav_buttons .stButton button:hover{
  background:#F8FAFC!important;color:#0F172A!important;border-color:#B8C5D1!important;
}
.st-key-dashboard_view_controls .st-key-week_nav_buttons .stButton button[kind="primary"],
.st-key-dashboard_view_controls .st-key-week_nav_buttons [data-testid="stBaseButton-primary"]{
  background:#075B35!important;color:#FFFFFF!important;border-color:#075B35!important;font-weight:950!important;
}
.st-key-dashboard_view_controls .st-key-week_nav_buttons .stButton button p,
.st-key-dashboard_view_controls .st-key-week_nav_buttons .stButton button span{
  margin:0!important;padding:0!important;font:inherit!important;line-height:1!important;white-space:nowrap!important;
}
.week-period-caption{display:none!important;height:0!important;margin:0!important;padding:0!important;}
@media(max-width:700px){
  .st-key-dashboard_view_controls .st-key-week_nav_buttons{overflow-x:visible!important;}
  .st-key-dashboard_view_controls .st-key-week_nav_buttons [data-testid="stHorizontalBlock"]{gap:2px!important;flex-wrap:nowrap!important;}
  .st-key-dashboard_view_controls .st-key-week_nav_buttons [data-testid="column"]{
    flex:0 0 55px!important;width:55px!important;min-width:55px!important;max-width:55px!important;
  }
  .st-key-dashboard_view_controls .st-key-week_nav_buttons .stButton,
  .st-key-dashboard_view_controls .st-key-week_nav_buttons .stButton>div,
  .st-key-dashboard_view_controls .st-key-week_nav_buttons .stButton button{
    width:55px!important;min-width:55px!important;max-width:55px!important;
  }
  .st-key-dashboard_view_controls .st-key-week_nav_buttons .stButton button{
    height:27px!important;min-height:27px!important;max-height:27px!important;padding:0 3px!important;border-radius:5px!important;font-size:.58rem!important;
  }
}
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
                if 0 <= index < len(ranges):
                    period = ranges[index]
            except Exception:
                period = None

        button_label = f"{period[0].day:02d}–{period[1].day:02d}" if period else str(label)
        st.markdown(selector_css, unsafe_allow_html=True)
        return original_button(button_label, *args, **kwargs)

    st.button = standardized_button
    st._commercial_week_dates_selector_installed = True
    st._weekly_commercial_selector_runtime_installed = True


def _install_refresh_button():
    """Insere o botão no próprio bloco de controles, logo após 'Atualizado ...'."""
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
.st-key-dashboard_view_controls div[data-testid="column"]:nth-child(3) div[data-testid="stButton"] button,
.st-key-dashboard_view_controls div[data-testid="column"]:nth-child(3) button[data-testid^="stBaseButton"],
div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(3) .st-key-commercial_refresh button{
  background:transparent!important;
  border:none!important;
  outline:none!important;
  box-shadow:none!important;
  color:#64748B!important;
  min-height:27px!important;
  height:27px!important;
  padding:0 7px!important;
  font-size:.57rem!important;
  font-weight:800!important;
  white-space:nowrap!important;
}
.st-key-dashboard_view_controls div[data-testid="column"]:nth-child(3) div[data-testid="stButton"] button:hover,
.st-key-dashboard_view_controls div[data-testid="column"]:nth-child(3) div[data-testid="stButton"] button:focus,
.st-key-dashboard_view_controls div[data-testid="column"]:nth-child(3) div[data-testid="stButton"] button:active{
  background:transparent!important;
  border:none!important;
  outline:none!important;
  box-shadow:none!important;
  color:#075B35!important;
}
@media(max-width:700px){
 .st-key-dashboard_view_controls > div[data-testid="stHorizontalBlock"],.st-key-dashboard_view_controls > [data-testid="stVerticalBlock"] > div[data-testid="stHorizontalBlock"]{grid-template-columns:minmax(0,1fr) auto minmax(0,1fr)!important}
 .st-key-dashboard_view_controls > div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(1),.st-key-dashboard_view_controls > [data-testid="stVerticalBlock"] > div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(1){grid-column:1/-1!important;grid-row:1!important}
 .st-key-dashboard_view_controls > div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(2),.st-key-dashboard_view_controls > [data-testid="stVerticalBlock"] > div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(2){grid-column:1!important;grid-row:2!important}
 .st-key-dashboard_view_controls > div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(3),.st-key-dashboard_view_controls > [data-testid="stVerticalBlock"] > div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(3){grid-column:2!important;grid-row:2!important;display:block!important;width:auto!important;max-width:none!important}
 .st-key-dashboard_view_controls > div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(4),.st-key-dashboard_view_controls > [data-testid="stVerticalBlock"] > div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(4){grid-column:3!important;grid-row:2!important;display:block!important}
 .st-key-dashboard_view_controls > div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(5),.st-key-dashboard_view_controls > [data-testid="stVerticalBlock"] > div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(5){display:none!important}
 .st-key-dashboard_view_controls div[data-testid="column"]:nth-child(3) div[data-testid="stButton"] button{height:25px!important;min-height:25px!important;font-size:.52rem!important;padding:0 6px!important}
}
</style>""", unsafe_allow_html=True)
            if st.button("↻ Atualizar dados", key="commercial_refresh", help="Consultar novamente os resultados da planilha"):
                st.session_state["commercial_force_refresh"] = True
                st.rerun()
        return cols[0], cols[1], cols[3], cols[4]

    st.columns = commercial_columns
    st._cdt_commercial_refresh_installed = True


def install(core):
    """Sincroniza a fonte online e instala a atualização manual do Comercial."""
    original_load_published = core.load_published
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
            metadata.update({"arquivo": SOURCE_NAME, "fonte_online": "Google Sheets · VENDAS", "fonte_online_status": "ok", "fonte_online_datas_inferidas": inferred_dates})
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
