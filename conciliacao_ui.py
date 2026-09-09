"""Conciliação screens. Google Sheets is only read; no credential is exported."""
import html
import io
import threading
import time
from calendar import monthrange
from datetime import date, datetime
from decimal import Decimal

from conciliacao import TZ, aggregate, award_for, normalized, read_source, summarize, useful_days, weeks


def money(value):
    return "R$ " + f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


class SourceCache:
    """Keep last complete validated read across sessions while this process lives."""
    def __init__(self):
        self.lock = threading.Lock()
        self.value = None
        self.attempted = None
        self.stale = False

    def get(self, settings, ttl, force=False, reader=read_source):
        with self.lock:
            now = time.monotonic()
            if force or self.attempted is None or now - self.attempted >= ttl:
                self.attempted = now
                try:
                    value = reader(settings)
                except Exception:
                    self.stale = True
                else:
                    self.value, self.stale = value, False
            return self.value, self.stale


def ranking_png(rows, title, period, synced_at):
    from PIL import Image, ImageDraw
    from app_core import _daily_font, _draw_daily_brand, _fit_image_text
    image = Image.new("RGB", (1080, max(430, 235 + len(rows) * 125)), "#f1f5f9")
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((20, 20, 1060, 165), radius=20, fill="#064e3b")
    _draw_daily_brand(draw, 45, 32)
    draw.text((45, 81), title, font=_daily_font(30, True), fill="white")
    draw.text((45, 124), period, font=_daily_font(22), fill="white")
    for i, row in enumerate(rows):
        y = 182 + i * 125
        draw.rounded_rectangle((20, y, 1060, y + 113), radius=18, fill="#ffffff")
        draw.text((42, y + 13), f"{i + 1}º", font=_daily_font(29, True), fill="#047857")
        name = _fit_image_text(draw, row["name"], _daily_font(28, True), 835)
        draw.text((118, y + 12), name, font=_daily_font(28, True), fill="#0f172a")
        draw.text((42, y + 53), f"QIAs: {row['qias']}   Trocas: {row['changes']}   Caixa: {money(row['cash'])}", font=_daily_font(23), fill="#0f172a")
        detail = f"Crédito: {row['credit']}   Neoenergia: {row['neo']}   Ticket: {money(row['ticket'])}"
        if "award" in row:
            detail += f"   Prêmio*: {money(row['award'])}"
        draw.text((42, y + 84), detail, font=_daily_font(19), fill="#475569")
    footer = f"Sincronizado {synced_at:%d/%m/%Y %H:%M} · *Semana aberta: projeção."
    if any(r.get("cash_invalid") for r in rows):
        footer += " Caixa/ticket parciais."
    draw.text((30, image.height - 32), footer, font=_daily_font(17), fill="#475569")
    output = io.BytesIO()
    image.save(output, "PNG")
    return output.getvalue()


