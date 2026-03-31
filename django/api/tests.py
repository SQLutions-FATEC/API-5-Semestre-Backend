from datetime import date, timedelta
from decimal import Decimal
from django.test import TestCase, Client
from api.models import (
    DimData, DimPrograma, DimProjeto, DimTarefa, FatoTarefa,
    DimMaterial, DimSolicitacao, FatoCompra, DimFornecedor, FatoEmpenho
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

    def test_compras_not_found(self):
        """Covers the get_object_or_404 failure branch"""
        response = self.client.get('/api/projetos/CODIGO-INVALIDO/compras/')
        self.assertEqual(response.status_code, 404)

    def test_compras_wrong_method(self):
        """Covers the @require_GET decorator blocking POST requests"""
        response = self.client.post(f'/api/projetos/{self.projeto_com_dados.codigo_projeto}/compras/')
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

class ProjetoEmpenhoViewTest(TestCase):
    def setUp(self):
        self.client = Client()

        self.data_1 = DimData.objects.create(dia=1, mes=2, ano=2024)
        self.data_2 = DimData.objects.create(dia=15, mes=3, ano=2024)

        self.programa = DimPrograma.objects.create(
            codigo_programa="PROG03", nome_programa="Prog 3",
            gerente_programa="Gerente P3", gerente_tecnico="Gerente T3",
            data_inicio=self.data_1, data_fim_prevista=self.data_2, status="Ativo"
        )

        self.projeto_com_dados = DimProjeto.objects.create(
            codigo_projeto="PRJ20", nome_projeto="Projeto Empenho",
            programa=self.programa, responsavel="Resp Empenho",
            custo_hora=Decimal('100.00'),
            data_inicio=self.data_1, data_fim_prevista=self.data_2, status="Ativo"
        )

        self.projeto_vazio = DimProjeto.objects.create(
            codigo_projeto="PRJ21", nome_projeto="Projeto Sem Empenho",
            programa=self.programa, responsavel="Resp Sem Dados",
            custo_hora=Decimal('80.00'),
            data_inicio=self.data_1, data_fim_prevista=self.data_2, status="Ativo"
        )

        self.material_1 = DimMaterial.objects.create(
            codigo_material="MAT01", descricao="Cimento", categoria="Construcao",
            fabricante="Votorantim", custo_estimado=Decimal('35.50'), status="Ativo"
        )

        self.material_2 = DimMaterial.objects.create(
            codigo_material="MAT02", descricao="Tinta", categoria="Acabamento",
            fabricante="Suvinil", custo_estimado=Decimal('120.00'), status="Ativo"
        )
        
        self.material_3 = DimMaterial.objects.create(
            codigo_material="MAT03", descricao="Tijolo", categoria="Construcao",
            fabricante="Olaria", custo_estimado=Decimal('1.50'), status="Ativo"
        )

        # Custo MAT01 no dia 1: 10 * 35.50 = 355.00
        FatoEmpenho.objects.create(
            quantidade_empenhada=10, projeto=self.projeto_com_dados, 
            material=self.material_1, data_empenho=self.data_1
        )
        # Custo MAT02 no dia 1: 5 * 120.00 = 600.00
        FatoEmpenho.objects.create(
            quantidade_empenhada=5, projeto=self.projeto_com_dados, 
            material=self.material_2, data_empenho=self.data_1
        )
        # Custo MAT03 no dia 2: 1000 * 1.50 = 1500.00
        FatoEmpenho.objects.create(
            quantidade_empenhada=1000, projeto=self.projeto_com_dados, 
            material=self.material_3, data_empenho=self.data_2
        )

    def test_empenho_success_with_data(self):
        """Testa o calculo dos empenhos quando ha dados factuais."""
        response = self.client.get(f'/api/projetos/{self.projeto_com_dados.codigo_projeto}/empenhos/')
        self.assertEqual(response.status_code, 200)

        data = response.json()
        
        self.assertEqual(data['projeto']['codigo'], self.projeto_com_dados.codigo_projeto)
        
        # Empenho Total = 355.00 + 600.00 + 1500.00 = 2455.00
        self.assertEqual(data['empenho_total'], 2455.00)

        # Empenho por Categoria
        # Construcao: 355.00 (MAT01) + 1500.00 (MAT03) = 1855.00
        # Acabamento: 600.00 (MAT02)
        categorias = {c['categoria']: c['total_custo'] for c in data['empenho_por_categoria']}
        self.assertEqual(categorias['Construcao'], 1855.00)
        self.assertEqual(categorias['Acabamento'], 600.00)

        # Empenho por Material
        materiais = {m['codigo_material']: m for m in data['empenho_por_material']}
        self.assertEqual(materiais['MAT01']['quantidade_total'], 10)
        self.assertEqual(materiais['MAT01']['total_custo'], 355.00)
        
        self.assertEqual(materiais['MAT02']['quantidade_total'], 5)
        self.assertEqual(materiais['MAT02']['total_custo'], 600.00)
        
        self.assertEqual(materiais['MAT03']['quantidade_total'], 1000)
        self.assertEqual(materiais['MAT03']['total_custo'], 1500.00)

        # Empenho por Tempo
        tempo = {t['data']: t for t in data['empenho_por_tempo']}
        
        self.assertEqual(tempo['2024-02-01']['total_custo'], 955.00) # MAT01 + MAT02
        materiais_fev = {m['codigo_material']: m for m in tempo['2024-02-01']['materiais']}
        self.assertEqual(materiais_fev['MAT01']['quantidade'], 10)
        self.assertEqual(materiais_fev['MAT01']['custo_unitario'], 35.50)
        self.assertEqual(materiais_fev['MAT01']['total_custo'], 355.00)
        self.assertEqual(materiais_fev['MAT02']['quantidade'], 5)
        self.assertEqual(materiais_fev['MAT02']['custo_unitario'], 120.00)
        self.assertEqual(materiais_fev['MAT02']['total_custo'], 600.00)
        
        self.assertEqual(tempo['2024-03-15']['total_custo'], 1500.00) # MAT03
        materiais_mar = {m['codigo_material']: m for m in tempo['2024-03-15']['materiais']}
        self.assertEqual(materiais_mar['MAT03']['quantidade'], 1000)
        self.assertEqual(materiais_mar['MAT03']['custo_unitario'], 1.50)
        self.assertEqual(materiais_mar['MAT03']['total_custo'], 1500.00)

    def test_empenho_success_without_data(self):
        """Testa os fallbacks para 0.0 quando nao ha empenhos no projeto."""
        response = self.client.get(f'/api/projetos/{self.projeto_vazio.codigo_projeto}/empenhos/')
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data['projeto']['codigo'], self.projeto_vazio.codigo_projeto)
        self.assertEqual(data['empenho_total'], 0.0)
        self.assertEqual(data['empenho_por_categoria'], [])
        self.assertEqual(data['empenho_por_material'], [])
        self.assertEqual(data['empenho_por_tempo'], [])

    def test_empenho_not_found(self):
        """Testa o status 404 quando o projeto nao existe."""
        response = self.client.get('/api/projetos/CODIGO-INVALIDO/empenhos/')
        self.assertEqual(response.status_code, 404)

    def test_empenho_wrong_method(self):
        """Testa o status 405 caso utilize verbo nao suportado como POST."""
        response = self.client.post(f'/api/projetos/{self.projeto_com_dados.codigo_projeto}/empenhos/')
        self.assertEqual(response.status_code, 405)



class ProjetoAlertasViewTest(TestCase):
    def setUp(self):
        self.client = Client()

        hoje = date.today()
        passado_20d = hoje - timedelta(days=20)
        passado_25d = hoje - timedelta(days=25)
        passado_45d = hoje - timedelta(days=45)

        # Cria os objetos DimData usando as datas calculadas
        self.data_hoje = DimData.objects.create(dia=hoje.day, mes=hoje.month, ano=hoje.year)
        self.data_passado_20d = DimData.objects.create(dia=passado_20d.day, mes=passado_20d.month, ano=passado_20d.year)
        self.data_passado_25d = DimData.objects.create(dia=passado_25d.day, mes=passado_25d.month, ano=passado_25d.year)
        self.data_passado_45d = DimData.objects.create(dia=passado_45d.day, mes=passado_45d.month, ano=passado_45d.year)

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
