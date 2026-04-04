---

# Documentação do Processo ETL (Extração, Transformação e Carga)

## 1. Visão Geral
Este documento descreve a arquitetura e o funcionamento do pipeline de dados responsável por alimentar o Data Warehouse (DW). O sistema realiza a extração de dados de arquivos brutos (CSV), aplica transformações para limpeza e geração de indicadores de desempenho, e persiste as informações em um banco de dados PostgreSQL utilizando o Django ORM.

## 2. Stack Tecnológica
* **Linguagem:** Python 3.12+
* **Manipulação de Dados:** pandas (DataFrames)
* **Framework de Persistência:** Django 5.x (ORM)
* **Banco de Dados:** PostgreSQL
* **Ambiente:** Docker & Docker Compose
* **Qualidade e Testes:** pytest, pytest-django, pytest-cov

## 3. Fluxo de Dados
O pipeline opera em três estágios principais, garantindo que o dado bruto seja refinado antes de chegar à camada analítica:

```text
[Arquivos CSV] ➔ [Extractors] ➔ [Transformers] ➔ [Loaders] ➔ [Data Warehouse]
```

1.  **Extração:** Os arquivos são lidos da pasta `etl/data/`.
2.  **Transformação:** Aplicação de regras de saneamento e cálculo de métricas (Lead Time e Atraso).
3.  **Carga:** Os dados transformados são mapeados para os modelos do Django e salvos no banco utilizando lógica de **Bulk Insert** para performance.

## 4. Regras de Negócio e Transformações
Para garantir a padronização e a utilidade dos dados para relatórios, o pipeline aplica as seguintes lógicas:

### A. Saneamento de Dados
* **Normalização de Texto:** Campos de texto (como status e nomes de responsáveis) são convertidos para **MAIÚSCULAS** e têm acentos e espaços em branco excedentes removidos.
* **Truncagem de Datas:** Datas que chegam com carimbos de hora (ex: `2026-01-01 00:00:00`) são limpas para o formato `YYYY-MM-DD` antes de serem processadas.

### B. Indicadores Calculados (Métricas)
* **Lead Time (Dias):** Diferença absoluta em dias entre a `data_inicio` e a `data_fim_prevista`.
* **Identificação de Atraso (`is_atrasado`):** Flag lógica definida como `True` se a `data_fim_prevista` for menor que a data atual e o `status` do item não for **"CONCLUIDO"**.

## 5. Mapeamento de Entidades

| Componente | Origem (CSV) | Tabela Destino | Indicadores Gerados |
| :--- | :--- | :--- | :--- |
| **Programas** | `programas.csv` | `DimPrograma` | - |
| **Projetos** | `projetos.csv` | `DimProjeto` | Lead Time, Flag de Atraso |
| **Tarefas** | `tarefas_projeto.csv` | `DimTarefa` | Lead Time, Flag de Atraso |
| **Suprimentos** | `materiais.csv` | `DimMaterial` | - |
| **Parceiros** | `fornecedores.csv` | `DimFornecedor` | - |
| **Processos** | `tempo_tarefas.csv` | `FatoTarefa` | Horas Trabalhadas |
| **Financeiro** | `pedidos_compra.csv` | `FatoCompra` | Valor Total |

## 6. Estrutura de Diretórios
```plaintext
django/etl/
├── data/                          # Arquivos CSV de origem (Source)
├── extractors/
│   ├── base.py                    # Classe base para leitura de CSV via pandas
│   └── extractors.py              # Implementação dos extratores por entidade
├── transformations/               # Camada de inteligência de negócio
│   └── transformers.py            # Funções de cálculo de Lead Time e limpeza
├── loaders/
│   └── loader.py                  # Carga em lote (Bulk Insert) para o banco
├── validators/
│   └── integrity.py               # Validação de volumetria (CSV vs DB)
├── tests/
│   ├── test_extraction.py         # Testes de integração do pipeline
│   └── test_transformers.py       # Testes unitários das métricas e cálculos
└── management/commands/
    └── run_etl.py                 # Gatilho manual (Comando de execução)
```

## 7. Qualidade e Testes
O projeto utiliza o **pytest** para validar as métricas de Lead Time e as flags de atraso, garantindo alta cobertura de código para o SonarCloud.

### **Procedimento para Execução de Testes**
Para garantir o contexto correto de banco de dados e dependências, siga os passos abaixo:

1.  **Acesse o diretório de deploy:**
    ```bash
    cd backend/deploy
    ```
2.  **Certifique-se de que os containers estão rodando:**
    ```bash
    docker compose up -d
    ```
3.  **Executar testes unitários (Validação de Lógica):**
    ```bash
    docker compose exec backend python -m pytest etl/tests/
    ```
4.  **Executar com Relatório de Cobertura (Qualidade):**
    ```bash
    docker compose exec backend python -m pytest --cov=etl --cov-report=term-missing etl/tests/
    ```

## 8. Gatilho de Sincronização Manual (Execução)
Para consolidar os dados dos arquivos operacionais para o Data Warehouse sob demanda, foi desenvolvido um comando de gerenciamento customizado do Django.

Para disparar o processo completo:

1.  **No diretório de deploy, execute:**
    ```bash
    docker compose exec backend python manage.py run_etl
    ```
2.  **Acompanhamento:**
    O terminal exibirá o progresso de cada etapa ("Extraindo...", "Carregando..."). Ao final, será exibida a mensagem de sucesso ou um relatório de erros caso ocorram falhas de integridade.

## 9. Processo de Carga e Idempotência
O carregamento das tabelas fato (`FatoTarefa`, `FatoEmpenho` e `FatoCompra`) e dimensões é a etapa final do pipeline analítico.

* **Otimização com Bulk Insert:** Para garantir alta performance, o carregamento utiliza o método `bulk_create` do Django ORM, persistindo os dados em listas de objetos em memória em uma única transação por entidade.
* **Garantia de Integridade e Idempotência:** O pipeline realiza uma limpeza prévia (`.delete()`) de registros antigos antes de cada carga. Isso garante que o Data Warehouse possa ser sincronizado múltiplas vezes sem duplicar dados, refletindo sempre o estado mais recente dos arquivos CSV.

---