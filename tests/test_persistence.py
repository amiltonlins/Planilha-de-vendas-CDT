import json
import tempfile
import unittest
from datetime import date, datetime
from pathlib import Path
from unittest.mock import patch

import app_core


class PersistenceTests(unittest.TestCase):
    def setUp(self):
        self.base = json.loads((app_core.ROOT / "config.json").read_text(encoding="utf-8"))
        self.rows = [{
            "data_venda": date(2026, 8, 27),
            "vendedor": "Vendedor Teste",
            "setor": "Interna",
            "categoria": "Vendedor",
            "neoenergia": "Não",
            "adimplencia_m2": "0",
            "status": "Aprovada",
            "id_venda": "TESTE-1",
        }]

    def test_save_publishes_remote_and_keeps_local_cache(self):
        with tempfile.TemporaryDirectory() as tmp:
            old_path = app_core.PUBLISHED_PATH
            app_core.PUBLISHED_PATH = Path(tmp) / "dados.json"
            try:
                with patch("app_core.save_remote_payload") as remote_save:
                    app_core.save_published(
                        self.rows,
                        self.base,
                        "relatorio.csv",
                        updated_at=datetime(2026, 8, 27, 14, 30),
                    )
                remote_save.assert_called_once()
                payload = json.loads(app_core.PUBLISHED_PATH.read_text(encoding="utf-8"))
                self.assertEqual("2026-08-27", payload["vendas"][0]["data_venda"])
            finally:
                app_core.PUBLISHED_PATH = old_path

    def test_load_prefers_remote_payload(self):
        payload = {
            "atualizado_em": "2026-08-27T14:30:00-03:00",
            "arquivo": "relatorio.csv",
            "config": self.base,
            "historico_importacoes": [],
            "vendas": [app_core.serialize_row(self.rows[0])],
        }
        with patch("app_core.remote_persistence_enabled", return_value=True), patch(
            "app_core.load_remote_payload", return_value=payload
        ):
            rows, _, metadata = app_core.load_published(self.base)
        self.assertEqual(date(2026, 8, 27), rows[0]["data_venda"])
        self.assertEqual("supabase", metadata["persistencia"])


if __name__ == "__main__":
    unittest.main()
