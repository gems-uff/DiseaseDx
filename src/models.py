from typing import Optional
from sqlalchemy import ForeignKey, String, Float, Integer, Table, Column
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from tribool import Tribool




class FatosSintomaResultado():
    """
    Class to represent the facts of symptoms and results.
    It works as a 'context' for evaluating the expressions in the interpreter design pattern.
    It's a dictionary that stores the symptoms and results as keys and their values as Tribool objects (True, False, None).
    """
    def __init__(self, sintomas, sintomas_presentes, sintomas_ausentes, resultados, resultados_presentes, resultados_ausentes) -> None:
        """
        Initialize self.fatos dictionary with present/absent/indeterminate symptoms and results.
        """
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

    
    def __getitem__(self, fato) -> Tribool:
        """
        Get the value of a fact (sintoma or resultado)
        Without this method defined, it would give an TypeError: 'FatosSintomaResultado' object is not subscriptable.
        """
        return self.fatos.get(fato)
    
    
    def print_fatos(self) -> None:
        """
        Print the facts in a readable format.
        """
        print(f"Fatos:")
        for fato, valor in self.fatos.items():
            print(f"-> {fato}: {valor}")




class AvaliaNode():
    """
    Class to represent a node in the evaluation tree.
    
    Attributes:
        expressao (str): The expression being evaluated.
        result (Tribool): The result of the evaluation (True, False, Indeterminate).
        children (list[AvaliaNode]): List of child nodes in the evaluation tree.
        instance (Expressao): The instance of the expression being evaluated.
    """
    def __init__(self) -> None:
        """
        Initialize the AvaliaNode with default values.
        """
        self.expressao = None
        self.result = None
        self.children = []
        self.instance = None


    def print_tree(self, level=0) -> None:
        """
        Print the evaluation tree in a readable format.
        The level parameter is used to indent the tree structure.
        """
        if level == 0:
            print(f"{self.expressao} ({self.result})")
        for child in self.children:
            print(f"{' ' * 4 * level} {child.expressao} ({child.result})")
            child.print_tree(level + 1)


    def build_string(self, level=0) -> str:
        """
        Build a string representation of the evaluation tree.
        The level parameter is used to indent the tree structure.
        """
        if level == 0:
            string = f"{self.expressao} ({self.result})"
        else:
            string = f"  \n{' ' * 4 * level} {self.expressao} ({self.result})"
        for child in self.children:
            string += child.build_string(level + 1)
        return string
    

    def build_html_string(self, level=0) -> str:
        """
        Build an HTML string representation of the evaluation tree.
        The level parameter is used to indent the tree structure.
        """
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
            string += child.build_html_string(level + 1)
        return string
    



class Base(DeclarativeBase):
    """
    Base class for SQLAlchemy models.
    """
    pass




"""
Table to represent the many-to-many relationship between AoMenos and Expressao.
This table is used to store the expressions that are part of the AoMenos expression.
"""
ao_menos_expressoes = Table(
    "ao_menos_expressoes",
    Base.metadata,
    Column("ao_menos_id", Integer, ForeignKey("ao_menos.id"), primary_key=True),
    Column("expressao_id", Integer, ForeignKey("expressao.id"), primary_key=True)
)




class Expressao(Base):
    """
    Base class for all expressions. It contains the common attributes and methods for all expressions.

    Attributes:
        id (int): The unique identifier for the expression.
        type (str): The type of the expression (discriminator column).
        ao_menos_expr (list[AoMenos]): List of AoMenos expressions associated with this expression.
    """
    __tablename__ = "expressao"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    type: Mapped[str] = mapped_column(String(255))

    ao_menos_expr: Mapped[list["AoMenos"]] = relationship("AoMenos", secondary=ao_menos_expressoes, back_populates="expressoes")

    __mapper_args__ = {
        "polymorphic_identity": "expressao",
        "polymorphic_on": "type",
    }


    def avalia(self, fatos: FatosSintomaResultado) -> tuple[Tribool, AvaliaNode]:
        """
        Evaluate the expression using the provided facts. It serves as the interpret method in the interpreter design pattern.

        Parameters:
            fatos (FatosSintomaResultado): The facts to be used for evaluation.
        """
        raise NotImplementedError("Subclass must implement this method")
    

    def contem(self, fato) -> bool:
        """
        Check if the expression contains the given fact (sintoma or resultado).

        Parameters:
            fato: The fact to be checked.
        """
        raise NotImplementedError("Subclass must implement this method")
    

    def __repr__(self) -> str:
        """
        Return a string representation of the expression.
        """
        return f"{self.__class__.__name__}({self.id})"




