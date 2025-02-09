from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectin_polymorphic, subqueryload, selectinload
from sqlalchemy import create_engine
from db_config import DatabaseConfig
from models import Doenca, Diagnostico, Or, And, AoMenos, Sintoma, Manifestacao, RegiaoComposta, RegiaoDoCorpo, Orgao, Exame, Resultado, Expressao, FatosSintomaResultado
import streamlit as st
import pandas as pd


class StreamlitQueries():
    def __init__(self):
        self.engine = DatabaseConfig().load_engine()


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
        sintomas = set()
        
        def collect_sintomas(expr):
            if isinstance(expr, Sintoma):
                sintomas.add(expr)
            elif isinstance(expr, (And, Or)):
                collect_sintomas(expr.left_expr)
                collect_sintomas(expr.right_expr)
            elif isinstance(expr, AoMenos):
                for e in expr.expressoes:
                    collect_sintomas(e)
        
        collect_sintomas(expr)
        return list(sintomas)
    

    # Função recursiva para buscar todos os resultados de uma expressão
    def get_all_resultados_from_expression(self, expr):
        resultados = set()
        
        def collect_resultados(expr):
            if isinstance(expr, Resultado):
                resultados.add(expr)
            elif isinstance(expr, (And, Or)):
                collect_resultados(expr.left_expr)
                collect_resultados(expr.right_expr)
            elif isinstance(expr, AoMenos):
                for e in expr.expressoes:
                    collect_resultados(e)
        
        collect_resultados(expr)
        return list(resultados)
    

    # Função para buscar todos os sintomas do banco de dados
    def get_all_sintomas(self):
        with Session(self.engine) as session:
            statement = select(Sintoma).options(
                joinedload(Sintoma.manifestacao),
                joinedload(Sintoma.regiao_do_corpo)
            )
            sintomas = session.scalars(statement).unique().all()
            return sintomas
        
        
    # Função para buscar todos os resultados do banco de dados
    def get_all_resultados(self):
        with Session(self.engine) as session:
            statement = select(Resultado).options(
                joinedload(Resultado.exame)
            )
            resultados = session.scalars(statement).unique().all()
            return resultados
        
    
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
            
            # TODO: Melhor do que usar o st.write como gambiarra mas deve ser melhor entendendo os tipos de load do sqlalchemy como selectin polymorphic (problema do DetachedInstanceError)
            for sintoma in sintomas:
                if sintoma.regiao_do_corpo != None:
                    sintoma.regiao_do_corpo = session.get(RegiaoDoCorpo, sintoma.regiao_do_corpo_id)
                sintoma.manifestacao = session.get(Manifestacao, sintoma.manifestacao_id)

            return sintomas
        
    
    # Função para buscar todos os resultados associados a uma doença
    def get_resultados_by_doenca(self, target_doenca):
        with Session(self.engine) as session:
            target_doenca = session.get(Doenca, target_doenca.id)

            diagnosticos = session.query(Diagnostico).options(
                joinedload(Diagnostico.doenca),
                joinedload(Diagnostico.expressao)
            ).all()

            resultados = []
            for diag in diagnosticos:
                if diag.doenca == target_doenca:
                    resultados = self.get_all_resultados_from_expression(diag.expressao)

            for resultado in resultados:
                resultado.exame = session.get(Exame, resultado.exame_id)

            return resultados


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
        

    # Função para buscar o diagnóstico de uma doença
    def get_diagnostico_by_doenca(self, doenca):
        with Session(self.engine) as session:
            doenca = session.get(Doenca, doenca.id)

            diagnosticos = session.query(Diagnostico).options(
                joinedload(Diagnostico.doenca),
                joinedload(Diagnostico.expressao)
            ).all()

            for diag in diagnosticos:
                if diag.doenca == doenca:
                    return diag

            return diag
        
    
    # Função para buscar todas as possíveis doenças associadas a listas de sintomas presentes e ausentes
    def get_diagnosticos_by_list_of_sintomas_and_resultados(self, present_sintomas, not_present_sintomas, present_resultados, not_present_resultados):
        with Session(self.engine) as session:
            sintomas = self.get_all_sintomas()
            sintomas_presentes = [session.get(Sintoma, sintoma.id) for sintoma in present_sintomas]
            sintomas_ausentes = [session.get(Sintoma, sintoma.id) for sintoma in not_present_sintomas]

            resultados = self.get_all_resultados()
            resultados_presentes = [session.get(Resultado, resultado.id) for resultado in present_resultados]
            resultados_ausentes = [session.get(Resultado, resultado.id) for resultado in not_present_resultados]

            diagnosticos = session.query(Diagnostico).options(
                joinedload(Diagnostico.doenca),
                joinedload(Diagnostico.expressao)
            ).all()
            
            diagnosticos_filtrados = {}

            # TODO: Validar essa lógica novamente
            fatos = FatosSintomaResultado(sintomas, sintomas_presentes, sintomas_ausentes, resultados, resultados_presentes, resultados_ausentes)
            for diag in diagnosticos:
                # Avalia checa se a expressão do diagnóstico é True a partir dos fatos (sintomas/resultados presentes e ausentes)
                # Se o sintoma/resultado não estiver presente nem ausente, consideramos ele como "Possivel" e o avaliamos como True para que não seja descartado
                if diag.expressao.avalia(fatos):
                    # Até aqui basicamente só descartamos o que temos certeza que não faz parte do diagnóstico, então sobrou só as possibilidades dado os fatos
                    # Para saber quais diagnósticos são de fato possíveis, vamos verificar se o dicionario de fatos tem um sintoma/resultado presente, então
                    # a expressão do diagnóstico também deve conter esse sintoma/resultado (se é fato que um sintoma é 'Dor no Abdome', não faz sentido retornar
                    # um diagnóstico que não contenha 'Dor no Abdome', como Diabetes por exemplo que só tem 'Sede' e 'Vontade de urinar várias vezes')
                    expressao_contem_sintoma_resultado = all(diag.expressao.contem(sintoma) for sintoma in sintomas_presentes) and \
                                                         all(diag.expressao.contem(resultado) for resultado in resultados_presentes)
                    if expressao_contem_sintoma_resultado:
                        # Agora temos os diagnósticos possíveis, mas não estão ainda fechados necessariamente (com todos os sintomas/resultados presentes 'marcados')
                        # Para Familial Mediterranean Fever por exemplo pode estar retornando como possível, mas ainda não sabemos se é a doença correta
                        diagnosticos_filtrados[diag] = diag.expressao

            return diagnosticos_filtrados
        
        
    # Criar um dataframe para exibir as informações de todas as doenças associadas a cada sintoma
    def st_write_sintoma_doencas_table(self):
        df = pd.DataFrame(columns=["Sintoma", "Doenças", "Count"])
        sintomas = self.get_all_sintomas()
        for sintoma in sintomas:
            diagnosticos = self.get_diagnosticos_by_sintoma(sintoma)
            doencas_names = sorted([diagnostico.doenca.name for diagnostico in diagnosticos])
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
            sintomas_names = sorted([
                f"{sintoma.manifestacao.name} no (a) {sintoma.regiao_do_corpo.name}" if sintoma.regiao_do_corpo 
                else f"{sintoma.manifestacao.name}" 
                for sintoma in sintomas
            ])
            df = pd.concat([df, pd.DataFrame([{
                "Doença": doenca.name,
                "Sintomas": sintomas_names
            }])], ignore_index=True)
        st.dataframe(df)


    # Criar um dataframe para exibir todos os sintomas e resultados de uma doença
    def st_write_doenca_sintomas_resultados_table(self):
        df = pd.DataFrame(columns=["Doença", "Sintomas", "Resultados"])
        doencas = self.get_all_doencas()
        for doenca in doencas:
            sintomas = self.get_sintomas_by_doenca(doenca)
            sintomas_names = sorted([
                f"{sintoma.manifestacao.name} no (a) {sintoma.regiao_do_corpo.name}" if sintoma.regiao_do_corpo 
                else f"{sintoma.manifestacao.name}" 
                for sintoma in sintomas
            ])
            resultados = self.get_resultados_by_doenca(doenca)
            resultados_names = sorted([resultado.name for resultado in resultados])
            df = pd.concat([df, pd.DataFrame([{
                "Doença": doenca.name,
                "Sintomas": sintomas_names,
                "Resultados": resultados_names
            }])], ignore_index=True)
        st.dataframe(df)


    # Criar um dataframe para exibir a expressão de cada diagnóstico
    def st_write_doenca_diagnostico_table(self):
        df = pd.DataFrame(columns=["Doença", "Diagnostico", "Especificidade", "Sensibilidade", "Acurácia"])
        doencas = self.get_all_doencas()
        for doenca in doencas:
            diagnostico = sorted(self.get_diagnostico_by_doenca(doenca))
            df = pd.concat([df, pd.DataFrame([{
                "Doença": diagnostico.doenca.name,
                "Diagnostico": diagnostico.expressao,
                "Especificidade": diagnostico.especificidade,
                "Sensibilidade": diagnostico.sensibilidade,
                "Acurácia": diagnostico.acuracia
            }])], ignore_index=True)
        st.dataframe(df)