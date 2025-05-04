from typing import Optional
from sqlalchemy import ForeignKey, String, Float, Integer, Table, Column
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, Session
from tribool import Tribool
import streamlit as st
import json
from typing import Dict


class Flyweight:
    """
    The Flyweight stores a common portion of the state (also called intrinsic
    state) that belongs to multiple real business entities. The Flyweight
    accepts the rest of the state (extrinsic state, unique for each entity) via
    its method parameters.
    """
    def __init__(self, shared_state: str) -> None:
        self._shared_state = shared_state
    
    def operation(self, unique_state: str) -> None:
        s = json.dumps(self._shared_state)
        u = json.dumps(unique_state)
        print(f"Flyweight: Displaying shared ({s}) and unique ({u}) state.", end="")


class FlyweightFactory():
    """
    The Flyweight Factory creates and manages the Flyweight objects. It ensures
    that flyweights are shared correctly. When the client requests a flyweight,
    the factory either returns an existing instance or creates a new one, if it
    doesn't exist yet.
    """

    _flyweights: Dict[str, Flyweight] = {}

    def __init__(self, db_engine, initial_flyweights: Dict) -> None:
        for state in initial_flyweights:
            self._flyweights[self.get_key(state)] = Flyweight(state)
            self.engine = db_engine

    def get_key(self, state: Dict) -> str:
        """
        Returns a Flyweight's string hash for a given state.
        """

        return "_".join(sorted(state))

    def get_flyweight(self, shared_state: Dict) -> Flyweight:
        """
        Returns an existing Flyweight with a given state or creates a new one.
        """

        key = self.get_key(shared_state)

        if not self._flyweights.get(key):
            print("FlyweightFactory: Can't find a flyweight, creating new one.")
            self._flyweights[key] = Flyweight(shared_state)
            with Session(self.engine, expire_on_commit=False) as session:
                session.add(self._flyweights[key])
                session.commit()
        else:
            print("FlyweightFactory: Reusing existing flyweight.")

        return self._flyweights[key]

    def list_flyweights(self) -> None:
        count = len(self._flyweights)
        print(f"FlyweightFactory: I have {count} flyweights:")
        print("\n".join(map(str, self._flyweights.keys())), end="")


class FatosSintomaResultado(): # Context
    def __init__(self, sintomas, sintomas_presentes, sintomas_ausentes, resultados, resultados_presentes, resultados_ausentes):
        self.fatos = {}
        for sintoma in sintomas:
            if sintoma in sintomas_presentes:
                self.fatos[sintoma] = Tribool(True)
            elif sintoma in sintomas_ausentes:
                self.fatos[sintoma] = Tribool(False)
            else:
                self.fatos[sintoma] = Tribool(None)
        for resultado in resultados:
            if resultado in resultados_presentes:
                self.fatos[resultado] = Tribool(True)
            elif resultado in resultados_ausentes:
                self.fatos[resultado] = Tribool(False)
            else:
                self.fatos[resultado] = Tribool(None)
    
    def __getitem__(self, fato):
        return self.fatos.get(fato)
    
    def print_fatos(self):
        print(f"Fatos:")
        for fato, valor in self.fatos.items():
            print(f"-> {fato}: {valor}")


