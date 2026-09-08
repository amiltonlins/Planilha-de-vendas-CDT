from datetime import date
import unittest

from app_core import daily_ranking_html, daily_ranking_png, daily_ranking_rows


def _sale(day, seller, neo="Não"):
    return {"data_venda": day, "vendedor": seller, "neoenergia": neo}


class DailyRankingTests(unittest.TestCase):
    def test_counts_today_week_and_neo(self):
        team = [
            {"vendedor": "Ana Lívia", "equipe": "Equipe Interna", "semanas": [1, 5]},
            {"vendedor": "Bruno", "equipe": "Equipe Externa", "semanas": [0, 4]},
        ]
        rows = [
            _sale(date(2026, 9, 8), "ANA LIVIA", "Neoenergia Celpe"),
            _sale(date(2026, 9, 8), "Ana Lívia"),
            _sale(date(2026, 9, 8), "Bruno", "Sim"),
            _sale(date(2026, 9, 7), "Bruno", "Sim"),
            _sale(date(2026, 9, 8), "Canal Nacional", "Sim"),
        ]
        cfg = {"ano": 2026, "mes": 9, "dia_referencia": 8}

        ranking, week_index, week_ranges = daily_ranking_rows(team, rows, cfg, date(2026, 9, 8))

        self.assertEqual(1, week_index)
        self.assertEqual([
            {"vendedor": "Ana Lívia", "equipe": "Equipe Interna", "vendas_dia": 2, "vendas_semana": 5, "neo_dia": 1},
            {"vendedor": "Bruno", "equipe": "Equipe Externa", "vendas_dia": 1, "vendas_semana": 4, "neo_dia": 1},
        ], ranking)
        self.assertIn("RANKING DE VENDAS — HOJE", daily_ranking_html(ranking, date(2026, 9, 8), week_index, week_ranges))
        self.assertTrue(daily_ranking_png(ranking, date(2026, 9, 8), week_index, week_ranges).startswith(b"\x89PNG\r\n\x1a\n"))

    def test_does_not_show_unpublished_future_day(self):
        team = [{"vendedor": "Ana", "equipe": "Equipe Interna", "semanas": [2]}]
        rows = [_sale(date(2026, 9, 2), "Ana", "Sim")]
        cfg = {"ano": 2026, "mes": 9, "dia_referencia": 1}

        ranking, _, _ = daily_ranking_rows(team, rows, cfg, date(2026, 9, 2))

        self.assertEqual(0, ranking[0]["vendas_dia"])
        self.assertEqual(0, ranking[0]["neo_dia"])


if __name__ == "__main__":
    unittest.main()
