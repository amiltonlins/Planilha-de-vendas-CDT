"""Ajustes leves de interface aplicados pelo bootstrap do app.py."""


def install(st=None):
    # Compatibilidade com o bootstrap atual do app.py, que chama install()
    # sem passar o módulo Streamlit explicitamente.
    if st is None:
        import streamlit as st

    import inspect

    # Mantém o dia de referência do Comercial alinhado automaticamente à data
    # atual quando o painel está exibindo a competência corrente. Sem isso, uma
    # referência persistida (ex.: dia 12) faz a Visão Geral ignorar vendas já
    # sincronizadas de dias posteriores (ex.: dia 14).
    try:
        import app_core as core

        current_summarize = core.summarize

        def summarize_with_live_reference(rows, cfg):
            live_cfg = dict(cfg or {})
            now = core.datetime.now(core.RECIFE_TZ).date()
            try:
                if int(live_cfg.get("ano", 0) or 0) == now.year and int(live_cfg.get("mes", 0) or 0) == now.month:
                    live_cfg["dia_referencia"] = now.day
            except Exception:
                pass
            return current_summarize(rows, live_cfg)

        core.summarize = summarize_with_live_reference
    except Exception:
        pass

    # O online_commercial instala core.load_published antes deste módulo. A função
    # instalada consulta _prepare_online_rows em tempo de execução, então podemos
    # substituir somente a leitura da planilha sem alterar o restante do painel.
    # Isso evita respostas antigas do cache do Streamlit/Google no Comercial.
    try:
        import os
        import time
        from urllib.request import Request, urlopen
        import online_commercial as commercial

        def prepare_online_rows_fresh(core, base):
            sheet_id = os.environ.get("PAINEL_GOOGLE_SHEET_ID", commercial.DEFAULT_SHEET_ID).strip()
            gid = os.environ.get("PAINEL_GOOGLE_SHEET_GID", commercial.DEFAULT_GID).strip()
            cache_buster = time.time_ns()
            url = (
                f"https://docs.google.com/spreadsheets/d/{sheet_id}/export"
                f"?format=csv&gid={gid}&_refresh={cache_buster}"
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

            raw_rows = core.rows_from_csv(data)
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

        commercial._prepare_online_rows = prepare_online_rows_fresh
    except Exception:
        # O ajuste visual continua funcionando mesmo se o módulo comercial não
        # estiver disponível em algum ambiente de manutenção/teste.
        pass

    original_popover = st.popover
    original_markdown = st.markdown

    def plain_account_popover(label, *args, **kwargs):
        text = str(label or "")
        is_account = text.startswith("◉ ") and text.endswith(" ⌄")
        if is_account:
            text = text[2:-2].strip()
            original_markdown(
                """<style>
.st-key-cdt_top_header [data-testid="stPopover"]>button{
  width:auto!important;min-width:0!important;height:auto!important;min-height:0!important;
  padding:0!important;margin:0!important;border:0!important;border-radius:0!important;
  background:transparent!important;box-shadow:none!important;color:#E2E8F0!important;
  font-size:.74rem!important;font-weight:800!important;line-height:1.2!important;
}
.st-key-cdt_top_header [data-testid="stPopover"]>button:hover,
.st-key-cdt_top_header [data-testid="stPopover"]>button:focus,
.st-key-cdt_top_header [data-testid="stPopover"]>button:active{
  background:transparent!important;border:0!important;box-shadow:none!important;
}
.st-key-cdt_top_header [data-testid="stPopover"]>button svg{display:none!important}
@media(max-width:560px){
  .st-key-cdt_top_header [data-testid="stPopover"]>button{font-size:.58rem!important}
}
</style>""",
                unsafe_allow_html=True,
            )
        return original_popover(text, *args, **kwargs)

    def markdown_with_overview_download(body, *args, **kwargs):
        result = original_markdown(body, *args, **kwargs)
        try:
            caller = inspect.currentframe().f_back
            is_overview_ranking = (
                caller is not None
                and caller.f_code.co_name == "render_app"
                and str(caller.f_code.co_filename).endswith("app_core.py")
                and caller.f_locals.get("area") == "VISÃO GERAL"
                and isinstance(body, str)
                and body.startswith('<div class="rank-card">')
            )
            if is_overview_ranking:
                from commercial_overview_export import overview_ranking_png

                ranking = list(caller.f_locals.get("ranking") or [])
                cfg = caller.f_locals.get("cfg") or {}
                team_filter = caller.f_locals.get("team_filter") or "TODAS AS EQUIPES"
                if ranking:
                    safe_filter = "geral" if team_filter == "TODAS AS EQUIPES" else str(team_filter).lower().replace(" ", "-")
                    st.download_button(
                        "BAIXAR RANKING GERAL",
                        data=overview_ranking_png(ranking, cfg, team_filter),
                        file_name=f"ranking-visao-geral-{safe_filter}-{int(cfg.get('ano', 0))}-{int(cfg.get('mes', 0)):02d}.png",
                        mime="image/png",
                        key="download_overview_ranking_png",
                        use_container_width=True,
                    )
        except Exception as exc:
            # Falha no exportador não deve interromper o painel principal.
            try:
                st.caption(f"Não foi possível preparar o download da Visão Geral: {exc}")
            except Exception:
                pass
        return result

    st.popover = plain_account_popover
    st.markdown = markdown_with_overview_download
