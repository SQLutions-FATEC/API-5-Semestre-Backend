from django.test import TestCase, Client
from api.models import DimData, DimPrograma, DimProjeto

class ProjetoDashboardViewTest(TestCase):
    def setUp(self):
        # 1. Create dummy data so our view has something to query
        self.client = Client()
        self.data = DimData.objects.create(dia=1, mes=1, ano=2024)
        
        self.programa = DimPrograma.objects.create(
            codigo_programa="PROG-TESTE",
            nome_programa="Programa Teste",
            gerente_programa="João",
            gerente_tecnico="Maria",
            data_inicio=self.data,
            data_fim_prevista=self.data,
            status="Ativo"
        )
        
        self.projeto = DimProjeto.objects.create(
            codigo_projeto="PRJ-TESTE",
            nome_projeto="Projeto de Teste",
            programa=self.programa,
            responsavel="Carlos",
            custo_hora=100.00,
            data_inicio=self.data,
            data_fim_prevista=self.data,
            status="Ativo"
        )

    def test_projeto_dashboard_api_success(self):
        # 2. Simulate a frontend GET request to the URL
        response = self.client.get(f'/api/projetos/{self.projeto.codigo_projeto}/')
        
        # 3. Assert the request was successful
        self.assertEqual(response.status_code, 200)
        
        # 4. Assert the JSON contains the correct project data
        json_data = response.json()
        self.assertEqual(json_data['projeto']['codigo'], "PRJ-TESTE")
        self.assertEqual(json_data['projeto']['nome'], "Projeto de Teste")

    def test_projeto_dashboard_api_not_found(self):
        # Test that a bad code returns a 404
        response = self.client.get('/api/projetos/CODIGO-FALSO/')
        self.assertEqual(response.status_code, 404)
