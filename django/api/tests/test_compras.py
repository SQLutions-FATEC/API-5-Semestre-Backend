from decimal import Decimal
from django.test import TestCase, Client
from api.models import (
    DimData, DimPrograma, DimProjeto, 
    DimMaterial, DimSolicitacao, FatoCompra, DimFornecedor
)

class ComprasProjetoViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        
        self.data_emissao = DimData.objects.create(dia=1, mes=1, ano=2024)
        self.data_previsao_1 = DimData.objects.create(dia=11, mes=1, ano=2024)
        self.data_previsao_2 = DimData.objects.create(dia=21, mes=1, ano=2024)
        
        self.programa = DimPrograma.objects.create(
            codigo_programa="PROG01", nome_programa="Prog 1",
            gerente_programa="Gerente P", gerente_tecnico="Gerente T",
            data_inicio=self.data_emissao, data_fim_prevista=self.data_emissao, status="Ativo"
        )
        
        self.projeto_com_dados = DimProjeto.objects.create(
            codigo_projeto="PRJ01", nome_projeto="Proj 1",
            programa=self.programa, responsavel="Resp",
            custo_hora=Decimal('100.00'),
            data_inicio=self.data_emissao, data_fim_prevista=self.data_emissao, status="Ativo"
        )

        self.projeto_vazio = DimProjeto.objects.create(
            codigo_projeto="PRJ02", nome_projeto="Proj 2",
            programa=self.programa, responsavel="Resp 2",
            custo_hora=Decimal('50.00'),
            data_inicio=self.data_emissao, data_fim_prevista=self.data_emissao, status="Ativo"
        )

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
        
        FatoCompra.objects.create(
            numero_pedido="PED01", valor_total=Decimal('150.50'), status="Entregue",
            solicitacao=self.solicitacao, fornecedor=self.fornecedor,
            data_pedido=self.data_emissao, data_previsao_entrega=self.data_previsao_1
        )

        FatoCompra.objects.create(
            numero_pedido="PED02", valor_total=Decimal('300.00'), status="Pendente",
            solicitacao=self.solicitacao, fornecedor=self.fornecedor,
            data_pedido=self.data_emissao, data_previsao_entrega=self.data_previsao_2
        )

    def test_compras_success_with_data(self):
        response = self.client.get(f'/api/projetos/{self.projeto_com_dados.codigo_projeto}/compras/')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data['tempo_medio_entrega_dias'], 15.0)
        self.assertEqual(len(data['pedidos']), 2)
        
        pedido_1 = next(p for p in data['pedidos'] if p['numero'] == 'PED01')
        self.assertEqual(pedido_1['fornecedor'], "Forn Teste")
        self.assertEqual(pedido_1['centro_custo'], "Proj 1")
        self.assertEqual(pedido_1['status'], "Entregue")
        self.assertEqual(pedido_1['dias_previstos_entrega'], 10)

    def test_compras_success_without_data(self):
        response = self.client.get(f'/api/projetos/{self.projeto_vazio.codigo_projeto}/compras/')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data['tempo_medio_entrega_dias'], 0.0)
        self.assertEqual(data['pedidos'], [])

    def test_compras_not_found(self):
        response = self.client.get('/api/projetos/CODIGO-INVALIDO/compras/')
        self.assertEqual(response.status_code, 404)

    def test_compras_wrong_method(self):
        response = self.client.post(f'/api/projetos/{self.projeto_com_dados.codigo_projeto}/compras/')
        self.assertEqual(response.status_code, 405)