class And(Expressao):
    """
    Class to represent the AND expression. It inherits from the Expressao class.

    Attributes:
        id (int): The unique identifier for the expression.
        left_expr_id (int): The unique identifier for the left expression.
        right_expr_id (int): The unique identifier for the right expression.
        left_expr (Expressao): The left expression of the AND operation. The relationship() works as a foreign key to the Expressao table.
        right_expr (Expressao): The right expression of the AND operation. The relationship() works as a foreign key to the Expressao table.
    """
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

    
    def __init__(self, left: Expressao, right: Expressao) -> None:
        """
        Constructor for the AND expression. It takes two expressions as arguments. Left and right, both of type Expressao.
        """
        self.left_expr = left
        self.right_expr = right


    def avalia(self, fatos: FatosSintomaResultado) -> tuple[Tribool, AvaliaNode]:
        """
        Evaluate the AND expression using the provided facts. It serves as the interpret method in the interpreter design pattern.
        It returns a tuple with the result (if the AND is True, False or Indeterminate) and an AvaliaNode object that represents the evaluation tree.
        """
        avalia_node = AvaliaNode()
        left_result, left_tree = self.left_expr.avalia(fatos)
        right_result, right_tree = self.right_expr.avalia(fatos)
        result = Tribool(left_result) & Tribool(right_result)
        avalia_node.expressao = self.__class__.__name__
        avalia_node.result = result
        avalia_node.instance = self
        avalia_node.children.append(left_tree)
        avalia_node.children.append(right_tree)
        return result, avalia_node
    
    
    def contem(self, fato) -> bool:
        """
        Check if the AND expression contains the given fact (sintoma or resultado).
        """
        return self.left_expr.contem(fato) or self.right_expr.contem(fato)
    

    def __repr__(self) -> str:
        """
        Return a string representation of the AND expression.
        """
        return f"{self.__class__.__name__}({self.left_expr}, {self.right_expr})"




class Or(Expressao):
    """
    Class to represent the OR expression. It inherits from the Expressao class.

    Attributes:
        id (int): The unique identifier for the expression.
        left_expr_id (int): The unique identifier for the left expression.
        right_expr_id (int): The unique identifier for the right expression.
        left_expr (Expressao): The left expression of the OR operation. The relationship() works as a foreign key to the Expressao table.
        right_expr (Expressao): The right expression of the OR operation. The relationship() works as a foreign key to the Expressao table.
    """
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

    
    def __init__(self, left: Expressao, right: Expressao) -> None:
        """
        Constructor for the OR expression. It takes two expressions as arguments. Left and right, both of type Expressao.
        """
        self.left_expr = left
        self.right_expr = right


    def avalia(self, fatos: FatosSintomaResultado) -> tuple[Tribool, AvaliaNode]:
        """
        Evaluate the OR expression using the provided facts. It serves as the interpret method in the interpreter design pattern.
        It returns a tuple with the result (if the OR is True, False or Indeterminate) and an AvaliaNode object that represents the evaluation tree.
        """
        avalia_node = AvaliaNode()
        left_result, left_tree = self.left_expr.avalia(fatos)
        right_result, right_tree = self.right_expr.avalia(fatos)
        result = Tribool(left_result) | Tribool(right_result)
        avalia_node.expressao = self.__class__.__name__
        avalia_node.result = result
        avalia_node.instance = self
        avalia_node.children.append(left_tree)
        avalia_node.children.append(right_tree)
        return result, avalia_node
    
    
    def contem(self, fato) -> bool:
        """
        Check if the OR expression contains the given fact (sintoma or resultado).
        """
        return self.left_expr.contem(fato) or self.right_expr.contem(fato)

    def __repr__(self) -> str:
        """
        Return a string representation of the OR expression.
        """
        return f"{self.__class__.__name__}({self.left_expr}, {self.right_expr})"




