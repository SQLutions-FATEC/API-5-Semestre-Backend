from decimal import Decimal
from django.test import TestCase, Client
from api.models import (
    DimData, DimPrograma, DimProjeto, DimTarefa, FatoTarefa,
    DimMaterial, DimSolicitacao, FatoCompra, DimFornecedor
)

class ProjetoDashboardViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        
        # 1. Base Dimensions
        self.data = DimData.objects.create(dia=1, mes=1, ano=2024)
        self.programa = DimPrograma.objects.create(
            codigo_programa="PROG01", nome_programa="Prog 1",
            gerente_programa="Gerente P", gerente_tecnico="Gerente T",
            data_inicio=self.data, data_fim_prevista=self.data, status="Ativo"
        )
        
        # 2. Project WITH data (for the happy path)
        self.projeto_com_dados = DimProjeto.objects.create(
            codigo_projeto="PRJ01", nome_projeto="Proj 1",
            programa=self.programa, responsavel="Resp",
            custo_hora=Decimal('100.00'),
            data_inicio=self.data, data_fim_prevista=self.data, status="Ativo"
        )

        # 3. Project WITHOUT data (for the 'or 0.0' fallback path)
        self.projeto_vazio = DimProjeto.objects.create(
            codigo_projeto="PRJ02", nome_projeto="Proj 2",
            programa=self.programa, responsavel="Resp 2",
            custo_hora=Decimal('50.00'),
            data_inicio=self.data, data_fim_prevista=self.data, status="Ativo"
        )

        # 4. Create tasks and worked hours for PRJ01
        self.tarefa = DimTarefa.objects.create(
            codigo_tarefa="T01", projeto=self.projeto_com_dados, titulo="Tarefa 1",
            responsavel="Resp", estimativa=10, data_inicio=self.data,
            data_fim_prevista=self.data, status="Ativo"
        )
        FatoTarefa.objects.create(
            usuario="User", horas_trabalhadas=5.5, tarefa=self.tarefa, data=self.data
        )

        # 5. Create materials, requests, and purchases for PRJ01
        self.material = DimMaterial.objects.create(
            codigo_material="M01", descricao="Mat 1", categoria="Cat",
            fabricante="Fab", custo_estimado=Decimal('10.00'), status="Ativo"
        )
        self.fornecedor = DimFornecedor.objects.create(
            codigo_fornecedor="F01", razao_social="Forn", cidade="Cid",
            estado="Est", categoria="Cat", status="Ativo"
        )
        self.solicitacao = DimSolicitacao.objects.create(
            numero_solicitacao="S01", projeto=self.projeto_com_dados, material=self.material,
            quantidade=1, data_solicitacao=self.data, prioridade="Alta", status="Ativo"
        )
        FatoCompra.objects.create(
            numero_pedido="PED01", valor_total=Decimal('150.50'), status="Ativo",
            solicitacao=self.solicitacao, fornecedor=self.fornecedor,
            data_pedido=self.data, data_previsao_entrega=self.data
        )

    def test_dashboard_success_with_data(self):
        """Covers the math logic when Fato tables have related data"""
        response = self.client.get(f'/api/projetos/{self.projeto_com_dados.codigo_projeto}/')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        # Math verification: 5.5 hours * 100.00 cost/hr = 550.00 labor cost.
        # Materials = 150.50. Total = 550.00 + 150.50 = 700.50.
        self.assertEqual(data['financeiro']['total_horas_trabalhadas'], 5.5)
        self.assertEqual(data['financeiro']['custo_total_materiais'], 150.5)
        self.assertEqual(data['financeiro']['custo_total_projeto'], 700.5)

    def test_dashboard_success_without_data(self):
        """Covers the `or 0.0` fallbacks when Fato tables are empty"""
        response = self.client.get(f'/api/projetos/{self.projeto_vazio.codigo_projeto}/')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data['financeiro']['total_horas_trabalhadas'], 0.0)
        self.assertEqual(data['financeiro']['custo_total_materiais'], 0.0)
        self.assertEqual(data['financeiro']['custo_total_projeto'], 0.0)

    def test_dashboard_not_found(self):
        """Covers the get_object_or_404 failure branch"""
        response = self.client.get('/api/projetos/CODIGO-INVALIDO/')
        self.assertEqual(response.status_code, 404)

    def test_dashboard_wrong_method(self):
        """Covers the @require_GET decorator blocking POST requests"""
        response = self.client.post(f'/api/projetos/{self.projeto_com_dados.codigo_projeto}/')
        self.assertEqual(response.status_code, 405) # 405 Method Not Allowed

