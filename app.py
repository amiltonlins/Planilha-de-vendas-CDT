#!/usr/bin/env python3
"""Camada mínima do app: mantém o núcleo atual e restringe o Relatório Geral à Gestão."""
import app_core as _core

_original_general_report_xlsx = _core.general_report_xlsx_bytes


def _management_general_report_xlsx(team, all_days):
    """Na Gestão, exibe a tabela completa antes de gerar o mesmo Excel já existente."""
    import streamlit as st

    columns = [
        ("equipe", "EQUIPE"),
        ("vendedor", "VENDEDOR"),
        ("vendas", "TOTAL"),
        ("projecao", "PROJEÇÃO"),
        ("media", "MÉDIA"),
        ("zeros", "ZEROS"),
        ("meta_pct", "% META"),
        ("neo", "NEO"),
        ("neo_pct_fmt", "% NEO"),
        ("base_fmt", "PREMIAÇÃO ATUAL"),
        ("proj_fmt", "PREMIAÇÃO PROJETADA"),
        ("neo_proj_fmt", "BÔNUS NEO PROJ."),
        ("adim_proj_fmt", "BÔNUS (SE) 100% ADIM"),
        ("premio_fmt", "SEMANAIS"),
        ("total_proj_fmt", "TOTAL VAR. PROJ."),
    ] + [(day.day, str(day.day)) for day in all_days]

    display = _core.general_report_display(team)
    row_color = lambda item: _core.performance(item["media"])[1]
    st.markdown(_core.table_html(display, columns, row_color, True), unsafe_allow_html=True)
    return _original_general_report_xlsx(team, all_days)


# A Gestão já possui o título e o botão de download. A tabela passa a ser renderizada
# exatamente nesse ponto, sem alterar cálculos, dados ou geração do arquivo Excel.
_core.general_report_xlsx_bytes = _management_general_report_xlsx

# A Visão Geral deixa de renderizar a tabela; todo o restante da área permanece igual.
_core.render_general_report = lambda *args, **kwargs: None


if __name__ == "__main__":
    _core.render_app()
