import logging
import random
import time
import uuid
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from faker import Faker
from api.models import (
    DimData, DimPrograma, DimProjeto, DimTarefa, DimMaterial,
    DimFornecedor, DimSolicitacao, FatoTarefa, FatoEmpenho, FatoCompra
)

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Popula o DW com dados dinâmicos utilizando Faker, respeitando regras de negócio.'

    def add_arguments(self, parser):
        parser.add_argument('--programs', type=int, default=1, help='Number of programs to create')
        parser.add_argument('--projects', type=int, default=3, help='Number of projects per program')
        parser.add_argument('--tasks', type=int, default=5, help='Number of tasks per project')
        parser.add_argument('--users', type=int, default=3, help='Number of users per project')
        parser.add_argument('--clear', action='store_true', help='Clear existing data before seeding')

    @transaction.atomic
    def handle(self, *args, **options):
        num_programs = options['programs']
        num_projects = options['projects']
        num_tasks = options['tasks']
        num_users = options['users']
        clear_db = options['clear']

        if clear_db:
            start_clear = time.time()
            self.stdout.write(self.style.WARNING('Limpando dados existentes...'))
            FatoCompra.objects.all().delete()
            FatoEmpenho.objects.all().delete()
            FatoTarefa.objects.all().delete()
            DimSolicitacao.objects.all().delete()
            DimFornecedor.objects.all().delete()
            DimMaterial.objects.all().delete()
            DimTarefa.objects.all().delete()
            DimProjeto.objects.all().delete()
            DimPrograma.objects.all().delete()
            DimData.objects.all().delete()
            self.stdout.write(self.style.WARNING(f'Tabelas limpas em {time.time() - start_clear:.2f} segundos.'))

        global_start = time.time()
        self.stdout.write(self.style.SUCCESS('Iniciando seed dinâmico...'))
        fake = Faker('pt_BR')

        dim_data_cache = {}
        def get_or_create_dim_data(dt_obj):
            if dt_obj in dim_data_cache:
                return dim_data_cache[dt_obj]
            dim_data, _ = DimData.objects.get_or_create(
                dia=dt_obj.day,
                mes=dt_obj.month,
                ano=dt_obj.year
            )
            dim_data_cache[dt_obj] = dim_data
            return dim_data

        def random_date(start_dt, end_dt):
            delta = end_dt - start_dt
            if delta.days <= 0:
                return start_dt
            random_days = random.randrange(delta.days)
            return start_dt + timedelta(days=random_days)

        status_tarefa_choices = ['Não iniciada', 'Em andamento', 'Concluído']

        # Categorias unificadas para Materiais e Fornecedores
        categorias_globais = ['Componentes Eletrônicos', 'Componentes Mecânicos', 'Placas de Circuito Impresso', 'Materiais de Solda', 'Sensores', 'Comunicação', 'Mecatrônica']

        total_projects = num_programs * num_projects
        
        global_fornecedores = {c: [] for c in categorias_globais}
        num_fornecedores_total = max(10, total_projects // 2)
        for _ in range(num_fornecedores_total):
            cat = random.choice(categorias_globais)
            f = DimFornecedor.objects.create(
                codigo_fornecedor=uuid.uuid4().hex[:6].upper(),
                razao_social=fake.company()[:256],
                cidade=fake.city()[:256],
                estado=fake.state_abbr(),
                categoria=cat,
                status='Ativo'
            )
            global_fornecedores[cat].append(f)

        global_materiais = {c: [] for c in categorias_globais}
        num_materiais_total = max(50, total_projects * 10)
        for _ in range(num_materiais_total):
            cat = random.choice(categorias_globais)
            m = DimMaterial.objects.create(
                codigo_material=uuid.uuid4().hex[:6].upper(),
                descricao=f"{random.choice(['Módulo', 'Componente', 'Peça', 'Conjunto', 'Estrutura'])} de {cat} - {fake.bothify(text='???-####').upper()}"[:256],
                categoria=cat,
                fabricante=fake.company()[:256],
                custo_estimado=round(random.uniform(5.0, 500.0), 2),
                status='Ativo'
            )
            global_materiais[cat].append(m)

        for p_idx in range(num_programs):
            prog_start = fake.date_time_between(start_date='-5y', end_date='-1y').date()
            prog_end = prog_start + timedelta(days=random.randint(1095, 3650))
            
            programa = DimPrograma.objects.create(
                codigo_programa=uuid.uuid4().hex[:6].upper(),
                nome_programa=f"Programa {fake.company()} - {fake.catch_phrase().title()}"[:256],
                gerente_programa=fake.name()[:256],
                gerente_tecnico=fake.name()[:256],
                data_inicio=get_or_create_dim_data(prog_start),
                data_fim_prevista=get_or_create_dim_data(prog_end),
                status=random.choice(['Em andamento', 'Concluído'])
            )

            for proj_idx in range(num_projects):
                # Project: 6 months to 3 years (180 to 1095 days)
                project_duration_days = random.randint(180, 1095)
                max_start_date = prog_end - timedelta(days=project_duration_days)
                
                if max_start_date <= prog_start:
                    proj_start = prog_start
                    proj_end = prog_end
                else:
                    proj_start = random_date(prog_start, max_start_date)
                    proj_end = proj_start + timedelta(days=project_duration_days)
                
                # Densidade proporcional ao mês
                duration_ratio = max(1.0, project_duration_days / 30.0)
                scaled_tasks = int(num_tasks * duration_ratio)
                scaled_users = max(1, int(num_users * duration_ratio))
                
                project_users = [fake.name()[:256] for _ in range(scaled_users)]
                project_responsavel = random.choice(project_users) if project_users else fake.name()[:256]

                today = timezone.now().date()
                if proj_start > today:
                    proj_status = 'Planejamento'
                elif proj_end < today:
                    proj_status = random.choice(['Concluído', 'Em andamento', 'Suspenso'])
                else:
                    proj_status = random.choice(['Em andamento', 'Suspenso'])

                projeto = DimProjeto.objects.create(
                    codigo_projeto=uuid.uuid4().hex[:6].upper(),
                    nome_projeto=fake.catch_phrase()[:256],
                    programa=programa,
                    responsavel=project_responsavel,
                    custo_hora=round(random.uniform(50.0, 300.0), 2),
                    data_inicio=get_or_create_dim_data(proj_start),
                    data_fim_prevista=get_or_create_dim_data(proj_end),
                    status=proj_status,
                    lead_time_dias=random.randint(0, 10),
                    is_atrasado=(proj_end < today and proj_status == 'Em andamento')
                )

                is_concluido = proj_status == 'Concluído'
                is_planejamento = proj_status == 'Planejamento'

                count_tarefas = 0
                count_fatos_tarefa = 0
                count_solicitacoes = 0
                count_pedidos = 0
                count_empenhos = 0

                for t_idx in range(scaled_tasks):
                    estimativa_horas = random.randint(2, 40)
                    estimativa_dias = (estimativa_horas + 7) // 8
                    
                    max_start = proj_end - timedelta(days=estimativa_dias)
                    if max_start < proj_start:
                        max_start = proj_start
                        
                    task_start = random_date(proj_start, max_start)
                    task_end = task_start + timedelta(days=estimativa_dias)
                    
                    responsavel_tarefa = random.choice(project_users) if project_users else fake.name()[:256]
                    
                    if is_planejamento:
                        t_status = 'Não iniciada'
                    elif is_concluido:
                        t_status = 'Concluído'
                    else:
                        t_status = random.choice(status_tarefa_choices)

                    tarefa = DimTarefa.objects.create(
                        codigo_tarefa=uuid.uuid4().hex[:6].upper(),
                        projeto=projeto,
                        titulo=f"{random.choice(['Analisar', 'Desenvolver', 'Testar', 'Projetar', 'Revisar', 'Homologar'])} {random.choice(['módulo', 'sistema', 'interface', 'integração', 'componente', 'circuito'])} {fake.bothify(text='??-##').upper()}"[:256],
                        responsavel=responsavel_tarefa,
                        estimativa=estimativa_horas,
                        data_inicio=get_or_create_dim_data(task_start),
                        data_fim_prevista=get_or_create_dim_data(task_end),
                        status=t_status,
                        lead_time_dias=random.randint(0, 5),
                        is_atrasado=random.choice([True, False])
                    )
                    count_tarefas += 1

                    # Lógica de FatoTarefa baseada no status
                    if t_status == 'Não iniciada':
                        pass # Sem logs de horas
                        
                    elif t_status in ('Concluído', 'Em andamento'):
                        if t_status == 'Concluído':
                            target_hours = float(tarefa.estimativa)
                        else:
                            target_hours = float(tarefa.estimativa) * random.uniform(0.1, 0.9)
                            
                        # Equipe de execução para a tarefa (1 membro a cada ~40h)
                        team_size = max(1, min(len(project_users), int(target_hours / 40) + 1))
                        task_team = random.sample(project_users, team_size)
                        
                        hours_created = 0.0
                        while target_hours - hours_created > 0.01:
                            execution_date = random_date(task_start, task_end)
                            remaining = target_hours - hours_created
                            
                            # Limite realista de 8 horas por dia por pessoa
                            horas = round(min(remaining, random.uniform(2.0, 8.0)), 2)
                            hours_created += horas
                            
                            FatoTarefa.objects.create(
                                usuario=random.choice(task_team),
                                horas_trabalhadas=horas,
                                tarefa=tarefa,
                                data=get_or_create_dim_data(execution_date)
                            )
                            count_fatos_tarefa += 1

                num_cats_to_pick = random.randint(1, len(categorias_globais))
                picked_cats = random.sample(categorias_globais, num_cats_to_pick)
                
                for cat in picked_cats:
                    if not global_materiais[cat]:
                        continue
                    
                    num_mat_in_cat = random.randint(min(3, len(global_materiais[cat])), min(15, len(global_materiais[cat])))
                    chosen_mats = random.sample(global_materiais[cat], num_mat_in_cat)
                    
                    for material in chosen_mats:
                        # Em média, um suprimento é pedido a cada semestre de duração para conter o volume
                        max_batches = max(2, int(duration_ratio / 6))
                        num_batches = random.randint(1, max_batches)
                        for _ in range(num_batches):
                            solic_date = random_date(proj_start, proj_end)
                            
                            if is_planejamento:
                                solicitacao_status = random.choices(['Pendente', 'Cancelada', 'Rejeitada'], weights=[80, 15, 5], k=1)[0]
                            elif is_concluido:
                                solicitacao_status = random.choices(['Aprovada', 'Cancelada', 'Rejeitada'], weights=[90, 5, 5], k=1)[0]
                            else:
                                solicitacao_status = random.choices(['Pendente', 'Cancelada', 'Rejeitada', 'Aprovada'], weights=[20, 5, 5, 70], k=1)[0]
                            
                            solicitacao = DimSolicitacao.objects.create(
                                numero_solicitacao=uuid.uuid4().hex[:6].upper(),
                                projeto=projeto,
                                material=material,
                                quantidade=random.randint(1, 1000),
                                data_solicitacao=get_or_create_dim_data(solic_date),
                                prioridade=random.choice(['Baixa', 'Média', 'Alta', 'Crítica']),
                                status=solicitacao_status
                            )
                            count_solicitacoes += 1
                        
                            if solicitacao_status == 'Aprovada':
                                pedido_date = random_date(solic_date, proj_end)
                                entrega_prev_date = pedido_date + timedelta(days=random.randint(5, 30))
                                
                                if global_fornecedores[cat]:
                                    fornecedor = random.choice(global_fornecedores[cat])
                                else:
                                    fornecedor = DimFornecedor.objects.create(
                                        codigo_fornecedor=uuid.uuid4().hex[:6].upper(),
                                        razao_social=fake.company()[:256],
                                        cidade=fake.city()[:256],
                                        estado=fake.state_abbr(),
                                        categoria=cat,
                                        status='Ativo'
                                    )
                                    global_fornecedores[cat].append(fornecedor)

                                if is_concluido:
                                    pedido_status = random.choices(['Entregue', 'Cancelado'], weights=[95, 5], k=1)[0]
                                elif entrega_prev_date <= today:
                                    pedido_status = random.choices(['Entregue', 'Cancelado'], weights=[95, 5], k=1)[0]
                                else:
                                    pedido_status = random.choices(['Aberto', 'Cancelado', 'Entregue', 'Enviado'], weights=[15, 5, 55, 25], k=1)[0]
                                
                                pedido = FatoCompra.objects.create(
                                    numero_pedido=uuid.uuid4().hex[:6].upper(),
                                    valor_total=round(material.custo_estimado * solicitacao.quantidade, 2),
                                    status=pedido_status,
                                    solicitacao=solicitacao,
                                    fornecedor=fornecedor,
                                    data_pedido=get_or_create_dim_data(pedido_date),
                                    data_previsao_entrega=get_or_create_dim_data(entrega_prev_date)
                                )
                                count_pedidos += 1

                                if pedido_status == 'Entregue':
                                    consumption_date = random_date(pedido_date, entrega_prev_date + timedelta(days=5))
                                    
                                    target_qty = solicitacao.quantidade
                                    qty_consumed = 0
                                    num_empenhos = random.randint(1, 5)
                                    
                                    for i in range(num_empenhos):
                                        remain = target_qty - qty_consumed
                                        if remain <= 0: break
                                        
                                        if i == num_empenhos - 1:
                                            qty = remain
                                        else:
                                            limit_qty = remain // 2
                                            qty = random.randint(1, limit_qty) if limit_qty >= 1 else remain
                                            
                                        qty_consumed += qty
                                        
                                        FatoEmpenho.objects.create(
                                            quantidade_empenhada=qty,
                                            projeto=projeto,
                                            material=material,
                                            data_empenho=get_or_create_dim_data(consumption_date)
                                        )
                                        count_empenhos += 1
                                        
                                        if consumption_date < proj_end:
                                            # Advance date for the next proportional release
                                            consumption_date = random_date(consumption_date + timedelta(days=1), proj_end)

                self.stdout.write(f'    -> Projeto "{projeto.nome_projeto[:30]}..." [ID: {projeto.codigo_projeto}] ({projeto.status}, {project_duration_days} dias): '
                                  f'{count_tarefas} Tarefas ({count_fatos_tarefa} fatos tarefa), {scaled_users} usuários, '
                                  f'{count_solicitacoes} Solic., {count_pedidos} Pedidos, {count_empenhos} Empenhos.')
        
            elapsed = time.time() - global_start
            self.stdout.write(f'  - [{p_idx+1}/{num_programs}] Programa "{programa.nome_programa}" [ID: {programa.codigo_programa}] gerado em {elapsed:.2f} segundos.')
            
        final_elapsed = time.time() - global_start
        self.stdout.write(self.style.SUCCESS(f'Seed dinâmico concluído em {final_elapsed:.2f} segundos! '
                                             f'Criados {num_programs} programas, {num_projects} projetos por programa.'))
