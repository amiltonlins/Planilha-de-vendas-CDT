from datetime import date
import io
import unittest

from PIL import Image

from app_core import weekly_prize_ranking_png


class WeeklyPrizeRankingTests(unittest.TestCase):
    def test_generates_selected_week_ranking_png(self):
        team = [
            {"vendedor": "Ana", "equipe": "Equipe Interna", "semanas": [8, 20], "premios": [0, 150]},
            {"vendedor": "Bruno", "equipe": "Equipe Externa", "semanas": [10, 14], "premios": [50, 100]},
            {"vendedor": "Carla", "equipe": "Equipe Interna", "semanas": [4, 0], "premios": [0, 0]},
        ]
        cfg = {
            "ano": 2026,
            "mes": 9,
            "premiacao_semanal": [
                {"vendas": 10, "premio": 50},
                {"vendas": 14, "premio": 100},
                {"vendas": 20, "premio": 150},
                {"vendas": 25, "premio": 200},
                {"vendas": 30, "premio": 300},
            ],
        }

        png = weekly_prize_ranking_png(team, 1, cfg)
        image = Image.open(io.BytesIO(png))

        self.assertTrue(png.startswith(b"\x89PNG\r\n\x1a\n"))
        self.assertEqual(1080, image.width)
        self.assertEqual(270 + 62 + 3 * 96 + 70, image.height)


if __name__ == "__main__":
    unittest.main()
