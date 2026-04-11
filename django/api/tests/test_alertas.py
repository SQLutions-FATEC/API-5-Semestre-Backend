from datetime import date, timedelta
from decimal import Decimal
from django.test import TestCase, Client
from api.models import (
    DimData, DimPrograma, DimProjeto, DimMaterial, 
    DimSolicitacao, FatoCompra, DimFornecedor
)

class ProjetoAlertasViewTest(TestCase):
    def setUp(self):
        self.client = Client()

        hoje = date.today()
        passado_20d = hoje - timedelta(days=20)
        passado_25d = hoje - timedelta(days=25)
        passado_45d = hoje - timedelta(days=45)

        self.data_hoje = DimData.objects.create(dia=hoje.day, mes=hoje.month, ano=hoje.year)
        self.data_passado_20d = DimData.objects.create(dia=passado_20d.day, mes=passado_20d.month, ano=passado_20d.year)
        self.data_passado_25d = DimData.objects.create(dia=passado_25d.day, mes=passado_25d.month, ano=passado_25d.year)
        self.data_passado_45d = DimData.objects.create(dia=passado_45d.day, mes=passado_45d.month, ano=passado_45d.year)

        self.programa = DimPrograma.objects.create(
            codigo_programa="PROG03", nome_programa="Prog 3",
            gerente_programa="Gerente P3", gerente_tecnico="Gerente T3",
            data_inicio=self.data_passado_45d, data_fim_prevista=self.data_hoje, status="Ativo"
        )

        self.projeto_com_alertas = DimProjeto.objects.create(
            codigo_projeto="PRJ20", nome_projeto="Projeto com Alertas",
            programa=self.programa, responsavel="Resp Alertas",
            custo_hora=Decimal('100.00'),
            data_inicio=self.data_passado_45d, data_fim_prevista=self.data_hoje, status="Ativo"
        )

        self.projeto_sem_alertas = DimProjeto.objects.create(
            codigo_projeto="PRJ21", nome_projeto="Projeto Sem Alertas",
            programa=self.programa, responsavel="Resp Sem Alertas",
            custo_hora=Decimal('100.00'),
            data_inicio=self.data_passado_45d, data_fim_prevista=self.data_hoje, status="Ativo"
        )

        self.material_ativo = DimMaterial.objects.create(
            codigo_material="M20", descricao="Material Ativo", categoria="Cat",
            fabricante="Fab", custo_estimado=Decimal('50.00'), status="Ativo"
        )
        self.material_obsoleto = DimMaterial.objects.create(
            codigo_material="M21", descricao="Material Obsoleto", categoria="Cat",
            fabricante="Fab", custo_estimado=Decimal('30.00'), status="Obsoleto"
        )

        self.fornecedor = DimFornecedor.objects.create(
            codigo_fornecedor="F20", razao_social="Fornecedor Teste", cidade="Cid",
            estado="Est", categoria="Cat", status="Ativo"
        )

        self.solicitacao_atrasada = DimSolicitacao.objects.create(
            numero_solicitacao="S20", projeto=self.projeto_com_alertas, material=self.material_ativo,
            quantidade=5, data_solicitacao=self.data_passado_45d, prioridade="Normal", status="Ativo"
        )
        FatoCompra.objects.create(
            numero_pedido="PED20", valor_total=Decimal('250.00'), status="Aberto",
            solicitacao=self.solicitacao_atrasada, fornecedor=self.fornecedor,
            data_pedido=self.data_passado_45d, data_previsao_entrega=self.data_passado_20d
        )

        self.solicitacao_prioritaria = DimSolicitacao.objects.create(
            numero_solicitacao="S21", projeto=self.projeto_com_alertas, material=self.material_ativo,
            quantidade=3, data_solicitacao=self.data_passado_25d, prioridade="Alta", status="Ativo"
        )
        FatoCompra.objects.create(
            numero_pedido="PED21", valor_total=Decimal('150.00'), status="Enviado",
            solicitacao=self.solicitacao_prioritaria, fornecedor=self.fornecedor,
            data_pedido=self.data_passado_25d, data_previsao_entrega=self.data_hoje
        )

        self.solicitacao_obsoleto = DimSolicitacao.objects.create(
            numero_solicitacao="S22", projeto=self.projeto_com_alertas, material=self.material_obsoleto,
            quantidade=2, data_solicitacao=self.data_passado_20d, prioridade="Normal", status="Ativo"
        )
        FatoCompra.objects.create(
            numero_pedido="PED22", valor_total=Decimal('60.00'), status="Aberto",
            solicitacao=self.solicitacao_obsoleto, fornecedor=self.fornecedor,
            data_pedido=self.data_passado_20d, data_previsao_entrega=self.data_hoje
        )

        self.solicitacao_concluida = DimSolicitacao.objects.create(
            numero_solicitacao="S23", projeto=self.projeto_com_alertas, material=self.material_ativo,
            quantidade=1, data_solicitacao=self.data_passado_45d, prioridade="Normal", status="Ativo"
        )
        FatoCompra.objects.create(
            numero_pedido="PED23", valor_total=Decimal('50.00'), status="Concluída",
            solicitacao=self.solicitacao_concluida, fornecedor=self.fornecedor,
            data_pedido=self.data_passado_45d, data_previsao_entrega=self.data_passado_45d
        )

    def test_alertas_success_with_data(self):
        response = self.client.get(f'/api/projetos/criticos/{self.projeto_com_alertas.codigo_projeto}')
        self.assertEqual(response.status_code, 200)

        data = response.json()
        alertas = data['alertas_criticos']

        self.assertEqual(len(alertas['pedidos_atrasados']), 1)
        self.assertEqual(alertas['pedidos_atrasados'][0]['numero_pedido'], 'PED20')

        self.assertEqual(len(alertas['pedidos_prioritarios_pendentes']), 1)
        self.assertEqual(alertas['pedidos_prioritarios_pendentes'][0]['numero_pedido'], 'PED21')

        self.assertEqual(len(alertas['materiais_obsoletos']), 1)
        self.assertTrue(alertas['materiais_obsoletos'][0]['vinculado_ao_projeto'])
        self.assertTrue(alertas['materiais_obsoletos'][0]['pedido_recente'])

    def test_alertas_success_without_data(self):
        response = self.client.get(f'/api/projetos/criticos/{self.projeto_sem_alertas.codigo_projeto}')
        self.assertEqual(response.status_code, 200)

        data = response.json()
        alertas = data['alertas_criticos']

        self.assertEqual(alertas['pedidos_atrasados'], [])
        self.assertEqual(alertas['pedidos_prioritarios_pendentes'], [])
        self.assertEqual(alertas['materiais_obsoletos'], [])

    def test_alertas_not_found(self):
        response = self.client.get('/api/projetos/criticos/CODIGO-INVALIDO')
        self.assertEqual(response.status_code, 404)

    def test_alertas_wrong_method(self):
        response = self.client.post(f'/api/projetos/criticos/{self.projeto_com_alertas.codigo_projeto}')
        self.assertEqual(response.status_code, 405)