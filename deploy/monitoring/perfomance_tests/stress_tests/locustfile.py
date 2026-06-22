import random
from locust import HttpUser, task, between

class SQLutionsBackendUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        self.projetos = ["PRJ003", "PRJ100", "PRJ-Gasto"]
        self.programas = ["PROG10", "MAX12AC", "MANSUP-ER"]

    # -------------------- ROTAS LEVES / BUSCAS (Peso Maior) --------------------
    @task(4)
    def testar_programas_busca(self):
        """ GET /api/programas/busca/ """
        self.client.get("/api/programas/busca/", name="/api/programas/busca/")

    @task(3)
    def testar_listagem_fornecedores(self):
        """ GET /api/fornecedores/ """
        self.client.get("/api/fornecedores/", name="/api/fornecedores/")

    @task(3)
    def testar_listagem_projetos_programa(self):
        """ GET /api/<programa_cod>/projetos/ """
        prog = random.choice(self.programas)
        self.client.get(f"/api/{prog}/projetos/", name="/api/[programa]/projetos/")

    # -------------------- ROTAS MEDIAS / DETALHES --------------------
    @task(2)
    def testar_dashboard_projeto(self):
        """ GET /api/projetos/<codigo_projeto>/ """
        proj = random.choice(self.projetos)
        self.client.get(f"/api/projetos/{proj}/", name="/api/projetos/[codigo]/")

    @task(2)
    def testar_tarefas_timesheet(self):
        """ GET /api/projetos/tarefas/<codigo_projeto> """
        proj = random.choice(self.projetos)
        self.client.get(f"/api/projetos/tarefas/{proj}", name="/api/projetos/tarefas/[codigo]")

    @task(2)
    def testar_solicitacoes_detalhes(self):
        """ GET /api/projetos/<codigo_projeto>/solicitacoes/detalhes/ """
        proj = random.choice(self.projetos)
        self.client.get(f"/api/projetos/{proj}/solicitacoes/detalhes/", name="/api/projetos/[codigo]/solicitacoes/detalhes/")

    # -------------------- ROTAS CRÍTICAS / AGREGADOS (Peso Menor) --------------------
    @task(1)
    def testar_alertas_criticos(self):
        """ GET /api/projetos/criticos/<codigo_projeto> """
        proj = random.choice(self.projetos)
        self.client.get(f"/api/projetos/criticos/{proj}", name="/api/projetos/criticos/[codigo]")

    @task(1)
    def testar_analitica_empenho(self):
        """ GET /api/projetos/<codigo_projeto>/empenhos/ """
        proj = random.choice(self.projetos)
        self.client.get(f"/api/projetos/{proj}/empenhos/", name="/api/projetos/[codigo]/empenhos/")

    @task(1)
    def testar_evolucao_gastos(self):
        """ GET /api/projetos/<codigo_projeto>/gastos/evolucao/ """
        proj = random.choice(self.projetos)
        self.client.get(f"/api/projetos/{proj}/gastos/evolucao/", name="/api/projetos/[codigo]/gastos/evolucao/")

    @task(1)
    def testar_otimizacao_estoque_sobras(self):
        """ GET /api/projetos/<codigo_projeto>/estoque/sobras/ """
        proj = random.choice(self.projetos)
        self.client.get(f"/api/projetos/{proj}/estoque/sobras/", name="/api/projetos/[codigo]/estoque/sobras/")