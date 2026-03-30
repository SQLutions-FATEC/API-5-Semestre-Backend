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


class ProjetoTarefasTimesheetViewTest(TestCase):
    def setUp(self):
        self.client = Client()

        self.data_1 = DimData.objects.create(dia=1, mes=1, ano=2024)
        self.data_2 = DimData.objects.create(dia=2, mes=1, ano=2024)

        self.programa = DimPrograma.objects.create(
            codigo_programa="PROG02", nome_programa="Prog 2",
            gerente_programa="Gerente P2", gerente_tecnico="Gerente T2",
            data_inicio=self.data_1, data_fim_prevista=self.data_2, status="Ativo"
        )

        self.projeto_com_dados = DimProjeto.objects.create(
            codigo_projeto="PRJ10", nome_projeto="Projeto Timesheet",
            programa=self.programa, responsavel="Resp TS",
            custo_hora=Decimal('120.00'),
            data_inicio=self.data_1, data_fim_prevista=self.data_2, status="Ativo"
        )

        self.projeto_vazio = DimProjeto.objects.create(
            codigo_projeto="PRJ11", nome_projeto="Projeto Sem Tarefas",
            programa=self.programa, responsavel="Resp Sem Dados",
            custo_hora=Decimal('80.00'),
            data_inicio=self.data_1, data_fim_prevista=self.data_2, status="Ativo"
        )

        self.tarefa_1 = DimTarefa.objects.create(
            codigo_tarefa="TS01", projeto=self.projeto_com_dados, titulo="Planejamento",
            responsavel="Ana", estimativa=8, data_inicio=self.data_1,
            data_fim_prevista=self.data_2, status="Ativo"
        )
        self.tarefa_2 = DimTarefa.objects.create(
            codigo_tarefa="TS02", projeto=self.projeto_com_dados, titulo="Execucao",
            responsavel="Bruno", estimativa=16, data_inicio=self.data_1,
            data_fim_prevista=self.data_2, status="Ativo"
        )

        FatoTarefa.objects.create(
            usuario="ana", horas_trabalhadas=2.25, tarefa=self.tarefa_1, data=self.data_1
        )
        FatoTarefa.objects.create(
            usuario="ana", horas_trabalhadas=1.75, tarefa=self.tarefa_1, data=self.data_2
        )
        FatoTarefa.objects.create(
            usuario="bruno", horas_trabalhadas=3.0, tarefa=self.tarefa_2, data=self.data_2
        )

    def test_timesheet_success_with_data(self):
        """Covers tasks aggregation and daily hours evolution with related data"""
        response = self.client.get(f'/api/projetos/tarefas/{self.projeto_com_dados.codigo_projeto}')
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data['projeto']['codigo'], self.projeto_com_dados.codigo_projeto)
        self.assertEqual(data['projeto']['nome'], self.projeto_com_dados.nome_projeto)

        self.assertEqual(len(data['tarefas']), 2)

        tarefa_1 = data['tarefas'][0]
        tarefa_2 = data['tarefas'][1]

        self.assertEqual(tarefa_1['codigo'], 'TS01')
        self.assertEqual(tarefa_1['total_horas_trabalhadas'], 4.0)
        self.assertEqual(tarefa_2['codigo'], 'TS02')
        self.assertEqual(tarefa_2['total_horas_trabalhadas'], 3.0)

        self.assertEqual(data['evolucao_horas']['2024-01-01'], 2.25)
        self.assertEqual(data['evolucao_horas']['2024-01-02'], 4.75)

    def test_timesheet_success_without_data(self):
        """Covers empty tasks and evolution when project has no related task/time data"""
        response = self.client.get(f'/api/projetos/tarefas/{self.projeto_vazio.codigo_projeto}')
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data['projeto']['codigo'], self.projeto_vazio.codigo_projeto)
        self.assertEqual(data['tarefas'], [])
        self.assertEqual(data['evolucao_horas'], {})

    def test_timesheet_not_found(self):
        """Covers the get_object_or_404 failure branch"""
        response = self.client.get('/api/projetos/tarefas/CODIGO-INVALIDO')
        self.assertEqual(response.status_code, 404)

    def test_timesheet_wrong_method(self):
        """Covers the @require_GET decorator blocking POST requests"""
        response = self.client.post(f'/api/projetos/tarefas/{self.projeto_com_dados.codigo_projeto}')
        self.assertEqual(response.status_code, 405)


