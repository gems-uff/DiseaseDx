from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectin_polymorphic, subqueryload, selectinload
from sqlalchemy import create_engine
from db_config import DatabaseConfig
from models import Doenca, Diagnostico, Or, And, AoMenos, Sintoma, Manifestacao, RegiaoComposta, RegiaoDoCorpo, Orgao, Exame, Resultado, Expressao, FatosSintomaResultado, AvaliaNode, Flyweight, FlyweightFactory
import streamlit as st
import pandas as pd
from tribool import Tribool


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
    

    # Função para buscar todas as manifestações do banco de dados
    def get_all_manifestacoes(self):
        with Session(self.engine, expire_on_commit=False) as session:
            statement = select(Manifestacao)
            manifestacoes = session.scalars(statement).unique().all()
            return manifestacoes
    

    # Função para buscar todas as regiões compostas do banco de dados
    def get_all_regioes_compostas(self):
        with Session(self.engine, expire_on_commit=False) as session:
            statement = select(RegiaoComposta)
            regioes_compostas = session.scalars(statement).unique().all()
            return regioes_compostas
        
    
    # Função para buscar todos os órgãos do banco de dados
    def get_all_orgaos(self):
        with Session(self.engine, expire_on_commit=False) as session:
            statement = select(Orgao)
            orgaos = session.scalars(statement).unique().all()
            return orgaos
        
    
    # Função para buscar todos os exames do banco de dados
    def get_all_exames(self):
        with Session(self.engine, expire_on_commit=False) as session:
            statement = select(Exame)
            exames = session.scalars(statement).unique().all()
            return exames


    # Função para buscar todos os sintomas do banco de dados
    def get_all_sintomas(self):
        with Session(self.engine, expire_on_commit=False) as session:
            statement = select(Sintoma).options(
                joinedload(Sintoma.manifestacao),
                joinedload(Sintoma.regiao_do_corpo)
            )
            sintomas = session.scalars(statement).unique().all()
            return sintomas
        
        
    # Função para buscar todos os resultados do banco de dados
    def get_all_resultados(self):
        with Session(self.engine, expire_on_commit=False) as session:
            statement = select(Resultado).options(
                joinedload(Resultado.exame)
            )
            resultados = session.scalars(statement).unique().all()
            return resultados
        
    
    # Função para buscar todas as doenças
    def get_all_doencas(self):
        with Session(self.engine, expire_on_commit=False) as session:
            doencas = session.query(Doenca).all()
            return doencas
        
    
    # Função para buscar todas as expressões do banco de dados
    def get_all_expressions(self):
        with Session(self.engine, expire_on_commit=False) as session:
            statement = select(Expressao)
            expressao = session.scalars(statement).unique().all()
            print(f"Expressao: {expressao}") # TODO: Ajeitar o loading para evitar DetachedInstanceError
            return expressao
        

    # Função para buscar todos os sintomas associados a uma doença
    def get_sintomas_by_doenca(self, target_doenca):
        with Session(self.engine, expire_on_commit=False) as session:
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
        with Session(self.engine, expire_on_commit=False) as session:
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


    # Função para buscar todos os diagnósticos associados a um sintoma
    def get_diagnosticos_by_sintoma(self, sintoma):
        with Session(self.engine, expire_on_commit=False) as session:
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
        

    # Função para buscar todos os diagnósitcos associados a um resultado
    def get_diagnosticos_by_resultado(self, resultado):
        with Session(self.engine, expire_on_commit=False) as session:
            resultado = session.get(Resultado, resultado.id)

            diagnosticos = session.query(Diagnostico).options(
                joinedload(Diagnostico.doenca),
                joinedload(Diagnostico.expressao)
            ).all()

            diagnosticos_filtrados = {}
            for diag in diagnosticos:
                if self.contains_expression(diag.expressao, resultado):
                    diagnosticos_filtrados[diag] = diag.expressao

            return diagnosticos_filtrados
        

    # Função para buscar o diagnóstico de uma doença
    def get_diagnostico_by_doenca(self, doenca):
        with Session(self.engine, expire_on_commit=False) as session:
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
        with Session(self.engine, expire_on_commit=False) as session:
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
            avalia_dict = {}

            # TODO: Validar essa lógica novamente
            fatos = FatosSintomaResultado(sintomas, sintomas_presentes, sintomas_ausentes, resultados, resultados_presentes, resultados_ausentes)
            fatos.print_fatos()
            for diag in diagnosticos:
                print(f"\n- Doenca: {diag.doenca.name}")
                avalia_result, avalia_return = diag.expressao.avalia(fatos)
                print(f"- Avalia Result: {avalia_result}")
                avalia_return.print_tree() # TODO: Ajeitar o loading para evitar DetachedInstanceError

                if avalia_result.value is not False:
                    diagnosticos_filtrados[diag.doenca] = diag.expressao

                avalia_dict[diag.doenca] = avalia_return

            return diagnosticos_filtrados, avalia_dict
        
    
    # Função para buscar o sintoma mais comum entre todos os diagnósticos
    def get_most_common_sintoma(self, sintomas, present_sintomas, not_present_sintomas):
        max_ammount = 0
        with Session(self.engine, expire_on_commit=False) as session:

            if len(sintomas) == 0:
                sintomas = self.get_all_sintomas()
            else:
                sintomas = [session.get(Sintoma, sintoma.id) for sintoma in sintomas]

            not_already_selected_sintomas = [sintoma for sintoma in sintomas if sintoma not in present_sintomas and sintoma not in not_present_sintomas]

            for sintoma in not_already_selected_sintomas:
                diagnosticos = self.get_diagnosticos_by_sintoma(sintoma)
                ammount = len(diagnosticos)
                if ammount > max_ammount:
                    max_ammount = ammount
                    most_common_sintoma = sintoma

            most_common_sintoma.manifestacao = session.get(Manifestacao, most_common_sintoma.manifestacao_id)  
            if most_common_sintoma.regiao_do_corpo != None:
                most_common_sintoma.regiao_do_corpo = session.get(RegiaoDoCorpo, most_common_sintoma.regiao_do_corpo_id)      

        return most_common_sintoma
    
    
    # Função para buscar o resultado mais comum entre todos os diagnósticos
    def get_most_common_resultado(self, resultados, present_resultados, not_present_resultados):
        max_ammount = 0
        with Session(self.engine, expire_on_commit=False) as session:

            if len(resultados) == 0:
                resultados = self.get_all_resultados()
            else:
                resultados = [session.get(Resultado, resultado.id) for resultado in resultados]

            not_already_selected_resultados = [resultado for resultado in resultados if resultado not in present_resultados and resultado not in not_present_resultados]

            for resultado in not_already_selected_resultados:
                diagnosticos = self.get_diagnosticos_by_resultado(resultado)
                ammount = len(diagnosticos)
                if ammount > max_ammount:
                    max_ammount = ammount
                    most_common_resultado = resultado

            most_common_resultado.exame = session.get(Exame, most_common_resultado.exame_id)  

        return most_common_resultado











    # Função para adicionar uma nova manifestação ao banco de dados
    def add_manifestacao(self, manifestacao):
        with Session(self.engine, expire_on_commit=False) as session:
            session.add(manifestacao)
            session.commit()
            return manifestacao


    # Função para adicionar um novo órgão ao banco de dados
    def add_orgao(self, orgao):
        with Session(self.engine, expire_on_commit=False) as session:
            session.add(orgao)
            session.commit()
            return orgao
        

    # Função para adicionar uma nova região composta ao banco de dados
    def add_regiao_composta(self, regiao_composta):
        with Session(self.engine, expire_on_commit=False) as session:
            session.add(regiao_composta)
            session.commit()
            return regiao_composta
        
    
    # Função para adicionar um novo sintoma ao banco de dados
    def add_sintoma(self, sintoma):
        with Session(self.engine, expire_on_commit=False) as session:
            session.add(sintoma)
            session.commit()
            return sintoma








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
        df_sorted = df.sort_values(by="Count", ascending=False)
        st.dataframe(df_sorted)


    # Criar um dataframe para exibir as informações de todos as doenças associadas a cada resultado
    def st_write_resultado_doencas_table(self):
        df = pd.DataFrame(columns=["Resultado", "Doenças", "Count"])
        resultados = self.get_all_resultados()
        for resultado in resultados:
            diagnosticos = self.get_diagnosticos_by_resultado(resultado)
            doencas_names = sorted([diagnostico.doenca.name for diagnostico in diagnosticos])
            df = pd.concat([df, pd.DataFrame([{
                "Resultado": f"{resultado.name}",
                "Doenças": doencas_names,
                "Count": len(doencas_names)
            }])], ignore_index=True)
        df_sorted = df.sort_values(by="Count", ascending=False)
        st.dataframe(df_sorted)


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