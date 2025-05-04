import os
import streamlit as st
from sqlalchemy import create_engine
from urllib.parse import quote_plus
from sqlalchemy_utils import database_exists, create_database, drop_database
from sqlalchemy.orm import Session
from models import Base, Manifestacao, Orgao, RegiaoComposta, Sintoma, Exame, Resultado, Or, And, AoMenos, Doenca, Diagnostico, Flyweight, FlyweightFactory


class DatabaseConfig:
    def __init__(self):
        self.username = os.getenv('MYSQL_USER')
        self.password = quote_plus(os.getenv('MYSQL_PASS'))
        self.server = "localhost"
        self.port = "3306"
        self.dbname = "diseasedx_test"
        self.connection_string = f"mysql+mysqlconnector://{self.username}:{self.password}@{self.server}:{self.port}/{self.dbname}"
        # self.connection_string = "sqlite:///mylocaldb.db" # python src/db_config.py to first create the database
        self.engine = create_engine(self.connection_string, echo=False)


    @st.cache_resource
    def load_engine(_self):
        return _self.engine
    

    def init_db(self):
        if database_exists(self.engine.url):
            print(f"Database {self.dbname} already exists. Dropping it...")
            drop_database(self.engine.url)
        create_database(self.engine.url)
        print(f"Database {self.dbname} created successfully.")
        Base.metadata.create_all(self.engine)
        print("Tables created successfully.")
        self.populate_with_examples()
        print("Populated database with example data.")
        

    def populate_with_examples(self):
        with Session(self.engine, expire_on_commit=False) as session:

            # Criando os objetos de Manifestacao
            dor = Manifestacao(name="Dor")
            artrite = Manifestacao(name="Artrite")
            coceira = Manifestacao(name="Coceira") # rash
            feb = Manifestacao(name="Febre")
            vermelhidao = Manifestacao(name="Vermelhidão")
            perda = Manifestacao(name="Perda")
            edema = Manifestacao(name="Edema")
            inflamacao = Manifestacao(name="Inflamação")
            inchaco = Manifestacao(name="Inchaço")
            ulcera = Manifestacao(name="Úlcera")
            coceira_mig = Manifestacao(name="Coceira Migratória")


            #Criando os objetos de Orgao
            ombro = Orgao(name="Ombro")
            pulmao = Orgao(name="Pulmão")
            estomago = Orgao(name="Estômago")
            olho = Orgao(name="Olho")
            ouvido = Orgao(name="Ouvido")
            osso = Orgao(name="Osso")
            boca = Orgao(name="Boca")


            # Criando os objetos de RegiaoComposta
            abdome = RegiaoComposta(name="Abdome", regioes=[estomago])
            torax = RegiaoComposta(name="Tórax", regioes=[pulmao])
            tronco = RegiaoComposta(name="Tronco", regioes=[abdome, torax])
            mao = RegiaoComposta(name="Mão")
            pele = RegiaoComposta(name="Pele")
            audicao = RegiaoComposta(name="Audição", regioes=[ouvido])
            musculo = RegiaoComposta(name="Músculo")
            periorbital = RegiaoComposta(name="Periorbital", regioes=[olho])
            gastrointestinal = RegiaoComposta(name="Gastrointestinal", regioes=[abdome])
            pescoco = RegiaoComposta(name="Pescoço")
            cervical = RegiaoComposta(name="Cervical", regioes=[pescoco])
            corpo = RegiaoComposta(name="Corpo")


            # Criando os objetos de Sintoma
            febre = Sintoma(feb)
            dor_no_tronco = Sintoma(dor, tronco)
            dor_no_abdome = Sintoma(dor, abdome)
            artrite_no_ombro = Sintoma(artrite, ombro)
            coceira_no_olho = Sintoma(coceira, olho)
            coceira_na_mao = Sintoma(coceira, mao)
            coceira_na_pele = Sintoma(coceira, pele)
            vermelhidao_no_olho = Sintoma(vermelhidao, olho)
            perda_de_audição = Sintoma(perda, audicao)
            artrite_no_corpo = Sintoma(artrite, corpo)
            dor_no_peito = Sintoma(dor, torax)
            dor_muscular = Sintoma(dor, musculo)
            coceira_migratoria = Sintoma(coceira_mig)
            edema_periorbital = Sintoma(edema, periorbital)
            inflamacao_gastrointestinal = Sintoma(inflamacao, gastrointestinal)
            inchaco_cervical = Sintoma(inchaco, cervical)
            ulcera_na_boca = Sintoma(ulcera, boca)


            # Criando os objetos de Exame e Resultado
            exame_nlrp3 = Exame(name="NLRP3", preco="R$3500,00")
            variante_nlrp3_patogenica = Resultado(name="Variante NLRP3 patogênica", exame=exame_nlrp3)
            vus_de_nlrp3 = Resultado(name="VUS de NLRP3", exame=exame_nlrp3)

            exame_mefv = Exame(name="MEFV", preco="R$3000,00")
            variante_mefv_patogenica = Resultado(name="Variante MEFV patogênica", exame=exame_mefv)
            vus_de_mefv = Resultado(name="VUS de MEFV", exame=exame_mefv)

            exame_tnfrsf1a = Exame(name="TNFRSF1A", preco="R$3300,00")
            variante_tnfrsf1a_patogenica = Resultado(name="Variante TNFRSF1A patogênica", exame=exame_tnfrsf1a)
            vus_de_tnfrsf1a = Resultado(name="VUS de TNFRSF1A", exame=exame_tnfrsf1a)

            exame_mvk = Exame(name="MVK", preco="R$3200,00")
            variante_mvk_patogenica = Resultado(name="Variante MVK patogênica", exame=exame_mvk)
            vus_de_mvk = Resultado(name="VUS de MVK", exame=exame_mvk)


            # Criando os ojetos das Expressões
            nlrp3_expr = Or(
                And(
                    variante_nlrp3_patogenica,
                    AoMenos(
                        1,
                        [coceira_na_pele, vermelhidao_no_olho, perda_de_audição]
                    )
                ),
                And(
                    vus_de_nlrp3,
                    AoMenos(
                        2,
                        [coceira_na_pele, vermelhidao_no_olho, perda_de_audição]
                    )
                )
            )

            fmf_expr = Or(
                And(
                    variante_mefv_patogenica,
                    AoMenos(
                        1,
                        [febre, dor_no_peito, dor_no_abdome, artrite_no_corpo]
                    )
                ),
                And(
                    vus_de_mefv,
                    AoMenos(
                        2,
                        [febre, dor_no_peito, dor_no_abdome, artrite_no_corpo]
                    )
                )
            )

            tnfrsf1a_expr = Or(
                And(
                    variante_tnfrsf1a_patogenica,
                    AoMenos(
                        1,
                        [dor_muscular, coceira_migratoria, edema_periorbital]
                    )
                ),
                And(
                    vus_de_tnfrsf1a,
                    AoMenos(
                        2,
                        [dor_muscular, coceira_migratoria, edema_periorbital]
                    )
                )
            )

            mvk_expr = And(
                variante_mvk_patogenica,
                AoMenos(
                    1,
                    [inflamacao_gastrointestinal, inchaco_cervical, ulcera_na_boca]
                )
            )


            # Criando uma doença e um diagnóstico para a expressão
            caps = Doenca(name="Cryopyrin-Associated Periodic Syndromes")
            diag = Diagnostico(sensibilidade=1, especificidade=1, acuracia=1, doenca=caps, expressao=nlrp3_expr)

            fmf = Doenca(name="Familial Mediterranean Fever")
            diag = Diagnostico(sensibilidade=0.94, especificidade=0.95, acuracia=0.98, doenca=fmf, expressao=fmf_expr)

            traps = Doenca(name="TNFRSF1A-Associated Periodic Syndrome")
            diag = Diagnostico(sensibilidade=0.95, especificidade=0.99, acuracia=0.99, doenca=traps, expressao=tnfrsf1a_expr)

            mkd = Doenca(name="Mevalonate Kinase Deficiency")
            diag = Diagnostico(sensibilidade=0.98, especificidade=1, acuracia=1, doenca=mkd, expressao=mvk_expr)

            # Adicionando os objetos no banco de dados (so precisa adicionar a doenca, pois da doenca navega para o diagnostico e expressao)
            session.add(caps)
            session.add(fmf)
            session.add(traps)
            session.add(mkd)

            
            # Fake expressions for testing
            exame_fake1 = Exame(name="Fake Exame 1", preco="R$1000,00")
            sintoma_fake1 = Sintoma(ulcera, audicao)
            sintoma_fake2 = Sintoma(feb, olho)
            sintoma_fake3 = Sintoma(coceira, gastrointestinal)
            present_resultado_fake = Resultado(name="Present Fake Result", exame=exame_fake1)
            vus_resultado_fake = Resultado(name="VUS Fake Result", exame=exame_fake1)
            fake_1 = Or(And(present_resultado_fake, AoMenos(1, [sintoma_fake1, sintoma_fake2, sintoma_fake3])), And(vus_resultado_fake, AoMenos(2, [sintoma_fake1, sintoma_fake2, sintoma_fake3])))
            fake_2 = Or(And(present_resultado_fake, AoMenos(1, [sintoma_fake1, sintoma_fake3])), And(vus_resultado_fake, AoMenos(2, [sintoma_fake1, sintoma_fake3])))
            fake_3 = Or(And(present_resultado_fake, AoMenos(1, [sintoma_fake2, sintoma_fake3])), And(vus_resultado_fake, AoMenos(2, [sintoma_fake2, sintoma_fake3])))
            fake1disease = Doenca(name="Fake Disease 1")
            fake1diag = Diagnostico(sensibilidade=0.99, especificidade=0.99, acuracia=0.99, doenca=fake1disease, expressao=fake_1)
            fake2disease = Doenca(name="Fake Disease 2")
            fake2diag = Diagnostico(sensibilidade=0.99, especificidade=0.99, acuracia=0.99, doenca=fake2disease, expressao=fake_2)
            fake3disease = Doenca(name="Fake Disease 3")
            fake3diag = Diagnostico(sensibilidade=0.99, especificidade=0.99, acuracia=0.99, doenca=fake3disease, expressao=fake_3)
            session.add(fake1disease)
            session.add(fake2disease)
            session.add(fake3disease)
            # End Fake expressions for testing


            session.commit()

if __name__ == "__main__":
    db_config = DatabaseConfig()
    try:
        db_config.init_db()
        print("Database initialized successfully!")
    except Exception as e:
        print(e)
        print(f"Error while initializing database: {e}")