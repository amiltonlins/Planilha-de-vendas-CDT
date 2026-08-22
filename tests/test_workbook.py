import io
import json
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET
from app import canonicalize, excel_bytes, performance, prepare_config, rows_from_csv, rows_from_xlsx
from gerar_painel import summarize

ROOT=Path(__file__).parents[1]; BOOK=ROOT/"output"/"Painel_Comercial_Afogados.xlsx"; NS={"m":"http://schemas.openxmlformats.org/spreadsheetml/2006/main"}

class WorkbookTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls): subprocess.run(["python3","gerar_painel.py"],cwd=ROOT,check=True)

    def test_expected_workbook(self):
        self.assertTrue(BOOK.exists()); self.assertGreater(BOOK.stat().st_size,20_000)
        with zipfile.ZipFile(BOOK) as z:
            for name in z.namelist():
                if name.endswith((".xml", ".rels")):
                    ET.fromstring(z.read(name))
            wb=ET.fromstring(z.read("xl/workbook.xml")); names=[x.attrib["name"] for x in wb.findall(".//m:sheet",NS)]
            self.assertEqual(names,["DASHBOARD","RELATORIO GERAL","SEMANAL","COMISSOES","CONFIGURACOES","CADASTRO VENDEDORES","BASE IMPORTADA"])
            dashboard=z.read("xl/worksheets/sheet1.xml"); self.assertIn(b"dataValidations",dashboard); self.assertIn(b"VLOOKUP",dashboard)
            general=z.read("xl/worksheets/sheet2.xml")
            self.assertIn(b'A5:A10 H5:H10',general)
            self.assertIn(b'1.5*$AG5',general)
            self.assertIn(b'0.7*$AG5',general)

    def test_configuration_and_csv_are_real_inputs(self):
        cfg=json.loads((ROOT/"config.json").read_text()); self.assertEqual(5,len(cfg["premiacao_semanal"])); self.assertEqual(8,len(cfg["reguas_comissao"]["abaixo_1000"]))
        self.assertTrue(all(x["meta_individual"] > 0 for x in cfg["vendedores"]))
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/"custom.xlsx"; subprocess.run(["python3","gerar_painel.py","--dados","dados_exemplo.csv","--config","config.json","--output",str(out)],cwd=ROOT,check=True); self.assertTrue(out.is_file())

    def test_web_csv_upload_calculates_and_downloads(self):
        cfg=json.loads((ROOT/"config.json").read_text())
        raw=rows_from_csv((ROOT/"dados_exemplo.csv").read_bytes()); rows,mapping=canonicalize(raw,cfg)
        configured=prepare_config(cfg,rows,8,2026); summary,days,elapsed,official=summarize(rows,configured)
        book=excel_bytes(rows,configured,summary,days,elapsed,official)
        self.assertEqual(239,len(rows)); self.assertIn("data_venda",mapping); self.assertGreater(len(book),20_000)
        with zipfile.ZipFile(io.BytesIO(book)) as archive: self.assertIn("xl/workbook.xml",archive.namelist())

    def test_web_xlsx_upload_autodetects_base(self):
        cfg=json.loads((ROOT/"config.json").read_text())
        raw=rows_from_xlsx(BOOK.read_bytes()); rows,mapping=canonicalize(raw,cfg)
        self.assertEqual(239,len(rows)); self.assertEqual("Data da venda",mapping["data_venda"])

    def test_online_performance_colors(self):
        self.assertEqual("Azul",performance(150,100)[0]); self.assertEqual("Verde",performance(100,100)[0])
        self.assertEqual("Amarelo",performance(70,100)[0]); self.assertEqual("Vermelho",performance(69,100)[0])

if __name__=="__main__": unittest.main()
