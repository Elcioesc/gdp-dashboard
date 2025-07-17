import streamlit as st
from modules.kpis import exibir_kpis
from modules.confiabilidade import exibir_confiabilidade
from modules.planejamento import exibir_planejamento
from modules.gestao_operacional import exibir_gestao

# Configuração da página
st.set_page_config(
    page_title="Analysis AI - Manutenção Industrial",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Menu lateral
with st.sidebar:
    st.title("Menu")
    st.image("https://cdn-icons-png.flaticon.com/512/2693/2693876.png", width=50)
    opcao = st.radio(
        "Selecione o módulo:",
        ["📊 KPIs de Manutenção", 
         "🔧 Análise de Confiabilidade",
         "📘 Planejamento Estratégico",
         "👷 Gestão Operacional"],
        index=0
    )
    st.markdown("---")
    st.caption("Versão 1.0 | Engenharia de Confiabilidade")

# Roteamento principal
if opcao == "📊 KPIs de Manutenção":
    exibir_kpis()
elif opcao == "🔧 Análise de Confiabilidade":
    exibir_confiabilidade()
elif opcao == "📘 Planejamento Estratégico":
    exibir_planejamento()
elif opcao == "👷 Gestão Operacional":
    exibir_gestao()