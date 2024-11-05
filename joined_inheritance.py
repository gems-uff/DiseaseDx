from typing import Optional
from sqlalchemy import ForeignKey, String, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, Session
import os
from urllib.parse import quote_plus


# Configurações de conexão com o MySQL ou SQLite
username = os.getenv('MYSQL_USER')
password = quote_plus(os.getenv('MYSQL_PASS'))
server = "localhost"
port = "3306"
dbname = "diseasedx_test"
connection_string = f"mysql+mysqlconnector://{username}:{password}@{server}:{port}/{dbname}"
# connection_string = "sqlite://"  # Se quiser usar em memoria


# Classe base declarativa
class Base(DeclarativeBase):
    pass


class Expressao(Base):
    __tablename__ = "expressao"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    expr: Mapped[str] = mapped_column(String(255))

    __mapper_args__ = {
        "polymorphic_on": "expr"
    }


class And(Expressao):
    __tablename__ = "and"
    id: Mapped[int] = mapped_column(ForeignKey("expressao.id"), primary_key=True)
    left_id: Mapped[Optional[int]] = mapped_column(ForeignKey("expressao.id"))
    right_id: Mapped[Optional[int]] = mapped_column(ForeignKey("expressao.id"))
    
    left_expr = relationship("Expressao", foreign_keys=[left_id])
    right_expr = relationship("Expressao", foreign_keys=[right_id])

    __mapper_args__ = {
        "inherit_condition": id == Expressao.id, # For joined table inheritance, 
                                                 # a SQL expression which will define how the two tables are joined; 
                                                 # defaults to a natural join between the two tables.
    }

    def __init__(self, left_expr, right_expr):
        super().__init__(expr=f"({left_expr.expr} AND {right_expr.expr})")
        self.left_expr = left_expr
        self.right_expr = right_expr


class Or(Expressao):
    __tablename__ = "or"
    id: Mapped[int] = mapped_column(ForeignKey("expressao.id"), primary_key=True)
    left_id: Mapped[Optional[int]] = mapped_column(ForeignKey("expressao.id"))
    right_id: Mapped[Optional[int]] = mapped_column(ForeignKey("expressao.id"))

    left_expr = relationship("Expressao", foreign_keys=[left_id])
    right_expr = relationship("Expressao", foreign_keys=[right_id])

    __mapper_args__ = {
        "inherit_condition": id == Expressao.id,
    }

    def __init__(self, left_expr, right_expr):
        super().__init__(expr=f"({left_expr.expr} OR {right_expr.expr})")
        self.left_expr = left_expr
        self.right_expr = right_expr


class Sintoma(Expressao):
    __tablename__ = "sintoma"
    id: Mapped[int] = mapped_column(ForeignKey("expressao.id"), primary_key=True)
    name: Mapped[str] = mapped_column(String(255))

    __mapper_args__ = {
        "inherit_condition": id == Expressao.id,
    }

    def __init__(self, name):
        super().__init__(expr=name)
        self.name = name


class Resultado(Expressao):
    __tablename__ = "resultado"
    id: Mapped[int] = mapped_column(ForeignKey("expressao.id"), primary_key=True)
    name: Mapped[str] = mapped_column(String(255))

    __mapper_args__ = {
        "inherit_condition": id == Expressao.id,
    }

    def __init__(self, name):
        super().__init__(expr=name)
        self.name = name


# Criando engine para conectar ao banco de dados
engine = create_engine(connection_string, echo=True)

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

    # Exemplo de inserção de dados syntax tree
    diseasedx_expr = And(
        left_expr=dor_de_cabeca,
        right_expr=Or(
            left_expr=febre,
            right_expr=ferro_alto
        )
    )

    fmf_expr = Or(
        left_expr=And(
            left_expr=variante_mefv_patogenica,
            right_expr=febre
        ),
        right_expr=And(
            left_expr=vus_de_mefv,
            right_expr=And(
                left_expr=dor_de_cabeca,
                right_expr=dor_no_peito
            )
        )
    )

    # Exemplo de inserção de dados linha a linha
    # or_expr = Or(left_expr=febre, right_expr=ferro_alto)
    # diseasedx_expr = And(left_expr=dor_de_cabeca, right_expr=or_expr)

    # Inserir as expressoes no banco de dados
    session.add(diseasedx_expr)
    session.add(fmf_expr)
    session.commit()

    # Buscando a expressão no banco de dados usando o objeto criado
    expr_query = select(Expressao).where(Expressao.expr == diseasedx_expr.expr)
    result = session.execute(expr_query).scalars().first()
    print(result.expr)

    expr_query = select(Expressao).where(Expressao.expr == fmf_expr.expr)
    result = session.execute(expr_query).scalars().first()
    print(result.expr)