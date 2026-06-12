FROM grafana/grafana:latest

# Remove os dashboards padrão
RUN rm -rf /var/lib/grafana/dashboards/*

# Copia as configurações de provisionamento (YAMLs)
COPY ./provisioning/dashboards /etc/grafana/provisioning/dashboards
COPY ./provisioning/datasources /etc/grafana/provisioning/datasources

# !!! IMPORTANTE: Copia os arquivos JSON dos dashboards para o local correto
# Verifique se o seu dashboards.yaml aponta para /var/lib/grafana/dashboards
COPY ./dashboards_models/*.json /var/lib/grafana/dashboards/

# Ajuste de permissões
USER root
RUN chown -R grafana:grafana /etc/grafana/provisioning/ /var/lib/grafana/dashboards/
USER grafana