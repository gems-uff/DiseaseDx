from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectin_polymorphic, subqueryload, selectinload
from sqlalchemy import create_engine
from db_config import DatabaseConfig
from models import Doenca, Diagnostico, Or, And, AoMenos, Sintoma, Manifestacao, RegiaoComposta, RegiaoDoCorpo, Orgao, Exame, Resultado, Expressao, FatosSintomaResultado, AvaliaNode
import streamlit as st
import pandas as pd
from tribool import Tribool


class StreamlitQueries():
    def __init__(self):
        self.engine = DatabaseConfig().load_engine()
        self.manifestacoes = {}
        self.or_cache = {}
        with Session(self.engine, expire_on_commit=False) as session:
            # Carregar todas as manifestações do banco de dados
            manifestacoes = session.query(Manifestacao).all()
            for man in manifestacoes:
                self.manifestacoes[man.name] = man
            
            # Carregar todos os or's do banco de dados
            ors = session.query(Or).all()
            for or_ in ors:
                key = (or_.left_expr_id, or_.right_expr_id)
                self.or_cache[key] = or_


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
    def get_all_sintomas_from_expression(_self, expr):
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
    def get_all_resultados_from_expression(_self, expr):
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
    @st.cache_data
    def get_all_manifestacoes(_self):
        with Session(_self.engine, expire_on_commit=False) as session:
            statement = select(Manifestacao)
            manifestacoes = session.scalars(statement).unique().all()
            return manifestacoes
    

    # Função para buscar todas as regiões compostas do banco de dados
    @st.cache_data
    def get_all_regioes_compostas(_self):
        with Session(_self.engine, expire_on_commit=False) as session:
            statement = select(RegiaoComposta)
            regioes_compostas = session.scalars(statement).unique().all()
            return regioes_compostas
        
    
    # Função para buscar todos os órgãos do banco de dados
    @st.cache_data
    def get_all_orgaos(_self):
        with Session(_self.engine, expire_on_commit=False) as session:
            statement = select(Orgao)
            orgaos = session.scalars(statement).unique().all()
            return orgaos
        
    
    # Função para buscar todos os exames do banco de dados
    @st.cache_data
    def get_all_exames(_self):
        with Session(_self.engine, expire_on_commit=False) as session:
            statement = select(Exame)
            exames = session.scalars(statement).unique().all()
            return exames


    # Função para buscar todos os sintomas do banco de dados
    @st.cache_data
    def get_all_sintomas(_self):
        with Session(_self.engine, expire_on_commit=False) as session:
            statement = select(Sintoma).options(
                joinedload(Sintoma.manifestacao),
                joinedload(Sintoma.regiao_do_corpo)
            )
            sintomas = session.scalars(statement).unique().all()
            return sintomas
        
        
    # Função para buscar todos os resultados do banco de dados
    @st.cache_data
    def get_all_resultados(_self):
        with Session(_self.engine, expire_on_commit=False) as session:
            statement = select(Resultado).options(
                joinedload(Resultado.exame)
            )
            resultados = session.scalars(statement).unique().all()
            return resultados
        
    
    # Função para buscar todas as doenças
    @st.cache_data
    def get_all_doencas(_self):
        with Session(_self.engine, expire_on_commit=False) as session:
            doencas = session.query(Doenca).all()
            return doencas
        
    
    # Função para buscar todas as expressões do banco de dados
    @st.cache_data
    def get_all_expressions(_self):
        with Session(_self.engine, expire_on_commit=False) as session:
            statement = select(Expressao)
            expressao = session.scalars(statement).unique().all()
            print(f"Expressao: {expressao}") # TODO: Ajeitar o loading para evitar DetachedInstanceError
            return expressao
        

    # Função para buscar todos os sintomas associados a uma doença
    @st.cache_data(hash_funcs={Doenca: lambda doenca: doenca.id})
    def get_sintomas_by_doenca(_self, target_doenca):
        with Session(_self.engine, expire_on_commit=False) as session:
            target_doenca = session.get(Doenca, target_doenca.id)

            diagnosticos = session.query(Diagnostico).options(
                joinedload(Diagnostico.doenca),
                joinedload(Diagnostico.expressao)
            ).all()

            sintomas = []
            for diag in diagnosticos:
                if diag.doenca == target_doenca:
                    sintomas = _self.get_all_sintomas_from_expression(diag.expressao)
            
            # TODO: Melhor do que usar o st.write como gambiarra mas deve ser melhor entendendo os tipos de load do sqlalchemy como selectin polymorphic (problema do DetachedInstanceError)
            for sintoma in sintomas:
                if sintoma.regiao_do_corpo != None:
                    sintoma.regiao_do_corpo = session.get(RegiaoDoCorpo, sintoma.regiao_do_corpo_id)
                sintoma.manifestacao = session.get(Manifestacao, sintoma.manifestacao_id)

            return sintomas
        
    
    # Função para buscar todos os resultados associados a uma doença
    @st.cache_data(hash_funcs={Doenca: lambda doenca: doenca.id})
    def get_resultados_by_doenca(_self, target_doenca):
        with Session(_self.engine, expire_on_commit=False) as session:
            target_doenca = session.get(Doenca, target_doenca.id)

            diagnosticos = session.query(Diagnostico).options(
                joinedload(Diagnostico.doenca),
                joinedload(Diagnostico.expressao)
            ).all()

            resultados = []
            for diag in diagnosticos:
                if diag.doenca == target_doenca:
                    resultados = _self.get_all_resultados_from_expression(diag.expressao)

            for resultado in resultados:
                resultado.exame = session.get(Exame, resultado.exame_id)

            return resultados


    # Função para buscar todos os diagnósticos associados a um sintoma
    @st.cache_data(hash_funcs={Sintoma: lambda sintoma: sintoma.id})
    def get_diagnosticos_by_sintoma(_self, sintoma):
        with Session(_self.engine, expire_on_commit=False) as session:
            sintoma = session.get(Sintoma, sintoma.id)

            diagnosticos = session.query(Diagnostico).options(
                joinedload(Diagnostico.doenca),
                joinedload(Diagnostico.expressao)
            ).all()

            diagnosticos_filtrados = {}
            for diag in diagnosticos:
                if _self.contains_expression(diag.expressao, sintoma):
                    diagnosticos_filtrados[diag] = diag.expressao

            return diagnosticos_filtrados
        

    # Função para buscar todos os diagnósitcos associados a um resultado
    @st.cache_data(hash_funcs={Resultado: lambda resultado: resultado.id})
    def get_diagnosticos_by_resultado(_self, resultado):
        with Session(_self.engine, expire_on_commit=False) as session:
            resultado = session.get(Resultado, resultado.id)

            diagnosticos = session.query(Diagnostico).options(
                joinedload(Diagnostico.doenca),
                joinedload(Diagnostico.expressao)
            ).all()

            diagnosticos_filtrados = {}
            for diag in diagnosticos:
                if _self.contains_expression(diag.expressao, resultado):
                    diagnosticos_filtrados[diag] = diag.expressao

            return diagnosticos_filtrados
        

    # Função para buscar o diagnóstico de uma doença
    @st.cache_data(hash_funcs={Doenca: lambda doenca: doenca.id})
    def get_diagnostico_by_doenca(_self, doenca):
        with Session(_self.engine, expire_on_commit=False) as session:
            doenca = session.get(Doenca, doenca.id)

            diagnosticos = session.query(Diagnostico).options(
                joinedload(Diagnostico.doenca),
                joinedload(Diagnostico.expressao)
            ).all()

            for diag in diagnosticos:
                if diag.doenca == doenca:
                    return diag

            return diag
        
    
    # Função para calcular o score de um nó
    def get_score(_self, node: AvaliaNode):
        if isinstance(node.instance, (Sintoma, Resultado)):
            if node.result is Tribool(True):
                score = 1
            elif node.result is Tribool(False):
                score = -0.5
            else:
                score = 0
        else:
            score = 0

        for child in node.children:
            score += _self.get_score(child)

        return score


    # Função para buscar todas as possíveis doenças associadas a listas de sintomas presentes e ausentes
    @st.cache_data(hash_funcs={Sintoma: lambda sintoma: sintoma.id, Resultado: lambda resultado: resultado.id})
    def get_diagnosticos_by_list_of_sintomas_and_resultados(_self, present_sintomas, not_present_sintomas, present_resultados, not_present_resultados):
        with Session(_self.engine, expire_on_commit=False) as session:
            sintomas = _self.get_all_sintomas()
            sintomas_presentes = [session.get(Sintoma, sintoma.id) for sintoma in present_sintomas]
            sintomas_ausentes = [session.get(Sintoma, sintoma.id) for sintoma in not_present_sintomas]

            resultados = _self.get_all_resultados()
            resultados_presentes = [session.get(Resultado, resultado.id) for resultado in present_resultados]
            resultados_ausentes = [session.get(Resultado, resultado.id) for resultado in not_present_resultados]

            diagnosticos = session.query(Diagnostico).options(
                joinedload(Diagnostico.doenca),
                joinedload(Diagnostico.expressao)
            ).all()
            
            avalia_dict = {}

            # TODO: Validar essa lógica novamente
            fatos = FatosSintomaResultado(sintomas, sintomas_presentes, sintomas_ausentes, resultados, resultados_presentes, resultados_ausentes)
            fatos.print_fatos()
            for diag in diagnosticos:
                print(f"\n- Doenca: {diag.doenca.name}")
                avalia_result, avalia_return = diag.expressao.avalia(fatos)
                print(f"- Avalia Result: {avalia_result}")
                avalia_return.print_tree() # TODO: Ajeitar o loading para evitar DetachedInstanceError

                diag_score = _self.get_score(avalia_return)

                avalia_dict[diag.doenca] = (avalia_return, diag_score)

            return avalia_dict
        
    
    # Função para buscar o sintoma mais comum entre todos os diagnósticos
    @st.cache_data(hash_funcs={Sintoma: lambda sintoma: sintoma.id})
    def get_most_common_sintoma(_self, sintomas, present_sintomas, not_present_sintomas):
        max_ammount = 0
        with Session(_self.engine, expire_on_commit=False) as session:

            if len(sintomas) == 0:
                sintomas = _self.get_all_sintomas()
            else:
                sintomas = [session.get(Sintoma, sintoma.id) for sintoma in sintomas]

            not_already_selected_sintomas = [sintoma for sintoma in sintomas if sintoma not in present_sintomas and sintoma not in not_present_sintomas]

            for sintoma in not_already_selected_sintomas:
                diagnosticos = _self.get_diagnosticos_by_sintoma(sintoma)
                ammount = len(diagnosticos)
                if ammount > max_ammount:
                    max_ammount = ammount
                    most_common_sintoma = sintoma

            most_common_sintoma.manifestacao = session.get(Manifestacao, most_common_sintoma.manifestacao_id)  
            if most_common_sintoma.regiao_do_corpo != None:
                most_common_sintoma.regiao_do_corpo = session.get(RegiaoDoCorpo, most_common_sintoma.regiao_do_corpo_id)      

        return most_common_sintoma
    
    
    # Função para buscar o resultado mais comum entre todos os diagnósticos
    @st.cache_data(hash_funcs={Resultado: lambda resultado: resultado.id})
    def get_most_common_resultado(_self, resultados, present_resultados, not_present_resultados):
        max_ammount = 0
        with Session(_self.engine, expire_on_commit=False) as session:

            if len(resultados) == 0:
                resultados = _self.get_all_resultados()
            else:
                resultados = [session.get(Resultado, resultado.id) for resultado in resultados]

            not_already_selected_resultados = [resultado for resultado in resultados if resultado not in present_resultados and resultado not in not_present_resultados]

            for resultado in not_already_selected_resultados:
                diagnosticos = _self.get_diagnosticos_by_resultado(resultado)
                ammount = len(diagnosticos)
                if ammount > max_ammount:
                    max_ammount = ammount
                    most_common_resultado = resultado

            most_common_resultado.exame = session.get(Exame, most_common_resultado.exame_id)  

        return most_common_resultado











    # Função para adicionar uma nova manifestação ao banco de dados
    def add_manifestacao(self, manifestacao_str):
        manifestacao = Manifestacao(name=manifestacao_str)
        if self.manifestacoes.get(manifestacao_str) == None and manifestacao_str != "":
            self.manifestacoes[manifestacao_str] = manifestacao
            with Session(self.engine, expire_on_commit=False) as session:
                session.add(manifestacao)
                session.commit()
            return 'Created'
        else:
            return 'Exists'
        
    # Função para adicionar um novo or ao banco de dados
    def add_or(self, left_expr, right_expr):
        # Generate a unique key based on the IDs of left_expr and right_expr
        key = (left_expr.id, right_expr.id)

        # Check if the Or object already exists in the cache
        if key in self.or_cache:
            return 'Exists'

        # Check if the Or object exists in the database
        with Session(self.engine, expire_on_commit=False) as session:
            existing_or = session.query(Or).filter_by(left_expr_id=left_expr.id, right_expr_id=right_expr.id).first()
            if existing_or:
                self.or_cache[key] = existing_or
                return 'Exists'

            # Create a new Or object if it doesn't exist
            new_or = Or(left=left_expr, right=right_expr)
            session.add(new_or)
            session.commit()

            # Add the new Or object to the cache
            self.or_cache[key] = new_or
            return 'Created'


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
    @st.cache_data
    def st_write_sintoma_doencas_table(_self):
        df = pd.DataFrame(columns=["Sintoma", "Doenças", "Count"])
        sintomas = _self.get_all_sintomas()
        for sintoma in sintomas:
            diagnosticos = _self.get_diagnosticos_by_sintoma(sintoma)
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
        # st.dataframe(df_sorted)
        return df_sorted


    # Criar um dataframe para exibir as informações de todos as doenças associadas a cada resultado
    @st.cache_data
    def st_write_resultado_doencas_table(_self):
        df = pd.DataFrame(columns=["Resultado", "Doenças", "Count"])
        resultados = _self.get_all_resultados()
        for resultado in resultados:
            diagnosticos = _self.get_diagnosticos_by_resultado(resultado)
            doencas_names = sorted([diagnostico.doenca.name for diagnostico in diagnosticos])
            df = pd.concat([df, pd.DataFrame([{
                "Resultado": f"{resultado.name}",
                "Doenças": doencas_names,
                "Count": len(doencas_names)
            }])], ignore_index=True)
        df_sorted = df.sort_values(by="Count", ascending=False)
        # st.dataframe(df_sorted)
        return df_sorted


    # Criar um dataframe para exibir todos os sintomas de uma doença
    @st.cache_data
    def st_write_doenca_sintomas_table(_self):
        df = pd.DataFrame(columns=["Doença", "Sintomas"])
        doencas = _self.get_all_doencas()
        for doenca in doencas:
            sintomas = _self.get_sintomas_by_doenca(doenca)
            sintomas_names = sorted([
                f"{sintoma.manifestacao.name} no (a) {sintoma.regiao_do_corpo.name}" if sintoma.regiao_do_corpo 
                else f"{sintoma.manifestacao.name}" 
                for sintoma in sintomas
            ])
            df = pd.concat([df, pd.DataFrame([{
                "Doença": doenca.name,
                "Sintomas": sintomas_names
            }])], ignore_index=True)
        # st.dataframe(df)
        return df


    # Criar um dataframe para exibir todos os sintomas e resultados de uma doença
    @st.cache_data(hash_funcs={Doenca: lambda doenca: doenca.id})
    def st_write_doenca_sintomas_resultados_table(_self):
        df = pd.DataFrame(columns=["Doença", "Sintomas", "Resultados"])
        doencas = _self.get_all_doencas()
        for doenca in doencas:
            sintomas = _self.get_sintomas_by_doenca(doenca)
            sintomas_names = sorted([
                f"{sintoma.manifestacao.name} no (a) {sintoma.regiao_do_corpo.name}" if sintoma.regiao_do_corpo 
                else f"{sintoma.manifestacao.name}" 
                for sintoma in sintomas
            ])
            resultados = _self.get_resultados_by_doenca(doenca)
            resultados_names = sorted([resultado.name for resultado in resultados])
            df = pd.concat([df, pd.DataFrame([{
                "Doença": doenca.name,
                "Sintomas": sintomas_names,
                "Resultados": resultados_names
            }])], ignore_index=True)
        # st.dataframe(df)
        return df


    # Criar um dataframe para exibir a expressão de cada diagnóstico
    @st.cache_data
    def st_write_doenca_diagnostico_table(_self):
        df = pd.DataFrame(columns=["Doença", "Diagnostico", "Especificidade", "Sensibilidade", "Acurácia"])
        doencas = _self.get_all_doencas()
        for doenca in doencas:
            diagnostico = sorted(_self.get_diagnostico_by_doenca(doenca))
            df = pd.concat([df, pd.DataFrame([{
                "Doença": diagnostico.doenca.name,
                "Diagnostico": diagnostico.expressao,
                "Especificidade": diagnostico.especificidade,
                "Sensibilidade": diagnostico.sensibilidade,
                "Acurácia": diagnostico.acuracia
            }])], ignore_index=True)
        # st.dataframe(df)
        return df