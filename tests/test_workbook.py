import io
import json
import subprocess
import tempfile
import unittest
import zipfile
from datetime import date, datetime
from pathlib import Path
from xml.etree import ElementTree as ET
import app
from app import canonicalize, excel_bytes, performance, prepare_config, regular, rows_from_csv, rows_from_xlsx, save_published, load_published
from gerar_painel import summarize, tier_value, weekly_prize

ROOT=Path(__file__).parents[1]; BOOK=ROOT/"output"/"Painel_Comercial_Afogados.xlsx"; NS={"m":"http://schemas.openxmlformats.org/spreadsheetml/2006/main"}

class WorkbookTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls): subprocess.run(["python3","gerar_painel.py"],cwd=ROOT,check=True)

    def test_expected_workbook(self):
        self.assertTrue(BOOK.exists()); self.assertGreater(BOOK.stat().st_size,15_000)
        with zipfile.ZipFile(BOOK) as z:
            for name in z.namelist():
                if name.endswith((".xml", ".rels")):
                    ET.fromstring(z.read(name))
            wb=ET.fromstring(z.read("xl/workbook.xml")); names=[x.attrib["name"] for x in wb.findall(".//m:sheet",NS)]
            self.assertEqual(names,["DASHBOARD","RELATORIO GERAL","SEMANAL","COMISSOES","CONFIGURACOES","CADASTRO VENDEDORES","BASE IMPORTADA"])
            dashboard=z.read("xl/worksheets/sheet1.xml"); self.assertIn(b"dataValidations",dashboard); self.assertIn(b"VLOOKUP",dashboard)
            general=z.read("xl/worksheets/sheet2.xml")
            self.assertIn(b'A5:A7 H5:H7',general)
            self.assertIn(b'1.5*$',general)
            self.assertIn(b'0.7*$',general)

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
        self.assertEqual(239,len(rows)); self.assertIn("data_venda",mapping); self.assertGreater(len(book),15_000)
        with zipfile.ZipFile(io.BytesIO(book)) as archive: self.assertIn("xl/workbook.xml",archive.namelist())

    def test_web_xlsx_upload_autodetects_base(self):
        cfg=json.loads((ROOT/"config.json").read_text())
        raw=rows_from_xlsx(BOOK.read_bytes()); rows,mapping=canonicalize(raw,cfg)
        self.assertEqual(239,len(rows)); self.assertEqual("Data da venda",mapping["data_venda"])

    def test_online_performance_colors(self):
        self.assertEqual("Azul",performance(150,100)[0]); self.assertEqual("Verde",performance(100,100)[0])
        self.assertEqual("Amarelo",performance(70,100)[0]); self.assertEqual("Vermelho",performance(69,100)[0])

    def test_real_headers_use_nome_as_product_without_private_output(self):
        cfg=json.loads((ROOT/"config.json").read_text())
        raw=[{"Franquia":"CLIN","Matricula":"123","Telefone":"9999","Nome":"NEOENERGIA CELPE","Data":"01/08/2026","Vendedor":"Teste","Login":"login"}]
        rows,mapping=canonicalize(raw,cfg)
        self.assertEqual("Nome",mapping["neoenergia"]); self.assertEqual("Sim",rows[0]["neoenergia"])
        self.assertNotIn("Telefone",rows[0]); self.assertNotIn("Matricula",rows[0]); self.assertNotIn("Nome",rows[0])

    def test_schedule_zeros_six_weeks_and_projected_scenario(self):
        cfg=json.loads((ROOT/"config.json").read_text()); cfg["dia_referencia"]=10; cfg["limite_cenario_maior"]=20
        cfg["vendedores"]=[{"vendedor":"Teste","setor":"CLIN","categoria":"Vendedor","ativo":True,"experiencia":True,"meta_individual":10,"trabalha_sabado":False,"trabalha_domingo":False,"data_inicio":"2026-08-05","data_desligamento":"","folgas":["2026-08-07"]}]
        rows=[{"data_venda":date(2026,8,5),"vendedor":"Teste","neoenergia":"Sim","adimplencia_m2":"100%"} for _ in range(10)]
        summary,_,_,official=summarize(rows,cfg); seller=summary[0]
        self.assertEqual(6,len(seller["semanas"])); self.assertEqual(2,seller["zeros"])
        self.assertEqual("abaixo_1000",official); self.assertEqual("maior_ou_igual_1000",seller["cenario_projetado"])
        self.assertEqual(0,seller["base"]); self.assertGreater(seller["comissao_proj"],0)

    def test_commission_and_weekly_business_rules(self):
        cfg=json.loads((ROOT/"config.json").read_text())
        high=cfg["reguas_comissao"]["maior_ou_igual_1000"]
        low=cfg["reguas_comissao"]["abaixo_1000"]
        self.assertEqual(30,tier_value(84,high)); self.assertEqual(2520,84*tier_value(84,high))
        self.assertEqual(18,tier_value(84,low)); self.assertEqual(0,tier_value(34,high))
        self.assertEqual(150,weekly_prize(22,cfg["premiacao_semanal"]))

    def test_unknown_seller_is_national_and_inactive_is_hidden(self):
        cfg=json.loads((ROOT/"config.json").read_text()); raw=[{"Data":"01/08/2026","Vendedor":"Vendedor Nacional","Nome":"VISA"}]
        rows,_=canonicalize(raw,cfg); configured=prepare_config(cfg,rows,8,2026)
        seller=next(x for x in configured["vendedores"] if x["vendedor"]=="Vendedor Nacional")
        self.assertFalse(seller["pertence_franquia"]); self.assertFalse(seller["ativo"]); self.assertEqual("Canal Nacional",seller["categoria"])
        summary,*_=summarize(rows,configured); self.assertEqual(1,sum(x["vendas"] for x in summary)); self.assertEqual([],regular(summary))

    def test_published_data_is_sanitized_and_session_independent(self):
        cfg=json.loads((ROOT/"config.json").read_text()); rows,_=canonicalize([{"Data":"01/08/2026","Vendedor":"Ana Silva","Nome":"NEOENERGIA CELPE","Telefone":"999","Matricula":"ABC"}],cfg); configured=prepare_config(cfg,rows,8,2026)
        with tempfile.TemporaryDirectory() as tmp:
            old=app.PUBLISHED_PATH; app.PUBLISHED_PATH=Path(tmp)/"dados.json"
            try:
                save_published(rows,configured,"relatorio.xlsx",datetime(2026,8,22,11,30)); loaded,_,metadata=load_published(cfg)
                payload=app.PUBLISHED_PATH.read_text(); self.assertNotIn("Telefone",payload); self.assertNotIn("Matricula",payload)
                self.assertEqual(rows,loaded); self.assertEqual("2026-08-22T11:30:00",metadata["atualizado_em"])
            finally: app.PUBLISHED_PATH=old

if __name__=="__main__": unittest.main()
