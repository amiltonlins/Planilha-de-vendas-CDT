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

    # A leitura online do Comercial permanece sob responsabilidade de
    # online_commercial.py, que já possui cache de dados e atualização manual.
    # Não substituir _prepare_online_rows aqui evita baixar e reprocessar a
    # planilha do Google Sheets em cada rerun do Streamlit.

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
