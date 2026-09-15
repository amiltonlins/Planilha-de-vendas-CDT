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
AUTO_REFRESH_SECONDS = 60


def _download_csv(sheet_id: str, gid: str) -> bytes:
    """Baixa sempre uma cópia nova da aba VENDAS, evitando cache local e HTTP."""
    cache_buster = str(time.time_ns())
    url = (
        f"https://docs.google.com/spreadsheets/d/{sheet_id}/export"
        f"?format=csv&gid={gid}&_={cache_buster}"
    )
    request = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Cache-Control": "no-cache, no-store, max-age=0",
            "Pragma": "no-cache",
        },
    )
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


def _install_daily_current_date(core):
    """Faz o Diário usar sempre a data atual de Recife, sem o corte de dia_referencia."""
    if getattr(core, "_daily_current_date_runtime_installed", False):
        return
    original_daily_ranking_rows = core.daily_ranking_rows

    def daily_ranking_rows_current(team, rows, cfg, reference_day=None):
        current_day = reference_day or core.datetime.now(core.RECIFE_TZ).date()
        effective_cfg = dict(cfg)
        if current_day.year == int(cfg["ano"]) and current_day.month == int(cfg["mes"]):
            effective_cfg["dia_referencia"] = current_day.day
        return original_daily_ranking_rows(team, rows, effective_cfg, current_day)

    core.daily_ranking_rows = daily_ranking_rows_current
    core._daily_current_date_runtime_installed = True


def _install_weekly_commercial_behavior(core):
    """Mantém semana completa, seletor por datas e download semanal corrigido."""
    if not getattr(core, "_weekly_complete_runtime_installed", False):
        original_summarize = core.summarize

        def summarize_with_complete_weeks(rows, cfg):
            result, calendar_days, elapsed_days, official = original_summarize(rows, cfg)
            full_weeks = _full_week_ranges(core, cfg["ano"], cfg["mes"])
            awards = list(cfg.get("premiacao_semanal", []) or [])

            def weekly_award(qty):
                eligible = [float(item.get("premio", 0) or 0) for item in awards if qty >= int(item.get("vendas", 0) or 0)]
                return eligible[-1] if eligible else 0

            rows_by_seller = {}
            for row in rows:
                key = core.normalize_text(row.get("vendedor", ""))
                if key:
                    rows_by_seller.setdefault(key, []).append(row)

            for item in result:
                seller_rows = rows_by_seller.get(core.normalize_text(item.get("vendedor", "")), [])
                weekly_sales = [sum(start <= row.get("data_venda") <= end for row in seller_rows) for start, end in full_weeks]
                item["semanas"] = weekly_sales
                item["premios"] = [weekly_award(qty) if item.get("elegivel_individual", False) else 0 for qty in weekly_sales]
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
    selector_css = """<style>.week-period-caption{display:none!important;height:0!important;margin:0!important;padding:0!important}</style>"""
    def standardized_button(label, *args, **kwargs):
        key = str(kwargs.get("key") or "")
        match = re.fullmatch(r"week_btn_(\d+)", key)
        if not match:
            return original_button(label, *args, **kwargs)
        index = int(match.group(1)); caller = inspect.currentframe().f_back; cfg = caller.f_locals.get("cfg") if caller is not None else None; period = None
        if isinstance(cfg, dict):
            try:
                ranges = core.month_weeks(int(cfg["ano"]), int(cfg["mes"])); period = ranges[index] if 0 <= index < len(ranges) else None
            except Exception: period = None
        button_label = f"{period[0].day:02d}–{period[1].day:02d}" if period else str(label)
        st.markdown(selector_css, unsafe_allow_html=True)
        return original_button(button_label, *args, **kwargs)
    st.button = standardized_button
    st._commercial_week_dates_selector_installed = True
    st._commercial_week_dates_selector_version = SELECTOR_VERSION
    st._weekly_commercial_selector_runtime_installed = True


