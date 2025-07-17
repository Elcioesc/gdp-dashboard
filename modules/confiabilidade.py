# modules/confiabilidade.py

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from lifelines import WeibullFitter

def exibir_confiabilidade():
    st.title("🔬 Análise de Confiabilidade")
    
    arquivo = st.file_uploader(
        "📊 Dados de Falhas", 
        type=["xlsx"],
        key="confiabilidade_upload"
    )
    
    if arquivo:
        try:
            df = pd.read_excel(arquivo)
            
            # Verificação e tratamento dos dados
            if 'Tempo entre falhas (h)' not in df.columns:
                raise ValueError("Coluna 'Tempo entre falhas (h)' não encontrada. Verifique o nome da coluna.")
                
            tempos = df['Tempo entre falhas (h)'].dropna().values
            
            if len(tempos) < 2:
                raise ValueError("Número insuficiente de dados (mínimo 2 registros) para realizar a análise de confiabilidade.")
                
            # Ajuste Weibull
            wf = WeibullFitter()
            wf.fit(tempos)
            
            # Preparação dos dados para o gráfico
            # Garante que x_values não seja vazio e tenha um range razoável
            if max(tempos) == 0: # Evita divisão por zero ou range inadequado
                x_values = np.linspace(0, 100, 200) # Define um range padrão se todos os tempos forem zero
            else:
                x_values = np.linspace(0, max(tempos) * 1.2, 200)
            
            y_values = 1 - wf.predict(x_values)
            
            # Criação do gráfico
            fig = px.line(
                x=x_values,
                y=y_values,
                title="Curva de Confiabilidade Weibull (R(t))",
                labels={'x': 'Tempo (horas)', 'y': 'Confiabilidade R(t)'}
            )
            fig.update_layout(xaxis_title="Tempo (horas)", yaxis_title="Confiabilidade R(t)")
            st.plotly_chart(fig, use_container_width=True)
            
            # Exibição dos parâmetros
            beta = wf.rho_
            eta = wf.lambda_
            
            col1, col2 = st.columns(2)
            col1.metric("β (Forma)", f"{beta:.2f}")
            col2.metric("η (Vida Característica)", f"{eta:.2f} horas")
            
            # Interpretação dos parâmetros
            st.subheader("Interpretação do Parâmetro β (Forma)")
            if beta < 1:
                st.info("🟢 **β < 1 (Falhas Infantis):** A taxa de falha está diminuindo com o tempo. Isso é comum no início da vida de um componente e pode ser devido a defeitos de fabricação ou instalação inadequada. Ações focadas em **inspeção inicial rigorosa** e **período de amadurecimento (burn-in)** podem ser úteis.")
            elif 0.9 <= beta <= 1.1: # Usando uma pequena margem para "aproximadamente 1"
                st.info("🟡 **β ≈ 1 (Falhas Aleatórias):** A taxa de falha é aproximadamente constante ao longo do tempo. Isso geralmente indica falhas súbitas e imprevisíveis, não relacionadas ao desgaste. Ações de **manutenção preventiva baseada em tempo** ou **condição** podem não ser eficazes; a **manutenção corretiva** e o **monitoramento** são mais relevantes.")
            else: # beta > 1.1
                st.warning("🔴 **β > 1 (Desgaste):** A taxa de falha está aumentando com o tempo. Isso é típico de componentes que estão se desgastando. Ações de **manutenção preventiva baseada em tempo (substituições programadas)** ou **manutenção preditiva (monitoramento de condição)** são altamente recomendadas para evitar falhas catastróficas.")
                
            st.markdown("---")
            st.subheader("O que é η (Vida Característica)?")
            st.info(f"O parâmetro **η (Eta)**, ou Vida Característica ({eta:.2f} horas), é o tempo no qual aproximadamente **63.2%** dos itens de uma população falharam. É um indicador importante da 'vida útil' do componente sob análise.")


        except ValueError as ve:
            st.error(f"Erro nos dados: {str(ve)}")
            st.info("Por favor, verifique se seu arquivo Excel possui a coluna 'Tempo entre falhas (h)' e se os dados são numéricos e suficientes.")
        except Exception as e:
            st.error(f"Ocorreu um erro inesperado: {str(e)}")
            st.info("Certifique-se de que o arquivo Excel está formatado corretamente e tente novamente.")