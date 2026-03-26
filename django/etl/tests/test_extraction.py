import os
import pandas as pd
from django.test import TestCase
from django.core.management import call_command
from api.models import DimPrograma, DimProjeto, DimTarefa, FatoCompra
from etl.extractors.base import CSV_BASE_PATH

class ETLIntegrationTest(TestCase):
    """
    Testes de integração para validar o fluxo CSV -> DW.
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

    def test_run_extraction_command(self):
        """
        Testa se o comando 'run_extraction' popula o banco corretamente.
        """
        # 1. Executa o comando de gerenciamento que criamos
        call_command('run_extraction')

        # 2. Valida DimPrograma (Dimensão Base)
        df_programas = pd.read_csv(os.path.join(CSV_BASE_PATH, 'programas.csv'))
        self.assertEqual(DimPrograma.objects.count(), len(df_programas))

        # 3. Valida FatoCompra (Fato com FKs)
        df_pedidos = pd.read_csv(os.path.join(CSV_BASE_PATH, 'pedidos_compra.csv'))
        self.assertEqual(FatoCompra.objects.count(), len(df_pedidos))

        # 4. Valida um dado específico para garantir que o mapeamento de colunas está OK
        #exemplo: Verificar se o primeiro pedido do CSV bate com o banco
        primeiro_pedido_csv = df_pedidos.iloc[0]['numero_pedido']
        primeiro_pedido_db = FatoCompra.objects.get(id=df_pedidos.iloc[0]['id'])
        self.assertEqual(primeiro_pedido_db.numero_pedido, primeiro_pedido_csv)

    def test_integrity_on_empty_csv(self):
        """
        Opcional: Garante que o loader lida com exclusão prévia (delete())
        rodando o comando duas vezes.
        """
        call_command('run_extraction')
        count_first_run = DimProjeto.objects.count()
        
        call_command('run_extraction') #deve truncar e carregar de novo
        self.assertEqual(DimProjeto.objects.count(), count_first_run)