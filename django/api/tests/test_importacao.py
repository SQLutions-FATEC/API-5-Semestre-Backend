from django.test import TestCase, Client
from django.core.files.uploadedfile import SimpleUploadedFile


class ImportacaoApiTest(TestCase):

    def setUp(self):
        self.client = Client()

    def test_upload_sem_arquivo(self):
        response = self.client.post("/api/importar_dados/")
        self.assertEqual(response.status_code, 400)

    def test_upload_arquivo_invalido(self):
        arquivo = SimpleUploadedFile(
            "teste.txt", b"arquivo invalido", content_type="text/plain"
        )

        response = self.client.post("/api/importar_dados/", {"file": arquivo})

        self.assertEqual(response.status_code, 400)

    def test_upload_csv_invalido(self):
        arquivo = SimpleUploadedFile(
            "teste.csv", b"conteudo invalido", content_type="text/csv"
        )

        response = self.client.post("/api/importar_dados/", {"file": arquivo})

        self.assertEqual(response.status_code, 400)

    def test_upload_csv(self):
        csv_content = """codigo_material,descricao,categoria,fabricante,custo_estimado,status
MAT001,Parafuso,Fixacao,Tramontina,10.50,Ativo"""

        arquivo = SimpleUploadedFile(
            "teste.csv", csv_content.encode("utf-8"), content_type="text/csv"
        )

        response = self.client.post("/api/importar_dados/", {"file": arquivo})

        self.assertEqual(response.status_code, 200)
