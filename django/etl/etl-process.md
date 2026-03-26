# Processo ETL — Extração

## Visão Geral

Este documento descreve as fontes de dados, métodos de extração e decisões técnicas da etapa de extração do pipeline do Data Warehouse.

## Stack

- Python 3.x + Django + pandas
- PostgreSQL (via Docker)
- Django management command: `python manage.py run_extraction`

## Fluxo de Dados

```text
[Arquivos CSV] → [Extractors] → [Loader] → [DW: dim_* e fato_* (PostgreSQL)]
```
Os dados são lidos diretamente dos arquivos CSV e carregados nas tabelas do DW usando o Django ORM. Não há área de stage intermediária nesta etapa.

## Fontes de Dados




| Extractor | Arquivo CSV | Tabela DW |
| :--- | :--- | :--- |
| ProgramasExtractor | programas.csv | DimPrograma |
| ProjetosExtractor | projetos.csv | DimProjeto |
| TarefasProjetoExtractor | tarefas_projeto.csv | DimTarefa |
| MateriaisExtractor | materiais.csv | DimMaterial |
| FornecedoresExtractor | fornecedores.csv | DimFornecedor |
| SolicitacoesCompraExtractor | solicitacoes_compra.csv | DimSolicitacao |
| TempoTarefasExtractor | tempo_tarefas.csv | FatoTarefa |
| EmpenhoMateriaisExtractor | empenho_materiais.csv | FatoEmpenho |
| PedidosCompraExtractor | pedidos_compra.csv | FatoCompra |

> **Nota:**  Os arquivos  `compras_projeto.csv`  e  `estoque_materiais_projeto.csv`  não possuem tabela correspondente no modelo DW atual. Mantidos no diretório  `etl/data/`  para referência futura.

## Estratégia de Extração

-   **Método:**  Full Load — todos os registros são extraídos a cada execução.
    
-   **Datas:**  Campos de data dos CSVs são convertidos automaticamente em registros  `DimData`  (dia, mês, ano) via  `get_or_create`.
    
-   **Comportamento:**  Cada tabela DW é truncada antes do carregamento (`delete()`).
    
-   **Ordem de execução:**  Dimensões são carregadas antes dos fatos para garantir integridade referencial.
    
-   **Verificação de integridade:**  Após o carregamento, a contagem de registros do CSV e da tabela DW são comparadas. Qualquer divergência gera um erro.
    

## Testes Automáticos

O processo de extração conta com testes de integração para garantir a integridade do pipeline (validação de leitura do CSV e persistência no banco).

Para executar a suíte de testes:


```
# Via Docker (Recomendado)
docker compose exec backend python manage.py test etl

# Local
python manage.py test etl


```

## Logs

-   **Localização:**  `logs/etl_YYYYMMDD.log`
    
-   **Níveis:**  `INFO`  (sucesso),  `ERROR`  (arquivo não encontrado, erros de carga, falhas de integridade)
    
-   **Cada extractor registra:**  início da extração, contagem de registros e confirmação de carregamento.
    

## Como Executar


```
# Via Docker (Recomendado)
docker compose exec backend python manage.py run_extraction

# Local
python manage.py run_extraction


```

## Estrutura de Arquivos

Plaintext

```
django/etl/
├── data/                          ← arquivos CSV de origem atualizados
│   ├── programas.csv
│   ├── projetos.csv
│   ├── tarefas_projeto.csv
│   ├── tempo_tarefas.csv
│   ├── materiais.csv
│   ├── fornecedores.csv
│   ├── solicitacoes_compra.csv
│   ├── pedidos_compra.csv
│   ├── empenho_materiais.csv
│   ├── compras_projeto.csv
│   └── estoque_materiais_projeto.csv
├── extractors/
│   ├── base.py                    ← classe base com leitura de CSV usando pandas
│   └── extractors.py              ← um extractor por arquivo CSV
├── loaders/                       ← carrega dados direto nas tabelas DW via ORM
│   └── loader.py                  
├── validators/
│   └── integrity.py               ← valida contagens CSV vs DW
├── utils/
│   └── logger.py                  ← sistema de logs
├── tests/
│   ├── __init__.py
│   └── test_extraction.py         ← testes de integração do pipeline ETL
├── management/commands/
│   └── run_extraction.py          ← orquestrador principal
└── etl-process.md                 ← documentação do processo
```