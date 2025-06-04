from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload
from db_config import DatabaseConfig
from models import Doenca, Diagnostico, Or, And, AoMenos, Sintoma, Manifestacao, RegiaoComposta, RegiaoDoCorpo, Orgao, Exame, Resultado, Expressao, FatosSintomaResultado, AvaliaNode
import streamlit as st
import pandas as pd
from tribool import Tribool




class StreamlitQueries():
    """
    Class to handle all queries to the database using SQLAlchemy.
    It uses Streamlit's caching to optimize the performance of the queries.
    """
    def __init__(self) -> None:
        """
        Initialize the class and load the database engine.
        It also loads all classes related to the diagnosis from the database into memory, saving them in dictionaries.
        This dictionary is used to avoid querying the database multiple times.
        We use it in the add functions to avoid duplicate entries by checking if it's already in the dict.
        """
        self.engine = DatabaseConfig().load_engine()
        self.manifestacao_cache = {}
        self.orgao_cache = {}
        self.regiao_cache = {}
        self.sintoma_cache = {}
        self.exame_cache = {}
        self.resultado_cache = {}
        self.doenca_cache = {}
        self.and_cache = {}
        self.or_cache = {}
        self.aomenos_cache = {}
        self.diagnostico_cache = {}

        with Session(self.engine, expire_on_commit=False) as session:
            for obj in session.query(Manifestacao).all():
                key = (obj.name,)
                self.manifestacao_cache[key] = obj

            for obj in session.query(Orgao).all():
                key = (obj.name,)
                self.orgao_cache[key] = obj
            
            for obj in session.query(RegiaoDoCorpo).all():
                key = (obj.name, obj.type)
                self.regiao_cache[key] = obj

            for obj in session.query(Sintoma).all():
                key = (
                    obj.manifestacao.id if obj.manifestacao else None,
                    obj.regiao_do_corpo.id if obj.regiao_do_corpo else None,
                )
                self.sintoma_cache[key] = obj

            for obj in session.query(Exame).all():
                key = (obj.name, obj.preco)
                self.exame_cache[key] = obj

            for obj in session.query(Resultado).all():
                key = (obj.name, obj.exame.id if obj.exame else None)
                self.resultado_cache[key] = obj

            for obj in session.query(Doenca).all():
                key = (obj.name,)
                self.doenca_cache[key] = obj

            # for obj in session.query(And).all():
            #     key = (obj.left_expr.id, obj.right_expr.id)
            #     self.and_cache[key] = obj
            
            # for obj in session.query(Or).all():
            #     ids = sorted([obj.left_expr.id, obj.right_expr.id])
            #     key = tuple(ids)
            #     self.or_cache[key] = obj

            for obj in session.query(AoMenos).all():
                ids = tuple(sorted(e.id for e in obj.expressoes))
                key = (obj.qtd, ids)
                self.aomenos_cache[key] = obj

            for obj in session.query(Diagnostico).all():
                key = (obj.doenca.id if obj.doenca else None, obj.expressao.id if obj.expressao else None)
                self.diagnostico_cache[key] = obj




    def contains_expression(self, expr, target_expr) -> bool:
        """
        Check if the expression contains the target expression.
        This is used to check if a symptom or result is part of the expression.
        """
        if expr == target_expr:
            return True
        if isinstance(expr, (And, Or, AoMenos)):
            return any(self.contains_expression(e, target_expr) for e in expr.expressoes)
        return False
    
    
    

    def get_all_sintomas_from_expression(_self, expr) -> list[Sintoma]:
        """
        Function to get all symptoms from an expression.
        It uses a recursive function to traverse the expression tree and collect all symptoms.
        """
        sintomas = set()
        
        def collect_sintomas(expr):
            if isinstance(expr, Sintoma):
                sintomas.add(expr)
            elif isinstance(expr, (And, Or, AoMenos)):
                for e in expr.expressoes:
                    collect_sintomas(e)
        
        collect_sintomas(expr)
        return list(sintomas)
    



    def get_all_resultados_from_expression(_self, expr) -> list[Resultado]:
        """
        Function to get all results from an expression.
        It uses a recursive function to traverse the expression tree and collect all results.
        """
        resultados = set()
        
        def collect_resultados(expr):
            if isinstance(expr, Resultado):
                resultados.add(expr)
            elif isinstance(expr, (And, Or, AoMenos)):
                for e in expr.expressoes:
                    collect_resultados(e)
        
        collect_resultados(expr)
        return list(resultados)
    



    @st.cache_data
    def get_all_manifestacoes(_self) -> list[Manifestacao]:
        """
        Function to get all manifestations from the database.
        """
        with Session(_self.engine, expire_on_commit=False) as session:
            statement = select(Manifestacao)
            manifestacoes = session.scalars(statement).unique().all()
            return manifestacoes
    

    

    @st.cache_data
    def get_all_regioes_compostas(_self) -> list[RegiaoComposta]:
        """
        Function to get all composed regions from the database.
        """
        with Session(_self.engine, expire_on_commit=False) as session:
            statement = select(RegiaoComposta)
            regioes_compostas = session.scalars(statement).unique().all()
            return regioes_compostas
        
    
    

    @st.cache_data
    def get_all_orgaos(_self) -> list[Orgao]:
        """
        Function to get all organs from the database.
        """
        with Session(_self.engine, expire_on_commit=False) as session:
            statement = select(Orgao)
            orgaos = session.scalars(statement).unique().all()
            return orgaos
        
    
    

    @st.cache_data
    def get_all_exames(_self) -> list[Exame]:
        """
        Function to get all exams from the database.
        """
        with Session(_self.engine, expire_on_commit=False) as session:
            statement = select(Exame)
            exames = session.scalars(statement).unique().all()
            return exames


    

    @st.cache_data
    def get_all_sintomas(_self) -> list[Sintoma]:
        """
        Function to get all symptoms from the database.
        """
        with Session(_self.engine, expire_on_commit=False) as session:
            statement = select(Sintoma).options(
                joinedload(Sintoma.manifestacao),
                joinedload(Sintoma.regiao_do_corpo)
            )
            sintomas = session.scalars(statement).unique().all()
            return sintomas
        
        
    

    @st.cache_data
    def get_all_resultados(_self) -> list[Resultado]:
        """
        Function to get all results from the database.
        """
        with Session(_self.engine, expire_on_commit=False) as session:
            statement = select(Resultado).options(
                joinedload(Resultado.exame)
            )
            resultados = session.scalars(statement).unique().all()
            return resultados
        
    
    

    @st.cache_data
    def get_all_doencas(_self) -> list[Doenca]:
        """
        Function to get all diseases from the database.
        """
        with Session(_self.engine, expire_on_commit=False) as session:
            doencas = session.query(Doenca).all()
            return doencas
        
    
    

    @st.cache_data
    def get_all_expressions(_self) -> list[Expressao]:
        """
        Function to get all expressions from the database.
        """
        with Session(_self.engine, expire_on_commit=False) as session:
            statement = select(Expressao)
            expressao = session.scalars(statement).unique().all()
            print(f"Expressao: {expressao}") # TODO: Ajeitar o loading para evitar DetachedInstanceError
            return expressao
        






    
    @st.cache_data(hash_funcs={Doenca: lambda doenca: doenca.id})
    def get_sintomas_by_doenca(_self, target_doenca) -> list[Sintoma]:
        """
        Function to get all symptoms associated with a disease.
        """
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
            
            # TODO: Ver eager loading pra evitar DetachedInstanceError
            for sintoma in sintomas:
                if sintoma.regiao_do_corpo != None:
                    sintoma.regiao_do_corpo = session.get(RegiaoDoCorpo, sintoma.regiao_do_corpo_id)
                sintoma.manifestacao = session.get(Manifestacao, sintoma.manifestacao_id)

            return sintomas
        


    
    @st.cache_data(hash_funcs={Doenca: lambda doenca: doenca.id})
    def get_resultados_by_doenca(_self, target_doenca) -> list[Resultado]:
        """
        Function to get all results associated with a disease.
        """
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




    @st.cache_data(hash_funcs={Sintoma: lambda sintoma: sintoma.id})
    def get_diagnosticos_by_sintoma(_self, sintoma) -> list[Diagnostico]:
        """
        Function to get all diagnoses associated with a symptom.
        """
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
        

    

    @st.cache_data(hash_funcs={Resultado: lambda resultado: resultado.id})
    def get_diagnosticos_by_resultado(_self, resultado) -> list[Diagnostico]:
        """
        Function to get all diagnoses associated with a result.
        """
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
        

    

    @st.cache_data(hash_funcs={Doenca: lambda doenca: doenca.id})
    def get_diagnostico_by_doenca(_self, doenca) -> Diagnostico:
        """
        Function to get the diagnosis associated with a disease.
        """
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


    

    @st.cache_data(hash_funcs={Sintoma: lambda sintoma: sintoma.id, Resultado: lambda resultado: resultado.id})
    def get_diagnosticos_by_list_of_sintomas_and_resultados(_self, present_sintomas, not_present_sintomas, present_resultados, not_present_resultados) -> list[Diagnostico]:
        """
        Function to get all diagnoses associated with a list of symptoms and results.
        """
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
            
            diagnosticos_filtrados = {}

            fatos = FatosSintomaResultado(sintomas, sintomas_presentes, sintomas_ausentes, resultados, resultados_presentes, resultados_ausentes)

            for diag in diagnosticos:
                print(f"\n- Doenca: {diag.doenca.name}")
                avalia_result, avalia_return = diag.expressao.avalia(fatos)
                print(f"- Avalia Result: {avalia_result}")
                avalia_return.print_tree() # TODO: Ajeitar o loading para evitar DetachedInstanceError

                if avalia_result.value is not False:
                    diagnosticos_filtrados[diag.doenca] = diag.expressao

            return diagnosticos_filtrados




    @st.cache_data(hash_funcs={Sintoma: lambda sintoma: sintoma.id, Resultado: lambda resultado: resultado.id})
    def get_diagnosticos_avaliacoes_by_list_of_sintomas_and_resultados(_self, present_sintomas, not_present_sintomas, present_resultados, not_present_resultados) -> dict[Doenca, tuple[AvaliaNode, float]]:
        """
        Function to get all diagnoses evaluations associated with a list of symptoms and results.
        """
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

            fatos = FatosSintomaResultado(sintomas, sintomas_presentes, sintomas_ausentes, resultados, resultados_presentes, resultados_ausentes)
            fatos.print_fatos()
            for diag in diagnosticos:
                print(f"\n- Doenca: {diag.doenca.name}")
                avalia_result, avalia_return = diag.expressao.avalia(fatos)
                print(f"- Avalia Result: {avalia_result}")
                avalia_return.print_tree() # TODO: Ajeitar o loading para evitar DetachedInstanceError

                diag_score = f"{avalia_return.score:.2f}"

                avalia_dict[diag.doenca] = (avalia_return, diag_score)

            return avalia_dict
        
    
    

    @st.cache_data(hash_funcs={Sintoma: lambda sintoma: sintoma.id})
    def get_most_common_sintoma(_self, sintomas, present_sintomas, not_present_sintomas) -> Sintoma:
        """
        Function to get the most common symptom among all diagnoses.
        """
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
    
    
    

    @st.cache_data(hash_funcs={Resultado: lambda resultado: resultado.id})
    def get_most_common_resultado(_self, resultados, present_resultados, not_present_resultados) -> Resultado:
        """
        Function to get the most common result among all diagnoses.
        """
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







    
    def add_manifestacao(self, manifestacao_str) -> str:
        """
        Function to add a new manifestation to the database.
        """
        manifestacao = Manifestacao(name=manifestacao_str)
        if self.manifestacoes.get(manifestacao_str) == None and manifestacao_str != "":
            self.manifestacoes[manifestacao_str] = manifestacao
            with Session(self.engine, expire_on_commit=False) as session:
                session.add(manifestacao)
                session.commit()
            return 'Created'
        else:
            return 'Exists'
        
    


    def add_or(self, left_expr, right_expr) -> str:
        """
        Function to add a new Or object to the database.
        """
        # Create a unique key for the Or object based on the left and right expressions
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


    

    def add_orgao(self, orgao) -> str:
        """
        Function to add a new organ to the database.
        """
        with Session(self.engine, expire_on_commit=False) as session:
            session.add(orgao)
            session.commit()
            return orgao
        

    

    def add_regiao_composta(self, regiao_composta) -> str:
        """
        Function to add a new composed region to the database.
        """
        with Session(self.engine, expire_on_commit=False) as session:
            session.add(regiao_composta)
            session.commit()
            return regiao_composta
        
    
    

    def add_sintoma(self, sintoma) -> str:
        """
        Function to add a new symptom to the database.
        """
        with Session(self.engine, expire_on_commit=False) as session:
            session.add(sintoma)
            session.commit()
            return sintoma







    
    @st.cache_data
    def st_write_sintoma_doencas_table(_self) -> pd.DataFrame:
        """
        Create a dataframe to display the information of all diseases associated with each symptom.
        """
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
        return df_sorted


    

    @st.cache_data
    def st_write_resultado_doencas_table(_self) -> pd.DataFrame:
        """
        Create a dataframe to display the information of all diseases associated with each result.
        """
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
        return df_sorted


    

    @st.cache_data
    def st_write_doenca_sintomas_table(_self) -> pd.DataFrame:
        """
        Create a dataframe to display the information of all diseases and their symptoms.
        """
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
        return df


    

    @st.cache_data(hash_funcs={Doenca: lambda doenca: doenca.id})
    def st_write_doenca_sintomas_resultados_table(_self) -> pd.DataFrame:
        """
        Create a dataframe to display the information of all diseases, their symptoms and results.
        """
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
        return df


    

    @st.cache_data
    def st_write_doenca_diagnostico_table(_self) -> pd.DataFrame:
        """
        Create a dataframe to display the information of all diseases and their diagnoses.
        """
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
        return df