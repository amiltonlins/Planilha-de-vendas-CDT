"""Calendário operacional do Painel Comercial Afogados.

Regra: dias trabalháveis são segunda a sábado. Domingo nunca entra como dia
trabalhado. Vendas realizadas aos domingos continuam existindo normalmente;
apenas o calendário usado em média, projeção e zeros não conta o domingo.

Feriados legais nacionais, estaduais de Pernambuco e municipais do Recife são
retirados dos dias trabalháveis. Pontos facultativos não são removidos.
"""
from datetime import date, timedelta


def _easter_sunday(year: int) -> date:
    """Computus gregoriano (Meeus/Jones/Butcher)."""
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return date(year, month, day)


def holidays_brazil(year: int) -> dict[date, str]:
    holidays = {
        date(year, 1, 1): "Confraternização Universal",
        date(year, 4, 21): "Tiradentes",
        date(year, 5, 1): "Dia do Trabalho",
        date(year, 9, 7): "Independência do Brasil",
        date(year, 10, 12): "Nossa Senhora Aparecida",
        date(year, 11, 2): "Finados",
        date(year, 11, 15): "Proclamação da República",
        date(year, 11, 20): "Dia Nacional de Zumbi e da Consciência Negra",
        date(year, 12, 25): "Natal",
    }
    # Paixão de Cristo: feriado religioso observado no Recife e também listado
    # no calendário oficial federal anual. Sexta-feira anterior à Páscoa.
    holidays[_easter_sunday(year) - timedelta(days=2)] = "Paixão de Cristo"
    return holidays


def holidays_pernambuco(year: int) -> dict[date, str]:
    return {
        date(year, 3, 6): "Data Magna de Pernambuco",
        date(year, 6, 24): "São João",
    }


def holidays_recife(year: int) -> dict[date, str]:
    # Lei Municipal nº 9.777/1967: Paixão de Cristo, São João,
    # Nossa Senhora do Carmo e Nossa Senhora da Conceição.
    return {
        _easter_sunday(year) - timedelta(days=2): "Paixão de Cristo",
        date(year, 6, 24): "São João",
        date(year, 7, 16): "Nossa Senhora do Carmo",
        date(year, 12, 8): "Nossa Senhora da Conceição",
    }


def annual_holidays(year: int) -> dict[date, str]:
    result = {}
    result.update(holidays_brazil(year))
    result.update(holidays_pernambuco(year))
    result.update(holidays_recife(year))
    return result


def month_holidays(year: int, month: int) -> dict[date, str]:
    return {day: name for day, name in annual_holidays(year).items() if day.month == month}


def operational_workdays(year: int, month: int, start=None, end=None, absences=None):
    """Retorna dias de trabalho: segunda-sábado, exceto feriados e ausências.

    Domingo é sempre excluído, independentemente de qualquer configuração antiga.
    """
    first = date(year, month, 1)
    if month == 12:
        last = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        last = date(year, month + 1, 1) - timedelta(days=1)
    start = start or first
    end = end or last
    holidays = set(annual_holidays(year))
    excluded = set(absences or []) | holidays
    days = []
    current = first
    while current <= last:
        if current.weekday() != 6 and start <= current <= end and current not in excluded:
            days.append(current)
        current += timedelta(days=1)
    return days
