"""Padroniza estruturalmente a navegação da Conciliação com o Comercial."""
import inspect
import streamlit as st

# O CSS isolado não reduz a largura da coluna Streamlit. A navegação precisa
# nascer em uma coluna compacta, preservando os mesmos botões e callbacks.
_original_columns = st.columns
_original_button = st.button


def _conciliacao_columns(spec, *args, **kwargs):
    caller = inspect.currentframe().f_back
    is_conc_header = (
        isinstance(spec, (list, tuple))
        and list(spec) == [5, 1]
        and caller is not None
        and caller.f_code.co_name == "body"
        and str(caller.f_code.co_filename).endswith("conciliacao_ui.py")
    )
    if not is_conc_header:
        return _original_columns(spec, *args, **kwargs)

    # Mesma lógica visual do Comercial: grupo de navegação compacto à esquerda,
    # atualizar dados logo depois e espaço livre à direita.
    compact_kwargs = dict(kwargs)
    compact_kwargs["vertical_alignment"] = "center"
    nav, refresh, _spacer = _original_columns([2.15, 1.15, 6.70], *args, **compact_kwargs)
    return nav, refresh


def _conciliacao_button(label, *args, **kwargs):
    # A lógica interna continua usando VISÃO GERAL; muda somente o texto exibido.
    if kwargs.get("key") == "conc_nav_VISÃO GERAL" and label == "VISÃO GERAL":
        label = "GERAL"
    return _original_button(label, *args, **kwargs)


st.columns = _conciliacao_columns
st.button = _conciliacao_button

STYLE = """<style>
.st-key-dashboard_view_controls .st-key-top_nav_buttons{
  width:100%!important;
  max-width:none!important;
  margin:0!important;
}
.st-key-dashboard_view_controls .st-key-top_nav_buttons [data-testid="stHorizontalBlock"]{
  gap:.35rem!important;
}
@media(max-width:700px){
  .st-key-dashboard_view_controls > div > [data-testid="stHorizontalBlock"]{
    gap:.35rem!important;
  }
}
</style>"""
