"""Remove o aspecto de balão do identificador de acesso no cabeçalho.

Mantém o popover e suas ações, mas exibe apenas o texto clicável.
"""


def install(st):
    original_popover = st.popover

    def plain_account_popover(label, *args, **kwargs):
        text = str(label or "")
        is_account = text.startswith("◉ ") and text.endswith(" ⌄")
        if is_account:
            text = text[2:-2].strip()
            st.markdown(
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

    st.popover = plain_account_popover
