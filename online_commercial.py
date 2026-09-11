#!/usr/bin/env python3
"""Sincroniza o Painel Comercial com a aba VENDAS de uma planilha Google Sheets."""
from __future__ import annotations

import os
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
        raise RuntimeError(
            "A aba VENDAS não está acessível para leitura anônima. "
            "Compartilhe a planilha como 'qualquer pessoa com o link - leitor' ou publique a aba para leitura."
        )
    return data


def _signature(rows, days):
    day_set = set(days)
    return sorted(
        (
            row.get("data_venda").isoformat() if hasattr(row.get("data_venda"), "isoformat") else str(row.get("data_venda", "")),
            str(row.get("id_venda", "")),
            str(row.get("vendedor", "")),
            str(row.get("neoenergia", "")),
        )
        for row in rows
        if row.get("data_venda") in day_set
    )


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


def install(core):
    """Substitui load_published por uma versão que sincroniza a fonte online antes de renderizar."""
    original_load_published = core.load_published

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
            metadata.update(
                {
                    "arquivo": SOURCE_NAME,
                    "fonte_online": "Google Sheets · VENDAS",
                    "fonte_online_status": "ok",
                    "fonte_online_datas_inferidas": inferred_dates,
                }
            )

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