def analytical_xlsx(records, summary, tiers):
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill
    wb = Workbook()
    ws = wb.active
    ws.title = "Resultados"
    fields = [("name", "Conciliador"), ("qias", "QIAs"), ("changes", "Trocas"), ("credit", "Crédito"),
              ("neo", "Neoenergia"), ("cash", "Caixa"), ("ticket", "Ticket médio"),
              ("qias_projection", "Projeção QIAs"), ("changes_projection", "Projeção trocas"),
              ("monthly_award", "Premiação mensal atual"), ("projected_award", "Mensal projetada"),
              ("weekly_award", "Semanais encerradas"), ("commission_projection", "Comissão projetada")]
    fields += [("cash_projection", "Projeção caixa"), ("tier", "Faixa atual"),
               ("projected_tier", "Faixa projetada"), ("qias_remaining", "QIAs restantes"),
               ("changes_remaining", "Trocas restantes"), ("cash_invalid", "Valores de caixa inválidos")]
    ws.append([label for _, label in fields])
    for row in summary:
        ws.append([float(row[k]) if isinstance(row[k], Decimal) else row[k] for k, _ in fields])
    daily = wb.create_sheet("Diário")
    daily.append(["Data", "Conciliador", "QIAs", "Trocas", "Crédito", "Neoenergia", "Caixa", "NR", "1 A 3", "4 A 6", "Outras", "Valores de caixa inválidos"])
    groups = {}
    for row in records:
        groups.setdefault((row["date"], row["key"]), []).append(row)
    for (day, _), rows in sorted(groups.items()):
        totals = aggregate(rows)
        daily.append([day, rows[0]["name"]] + [float(totals[k]) for k in ("qias", "changes", "credit", "neo", "cash", "NR", "1 A 3", "4 A 6", "OUTRAS", "cash_invalid")])
    issues = wb.create_sheet("Pendências de caixa")
    issues.append(["Linha na aba operacional", "Data", "Conciliador", "Pendência"])
    for row in records:
        if row.get("cash_invalid"):
            issues.append([row["source_line"], row["date"], row["name"], "Valor inválido; caixa e ticket parciais. Corrigir coluna E na origem."])
    config = wb.create_sheet("Faixas consultadas")
    config.append(["Tipo", "Faixa", "QIAs", "Trocas", "Valor"])
    for section, values in tiers.items():
        for i, tier in enumerate(values, 1):
            config.append([section, i, tier["qias"], tier["changes"], float(tier["award"])])
    for sheet in wb:
        sheet.freeze_panes = "A2"
        sheet.auto_filter.ref = sheet.dimensions
        for row in sheet:
            for cell in row:
                if isinstance(cell.value, str):
                    cell.data_type = "s"  # Untrusted names must never become formulas.
                if isinstance(cell.value, date):
                    cell.number_format = "dd/mm/yyyy"
        for cell in sheet[1]:
            cell.font = Font(color="FFFFFF", bold=True)
            cell.fill = PatternFill("solid", fgColor="065F46")
            sheet.column_dimensions[cell.column_letter].width = 24
    output = io.BytesIO()
    wb.save(output)
    return output.getvalue()


def period_ranking(records, names, start, end, today):
    rows = [{"name": name, "key": key, **aggregate([r for r in records if r["key"] == key and start <= r["date"] <= min(end, today)])} for key, name in names.items()]
    return sorted(rows, key=lambda r: (-r["qias"], -r["changes"], -r["cash"], normalized(r["name"])))


def weekly_ranking(records, names, start, end, today, tiers):
    rows = period_ranking(records, names, start, end, today)
    elapsed, total = useful_days(start, min(today, end)), useful_days(start, end)
    for row in rows:
        row["tier"], row["earned_award"] = award_for(row["qias"], row["changes"], tiers)
        for metric in ("qias", "changes", "cash"):
            row[metric + "_projection"] = Decimal(row[metric]) * total / elapsed if elapsed else Decimal(0)
        row["projected_tier"], projected = award_for(row["qias_projection"], row["changes_projection"], tiers)
        row["award"] = row["earned_award"] if end < today else projected
    return rows


def render_ranking(st, rows):
    st.markdown("""<style>
.conciliation-row{background:#fff;border:1px solid #e2e8f0;border-radius:16px;padding:12px 16px;margin:8px 0;color:#0f172a}
.conciliation-row strong{font-size:1rem}.conciliation-row p{margin:5px 0 0;font-size:.85rem}
@media(max-width:600px){.conciliation-row{padding:10px}.conciliation-row p{font-size:.76rem}}
</style>""", unsafe_allow_html=True)
    for i, row in enumerate(rows, 1):
        award = f" · Premiação: {money(row['award'])}" if "award" in row else ""
        if "tier" in row:
            award += f" · Faixa atual: {row['tier']}ª" if row["tier"] else " · Sem faixa atingida"
        st.markdown(f'<div class="conciliation-row"><strong>{i}º · {html.escape(row["name"])}</strong><p>'
                    f'QIAs: {row["qias"]} · Trocas: {row["changes"]} · Caixa: {money(row["cash"])}{award}</p><p>'
                    f'Crédito: {row["credit"]} · Neoenergia: {row["neo"]} · Ticket: {money(row["ticket"])}</p></div>', unsafe_allow_html=True)
        if row.get("cash_invalid"):
            st.caption("Caixa e ticket parciais: há valores inválidos na origem.")


