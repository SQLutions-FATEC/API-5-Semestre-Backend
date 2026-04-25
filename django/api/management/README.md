# Guia de Uso - Processo Escalonado de Seeding

Este guia documenta o processo de popular o banco de dados do Data Warehouse com registros maciços que respeitam o ciclo de vida dos negócios desenvolvidos.

> [!WARNING]
> O comando antigo `seed_db` está **COMPLETAMENTE DEPRECADO**. Utilize invariavelmente o script `seed_dynamic.py` para todas as simulações, haja vista que a nova rotina gera a hierarquia inteligente, encadeia os temporais logísticos e não infeta o DB com mockups simples.

---

## 1. Subir a Aplicação (Docker)

Navegue até a pasta `deploy` e inicie todos os containers envolvidos no ciclo:

```bash
cd ../../../deploy
docker compose up -d
```

**⚠️ Importante:** Se você já tem PostgreSQL rodando no host da sua máquina operando na porta **5432**, evite conflito de bind alterando as instâncias mapeadas do *docker-compose.yaml* (Ex: de `- "5432:5432"` para `- "5433:5432"`).

---

## 2. Anatomia do `seed_dynamic`

O comando `seed_dynamic.py` introduz a biblioteca Faker em pt_BR combinada a regras rigorosas corporativas para produzir uma massa de dados coerente. As etapas lógicas e temporais do processo de seeding são:

### 2.1. Carga Base (Global)
- **Dimensão de Datas (`DimData`)**: O script trabalha com um sistema de cache para instâncias de data. Assim, garante eficiência nos inserts e evita duplicatas nas tabelas relacionais.
- **Fornecedores (`DimFornecedor`)**: É criada uma lista-base escalável de negócios ativos, rotulados por categorias macro ("Comunicação", "Mecatrônica", "Placas de Circuito Impresso", etc).
- **Catálogo de Materiais (`DimMaterial`)**: São geradas as peças e suprimentos da operação que farão parte do catálogo de compras, com nomenclaturas padronizadas por área e orçamentos unitários parametrizados.

### 2.2. O Ciclo: Programas e Projetos
- **Matriz `DimPrograma`**: Gera os programas corporativos de patrocínio que hospedam um leque de projetos. Assumem calendários muito abrangentes (durações em anos).
- **Matriz `DimProjeto`**: Cada programa instanciará *X* projetos, seguindo estas regras de sanidade:
  - O projeto respeita uma duração lógica atrelada a uma janela possível dentre o início e fim do programa.
  - O **status real** do projeto ("Planejamento", "Concluído", "Em Andamento") é apurado dinamicamente contra a cronologia real perante a data de *hoje*, não sendo escolhido randomicamente no vazio.

### 2.3. Execução: Fracionamento de Tarefas e Uso do Time
- **Estimação (`DimTarefa`)**: Para cada projeto válido (declinando da duração via o `duration_ratio`), é computada uma fração de tarefas curtas (estimadas estritamente de 2h a 40h de esforço bruto). O prazo limite da tarefa é alinhado automaticamente, pressupondo 1 dia de *deadline* a cada 8h trabalhadas.
- **A Apropriação (`FatoTarefa`)**:
  - O tamanho da equipe designada para o microtrabalho varia de acordo com o tamanho da tarefa e disponibilidade das tropas. Um time estrito e seu líder são formados na criação da tarefa.
  - O sistema emula que as horas alocadas pela meta sejam consumidas em iterativos *chunks* diários por seus membros autorizados.

### 2.4. Logística, *Supply Chain* e Retiradas
- **A Lógica de Consumo (`DimSolicitacao`)**: Usando a duração do projeto, sorteia-se de maneira realista se um ciclo necessitará de uso de um novo material. Dependendo do estado do projeto, solicitações podem ser aprovadas, canceladas ou ficarem pendentes.
- **Faturamento e Compras (`FatoCompra`)**: Se aprovado, a operação busca fornecedores atrelados àquela área e injeta um pedido validado atrelando aos custos dos insumos do passo Global.
- **Empenhos Periódicos (`FatoEmpenho`)**: Comprado com sucesso, a quantidade adquirida ingressa num ciclo emulador onde o projeto consome frações do volume original no decorrer dos próximos dias úteis até extinguir a necessidade da entrega, finalizando a cadeia do Fato de suprimento.

### 2.5 Argumentos do Comando

Execute o comando utilizando flags para moldar a agressividade do seeding. O comando roda do host passando pelo executável do container `django-app`. 

```bash
docker exec -it django-app python manage.py seed_dynamic
```

Personalizações de CLI disponíveis e o impacto nas gerações:

- `--programs`: Define a quantidade absoluta de programas (`DimPrograma`) que serão gerados. (Padrão: 1)
- `--projects`: Número limite de projetos (`DimProjeto`) gerados **por** programa. Se for invocado `--programs 2 --projects 3`, um total absoluto de 6 projetos serão instanciados. (Padrão: 3)
- `--tasks`: **Densidade de Tarefas**. Quantidade esperada de tarefas por mês a serem geradas. (Padrão: 5)
- `--users`: **Densidade do Time**. Define a quantidade de usuários a serem criados, medido em usuários por mês de execução de projeto. (Padrão: 3)
- `--clear`: **Zera** completamente os dados antigos nas tabelas e fatos do DW antes de iniciar a simulação limpa.

> **Exemplo Prático**: Injetar alta volumetria limpando o banco local:
> `docker exec django-app python manage.py seed_dynamic --programs 3 --projects 3 --tasks 12 --users 8 --clear`

### 2.6. Execução Automática no Deploy (Auto-Seeding)

O setup de deploy do backend está preparado para engatilhar a construção da massa de dados ao inicializar pela primeira vez.

Para não precisar rodar o seeding manualmente toda vez que reiniciar o projeto:
1. Abra as as suas variaveis ambientes no arquivo `.env` (localizado na pasta `deploy`).
2. Ajuste e ative a flag assinalando true na propriedade **`RUN_SEED`**:
   ```env
   RUN_SEED=true
   ```
3. Pronto! Ao realizar o próximo comando de deploy (`docker compose up -d`), o container rodará as migrações e chamará as regras generativas do seed imediatamente no seu log de start.

---

## 3. Conectando o DBeaver (GUI)

Use uma IDE PostgreSQL como o DBeaver para checar e aprovar as modelagens geradas:

1. Crie uma **Nova Conexão > PostgreSQL**.
2. Preencha as credenciais injetadas no deploy paramétrico:
   - **Host:** `localhost`
   - **Port:** `5432` *(ou a nova porta customizada)*
   - **Database:** `api_db`
   - **Username:** `api_user`
   - **Password:** `senha_padrao`
3. Salve com **Finish** e verifique as tabelas recém geradas pela carga indo no esquerdo em: **Databases > api_db > Schemas > schema_api > Tables**.
