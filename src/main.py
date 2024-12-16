from sqlalchemy import select, inspect
from sqlalchemy.orm import Session, joinedload, aliased
from db_config import DatabaseConfig
from models import Doenca, Diagnostico, Or, And, AoMenos, Sintoma, Manifestacao, RegiaoComposta, RegiaoDoCorpo, Orgao, Exame, Resultado, Expressao
import streamlit as st
# import pandas as pd # Importar o pandas faz com que o script nem execute, não apresenta erro nem nada


# Criando o banco de dados e as tabelas
engine = DatabaseConfig().init_db()

def walk(obj):
    deque = [obj]

    seen = set()

    while deque:
        obj = deque.pop(0)
        if obj in seen:
            continue
        else:
            seen.add(obj)
            yield obj
        insp = inspect(obj)
        for relationship in insp.mapper.relationships:
            related = getattr(obj, relationship.key)
            if relationship.uselist:
                deque.extend(related)
            elif related is not None:
                deque.append(related)

# Função para buscar todos os sintomas do banco de dados
def get_all_sintomas():
    with Session(engine) as session:
        statement = select(Sintoma).options(
            joinedload(Sintoma.manifestacao),
            joinedload(Sintoma.regiao_do_corpo.of_type(RegiaoComposta)).joinedload(RegiaoComposta.regioes),
            joinedload(Sintoma.regiao_do_corpo.of_type(RegiaoDoCorpo)).joinedload(RegiaoDoCorpo.regiao_composta),
            joinedload(Sintoma.ao_menos_expr).joinedload(AoMenos.expressoes)
        )
        sintomas = session.scalars(statement).unique().all()
        return sintomas


def get_doencas_by_sintoma(sintoma):
    with Session(engine) as session:
        sintoma_id = sintoma.id
        sintoma = session.get(Sintoma, sintoma_id)
        print(f"\n- Sintoma recuperado do banco de dados:", sintoma)
        expressoes = sintoma.ao_menos_expr
        print(f"\n- Expressoes do sintoma recuperado do banco de dados:")
        for expr in expressoes:
            print(expr)

        # Função recursiva para verificar se uma expressão contém outra expressão
        def contains_expression(expr, target_expr):
            print(f"\n- Verificando se a expressão: {expr} \n- Contém a expressão: {target_expr}")
            if expr == target_expr:
                print(f"Expressão encontrada dentro de: {expr}")
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
        print(f"\n- Diagnósticos recuperados do banco de dados:")
        for diag in diagnosticos:
            print(diag)

        diagnosticos_filtrados = []
        for diag in diagnosticos:
            for expr in expressoes:
                if contains_expression(diag.expressao, sintoma):
                    diagnosticos_filtrados.append(diag)
                    break
            
        # diagnosticos_filtrados = [
        #     diag for diag in diagnosticos
        #     if any(contains_expression(diag.expressao, expr) for expr in expressoes)
        # ]

        # Obter todas as doenças ligadas a esses diagnósticos
        doencas = [diag.doenca for diag in diagnosticos_filtrados]

        return doencas

# Exemplo de uso
sintomas = get_all_sintomas()
st.write(sintomas)

doencas = get_doencas_by_sintoma(sintomas[2])
st.write(doencas)