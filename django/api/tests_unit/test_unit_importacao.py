"""
Testes unitários para a view importar_dados_api.

Cenários testados:
1. Falha ao não enviar nenhum ficheiro.
2. Falha ao enviar um ficheiro que não tem a extensão .csv.
3. Sucesso na orquestração completa do pipeline ETL.
4. Tratamento adequado de exceções (ValueError) lançadas pelas funções de ETL.
"""

import json
import pytest
from unittest.mock import patch, MagicMock
from django.test import RequestFactory
from django.core.files.uploadedfile import SimpleUploadedFile
from api.views.importacao import importar_dados_api


class TestImportarDadosAPI:

    def setup_method(self):
        # Inicializa o RequestFactory para simular as requisições HTTP POST
        self.factory = RequestFactory()

    def test_retorna_erro_quando_nenhum_arquivo_e_enviado(self):
        # Arrange: Cria um POST request sem ficheiros
        request = self.factory.post('/api/importar/')

        # Act
        response = importar_dados_api(request)
        data = json.loads(response.content)

        # Assert
        assert response.status_code == 400
        assert data["erro"] == "Arquivo não enviado"

    def test_retorna_erro_quando_extensao_nao_e_csv(self):
        # Arrange: Cria um ficheiro de texto comum (.txt) simulado
        arquivo_invalido = SimpleUploadedFile(
            "documento.txt", b"conteudo ficticio", content_type="text/plain"
        )
        request = self.factory.post('/api/importar/', {"file": arquivo_invalido})

        # Act
        response = importar_dados_api(request)
        data = json.loads(response.content)

        # Assert
        assert response.status_code == 400
        assert data["erro"] == "Apenas arquivos CSV são permitidos"

    # Fazemos o mock das funções importadas DENTRO do ficheiro da view.
    # Lembre-se de alterar 'api.views.importacao' pelo caminho correto do seu módulo.
    @patch("api.views.importacao.carregar_csv")
    @patch("api.views.importacao.transformar_csv")
    @patch("api.views.importacao.validar_csv")
    @patch("api.views.importacao.extrair_csv")
    def test_sucesso_na_importacao_executa_pipeline_etl(
        self, mock_extrair, mock_validar, mock_transformar, mock_carregar
    ):
        # Arrange
        # Configura os retornos esperados dos mocks para simular o fluxo de dados
        df_ficticio = MagicMock()
        df_transformado_ficticio = MagicMock()
        tipo_csv_ficticio = "fornecedores"

        mock_extrair.return_value = df_ficticio
        mock_validar.return_value = tipo_csv_ficticio
        mock_transformar.return_value = df_transformado_ficticio

        arquivo_valido = SimpleUploadedFile(
            "dados.csv", b"coluna1,coluna2\nvalor1,valor2", content_type="text/csv"
        )
        request = self.factory.post('/api/importar/', {"file": arquivo_valido})

        # Act
        response = importar_dados_api(request)
        data = json.loads(response.content)

        # Assert
        assert response.status_code == 200
        assert data["mensagem"] == "Importação realizada com sucesso"

        # Verifica se as funções do ETL foram chamadas com os argumentos corretos e na ordem certa
        mock_extrair.assert_called_once()
        mock_validar.assert_called_once_with(df_ficticio)
        mock_transformar.assert_called_once_with(df_ficticio, tipo_csv_ficticio)
        mock_carregar.assert_called_once_with(
            df_transformado_ficticio, tipo_csv_ficticio
        )

    @patch("api.views.importacao.extrair_csv")
    def test_retorna_erro_quando_ocorrer_value_error_no_etl(self, mock_extrair):
        # Arrange
        # Simula que a primeira etapa do ETL (extrair_csv) falhou por formatação incorreta
        mensagem_erro_simulada = "Formato de CSV desconhecido ou corrompido"
        mock_extrair.side_effect = ValueError(mensagem_erro_simulada)

        arquivo_valido = SimpleUploadedFile(
            "dados_corrompidos.csv", b"lixo,lixo", content_type="text/csv"
        )
        request = self.factory.post('/api/importar/', {"file": arquivo_valido})

        # Act
        response = importar_dados_api(request)
        data = json.loads(response.content)

        # Assert
        assert response.status_code == 400
        assert data["erro"] == mensagem_erro_simulada
