# modules/kpis.py

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime
from sklearn.ensemble import IsolationForest
from fpdf import FPDF
import base64
from io import BytesIO
import warnings

# Adicione esta função no início do código (após os imports)
def carregar_banco_conhecimento():
    """Carrega o banco de conhecimento de falhas, causas e soluções"""
    try:
        # Carrega de um arquivo Excel específico
        # Assumindo que 'banco_conhecimento.xlsx' está no mesmo diretório ou caminho acessível
        df_conhecimento = pd.read_excel("banco_conhecimento.xlsx", sheet_name="Falhas")
        
        # Padroniza os dados
        df_conhecimento['TipoFalha'] = df_conhecimento['TipoFalha'].str.lower().str.strip()
        df_conhecimento['Causa'] = df_conhecimento['Causa'].str.lower().str.strip()
        df_conhecimento['AcaoRecomendada'] = df_conhecimento['AcaoRecomendada'].astype(str)
        
        return df_conhecimento
    except FileNotFoundError:
        st.warning("Arquivo 'banco_conhecimento.xlsx' não encontrado. As recomendações serão genéricas.")
        return pd.DataFrame(columns=['TipoFalha', 'Causa', 'AcaoRecomendada'])
    except Exception as e:
        st.warning(f"Não foi possível carregar o banco de conhecimento: {str(e)}")
        return pd.DataFrame(columns=['TipoFalha', 'Causa', 'AcaoRecomendada'])

# Modifique a função gerar_recomendacao para:
def gerar_recomendacao(causa, df_conhecimento):
    """Gera recomendações baseadas no banco de conhecimento"""
    causa = str(causa).lower().strip()
    
    # Busca no banco de conhecimento
    if not df_conhecimento.empty and 'Causa' in df_conhecimento.columns:
        recomendacoes = df_conhecimento[df_conhecimento['Causa'].str.contains(causa, case=False, na=False)]
        
        if not recomendacoes.empty:
            # Retorna as 3 melhores recomendações
            return "\n".join([f"• {rec}" for rec in recomendacoes['AcaoRecomendada'].head(3).tolist()])
    
    # Padrões genéricos se não encontrar no banco ou se o banco não for carregado
    padroes = {
        "desgaste": "Implementar programa de lubrificação preventiva e inspeção periódica",
        "vazamento": "Substituição programada de selos e juntas conforme vida útil",
        "elétric": "Realizar termografia periódica e análise de vibração",
        "hidráulic": "Monitoramento contínuo de pressão e vazão",
        "corrosão": "Aplicação de proteção superficial e controle ambiental",
        "sobreaquecimento": "Verificação do sistema de refrigeração e limpeza de radiadores",
        "alinhamento": "Realizar alinhamento a laser trimestral",
        "contaminaç": "Melhorar filtragem e controle de qualidade dos fluidos"
    }
    
    for palavra_chave, acao in padroes.items():
        if palavra_chave in causa:
            return acao
    
    return "Realizar análise de causa raiz com a equipe técnica"

warnings.filterwarnings('ignore')

