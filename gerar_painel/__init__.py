"""Camada de calendário do gerador do painel.

Mantém integralmente as regras comerciais do gerador existente e substitui
somente a função de calendário de dias trabalháveis usada pelo aplicativo.
"""
from __future__ import annotations

import importlib.util
from datetime import date, datetime
from pathlib import Path

from calendario_feriados import operational_workdays

_LEGACY_PATH = Path(__file__).resolve().parent.parent / "gerar_painel.py"
_spec = importlib.util.spec_from_file_location("_gerar_painel_core", _LEGACY_PATH)
if _spec is None or _spec.loader is None:
    raise ImportError(f"Não foi possível carregar {_LEGACY_PATH}")
_core = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_core)


def _parse_flexible_date(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(str(value), fmt).date()
        except ValueError:
            pass
    return None


def workdays(year, month, saturday=True, sunday=False, start=None, end=None, absences=None):
    """Calendário oficial da operação: segunda a sábado, nunca domingo.

    Os parâmetros saturday/sunday permanecem apenas para compatibilidade com as
    chamadas antigas. Vendas de domingo continuam sendo contabilizadas pelas
    rotinas de vendas; o domingo apenas não entra no calendário de dias
    trabalhados, média, projeção e zeros.
    """
    parsed_absences = [day for value in (absences or []) if (day := _parse_flexible_date(value))]
    return operational_workdays(
        int(year),
        int(month),
        start=_parse_flexible_date(start),
        end=_parse_flexible_date(end),
        absences=parsed_absences,
    )


# As funções do módulo original consultam workdays pelo namespace global do
# próprio módulo. Trocamos apenas essa referência; todos os demais cálculos
# permanecem exatamente os mesmos.
_core.workdays = workdays

# Reexporta a API pública já utilizada por app.py e scripts existentes.
for _name, _value in vars(_core).items():
    if not _name.startswith("_") and _name != "workdays":
        globals()[_name] = _value

__all__ = [name for name in globals() if not name.startswith("_")]
