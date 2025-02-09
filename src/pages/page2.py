import streamlit as st
from utils import StreamlitQueries


with st.sidebar:
	st.page_link('main.py', label='Diagramas de Classe e Objeto', icon='📊')
	st.page_link('pages/page0.py', label='Listar Doencas de um Sintoma', icon='📝')
	st.page_link('pages/page1.py', label='Contador de Sintomas', icon='🔢')
	st.page_link('pages/page2.py', label='Filtrar Doencas por Sintomas', icon='🔬')
st.title("Filtrar Doencas por Sintomas")


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
		format_func=lambda sintoma: f"{sintoma.manifestacao.name} no (a) {sintoma.regiao_do_corpo.name}" if sintoma.regiao_do_corpo else f"{sintoma.manifestacao.name}",
		placeholder="Selecione os sintomas presentes"
	)

	present_resultados = st.multiselect(
		"Selecione os resultados presentes", 
		resultados,
		format_func=lambda resultado: f"{resultado.name} do exame {resultado.exame}",
		placeholder="Selecione os resultados presentes"
	)

with col2:
	not_present_sintomas = st.multiselect(
		"Selecione os sintomas ausentes", 
		sintomas,
		format_func=lambda sintoma: f"{sintoma.manifestacao.name} no (a) {sintoma.regiao_do_corpo.name}" if sintoma.regiao_do_corpo else f"{sintoma.manifestacao.name}",
		placeholder="Selecione os sintomas ausentes"
	)

	not_present_resultados = st.multiselect(
		"Selecione os resultados ausentes", 
		resultados,
		format_func=lambda resultado: f"{resultado.name} do exame {resultado.exame}",
		placeholder="Selecione os resultados ausentes"
	)


# Listar as doenças associadas ao sintoma
diagnosticos = sq.get_diagnosticos_by_list_of_sintomas_and_resultados(present_sintomas, not_present_sintomas, present_resultados, not_present_resultados)
doencas = [diagnostico.doenca for diagnostico in diagnosticos]
st.write("Possiveis Doencas:", doencas)


# Criar um dataframe para exibir as informações de todas as doenças associadas a cada sintoma
sq.st_write_doenca_sintomas_resultados_table()