def render_conciliacao(st, registry, save_registry, manager_password):
    import hashlib
    import hmac
    import json
    st.subheader("CONCILIAÇÃO · AFOGADOS")
    try:
        settings = dict(st.secrets["conciliacao"])
        settings["service_account"] = dict(settings["service_account"])
        ttl = max(60, int(settings.get("cache_seconds", 300)))
        identity = hashlib.sha256(json.dumps(settings, sort_keys=True).encode()).hexdigest()
    except (KeyError, FileNotFoundError, ValueError, TypeError):
        st.error("Configure a seção conciliacao e a conta de serviço nos Secrets do Streamlit.")
        return

    @st.cache_resource(show_spinner=False)
    def source_cache(source_identity):
        return SourceCache()

    @st.fragment(run_every=ttl)
    def body():
        if not st.session_state.get("dashboard_autenticado"):
            return
        force = st.button("ATUALIZAR DADOS", key="conc_refresh")
        payload, stale = source_cache(identity).get(settings, ttl, force)
        if stale:
            st.warning("Não foi possível atualizar. Confira API ativada, compartilhamento e credenciais. Última leitura válida mantida, quando disponível.")
        if payload is None:
            st.error("Ainda não há leitura válida da planilha. Nenhum resultado foi estimado.")
            return
        st.caption(f"Última sincronização: {payload['synced_at']:%d/%m/%Y %H:%M:%S} · somente leitura · atualização a cada {ttl // 60} min")
        if payload["duplicates"]:
            st.caption(f"{payload['duplicates']} registros duplicados desconsiderados.")
        records, tiers = payload["records"], payload["tiers"]
        today = datetime.now(TZ).date()
        months = sorted({(r["date"].year, r["date"].month) for r in records} | {(today.year, today.month)}, reverse=True)
        year, month = st.selectbox("Competência", months, format_func=lambda p: f"{p[1]:02d}/{p[0]}", key="conc_month")
        summary = summarize(records, tiers, year, month, today, registry)
        names = {r["key"]: r["name"] for r in summary}
        month_rows = [r for r in records if r["key"] in names and (r["date"].year, r["date"].month) == (year, month) and r["date"] <= today]
        if any(r.get("cash_invalid") for r in month_rows):
            st.warning("Caixa, ticket e projeção de caixa parciais nesta competência: valores inválidos não foram somados. QIAs e trocas foram preservados. Consulte as linhas em Gestão.")
        view = st.radio("Visualização", ["VISÃO GERAL", "DIÁRIO", "SEMANAL", "GESTÃO"], horizontal=True, key="conc_view")
        if view == "GESTÃO":
            if not st.session_state.get("gestor_autenticado"):
                supplied = st.text_input("Senha do gestor", type="password", key="conc_password")
                if st.button("ENTRAR NA GESTÃO", key="conc_login"):
                    if manager_password and hmac.compare_digest(supplied, manager_password):
                        st.session_state.gestor_autenticado = True
                        st.rerun()
                    else:
                        st.error("Senha inválida ou não configurada.")
                return
            st.info("Metas e premiações são editadas exclusivamente na aba Config da planilha.")
            all_names = {r["key"]: r["name"] for r in records}
            all_names.update({key: flags.get("name", all_names.get(key, key)) for key, flags in registry.items()})
            issues = [r["source_line"] for r in records if r.get("cash_invalid")]
            if issues:
                st.warning("Corrigir valores da coluna E na aba operacional, linhas: " + ", ".join(map(str, issues)))
            st.caption(f"Conexão: {'desatualizada' if stale else 'ativa'} · {len(records)} registros · {len(tiers['monthly'])} faixas mensais · {len(tiers['weekly'])} semanais")
            with st.form("conc_registry"):
                updated = {}
                for key, name in sorted(all_names.items()):
                    a, b, c = st.columns([3, 1, 1])
                    a.write(name)
                    updated[key] = {"name": name, "active": b.checkbox("Ativo", value=registry.get(key, {}).get("active", True), key="conc_active_" + key),
                                    "visible": c.checkbox("Exibir", value=registry.get(key, {}).get("visible", True), key="conc_visible_" + key)}
                added = st.text_input("Adicionar conciliador sem lançamentos (nome oficial)", key="conc_new_name")
                if st.form_submit_button("SALVAR CONCILIADORES"):
                    if normalized(added):
                        updated.setdefault(normalized(added), {"name": " ".join(added.split()), "active": True, "visible": True})
                    try:
                        save_registry(updated)
                    except Exception:
                        st.error("Não foi possível salvar o cadastro. As configurações anteriores foram mantidas.")
                    else:
                        st.rerun()
            st.download_button("BAIXAR RELATÓRIO ANALÍTICO", analytical_xlsx(month_rows, summary, tiers),
                               file_name=f"conciliacao-{year}-{month:02d}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            return
        if view == "VISÃO GERAL":
            selected = st.selectbox("Conciliador", [""] + list(names), format_func=lambda k: names.get(k, "TODOS"), key="conc_person")
            displayed = [r for r in summary if not selected or r["key"] == selected]
            filtered = [r for r in month_rows if not selected or r["key"] == selected]
            totals = aggregate(filtered)
            from app_core import cards
            cards(st, [("QIAs", totals["qias"]), ("TROCAS", totals["changes"]), ("CAIXA", money(totals["cash"])), ("TICKET MÉDIO", money(totals["ticket"]))])
            first = tiers["monthly"][0]
            count = len(displayed)
            st.caption(f"Meta inicial individual: {first['qias']} QIAs + {first['changes']} trocas. Meta agregada: soma de {count} conciliadores exibidos.")
            goal = first["qias"] * count
            st.write(f"QIAs: {totals['qias'] / goal * 100 if goal else 0:.1f}% de {goal} · Meta de trocas: {first['changes'] * count}")
            cards(st, [("PROJEÇÃO QIAs", f"{sum(r['qias_projection'] for r in displayed):.0f}"),
                       ("PROJEÇÃO TROCAS", f"{sum(r['changes_projection'] for r in displayed):.0f}"),
                       ("PROJEÇÃO CAIXA", money(sum(r["cash_projection"] for r in displayed))),
                       ("COMISSÃO PROJETADA", money(sum(r["commission_projection"] for r in displayed)))])
            st.caption(f"Média diária: {sum(r['qias_average'] for r in displayed):.1f} QIAs · {sum(r['changes_average'] for r in displayed):.1f} trocas. Segunda a sábado; domingos excluídos do divisor.")
            for regime in ("NR", "1 A 3", "4 A 6", "OUTRAS"):
                st.write(f"{regime}: {totals[regime]} QIAs ({totals[regime] / totals['qias'] * 100 if totals['qias'] else 0:.1f}%)")
            st.caption(f"Trocas crédito: {totals['credit']} ({totals['credit'] / totals['changes'] * 100 if totals['changes'] else 0:.1f}%) · Neoenergia: {totals['neo']} ({totals['neo'] / totals['changes'] * 100 if totals['changes'] else 0:.1f}%)")
            st.write(f"Premiação mensal atual: {money(sum(r['monthly_award'] for r in displayed))} · Mensal projetada: {money(sum(r['projected_award'] for r in displayed))} · Semanais conquistadas: {money(sum(r['weekly_award'] for r in displayed))}")
            with st.expander("Evolução de QIAs por régua"):
                import pandas as pd
                for label, grouping in (("Diária", lambda r: r["date"].isoformat()), ("Semanal", lambda r: f"S{(r['date'].day - 1) // 7 + 1}")):
                    groups = {}
                    for record in filtered:
                        groups.setdefault(grouping(record), []).append(record)
                    table = [{"Período": key, **{k: aggregate(value)[k] for k in ("NR", "1 A 3", "4 A 6")}} for key, value in sorted(groups.items())]
                    st.write(label)
                    if table:
                        st.bar_chart(pd.DataFrame(table).set_index("Período"))
            render_ranking(st, displayed)
            for row in displayed:
                with st.expander(row["name"] + " · projeções e premiação"):
                    st.write(f"QIAs projetados: {row['qias_projection']:.1f} · Trocas projetadas: {row['changes_projection']:.1f}")
                    st.write(f"Faixa mensal atual: {row['tier']} · Projetada: {row['projected_tier']}")
                    st.write(f"Mensal atual: {money(row['monthly_award'])} · Projetada: {money(row['projected_award'])}")
                    st.write(f"Semanas encerradas: {money(row['weekly_award'])} · Total projetado: {money(row['commission_projection'])}")
                    st.write(f"Réguas: NR {row['NR']} · 1 A 3 {row['1 A 3']} · 4 A 6 {row['4 A 6']}")
                    st.write(f"Para a próxima faixa: {row['qias_remaining']} QIAs e {row['changes_remaining']} trocas.")
            return
        periods = weeks(year, month)
        default_day = min(today.day, monthrange(year, month)[1]) if (year, month) == (today.year, today.month) else 1
        if view == "DIÁRIO":
            start = end = st.date_input("Dia", date(year, month, default_day), min_value=date(year, month, 1), max_value=date(year, month, monthrange(year, month)[1]), key=f"conc_day_{year}_{month}")
            ranked = period_ranking(records, names, start, end, today)
            a, b = periods[(start.day - 1) // 7]
            weekly = {r["key"]: r for r in period_ranking(records, names, a, b, today)}
            monthly = {r["key"]: r for r in summary}
            period = f"{start:%d/%m/%Y}"
        else:
            index = st.selectbox("Semana", range(len(periods)), index=min((default_day - 1) // 7, len(periods) - 1), format_func=lambda i: f"S{i+1} · {periods[i][0]:%d/%m} a {periods[i][1]:%d/%m}", key=f"conc_week_{year}_{month}")
            start, end = periods[index]
            ranked = weekly_ranking(records, names, start, end, today, tiers["weekly"])
            st.info("Semana encerrada: premiação conquistada." if end < today else "Semana aberta ou futura: premiação projetada, não somada às conquistadas.")
            if index:
                previous = period_ranking(records, names, *periods[index - 1], today)
                st.caption(f"Comparativo do total com a semana anterior: QIAs {sum(r['qias'] for r in ranked) - sum(r['qias'] for r in previous):+d} · Trocas {sum(r['changes'] for r in ranked) - sum(r['changes'] for r in previous):+d} · Caixa {money(sum(r['cash'] for r in ranked) - sum(r['cash'] for r in previous))}")
            period = f"S{index+1} · {start:%d/%m/%Y} a {end:%d/%m/%Y}"
        from app_core import cards
        totals = aggregate([r for r in month_rows if start <= r["date"] <= end])
        cards(st, [("QIAs", totals["qias"]), ("TROCAS", totals["changes"]), ("CAIXA", money(totals["cash"])), ("TICKET MÉDIO", money(totals["ticket"]))])
        render_ranking(st, ranked)
        if view == "SEMANAL":
            with st.expander("Projeções da semana"):
                for row in ranked:
                    st.write(f"{row['name']}: {row['qias_projection']:.1f} QIAs · {row['changes_projection']:.1f} trocas · Caixa {money(row['cash_projection'])} · Faixa projetada {row['projected_tier']} · Prêmio {money(row['award'])}")
        if view == "DIÁRIO":
            with st.expander("Acumulados semanal e mensal"):
                for row in ranked:
                    w, m = weekly[row["key"]], monthly[row["key"]]
                    st.write(f"{row['name']}: semana {w['qias']} QIAs / {w['changes']} trocas · mês {m['qias']} QIAs / {m['changes']} trocas")
        st.download_button("BAIXAR RANKING PNG", ranking_png(ranked, "CONCILIAÇÃO · " + view, period, payload["synced_at"]),
                           file_name=f"ranking-conciliacao-{view.lower()}-{start.isoformat()}.png", mime="image/png")
    body()
