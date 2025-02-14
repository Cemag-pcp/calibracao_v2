# management/commands/importar_funcionarios_json.py
import json
from django.core.management.base import BaseCommand
from cadastro.models import Setor, Funcionario, Operadores

class Command(BaseCommand):
    help = 'Importa funcionários de um arquivo JSON para o banco de dados'

    def handle(self, *args, **kwargs):
        setores_administrativos = [
            'PCP', 'SESMT', 'COMPRAS', 'T.I - MANUTENCAO - REDE', 'T.I - DESENVOLVIMENTO', 
            'PROJETOS', 'COMERCIAL', 'GESTAO DE PESSOAS', 'CONTABILIDADE', 'GESTAO INDUSTRIAL', 
            'MARKETING'
        ]

        # Abre o arquivo JSON e carrega os dados
        with open('base_dados_funcionarios.json', 'r', encoding='utf-8') as jsonfile:
            dados = json.load(jsonfile)
            funcionarios = dados.get('funcionarios', [])

            for funcionario_data in funcionarios:
                matricula = funcionario_data['matricula']
                nome = funcionario_data['nome']
                setor_nome = funcionario_data['setor']

                # Verifica se já existe um funcionário com a mesma matrícula
                if Funcionario.objects.filter(matricula=matricula).exists():
                    self.stdout.write(self.style.WARNING(f'Funcionário com matrícula {matricula} já existe. Pulando...'))
                    continue

                # Verifica se o setor já existe, se não, cria um novo
                setor, created = Setor.objects.get_or_create(nome=setor_nome)

                # Cria o funcionário
                funcionario = Funcionario.objects.create(
                    matricula=matricula,
                    nome=nome,
                    setor=setor,
                    status='ativo'
                )

                # Se o setor não estiver na lista de setores administrativos, cria um operador com os mesmos dados
                if setor_nome not in setores_administrativos:
                    # Verifica se já existe um operador com a mesma matrícula
                    if Operadores.objects.filter(matricula=matricula).exists():
                        self.stdout.write(self.style.WARNING(f'Operador com matrícula {matricula} já existe. Pulando...'))
                    else:
                        Operadores.objects.create(
                            matricula=matricula,
                            nome=nome,
                            status='ativo'
                        )
                    self.stdout.write(self.style.SUCCESS(f'Operador {matricula} - {nome} importado com sucesso!'))


                self.stdout.write(self.style.SUCCESS(f'Funcionário {matricula} - {nome} importado com sucesso!'))