

---

# Documentação do Processo ETL (Extração, Transformação e Carga)

## 1. Visão Geral
Este documento descreve a arquitetura e o funcionamento do pipeline de dados responsável por alimentar o Data Warehouse (DW). O sistema realiza a extração de dados de arquivos brutos (CSV), aplica transformações para limpeza e geração de indicadores de desempenho, e persiste as informações em um banco de dados PostgreSQL utilizando o Django ORM.

## 2. Stack Tecnológica
*   **Linguagem:** Python 3.12+
*   **Manipulação de Dados:** pandas (DataFrames)
*   **Framework de Persistência:** Django 5.x (ORM)
*   **Banco de Dados:** PostgreSQL
*   **Ambiente:** Docker & Docker Compose
*   **Qualidade e Testes:** pytest, pytest-django, pytest-cov

## 3. Fluxo de Dados
O pipeline opera em três estágios principais, garantindo que o dado bruto seja refinado antes de chegar à camada analítica:

```text
[Arquivos CSV] ➔ [Extractors] ➔ [Transformers] ➔ [Loaders] ➔ [Data Warehouse]
```

1.  **Extração:** Os arquivos são lidos da pasta `etl/data/`.
2.  **Transformação:** Aplicação de regras de saneamento e cálculo de métricas (Lead Time e Atraso).
3.  **Carga:** Os dados transformados são mapeados para os modelos do Django e salvos no banco.

## 4. Regras de Negócio e Transformações
Para garantir a padronização e a utilidade dos dados para relatórios, o pipeline aplica as seguintes lógicas:

### A. Saneamento de Dados
*   **Normalização de Texto:** Campos de texto (como status e nomes de responsáveis) são convertidos para **MAIÚSCULAS** e têm espaços em branco excedentes removidos (trim).
*   **Truncagem de Datas:** Datas que chegam com carimbos de hora (ex: `2026-01-01 00:00:00`) são limpas para o formato `YYYY-MM-DD` antes de serem processadas pela dimensão de tempo.

### B. Indicadores Calculados (Métricas)
*   **Lead Time (Dias):** Calculado automaticamente como a diferença absoluta em dias entre a `data_inicio` e a `data_fim_prevista`.
*   **Identificação de Atraso (`is_atrasado`):** Uma flag lógica definida como `True` se a `data_fim_prevista` for menor que a data atual e o `status` do item não for "CONCLUÍDO".

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
A organização do código reflete a separação de responsabilidades do pipeline:

```plaintext
django/etl/
├── data/                          # Arquivos CSV de origem (Source)
├── extractors/
│   ├── base.py                    # Classe base para leitura de CSV via pandas
│   └── extractors.py              # Implementação dos extratores por entidade
├── transformations/               # Camada de inteligência de negócio
│   └── transformers.py            # Funções de cálculo de Lead Time e limpeza
├── loaders/
│   └── loader.py                  # Conversão de DataFrames para Django ORM
├── validators/
│   └── integrity.py               # Validação de volumetria (CSV vs DB)
├── utils/
│   └── logger.py                  # Centralização de logs do processo
├── tests/
│   ├── test_extraction.py         # Testes de integração do pipeline
│   └── test_transformers.py       # Testes unitários das métricas e cálculos
├── management/commands/
│   └── run_extraction.py          # Orquestrador (Comando de execução)
└── etl-process.md                 # Documentação técnica do processo
```

## 7. Qualidade e Testes
O projeto utiliza uma suíte de testes automatizados para garantir que as métricas de Lead Time e as flags de atraso sejam calculadas com precisão, atingindo alta cobertura de código para satisfazer critérios de qualidade (SonarCloud).

### Executar Testes
```bash
docker-compose exec backend env PYTHONPATH=. python -m pytest --cov=etl etl/tests/
```

## 8. Como Executar o Processo
Para disparar a carga completa (Full Load) do Data Warehouse:

```bash
docker-compose exec backend python manage.py run_extraction
```

---