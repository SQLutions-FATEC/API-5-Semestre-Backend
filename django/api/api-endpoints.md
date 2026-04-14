## Rota Dashboard de Projeto

Retorna um consolidado de dados (dashboard) de um projeto específico, incluindo informações gerais, dados financeiros calculados dinamicamente (custo de materiais e horas trabalhadas) e detalhes do programa ao qual o projeto pertence.

### **Endpoint**
`GET /api/projetos/<codigo_projeto>/`

### **Parâmetros de Rota (Path Parameters)**

| Parâmetro | Tipo | Descrição | Exemplo |
| :--- | :--- | :--- | :--- |
| `codigo_projeto` | `String` | O código identificador único do projeto no banco de dados. | `PRJ100` |

### **Regras de Negócio e Cálculos**
* **Custo Total de Materiais:** Soma do `valor_total` de todas as compras associadas às solicitações do projeto.
* **Total de Horas Trabalhadas:** Soma das `horas_trabalhadas` de todas as tarefas associadas ao projeto.
* **Custo Total do Projeto:** Calculado através da fórmula: `(Total de Horas Trabalhadas * Custo/Hora do Projeto) + Custo Total de Materiais`.

---

### **Respostas**

#### Sucesso: `200 OK`
Retornado quando o projeto é encontrado com sucesso.

**Exemplo de Resposta (JSON):**
```json
{
    "projeto": {
        "codigo": "PRJ003",
        "nome": "UNIDADE TESTE AUTOMATICO",
        "status": "SUSPENSO",
        "data_inicio": "2022-05-09",
        "data_fim_prevista": "2025-04-30"
    },
    "financeiro": {
        "total_horas_trabalhadas": 26.44,
        "custo_total_materiais": 27070.40,
        "custo_total_projeto": 30166.26
    },
    "programa": {
        "codigo": "MAX12AC",
        "nome": "MAX 1.2 AC",
        "gerente": "Ana Paula Ribeiro"
    }
}
```

#### Erro: `404 Not Found`
Retornado quando o `codigo_projeto` fornecido na URL não existe no banco de dados.

**Exemplo de Resposta (HTML/JSON padrão do Django):**
```json
{
    "detail": "Not found."
}
```

---

## Rota Tarefas e Timesheet de Projeto

Retorna as tarefas de um projeto com total de horas trabalhadas por tarefa e um objeto de evolucao temporal para alimentar grafico de horas no frontend.

### **Endpoint**
`GET /api/projetos/tarefas/<codigo_projeto>`

### **Parametros de Rota (Path Parameters)**

| Parametro | Tipo | Descricao | Exemplo |
| :--- | :--- | :--- | :--- |
| `codigo_projeto` | `String` | Codigo identificador do projeto no banco de dados. | `PRJ003` |

### **Regras de Negocio e Calculos**
* **Lista de Tarefas:** Retorna `codigo`, `titulo`, `responsavel`, `estimativa` e `status`.
* **Total de Horas por Tarefa:** Campo calculado `total_horas_trabalhadas` via agregacao (`Sum`) da tabela de fatos.
* **Evolucao Temporal:** Objeto `evolucao_horas` com chave no formato `YYYY-MM-DD` e valor com soma de horas do dia.

### **Resposta de Sucesso: `200 OK`**

```json
{
    "projeto": {
        "codigo": "PRJ003",
        "nome": "UNIDADE TESTE AUTOMATICO"
    },
    "tarefas": [
        {
            "codigo": "TAR001",
            "titulo": "Levantamento de Requisitos",
            "responsavel": "JOAO PEDRO ALVES",
            "estimativa": 40,
            "status": "CONCLUIDO",
            "total_horas_trabalhadas": 20.5
        },
        {
            "codigo": "TSK009",
            "titulo": "Prototipacao da placa",
            "responsavel": "MARCELO CARDOSO",
            "estimativa": 46,
            "status": "EM ANDAMENTO",
            "total_horas_trabalhadas": 5.94
        }
    ],
    "evolucao_horas": {
        "2022-05-09": 26.44,
        "2024-11-21": 2.17
    }
}
```

### **Resposta de Erro: `404 Not Found`**

