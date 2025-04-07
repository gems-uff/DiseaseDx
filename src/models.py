from typing import Optional
from sqlalchemy import ForeignKey, String, Float, Integer, Table, Column
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class FatosSintomaResultado(): # Context
    def __init__(self, sintomas, sintomas_presentes, sintomas_ausentes, resultados, resultados_presentes, resultados_ausentes):
        self.fatos = {}
        for sintoma in sintomas:
            if sintoma in sintomas_presentes:
                self.fatos[sintoma] = True
            elif sintoma in sintomas_ausentes:
                self.fatos[sintoma] = False
            else:
                self.fatos[sintoma] = "Possivel"
        for resultado in resultados:
            if resultado in resultados_presentes:
                self.fatos[resultado] = True
            elif resultado in resultados_ausentes:
                self.fatos[resultado] = False
            else:
                self.fatos[resultado] = "Possivel"
        print(f"Fatos:")
        for fato in self.fatos:
            print(f"-> {fato} = {self.fatos[fato]}")
    
    def __getitem__(self, fato):
        return self.fatos.get(fato, True)


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

    def avalia(self, fatos: FatosSintomaResultado, level=0): # Interpret
        raise NotImplementedError("Subclasses devem implementar este método")

    def contem(self, fato):
        raise NotImplementedError("Subclasses devem implementar este método")

    def __repr__(self):
        return f"{self.__class__.__name__}({self.id!r})"
    
    def printtree(self, level=0):
        pass


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

    def avalia(self, fatos: FatosSintomaResultado, level=0):
        result = self.left_expr.avalia(fatos, level+1) and self.right_expr.avalia(fatos, level+1)
        print(f"{' ' * 4 * level}{result} : AND")
        # print(f"-> {result} : {self}")
        return result
    
    def contem(self, fato):
        return self.left_expr.contem(fato) or self.right_expr.contem(fato)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.left_expr!r}, {self.right_expr!r})"
    
    def printtree(self, level=0):
        print(f"{' ' * 4 * level}AND")
        self.left_expr.printtree(level + 1)
        self.right_expr.printtree(level + 1)


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

    def avalia(self, fatos: FatosSintomaResultado, level=0):
        result = self.left_expr.avalia(fatos, level+1) or self.right_expr.avalia(fatos, level+1)
        print(f"{' ' * 4 * level}{result} : OR")
        # print(f"-> {result} : {self}")
        return result
    
    def contem(self, fato):
        return self.left_expr.contem(fato) or self.right_expr.contem(fato)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.left_expr!r}, {self.right_expr!r})"
    
    def printtree(self, level=0):
        print(f"{' ' * level}OR")
        self.left_expr.printtree(level + 1)
        self.right_expr.printtree(level + 1)


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

    def avalia(self, fatos: FatosSintomaResultado, level=0):
        count = self.qtd
        for exp in self.expressoes:
            if exp.avalia(fatos, level+1):
                count -= 1
                if count == 0:
                    # print(f"-> True : {self}")
                    print(f"{' ' * 4 * level}True : AoMenos({self.qtd})")
                    return True
        # print(f"-> False : {self}")
        print(f"{' ' * 4 * level}False : AoMenos({self.qtd})")
        return False
    
    def contem(self, fato):
        return any(expr.contem(fato) for expr in self.expressoes)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.qtd!r})({self.expressoes!r})"
    
    def printtree(self, level=0):
        print(f"{' ' * 4 * level}AoMenos({self.qtd})")
        for expr in self.expressoes:
            expr.printtree(level + 1)


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

    def avalia(self, fatos, level=0):
        if (fatos[self] == "Possivel"):
            print(f"{' ' * 4 * level}True : {self}")
            return True
        else:
            print(f"{' ' * 4 * level}{fatos[self]} : {self}")
            return fatos[self]
        
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
    
    def printtree(self, level=0):
        print(f"{' ' * 4 * level}{self.__class__.__name__}({self.manifestacao})({self.regiao_do_corpo})")


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

    def avalia(self, fatos, level=0):
        if (fatos[self] == "Possivel"):
            print(f"{' ' * 4 * level}True : {self}")
            return True
        else:
            print(f"{' ' * 4 * level}{fatos[self]} : {self}")
            return fatos[self]
        
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
    
    def printtree(self, level=0):
        print(f"{' ' * 4 * level}{self.__class__.__name__}({self.name})")


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