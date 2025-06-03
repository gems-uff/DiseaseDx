import streamlit as st
from utils import StreamlitQueries
from models import Sintoma


st.set_page_config(layout="wide", page_icon="🩺")
st.title("Auxiliar no Diagnostico")


def format_func(item) -> str:
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


diagnosticos_avaliacoes = sq.get_diagnosticos_avaliacoes_by_list_of_sintomas_and_resultados(present_sintomas, not_present_sintomas, present_resultados, not_present_resultados)


if 'clicked' not in st.session_state:
    st.session_state.clicked = False


def click_button() -> None:
    st.session_state.clicked = not st.session_state.clicked


with col2:

	for doenca in diagnosticos_avaliacoes.keys():
		if diagnosticos_avaliacoes[doenca][0].result.value == True:
			st.success(doenca.name + " bate com os sintomas e resultados selecionados.")

	if st.session_state.clicked:
		st.button(f"Ocultar Árvores de Avaliação", on_click=click_button, key="exibir_arvore")
		st.write("Possiveis Doenças:")

		diagnosticos_ordered_by_score = sorted(diagnosticos_avaliacoes.keys(), key=lambda x: diagnosticos_avaliacoes[x][1], reverse=True)
		
		for doenca in diagnosticos_ordered_by_score:
			diagnostico = sq.get_diagnostico_by_doenca(doenca)
			if diagnostico.paper_link:
				st.html(f'<span style="color:#1f77b4;"><a href="{diagnostico.paper_link}" target="_blank">{doenca.name}</a> | Score = {diagnosticos_avaliacoes[doenca][1]}</span>')
			else:
				st.html(f'<span style="color:#1f77b4;">{doenca.name} | Score = {diagnosticos_avaliacoes[doenca][1]}</span>')
			st.html(diagnosticos_avaliacoes[doenca][0].build_html_string())
			
	else:
		st.button(f"Exibir Árvores de Avaliação", on_click=click_button, key="exibir_arvore")


with col1:

	most_common_sintoma = sq.get_most_common_sintoma(sintomas, present_sintomas, not_present_sintomas)
	st.write("Sintoma mais comum:", most_common_sintoma)

	most_common_resultado = sq.get_most_common_resultado(resultados, present_resultados, not_present_resultados)
	st.write("Resultado mais comum:", most_common_resultado)
	
	df_sintoma_doencas = sq.st_write_sintoma_doencas_table()
	st.dataframe(df_sintoma_doencas)

	df_resultado_doencas = sq.st_write_resultado_doencas_table()
	st.dataframe(df_resultado_doencas)