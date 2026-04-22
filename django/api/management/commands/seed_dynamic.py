import logging
import random
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
        parser.add_argument('--materials', type=int, default=5, help='Number of materials per project')
        parser.add_argument('--users', type=int, default=3, help='Number of users per project')
        parser.add_argument('--clear', action='store_true', help='Clear existing data before seeding')

    @transaction.atomic
    def handle(self, *args, **options):
        num_programs = options['programs']
        num_projects = options['projects']
        num_tasks = options['tasks']
        num_materials = options['materials']
        num_users = options['users']
        clear_db = options['clear']

        if clear_db:
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

        status_solicitacao_choices = ['Pendente', 'Cancelada', 'Rejeitada', 'Aprovada']
        status_pedido_choices = ['Aberto', 'Cancelado', 'Entregue', 'Enviado']
        status_projeto_choices = ['Planejamento', 'Em andamento', 'Concluído', 'Suspenso']
        status_tarefa_choices = ['Não iniciada', 'Em andamento', 'Concluído']

        # Categorias unificadas para Materiais e Fornecedores
        categorias_globais = ['Componentes Eletrônicos', 'Componentes Mecânicos', 'Placas de Circuito Impresso', 'Materiais de Solda', 'Sensores', 'Comunicação', 'Mecatrônica']

        total_projects = num_programs * num_projects
        
        global_fornecedores = {c: [] for c in categorias_globais}
        num_fornecedores_total = max(10, total_projects // 2)
        for _ in range(num_fornecedores_total):
            cat = random.choice(categorias_globais)
            f = DimFornecedor.objects.create(
                codigo_fornecedor=fake.unique.bothify(text='######').upper(),
                razao_social=fake.company()[:256],
                cidade=fake.city()[:256],
                estado=fake.state_abbr(),
                categoria=cat,
                status='Ativo'
            )
            global_fornecedores[cat].append(f)

        global_materiais = {c: [] for c in categorias_globais}
        num_materiais_total = max(20, total_projects * 2)
        for _ in range(num_materiais_total):
            cat = random.choice(categorias_globais)
            m = DimMaterial.objects.create(
                codigo_material=fake.unique.bothify(text='######').upper(),
                descricao=fake.sentence(nb_words=3)[:256],
                categoria=cat,
                fabricante=fake.company()[:256],
                custo_estimado=round(random.uniform(5.0, 500.0), 2),
                status='Ativo'
            )
            global_materiais[cat].append(m)

        for p_idx in range(num_programs):
            prog_start = fake.date_time_between(start_date='-2y', end_date='now').date()
            prog_end = prog_start + timedelta(days=random.randint(180, 730))
            
            programa = DimPrograma.objects.create(
                codigo_programa=fake.unique.bothify(text='######').upper(),
                nome_programa=fake.bs().title()[:256],
                gerente_programa=fake.name()[:256],
                gerente_tecnico=fake.name()[:256],
                data_inicio=get_or_create_dim_data(prog_start),
                data_fim_prevista=get_or_create_dim_data(prog_end),
                status=random.choice(['Em andamento', 'Concluído'])
            )

            for proj_idx in range(num_projects):
                # Bounded by program
                if prog_start == prog_end:
                    proj_start = prog_start
                    proj_end = prog_end
                else:
                    proj_start = random_date(prog_start, prog_end - timedelta(days=30))
                    proj_end = random_date(proj_start + timedelta(days=30), prog_end)
                
                project_users = [fake.name()[:256] for _ in range(num_users)]
                project_responsavel = random.choice(project_users) if project_users else fake.name()[:256]

                projeto = DimProjeto.objects.create(
                    codigo_projeto=fake.unique.bothify(text='######').upper(),
                    nome_projeto=fake.catch_phrase()[:256],
                    programa=programa,
                    responsavel=project_responsavel,
                    custo_hora=round(random.uniform(50.0, 300.0), 2),
                    data_inicio=get_or_create_dim_data(proj_start),
                    data_fim_prevista=get_or_create_dim_data(proj_end),
                    status=random.choice(status_projeto_choices),
                    lead_time_dias=random.randint(0, 10),
                    is_atrasado=random.choice([True, False])
                )

                if projeto.status == 'Planejamento': continue

                is_concluido = projeto.status == 'Concluído'

                for t_idx in range(num_tasks):
                    task_start = random_date(proj_start, proj_end)
                    task_end = random_date(task_start, proj_end)
                    responsavel_tarefa = random.choice(project_users) if project_users else fake.name()[:256]
                    
                    t_status = 'Concluído' if is_concluido else random.choice(status_tarefa_choices)

                    tarefa = DimTarefa.objects.create(
                        codigo_tarefa=fake.unique.bothify(text='######').upper(),
                        projeto=projeto,
                        titulo=fake.sentence(nb_words=4)[:256],
                        responsavel=responsavel_tarefa,
                        estimativa=random.randint(10, 200),
                        data_inicio=get_or_create_dim_data(task_start),
                        data_fim_prevista=get_or_create_dim_data(task_end),
                        status=t_status,
                        lead_time_dias=random.randint(0, 5),
                        is_atrasado=random.choice([True, False])
                    )

                    # Create some FatoTarefa entries indicating execution hours
                    for _ in range(random.randint(1, 3)):
                        execution_date = random_date(task_start, task_end)
                        FatoTarefa.objects.create(
                            usuario=responsavel_tarefa,
                            horas_trabalhadas=round(random.uniform(1.0, 8.0), 2),
                            tarefa=tarefa,
                            data=get_or_create_dim_data(execution_date)
                        )

                num_cats_to_pick = random.randint(1, len(categorias_globais))
                picked_cats = random.sample(categorias_globais, num_cats_to_pick)
                
                for cat in picked_cats:
                    if not global_materiais[cat]:
                        continue
                    
                    num_mat_in_cat = random.randint(1, min(5, len(global_materiais[cat])))
                    chosen_mats = random.sample(global_materiais[cat], num_mat_in_cat)
                    
                    for material in chosen_mats:
                        solic_date = random_date(proj_start, proj_end)
                        solicitacao_status = random.choice(['Aprovada', 'Cancelada', 'Rejeitada']) if is_concluido else random.choice(status_solicitacao_choices)
                        
                        solicitacao = DimSolicitacao.objects.create(
                            numero_solicitacao=fake.unique.bothify(text='######').upper(),
                            projeto=projeto,
                            material=material,
                            quantidade=random.randint(1, 1000),
                            data_solicitacao=get_or_create_dim_data(solic_date),
                            prioridade=random.choice(['Baixa', 'Média', 'Alta', 'Crítica']),
                            status=solicitacao_status
                        )
                        
                        if solicitacao_status == 'Aprovada':
                            pedido_date = random_date(solic_date, proj_end)
                            entrega_prev_date = pedido_date + timedelta(days=random.randint(5, 30))
                            
                            if global_fornecedores[cat]:
                                fornecedor = random.choice(global_fornecedores[cat])
                            else:
                                fornecedor = DimFornecedor.objects.create(
                                    codigo_fornecedor=fake.unique.bothify(text='######').upper(),
                                    razao_social=fake.company()[:256],
                                    cidade=fake.city()[:256],
                                    estado=fake.state_abbr(),
                                    categoria=cat,
                                    status='Ativo'
                                )
                                global_fornecedores[cat].append(fornecedor)

                            pedido_status = random.choice(['Entregue', 'Cancelado']) if is_concluido else random.choice(status_pedido_choices)
                            
                            pedido = FatoCompra.objects.create(
                                numero_pedido=fake.unique.bothify(text='######').upper(),
                                valor_total=round(material.custo_estimado * solicitacao.quantidade, 2),
                                status=pedido_status,
                                solicitacao=solicitacao,
                                fornecedor=fornecedor,
                                data_pedido=get_or_create_dim_data(pedido_date),
                                data_previsao_entrega=get_or_create_dim_data(entrega_prev_date)
                            )

                            if pedido_status == 'Entregue':
                                empenho_date = random_date(pedido_date, entrega_prev_date + timedelta(days=5))
                                
                                FatoEmpenho.objects.create(
                                    quantidade_empenhada=solicitacao.quantidade,
                                    projeto=projeto,
                                    material=material,
                                    data_empenho=get_or_create_dim_data(empenho_date)
                                )
        
        self.stdout.write(self.style.SUCCESS(f'Seed dinâmico concluído! '
                                             f'Criados {num_programs} programas, {num_projects} projetos por programa.'))
