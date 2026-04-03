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
  "financeiro": {
    "custo_total_materiais": 37009.71,
    "custo_total_projeto": 39167.4487,
    "total_horas_trabalhadas": 18.07
  },
  "programa": {
    "codigo": "MAX12AC",
    "gerente": "Ana Paula Ribeiro",
    "nome": "MAX 1.2 AC"
  },
  "projeto": {
    "codigo": "PRJ100",
    "data_fim_prevista": "2025-09-28",
    "data_inicio": "2024-11-09",
    "nome": "Driver Motor de Passo 3",
    "responsavel": "Lucas Pereira",
    "status": "EM ANDAMENTO"
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