class AoMenos(Expressao):
    """
    Class to represent the AoMenos expression. It inherits from the Expressao class.
    It represents the expression that requires at least a certain number of expressions to be true.

    Attributes:
        id (int): The unique identifier for the expression.
        qtd (int): The number of expressions that need to be true.
        expressoes (list[Expressao]): List of expressions associated with this AoMenos expression. The relationship() works as a foreign key to the Expressao table.
    """
    __tablename__ = "ao_menos"
    id: Mapped[int] = mapped_column(ForeignKey("expressao.id"), primary_key=True)
    qtd: Mapped[int] = mapped_column(Integer)

    expressoes: Mapped[list["Expressao"]] = relationship("Expressao", secondary=ao_menos_expressoes, back_populates="ao_menos_expr")

    __mapper_args__ = {
        "polymorphic_identity": "ao_menos"
    }


    def __init__(self, qtd: int, expressoes: list[Expressao]) -> None:
        """
        Set the number of expressions that need to be true and the list of expressions.
        """
        self.qtd = qtd
        self.expressoes = expressoes


    def avalia(self, fatos: FatosSintomaResultado) -> tuple[Tribool, AvaliaNode]:
        """
        Evaluate the AoMenos expression using the provided facts. It serves as the interpret method in the interpreter design pattern.
        It returns a tuple with the result (if the AoMenos is True, False or Indeterminate) and an AvaliaNode object that represents the evaluation tree.
        """
        avalia_node = AvaliaNode()
        avalia_node.instance = self
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
    
    
    def contem(self, fato) -> bool:
        """
        Check if the AoMenos expression contains the given fact (sintoma or resultado).
        """
        return any(expr.contem(fato) for expr in self.expressoes)


    def __repr__(self) -> str:
        """
        Return a string representation of the AoMenos expression.
        """
        return f"{self.__class__.__name__}({self.qtd})({self.expressoes})"




"""
Table to represent the many-to-many relationship between RegiaoComposta and RegiaoDoCorpo.
This table is used to store the regions that are part of the RegiaoComposta region.
"""
regioes_da_parte = Table(
    "regioes",
    Base.metadata,
    Column("regiao_composta_id", Integer, ForeignKey("regiao_composta.id"), primary_key=True),
    Column("regiao_do_corpo_id", Integer, ForeignKey("regiao_do_corpo.id"), primary_key=True)
)




class RegiaoDoCorpo(Base):
    """
    Class to represent a region of the body. It is the base class for all regions of the body.
    It contains the common attributes and methods for all regions of the body. It works like the Expressao class.
    It uses the composite pattern to represent a region that can be composed of other regions.

    Attributes:
        id (int): The unique identifier for the region of the body.
        name (str): The name of the region of the body.
        type (str): The type of the region of the body (discriminator column).
        regiao_composta (list[RegiaoComposta]): List of RegiaoComposta regions associated with this region of the body. The relationship() works as a foreign key.
    """
    __tablename__ = "regiao_do_corpo"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255))
    type: Mapped[str] = mapped_column(String(255))

    regiao_composta: Mapped[list["RegiaoComposta"]] = relationship("RegiaoComposta", secondary=regioes_da_parte, back_populates="regioes")

    __mapper_args__ = {
        "polymorphic_identity": "regiao_do_corpo",
        "polymorphic_on": "type",
    }


    def __repr__(self) -> str:
        """
        Return a string representation of the region of the body.
        """
        return f"({self.name})"




class RegiaoComposta(RegiaoDoCorpo):
    """
    Class to represent a composite region of the body. It inherits from the RegiaoDoCorpo class.
    It uses the composite pattern to represent a region that is composed of other regions.

    Attributes:
        id (int): The unique identifier for the composite region of the body.
        name (str): The name of the composite region of the body. Inherits from RegiaoDoCorpo.
        regioes (list[RegiaoDoCorpo]): List of RegiaoDoCorpo regions associated with this composite region of the body. The relationship() works as a foreign key.
    """
    __tablename__ = "regiao_composta"
    id: Mapped[int] = mapped_column(ForeignKey("regiao_do_corpo.id"), primary_key=True)
    regioes: Mapped[list[RegiaoDoCorpo]] = relationship("RegiaoDoCorpo", secondary=regioes_da_parte, back_populates="regiao_composta")

    __mapper_args__ = {
        "polymorphic_identity": "regiao_composta",
    }


    def __init__(self, name: str, regioes: list[RegiaoDoCorpo] = []) -> None:
        """
        Initialize the composite region of the body with a name and a list of regions.
        """
        self.name = name
        self.regioes = regioes


    def __repr__(self) -> str:
        """
        Return a string representation of the composite region of the body.
        """
        return f"{self.name}"
    



