## Rota Dashboard de Projeto

Retorna um consolidado de dados (dashboard) de um projeto específico, incluindo informações gerais, dados financeiros calculados dinamicamente (custo de materiais e horas trabalhadas) e detalhes do programa ao qual o projeto pertence.

### **Endpoint**
`GET /api/projetos/<codigo_projeto>/`

### **Parâmetros de Rota (Path Parameters)**

| Parâmetro | Tipo | Descrição | Exemplo |
| :--- | :--- | :--- | :--- |
| `codigo_projeto` | `String` | O código identificador único do projeto no banco de dados. | `PRJ003` |

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
        "nome": "Unidade Teste Automático",
        "status": "Suspenso",
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
        "nome": "Unidade Teste Automatico"
    },
    "tarefas": [
        {
            "codigo": "TAR001",
            "titulo": "Levantamento de Requisitos",
            "responsavel": "Joao Pedro Alves",
            "estimativa": 40,
            "status": "Concluido",
            "total_horas_trabalhadas": 20.5
        },
        {
            "codigo": "TSK009",
            "titulo": "Prototipacao da placa",
            "responsavel": "Marcelo Cardoso",
            "estimativa": 46,
            "status": "Em andamento",
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
* **Pedidos Atrasados:** Lista pedidos em que `data_atual > data_previsao_entrega` e o `status` nao e `Concluido`.
* **Pedidos Prioritarios Pendentes:** Lista pedidos com prioridade `Alta` ou `Urgente` cujo status seja `Aberto` ou `Enviado`.
* **Materiais Obsoletos Criticos:** Lista materiais com `status = Obsoleto` vinculados ao projeto ou presentes em pedidos recentes (ultimos 30 dias).

### **Resposta de Sucesso: `200 OK`**

```json
{
    "projeto": {
        "codigo": "PRJ003",
        "nome": "Unidade Teste Automatico"
    },
    "data_referencia": "2026-03-30",
    "alertas_criticos": {
        "pedidos_atrasados": [
            {
                "numero_pedido": "PED001",
                "status": "Pendente",
                "data_previsao_entrega": "2026-03-10",
                "dias_atraso": 20
            }
        ],
        "pedidos_prioritarios_pendentes": [
            {
                "numero_pedido": "PED007",
                "prioridade": "Urgente",
                "status": "Pendente",
                "data_pedido": "2026-03-25"
            }
        ],
        "materiais_obsoletos": [
            {
                "codigo_material": "MAT015",
                "descricao": "Controlador legado",
                "status": "Obsoleto",
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
        "nome": "Unidade Teste Automático"
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