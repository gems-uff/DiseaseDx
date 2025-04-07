import streamlit as st
from utils import StreamlitQueries


st.set_page_config(layout="wide")
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