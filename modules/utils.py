# modules/utils.py

import streamlit as st
import pandas as pd
import numpy as np
from fpdf import FPDF
import base64
from io import BytesIO
import warnings

warnings.filterwarnings('ignore')

# --- Funções de Carregamento e Recomendação do Banco de Conhecimento ---

def carregar_banco_conhecimento():
    """Carrega o banco de conhecimento de falhas, causas e soluções de 'banco_conhecimento.xlsx'."""
    try:
        df_conhecimento = pd.read_excel("banco_conhecimento.xlsx", sheet_name="Falhas")
        df_conhecimento['TipoFalha'] = df_conhecimento['TipoFalha'].str.lower().str.strip()
        df_conhecimento['Causa'] = df_conhecimento['Causa'].str.lower().str.strip()
        df_conhecimento['AcaoRecomendada'] = df_conhecimento['AcaoRecomendada'].astype(str)
        return df_conhecimento
    except Exception as e:
        st.warning(f"Não foi possível carregar o banco de conhecimento (banco_conhecimento.xlsx): {str(e)}. Verifique se o arquivo está na pasta raiz do projeto.")
        return pd.DataFrame(columns=['TipoFalha', 'Causa', 'AcaoRecomendada'])

def gerar_recomendacao(causa, df_conhecimento):
    """Gera recomendações baseadas no banco de conhecimento ou em padrões genéricos."""
    causa = str(causa).lower().strip()
    
    recomendacoes = df_conhecimento[df_conhecimento['Causa'].str.contains(causa, case=False, na=False)]
    
    if not recomendacoes.empty:
        return "\n".join([f"• {rec}" for rec in recomendacoes['AcaoRecomendada'].head(3).tolist()])
    
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
        if palavra_chave.lower() in causa:
            return acao
    
    return "Realizar análise de causa raiz com a equipe técnica"

# --- Funções de Limpeza de Dados ---

def clean_duration(value):
    """Converte valores de duração para float de forma segura."""
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
    """Limpa e converte uma coluna para string consistente."""
    return series.astype(str).str.strip()

# --- Funções de Geração de Relatórios PDF ---

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

def generate_pdf_report(df, top_equipments, timeline_data, kpis_hierarquia, df_conhecimento):
    pdf = PDFReport()
    pdf.add_page()
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'Relatório de Análise de Manutenção', 0, 1, 'C')
    pdf.ln(10)
    
    if not top_equipments.empty:
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, 'Top 10 Equipamentos Críticos', 0, 1)
        pdf.ln(5)
        
        pdf.set_font('Arial', '', 10)
        col_widths = [30, 25, 25, 25, 25, 25]
        headers = ['Equipamento', 'Frota', 'Tempo Total (h)', 'Falhas', 'Sistema', 'Conjunto']
        
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
    
    pdf.add_page()
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'Análise Hierárquica de Falhas', 0, 1)
    pdf.ln(5)
    
    for nivel, df_kpi in kpis_hierarquia.items():
        if not df_kpi.empty:
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 10, f'Nível: {nivel}', 0, 1)
            pdf.ln(3)
            
            pdf.set_font('Arial', '', 10)
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
    
    pdf.add_page()
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'Linha do Tempo das Falhas Mais Impactantes', 0, 1)
    pdf.ln(5)
    
    if not timeline_data.empty:
        pdf.set_font('Arial', '', 10)
        for _, event in timeline_data.iterrows():
            pdf.set_fill_color(200, 220, 255)
            pdf.cell(0, 10, f"{event['DATA INICIAL'].strftime('%d/%m/%Y')} - {event['EQUIPAMENTO']}", 1, 1, 'L', 1)
            pdf.cell(0, 8, f"Sistema: {event['SISTEMA']} > Conjunto: {event['CONJUNTO']} > Item: {event['ITEM']}", 0, 1)
            pdf.cell(0, 8, f"Falha: {event['CAUSA']}", 0, 1)
            pdf.cell(0, 8, f"Duração: {event['DURAÇÃO']} horas | Impacto: {event['Impacto']}", 0, 1)
            pdf.ln(3)
    
    pdf.add_page()
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'Recomendações Prioritárias', 0, 1)
    pdf.ln(5)
    
    if not timeline_data.empty:
        causas = timeline_data['CAUSA'].value_counts().nlargest(5)
        for i, (causa, _) in enumerate(causas.items(), 1):
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 10, f"{i}. {causa}", 0, 1)
            pdf.set_font('Arial', '', 10)
            pdf.multi_cell(0, 8, gerar_recomendacao(causa, df_conhecimento))
            pdf.ln(3)
    
    return pdf.output(dest='S').encode('latin1')