class Orgao(RegiaoDoCorpo):
    """
    Class to represent an organ. It inherits from the RegiaoDoCorpo class.
    It is a leaf in the composite pattern, meaning it does not contain any other regions.

    Attributes:
        id (int): The unique identifier for the organ.
        name (str): The name of the organ. Inherits from RegiaoDoCorpo.
    """
    __tablename__ = "orgao"
    id: Mapped[int] = mapped_column(ForeignKey("regiao_do_corpo.id"), primary_key=True)

    __mapper_args__ = {
        "polymorphic_identity": "orgao",
    }


    def __repr__(self) -> str:
        """
        Return a string representation of the organ.
        """
        return f"{self.name}"




class Manifestacao(Base):
    """
    Class to represent a manifestation. A manifestation is part of a symptom.
    In 'Neck Pain', for example, 'Pain' is the manifestation and 'Neck' is the region of the body. The symptom is 'Neck Pain'.

    Attributes:
        id (int): The unique identifier for the manifestation.
        name (str): The name of the manifestation.
    """
    __tablename__ = "manifestacao"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255))


    def __repr__(self) -> str:
        """
        Return a string representation of the manifestation.
        """
        return f"{self.name}"




class Sintoma(Expressao):
    """
    Class to represent a symptom. It inherits from the Expressao class.
    It contains the manifestation and the region of the body associated with the symptom. RegiaoDoCorpo is optional, cause 'Fever' can be a symptom without a region.

    Attributes:
        id (int): The unique identifier for the symptom.
        manifestacao_id (int): The unique identifier for the manifestation. 
        regiao_do_corpo_id (int): The unique identifier for the region of the body.
        manifestacao (Manifestacao): The manifestation associated with this symptom. The relationship() works as a foreign key to the Manifestacao table.
        regiao_do_corpo (RegiaoDoCorpo): The region of the body associated with this symptom. The relationship() works as a foreign key to the RegiaoDoCorpo table.
    """
    __tablename__ = "sintoma"
    id: Mapped[int] = mapped_column(ForeignKey("expressao.id"), primary_key=True)
    manifestacao_id: Mapped[int] = mapped_column(ForeignKey("manifestacao.id"))
    regiao_do_corpo_id: Mapped[Optional[int]] = mapped_column(ForeignKey("regiao_do_corpo.id"), nullable=True)

    manifestacao: Mapped[Manifestacao] = relationship("Manifestacao")
    regiao_do_corpo: Mapped[Optional[RegiaoDoCorpo]] = relationship("RegiaoDoCorpo")

    __mapper_args__ = {
        "polymorphic_identity": "sintoma",
    }


    def __init__(self, manifestacao: Manifestacao, regiao_do_corpo: Optional[RegiaoDoCorpo] = None) -> None:
        """
        Initialize the symptom with a manifestation and an optional region of the body.
        """
        self.manifestacao = manifestacao
        self.regiao_do_corpo = regiao_do_corpo


    def avalia(self, fatos) -> tuple[Tribool, AvaliaNode]:
        """
        Evaluate the symptom using the provided facts. It serves as the interpret method in the interpreter design pattern.
        It returns a tuple with the result (if the symptom is True, False or Indeterminate) and an AvaliaNode object that represents the evaluation tree.
        """
        avalia_node = AvaliaNode()
        avalia_node.instance = self
        avalia_node.expressao = self
        result = fatos[self]
        avalia_node.result = result
        return result, avalia_node

        
    def contem(self, fato) -> bool:
        """
        Check if the symptom contains the given fact (sintoma or resultado).
        """
        return self == fato
        
    def __hash__(self) -> int:
        """
        Set the hash of the symptom to be the id of the symptom. It's useful to use the symptom as a key in a dictionary.
        """
        return hash(self.id)


    def __eq__(self, other) -> bool:
        """
        Check if the symptom is equal to another symptom. It compares the id of the symptoms.
        """
        if isinstance(other, Sintoma):
            return self.id == other.id
        return False
    

    def __repr__(self) -> str:
        """
        Return a string representation of the symptom.
        """
        if self.regiao_do_corpo:
            return f"{self.manifestacao} no(a) {self.regiao_do_corpo}"
        else:
            return f"{self.manifestacao}"




