import io
import unittest
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import patch

from conciliacao import SCOPE, aggregate, award_for, parse_rows, parse_tiers, read_source, summarize, useful_days, weeks
from conciliacao_ui import SourceCache, analytical_xlsx, ranking_png, weekly_ranking


HEADER = ["Carimbo de data/hora", "MATRÍCULA", "TOTAL DE QIA'S", "Régua", "VALOR RECEBIDO", "FORMA", "COMPROVANTE", "FEZ ALTERAÇÃO", "OBS", "CONCILIADOR (A)"]
CONFIG = [["META CONCILIAÇÃO (mensal)"], ["RÉGUAS", "QIA'S", "TROCAS", "VALOR"],
          ["1ª", 650, 90, 400], ["2ª", 750, 100, 500], [], ["SEMANAL CONCILIAÇÃO"],
          ["QIA'S", "TROCAS", "RÉGUA", "VALOR"], [170, 20, "1ª", 50], [200, 25, "1ª", 100]]


def raw(day="01/09/2026 09:00:00", qias=6, cash="30,90", change="SIM - CRÉDITO", name="ANANNDA BRITO", registration="123"):
    return [day, registration, qias, "1 a 3", cash, "APENAS TROCA", "private-link", change, "private-note", name]


class ConciliationTests(unittest.TestCase):
    def test_normalization_dedup_and_sums(self):
        values = [HEADER, raw(), raw(name=" anannda   brito "), raw(qias=0, cash=0, registration="456", change="SIM - NEOENERGIA")]
        rows, duplicates = parse_rows(values)
        self.assertEqual(duplicates, 1)
        self.assertEqual(rows[0]["name"], "ANANNDA BRITO")
        total = aggregate(rows)
        self.assertEqual((total["qias"], total["changes"], total["cash"]), (6, 2, Decimal("30.90")))
        self.assertEqual(total["ticket"], Decimal("5.15"))
        self.assertEqual(total["1 A 3"], 6)
        self.assertNotIn("private-link", str(rows))
        self.assertNotIn("123", str(rows))

    def test_invalid_does_not_silently_understate(self):
        with self.assertRaises(ValueError):
            parse_rows([HEADER, raw(qias="inválido")])

    def test_no_change_and_zero_ticket(self):
        rows, _ = parse_rows([HEADER, raw(qias=0, cash=0, change="NÃO REALIZADA")])
        self.assertEqual(aggregate(rows)["changes"], 0)
        self.assertEqual(aggregate(rows)["ticket"], 0)

    def test_bad_cash_preserves_qias_and_marks_partial(self):
        rows, _ = parse_rows([HEADER, raw(cash="na oferta"), raw(cash="61,,80", registration="2")])
        totals = aggregate(rows)
        self.assertEqual((totals["qias"], totals["changes"], totals["cash_invalid"]), (12, 2, 2))
        self.assertEqual(totals["cash"], 0)
        self.assertEqual(rows[0]["source_line"], 2)

    def test_registry_person_without_any_record(self):
        summary = summarize([], parse_tiers(CONFIG), 2026, 9, date(2026, 9, 9),
                            {"NOVO": {"name": "Novo", "active": True, "visible": True}})
        self.assertEqual((summary[0]["name"], summary[0]["qias"]), ("Novo", 0))

    def test_week_projection_and_future(self):
        rows, _ = parse_rows([HEADER] + [raw(day="08/09/2026", qias=4, registration=str(i)) for i in range(20)])
        start, end = date(2026, 9, 8), date(2026, 9, 14)
        names = {"ANANNDA BRITO": "ANANNDA BRITO"}
        tiers = parse_tiers(CONFIG)["weekly"]
        opened = weekly_ranking(rows, names, start, end, start, tiers)[0]
        self.assertEqual((opened["earned_award"], opened["award"]), (0, 100))
        self.assertEqual(opened["qias_projection"], 480)
        future = weekly_ranking(rows, names, start, end, date(2026, 9, 7), tiers)[0]
        self.assertEqual((future["qias_projection"], future["award"]), (0, 0))

    def test_source_readonly_and_complete_payload(self):
        from unittest.mock import MagicMock
        session = MagicMock()
        session.__enter__.return_value = session
        session.get.return_value.json.return_value = {"valueRanges": [{"values": [HEADER, raw()]}, {"values": CONFIG}]}
        factory = MagicMock(return_value=session)
        with patch("google.oauth2.service_account.Credentials.from_service_account_info") as credentials:
            result = read_source({"service_account": {}, "spreadsheet_id": "test-sheet"}, factory)
        self.assertEqual(credentials.call_args.kwargs["scopes"], [SCOPE])
        self.assertEqual(len(result["records"]), 1)
        self.assertEqual(len(result["tiers"]["weekly"]), 2)
        self.assertEqual(session.get.call_args.kwargs["params"]["ranges"], ["'2026'!A:J", "'Config'!A:D"])
        session.post.assert_not_called()
        session.get.return_value.raise_for_status.assert_called_once()

    def test_six_monthly_tiers_and_malformed_config(self):
        config = CONFIG[:4] + [["3ª",850,110,600],["4ª",950,120,700],["5ª",1000,130,800],["6ª",1050,140,900]] + CONFIG[4:]
        self.assertEqual(award_for(1050,140,parse_tiers(config)["monthly"]),(6,900))
        with self.assertRaises(ValueError):
            parse_tiers(CONFIG + [[250,30,"3ª"]])

    def test_dynamic_tiers_joint_and_repeated_labels(self):
        tiers = parse_tiers(CONFIG)
        self.assertEqual(len(tiers["weekly"]), 2)
        self.assertEqual(award_for(999, 89, tiers["monthly"]), (0, 0))
        self.assertEqual(award_for(999, 90, tiers["monthly"]), (1, 400))
        self.assertEqual(award_for(999, 999, tiers["monthly"]), (2, 500))
        self.assertEqual(award_for(200, 25, tiers["weekly"]), (2, 100))

    def test_calendar(self):
        self.assertEqual(useful_days(date(2026, 9, 1), date(2026, 9, 7)), 6)
        self.assertEqual(weeks(2026, 2)[-1], (date(2026, 2, 22), date(2026, 2, 28)))
        self.assertEqual(weeks(2026, 9)[-1], (date(2026, 9, 29), date(2026, 9, 30)))

    def test_weekly_columns_reordered(self):
        config = CONFIG[:5] + [["SEMANAL CONCILIAÇÃO"], ["RÉGUA", "QIA'S", "TROCAS", "VALOR"], ["1ª", 170, 20, 50]]
        self.assertEqual(parse_tiers(config)["weekly"][0], {"qias": 170, "changes": 20, "award": 50})

    def test_closed_weeks_only_and_zero_people(self):
        rows, _ = parse_rows([HEADER] + [raw(qias=10, registration=str(i)) for i in range(20)] + [raw(day="01/08/2026", name="ZERADO")])
        tiers = parse_tiers(CONFIG)
        open_week = summarize(rows, tiers, 2026, 9, date(2026, 9, 7))
        closed = summarize(rows, tiers, 2026, 9, date(2026, 9, 8))
        self.assertEqual(open_week[0]["weekly_award"], 0)
        self.assertEqual(closed[0]["weekly_award"], 50)
        self.assertEqual(closed[1]["qias"], 0)
        self.assertEqual(closed[0]["commission_projection"], closed[0]["projected_award"] + 50)
        self.assertEqual(len(summarize(rows, tiers, 2026, 9, date(2026, 9, 8), {"ZERADO": {"visible": False}})), 1)

    def test_future_excluded_projection(self):
        rows, _ = parse_rows([HEADER, raw(), raw(day="30/09/2026", registration="other")])
        summary = summarize(rows, parse_tiers(CONFIG), 2026, 9, date(2026, 9, 1))
        self.assertEqual(summary[0]["qias"], 6)
        self.assertEqual(summary[0]["qias_projection"], 6 * useful_days(date(2026, 9, 1), date(2026, 9, 30)))

    def test_cache_keeps_last_good_both_sections(self):
        cache = SourceCache()
        good = {"records": [1], "tiers": [2]}
        self.assertEqual(cache.get({}, 300, reader=lambda _: good), (good, False))
        def fail(_):
            raise ValueError("secret must not appear")
        self.assertEqual(cache.get({}, 300, force=True, reader=fail), (good, True))
        self.assertEqual(cache.get({}, 300, force=True, reader=lambda _: {"records": [3], "tiers": [4]})[1], False)

    def test_exports(self):
        from PIL import Image
        from openpyxl import load_workbook
        rows, _ = parse_rows([HEADER, raw(name="=NAME")])
        tiers = parse_tiers(CONFIG)
        summary = summarize(rows, tiers, 2026, 9, date(2026, 9, 9))
        png = ranking_png(summary, "CONCILIAÇÃO · DIÁRIO", "09/09/2026", datetime(2026, 9, 9))
        self.assertEqual(Image.open(io.BytesIO(png)).width, 1080)
        workbook = load_workbook(io.BytesIO(analytical_xlsx(rows, summary, tiers)))
        self.assertEqual(workbook["Resultados"]["A2"].data_type, "s")
        self.assertNotIn("MATRÍCULA", [cell.value for sheet in workbook for row in sheet for cell in row])

    def test_streamlit_views_and_manager_access(self):
        from streamlit.testing.v1 import AppTest
        rows, _ = parse_rows([HEADER, raw()])
        payload = {"records": rows, "tiers": parse_tiers(CONFIG), "duplicates": 0,
                   "synced_at": datetime(2026, 9, 9)}
        app = AppTest.from_string('''
import streamlit as st
from conciliacao_ui import render_conciliacao
render_conciliacao(st, {}, lambda value: None, "test-manager")
''')
        app.secrets["conciliacao"] = {"service_account": {}, "spreadsheet_id": "test"}
        app.session_state["dashboard_autenticado"] = True
        with patch.object(SourceCache, "get", return_value=(payload, False)):
            app.run()
            self.assertFalse(app.exception)
            for view in ("DIÁRIO", "SEMANAL", "GESTÃO"):
                app.radio(key="conc_view").set_value(view).run()
                self.assertFalse(app.exception)
            self.assertEqual(len(app.text_input), 1)
            app.text_input(key="conc_password").set_value("test-manager")
            app.button(key="conc_login").click().run()
            self.assertFalse(app.exception)
            self.assertTrue(app.session_state["gestor_autenticado"])
            self.assertTrue(app.checkbox)


if __name__ == "__main__":
    unittest.main()
