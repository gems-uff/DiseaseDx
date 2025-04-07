import streamlit as st
from utils import StreamlitQueries
from models import Sintoma


st.set_page_config(layout="wide")
st.title("Auxiliar no Diagnostico")


def format_func(item):
    if isinstance(item, Sintoma):
        return f"{item.manifestacao.name} no(a) {item.regiao_do_corpo.name}" if item.regiao_do_corpo else f"{item.manifestacao.name}"
    else:
        return f"{item.name} do exame {item.exame}"


sq = StreamlitQueries()


sintomas = sq.get_all_sintomas()
resultados = sq.get_all_resultados()


col1, col2 = st.columns(2)


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


diagnosticos = sq.get_diagnosticos_by_list_of_sintomas_and_resultados(present_sintomas, not_present_sintomas, present_resultados, not_present_resultados)
possiveis_doencas = [diagnostico.doenca for diagnostico in diagnosticos]
st.write("Possíveis Doenças:", possiveis_doencas)


sintomas_of_possiveis_doencas = []
for doenca in possiveis_doencas:
	for sintoma in sq.get_sintomas_by_doenca(doenca):
		if sintoma not in sintomas_of_possiveis_doencas and sintoma not in not_present_sintomas:
			sintomas_of_possiveis_doencas.append(sintoma)

resultados_of_possiveis_doencas = []
for doenca in possiveis_doencas:
	for resultado in sq.get_resultados_by_doenca(doenca):
		if resultado not in resultados_of_possiveis_doencas and resultado not in not_present_resultados:
			resultados_of_possiveis_doencas.append(resultado)


most_common_sintoma = sq.get_most_common_sintoma(sintomas_of_possiveis_doencas, present_sintomas, not_present_sintomas)
st.write("Sintoma mais comum:", most_common_sintoma)

most_common_resultado = sq.get_most_common_resultado(resultados_of_possiveis_doencas, present_resultados, not_present_resultados)
st.write("Resultado mais comum:", most_common_resultado)


sq.st_write_sintoma_doencas_table()