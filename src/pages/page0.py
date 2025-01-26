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
st.title("Listar Doencas de um Sintoma")


sq = StreamlitQueries()


# Obter todos os sintomas do banco de dados
sintomas = sq.get_all_sintomas()
st.write("Lista de todos os Sintomas:", sintomas)


# Create a dropdown option to select a specific symptom to search for diseases
sintoma = st.selectbox(
    "Selecione o sintoma", 
	sintomas, 
	index=None, 
	format_func=lambda sintoma: f"{sintoma.manifestacao.name} no (a) {sintoma.regiao_do_corpo.name}" if sintoma.regiao_do_corpo else f"{sintoma.manifestacao.name}",
	placeholder="Selecione um sintoma"
)


# Listar as doenças associadas ao sintoma
if sintoma:
	diagnosticos = sq.get_diagnosticos_by_sintoma(sintoma)
	doencas = [diagnostico.doenca for diagnostico in diagnosticos]
	st.write(f"Doenças do Sintoma:", doencas)