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
st.title("Listar Doencas de um Sintoma")


sq = StreamlitQueries()


# Obter todos os sintomas do banco de dados
sintomas = sq.get_all_sintomas()
st.write("Lista de todos os Sintomas:", sintomas)


# Create a dropdown option to select a specific symptom to search for diseases
sintoma = st.selectbox("Selecione o sintoma", sintomas)


# Listar as doenças associadas ao sintoma
diagnosticos = sq.get_diagnosticos_by_sintoma(sintoma)
doencas = [diagnostico.doenca for diagnostico in diagnosticos]
st.write(f"Doenças do Sintoma:", doencas)