Retornada quando o `codigo_projeto` informado nao existe.

---

## Rota Inteligencia de Alertas Criticos

Retorna alertas automaticos para apoiar a decisao do gestor com foco em atrasos, prioridades e materiais obsoletos.

### **Endpoint**
`GET /api/projetos/criticos/<codigo_projeto>`

### **Parametros de Rota (Path Parameters)**

| Parametro | Tipo | Descricao | Exemplo |
| :--- | :--- | :--- | :--- |
| `codigo_projeto` | `String` | Codigo identificador do projeto no banco de dados. | `PRJ003` |

### **Regras de Negocio e Criterios de Aceitacao**
* **Pedidos Atrasados:** Lista pedidos em que `data_atual > data_previsao_entrega` e o `status` nao é `CONCLUIDO`.
* **Pedidos Prioritarios Pendentes:** Lista pedidos com prioridade `ALTA` ou `URGENTE` cujo status seja `ABERTO` ou `ENVIADO`.
* **Materiais Obsoletos Criticos:** Lista materiais com `status = OBSOLETO` vinculados ao projeto ou presentes em pedidos recentes (ultimos 30 dias).

### **Resposta de Sucesso: `200 OK`**

```json
{
    "projeto": {
        "codigo": "PRJ003",
        "nome": "UNIDADE TESTE AUTOMATICO"
    },
    "data_referencia": "2026-03-30",
    "alertas_criticos": {
        "pedidos_atrasados": [
            {
                "numero_pedido": "PED001",
                "status": "PENDENTE",
                "data_previsao_entrega": "2026-03-10",
                "dias_atraso": 20
            }
        ],
        "pedidos_prioritarios_pendentes": [
            {
                "numero_pedido": "PED007",
                "prioridade": "URGENTE",
                "status": "PENDENTE",
                "data_pedido": "2026-03-25"
            }
        ],
        "materiais_obsoletos": [
            {
                "codigo_material": "MAT015",
                "descricao": "Controlador legado",
                "status": "OBSOLETO",
                "vinculado_ao_projeto": true,
                "pedido_recente": false
            }
        ]
    }
}
```

### **Resposta de Erro: `404 Not Found`**

Retornada quando o `codigo_projeto` informado nao existe.

## Rota Analítica de Empenho de Projeto

Retorna dados analíticos sobre os materiais empenhados de um projeto específico, incluindo o custo total de empenho, agrupamento por categoria, agrupamento por material (com quantidades) e a evolução temporal do empenho.

### **Endpoint**
`GET /api/projetos/<codigo_projeto>/empenhos/`

### **Parâmetros de Rota (Path Parameters)**

| Parâmetro | Tipo | Descrição | Exemplo |
| :--- | :--- | :--- | :--- |
| `codigo_projeto` | `String` | Código identificador único do projeto no banco de dados. | `PRJ003` |

### **Regras de Negócio e Cálculos**
* **Custo Total de Empenho:** Soma do custo calculado de cada empenho associado ao projeto. O custo individual é obtido multiplicando a `quantidade_empenhada` pelo `custo_estimado` do material no banco.
* **Empenho por Categoria:** Agrupamento do custo total de empenho baseado na categoria dos materiais associados.
* **Empenho por Material:** Agrupamento por material listando código, descrição, categoria, quantidade total empenhada e o custo correspondente.
* **Empenho no Tempo:** Histórico diário (agregação no formato `YYYY-MM-DD`) com a soma dos custos de empenhos registrados naquele dia específico e a lista detalhada dos materiais atrelados àquela data.

### **Resposta de Sucesso: `200 OK`**

