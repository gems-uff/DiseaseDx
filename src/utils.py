from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload
from db_config import DatabaseConfig
from models import Doenca, Diagnostico, Or, And, AoMenos, Sintoma, Manifestacao, RegiaoComposta, RegiaoDoCorpo, Orgao, Exame, Resultado, Expressao
import streamlit as st
import pandas as pd

class StreamlitQueries():
    def __init__(self):
        # Criando o banco de dados e as tabelas
        self.engine = DatabaseConfig().init_db() # TODO: Rever isso em algum momento pois ele inicia a base de dados toda vez que a aplicação é iniciada


    # Função recursiva para verificar se uma expressão contém outra expressão
    def contains_expression(self, expr, target_expr):
        if expr == target_expr:
            return True
        if isinstance(expr, (And, Or)):
            return self.contains_expression(expr.left_expr, target_expr) or self.contains_expression(expr.right_expr, target_expr)
        if isinstance(expr, AoMenos):
            return any(self.contains_expression(e, target_expr) for e in expr.expressoes)
        return False
    
    
    # Função recursiva para buscar todos os sintomas de uma expressão
    def get_all_sintomas_from_expression(self, expr):
        if isinstance(expr, Sintoma):
            return [expr]
        if isinstance(expr, (And, Or)):
            return self.get_all_sintomas_from_expression(expr.left_expr) + self.get_all_sintomas_from_expression(expr.right_expr)
        if isinstance(expr, AoMenos):
            return [sintoma for e in expr.expressoes for sintoma in self.get_all_sintomas_from_expression(e)]
        return []
    

    # Função para buscar todos os sintomas do banco de dados
    def get_all_sintomas(self):
        with Session(self.engine) as session:
            statement = select(Sintoma).options(
                joinedload(Sintoma.manifestacao),
                joinedload(Sintoma.regiao_do_corpo)
            )
            sintomas = session.scalars(statement).unique().all()
            return sintomas
        
    
    # Função para buscar todas as doenças
    def get_all_doencas(self):
        with Session(self.engine) as session:
            doencas = session.query(Doenca).all()
            return doencas
        

    # Função para buscar todos os sintomas associados a uma doença
    def get_sintomas_by_doenca(self, target_doenca):
        with Session(self.engine) as session:
            target_doenca = session.get(Doenca, target_doenca.id)

            diagnosticos = session.query(Diagnostico).options(
                joinedload(Diagnostico.doenca),
                joinedload(Diagnostico.expressao)
            ).all()

            sintomas = []
            for diag in diagnosticos:
                if diag.doenca == target_doenca:
                    sintomas = self.get_all_sintomas_from_expression(diag.expressao)
            
            st.write(f"Sintomas da doença {target_doenca.name}:", sintomas) # TODO: Investigar como resolver o problema do DetachedInstanceError que ocorre caso eu não faça essa chamada

            return sintomas


    # Função para buscar todas as doenças associadas a um sintoma
    def get_diagnosticos_by_sintoma(self, sintoma):
        with Session(self.engine) as session:
            sintoma = session.get(Sintoma, sintoma.id)

            diagnosticos = session.query(Diagnostico).options(
                joinedload(Diagnostico.doenca),
                joinedload(Diagnostico.expressao)
            ).all()

            diagnosticos_filtrados = {}
            for diag in diagnosticos:
                if self.contains_expression(diag.expressao, sintoma):
                    diagnosticos_filtrados[diag] = diag.expressao

            return diagnosticos_filtrados
        
    
    # Função para buscar todas as possíveis doenças associadas a listas de sintomas presentes e ausentes
    def get_diagnosticos_by_list_of_sintomas(self, present_sintomas, not_present_sintomas):
        with Session(self.engine) as session:
            sintomas_presentes = []
            sintomas_ausentes = []
            for sintoma in present_sintomas:
                sintomas_presentes.append(session.get(Sintoma, sintoma.id))
            for sintoma in not_present_sintomas:
                sintomas_ausentes.append(session.get(Sintoma, sintoma.id))

            diagnosticos = session.query(Diagnostico).options(
                joinedload(Diagnostico.doenca),
                joinedload(Diagnostico.expressao)
            ).all()
            
            diagnosticos_filtrados = {}
            for diag in diagnosticos:
                if all(self.contains_expression(diag.expressao, sintoma) for sintoma in sintomas_presentes) and all(not self.contains_expression(diag.expressao, sintoma) for sintoma in sintomas_ausentes):
                    diagnosticos_filtrados[diag] = diag.expressao

            return diagnosticos_filtrados
        
    # Criar um dataframe para exibir as informações de todas as doenças associadas a cada sintoma
    def st_write_sintoma_doencas_table(self):
        df = pd.DataFrame(columns=["Sintoma", "Doenças", "Count"])
        sintomas = self.get_all_sintomas()
        for sintoma in sintomas:
            diagnosticos = self.get_diagnosticos_by_sintoma(sintoma)
            doencas_names = [diagnostico.doenca.name for diagnostico in diagnosticos]
            if(sintoma.regiao_do_corpo == None):
                df = pd.concat([df, pd.DataFrame([{
                    "Sintoma": f"{sintoma.manifestacao.name}",
                    "Doenças": doencas_names,
                    "Count": len(doencas_names)
                }])], ignore_index=True)
            else:
                df = pd.concat([df, pd.DataFrame([{
                    "Sintoma": f"{sintoma.manifestacao.name} no(a) {sintoma.regiao_do_corpo.name}", 
                    "Doenças": doencas_names,
                    "Count": len(doencas_names)
                }])], ignore_index=True)
        st.dataframe(df)

    # Criar um dataframe para exibir todos os sintomas de uma doença
    def st_write_doenca_sintomas_table(self):
        df = pd.DataFrame(columns=["Doença", "Sintomas"])
        doencas = self.get_all_doencas()
        for doenca in doencas:
            sintomas = self.get_sintomas_by_doenca(doenca)
            sintomas_names = [
                f"{sintoma.manifestacao.name} no (a) {sintoma.regiao_do_corpo.name}" if sintoma.regiao_do_corpo 
                else f"{sintoma.manifestacao.name}" 
                for sintoma in sintomas
            ]
            df = pd.concat([df, pd.DataFrame([{
                "Doença": doenca.name,
                "Sintomas": sintomas_names
            }])], ignore_index=True)
        st.dataframe(df)