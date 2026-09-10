"""Read-only Conciliação source and business rules, independent of sales."""
from calendar import monthrange
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
import re
import unicodedata
from urllib.parse import quote
from zoneinfo import ZoneInfo

TZ = ZoneInfo("America/Recife")
SCOPE = "https://www.googleapis.com/auth/spreadsheets.readonly"


def normalized(value):
    text = " ".join(str(value or "").upper().split())
    return "".join(c for c in unicodedata.normalize("NFD", text) if not unicodedata.combining(c))


def number(value):
    if value is None or value == "":
        return Decimal(0)
    text = str(value).replace("R$", "").replace("\xa0", "").replace(" ", "")
    if "," in text:
        text = text.replace(".", "").replace(",", ".")
    result = Decimal(text)
    if not result.is_finite() or result < 0:
        raise ValueError("Valor inválido")
    return result


def timestamp(value):
    if isinstance(value, (int, float)):
        return datetime(1899, 12, 30) + timedelta(days=value)
    for fmt in ("%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M", "%d/%m/%Y", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(str(value), fmt)
        except ValueError:
            pass
    raise ValueError("Carimbo de data/hora inválido")


def parse_rows(values):
    if not values or len(values[0]) < 10 or "CARIMBO" not in normalized(values[0][0]) or "CONCILIADOR" not in normalized(values[0][9]):
        raise ValueError("Cabeçalho da aba operacional diferente do esperado")
    records, seen, names = [], set(), {}
    duplicates = 0
    for line, raw in enumerate(values[1:], 2):
        if not any(str(v).strip() for v in raw):
            continue
        row = list(raw) + [""] * max(0, 10 - len(raw))
        try:
            stamp = timestamp(row[0])
            display = " ".join(str(row[9]).split())
            key = normalized(display)
            if not key:
                raise ValueError("Conciliador ausente")
            qias = number(row[2])
            cash_invalid = False
            try:
                cash = number(row[4])
            except (ValueError, InvalidOperation):
                cash, cash_invalid = Decimal(0), True
            if qias != qias.to_integral_value():
                raise ValueError("QIAs fracionários")
            identity = (stamp, normalized(row[1]), key)
            if identity in seen:
                duplicates += 1
                continue
            seen.add(identity)
            names.setdefault(key, display)
            regime = re.sub(r"\s+", "", normalized(row[3]))
            regime = {"NR": "NR", "1A3": "1 A 3", "4A6": "4 A 6"}.get(regime, "OUTRAS")
            change = normalized(row[7]).replace("–", "-").replace("—", "-")
            change = re.sub(r"\s*-\s*", " - ", change)
            records.append({"date": stamp.date(), "key": key, "name": names[key], "qias": int(qias),
                            "cash": cash, "cash_invalid": cash_invalid, "source_line": line,
                            "regime": regime, "credit": int(change == "SIM - CREDITO"),
                            "neo": int(change == "SIM - NEOENERGIA")})
        except (ValueError, InvalidOperation) as exc:
            # Never put source values, identifiers or credentials in error messages.
            raise ValueError(f"Registro inválido na linha {line}; revise data, nome e valores.") from exc
    return records, duplicates


def parse_tiers(values):
    sections = {"monthly": [], "weekly": []}
    section = None
    columns = None
    for row in values:
        text = normalized(" ".join(str(v) for v in row))
        if "CONCILIACAO" in text and "MENSAL" in text:
            section = "monthly"
            columns = None
            continue
        if "CONCILIACAO" in text and "SEMANAL" in text:
            section = "weekly"
            columns = None
            continue
        if not row or not any(str(v).strip() for v in row):
            section = None
            columns = None
            continue
        if section:
            if "QIA" in text and "TROCA" in text:
                labels = [normalized(v) for v in row]
                columns = (next(i for i, v in enumerate(labels) if "QIA" in v),
                           next(i for i, v in enumerate(labels) if "TROCA" in v),
                           next((i for i, v in enumerate(labels) if "VALOR" in v), -1))
                if -1 in columns:
                    raise ValueError("Cabeçalho VALOR ausente na aba Config")
                continue
            try:
                if columns is None:
                    raise ValueError("Cabeçalho das faixas ausente")
                q, t, award = (number(row[i]) for i in columns)
                if q <= 0 or t <= 0 or q != int(q) or t != int(t):
                    raise ValueError("Faixa inválida")
                sections[section].append({"qias": int(q), "changes": int(t), "award": award})
            except (ValueError, InvalidOperation, IndexError) as exc:
                raise ValueError("Faixa de premiação inválida na aba Config") from exc
    if not all(sections.values()):
        raise ValueError("As seções mensal e semanal não foram encontradas na aba Config")
    for tiers in sections.values():
        tiers.sort(key=lambda tier: (tier["qias"], tier["changes"]))
    return sections


def read_source(settings, session_factory=None):
    """One read request, with read-only scope and no secret in returned data."""
    from google.oauth2.service_account import Credentials
    from google.auth.transport.requests import AuthorizedSession
    info = dict(settings["service_account"])
    # Use Google's fixed token endpoint, never a configurable credential destination.
    info["token_uri"] = "https://oauth2.googleapis.com/token"
    credentials = Credentials.from_service_account_info(info, scopes=[SCOPE])
    sheet_id = quote(str(settings["spreadsheet_id"]), safe="")
    tab = lambda name: "'" + str(name).replace("'", "''") + "'"
    ranges = [tab(settings.get("data_sheet", "2026")) + "!A:J",
              tab(settings.get("config_sheet", "Config")) + "!A:D"]
    with (session_factory or AuthorizedSession)(credentials, refresh_timeout=20) as session:
        response = session.get(f"https://sheets.googleapis.com/v4/spreadsheets/{sheet_id}/values:batchGet",
                               params={"ranges": ranges, "valueRenderOption": "UNFORMATTED_VALUE",
                                       "dateTimeRenderOption": "SERIAL_NUMBER"}, timeout=30)
        response.raise_for_status()
        values = response.json()["valueRanges"]
    records, duplicates = parse_rows(values[0].get("values", []))
    tiers = parse_tiers(values[1].get("values", []))
    return {"records": records, "tiers": tiers, "duplicates": duplicates,
            "synced_at": datetime.now(TZ)}


def weeks(year, month):
    last = monthrange(year, month)[1]
    return [(date(year, month, day), date(year, month, min(day + 6, last))) for day in range(1, last + 1, 7)]


def useful_days(start, end):
    return sum((start + timedelta(days=i)).weekday() != 6 for i in range(max(0, (end - start).days + 1)))


def aggregate(records):
    qias = sum(r["qias"] for r in records)
    cash = sum((r["cash"] for r in records), Decimal(0))
    credit, neo = sum(r["credit"] for r in records), sum(r["neo"] for r in records)
    regime_tickets = {}
    for regime in ("NR", "1 A 3", "4 A 6", "OUTRAS"):
        selected = [r for r in records if r["regime"] == regime]
        count = sum(r["qias"] for r in selected)
        regime_tickets[regime] = sum((r["cash"] for r in selected), Decimal(0)) / count if count else Decimal(0)
    return {"regime_tickets": regime_tickets, "qias": qias, "cash": cash, "credit": credit, "neo": neo, "changes": credit + neo,
            "cash_invalid": sum(bool(r.get("cash_invalid")) for r in records),
            "ticket": cash / qias if qias else Decimal(0),
            **{regime: sum(r["qias"] for r in records if r["regime"] == regime) for regime in ("NR", "1 A 3", "4 A 6", "OUTRAS")}}


def award_for(qias, changes, tiers):
    eligible = [(i + 1, tier["award"]) for i, tier in enumerate(tiers) if qias >= tier["qias"] and changes >= tier["changes"]]
    return eligible[-1] if eligible else (0, Decimal(0))


def summarize(records, tiers, year, month, today=None, registry=None):
    today = today or datetime.now(TZ).date()
    start, end = date(year, month, 1), date(year, month, monthrange(year, month)[1])
    elapsed, total = useful_days(start, min(today, end)), useful_days(start, end)
    registry = registry or {}
    names = {r["key"]: r["name"] for r in records}
    for key, flags in registry.items():
        names.setdefault(key, flags.get("name", key))
    result = []
    for key, name in names.items():
        flags = registry.get(key, {})
        if not flags.get("active", True) or not flags.get("visible", True):
            continue
        rows = [r for r in records if r["key"] == key and start <= r["date"] <= min(today, end)]
        item = {"key": key, "name": name, **aggregate(rows)}
        for metric in ("qias", "changes", "cash"):
            item[metric + "_average"] = Decimal(item[metric]) / elapsed if elapsed else Decimal(0)
            item[metric + "_projection"] = item[metric + "_average"] * total
        item["tier"], item["monthly_award"] = award_for(item["qias"], item["changes"], tiers["monthly"])
        item["projected_tier"], item["projected_award"] = award_for(item["qias_projection"], item["changes_projection"], tiers["monthly"])
        item["weekly_award"] = Decimal(0)
        for a, b in weeks(year, month):
            if b < today:
                week = aggregate([r for r in rows if a <= r["date"] <= b])
                item["weekly_award"] += award_for(week["qias"], week["changes"], tiers["weekly"])[1]
        item["commission_projection"] = item["projected_award"] + item["weekly_award"]
        next_tier = tiers["monthly"][item["tier"]] if item["tier"] < len(tiers["monthly"]) else None
        item["qias_remaining"] = max(0, next_tier["qias"] - item["qias"]) if next_tier else 0
        item["changes_remaining"] = max(0, next_tier["changes"] - item["changes"]) if next_tier else 0
        result.append(item)
    return sorted(result, key=lambda r: (-r["qias"], -r["changes"], -r["cash"], normalized(r["name"])))