class PDFReport(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Relatório de Análise de Manutenção', 0, 1, 'C')
        self.ln(5)
    
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

def create_download_link(val, filename):
    b64 = base64.b64encode(val)
    return f'<a href="data:application/octet-stream;base64,{b64.decode()}" download="{filename}">Download Relatório PDF</a>'

def generate_pdf_report(df_falhas_filtrado, top_equipments, timeline_data, kpis_hierarquia, df_conhecimento):
    pdf = PDFReport()
    # Adicionando fonte que suporte caracteres UTF-8
    pdf.add_font('DejaVu', '', 'DejaVuSansCondensed.ttf', uni=True)
    pdf.add_font('DejaVu', 'B', 'DejaVuSansCondensed-Bold.ttf', uni=True)
    
    pdf.add_page()
    pdf.set_font('DejaVu', 'B', 16)
    pdf.cell(0, 10, 'Relatório de Análise de Manutenção', 0, 1, 'C')
    pdf.ln(10)
    
    if not top_equipments.empty:
        # Top 10 Equipamentos Críticos
        pdf.set_font('DejaVu', 'B', 14)
        pdf.cell(0, 10, 'Top 10 Equipamentos Críticos', 0, 1)
        pdf.ln(5)
        
        pdf.set_font('DejaVu', '', 10)
        # Ajusta largura das colunas para nomes de colunas na planilha
        col_widths = [30, 25, 25, 25, 25, 25] 
        headers = ['Equipamento', 'Frota', 'Tempo Total (h)', 'Ocorrências', 'Sistema', 'Conjunto']
        
        for i, header in enumerate(headers):
            pdf.cell(col_widths[i], 10, header, 1, 0, 'C')
        pdf.ln()
        
        for _, row in top_equipments.iterrows():
            pdf.cell(col_widths[0], 10, str(row['EQUIPAMENTO']), 1)
            pdf.cell(col_widths[1], 10, str(row['FROTA']), 1)
            pdf.cell(col_widths[2], 10, f"{row['Tempo Total (h)']:.1f}", 1, 0, 'C')
            pdf.cell(col_widths[3], 10, str(row['Ocorrências']), 1, 0, 'C')
            pdf.cell(col_widths[4], 10, str(row['SISTEMA']), 1)
            pdf.cell(col_widths[5], 10, str(row['CONJUNTO']), 1)
            pdf.ln()
    
    # KPIs Hierárquicos
    pdf.add_page()
    pdf.set_font('DejaVu', 'B', 14)
    pdf.cell(0, 10, 'Análise Hierárquica de Falhas', 0, 1, 'C')
    pdf.ln(5)
    
    for nivel, df_kpi in kpis_hierarquia.items():
        if not df_kpi.empty:
            pdf.set_font('DejaVu', 'B', 12)
            pdf.cell(0, 10, f'Nível: {nivel}', 0, 1)
            pdf.ln(3)
            
            pdf.set_font('DejaVu', '', 10)
            col_widths = [50, 25, 25, 25, 25]
            headers = [nivel, 'Tempo Total (h)', 'MTTR (h)', 'Ocorrências', 'Equip. Afetados']
            
            for i, header in enumerate(headers):
                pdf.cell(col_widths[i], 10, header, 1, 0, 'C')
            pdf.ln()
            
            for _, row in df_kpi.iterrows():
                pdf.cell(col_widths[0], 10, str(row.name), 1)
                pdf.cell(col_widths[1], 10, f"{row['Tempo Total (h)']:.1f}", 1, 0, 'C')
                pdf.cell(col_widths[2], 10, f"{row['MTTR (h)']:.1f}", 1, 0, 'C')
                pdf.cell(col_widths[3], 10, str(row['Ocorrências']), 1, 0, 'C')
                pdf.cell(col_widths[4], 10, str(row['Equip. Afetados']), 1, 0, 'C')
                pdf.ln()
            pdf.ln(10)
    
    # Linha do Tempo de Falhas
    pdf.add_page()
    pdf.set_font('DejaVu', 'B', 14)
    pdf.cell(0, 10, 'Linha do Tempo das Falhas Mais Impactantes', 0, 1, 'C')
    pdf.ln(5)
    
    if not timeline_data.empty:
        pdf.set_font('DejaVu', '', 10)
        for _, event in timeline_data.iterrows():
            pdf.set_fill_color(200, 220, 255)
            pdf.cell(0, 10, f"{event['DATA INICIAL'].strftime('%d/%m/%Y')} - {event['EQUIPAMENTO']}", 1, 1, 'L', 1)
            pdf.cell(0, 8, f"Sistema: {event['SISTEMA']} > Conjunto: {event['CONJUNTO']} > Item: {event['ITEM']}", 0, 1)
            pdf.cell(0, 8, f"Falha: {event['CAUSA']}", 0, 1)
            pdf.cell(0, 8, f"Duração: {event['DURAÇÃO']} horas | Impacto: {event['Impacto']}", 0, 1)
            pdf.ln(3)
    
    # Recomendações
    pdf.add_page()
    pdf.set_font('DejaVu', 'B', 14)
    pdf.cell(0, 10, 'Recomendações Prioritárias', 0, 1, 'C')
    pdf.ln(5)
    
    if not timeline_data.empty:
        causas = timeline_data['CAUSA'].value_counts().nlargest(5)
        for i, (causa, _) in enumerate(causas.items(), 1):
            pdf.set_font('DejaVu', 'B', 12)
            pdf.cell(0, 10, f"{i}. {causa}", 0, 1)
            pdf.set_font('DejaVu', '', 10)
            # Passa df_conhecimento para a função gerar_recomendacao
            pdf.multi_cell(0, 8, gerar_recomendacao(causa, df_conhecimento)) 
            pdf.ln(3)
    
    return pdf.output(dest='S').encode('utf-8') # Alterado para utf-8

def clean_duration(value):
    """Converte valores de duração para float de forma segura"""
    try:
        if pd.isna(value):
            return np.nan
        if isinstance(value, str):
            value = value.replace(',', '.').strip()
            if 'h' in value.lower():
                value = value.lower().split('h')[0]
        return float(value)
    except:
        return np.nan

def clean_and_convert_column(series):
    """Limpa e converte uma coluna para string consistente"""
    return series.astype(str).str.strip()

def exibir_kpis():
    st.title("📊 Análise Completa de KPIs de Manutenção")
    
    arquivo = st.file_uploader(
        "📁 Upload do histórico de manutenção (planilhas 'Falhas' e 'Indicadores' no mesmo arquivo .xlsx)", 
        type=["xlsx"]
    )
    
    if not arquivo:
        st.info("Por favor, faça upload do arquivo Excel para análise")
        return

    # Tela de carregamento
    with st.spinner("Realizando análise de dados... Isso pode levar alguns segundos."):
        try:
            df_conhecimento = carregar_banco_conhecimento()

            # --- Carregamento das duas planilhas ---
            # Tenta carregar a planilha 'Falhas'
            try:
                df_falhas = pd.read_excel(arquivo, sheet_name='Falhas')
            except ValueError:
                st.error("A planilha 'Falhas' não foi encontrada no arquivo Excel. Por favor, verifique o nome da aba.")
                return

            # Tenta carregar a planilha 'Indicadores'
            try:
                df_indicadores = pd.read_excel(arquivo, sheet_name='Indicadores')
            except ValueError:
                st.error("A planilha 'Indicadores' não foi encontrada no arquivo Excel. Por favor, verifique o nome da aba.")
                return
                
            # --- Processamento de df_falhas ---
            
            # Verificação de colunas obrigatórias para Falhas
            required_cols_falhas = ['EQUIPAMENTO', 'FROTA', 'SISTEMA', 'CONJUNTO', 'ITEM', 
                                    'DATA INICIAL', 'DATA FINAL', 'DURAÇÃO', 'CAUSA']
            missing_cols_falhas = [col for col in required_cols_falhas if col not in df_falhas.columns]
            if missing_cols_falhas:
                st.error(f"Colunas obrigatórias faltando na planilha 'Falhas': {', '.join(missing_cols_falhas)}")
                return

            # Conversão segura de tipos para Falhas
            df_falhas['DATA INICIAL'] = pd.to_datetime(df_falhas['DATA INICIAL'], errors='coerce')
            df_falhas['DATA FINAL'] = pd.to_datetime(df_falhas['DATA FINAL'], errors='coerce')
            df_falhas['DURAÇÃO'] = df_falhas['DURAÇÃO'].apply(clean_duration)
            
            # Limpeza das colunas de texto para Falhas
            text_cols_falhas = ['SISTEMA', 'CONJUNTO', 'ITEM', 'CAUSA', 'EQUIPAMENTO', 'FROTA']
            for col in text_cols_falhas:
                df_falhas[col] = clean_and_convert_column(df_falhas[col])
            
            # Remoção de registros inválidos em Falhas
            original_count_falhas = len(df_falhas)
            df_falhas = df_falhas.dropna(subset=['DATA INICIAL', 'DATA FINAL', 'DURAÇÃO'])
            if len(df_falhas) < original_count_falhas:
                st.warning(f"Removidos {original_count_falhas - len(df_falhas)} registros inválidos da planilha 'Falhas'.")
            
            if len(df_falhas) == 0:
                st.error("Nenhum dado válido encontrado na planilha 'Falhas' após a limpeza.")
                return

            # --- Processamento de df_indicadores (NOVO) ---
            
            # Padroniza nomes das colunas de df_indicadores para facilitar o acesso
            df_indicadores.columns = df_indicadores.columns.str.upper().str.replace(' ', '_').str.replace('%', '_PERCENT').str.strip()
            
            # Verificação de colunas obrigatórias para Indicadores
            required_cols_indicadores = ['EQUIPAMENTO', 'FROTA', 'DATA_INICIAL', 'DATA_FINAL', 
                                        'DISPONIBILIDADE_FISICA', 'MTBF', 'MTTR', 'OEE', 'PRODUTIVIDADE']
            # CORREÇÃO: Removido o 'col' duplicado aqui
            missing_cols_indicadores = [col for col in required_cols_indicadores if col not in df_indicadores.columns]
            if missing_cols_indicadores:
                st.warning(f"Algumas colunas esperadas na planilha 'Indicadores' não foram encontradas: {', '.join(missing_cols_indicadores)}. Certas análises podem estar incompletas.")
                
            # Verifica colunas críticas para correlação
            if 'EQUIPAMENTO' not in df_indicadores.columns or 'FROTA' not in df_indicadores.columns:
                 st.error("Colunas 'EQUIPAMENTO' e/ou 'FROTA' ausentes na planilha 'Indicadores'. Não é possível correlacionar os dados.")
                 return

            # Conversão segura de tipos para Indicadores
            if 'DATA_INICIAL' in df_indicadores.columns:
                df_indicadores['DATA_INICIAL'] = pd.to_datetime(df_indicadores['DATA_INICIAL'], errors='coerce')
            if 'DATA_FINAL' in df_indicadores.columns:
                df_indicadores['DATA_FINAL'] = pd.to_datetime(df_indicadores['DATA_FINAL'], errors='coerce')

            numeric_cols_indicadores = [
                'HORAS_CALENDARIO', 'HORAS_DE_MANUTENCAO', 'HORA_DE_MANUTENÇÃO_CORRETIVA', 'HORA_ACIDENTE', 
                'HORA_DE_MANUTENÇÃO_PREVENTIVA', 'HORA_DE_MANUTENÇÃO_PREVENTIVA_SISTEMÁTICA', 
                'HORA_DE_MANUTENÇÃO_PREVENTIVA_NÃO_SISTEMÁTICA', 'HORAS_DISPONIVÉIS', 'HORA_OCIOSA', 
                'HORA_OCIOSA_INTERNA', 'HORA_OCIOSA_EXTERNA', 'HORA_TRABALHADA', 'HORA_TRABALHADA_PRODUTIVA', 
                'HORA_EFETIVA', 'HORA_DE_ATRASO_OPERACIONAL', 'HORA_TRABALHADA_NÃO_PRODUTIVA', 
                'HORA_TRABALHADA_DE_INFRA', 'HORA_TRABALHADA_DIVERSA', 
                'DISPONIBILIDADE_FISICA', 'UTILIZACAO_FISICA', 'RENDIMENTO_OPERACIONAL', 'DI_PERCENT', 'EP', 'OEE',
                'NUMERO_DE_INTERVEÇÕES_CORRETIVAS', 'IAO', 'TON_HE', 'MTBF', 'MTTR', 'MTBS', 'MTTS', 'NIM', 'FMP',
                'PRODUÇÃO', 'PRODUTIVIDADE', 'PERCENT_IMPACTO_NO_PAI'
            ]
            for col in numeric_cols_indicadores:
                if col in df_indicadores.columns:
                    df_indicadores[col] = pd.to_numeric(df_indicadores[col], errors='coerce')
            
            # Limpeza das colunas de texto para Indicadores
            text_cols_indicadores = ['DIRETORIA', 'COMPLEXO', 'UNIDADE', 'FASE_PRODUTIVA', 'SISTEMA_PRODUTIVO', 
                                     'SUBPROCESSO', 'LINHA', 'CATEGORIA', 'GRUPO_DE_EQUIPAMENTOS', 'FAMÍLIA', 
                                     'CLASSE', 'PORTE', 'FROTA', 'ROTA', 'EQUIPAMENTO', 'ATIVIDADE', 'STATUS']
            for col in text_cols_indicadores:
                if col in df_indicadores.columns:
                    df_indicadores[col] = clean_and_convert_column(df_indicadores[col])
            
            # --- Filtros laterais ---
            with st.sidebar:
                st.header("🔍 Filtros")
                
                # Garante que as datas mínimas e máximas sejam válidas
                min_date_falhas = df_falhas['DATA INICIAL'].min().date() if not pd.isna(df_falhas['DATA INICIAL'].min()) else datetime.now().date()
                max_date_falhas = df_falhas['DATA INICIAL'].max().date() if not pd.isna(df_falhas['DATA INICIAL'].max()) else datetime.now().date()
                
                # Use as datas da planilha de falhas como referência para o filtro de período principal
                date_range = st.date_input("Período", [min_date_falhas, max_date_falhas])
                
                # Filtro de Frotas
                frotas_all = ["Todas"] + sorted(list(df_falhas['FROTA'].unique()))
                frota_selecionada = st.multiselect("Frotas", frotas_all, default=["Todas"])
                
                # Filtro de Equipamentos (Correlacionado com Frota)
                equipamentos_disponiveis = []
                if "Todas" in frota_selecionada:
                    equipamentos_disponiveis = ["Todos"] + sorted(list(df_falhas['EQUIPAMENTO'].unique()))
                elif frota_selecionada:
                    df_temp_equip = df_falhas[df_falhas['FROTA'].isin(frota_selecionada)]
                    equipamentos_disponiveis = ["Todos"] + sorted(list(df_temp_equip['EQUIPAMENTO'].unique()))
                
                equipamento_selecionado = st.multiselect("Equipamentos", equipamentos_disponiveis, default=["Todos"])
                
                # Filtro de Sistemas
                sistemas_all = ["Todos"] + sorted(list(df_falhas['SISTEMA'].unique()))
                sistemas_selecionados = st.multiselect("Sistemas", sistemas_all, default=["Todos"])

                # Filtro de Conjuntos para Pareto e Confiabilidade de Componentes
                conjuntos_all = ["Todos"] + sorted(list(df_falhas['CONJUNTO'].unique()))
                conjunto_selecionado = st.multiselect("Conjuntos", conjuntos_all, default=["Todos"])

                # Filtro de Itens para Confiabilidade de Componentes
                itens_all = ["Todos"] + sorted(list(df_falhas['ITEM'].unique()))
                item_selecionado = st.multiselect("Itens", itens_all, default=["Todos"])


            # --- Aplicação dos filtros aos DataFrames ---
            df_falhas_filtrado = df_falhas.copy()
            df_indicadores_filtrado = df_indicadores.copy() # Copia para filtrar tbm

            if len(date_range) == 2:
                start_date = pd.Timestamp(date_range[0])
                end_date = pd.Timestamp(date_range[1])
                
                df_falhas_filtrado = df_falhas_filtrado[
                    (df_falhas_filtrado['DATA INICIAL'] >= start_date) &
                    (df_falhas_filtrado['DATA INICIAL'] <= end_date)
                ]
                
                # Filtra indicadores pela DATA_FINAL dentro do range
                if 'DATA_FINAL' in df_indicadores_filtrado.columns:
                    df_indicadores_filtrado = df_indicadores_filtrado[
                        (df_indicadores_filtrado['DATA_FINAL'] >= start_date) &
                        (df_indicadores_filtrado['DATA_FINAL'] <= end_date)
                    ]
            
            if "Todas" not in frota_selecionada and frota_selecionada:
                df_falhas_filtrado = df_falhas_filtrado[df_falhas_filtrado['FROTA'].isin(frota_selecionada)]
                df_indicadores_filtrado = df_indicadores_filtrado[df_indicadores_filtrado['FROTA'].isin(frota_selecionada)]
            
            if "Todos" not in equipamento_selecionado and equipamento_selecionado:
                df_falhas_filtrado = df_falhas_filtrado[df_falhas_filtrado['EQUIPAMENTO'].isin(equipamento_selecionado)]
                df_indicadores_filtrado = df_indicadores_filtrado[df_indicadores_filtrado['EQUIPAMENTO'].isin(equipamento_selecionado)]

            if "Todos" not in sistemas_selecionados and sistemas_selecionados:
                df_falhas_filtrado = df_falhas_filtrado[df_falhas_filtrado['SISTEMA'].isin(sistemas_selecionados)]
                # Note: df_indicadores_filtrado não possui 'SISTEMA' padronizado como 'SISTEMA'. Se houver, adicione aqui.
                # Se for 'SISTEMA_PRODUTIVO' use:
                if 'SISTEMA_PRODUTIVO' in df_indicadores_filtrado.columns:
                    df_indicadores_filtrado = df_indicadores_filtrado[df_indicadores_filtrado['SISTEMA_PRODUTIVO'].isin(sistemas_selecionados)]
            
            if "Todos" not in conjunto_selecionado and conjunto_selecionado:
                df_falhas_filtrado = df_falhas_filtrado[df_falhas_filtrado['CONJUNTO'].isin(conjunto_selecionado)]

            if "Todos" not in item_selecionado and item_selecionado:
                df_falhas_filtrado = df_falhas_filtrado[df_falhas_filtrado['ITEM'].isin(item_selecionado)]


            if len(df_falhas_filtrado) == 0:
                st.warning("Nenhum dado de falhas encontrado com os filtros aplicados.")
                return
            
            # --- Agrega indicadores (pega o último registro por equipamento dentro do período) ---
            # Para pegar o último valor acumulado por equipamento dentro do período filtrado.
            df_indicadores_agregados = pd.DataFrame()
            if 'DATA_FINAL' in df_indicadores_filtrado.columns:
                df_indicadores_agregados = df_indicadores_filtrado.sort_values('DATA_FINAL').groupby(['EQUIPAMENTO', 'FROTA']).last().reset_index()
            elif not df_indicadores_filtrado.empty:
                # Se não há coluna de data_final para agregar, usa a última entrada por equipamento/frota (menos ideal, mas tenta continuar)
                df_indicadores_agregados = df_indicadores_filtrado.groupby(['EQUIPAMENTO', 'FROTA']).last().reset_index()
            
            if len(df_indicadores_agregados) == 0:
                st.warning("Nenhum dado de indicadores encontrado com os filtros aplicados. Algumas análises podem estar incompletas.")

            # --- Análise Hierárquica ---
            st.header("🔎 Análise Hierárquica de Falhas")
            
            nivel_analise = st.radio(
                "Nível de Análise",
                ["Sistema", "Conjunto", "Item"],
                horizontal=True,
                key="nivel_analise_kpi"
            )
            
            grupo = {'Sistema': 'SISTEMA', 'Conjunto': 'CONJUNTO', 'Item': 'ITEM'}[nivel_analise]
            
            # Cálculo de KPIs com verificação de dados
            try:
                kpis = df_falhas_filtrado.groupby(grupo).agg({
                    'DURAÇÃO': ['mean', 'sum', 'count'],
                    'EQUIPAMENTO': 'nunique' # Usa EQUIPAMENTO da planilha de Falhas
                }).sort_values(('DURAÇÃO', 'sum'), ascending=False)
                
                kpis.columns = ['MTTR (h)', 'Tempo Total (h)', 'Ocorrências', 'Equip. Afetados']
                
                # Exibição dos resultados
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    st.subheader(f"KPIs por {nivel_analise}")
                    st.dataframe(
                        kpis.style.format({
                            'MTTR (h)': '{:.1f}',
                            'Tempo Total (h)': '{:.1f}'
                        }).background_gradient(cmap='Reds'),
                        height=400
                    )
                
                with col2:
                    st.subheader(f"Distribuição por {nivel_analise}")
                    fig = px.pie(
                        kpis.reset_index(),
                        names=grupo,
                        values='Tempo Total (h)',
                        hover_data=['Ocorrências']
                    )
                    st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error(f"Erro na análise hierárquica: {str(e)}")

            # --- Análise de Pareto de Componentes/Itens ---
            st.header("📈 Análise de Pareto de Componentes/Itens")

            pareto_nivel = st.radio(
                "Nível de Pareto",
                ["Item", "Conjunto"],
                horizontal=True,
                key="pareto_nivel"
            )
            pareto_group_col = {'Item': 'ITEM', 'Conjunto': 'CONJUNTO'}[pareto_nivel]

            if not df_falhas_filtrado.empty:
                df_pareto = df_falhas_filtrado.groupby(pareto_group_col)['DURAÇÃO'].sum().sort_values(ascending=False).reset_index()
                df_pareto.columns = [pareto_group_col, 'Tempo Total Parada (h)']
                df_pareto['Porcentagem Cumulativa (%)'] = (df_pareto['Tempo Total Parada (h)'].cumsum() / df_pareto['Tempo Total Parada (h)'].sum()) * 100

                fig_pareto = px.bar(
                    df_pareto,
                    x=pareto_group_col,
                    y='Tempo Total Parada (h)',
                    title=f'Análise de Pareto por {pareto_nivel} (Tempo de Parada)',
                    text_auto=True # Mostra o valor no topo das barras
                )
                fig_pareto.add_scatter(
                    x=df_pareto[pareto_group_col],
                    y=df_pareto['Porcentagem Cumulativa (%)'],
                    mode='lines+markers',
                    name='Cumulativo (%)',
                    yaxis='y2' # Usa um segundo eixo Y
                )
                fig_pareto.update_layout(yaxis2=dict(
                    title='Porcentagem Cumulativa (%)',
                    overlaying='y',
                    side='right',
                    range=[0,100]
                ))
                st.plotly_chart(fig_pareto, use_container_width=True)
            else:
                st.info("Nenhum dado para análise de Pareto.")


            # --- Análise de Confiabilidade Básica de Componentes ---
            st.header("🔬 Análise de Confiabilidade Básica de Componentes")

            if not df_falhas_filtrado.empty:
                # Calcular total de horas no período filtrado
                total_period_seconds = (end_date - start_date).total_seconds() if len(date_range) == 2 else (df_falhas['DATA FINAL'].max() - df_falhas['DATA INICIAL'].min()).total_seconds()
                total_period_hours = total_period_seconds / 3600

                # Calcular MTTR, Ocorrências e Tempo Total Parada por ITEM
                df_reliability = df_falhas_filtrado.groupby('ITEM').agg(
                    Ocorrencias=('ITEM', 'count'),
                    Tempo_Total_Parada=('DURAÇÃO', 'sum'),
                    MTTR=('DURAÇÃO', 'mean'),
                    Ultima_Falha=('DATA FINAL', 'max') # Para previsão de falhas
                ).reset_index()

                # Calcular MTBF (aproximado): (Total Horas Observadas - Tempo Total Parada) / Ocorrências
                # Assumindo que todos os itens estavam "disponíveis" durante o período total
                # Cuidado: Esta é uma simplificação. Um MTBF preciso requer horas de operação exatas por item.
                df_reliability['MTBF (h)'] = (total_period_hours - df_reliability['Tempo_Total_Parada']) / df_reliability['Ocorrencias']
                df_reliability.replace([np.inf, -np.inf], np.nan, inplace=True) # Trata divisão por zero se Ocorrencias for 0
                df_reliability['MTBF (h)'] = df_reliability['MTBF (h)'].fillna(total_period_hours) # Se nunca falhou, MTBF é pelo menos o período total

                df_reliability = df_reliability.sort_values('Ocorrencias', ascending=False)

                st.subheader("Métricas de Confiabilidade por Item")
                st.dataframe(df_reliability.style.format({
                    'Tempo_Total_Parada': '{:.1f}',
                    'MTTR': '{:.1f}',
                    'MTBF (h)': '{:.1f}',
                    'Ultima_Falha': lambda x: x.strftime('%Y-%m-%d %H:%M') if pd.notna(x) else 'N/A'
                }), use_container_width=True)

                fig_reliability_mtbf = px.bar(
                    df_reliability.head(10), # Top 10 por ocorrências ou outro critério
                    x='ITEM',
                    y=['MTTR', 'MTBF (h)'],
                    title='MTTR e MTBF dos Componentes Principais',
                    barmode='group'
                )
                st.plotly_chart(fig_reliability_mtbf, use_container_width=True)
            else:
                st.info("Nenhum dado para análise de confiabilidade de componentes.")

            # --- Previsão de Falhas (Simples) ---
            st.header("🔮 Previsão de Falhas (Simples)")
            st.info("Esta é uma previsão heurística baseada no MTBF histórico dos itens. Considere um modelo preditivo mais avançado para maior precisão.")

            if not df_reliability.empty and 'Ultima_Falha' in df_reliability.columns and 'MTBF (h)' in df_reliability.columns:
                # Data de referência para calcular o tempo desde a última falha (pode ser a data atual ou a data final dos dados)
                current_ref_date = end_date if len(date_range) == 2 else datetime.now() # Usar a data final do período filtrado
                
                df_reliability['Tempo_Desde_Ultima_Falha (h)'] = (current_ref_date - df_reliability['Ultima_Falha']).dt.total_seconds() / 3600
                
                # Flag de risco: Se o tempo desde a última falha é >= 80% do MTBF
                df_reliability['Risco_Proxima_Falha'] = np.where(
                    (df_reliability['Tempo_Desde_Ultima_Falha (h)'] >= df_reliability['MTBF (h)'] * 0.8) & (df_reliability['Ocorrencias'] > 0),
                    'Alto', 'Baixo'
                )
                df_reliability['Risco_Proxima_Falha'] = np.where(df_reliability['Ocorrencias'] == 0, 'N/A (Sem Histórico)', df_reliability['Risco_Proxima_Falha'])


                st.subheader("Itens com Risco Potencial de Próxima Falha")
                risk_items = df_reliability[df_reliability['Risco_Proxima_Falha'] == 'Alto'].sort_values('Tempo_Desde_Ultima_Falha (h)', ascending=False)
                
                if not risk_items.empty:
                    st.dataframe(risk_items[[
                        'ITEM', 'Ocorrencias', 'MTBF (h)', 'Tempo_Desde_Ultima_Falha (h)', 'Ultima_Falha', 'Risco_Proxima_Falha'
                    ]].style.format({
                        'MTBF (h)': '{:.1f}',
                        'Tempo_Desde_Ultima_Falha (h)': '{:.1f}',
                        'Ultima_Falha': lambda x: x.strftime('%Y-%m-%d %H:%M') if pd.notna(x) else 'N/A'
                    }), use_container_width=True)
                else:
                    st.info("Nenhum item com alto risco de próxima falha identificado com os critérios atuais.")
            else:
                st.info("Dados insuficientes para realizar previsão de falhas.")

            # Análise Comparativa
            st.header("📊 Comparação de Desempenho (Interno)")
            
            # Comparação por Equipamento (já existente, mas agora com MTTR/MTBF se disponível)
            st.subheader("Comparação de KPIs por Equipamento")
            equipamentos_disp_comp = list(df_falhas_filtrado['EQUIPAMENTO'].unique())
            equipamentos_selecionados_comp = st.multiselect(
                "Selecione os Equipamentos para comparar detalhadamente",
                equipamentos_disp_comp,
                default=equipamentos_disp_comp[:min(3, len(equipamentos_disp_comp))] if equipamentos_disp_comp else [],
                key="equip_comp"
            )
            
            if equipamentos_selecionados_comp:
                try:
                    df_comp_equip = df_falhas_filtrado[df_falhas_filtrado['EQUIPAMENTO'].isin(equipamentos_selecionados_comp)]
                    kpis_comp_equip = df_comp_equip.groupby('EQUIPAMENTO').agg(
                        Tempo_Total_Parada=('DURAÇÃO', 'sum'),
                        Ocorrencias=('DURAÇÃO', 'count'),
                        MTTR_h=('DURAÇÃO', 'mean')
                    ).reset_index()

                    # Merge com MTBF calculado anteriormente, se aplicável
                    if not df_reliability.empty:
                        # Criar um DataFrame de resumo de MTBF por equipamento a partir de df_reliability
                        # Primeiro, mapeie os ITENS para seus EQUIPAMENTOS originais se a falha estiver ligada
                        # ou calcule MTBF por EQUIPAMENTO diretamente da falhas filtradas.
                        # Para manter a lógica anterior de MTBF por ITEM, vamos agrupar o resultado de MTBF por ITEM pelo EQUIPAMENTO
                        
                        # Para isso, precisamos da ligação EQUIPAMENTO-ITEM.
                        # Agrupe df_falhas_filtrado por EQUIPAMENTO e ITEM para obter as ocorrências por item em cada equipamento
                        df_equip_item_summary = df_falhas_filtrado.groupby(['EQUIPAMENTO', 'ITEM']).agg(
                            Ocorrencias_Item=('ITEM', 'count')
                        ).reset_index()

                        # Juntar com df_reliability para obter o MTBF de cada ITEM no EQUIPAMENTO
                        df_equip_item_reliability = pd.merge(df_equip_item_summary, df_reliability[['ITEM', 'MTBF (h)']], on='ITEM', how='left')
                        
                        # Agora podemos calcular um MTBF médio (ponderado ou simples) por EQUIPAMENTO
                        # Uma média simples é um bom começo
                        df_reliability_equip_summary = df_equip_item_reliability.groupby('EQUIPAMENTO')['MTBF (h)'].mean().reset_index()
                        df_reliability_equip_summary.rename(columns={'MTBF (h)': 'MTBF_h'}, inplace=True) # Renomeia para merge
                        
                        kpis_comp_equip = pd.merge(kpis_comp_equip, df_reliability_equip_summary, on='EQUIPAMENTO', how='left')


                    st.dataframe(kpis_comp_equip.style.format({
                        'Tempo_Total_Parada': '{:.1f}',
                        'MTTR_h': '{:.1f}',
                        'MTBF_h': '{:.1f}'
                    }), use_container_width=True)
                    
                    fig_comparacao = px.bar(
                        kpis_comp_equip,
                        x='EQUIPAMENTO',
                        y=['Tempo_Total_Parada', 'Ocorrencias', 'MTTR_h'],
                        title=f"Tempo Total de Manutenção, Ocorrências e MTTR por Equipamento",
                        barmode='group'
                    )
                    if 'MTBF_h' in kpis_comp_equip.columns:
                        fig_comparacao.add_scatter(x=kpis_comp_equip['EQUIPAMENTO'], y=kpis_comp_equip['MTBF_h'], mode='lines+markers', name='MTBF (h)', yaxis='y2')
                        fig_comparacao.update_layout(yaxis2=dict(title='MTBF (h)', overlaying='y', side='right'))

                    st.plotly_chart(fig_comparacao, use_container_width=True)
                except Exception as e:
                    st.error(f"Erro na comparação entre equipamentos: {str(e)}")
            else:
                st.warning("Selecione pelo menos um equipamento para comparação")

            # Nova Comparação por Frota
            st.subheader("Comparação de KPIs por Frota")
            
            # Garante que há mais de uma frota no filtro ou para comparar
            if len(frota_selecionada) > 1 and "Todas" not in frota_selecionada or ("Todas" in frota_selecionada and len(df_falhas_filtrado['FROTA'].unique()) > 1):
                df_comp_frota = df_falhas_filtrado
                if "Todas" not in frota_selecionada: # Aplica filtro se "Todas" não estiver selecionado
                     df_comp_frota = df_comp_frota[df_comp_frota['FROTA'].isin(frota_selecionada)]

                kpis_comp_frota = df_comp_frota.groupby('FROTA').agg(
                    Tempo_Total_Parada=('DURAÇÃO', 'sum'),
                    Ocorrencias=('DURAÇÃO', 'count'),
                    MTTR_h=('DURAÇÃO', 'mean')
                ).reset_index()
                
                # Para MTBF por frota, precisaríamos de uma agregação do MTBF dos itens/equipamentos dentro da frota.
                # Aqui faremos uma média simples do MTBF médio dos equipamentos da frota.
                if 'MTBF_h' in kpis_comp_equip.columns: # Reusa o cálculo de MTBF_h do df kpis_comp_equip se disponível
                    df_equip_mtbf_frota = kpis_comp_equip[['EQUIPAMENTO', 'MTBF_h']].dropna()
                    df_equip_frota_link = df_falhas_filtrado[['EQUIPAMENTO', 'FROTA']].drop_duplicates()
                    df_merged_mtbf_frota = pd.merge(df_equip_mtbf_frota, df_equip_frota_link, on='EQUIPAMENTO', how='inner')
                    
                    mtbf_frota = df_merged_mtbf_frota.groupby('FROTA')['MTBF_h'].mean().reset_index()
                    kpis_comp_frota = pd.merge(kpis_comp_frota, mtbf_frota, on='FROTA', how='left')


                st.dataframe(kpis_comp_frota.style.format({
                    'Tempo_Total_Parada': '{:.1f}',
                    'MTTR_h': '{:.1f}',
                    'MTBF_h': '{:.1f}'
                }), use_container_width=True)

                fig_comp_frota = px.bar(
                    kpis_comp_frota,
                    x='FROTA',
                    y=['Tempo_Total_Parada', 'Ocorrencias', 'MTTR_h'],
                    title="Tempo Total de Manutenção, Ocorrências e MTTR por Frota",
                    barmode='group'
                )
                if 'MTBF_h' in kpis_comp_frota.columns:
                    fig_comp_frota.add_scatter(x=kpis_comp_frota['FROTA'], y=kpis_comp_frota['MTBF_h'], mode='lines+markers', name='MTBF (h)', yaxis='y2')
                    fig_comp_frota.update_layout(yaxis2=dict(title='MTBF (h)', overlaying='y', side='right'))
                
                st.plotly_chart(fig_comp_frota, use_container_width=True)
            else:
                st.info("Selecione pelo menos duas frotas no filtro lateral para comparação por Frota ou remova o filtro 'Todas' se houver apenas uma frota nos dados.")
            
            # --- Visualização de Calendário/Heatmap de Falhas ---
            st.header("🔥 Padrões Temporais de Falha (Heatmap)")
            st.info("Identifica padrões de falha por dia da semana e mês, ou por hora e dia da semana.")

            if not df_falhas_filtrado.empty:
                df_falhas_filtrado['Dia da Semana'] = df_falhas_filtrado['DATA INICIAL'].dt.day_name(locale='pt_BR')
                df_falhas_filtrado['Mês'] = df_falhas_filtrado['DATA INICIAL'].dt.month_name(locale='pt_BR')
                df_falhas_filtrado['Hora'] = df_falhas_filtrado['DATA INICIAL'].dt.hour

                # Ordenar dias da semana e meses para o heatmap
                ordem_dias = ['Segunda-feira', 'Terça-feira', 'Quarta-feira', 'Quinta-feira', 'Sexta-feira', 'Sábado', 'Domingo']
                ordem_meses = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']

                heatmap_option = st.radio(
                    "Tipo de Heatmap:",
                    ["Falhas por Dia da Semana e Mês", "Falhas por Hora do Dia e Dia da Semana"],
                    horizontal=True,
                    key="heatmap_option"
                )

                if heatmap_option == "Falhas por Dia da Semana e Mês":
                    df_heatmap = df_falhas_filtrado.groupby(['Dia da Semana', 'Mês']).agg(
                        Total_Duracao=('DURAÇÃO', 'sum'),
                        Contagem_Falhas=('DURAÇÃO', 'count')
                    ).reset_index()

                    df_heatmap['Dia da Semana'] = pd.Categorical(df_heatmap['Dia da Semana'], categories=ordem_dias, ordered=True)
                    df_heatmap['Mês'] = pd.Categorical(df_heatmap['Mês'], categories=ordem_meses, ordered=True)
                    df_heatmap = df_heatmap.sort_values(['Dia da Semana', 'Mês'])

                    metric_to_show = st.radio("Mostrar no Heatmap:", ["Tempo de Parada (h)", "Contagem de Falhas"], horizontal=True, key="heatmap_metric_month_day")
                    z_col = 'Total_Duracao' if metric_to_show == "Tempo de Parada (h)" else 'Contagem_Falhas'
                    title_text = f'Heatmap de {metric_to_show} por Dia da Semana e Mês'

                    fig_heatmap = px.density_heatmap(
                        df_heatmap,
                        x='Mês',
                        y='Dia da Semana',
                        z=z_col,
                        title=title_text,
                        color_continuous_scale="Viridis"
                    )
                    st.plotly_chart(fig_heatmap, use_container_width=True)

                elif heatmap_option == "Falhas por Hora do Dia e Dia da Semana":
                    df_heatmap_hora = df_falhas_filtrado.groupby(['Hora', 'Dia da Semana']).agg(
                        Total_Duracao=('DURAÇÃO', 'sum'),
                        Contagem_Falhas=('DURAÇÃO', 'count')
                    ).reset_index()

                    df_heatmap_hora['Dia da Semana'] = pd.Categorical(df_heatmap_hora['Dia da Semana'], categories=ordem_dias, ordered=True)
                    df_heatmap_hora = df_heatmap_hora.sort_values(['Hora', 'Dia da Semana'])

                    metric_to_show_hour = st.radio("Mostrar no Heatmap:", ["Tempo de Parada (h)", "Contagem de Falhas"], horizontal=True, key="heatmap_metric_hour_day")
                    z_col_hour = 'Total_Duracao' if metric_to_show_hour == "Tempo de Parada (h)" else 'Contagem_Falhas'
                    title_text_hour = f'Heatmap de {metric_to_show_hour} por Hora do Dia e Dia da Semana'

                    fig_heatmap_hora = px.density_heatmap(
                        df_heatmap_hora,
                        x='Hora',
                        y='Dia da Semana',
                        z=z_col_hour,
                        title=title_text_hour,
                        color_continuous_scale="Viridis"
                    )
                    st.plotly_chart(fig_heatmap_hora, use_container_width=True)
            else:
                st.info("Nenhum dado para gerar heatmaps de padrões temporais.")

            # --- Análise de "Bad Actors" (Piores Ativos) ---
            st.header("📉 Análise de Piores Ativos ('Bad Actors')")
            st.info("Identifica equipamentos que consistentemente apresentam o pior desempenho em múltiplos KPIs.")

            if not df_falhas_filtrado.empty:
                # Re-calcular KPIs por equipamento (garantindo que estão atualizados com o filtro)
                kpis_equipamento = df_falhas_filtrado.groupby('EQUIPAMENTO').agg(
                    Tempo_Total_Parada=('DURAÇÃO', 'sum'),
                    Ocorrencias=('DURAÇÃO', 'count'),
                    MTTR=('DURAÇÃO', 'mean')
                ).reset_index()

                # Merge com o MTBF calculado anteriormente (por item, agregado por equipamento)
                # kpis_comp_equip é o dataframe que contém o MTBF_h por equipamento
                if 'MTBF_h' in kpis_comp_equip.columns: 
                    kpis_equipamento = pd.merge(kpis_equipamento, kpis_comp_equip[['EQUIPAMENTO', 'MTBF_h']], on='EQUIPAMENTO', how='left')
                else:
                    kpis_equipamento['MTBF_h'] = np.nan # Garante que a coluna existe

                if kpis_equipamento.empty:
                    st.info("Nenhum equipamento para análise de Bad Actors com os filtros atuais.")
                    return

                # Normalização Min-Max para criar um "Índice de Criticidade"
                # Quanto MAIOR o valor do índice, PIOR o equipamento.
                
                # Inicia o dataframe de scores
                df_scores = kpis_equipamento[['EQUIPAMENTO']].copy()

                # Tempo Total de Parada (maior é pior)
                if kpis_equipamento['Tempo_Total_Parada'].max() > 0:
                    df_scores['Score_Tempo_Parada'] = (kpis_equipamento['Tempo_Total_Parada'] - kpis_equipamento['Tempo_Total_Parada'].min()) / \
                                                     (kpis_equipamento['Tempo_Total_Parada'].max() - kpis_equipamento['Tempo_Total_Parada'].min())
                else:
                    df_scores['Score_Tempo_Parada'] = 0 # Se todos têm tempo de parada zero

                # Ocorrências (maior é pior)
                if kpis_equipamento['Ocorrencias'].max() > 0:
                    df_scores['Score_Ocorrencias'] = (kpis_equipamento['Ocorrencias'] - kpis_equipamento['Ocorrencias'].min()) / \
                                                    (kpis_equipamento['Ocorrencias'].max() - kpis_equipamento['Ocorrencias'].min())
                else:
                    df_scores['Score_Ocorrencias'] = 0 # Se todos têm zero ocorrências

                # MTTR (maior é pior)
                if kpis_equipamento['MTTR'].max() > 0:
                    df_scores['Score_MTTR'] = (kpis_equipamento['MTTR'] - kpis_equipamento['MTTR'].min()) / \
                                             (kpis_equipamento['MTTR'].max() - kpis_equipamento['MTTR'].min())
                else:
                    df_scores['Score_MTTR'] = 0 # Se todos têm MTTR zero ou NaN

                # MTBF (menor é pior, então inverta a lógica: (max_val - val) / (max_val - min_val))
                if 'MTBF_h' in kpis_equipamento.columns and kpis_equipamento['MTBF_h'].count() > 1: # Precisa de pelo menos 2 valores não NaN
                    # Trata NaNs no MTBF para que não afetem min/max
                    mtbf_valid = kpis_equipamento['MTBF_h'].dropna()
                    if not mtbf_valid.empty and mtbf_valid.max() > mtbf_valid.min():
                        df_scores['Score_MTBF'] = (mtbf_valid.max() - kpis_equipamento['MTBF_h']) / \
                                                  (mtbf_valid.max() - mtbf_valid.min())
                    else:
                        df_scores['Score_MTBF'] = 0
                else:
                    df_scores['Score_MTBF'] = 0 # Se MTBF não é aplicável ou não varia

                df_scores = df_scores.fillna(0) # Trata quaisquer NaNs resultantes da normalização (ex: se min=max)

                # Combina os scores (peso igual por padrão, pode ser ajustado com st.slider futuramente)
                df_scores['Indice_Criticidade'] = df_scores[['Score_Tempo_Parada', 'Score_Ocorrencias', 'Score_MTTR', 'Score_MTBF']].sum(axis=1)

                # Adiciona as colunas originais de KPI para visualização
                df_bad_actors = pd.merge(df_scores, kpis_equipamento, on='EQUIPAMENTO', how='left')
                df_bad_actors = df_bad_actors.sort_values('Indice_Criticidade', ascending=False)
                
                st.subheader("Ranking de Piores Ativos (Bad Actors)")
                st.dataframe(df_bad_actors[[
                    'EQUIPAMENTO', 'Indice_Criticidade', 'Tempo_Total_Parada', 'Ocorrencias', 'MTTR', 'MTBF_h'
                ]].style.format({
                    'Indice_Criticidade': '{:.2f}',
                    'Tempo_Total_Parada': '{:.1f}',
                    'MTTR': '{:.1f}',
                    'MTBF_h': '{:.1f}'
                }).background_gradient(cmap='Reds', subset=['Indice_Criticidade']),
                use_container_width=True)

                fig_bad_actors = px.bar(
                    df_bad_actors.head(10), # Mostra os top 10
                    x='EQUIPAMENTO',
                    y='Indice_Criticidade',
                    title='Top 10 Piores Ativos por Índice de Criticidade',
                    hover_data=['Tempo_Total_Parada', 'Ocorrencias', 'MTTR', 'MTBF_h']
                )
                st.plotly_chart(fig_bad_actors, use_container_width=True)

            else:
                st.info("Nenhum dado para análise de 'Bad Actors'.")


            # Análise Temporal
            st.header("⏳ Evolução Temporal")
            
            try:
                # Agrupamento para evolucao temporal por data (diário ou semanal)
                df_falhas_filtrado['DATA_DIA'] = df_falhas_filtrado['DATA INICIAL'].dt.to_period('D').dt.to_timestamp()
                df_temporal = df_falhas_filtrado.groupby(['DATA_DIA', 'EQUIPAMENTO'])['DURAÇÃO'].sum().reset_index()
                
                fig_temporal = px.line(
                    df_temporal,
                    x='DATA_DIA',
                    y='DURAÇÃO',
                    color='EQUIPAMENTO',
                    title="Evolução do Tempo de Manutenção Diário"
                )
                fig_temporal.update_xaxes(title_text="Data")
                fig_temporal.update_yaxes(title_text="Duração da Parada (h)")
                st.plotly_chart(fig_temporal, use_container_width=True)
            except Exception as e:
                st.error(f"Erro na análise temporal: {str(e)}")

            # Detecção de Anomalias
            st.header("⚠️ Detecção de Anomalias")
            
            if len(df_falhas_filtrado) > 10:
                try:
                    model = IsolationForest(contamination=0.1, random_state=42)
                    features = df_falhas_filtrado[['DURAÇÃO']].values
                    df_falhas_filtrado['Anomalia'] = model.fit_predict(features)
                    
                    # Converte -1 para 'Anomalia' e 1 para 'Normal'
                    df_falhas_filtrado['Anomalia_Label'] = df_falhas_filtrado['Anomalia'].map({-1: 'Anomalia', 1: 'Normal'})

                    fig_anomalias = px.scatter(
                        df_falhas_filtrado,
                        x='DATA INICIAL',
                        y='DURAÇÃO',
                        color='Anomalia_Label', # Usa a nova coluna para cor
                        color_discrete_map={'Anomalia': 'red', 'Normal': 'blue'}, # Cores personalizadas
                        hover_data=['EQUIPAMENTO', 'SISTEMA', 'CONJUNTO', 'ITEM', 'CAUSA'],
                        title="Eventos de Manutenção Anômalos"
                    )
                    st.plotly_chart(fig_anomalias, use_container_width=True)
                except Exception as e:
                    st.warning(f"Não foi possível executar a detecção de anomalias: {str(e)}")
            else:
                st.warning("Dados insuficientes para detecção de anomalias (mínimo 10 registros)")

            # Análise de Causas
            st.header("🛠️ Análise de Causas e Recomendações")
            
            try:
                causas = df_falhas_filtrado['CAUSA'].value_counts().nlargest(5)
                
                if not causas.empty:
                    tab1, tab2 = st.tabs(["Frequência", "Ações Recomendadas"])
                    
                    with tab1:
                        fig_causas = px.bar(
                            causas.reset_index(),
                            x='count', # 'count' é o nome padrão da coluna value_counts
                            y='CAUSA',
                            orientation='h',
                            title="Principais Causas de Falhas"
                        )
                        st.plotly_chart(fig_causas, use_container_width=True)
                    
                    with tab2:
                        st.subheader("Top 5 Causas e Recomendações Personalizadas")
                        for causa, count in causas.items():
                            with st.expander(f"**{causa}** ({count} ocorrências)"):
                                recomendacao = gerar_recomendacao(causa, df_conhecimento)
                                st.write(f"**Ação recomendada:** {recomendacao}")
                                st.write("**Equipamentos mais afetados por esta causa:**")
                                st.table(
                                    df_falhas_filtrado[df_falhas_filtrado['CAUSA'] == causa]['EQUIPAMENTO']
                                    .value_counts()
                                    .head(3)
                                    .reset_index()
                                )
                else:
                    st.warning("Nenhuma causa registrada nos dados filtrados.")
            except Exception as e:
                st.error(f"Erro na análise de causas: {str(e)}")

            # --- Análise de Variação e Outliers (Box Plots / Jackknife) ---
            st.header("📈 Análise de Variação e Outliers (Box Plots / Jackknife)")

            # Box plot por Sistema
            if len(df_falhas_filtrado['SISTEMA'].unique()) > 1:
                fig_boxplot_sistema = px.box(
                    df_falhas_filtrado,
                    x='SISTEMA',
                    y='DURAÇÃO',
                    title='Distribuição da Duração das Falhas por Sistema',
                    labels={'DURAÇÃO': 'Duração da Parada (h)'},
                    points="outliers" # Mostra os outliers
                )
                st.plotly_chart(fig_boxplot_sistema, use_container_width=True)
            else:
                st.info("Pelo menos dois sistemas são necessários para o Box Plot por Sistema (da planilha de Falhas).")

            # Box plot por Equipamento Selecionado
            if len(equipamentos_selecionados_comp) > 1:
                fig_boxplot_equip = px.box(
                    df_falhas_filtrado[df_falhas_filtrado['EQUIPAMENTO'].isin(equipamentos_selecionados_comp)],
                    x='EQUIPAMENTO',
                    y='DURAÇÃO',
                    title='Distribuição da Duração das Falhas por Equipamento Selecionado',
                    labels={'DURAÇÃO': 'Duração da Parada (h)'},
                    points="outliers"
                )
                st.plotly_chart(fig_boxplot_equip, use_container_width=True)
            else:
                st.info("Selecione pelo menos dois equipamentos para o Box Plot por Equipamento (da planilha de Falhas).")
            
            # Seção Final - Resumo Executivo, MCS, Outros Indicadores e Jackknife
            st.header("📌 Resumo Executivo e Detalhes")
            
            # --- Quadro estilo MCS ---
            st.subheader("📋 Quadro MCS (Motivo, Causa, Solução) e Performance")
            
            df_display_performance = pd.DataFrame()
            if not df_indicadores_agregados.empty and 'DISPONIBILIDADE_FISICA' in df_indicadores_agregados.columns:
                df_display_performance = df_indicadores_agregados[['EQUIPAMENTO', 'FROTA', 'DISPONIBILIDADE_FISICA']].copy()
                df_display_performance.rename(columns={'DISPONIBILIDADE_FISICA': 'DF_Alcancada_Indicadores (%)'}, inplace=True)
            
            # Cálculo de DF baseada em paradas (aproximação se não tiver dados de horas totais)
            if 'DATA INICIAL' in df_falhas_filtrado.columns and 'DATA FINAL' in df_falhas_filtrado.columns:
                total_days_in_period = (end_date - start_date).days + 1
                if total_days_in_period > 0:
                    total_period_hours = total_days_in_period * 24
                    downtime_per_equip = df_falhas_filtrado.groupby('EQUIPAMENTO')['DURAÇÃO'].sum().reset_index()
                    downtime_per_equip['DF_Alcancada_Calculada (%)'] = (1 - (downtime_per_equip['DURAÇÃO'] / total_period_hours)) * 100
                    downtime_per_equip['DF_Alcancada_Calculada (%)'] = downtime_per_equip['DF_Alcancada_Calculada (%)'].apply(lambda x: max(0, x)) # Garante que DF não é negativa
                    
                    # Merge com df_display_performance se ela existe, ou cria se não
                    if not df_display_performance.empty:
                        df_display_performance = pd.merge(df_display_performance, downtime_per_equip[['EQUIPAMENTO', 'DF_Alcancada_Calculada (%)']], on='EQUIPAMENTO', how='left')
                    else:
                        df_display_performance = downtime_per_equip[['EQUIPAMENTO', 'DURAÇÃO', 'DF_Alcancada_Calculada (%)']].rename(columns={'DURAÇÃO': 'Tempo Total Parada (h)'})

            if not df_display_performance.empty:
                df_meta_input = st.number_input("Insira a DF Meta (%) para os equipamentos:", min_value=0.0, max_value=100.0, value=90.0, step=0.1, key="df_meta_input")
                df_display_performance['DF_Meta (%)'] = df_meta_input
                if 'DF_Alcancada_Indicadores (%)' in df_display_performance.columns:
                    df_display_performance['Lacuna_DF (%)'] = df_display_performance['DF_Meta (%)'] - df_display_performance['DF_Alcancada_Indicadores (%)']
                elif 'DF_Alcancada_Calculada (%)' in df_display_performance.columns:
                    df_display_performance['Lacuna_DF (%)'] = df_display_performance['DF_Meta (%)'] - df_display_performance['DF_Alcancada_Calculada (%)']
                else:
                    df_display_performance['Lacuna_DF (%)'] = np.nan # Se nenhuma DF foi calculada

                st.markdown("---")
                st.subheader("Disponibilidade Física (DF) e Meta por Equipamento")
                
                st.dataframe(df_display_performance.style.format({
                    'DF_Alcancada_Indicadores (%)': '{:.2f}%',
                    'DF_Alcancada_Calculada (%)': '{:.2f}%',
                    'DF_Meta (%)': '{:.2f}%',
                    'Lacuna_DF (%)': '{:.2f}%'
                }).background_gradient(cmap='RdYlGn_r', subset=['Lacuna_DF (%)']), # Inverte o cmap para verde = bom, vermelho = ruim
                use_container_width=True)
                st.info("Nota: 'DF Alcançada (Indicadores)' vem da sua planilha de Indicadores. 'DF Alcançada (Calculada)' é uma estimativa baseada no tempo de parada e no período selecionado.")
            else:
                st.warning("Dados insuficientes para exibir a Disponibilidade Física dos equipamentos.")

            st.markdown("---")
            st.subheader("Análise MCS das Principais Causas (Detalhamento)")
            # Pega as 10 principais falhas para detalhamento MCS
            top_failures_for_mcs = df_falhas_filtrado.groupby(['EQUIPAMENTO', 'CAUSA']).agg(
                Tempo_Parada=('DURAÇÃO', 'sum'),
                Ocorrencias=('DURAÇÃO', 'count')
            ).reset_index().sort_values('Tempo_Parada', ascending=False).head(10)

            mcs_data = []
            if not top_failures_for_mcs.empty:
                for index, row in top_failures_for_mcs.iterrows():
                    equip = row['EQUIPAMENTO']
                    causa = row['CAUSA']
                    tempo_parada = row['Tempo_Parada']
                    ocorrencias = row['Ocorrencias']
                    recomendacao = gerar_recomendacao(causa, df_conhecimento)

                    mcs_data.append({
                        "Equipamento": equip,
                        "Motivo (Causa Principal)": causa, 
                        "Causa Detalhada": causa, 
                        "Solução/Ação Recomendada": recomendacao,
                        "Tempo de Parada (h)": f"{tempo_parada:.1f}",
                        "Ocorrências": ocorrencias
                    })
                st.dataframe(pd.DataFrame(mcs_data), use_container_width=True)
            else:
                st.warning("Não há principais causas de falha para exibir no quadro MCS com os filtros atuais.")


            st.markdown("---")
            st.subheader("Outros Indicadores Agregados (Planilha de Indicadores)")
            
            if not df_indicadores_agregados.empty:
                selected_indicadores_cols = [col for col in ['DISPONIBILIDADE_FISICA', 'UTILIZACAO_FISICA', 'OEE', 'MTBF', 'MTTR', 'PRODUTIVIDADE'] if col in df_indicadores_agregados.columns]
                
                if selected_indicadores_cols:
                    # Mostra médias/somas dos indicadores para o período/filtros selecionados
                    st.write("**Média/Total dos Indicadores no período:**")
                    indicadores_resumo = df_indicadores_agregados[selected_indicadores_cols].mean().to_frame(name='Valor Médio/Total')
                    st.dataframe(indicadores_resumo.style.format('{:.2f}'), use_container_width=True)

                    # Gráfico de barras dos principais KPIs do Indicadores por equipamento
                    fig_kpi_indicadores_equip = px.bar(
                        df_indicadores_agregados,
                        x='EQUIPAMENTO',
                        y=selected_indicadores_cols,
                        title="Principais Indicadores por Equipamento (da Planilha Indicadores)",
                        labels={"value": "Valor", "variable": "Indicador"},
                        barmode='group'
                    )
                    st.plotly_chart(fig_kpi_indicadores_equip, use_container_width=True)
                else:
                    st.info("Nenhum dos indicadores comuns (DF, Utilização, OEE, MTBF, MTTR, Produtividade) foi encontrado na planilha de Indicadores.")
            else:
                st.warning("Não há dados de indicadores para exibir com os filtros aplicados.")
            
            # --- Geração de Relatório PDF ---
            # Seção Final - Ranking e Linha do Tempo (mantido para o relatório)
            st.header("📌 Resumo Executivo (Para Relatório PDF)")
            
            # Top 10 Equipamentos Críticos
            st.subheader("🏆 Top 10 Equipamentos Mais Críticos")
            try:
                top_equipments = df_falhas_filtrado.groupby(['EQUIPAMENTO', 'FROTA', 'SISTEMA', 'CONJUNTO']).agg({
                    'DURAÇÃO': ['sum', 'count'],
                    'ITEM': lambda x: x.value_counts().index[0] if len(x.value_counts()) > 0 else 'N/A'
                }).reset_index()
                
                top_equipments.columns = ['EQUIPAMENTO', 'FROTA', 'SISTEMA', 'CONJUNTO', 'Tempo Total (h)', 'Ocorrências', 'Item Mais Frequente']
                top_equipments = top_equipments.sort_values('Tempo Total (h)', ascending=False).head(10)
                
                if not top_equipments.empty:
                    st.dataframe(
                        top_equipments.style.format({'Tempo Total (h)': '{:.1f}'}),
                        height=400
                    )
                else:
                    st.warning("Nenhum equipamento crítico encontrado.")
            except Exception as e:
                st.error(f"Erro ao identificar equipamentos críticos: {str(e)}")
            
            # Linha do Tempo das Falhas Mais Impactantes
            st.subheader("🕒 Linha do Tempo das Falhas Mais Impactantes")
            try:
                timeline_data = df_falhas_filtrado.sort_values('DURAÇÃO', ascending=False).head(20).copy()
                timeline_data['Impacto'] = pd.cut(
                    timeline_data['DURAÇÃO'],
                    bins=[0, 8, 24, float('inf')],
                    labels=['Baixo', 'Médio', 'Alto']
                )
                
                fig_timeline = px.scatter(
                    timeline_data,
                    x='DATA INICIAL',
                    y='DURAÇÃO',
                    color='Impacto',
                    size='DURAÇÃO',
                    hover_name='EQUIPAMENTO',
                    hover_data=['SISTEMA', 'CONJUNTO', 'ITEM', 'CAUSA'],
                    title="20 Falhas com Maior Impacto Temporal"
                )
                st.plotly_chart(fig_timeline, use_container_width=True)
            except Exception as e:
                st.error(f"Erro ao criar linha do tempo: {str(e)}")
            
            # KPIs por todos os níveis hierárquicos para o relatório
            kpis_hierarquia = {}
            try:
                for nivel, col in [('Sistema', 'SISTEMA'), ('Conjunto', 'CONJUNTO'), ('Item', 'ITEM')]:
                    df_kpi = df_falhas_filtrado.groupby(col).agg({
                        'DURAÇÃO': ['sum', 'mean', 'count'],
                        'EQUIPAMENTO': 'nunique' # Usa EQUIPAMENTO da planilha de Falhas
                    }).sort_values(('DURAÇÃO', 'sum'), ascending=False).head(10)
                    
                    if not df_kpi.empty:
                        df_kpi.columns = ['Tempo Total (h)', 'MTTR (h)', 'Ocorrências', 'Equip. Afetados']
                        kpis_hierarquia[nivel] = df_kpi
            except Exception as e:
                st.warning(f"Erro ao preparar dados para relatório: {str(e)}")
            
            # Botão para gerar relatório PDF
            st.markdown("---")
            if st.button("📄 Gerar Relatório PDF Completo"):
                with st.spinner("Gerando relatório..."):
                    try:
                        if not top_equipments.empty and not timeline_data.empty and kpis_hierarquia:
                            pdf_report = generate_pdf_report(df_falhas_filtrado, top_equipments, timeline_data, kpis_hierarquia, df_conhecimento)
                            st.markdown(create_download_link(pdf_report, "relatorio_manutencao.pdf"), unsafe_allow_html=True)
                            st.success("Relatório gerado com sucesso!")
                        else:
                            st.warning("Dados insuficientes para gerar o relatório completo")
                    except Exception as e:
                        st.error(f"Erro ao gerar relatório PDF: {str(e)}")

        except Exception as e:
            st.error(f"Erro ao processar os dados: {str(e)}")
            st.exception(e)

if __name__ == "__main__":
    exibir_kpis()