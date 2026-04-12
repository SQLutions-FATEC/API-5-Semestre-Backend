import os
import pandas as pd
import pytest
from django.test import TestCase
from django.core.management import call_command
from api.models import DimPrograma, DimProjeto, DimTarefa, FatoCompra
from etl.extractors.base import CSV_BASE_PATH

class ETLIntegrationTest(TestCase):
    """
    Testes de integração para validar o fluxo CSV -> DW e comandos de carga.
    """

    def setUp(self):
        """
        Verifica se os arquivos CSV existem antes de rodar o comando.
        """
        self.required_files = [
            'programas.csv', 'projetos.csv', 'tarefas_projeto.csv', 
            'pedidos_compra.csv'
        ]
        for f in self.required_files:
            path = os.path.join(CSV_BASE_PATH, f)
            self.assertTrue(os.path.exists(path), f"Arquivo não encontrado: {path}")

    def test_run_etl_command(self):
        """
        Testa se o comando 'run_etl' popula o banco corretamente e aplica transformações.
        """
        # 1. Executa o comando de gerenciamento para rodar o ETL
        call_command('run_etl')

        # 2. Valida DimPrograma (Dimensão Base)
        df_programas = pd.read_csv(os.path.join(CSV_BASE_PATH, 'programas.csv'))
        self.assertEqual(DimPrograma.objects.count(), len(df_programas))

        # 3. Valida FatoCompra (Fato com FKs)
        df_pedidos = pd.read_csv(os.path.join(CSV_BASE_PATH, 'pedidos_compra.csv'))
        self.assertEqual(FatoCompra.objects.count(), len(df_pedidos))

        # 4. Valida um dado específico para garantir que o mapeamento de colunas está OK
        primeiro_pedido_csv = df_pedidos.iloc[0]['numero_pedido']
        primeiro_pedido_db = FatoCompra.objects.get(id=df_pedidos.iloc[0]['id'])
        self.assertEqual(primeiro_pedido_db.numero_pedido, primeiro_pedido_csv)

        # 5. Validação das Transformações (Adicionado conforme Comentário do PR)
        projeto = DimProjeto.objects.first()
        self.assertIsNotNone(projeto, "O banco deveria ter pelo menos um projeto carregado.")
        
        #garante que o status ficou tudo em maiúsculo (standardize_strings)
        self.assertEqual(projeto.status, projeto.status.upper())
        
        #garante que o cálculo de métricas rodou corretamente (calculate_project_metrics)
        self.assertGreaterEqual(projeto.lead_time_dias, 0)

    def test_etl_command_idempotency(self):
        """
        Garante que rodar o comando duas vezes não duplica dados (Idempotência).
        """
        call_command('run_etl')
        count_first_run = DimProjeto.objects.count()
        self.assertGreater(count_first_run, 0, "A tabela não deveria estar vazia após a carga.")
        
        call_command('run_etl') # deve apagar os dados antigos e carregar de novo
        self.assertEqual(DimProjeto.objects.count(), count_first_run)

    def test_seed_db_command(self):
        """
        Testa se o comando 'seed_db' limpa o banco e insere os dados mockados.
        Garante a cobertura do arquivo api/management/commands/seed_db.py.
        """
        # 1. Executa o comando de seed que refatoramos para o Sonar
        call_command('seed_db')

        # 2. Valida se os dados básicos do seed foram inseridos
        # O script de seed insere exatamente 3 programas: MANSUP, MANSUP-ER e MAX12AC
        self.assertEqual(DimPrograma.objects.count(), 3)

        # 3. Valida se a limpeza (delete) está funcionando para garantir idempotência
        # Ao rodar novamente, ele deve deletar os 3 e inserir os mesmos 3 (total continua 3)
        call_command('seed_db')
        self.assertEqual(DimPrograma.objects.count(), 3)

        # 4. Valida um dado específico inserido via constante no Command
        # O programa 1 no seed tem status "Concluído"
        programa = DimPrograma.objects.get(id=1)
        self.assertEqual(programa.status, 'Concluído')