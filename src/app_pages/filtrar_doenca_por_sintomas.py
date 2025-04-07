import streamlit as st
from utils import StreamlitQueries
from models import Sintoma


st.set_page_config(layout="wide")
st.title("Filtrar Doencas por Sintomas")


def format_func(item):
    if isinstance(item, Sintoma):
        return f"{item.manifestacao.name} no(a) {item.regiao_do_corpo.name}" if item.regiao_do_corpo else f"{item.manifestacao.name}"
    else:
        return f"{item.name} do exame {item.exame}"


sq = StreamlitQueries()


# Obter todos os sintomas do banco de dados
sintomas = sq.get_all_sintomas()
resultados = sq.get_all_resultados()


col1, col2 = st.columns(2)

# TODO: Descobrir como filtrar os itens dos multiselects baseados nas escolhas do outro 
# se um sintoma está presente, ele não pode ser escolhido como ausente e vice-versa (provavelmente usar o session.state do streamlit)
with col1:
	present_sintomas = st.multiselect(
		"Selecione os sintomas presentes", 
		sintomas,
		format_func=lambda sintoma: format_func(sintoma),
		placeholder="Selecione os sintomas presentes"
	)

	present_resultados = st.multiselect(
		"Selecione os resultados presentes", 
		resultados,
		format_func=lambda resultado: format_func(resultado),
		placeholder="Selecione os resultados presentes"
	)

with col2:
	not_present_sintomas = st.multiselect(
		"Selecione os sintomas ausentes", 
		sintomas,
		format_func=lambda sintoma: format_func(sintoma),
		placeholder="Selecione os sintomas ausentes"
	)

	not_present_resultados = st.multiselect(
		"Selecione os resultados ausentes", 
		resultados,
		format_func=lambda resultado: format_func(resultado),
		placeholder="Selecione os resultados ausentes"
	)


# Listar as doenças associadas ao sintoma
diagnosticos = sq.get_diagnosticos_by_list_of_sintomas_and_resultados(present_sintomas, not_present_sintomas, present_resultados, not_present_resultados)
doencas = [diagnostico.doenca for diagnostico in diagnosticos]
st.write("Possiveis Doencas:", doencas)


# Criar um dataframe para exibir as informações de todas as doenças associadas a cada sintoma
sq.st_write_doenca_sintomas_resultados_table()