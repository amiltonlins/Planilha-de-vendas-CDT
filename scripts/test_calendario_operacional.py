#!/usr/bin/env python3
"""Testes simples do calendário operacional, sem dependências externas."""
from datetime import date

from calendario_feriados import annual_holidays, operational_workdays


def main():
    holidays = annual_holidays(2026)
    assert date(2026, 3, 6) in holidays, "Data Magna de Pernambuco ausente"
    assert date(2026, 6, 24) in holidays, "São João ausente"
    assert date(2026, 7, 16) in holidays, "Nossa Senhora do Carmo ausente"
    assert date(2026, 12, 8) in holidays, "Nossa Senhora da Conceição ausente"
    assert date(2026, 11, 20) in holidays, "Consciência Negra ausente"

    august = operational_workdays(2026, 8)
    assert len(august) == 26, f"Agosto/2026 deveria ter 26 dias trabalháveis, recebeu {len(august)}"
    assert all(day.weekday() != 6 for day in august), "Domingo entrou como dia trabalhado"
    assert date(2026, 8, 1) in august, "Sábado deve ser dia trabalhável"
    assert date(2026, 8, 2) not in august, "Domingo não deve ser dia trabalhável"

    march = operational_workdays(2026, 3)
    assert date(2026, 3, 6) not in march, "Data Magna não foi excluída"

    july = operational_workdays(2026, 7)
    assert date(2026, 7, 16) not in july, "Feriado municipal do Recife não foi excluído"

    print("Calendário operacional OK")


if __name__ == "__main__":
    main()
