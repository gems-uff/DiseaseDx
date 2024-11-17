from typing import Optional
from sqlalchemy import ForeignKey, String, create_engine, select
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


class Base(DeclarativeBase):
    pass


class Employee(Base):
    __tablename__ = "employee"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    type: Mapped[str] = mapped_column(String(255))

    __mapper_args__ = {
        "polymorphic_identity": "employee",
        "polymorphic_on": "type",
    }

    def __repr__(self):
        return f"{self.__class__.__name__}({self.name!r})"
    

class Engineer(Employee):
    __tablename__ = "engineer"
    id: Mapped[int] = mapped_column(ForeignKey("employee.id"), primary_key=True)
    engineer_name: Mapped[str] = mapped_column(String(255))

    __mapper_args__ = {
        "polymorphic_identity": "engineer",
    }


class Manager(Employee):
    __tablename__ = "manager"
    id: Mapped[int] = mapped_column(ForeignKey("employee.id"), primary_key=True)
    manager_name: Mapped[str] = mapped_column(String(255))

    __mapper_args__ = {
        "polymorphic_identity": "manager",
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

    # Create an engineer
    engineer = Engineer(name="John Engineer", engineer_name="John Engineer")

    # Create a manager
    manager = Manager(name="Jane Manager", manager_name="Jane Manager")

    print("\nObject created on memory before inserting in the database:")
    print(engineer)
    print(type(engineer))
    print(manager)
    print(type(manager))

    # Inserir as expressoes no banco de dados
    session.add(engineer)
    session.add(manager)
    session.commit()

    # Buscando a expressão no banco de dados usando o objeto criado
    statement = select(Employee).where(Employee.id == engineer.id)
    engineer_result = session.execute(statement).scalars().first()
    statement = select(Employee).where(Employee.id == manager.id)
    manager_result = session.execute(statement).scalars().first()

    print("\nObject returned from database:")
    print(engineer_result)
    print(type(engineer_result))
    print(f"Engineer name = {engineer_result.engineer_name}")
    print(manager_result)
    print(type(manager_result))
    print(f"Manager name = {manager_result.manager_name}")