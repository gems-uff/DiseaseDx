from sqlalchemy import select, inspect
from sqlalchemy.orm import Session, joinedload, aliased
from db_config import DatabaseConfig
from models import Doenca, Diagnostico, Or, And, AoMenos, Sintoma, Manifestacao, RegiaoComposta, RegiaoDoCorpo, Orgao, Exame, Resultado, Expressao
import streamlit as st
# import pandas as pd # Importar o pandas faz com que o script nem execute, não apresenta erro nem nada


# Criando o banco de dados e as tabelas
engine = DatabaseConfig().init_db()


# Função para buscar todos os sintomas do banco de dados
def get_all_sintomas():
    with Session(engine) as session:
        statement = select(Sintoma).options(
            joinedload(Sintoma.manifestacao),
            joinedload(Sintoma.regiao_do_corpo)
        )
        sintomas = session.scalars(statement).unique().all()
        return sintomas


def get_doencas_by_sintoma(sintoma):
    with Session(engine) as session:
        sintoma_id = sintoma.id
        sintoma = session.get(Sintoma, sintoma_id)

        # Função recursiva para verificar se uma expressão contém outra expressão
        def contains_expression(expr, target_expr):
            if expr == target_expr:
                return True
            if isinstance(expr, (And, Or)):
                return contains_expression(expr.left_expr, target_expr) or contains_expression(expr.right_expr, target_expr)
            if isinstance(expr, AoMenos):
                return any(contains_expression(e, target_expr) for e in expr.expressoes)
            return False

        # Obter todos os diagnósticos do banco de dados
        diagnosticos = session.query(Diagnostico).options(
            joinedload(Diagnostico.doenca),
            joinedload(Diagnostico.expressao)
        ).all()

        diagnosticos_filtrados = []
        for diag in diagnosticos:
            if contains_expression(diag.expressao, sintoma):
                diagnosticos_filtrados.append(diag)
            
        doencas = []
        for diag in diagnosticos_filtrados:
            doencas.append(diag.doenca)

        return doencas

# Exemplo de uso
sintomas = get_all_sintomas()
st.write(sintomas)

# Create a dropdown option to select a specific symptom to search for diseases
sintoma = st.selectbox("Selecione o sintoma", [sintoma for sintoma in sintomas])

# Only run get_doencas_by_sintoma after selecting at least 1 symptom from the multiselect
doencas = get_doencas_by_sintoma(sintoma)
st.write(doencas)