class Exame(Base):
    """
    Class to represent an exam. It contains the name and price of the exam.

    Attributes:
        id (int): The unique identifier for the exam.
        name (str): The name of the exam.
        preco (str): The price of the exam.
        resultados (list[Resultado]): List of results associated with this exam. The relationship() works as a foreign key to the Resultado table.
    """
    __tablename__ = "exame"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255))
    preco: Mapped[str] = mapped_column(String(255))

    resultados: Mapped[list["Resultado"]] = relationship("Resultado", back_populates="exame")


    def __repr__(self) -> str:
        """
        Return a string representation of the exam.
        """
        return f"{self.__class__.__name__}({self.name})"




class Resultado(Expressao):
    """
    Class to represent a result. It inherits from the Expressao class.

    Attributes:
        id (int): The unique identifier for the result.
        name (str): The name of the result.
        exame_id (int): The unique identifier for the exam.
        exame (Exame): The exam associated with this result. The relationship() works as a foreign key to the Exame table.
    """
    __tablename__ = "resultado"
    id: Mapped[int] = mapped_column(ForeignKey("expressao.id"), primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    exame_id: Mapped[int] = mapped_column(ForeignKey("exame.id"))
    
    exame: Mapped[Exame] = relationship("Exame", back_populates="resultados")

    __mapper_args__ = {
        "polymorphic_identity": "resultado",
    }


    def __init__ (self, name: str, exame: Exame) -> None:
        """
        Initialize the result with a name and an exam.
        """
        self.name = name
        self.exame = exame


    def avalia(self, fatos) -> tuple[Tribool, AvaliaNode]:
        """
        Evaluate the result using the provided facts. It serves as the interpret method in the interpreter design pattern.
        """
        avalia_node = AvaliaNode()
        avalia_node.instance = self
        avalia_node.expressao = self
        result = fatos[self]
        avalia_node.result = result
        return result, avalia_node

        
    def contem(self, fato) -> bool:
        """
        Check if the result contains the given fact (sintoma or resultado).
        """
        return self == fato
    
        
    def __hash__(self) -> int:
        """
        Set the hash of the result to be the id of the result. It's useful to use the result as a key in a dictionary.
        """
        return hash(self.id)
    

    def __eq__(self, other) -> bool:
        """
        Check if the result is equal to another result. It compares the id of the results.
        """
        if isinstance(other, Resultado):
            return self.id == other.id
        return False
    

    def __repr__(self) -> str:
        """
        Return a string representation of the result.
        """
        return f"{self.name}"




class Doenca(Base):
    """
    Class to represent a disease. It contains the name of the disease and the associated diagnosis.

    Attributes:
        id (int): The unique identifier for the disease.
        name (str): The name of the disease.
        diagnostico (Diagnostico): The diagnosis associated with this disease. The relationship() works as a foreign key to the Diagnostico table.
    """
    __tablename__ = "doenca"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255))
    diagnostico: Mapped["Diagnostico"] = relationship("Diagnostico", back_populates="doenca") # Doenca tem 1 Diagnostico e Diagnostico tem 1 Expressao que tem 1 ou mais Expressoes


    def __repr__(self) -> str:
        """
        Return a string representation of the disease.
        """
        return f"{self.name}"
    



class Diagnostico(Base):
    """
    Class to represent a diagnosis. It contains the sensitivity, specificity, accuracy and the associated disease and expression.

    Attributes:
        id (int): The unique identifier for the diagnosis.
        sensibilidade (float): The sensitivity of the diagnosis.
        especificidade (float): The specificity of the diagnosis.
        acuracia (float): The accuracy of the diagnosis.
        doenca_id (int): The unique identifier for the disease.
        expressao_id (int): The unique identifier for the expression.
        doenca (Doenca): The disease associated with this diagnosis. The relationship() works as a foreign key to the Doenca table.
        expressao (Expressao): The expression associated with this diagnosis. The relationship() works as a foreign key to the Expressao table.
    """
    __tablename__ = "diagnostico"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    sensibilidade: Mapped[Optional[float]] = mapped_column(Float)
    especificidade: Mapped[Optional[float]] = mapped_column(Float)
    acuracia: Mapped[Optional[float]] = mapped_column(Float)
    doenca_id: Mapped[int] = mapped_column(ForeignKey("doenca.id"))
    expressao_id: Mapped[int] = mapped_column(ForeignKey("expressao.id"))
    
    doenca: Mapped[Doenca] = relationship("Doenca", back_populates="diagnostico")
    expressao: Mapped[Expressao] = relationship("Expressao")
    

    def __repr__(self) -> str:
        """
        Return a string representation of the diagnosis.
        """
        return f"{self.__class__.__name__}({self.doenca}, {self.expressao})"