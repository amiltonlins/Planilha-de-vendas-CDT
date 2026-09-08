from datetime import date
import json
import unittest
from pathlib import Path

from app_core import _daily_overlay_color, apply_team_labels, daily_performance, daily_ranking_html, daily_ranking_png, daily_ranking_rows, daily_team_totals, regular
from gerar_painel import summarize


def _sale(day, seller, neo="Não"):
    return {"data_venda": day, "vendedor": seller, "neoenergia": neo}


class DailyRankingTests(unittest.TestCase):
    def test_counts_today_week_and_neo(self):
        team = [
            {"vendedor": "Ana Lívia", "equipe": "Equipe Interna", "semanas": [1, 5], "media": 2.1},
            {"vendedor": "Bruno", "equipe": "Equipe Externa", "semanas": [0, 4], "media": 1.6},
            {"vendedor": "Carla", "equipe": "Equipe Interna", "semanas": [0, 0], "media": 0},
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
            {"vendedor": "Ana Lívia", "equipe": "Equipe Interna", "vendas_dia": 2, "vendas_semana": 5, "neo_dia": 1, "classificacao": "Verde", "cor_classificacao": "#16A34A", "emoji": "🙂"},
            {"vendedor": "Bruno", "equipe": "Equipe Externa", "vendas_dia": 1, "vendas_semana": 4, "neo_dia": 1, "classificacao": "Amarelo", "cor_classificacao": "#F59E0B", "emoji": "😐"},
            {"vendedor": "Carla", "equipe": "Equipe Interna", "vendas_dia": 0, "vendas_semana": 0, "neo_dia": 0, "classificacao": "Vermelho", "cor_classificacao": "#DC2626", "emoji": "😟"},
        ], ranking)
        self.assertEqual({
            "Equipe Interna": {"dia": 2, "semana": 5, "neo": 1},
            "Equipe Externa": {"dia": 1, "semana": 4, "neo": 1},
        }, daily_team_totals(ranking))
        ranking_html = daily_ranking_html(ranking, date(2026, 9, 8), week_index, week_ranges)
        self.assertIn("RANKING DE VENDAS — HOJE", ranking_html)
        self.assertIn("--daily-color:#16A34A", ranking_html)
        self.assertIn("NEO HOJE</small><strong>1</strong>", ranking_html)
        self.assertNotIn("<small>Verde</small>", ranking_html)
        self.assertNotIn("<small>Amarelo</small>", ranking_html)
        self.assertTrue(daily_ranking_png(ranking, date(2026, 9, 8), week_index, week_ranges).startswith(b"\x89PNG\r\n\x1a\n"))

    def test_daily_color_thresholds(self):
        self.assertEqual(("Azul", "#0891B2", "😎"), daily_performance(3))
        self.assertEqual(("Azul", "#0891B2", "😎"), daily_performance(8))
        self.assertEqual(("Verde", "#16A34A", "🙂"), daily_performance(2))
        self.assertEqual(("Amarelo", "#F59E0B", "😐"), daily_performance(1))
        self.assertEqual(("Vermelho", "#DC2626", "😟"), daily_performance(0))

    def test_png_neo_highlight_matches_translucent_dashboard_style(self):
        self.assertEqual((59, 178, 103), _daily_overlay_color("#16A34A"))
        self.assertEqual((247, 174, 50), _daily_overlay_color("#F59E0B"))

    def test_does_not_show_unpublished_future_day(self):
        team = [{"vendedor": "Ana", "equipe": "Equipe Interna", "semanas": [2]}]
        rows = [_sale(date(2026, 9, 2), "Ana", "Sim")]
        cfg = {"ano": 2026, "mes": 9, "dia_referencia": 1}

        ranking, _, _ = daily_ranking_rows(team, rows, cfg, date(2026, 9, 2))

        self.assertEqual(0, ranking[0]["vendas_dia"])
        self.assertEqual(0, ranking[0]["neo_dia"])

    def test_includes_every_active_dashboard_seller_even_with_zero_sales(self):
        cfg = json.loads((Path(__file__).parents[1] / "config.json").read_text(encoding="utf-8"))
        active = dict(cfg["vendedores"][0], vendedor="Vendedora Ativa", ativo=True, pertence_franquia=True, categoria="Vendedor")
        inactive = dict(cfg["vendedores"][0], vendedor="Vendedora Oculta", ativo=False, pertence_franquia=True, categoria="Vendedor")
        cfg.update({"ano": 2026, "mes": 9, "dia_referencia": 8, "vendedores": [active, inactive]})

        summary, _, _, _ = summarize([], cfg)
        visible = regular(apply_team_labels(summary, cfg))
        ranking, _, _ = daily_ranking_rows(visible, [], cfg, date(2026, 9, 8))

        self.assertEqual(["Vendedora Ativa"], [item["vendedor"] for item in ranking])
        self.assertEqual(0, ranking[0]["vendas_dia"])
        self.assertEqual(0, ranking[0]["vendas_semana"])


if __name__ == "__main__":
    unittest.main()