class AvaliaNode():
    def __init__(self):
        self.expressao = None
        self.result = None
        self.children = []

    def print_tree(self, level=0):
        if level == 0:
            print(f"{self.expressao} ({self.result})")
        for child in self.children:
            print(f"{' ' * 4 * level} {child.expressao} ({child.result})")
            child.print_tree(level + 1)

    # def build_string(self, level=0):
    #     if level == 0:
    #         string = f"{self.expressao} ({self.result})"
    #     else:
    #         string = f"  \n{' ' * 4 * level} {self.expressao} ({self.result})"
    #     for child in self.children:
    #         string += child.build_string(level + 1)
    #     return string

    def build_string(self, level=0):
        if level == 0:
            if self.result is Tribool(True):
                string = f"<span style='background-color:green;'>{self.expressao} ({self.result})</span>"
            elif self.result is Tribool(False):
                string = f"<span style='background-color:red;'>{self.expressao} ({self.result})</span>"
            else:
                string = f"{self.expressao} ({self.result})"
        else:
            indent = "&nbsp;" * 12 * level
            if self.result is Tribool(True):
                string = f"<br>{indent}<span style='background-color:green;'>{self.expressao} ({self.result})</span>"
            elif self.result is Tribool(False):
                string = f"<br>{indent}<span style='background-color:red;'>{self.expressao} ({self.result})</span>"
            else:
                string = f"<br>{indent}{self.expressao} ({self.result})"
        for child in self.children:
            string += child.build_string(level + 1)
        return string
    



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

    def avalia(self, fatos: FatosSintomaResultado): # Interpret
        raise NotImplementedError("Subclasses devem implementar este método")

    def contem(self, fato):
        raise NotImplementedError("Subclasses devem implementar este método")
    
    def add_to_db(self, factory: FlyweightFactory, extrinsic_state: Dict, intrinsic_state: Dict) -> None:
        print(f"\n\n----- Adding {self.__class__.__name__} to DB")
        flyweight = factory.get_flyweight(intrinsic_state)
        flyweight.operation(extrinsic_state)

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

    def avalia(self, fatos: FatosSintomaResultado):
        avalia_node = AvaliaNode()
        left_result, left_tree = self.left_expr.avalia(fatos)
        right_result, right_tree = self.right_expr.avalia(fatos)
        result = Tribool(left_result) & Tribool(right_result)
        avalia_node.expressao = self.__class__.__name__
        avalia_node.result = result
        avalia_node.children.append(left_tree)
        avalia_node.children.append(right_tree)
        return result, avalia_node
    
    def contem(self, fato):
        return self.left_expr.contem(fato) or self.right_expr.contem(fato)

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

    def avalia(self, fatos: FatosSintomaResultado):
        avalia_node = AvaliaNode()
        left_result, left_tree = self.left_expr.avalia(fatos)
        right_result, right_tree = self.right_expr.avalia(fatos)
        result = Tribool(left_result) | Tribool(right_result)
        avalia_node.expressao = self.__class__.__name__
        avalia_node.result = result
        avalia_node.children.append(left_tree)
        avalia_node.children.append(right_tree)
        return result, avalia_node
    
    def contem(self, fato):
        return self.left_expr.contem(fato) or self.right_expr.contem(fato)

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

    def avalia(self, fatos: FatosSintomaResultado):
        avalia_node = AvaliaNode()
        avalia_node.expressao = f"{self.__class__.__name__}({self.qtd})"
        count = self.qtd
        count_false = 0
        for exp in self.expressoes:
            result, exp_avalia_node = exp.avalia(fatos)
            avalia_node.children.append(exp_avalia_node)

            if result is Tribool(True):
                count -= 1
                if count == 0:
                    avalia_node.result = result
                    return result, avalia_node
            if result is Tribool(False):
                count_false += 1
                if len(self.expressoes) - count_false < self.qtd:
                    avalia_node.result = result
                    return result, avalia_node

        return Tribool(None), avalia_node
    
    def contem(self, fato):
        return any(expr.contem(fato) for expr in self.expressoes)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.qtd!r})({self.expressoes!r})"


regioes_da_parte = Table(
    "regioes",
    Base.metadata,
    Column("regiao_composta_id", Integer, ForeignKey("regiao_composta.id"), primary_key=True),
    Column("regiao_do_corpo_id", Integer, ForeignKey("regiao_do_corpo.id"), primary_key=True)
)


class RegiaoDoCorpo(Base):
    __tablename__ = "regiao_do_corpo"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255))
    type: Mapped[str] = mapped_column(String(255)) # Coluna discriminadora para o tipo de região do corpo

    regiao_composta: Mapped[list["RegiaoComposta"]] = relationship("RegiaoComposta", secondary=regioes_da_parte, back_populates="regioes")

    __mapper_args__ = {
        "polymorphic_identity": "regiao_do_corpo",
        "polymorphic_on": "type",
    }

    def __repr__(self):
        return f"({self.name})"


