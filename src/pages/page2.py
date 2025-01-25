from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload
from db_config import DatabaseConfig
from models import Doenca, Diagnostico, Or, And, AoMenos, Sintoma, Manifestacao, RegiaoComposta, RegiaoDoCorpo, Orgao, Exame, Resultado, Expressao
import streamlit as st
import pandas as pd
from utils import StreamlitQueries


with st.sidebar:
        st.page_link('main.py', label='Listar Doencas de um Sintoma', icon='📝')
        st.page_link('pages/page1.py', label='Contador de Sintomas', icon='🔢')
        st.page_link('pages/page2.py', label='Filtrar Doencas por Sintomas', icon='🔬')
st.title("Filtrar Doencas por Sintomas")


sq = StreamlitQueries()


# Obter todos os sintomas do banco de dados
sintomas = sq.get_all_sintomas()
st.write("Lista de todos os Sintomas:", sintomas)


# TODO: Descobrir como filtrar os itens dos multiselects baseados nas escolhas do outro (se um sintoma está presente, ele não pode ser escolhido como ausente e vice-versa)
present_sintomas = st.multiselect("Selecione os sintomas presentes", sintomas)
not_present_sintomas = st.multiselect("Selecione os sintomas ausentes", sintomas)


# Listar as doenças associadas ao sintoma
diagnosticos = sq.get_diagnosticos_by_list_of_sintomas(present_sintomas, not_present_sintomas)
doencas = [diagnostico.doenca for diagnostico in diagnosticos]
st.write("Possiveis Doencas:", doencas)

# Criar um dataframe para exibir as informações de todas as doenças associadas a cada sintoma
sq.st_write_doenca_sintomas_table()