from typing import Optional
from sqlalchemy import ForeignKey, String, Float, Integer, Table, Column, create_engine, select
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
connection_string = f"mysql+mysqlconnector://{username}:{password}@{server}:{port}/{dbname}"
# connection_string = "sqlite://"  # Se quiser criar uma db em memória
# connection_string = "sqlite:///mylocaldb.db"  # Se quiser criar uma db local


# Classe base declarativa
class Base(DeclarativeBase):
    pass


ao_menos_expressoes = Table(
    "ao_menos_expressoes",
    Base.metadata,
    Column("ao_menos_id", Integer, ForeignKey("ao_menos.id"), primary_key=True),
    Column("expressao_id", Integer, ForeignKey("expressao.id"), primary_key=True)
)


class Expressao(Base):
    __tablename__ = "expressao"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    type: Mapped[str] = mapped_column(String(255)) # Coluna discriminadora para o tipo de expressão

    ao_menos_expr: Mapped[list["AoMenos"]] = relationship("AoMenos", secondary=ao_menos_expressoes, back_populates="expressoes")

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


class AoMenos(Expressao):
    __tablename__ = "ao_menos"
    id: Mapped[int] = mapped_column(ForeignKey("expressao.id"), primary_key=True)
    qtd: Mapped[int] = mapped_column(Integer)

    expressoes: Mapped[list["Expressao"]] = relationship("Expressao", secondary=ao_menos_expressoes, back_populates="ao_menos_expr")

    __mapper_args__ = {
        "polymorphic_identity": "ao_menos"
    }

    def __init__(self, qtd: int, expressoes: list[Expressao]):
        self.qtd = qtd
        self.expressoes = expressoes

    def __repr__(self):
        return f"{self.__class__.__name__}({self.qtd!r})({self.expressoes!r})"


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
    diagnostico: Mapped["Diagnostico"] = relationship("Diagnostico", back_populates="doenca") # Doenca tem 1 Diagnostico e Diagnostico tem 1 Expressao que tem 1 ou mais Expressoes

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
    
    doenca: Mapped[Doenca] = relationship("Doenca", back_populates="diagnostico")
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

    # Criando a expressão para a doença Familial Mediterranean Fever
    fmf_expr = Or(
        And(
            variante_mefv_patogenica,
            AoMenos(
                1,
                [dor_no_peito, dor_no_abdome, artrite_no_ombro]
            )
        ),
        And(
            vus_de_mefv,
            AoMenos(
                2,
                [dor_no_peito, dor_no_abdome, artrite_no_ombro]
            )
        )
    )

    # Criando uma doença e um diagnóstico para a expressão
    fmf = Doenca(name="Familial Mediterranean Fever")
    diag = Diagnostico(sensibilidade=0.94, especificidade=0.95, acuracia=0.98, doenca=fmf, expressao=fmf_expr)

    # Verificando o objeto criado em memoria
    print("\n### Objeto Doenca FMF criado em memoria antes de ser adicionado ao banco de dados:")
    print(fmf)
    print(type(fmf))
    print()

    # Adicionando os objetos no banco de dados (so precisa adicionar a doenca, pois da doenca navega para o diagnostico e expressao)
    session.add(fmf)
    session.commit()

    # Buscando a expressão no banco de dados usando o objeto criado
    statement = select(Doenca).where(Doenca.name == "Familial Mediterranean Fever")
    doenca = session.scalars(statement).first()

    # Verificando o objeto Doenca recuperado do banco de dados
    print("\n### Objeto Doenca FMF recuperado do banco de dados:")
    print(doenca)
    print(type(doenca))
    print()

    # Navegando para o Diagnostico a partir da Doenca
    diagnostico = doenca.diagnostico
    print("\n### Diagnostico a partir da Doenca FMF:")
    print(diagnostico)
    print()
    print(f"Nome da doença: {diagnostico.doenca}")
    print(f"Expressão: {diagnostico.expressao}")
    print(f"Sensibilidade: {diagnostico.sensibilidade}")
    print(f"Especificidade: {diagnostico.especificidade}")
    print(f"Acurácia: {diagnostico.acuracia}")
    print()

    # Navegando para a Expressao a partir do Diagnostico
    expr = diagnostico.expressao
    print("\n### Expressao a partir do Diagnostico:")
    print(expr)
    print(type(expr))
    print()

    # Navegando para as Expressoes do AoMenos a partir da Expressao do Diagnostico
    ao_menos = expr.left_expr.right_expr # Rever se tem como navegar para ca melhor
    print("\n### Expressoes do AoMenos a partir da Expressao:")
    print(ao_menos)
    print(type(ao_menos))
    print()

    print(ao_menos.qtd)
    for expressao in ao_menos.expressoes:
        print(expressao)