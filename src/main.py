import streamlit as st


diagrams = st.Page("app_pages/diagrams.py", title="Diagramas de Classe e Objeto", icon="📊")
listar_doencas_do_sintoma = st.Page("app_pages/listar_doencas_do_sintoma.py", title="Listar Doencas de um Sintoma", icon="📝")
contador_de_sintomas = st.Page("app_pages/contador_de_sintomas.py", title="Contador de Sintomas", icon="🔢")
filtrar_doenca_por_sintomas = st.Page("app_pages/filtrar_doenca_por_sintomas.py", title="Filtrar Doencas por Sintomas", icon="🔬")
auxiliar_no_diagnostico = st.Page("app_pages/auxiliar_no_diagnostico.py", title="Auxiliar no Diagnostico", icon="🩺")


pg = st.navigation(
	[
		diagrams,
		listar_doencas_do_sintoma, 
		contador_de_sintomas, 
		filtrar_doenca_por_sintomas, 
		auxiliar_no_diagnostico
	]
)


pg.run()