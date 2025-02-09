import streamlit as st


with st.sidebar:
	st.page_link('main.py', label='Diagramas de Classe e Objeto', icon='📊')
	st.page_link('pages/page0.py', label='Listar Doencas de um Sintoma', icon='📝')
	st.page_link('pages/page1.py', label='Contador de Sintomas', icon='🔢')
	st.page_link('pages/page2.py', label='Filtrar Doencas por Sintomas', icon='🔬')
st.title("Diagramas de Classe e Objeto")


st.image("images/tcc_class_diagram.png", caption="Diagrama de Classe", use_container_width=True)
st.image("images/tcc_object_diagram.png", caption="Diagrama de Objeto", use_container_width=True)