class RegiaoComposta(RegiaoDoCorpo):
    __tablename__ = "regiao_composta"
    id: Mapped[int] = mapped_column(ForeignKey("regiao_do_corpo.id"), primary_key=True)

    regioes: Mapped[list[RegiaoDoCorpo]] = relationship("RegiaoDoCorpo", secondary=regioes_da_parte, back_populates="regiao_composta")

    __mapper_args__ = {
        "polymorphic_identity": "regiao_composta",
    }

    def __init__(self, name: str, regioes: list[RegiaoDoCorpo] = []):
        self.name = name
        self.regioes = regioes

    def __repr__(self):
        return f"{self.name}"
    

class Orgao(RegiaoDoCorpo):
    __tablename__ = "orgao"
    id: Mapped[int] = mapped_column(ForeignKey("regiao_do_corpo.id"), primary_key=True)

    __mapper_args__ = {
        "polymorphic_identity": "orgao",
    }

    def __repr__(self):
        return f"{self.name}"


class Manifestacao(Base):
    __tablename__ = "manifestacao"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255))

    def __repr__(self):
        return f"{self.name}"


class Sintoma(Expressao):
    __tablename__ = "sintoma"
    id: Mapped[int] = mapped_column(ForeignKey("expressao.id"), primary_key=True)
    manifestacao_id: Mapped[int] = mapped_column(ForeignKey("manifestacao.id"))
    regiao_do_corpo_id: Mapped[Optional[int]] = mapped_column(ForeignKey("regiao_do_corpo.id"), nullable=True) # Alterei para optional

    manifestacao: Mapped[Manifestacao] = relationship("Manifestacao")
    regiao_do_corpo: Mapped[Optional[RegiaoDoCorpo]] = relationship("RegiaoDoCorpo") # Alterei para optional

    __mapper_args__ = {
        "polymorphic_identity": "sintoma",
    }

    def __init__(self, manifestacao: Manifestacao, regiao_do_corpo: Optional[RegiaoDoCorpo] = None): # Alterei para optional
        self.manifestacao = manifestacao
        self.regiao_do_corpo = regiao_do_corpo

    def avalia(self, fatos):
        avalia_node = AvaliaNode()
        avalia_node.expressao = self
        result = fatos[self]
        avalia_node.result = result
        return result, avalia_node

    # def avalia(self, fatos, level=0):
    #     result = fatos[self]
    #     tree = f"{' ' * 4 * level}{self} ({result})"
    #     return result, tree
        
    def contem(self, fato):
        return self == fato
        
    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        if isinstance(other, Sintoma):
            return self.id == other.id
        return False

    def __repr__(self):
        if self.regiao_do_corpo:
            return f"{self.manifestacao} no(a) {self.regiao_do_corpo}"
        else:
            return f"{self.manifestacao}"


class Exame(Base):
    __tablename__ = "exame"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255))
    preco: Mapped[str] = mapped_column(String(255))

    resultados: Mapped[list["Resultado"]] = relationship("Resultado", back_populates="exame")

    def __repr__(self):
        return f"{self.__class__.__name__}({self.name!r})"


class Resultado(Expressao):
    __tablename__ = "resultado"
    id: Mapped[int] = mapped_column(ForeignKey("expressao.id"), primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    exame_id: Mapped[int] = mapped_column(ForeignKey("exame.id"))
    
    exame: Mapped[Exame] = relationship("Exame", back_populates="resultados")

    __mapper_args__ = {
        "polymorphic_identity": "resultado",
    }

    def __init__ (self, name: str, exame: Exame):
        self.name = name
        self.exame = exame

    def avalia(self, fatos):
        avalia_node = AvaliaNode()
        avalia_node.expressao = self
        result = fatos[self]
        avalia_node.result = result
        return result, avalia_node

    # def avalia(self, fatos, level=0):
    #     result = fatos[self]
    #     tree = f"{' ' * 4 * level}{self} ({result})"
    #     return result, tree
        
    def contem(self, fato):
        return self == fato
        
    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        if isinstance(other, Resultado):
            return self.id == other.id
        return False

    def __repr__(self):
        return f"{self.name}"


class Doenca(Base):
    __tablename__ = "doenca"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255))
    diagnostico: Mapped["Diagnostico"] = relationship("Diagnostico", back_populates="doenca") # Doenca tem 1 Diagnostico e Diagnostico tem 1 Expressao que tem 1 ou mais Expressoes

    def __repr__(self):
        return f"{self.name}"
    

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