class ProjetoAlertasViewTest(TestCase):
    def setUp(self):
        self.client = Client()

        # Base dates: data_atual will be today
        self.data_passado_45d = DimData.objects.create(dia=14, mes=2, ano=2026)  # 45 dias atrás
        self.data_passado_25d = DimData.objects.create(dia=7, mes=3, ano=2026)   # 25 dias atrás (dentro de 30d)
        self.data_passado_20d = DimData.objects.create(dia=10, mes=3, ano=2026)  # 20 dias atrás (dentro de 30d)
        self.data_hoje = DimData.objects.create(dia=30, mes=3, ano=2026)         # Hoje

        self.programa = DimPrograma.objects.create(
            codigo_programa="PROG03", nome_programa="Prog 3",
            gerente_programa="Gerente P3", gerente_tecnico="Gerente T3",
            data_inicio=self.data_passado_45d, data_fim_prevista=self.data_hoje, status="Ativo"
        )

        # Project WITH alerts
        self.projeto_com_alertas = DimProjeto.objects.create(
            codigo_projeto="PRJ20", nome_projeto="Projeto com Alertas",
            programa=self.programa, responsavel="Resp Alertas",
            custo_hora=Decimal('100.00'),
            data_inicio=self.data_passado_45d, data_fim_prevista=self.data_hoje, status="Ativo"
        )

        # Project WITHOUT alerts
        self.projeto_sem_alertas = DimProjeto.objects.create(
            codigo_projeto="PRJ21", nome_projeto="Projeto Sem Alertas",
            programa=self.programa, responsavel="Resp Sem Alertas",
            custo_hora=Decimal('100.00'),
            data_inicio=self.data_passado_45d, data_fim_prevista=self.data_hoje, status="Ativo"
        )

        # Create materials
        self.material_ativo = DimMaterial.objects.create(
            codigo_material="M20", descricao="Material Ativo", categoria="Cat",
            fabricante="Fab", custo_estimado=Decimal('50.00'), status="Ativo"
        )
        self.material_obsoleto = DimMaterial.objects.create(
            codigo_material="M21", descricao="Material Obsoleto", categoria="Cat",
            fabricante="Fab", custo_estimado=Decimal('30.00'), status="Obsoleto"
        )

        # Create supplier
        self.fornecedor = DimFornecedor.objects.create(
            codigo_fornecedor="F20", razao_social="Fornecedor Teste", cidade="Cid",
            estado="Est", categoria="Cat", status="Ativo"
        )

        # Create requests and purchases with alerts
        # 1. Pedido ATRASADO
        self.solicitacao_atrasada = DimSolicitacao.objects.create(
            numero_solicitacao="S20", projeto=self.projeto_com_alertas, material=self.material_ativo,
            quantidade=5, data_solicitacao=self.data_passado_45d, prioridade="Normal", status="Ativo"
        )
        FatoCompra.objects.create(
            numero_pedido="PED20", valor_total=Decimal('250.00'), status="Aberto",
            solicitacao=self.solicitacao_atrasada, fornecedor=self.fornecedor,
            data_pedido=self.data_passado_45d, data_previsao_entrega=self.data_passado_20d  # Atrasado
        )

        # 2. Pedido PRIORITÁRIO PENDENTE
        self.solicitacao_prioritaria = DimSolicitacao.objects.create(
            numero_solicitacao="S21", projeto=self.projeto_com_alertas, material=self.material_ativo,
            quantidade=3, data_solicitacao=self.data_passado_25d, prioridade="Alta", status="Ativo"
        )
        FatoCompra.objects.create(
            numero_pedido="PED21", valor_total=Decimal('150.00'), status="Enviado",
            solicitacao=self.solicitacao_prioritaria, fornecedor=self.fornecedor,
            data_pedido=self.data_passado_25d, data_previsao_entrega=self.data_hoje
        )

        # 3. Material OBSOLETO vinculado RECENTEMENTE
        self.solicitacao_obsoleto = DimSolicitacao.objects.create(
            numero_solicitacao="S22", projeto=self.projeto_com_alertas, material=self.material_obsoleto,
            quantidade=2, data_solicitacao=self.data_passado_20d, prioridade="Normal", status="Ativo"
        )
        FatoCompra.objects.create(
            numero_pedido="PED22", valor_total=Decimal('60.00'), status="Aberto",
            solicitacao=self.solicitacao_obsoleto, fornecedor=self.fornecedor,
            data_pedido=self.data_passado_20d, data_previsao_entrega=self.data_hoje
        )

        # 4. Pedido CONCLUÍDO (não deve aparecer em atrasados)
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
        """Covers all alert branches with related data (delayed orders, priority pending, obsolete materials)"""
        response = self.client.get(f'/api/projetos/criticos/{self.projeto_com_alertas.codigo_projeto}')
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data['projeto']['codigo'], self.projeto_com_alertas.codigo_projeto)
        self.assertEqual(data['projeto']['nome'], self.projeto_com_alertas.nome_projeto)

        alertas = data['alertas_criticos']

        # Verify delayed orders (PED20 is delayed)
        self.assertEqual(len(alertas['pedidos_atrasados']), 1)
        pedido_atrasado = alertas['pedidos_atrasados'][0]
        self.assertEqual(pedido_atrasado['numero_pedido'], 'PED20')
        self.assertEqual(pedido_atrasado['status'], 'Aberto')
        self.assertGreater(pedido_atrasado['dias_atraso'], 0)

        # Verify priority pending orders (PED21 is priority + open/sent)
        self.assertEqual(len(alertas['pedidos_prioritarios_pendentes']), 1)
        pedido_prioritario = alertas['pedidos_prioritarios_pendentes'][0]
        self.assertEqual(pedido_prioritario['numero_pedido'], 'PED21')
        self.assertEqual(pedido_prioritario['prioridade'], 'Alta')
        self.assertEqual(pedido_prioritario['status'], 'Enviado')

        # Verify obsolete materials (M21 is obsolete and recently ordered via PED22)
        self.assertEqual(len(alertas['materiais_obsoletos']), 1)
        material_obsoleto = alertas['materiais_obsoletos'][0]
        self.assertEqual(material_obsoleto['codigo_material'], 'M21')
        self.assertEqual(material_obsoleto['status'], 'Obsoleto')
        self.assertTrue(material_obsoleto['vinculado_ao_projeto'])
        self.assertTrue(material_obsoleto['pedido_recente'])

    def test_alertas_success_without_data(self):
        """Covers empty alerts when project has no related purchases"""
        response = self.client.get(f'/api/projetos/criticos/{self.projeto_sem_alertas.codigo_projeto}')
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data['projeto']['codigo'], self.projeto_sem_alertas.codigo_projeto)
        alertas = data['alertas_criticos']

        self.assertEqual(alertas['pedidos_atrasados'], [])
        self.assertEqual(alertas['pedidos_prioritarios_pendentes'], [])
        self.assertEqual(alertas['materiais_obsoletos'], [])

    def test_alertas_not_found(self):
        """Covers the get_object_or_404 failure branch"""
        response = self.client.get('/api/projetos/criticos/CODIGO-INVALIDO')
        self.assertEqual(response.status_code, 404)

    def test_alertas_wrong_method(self):
        """Covers the @require_GET decorator blocking POST requests"""
        response = self.client.post(f'/api/projetos/criticos/{self.projeto_com_alertas.codigo_projeto}')
        self.assertEqual(response.status_code, 405)