def _install_refresh_button():
    if getattr(st, "_cdt_commercial_refresh_installed", False): return
    original_columns = st.columns; target = [2.15, 2.05, 1.15, 4.65]
    def commercial_columns(spec, *args, **kwargs):
        caller = inspect.currentframe().f_back
        matches = isinstance(spec, (list, tuple)) and list(spec) == target and caller is not None and caller.f_code.co_name == "render_app" and str(caller.f_code.co_filename).endswith("app_core.py")
        if not matches: return original_columns(spec, *args, **kwargs)
        cols = original_columns([2.15, 2.05, 1.25, 1.15, 3.40], *args, **kwargs)
        with cols[2]:
            if st.button("↻ Atualizar dados", key="commercial_refresh", help="Consultar novamente os resultados da planilha"):
                st.session_state["commercial_force_refresh"] = True; st.rerun()
        return cols[0], cols[1], cols[3], cols[4]
    st.columns = commercial_columns; st._cdt_commercial_refresh_installed = True


def _install_auto_refresh():
    """Atualiza a página automaticamente para buscar novas vendas sem ação manual."""
    if not st.session_state.get("dashboard_autenticado", False):
        return
    try:
        import streamlit.components.v1 as components
        components.html(
            f"""<script>
            setTimeout(function(){{
              try {{ window.parent.location.reload(); }} catch(e) {{ window.location.reload(); }}
            }}, {AUTO_REFRESH_SECONDS * 1000});
            </script>""",
            height=0,
        )
    except Exception:
        pass


def _normalize_access_code(value: str) -> str:
    return str(value or "").strip().casefold()


def _install_access_code_login(core):
    if getattr(core, "_results_access_code_login_installed", False): return
    original_validate_token = core.validate_dashboard_token
    def validate_dashboard_token(st_module, cfg, token):
        current = original_validate_token(st_module, cfg, token)
        if current: return current
        key = core.auth_signing_key(st_module)
        if not key or not token: return None
        try:
            padded = str(token) + "=" * ((4 - len(str(token)) % 4) % 4); raw = base64.urlsafe_b64decode(padded.encode("ascii")).decode("utf-8"); user, expiry_text, sig = raw.rsplit("|", 2)
            if user != ACCESS_SESSION_USER or int(expiry_text) < int(time.time()): return None
            payload = f"{user}|{expiry_text}"; expected = hmac.new(key.encode("utf-8"), payload.encode("utf-8"), "sha256").hexdigest()
            return user if hmac.compare_digest(sig, expected) else None
        except Exception: return None
    core.validate_dashboard_token = validate_dashboard_token
    core._results_access_code_login_installed = True


def install(core):
    """Sincroniza a fonte online e instala atualização automática do Comercial."""
    original_load_published = core.load_published
    _install_access_code_login(core)
    _install_daily_current_date(core)
    _install_weekly_commercial_behavior(core)
    _install_refresh_button()

    def load_published_online(base):
        rows, cfg, metadata = original_load_published(base); metadata = dict(metadata or {})
        force_refresh = bool(st.session_state.pop("commercial_force_refresh", False))
        try:
            incoming, inferred_dates = _prepare_online_rows(core, base)
            imported_days = sorted({row["data_venda"] for row in incoming}); before = _signature(rows, imported_days); merged, imported_days = core.merge_daily_history(rows, incoming); after = _signature(merged, imported_days)
            if imported_days:
                latest = max(imported_days); cfg = core.prepare_config(core.merge_registry(base, cfg), merged, latest.month, latest.year)
            now = core.datetime.now(core.RECIFE_TZ)
            metadata.update({"arquivo": SOURCE_NAME,"fonte_online":"Google Sheets · VENDAS","fonte_online_status":"ok","fonte_online_datas_inferidas":inferred_dates})
            if before != after or force_refresh:
                history = metadata.get("historico_importacoes", []); core.save_published(merged, cfg, SOURCE_NAME, history, updated_at=now); metadata["atualizado_em"] = now.isoformat(timespec="seconds")
            return merged, cfg, metadata
        except Exception as exc:
            metadata["fonte_online"]="Google Sheets · VENDAS"; metadata["fonte_online_status"]="fallback"; metadata["fonte_online_erro"]=str(exc)
            if force_refresh: st.warning("Não foi possível atualizar. Última leitura válida mantida, quando disponível.")
            return rows, cfg, metadata

    core.load_published = load_published_online
    _install_auto_refresh()
