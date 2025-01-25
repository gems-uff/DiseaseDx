import os
from sqlalchemy import create_engine
from urllib.parse import quote_plus
from sqlalchemy_utils import database_exists, create_database, drop_database
from sqlalchemy.orm import Session
from models import Base, Manifestacao, Orgao, RegiaoComposta, Sintoma, Exame, Resultado, Or, And, AoMenos, Doenca, Diagnostico



# Configuração do banco de dados
class DatabaseConfig:
    def __init__(self):
        self.username = os.getenv('MYSQL_USER')
        self.password = quote_plus(os.getenv('MYSQL_PASS'))
        self.server = "localhost"
        self.port = "3306"
        self.dbname = "diseasedx_test"
        self.connection_string = "sqlite://" #f"mysql+mysqlconnector://{self.username}:{self.password}@{self.server}:{self.port}/{self.dbname}" # "sqlite://" - Cria em memória / "sqlite:///mylocaldb.db" - Cria uma db local
        self.engine = create_engine(self.connection_string, echo=False)


    # Inicia o banco de dados com as tabelas definidas em models.py
    def init_db(self):
        if database_exists(self.engine.url):
            drop_database(self.engine.url)

        create_database(self.engine.url)

        Base.metadata.create_all(self.engine)

        self.populate_with_examples()

        return self.engine
    

    def populate_with_examples(self):
        with Session(self.engine, expire_on_commit=False) as session:

            # Criando os objetos de Manifestacao e RegiaoDoCorpo
            dor = Manifestacao(name="Dor")
            artrite = Manifestacao(name="Artrite")
            coceira = Manifestacao(name="Coceira")
            ombro = Orgao(name="Ombro")
            pulmao = Orgao(name="Pulmão")
            estomago = Orgao(name="Estômago")
            olho = Orgao(name="Olho")
            abdome = RegiaoComposta(name="Abdome", regioes=[estomago])
            torax = RegiaoComposta(name="Tórax", regioes=[pulmao])
            tronco = RegiaoComposta(name="Tronco", regioes=[abdome, torax])
            mao = RegiaoComposta(name="Mão")

            # Criando os objetos de Sintoma
            dor_no_tronco = Sintoma(dor, tronco)
            dor_no_abdome = Sintoma(dor, abdome)
            artrite_no_ombro = Sintoma(artrite, ombro)
            coceira_no_olho = Sintoma(coceira, olho)
            coceira_na_mao = Sintoma(coceira, mao)

            # Criando os objetos de Exame e Resultado
            exame_mefv = Exame(name="MEFV", preco="R$3500,00")
            variante_mefv_patogenica = Resultado(name="Variante MEFV patogênica", exame=exame_mefv)
            vus_de_mefv = Resultado(name="VUS de MEFV", exame=exame_mefv)

            # Criando a expressão para a doença Familial Mediterranean Fever
            fmf_expr = Or(
                And(
                    variante_mefv_patogenica,
                    AoMenos(
                        1,
                        [dor_no_tronco, dor_no_abdome, artrite_no_ombro]
                    )
                ),
                And(
                    vus_de_mefv,
                    AoMenos(
                        2,
                        [dor_no_tronco, dor_no_abdome, artrite_no_ombro]
                    )
                )
            )

            fmf2_expr = Or(
                And(
                    variante_mefv_patogenica,
                    coceira_na_mao
                ),
                And(
                    vus_de_mefv,
                    AoMenos(
                        2,
                        [dor_no_tronco, dor_no_abdome, coceira_no_olho]
                    )
                )
            )

            diabetes_expr = And(
                Resultado(name="Glicose > 126 mg/dL", exame=Exame(name="Glicemia de jejum", preco="R$50,00")),
                AoMenos(
                    2,
                    [
                        Sintoma(Manifestacao(name="Sede")),
                        Sintoma(Manifestacao(name="Vontade de urinar varias vezes"))
                    ]
                )
            )

            # Criando uma doença e um diagnóstico para a expressão
            fmf = Doenca(name="Familial Mediterranean Fever")
            diag = Diagnostico(sensibilidade=0.94, especificidade=0.95, acuracia=0.98, doenca=fmf, expressao=fmf_expr)

            fmf2 = Doenca(name="Familial Maisumteste Febre")
            diag = Diagnostico(sensibilidade=0.9, especificidade=0.84, acuracia=0.76, doenca=fmf2, expressao=fmf2_expr)

            diabetes = Doenca(name="Diabetes")
            diag = Diagnostico(doenca=diabetes, expressao=diabetes_expr)

            # Adicionando os objetos no banco de dados (so precisa adicionar a doenca, pois da doenca navega para o diagnostico e expressao)
            session.add(fmf)
            session.add(fmf2)
            session.add(diabetes)
            session.commit()