from typing import Optional
from sqlalchemy import ForeignKey, String, Float, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, Session
import os
from urllib.parse import quote_plus
from sqlalchemy_utils import database_exists, create_database, drop_database


# Configurações de conexão com o MySQL ou SQLite
username = os.getenv('MYSQL_USER')
password = quote_plus(os.getenv('MYSQL_PASS'))
server = "localhost"
port = "3306"
dbname = "diseasedx_test"
# connection_string = f"mysql+mysqlconnector://{username}:{password}@{server}:{port}/{dbname}"
# connection_string = "sqlite://"  # Se quiser criar uma db em memória
connection_string = "sqlite:///mylocaldb.db"  # Se quiser criar uma db local


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

    def __repr__(self):
        return f"{self.__class__.__name__}({self.id!r})"


class And(Expressao):
    __tablename__ = "and"
    id: Mapped[int] = mapped_column(ForeignKey("expressao.id"), primary_key=True)
    left_expr_id: Mapped[int] = mapped_column(ForeignKey("expressao.id"))
    right_expr_id: Mapped[int] = mapped_column(ForeignKey("expressao.id"))

    left_expr: Mapped[Expressao] = relationship("Expressao", foreign_keys=[left_expr_id])
    right_expr: Mapped[Expressao] = relationship("Expressao", foreign_keys=[right_expr_id])

    __mapper_args__ = {
        "polymorphic_identity": "and",
        "inherit_condition": id == Expressao.id,
    }

    # O construtor padrão espera 1 argumento e gera esse erro: TypeError: __init__() takes 1 positional argument but 3 were given
    def __init__(self, left: Expressao, right: Expressao):
        self.left_expr = left
        self.right_expr = right

    def __repr__(self):
        return f"{self.__class__.__name__}({self.left_expr!r}, {self.right_expr!r})"


class Or(Expressao):
    __tablename__ = "or"
    id: Mapped[int] = mapped_column(ForeignKey("expressao.id"), primary_key=True)
    left_expr_id: Mapped[int] = mapped_column(ForeignKey("expressao.id"))
    right_expr_id: Mapped[int] = mapped_column(ForeignKey("expressao.id"))

    left_expr: Mapped[Expressao] = relationship("Expressao", foreign_keys=[left_expr_id])
    right_expr: Mapped[Expressao] = relationship("Expressao", foreign_keys=[right_expr_id])

    __mapper_args__ = {
        "polymorphic_identity": "or",
        "inherit_condition": id == Expressao.id,
    }

    # O construtor padrão espera 1 argumento e gera esse erro: TypeError: __init__() takes 1 positional argument but 3 were given
    def __init__(self, left: Expressao, right: Expressao):
        self.left_expr = left
        self.right_expr = right

    def __repr__(self):
        return f"{self.__class__.__name__}({self.left_expr!r}, {self.right_expr!r})"



class Sintoma(Expressao):
    __tablename__ = "sintoma"
    id: Mapped[int] = mapped_column(ForeignKey("expressao.id"), primary_key=True)
    name: Mapped[str] = mapped_column(String(255))

    __mapper_args__ = {
        "polymorphic_identity": "sintoma",
    }

    def __repr__(self):
        return f"{self.__class__.__name__}({self.name!r})"


class Resultado(Expressao):
    __tablename__ = "resultado"
    id: Mapped[int] = mapped_column(ForeignKey("expressao.id"), primary_key=True)
    name: Mapped[str] = mapped_column(String(255))

    __mapper_args__ = {
        "polymorphic_identity": "resultado",
    }

    def __repr__(self):
        return f"{self.__class__.__name__}({self.name!r})"
    
# Adicionando classes para Doenca e Diagnostico

class Doenca(Base):
    __tablename__ = "doenca"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255))

    def __repr__(self):
        return f"{self.__class__.__name__}({self.name!r})"
    
class Diagnostico(Base):
    __tablename__ = "diagnostico"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    sensibilidade: Mapped[Optional[float]] = mapped_column(Float)
    especificidade: Mapped[Optional[float]] = mapped_column(Float)
    acuracia: Mapped[Optional[float]] = mapped_column(Float)
    doenca_id: Mapped[int] = mapped_column(ForeignKey("doenca.id"))
    expressao_id: Mapped[int] = mapped_column(ForeignKey("expressao.id"))
    
    doenca: Mapped[Doenca] = relationship("Doenca")
    expressao: Mapped[Expressao] = relationship("Expressao")
    
    def __repr__(self):
        return f"{self.__class__.__name__}({self.doenca!r}, {self.expressao!r})"


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
    dor_no_peito = Sintoma(name="Dor no peito")
    dor_no_abdome = Sintoma(name="Dor no abdome")
    artrite_no_ombro = Sintoma(name="Artrite no ombro")
    variante_mefv_patogenica = Resultado(name="Variante MEFV patogênica")
    vus_de_mefv = Resultado(name="VUS de MEFV")

    # Adicionando ao banco para garantir que tenham IDs
    session.add_all([dor_no_peito, dor_no_abdome, artrite_no_ombro, variante_mefv_patogenica, vus_de_mefv])
    session.commit()

    # Criando a expressão para a doença Familial Mediterranean Fever
    fmf_expr = Or(
        And(
            dor_no_peito,
            variante_mefv_patogenica
        ),
        And(
            vus_de_mefv,
            And(
                dor_no_abdome,
                artrite_no_ombro
            )
        )
    )

    print("\n--- Expression object created on memory before inserting in the database:")
    print(fmf_expr)
    print(type(fmf_expr))
    print()

    # Inserir as expressoes no banco de dados
    session.add(fmf_expr)
    session.commit()

    # Buscando a expressão no banco de dados usando o objeto criado
    statement = select(Expressao).where(Expressao.id == fmf_expr.id)
    expr = session.scalars(statement).first()

    print("\n--- Expression object returned from database:")
    print(expr)
    print(type(expr))
    print("\n")

    print(expr.left_expr)
    print(expr.right_expr)
    print(type(expr.left_expr))
    print(type(expr.right_expr))

    print(expr.left_expr.left_expr)
    print(expr.left_expr.right_expr)

    print(expr.right_expr.left_expr)
    print(expr.right_expr.right_expr)

    print(expr.right_expr.right_expr.left_expr)
    print(expr.right_expr.right_expr.right_expr)

    # Criando uma doença e um diagnóstico para a expressão

    fmf = Doenca(name="Familial Mediterranean Fever")
    session.add(fmf)
    session.commit()

    diag = Diagnostico(sensibilidade=0.94, especificidade=0.95, acuracia=0.98, doenca=fmf, expressao=fmf_expr)
    session.add(diag)
    session.commit()

    # Buscando o diagnóstico no banco de dados
    statement = select(Diagnostico).where(Diagnostico.id == diag.id)
    diag = session.scalars(statement).first()

    print("\n--- Diagnostic object returned from database:")
    print(diag)
    print(type(diag))
    print("\n")
    print(f"- Nome da doença: {diag.doenca}")
    print(f"- Expressão: {diag.expressao}")
    print(f"- Sensibilidade: {diag.sensibilidade}")
    print(f"- Especificidade: {diag.especificidade}")
    print(f"- Acurácia: {diag.acuracia}")