from django.test import TestCase
from django.urls import reverse
from api.models import (
    DimProjeto, DimPrograma, DimMaterial, DimData, DimLocalizacao,
    FatoEstoqueSaldo, DimSolicitacao
)


class SobrasAPITest(TestCase):
    def setUp(self):
        self.data = DimData.objects.create(dia=1, mes=1, ano=2024)

        self.programa = DimPrograma.objects.create(
            codigo_programa="PROG1", nome_programa="Prog 1", status="ATIVO",
            data_inicio=self.data, data_fim_prevista=self.data
        )

        #projeto Alvo (precisa do material)
        self.projeto_alvo = DimProjeto.objects.create(
            codigo_projeto="PRJ100", nome_projeto="Proj Alvo", programa=self.programa,
            status="EM ANDAMENTO", custo_hora=50.0, data_inicio=self.data, data_fim_prevista=self.data
        )

        #projeto com sobra e status válido
        self.projeto_sobra = DimProjeto.objects.create(
            codigo_projeto="PRJ101", nome_projeto="Proj Sobra", programa=self.programa,
            status="CONCLUIDO", custo_hora=50.0, data_inicio=self.data, data_fim_prevista=self.data
        )

        #projeto com sobra mas status inválido (Em Andamento não deve dar sobra)
        self.projeto_ativo = DimProjeto.objects.create(
            codigo_projeto="PRJ102", nome_projeto="Proj Ativo", programa=self.programa,
            status="EM ANDAMENTO", custo_hora=50.0, data_inicio=self.data, data_fim_prevista=self.data
        )

        self.material = DimMaterial.objects.create(
            codigo_material="MAT1", descricao="Cabo", custo_estimado=10.0, status="ATIVO"
        )
        self.localizacao = DimLocalizacao.objects.create(id_localizacao="L1", localizacao="Almoxarifado")

        #estoque das sobras
        FatoEstoqueSaldo.objects.create(
            material=self.material, projeto=self.projeto_sobra, localizacao=self.localizacao,
            quantidade_disponivel=50, valor_total=500.0, data_ultima_atualizacao=self.data
        )
        FatoEstoqueSaldo.objects.create(
            material=self.material, projeto=self.projeto_ativo, localizacao=self.localizacao,
            quantidade_disponivel=100, valor_total=1000.0, data_ultima_atualizacao=self.data
        )

        #solicitação aberta no projeto alvo
        DimSolicitacao.objects.create(
            numero_solicitacao="SOL1", projeto=self.projeto_alvo, material=self.material,
            quantidade=20, status="ABERTO", data_solicitacao=self.data, prioridade="MEDIA"
        )

    def test_regra_filtragem_status_projeto(self):
        """Valida que sobras só vêm de projetos CONCLUÍDOS ou SUSPENSOS"""
        url = reverse('projeto-estoque-sobras', kwargs={'codigo_projeto': 'PRJ100'})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        data = response.json()

        alertas = data.get('alertas_estoque_ocioso', [])
        self.assertEqual(len(alertas), 1)

        sobras = alertas[0]['sobras_detectadas']
        self.assertEqual(len(sobras), 1)

        #só deve apontar para a sobra do projeto CONCLUIDO (PRJ101), ignorando o PRJ102
        self.assertEqual(sobras[0]['projeto_origem_codigo'], 'PRJ101')