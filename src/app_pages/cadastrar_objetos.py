from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectin_polymorphic, subqueryload, selectinload
from sqlalchemy import create_engine
from db_config import DatabaseConfig
from models import Doenca, Diagnostico, Or, And, AoMenos, Sintoma, Manifestacao, RegiaoComposta, RegiaoDoCorpo, Orgao, Exame, Resultado, Expressao, FatosSintomaResultado, AvaliaNode
from utils import StreamlitQueries
import streamlit as st


st.set_page_config(layout="wide", page_icon="🎲")
st.title("Cadastrar Dados")
sq = StreamlitQueries()


tab_names = ["Manifestação", "Orgão", "Região Composta", "Exame", "Resultado", "Sintoma", "Doença", "Or", "And", "Ao Menos", "Diagnóstico"]
tabs = {}
created_tabs = st.tabs(tab_names)


for tab_name, tab in zip(tab_names, created_tabs):
    tabs[tab_name] = tab


with tabs["Manifestação"]:
    manifestacoes = sq.get_all_manifestacoes()
    st.selectbox("Busque manifestações já existentes", options=manifestacoes, index=None, placeholder="Digite o nome de uma manifestação")
    text_input = st.text_input("Nome da nova Manifestação", placeholder="e.g.: Coceira, Irritação, Dor, Inchaço...")
    if st.button("Cadastrar", type="primary", key="manifestacao"):
        response = sq.add_manifestacao(text_input)
        if response == 'Created':
            st.success(f"Manifestação '{text_input}' cadastrada com sucesso!")
        else:
            st.warning(f"Manifestação '{text_input}' já existe!")



with tabs["Orgão"]:
    orgaos = sq.get_all_orgaos()
    st.selectbox("Busque órgãos já existentes", options=orgaos, index=None, placeholder="Digite o nome de um órgão")
    text_input = st.text_input("Nome do novo Órgão", placeholder="e.g.: Coração, Pulmão, Fígado...")
    if text_input:
        if st.button("Cadastrar", type="primary", key="orgao"):
            st.success(f"Órgão '{text_input}' cadastrado com sucesso!")


with tabs["Região Composta"]:
    regioes_compostas = sq.get_all_regioes_compostas()
    st.selectbox("Busque regiões compostas já existentes", options=regioes_compostas, index=None, placeholder="Digite o nome de uma região composta")
    text_input = st.text_input("Nome da nova Região Composta", placeholder="e.g.: Corpo, Abdome, Tórax...")
    if text_input:
        if st.button("Cadastrar", type="primary", key="regiao_composta"):
            st.success(f"Região Composta '{text_input}' cadastrada com sucesso!")


with tabs["Exame"]:
    exames = sq.get_all_exames()
    st.selectbox("Busque exames já existentes", options=exames, index=None, placeholder="Digite o nome de um exame")
    text_input = st.text_input("Nome do novo Exame", placeholder="e.g.: Hemograma, Raio-X, Tomografia...")
    if text_input:
        if st.button("Cadastrar", type="primary", key="exame"):
            st.success(f"Exame '{text_input}' cadastrado com sucesso!")


with tabs["Resultado"]:
    resultados = sq.get_all_resultados()
    st.selectbox("Busque resultados já existentes", options=resultados, index=None, placeholder="Digite o nome de um resultado")
    text_input = st.text_input("Nome do novo Resultado", placeholder="e.g.: Normal, Alterado, Positivo, Negativo...")
    if text_input:
        if st.button("Cadastrar", type="primary", key="resultado"):
            st.success(f"Resultado '{text_input}' cadastrado com sucesso!")


with tabs["Sintoma"]:
    sintomas = sq.get_all_sintomas()
    sintoma = st.selectbox("Busque Sintomas já existentes", options=sintomas, index=None, placeholder="Digite o nome de um Sintoma")
    col1, col2 = st.columns(2)
    with col1:
        manifestacao_input = st.text_input("Nome da Manifestação do novo Sintoma", placeholder="e.g.: Coceira, Irritação, Dor, Inchaço...")
    with col2:
        regiao_composta_input = st.text_input("Nome da Região Composta do novo Sintoma", placeholder="e.g.: Corpo, Abdome, Tórax...")
    if manifestacao_input and regiao_composta_input:
        if st.button("Cadastrar", type="primary", key="sintoma"):
            st.success(f"Sintoma '{manifestacao_input} no(a) {regiao_composta_input}' cadastrado com sucesso!")


with tabs["Doença"]:
    doencas = sq.get_all_doencas()
    doenca = st.selectbox("Busque Doenças já existentes", options=doencas, index=None, placeholder="Digite o nome de uma Doença")
    text_input = st.text_input("Nome da nova Doença", placeholder="e.g.: Familial Mediterranean Fever, Mevalonate Kinase Deficiency...")
    if text_input:
        if st.button("Cadastrar", type="primary", key="doenca"):
            st.success(f"Doença '{text_input}' cadastrada com sucesso!")


# with tabs["Or"]:
#     expressions = sq.get_all_expressions()
#     col1, col2 = st.columns(2)
#     with col1:
#         or_left_expr = st.selectbox("Busque expressões já existentes", options=expressions, index=None, placeholder="Digite um pedaço da expressão Or", key="or_left")
#     with col2:
#         or_right_expr = st.selectbox("Busque expressões já existentes", options=expressions, index=None, placeholder="Digite um pedaço da expressão Or", key="or_right")
#     if st.button("Cadastrar", type="primary", key="or"):
#         response = sq.add_or(or_left_expr, or_right_expr)
#         if response == 'Created':
#             st.success(f"Expressão: '{or_left_expr}' OR '{or_right_expr}' cadastrada com sucesso!")
#         else:
#             st.warning(f"Expressão: '{or_left_expr}' OR '{or_right_expr}' já existe!")