from decimal import Decimal
from django.test import TestCase, Client
from api.models import (
    DimData, DimPrograma, DimProjeto, 
    DimMaterial, DimSolicitacao, FatoCompra, DimFornecedor
)

class ComprasProjetoViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        
        # 1. Base Dimensions (We need different dates to calculate delivery days)
        self.data_emissao = DimData.objects.create(dia=1, mes=1, ano=2024)
        self.data_previsao_1 = DimData.objects.create(dia=11, mes=1, ano=2024) # 10 days later
        self.data_previsao_2 = DimData.objects.create(dia=21, mes=1, ano=2024) # 20 days later
        
        self.programa = DimPrograma.objects.create(
            codigo_programa="PROG01", nome_programa="Prog 1",
            gerente_programa="Gerente P", gerente_tecnico="Gerente T",
            data_inicio=self.data_emissao, data_fim_prevista=self.data_emissao, status="Ativo"
        )
        
        # 2. Project WITH data (for the happy path)
        self.projeto_com_dados = DimProjeto.objects.create(
            codigo_projeto="PRJ01", nome_projeto="Proj 1",
            programa=self.programa, responsavel="Resp",
            custo_hora=Decimal('100.00'),
            data_inicio=self.data_emissao, data_fim_prevista=self.data_emissao, status="Ativo"
        )

        # 3. Project WITHOUT data (for the empty list/0 fallback path)
        self.projeto_vazio = DimProjeto.objects.create(
            codigo_projeto="PRJ02", nome_projeto="Proj 2",
            programa=self.programa, responsavel="Resp 2",
            custo_hora=Decimal('50.00'),
            data_inicio=self.data_emissao, data_fim_prevista=self.data_emissao, status="Ativo"
        )

        # 4. Create materials, requests, and purchases for PRJ01
        self.material = DimMaterial.objects.create(
            codigo_material="M01", descricao="Mat 1", categoria="Cat",
            fabricante="Fab", custo_estimado=Decimal('10.00'), status="Ativo"
        )
        self.fornecedor = DimFornecedor.objects.create(
            codigo_fornecedor="F01", razao_social="Forn Teste", cidade="Cid",
            estado="Est", categoria="Cat", status="Ativo"
        )
        self.solicitacao = DimSolicitacao.objects.create(
            numero_solicitacao="S01", projeto=self.projeto_com_dados, material=self.material,
            quantidade=2, data_solicitacao=self.data_emissao, prioridade="Alta", status="Ativo"
        )
        
        # Creating Order 1 (Takes 10 days)
        FatoCompra.objects.create(
            numero_pedido="PED01", valor_total=Decimal('150.50'), status="Entregue",
            solicitacao=self.solicitacao, fornecedor=self.fornecedor,
            data_pedido=self.data_emissao, data_previsao_entrega=self.data_previsao_1
        )

        # Creating Order 2 (Takes 20 days)
        FatoCompra.objects.create(
            numero_pedido="PED02", valor_total=Decimal('300.00'), status="Pendente",
            solicitacao=self.solicitacao, fornecedor=self.fornecedor,
            data_pedido=self.data_emissao, data_previsao_entrega=self.data_previsao_2
        )

    def test_compras_success_with_data(self):
        """Covers the math logic when Fato tables have related data"""
        response = self.client.get(f'/api/projetos/{self.projeto_com_dados.codigo_projeto}/compras/')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        
        # Math verification: 
        # PED01: 2024-01-11 - 2024-01-01 = 10 days
        # PED02: 2024-01-21 - 2024-01-01 = 20 days
        # Average = (10 + 20) / 2 = 15.0 days
        self.assertEqual(data['tempo_medio_entrega_dias'], 15.0)
        self.assertEqual(len(data['pedidos']), 2)
        
        # Fetching PED01 to check columns
        pedido_1 = next(p for p in data['pedidos'] if p['numero'] == 'PED01')
        self.assertEqual(pedido_1['fornecedor'], "Forn Teste")
        self.assertEqual(pedido_1['centro_custo'], "Proj 1")
        self.assertEqual(pedido_1['status'], "Entregue")
        self.assertEqual(pedido_1['dias_previstos_entrega'], 10)

    def test_compras_success_without_data(self):
        """Covers the empty fallbacks when Fato tables are empty"""
        response = self.client.get(f'/api/projetos/{self.projeto_vazio.codigo_projeto}/compras/')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data['tempo_medio_entrega_dias'], 0.0)
        self.assertEqual(data['pedidos'], []) # Must return an empty list

    