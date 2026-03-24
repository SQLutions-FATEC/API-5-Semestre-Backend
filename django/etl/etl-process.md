# ETL Process — Extraction
 
## Overview
 
This document describes the data sources, extraction methods, and technical decisions
for the ETL extraction step of the Data Warehouse pipeline.
 
## Stack
 
- Python 3.x + Django
- PostgreSQL (via Docker)
- Django management command: `python manage.py run_extraction`
 
## Data Flow
 
```
[Operational Tables] → [Extractors] → [Stage Tables (PostgreSQL)]
```
 
Stage tables are raw copies of the operational data, with no transformations applied.
They serve as the input for the next ETL step (Transformation).
 
## Data Sources
 
| Extractor | Source Table | Stage Table |
|---|---|---|
| ProgramasEmpresaExtractor | programasempresa | stage_programas |
| ProjetosProgramasExtractor | projetosprogramas | stage_projetos |
| TarefasProjetoExtractor | tarefasprojeto | stage_tarefas |
| TempoTarefasExtractor | tempotarefas | stage_tempo_tarefas |
| MateriaisEngenhariaExtractor | materiaisengenharia | stage_materiais |
| FornecedoresExtractor | fornecedor | stage_fornecedores |
| SolicitacoesCompraExtractor | solicitacoescompra | stage_solicitacoes |
| PedidosCompraExtractor | pedidoscompra | stage_pedidos_compra |
| EmpenhoMateriaisExtractor | empenhomateriais | stage_empenho_materiais |
| ComprasProjetoExtractor | comprasprojeto | stage_compras_projeto |
| EstoqueMateriaisExtractor | estoquemateriaisproj | stage_estoque_materiais |
 
## Extraction Strategy
 
- **Method:** Full Load — all records are extracted on every run.
- **Stage behavior:** Each stage table is truncated before loading (`TRUNCATE ... RESTART IDENTITY`).
- **Integrity check:** After loading, record counts from source and stage are compared. Any mismatch raises an error.
 
## Logs
 
- Location: `logs/etl_YYYYMMDD.log`
- Levels: `INFO` (success), `ERROR` (connection failures, extraction errors, integrity failures)
- Each extractor logs: connection check, extraction start, record count, and load confirmation.
 
## How to Run
 
```bash
# Local
python manage.py run_extraction
 
# Via Docker
docker compose exec backend python manage.py run_extraction
```
 
## Known Field Gaps (to align with DW team)
 
The following fields exist in the DW model but have no source in the operational tables.
These must be resolved before the Transformation step:
 
| Field | DW Table | Status |
|---|---|---|
| gerente_tecnico | dim_programa | Not found in ProgramasEmpresa |
| data_fim_prevista | dim_programa, dim_projeto | Not found in source tables |
| custo_hora | dim_projeto | Not found in ProjetosProgramas |
| data_inicio / data_fim_prevista | dim_tarefa | Not found in TarefasProjeto |
| projeto_id / material_id | dim_solicitacao | Not found in SolicitacoesCompra |
| solicitacao_id | fato_compra | PedidosCompra has no FK to SolicitacoesCompra |
 

 # -------------------------------------------------- VERSÃO PT-BR------------------------------------------------------------

 # Processo ETL — Extração

## Visão Geral

Este documento descreve as fontes de dados, métodos de extração e decisões técnicas
da etapa de extração do pipeline do Data Warehouse.

## Stack

- Python 3.x + Django
- PostgreSQL (via Docker)
- Django management command: `python manage.py run_extraction`

## Fluxo de Dados
```
[Tabelas Operacionais] → [Extractors] → [Tabelas de Stage (PostgreSQL)]
```

As tabelas de stage são cópias brutas dos dados operacionais, sem nenhuma transformação aplicada.
Elas servem como entrada para a próxima etapa do ETL (Transformação).

## Fontes de Dados

| Extractor | Tabela Origem | Tabela Stage |
|---|---|---|
| ProgramasEmpresaExtractor | programasempresa | stage_programas |
| ProjetosProgramasExtractor | projetosprogramas | stage_projetos |
| TarefasProjetoExtractor | tarefasprojeto | stage_tarefas |
| TempoTarefasExtractor | tempotarefas | stage_tempo_tarefas |
| MateriaisEngenhariaExtractor | materiaisengenharia | stage_materiais |
| FornecedoresExtractor | fornecedor | stage_fornecedores |
| SolicitacoesCompraExtractor | solicitacoescompra | stage_solicitacoes |
| PedidosCompraExtractor | pedidoscompra | stage_pedidos_compra |
| EmpenhoMateriaisExtractor | empenhomateriais | stage_empenho_materiais |
| ComprasProjetoExtractor | comprasprojeto | stage_compras_projeto |
| EstoqueMateriaisExtractor | estoquemateriaisproj | stage_estoque_materiais |

## Estratégia de Extração

- **Método:** Full Load — todos os registros são extraídos a cada execução.
- **Comportamento do stage:** Cada tabela de stage é truncada antes do carregamento (`TRUNCATE ... RESTART IDENTITY`).
- **Verificação de integridade:** Após o carregamento, a contagem de registros da origem e do stage são comparadas. Qualquer divergência gera um erro.

## Logs

- **Localização:** `logs/etl_YYYYMMDD.log`
- **Níveis:** `INFO` (sucesso), `ERROR` (falhas de conexão, erros de extração, falhas de integridade)
- **Cada extractor registra:** verificação de conexão, início da extração, contagem de registros e confirmação de carregamento.

## Como Executar
```bash
# Local
python manage.py run_extraction

# Via Docker
docker compose exec backend python manage.py run_extraction
```

## Campos Ausentes na Origem (alinhar com o time DW)

Os campos abaixo existem no modelo do DW mas não possuem origem nas tabelas operacionais.
Devem ser resolvidos antes da etapa de Transformação:

| Campo | Tabela DW | Status |
|---|---|---|
| gerente_tecnico | dim_programa | Não encontrado em ProgramasEmpresa |
| data_fim_prevista | dim_programa, dim_projeto | Não encontrado nas tabelas de origem |
| custo_hora | dim_projeto | Não encontrado em ProjetosProgramas |
| data_inicio / data_fim_prevista | dim_tarefa | Não encontrado em TarefasProjeto |
| projeto_id / material_id | dim_solicitacao | Não encontrado em SolicitacoesCompra |
| solicitacao_id | fato_compra | PedidosCompra não possui FK para SolicitacoesCompra |