```json
{
    "projeto": {
        "codigo": "PRJ003",
        "nome": "UNIDADE TESTE AUTOMATICO"
    },
    "empenho_total": 4500.50,
    "empenho_por_categoria": [
        {
            "categoria": "Eletrônicos",
            "total_custo": 3000.50
        },
        {
            "categoria": "Mecânica",
            "total_custo": 1500.00
        }
    ],
    "empenho_por_material": [
        {
            "codigo_material": "MAT101",
            "descricao": "Capacitor 100uF",
            "categoria": "Eletrônicos",
            "custo_unitario": 6.00,
            "quantidade_total": 500,
            "total_custo": 3000.00
        },
        {
            "codigo_material": "MAT205",
            "descricao": "Parafuso M4",
            "categoria": "Mecânica",
            "custo_unitario": 1.50,
            "quantidade_total": 1000,
            "total_custo": 1500.00
        }
    ],
    "empenho_por_tempo": [
        {
            "data": "2024-03-10",
            "total_custo": 2000.00,
            "materiais": [
                {
                    "codigo_material": "MAT101",
                    "descricao": "Capacitor 100uF",
                    "custo_unitario": 6.00,
                    "quantidade": 333,
                    "total_custo": 1998.00
                }
            ]
        },
        {
            "data": "2024-03-15",
            "total_custo": 2500.00,
            "materiais": [
                {
                    "codigo_material": "MAT205",
                    "descricao": "Parafuso M4",
                    "custo_unitario": 1.50,
                    "quantidade": 1000,
                    "total_custo": 1500.00
                }
            ]
        }
    ]
}
```

### **Resposta de Erro: `404 Not Found`**

Retornada quando o `codigo_projeto` informado não existe.

---

## Rota Detalhes de Compras do Projeto

Retorna a listagem de todos os pedidos de compra vinculados a um projeto específico, processando métricas de prazos de entrega e consolidando informações de fornecedores e centros de custo.

### **Endpoint**
`GET /api/projetos/<codigo_projeto>/compras/`

### **Parâmetros de Rota (Path Parameters)**

| Parâmetro | Tipo | Descrição | Exemplo |
| :--- | :--- | :--- | :--- |
| `codigo_projeto` | `String` | O código identificador único do projeto no banco de dados. | `PRJ003` |

### **Regras de Negócio e Cálculos**

* **Dias Previstos de Entrega:** Calculado individualmente para cada pedido através da diferença entre a data de previsão e a data de emissão: (Data Previsão - Data Pedido).
* **Tempo Médio de Entrega:** Média aritmética simples de todos os `dias_previstos_entrega` dos pedidos vinculados ao projeto.
* **Otimização de Query:** Utiliza `Select Related` para buscar dimensões de Fornecedor, Datas e Solicitações em uma única consulta.

### **Respostas**

#### Sucesso: `200 OK`
Retornado quando o projeto é encontrado, mesmo que não haja compras vinculadas (neste caso, retorna lista vazia e média 0).

**Exemplo de Resposta (JSON)**:

```json
{
    "projeto": "PRJ003",
    "tempo_medio_entrega_dias": 15.0,
    "pedidos": [
        {
            "numero": "PED01",
            "emissao": "2024-01-01",
            "previsao": "2024-01-11",
            "fornecedor": "Forn Teste",
            "centro_custo": "Proj 1",
            "status": "ENTREGUE",
            "dias_previstos_entrega": 10
        },
        {
            "numero": "PED02",
            "emissao": "2024-01-01",
            "previsao": "2024-01-21",
            "fornecedor": "Forn Teste",
            "centro_custo": "Proj 1",
            "status": "PENDENTE",
            "dias_previstos_entrega": 20
        }
    ]
}

```

#### Erro: `404 Not Found`
Retornado quando o `codigo_projeto` fornecido na URL não existe no banco de dados.

**Exemplo de Resposta (HTML/JSON padrão do Django):**
```json
{
    "detail": "Not found."
}
```

#### Erro: `405 Method Not Allowed`
Retornado caso a requisição utilize um método diferente de GET (ex: POST, PUT, DELETE).

**Exemplo de Resposta (HTML/JSON padrão do Django):**
```json
{
    "detail": "Method \"POST\" not allowed."
}
```

---

## Rota de Empenhos por Programa

Retorna uma listagem detalhada dos empenhos de materiais realizados, permitindo a filtragem por um programa específico ou por categoria de material. O endpoint também fornece o cálculo do valor total empenhado com base no custo estimado dos materiais.

### **Endpoint**
`GET /api/empenhos/`

### **Parâmetros de Rota (Path Parameters)**

