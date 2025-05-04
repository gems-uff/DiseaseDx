import streamlit as st
from utils import StreamlitQueries


st.set_page_config(layout="wide", page_icon="🔢")
st.title("Contador de Sintomas de uma Doenca")


sq = StreamlitQueries()


# Obter todos os sintomas do banco de dados
sintomas = sq.get_all_sintomas()
st.write("Lista de todos os Sintomas:", sintomas)


# Criar um dataframe para exibir as informações de todas as doenças associadas a cada sintoma
st.write("Tabela de Doenças com Sintoma em comum:")
sq.st_write_sintoma_doencas_table()