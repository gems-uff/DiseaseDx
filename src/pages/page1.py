from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload
from db_config import DatabaseConfig
from models import Doenca, Diagnostico, Or, And, AoMenos, Sintoma, Manifestacao, RegiaoComposta, RegiaoDoCorpo, Orgao, Exame, Resultado, Expressao
import streamlit as st
import pandas as pd
from utils import StreamlitQueries


with st.sidebar:
	st.page_link('main.py', label='Diagramas de Classe e Objeto', icon='📊')
	st.page_link('pages/page0.py', label='Listar Doencas de um Sintoma', icon='📝')
	st.page_link('pages/page1.py', label='Contador de Sintomas', icon='🔢')
	st.page_link('pages/page2.py', label='Filtrar Doencas por Sintomas', icon='🔬')
st.title("Contador de Sintomas de uma Doenca")


sq = StreamlitQueries()


# Obter todos os sintomas do banco de dados
sintomas = sq.get_all_sintomas()
st.write("Lista de todos os Sintomas:", sintomas)


# Criar um dataframe para exibir as informações de todas as doenças associadas a cada sintoma
st.write("Tabela de Doenças com Sintoma em comum:")
sq.st_write_sintoma_doencas_table()