| Parâmetro | Tipo | Descrição | Exemplo |
| :--- | :--- | :--- | :--- |
| `programa_id` | `Integer` | (Opcional) ID do programa para filtrar os empenhos vinculados. | `12` |
| `categoria` | `String` | (Opcional) Filtra os materiais por categoria específica. | `Eletrônicos` |

### **Regras de Negócio e Cálculos**
* **Valor Empenhado (Item):** Calculado multiplicando a quantidade empenhada pelo custo unitário estimado do material. O cálculo seria `Valor` = `Quantidade Empenhada` x `Custo Estimado Material`.
* **Valor Total Empenhado:** Soma acumulada de todos os valores empenhados dos itens retornados na consulta.

---

### **Respostas**

#### Sucesso: `200 OK`
Retornado com a lista de empenhos (resultados) e o somatório total. Se nenhum filtro for aplicado, retorna todos os registros.

**Exemplo de Resposta (JSON):**
```json
{
    "resultados": [
        {
            "nome_projeto": "UNIDADE TESTE AUTOMATICO",
            "nome_material": "Conector Molex 4 vias",
            "quantidade_empenhada": 470,
            "valor_empenhado": 18630.8,
            "data_empenho": "3/11/2024"
        },
        {
            "nome_projeto": "CONTROLADOR MOTOR BRUSHLESS",
            "nome_material": "Diodo Retificador UF4007",
            "quantidade_empenhada": 286,
            "valor_empenhado": 34305.7,
            "data_empenho": "18/5/2024"
        }
    ],
    "valor_total_empenhado": 52936.5
}
```

#### Erro: `500 Internal Server Error`
Retornado caso ocorra algum erro inesperado no processamento dos dados ou falha de conexão com o banco de dados.

**Exemplo de Resposta (HTML/JSON padrão do Django):**
```json
{
    "detail": "Erro interno no servidor. Por favor, tente novamente mais tarde."
}
```
---
## Rota Analítica de Solicitações (Estatísticas)

Retorna as estatísticas e indicadores de topo (cards de resumo) para a tela de solicitações de um projeto específico. O endpoint consolida o volume de requisições pendentes e destaca os itens críticos e urgentes que exigem atenção imediata, calculando o tempo de espera desde a abertura.

### **Endpoint**
`GET /api/empenhos/`

### **Parâmetros de Rota (Path Parameters)**

| Parâmetro | Tipo | Descrição | Exemplo |
| :--- | :--- | :--- | :--- |
| `codigo_projeto` | `String` | (Obrigatório) Código identificador único do projeto no banco de dados. | `PRJ003` |

### **Regras de Negócio e Cálculos**
* **Total de Pendentes (`total_pendentes`):** Contagem absoluta de solicitações vinculadas ao projeto que se encontram com o status exato de "ABERTO".
* **Urgentes e Críticas (`urgentes_criticas`):** Contagem absoluta de solicitações vinculadas ao projeto que se encontram com o status exato de "ABERTO".
* **Dias Pendentes (`dias_pendentes`):** Campo inserido dinamicamente no backend, calculado pela diferença em dias entre a data em que o servidor processa a requisição e a data de criação da solicitação (`Data Atual` - `data_solicitacao`).

---

### **Respostas**

#### Sucesso: `200 OK`
Retornado quando o projeto é encontrado e as estatísticas são processadas corretamente. O objeto é estruturado para consumo direto nos cards do front-end.

**Exemplo de Resposta (JSON):**
```json
{
    {
        "projeto": "PRJ003",
        "estatisticas": {
            "total_pendentes": 12,
            "urgentes_criticas": [
                {
                    "numero_solicitacao": "SOL-998",
                    "prioridade": "URGENTE",
                    "status": "Aberto",
                    "dias_desde_criacao": 5
                },
                {
                    "numero_solicitacao": "SOL-1005",
                    "prioridade": "ALTA",
                    "status": "Aberto",
                    "dias_desde_criacao": 2
                }
            ]
        }
    }
}
```

#### Erro: `404 Not Found`
Retornado caso o código do projeto fornecido na URL não seja localizado na base de dados (`DimProjeto`).

**Exemplo de Resposta (HTML/JSON padrão do Django):**
```json
{
    "detail": "Não encontrado."
}
```

---