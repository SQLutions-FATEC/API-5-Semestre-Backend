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
    "projeto": "PRJ01",
    "tempo_medio_entrega_dias": 15.0,
    "pedidos": [
        {
            "numero": "PED01",
            "emissao": "2024-01-01",
            "previsao": "2024-01-11",
            "fornecedor": "Forn Teste",
            "centro_custo": "Proj 1",
            "status": "Entregue",
            "dias_previstos_entrega": 10
        },
        {
            "numero": "PED02",
            "emissao": "2024-01-01",
            "previsao": "2024-01-21",
            "fornecedor": "Forn Teste",
            "centro_custo": "Proj 1",
            "status": "Pendente",
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