from locust import HttpUser, task, between

class SQLutionsBackendUser(HttpUser):
    # Simula o "tempo de pensamento" do usuário real entre um clique e outro
    # (Aguarda aleatoriamente entre 1 e 3 segundos antes de mandar a próxima request)
    wait_time = between(1, 3)

    def on_start(self):
        """ Executado uma vez quando o usuário virtual é criado.
            Útil para fazer login ou gerar massa de dados inicial. """
        pass

    @task(3)
    def testar_home_api(self):
        """ Endpoint leve apenas para checar vazão de requisições pura do Django """
        self.client.get("/")

    @task(1)
    def testar_rota_critica_banco(self):
        """ Rota pesada que busca dados no MySQL. 
            O peso (1) em relação ao (3) da home simula um comportamento real 
            onde nem todo mundo clica no relatório pesado ao mesmo tempo. """
        self.client.get("/api/v1/relatorios-complexos/")