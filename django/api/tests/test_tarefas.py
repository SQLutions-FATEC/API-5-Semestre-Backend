from decimal import Decimal
from django.test import TestCase, Client
from api.models import DimData, DimPrograma, DimProjeto, DimTarefa, FatoTarefa

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
        response = self.client.get(f'/api/projetos/tarefas/{self.projeto_com_dados.codigo_projeto}')
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data['projeto']['codigo'], self.projeto_com_dados.codigo_projeto)
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
        response = self.client.get(f'/api/projetos/tarefas/{self.projeto_vazio.codigo_projeto}')
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data['tarefas'], [])
        self.assertEqual(data['evolucao_horas'], {})

    def test_timesheet_not_found(self):
        response = self.client.get('/api/projetos/tarefas/CODIGO-INVALIDO')
        self.assertEqual(response.status_code, 404)

    def test_timesheet_wrong_method(self):
        response = self.client.post(f'/api/projetos/tarefas/{self.projeto_com_dados.codigo_projeto}')
        self.assertEqual(response.status_code, 405)