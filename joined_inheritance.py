from typing import Optional
from sqlalchemy import ForeignKey, String, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, Session
import os
from urllib.parse import quote_plus
from sqlalchemy_utils import database_exists, create_database, drop_database


# Printa o objeto recursivamente para visualização
def print_object(o, tabdepth=0):
    for key, value in o.__dict__.items():
        print('\t' * tabdepth + key)
        if hasattr(value, '__dict__'):
            print_object(value, tabdepth + 1)
        else:
            print('\t' * (tabdepth + 1), value)


# Configurações de conexão com o MySQL ou SQLite
username = os.getenv('MYSQL_USER')
password = quote_plus(os.getenv('MYSQL_PASS'))
server = "localhost"
port = "3306"
dbname = "diseasedx_test"
connection_string = f"mysql+mysqlconnector://{username}:{password}@{server}:{port}/{dbname}"
# connection_string = "sqlite://"  # Se quiser criar uma db em memória
# connection_string = "sqlite:///mylocaldb.db"  # Se quiser criar uma db local


# Classe base declarativa
class Base(DeclarativeBase):
    pass


class Expressao(Base):
    __tablename__ = "expressao"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    type: Mapped[str] = mapped_column(String(255)) # Coluna discriminadora para o tipo de expressão 

    __mapper_args__ = {
        "polymorphic_identity": "expressao",
        "polymorphic_on": "type",
    }


class And(Expressao):
    __tablename__ = "and"
    id: Mapped[int] = mapped_column(ForeignKey("expressao.id"), primary_key=True)
    left_expr: Mapped[Optional[int]] = mapped_column(ForeignKey("expressao.id"))
    right_expr: Mapped[Optional[int]] = mapped_column(ForeignKey("expressao.id"))

    __mapper_args__ = {
        "polymorphic_identity": "and",
        "inherit_condition": id == Expressao.id,  # Especifica como herdar a tabela base
    }

    def __init__(self, left: Expressao, right: Expressao):
        self.left_expr = left.id
        self.right_expr = right.id


class Or(Expressao):
    __tablename__ = "or"
    id: Mapped[int] = mapped_column(ForeignKey("expressao.id"), primary_key=True)
    left_expr: Mapped[Optional[int]] = mapped_column(ForeignKey("expressao.id"))
    right_expr: Mapped[Optional[int]] = mapped_column(ForeignKey("expressao.id"))

    __mapper_args__ = {
        "polymorphic_identity": "or",
        "inherit_condition": id == Expressao.id,  # Especifica como herdar a tabela base
    }

    def __init__(self, left: Expressao, right: Expressao):
        self.left_expr = left.id
        self.right_expr = right.id



class Sintoma(Expressao):
    __tablename__ = "sintoma"
    id: Mapped[int] = mapped_column(ForeignKey("expressao.id"), primary_key=True)
    name: Mapped[str] = mapped_column(String(255))

    __mapper_args__ = {
        "polymorphic_identity": "sintoma",
    }


class Resultado(Expressao):
    __tablename__ = "resultado"
    id: Mapped[int] = mapped_column(ForeignKey("expressao.id"), primary_key=True)
    name: Mapped[str] = mapped_column(String(255))

    __mapper_args__ = {
        "polymorphic_identity": "resultado",
    }


# Criando engine para conectar ao banco de dados
engine = create_engine(connection_string, echo=False) # echo=True para ver as queries executadas


# Verifica se o banco de dados existe e o deleta
if database_exists(engine.url):
    drop_database(engine.url)

create_database(engine.url)

Base.metadata.create_all(engine)  # Cria as tabelas com o esquema atualizado


# Iniciando uma sessão para inserir dados no banco de dados
with Session(engine) as session:

    # Criando os objetos previamente para nao duplicar a entrada no banco de dados
    dor_de_cabeca = Sintoma(name="Dor de cabeça")
    febre = Sintoma(name="Febre")
    ferro_alto = Resultado(name="Ferro alto")
    variante_mefv_patogenica = Resultado(name="Variante MEFV patogênica")
    vus_de_mefv = Resultado(name="VUS de MEFV")
    dor_no_peito = Sintoma(name="Dor no peito")

    session.add_all([dor_de_cabeca, febre, ferro_alto, variante_mefv_patogenica, vus_de_mefv, dor_no_peito])
    session.commit()

    # Criando a expressão para a doença Familial Mediterranean Fever
    fmf_expr = Or(
        And(
            variante_mefv_patogenica,
            febre
        ),
        And(
            vus_de_mefv,
            And(
                dor_de_cabeca,
                dor_no_peito
            )
        )
    )

    # print("\n\nObject created on memory before inserting in the database:")
    # print_object(fmf_expr)
    # print("\n\n")

    # Inserir as expressoes no banco de dados
    session.add(fmf_expr)
    session.commit()

    # Buscando a expressão no banco de dados usando o objeto criado
    statement = select(Expressao).where(Expressao.id == fmf_expr.id)
    result = session.execute(statement).scalars().first()
    # print("\n\nObject returned from database:")
    # print_object(result)
    # print("\n\n\n")
    print(result)