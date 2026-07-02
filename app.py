import streamlit as st
import pandas as pd
import xml.etree.ElementTree as ET
from io import BytesIO
from PIL import Image
import os

# Configuração da página
st.set_page_config(page_title="Identificador de DIFAL", page_icon="📊", layout="wide")

# Estilo CSS para deixar o visual "Premium"
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        background-color: #ff4b4b;
        color: white;
        font-weight: bold;
    }
    .footer-text {
        text-align: center;
        color: #666;
        padding: 30px;
        font-family: sans-serif;
    }
    .sidebar .sidebar-content { background-color: #ffffff; }
    </style>
    """, unsafe_allow_html=True)

# --- LOGO NA BARRA LATERAL ---
# O código vai procurar por 'logo.png' ou 'logo.jpg'
if os.path.exists("logo.png"):
    st.sidebar.image("logo.png", use_container_width=True)
elif os.path.exists("logo.jpg"):
    st.sidebar.image("logo.jpg", use_container_width=True)

st.sidebar.divider()
st.sidebar.markdown("### ⚙️ Sistema Interno")
st.sidebar.info("Ferramenta exclusiva para o processamento de XMLs de NF-e do **Grupo Santo Anjo**.")

# --- TÍTULO PRINCIPAL ---
st.title("🎯 Identificador Automático de DIFAL")
st.markdown("#### Inteligência Fiscal - Grupo Santo Anjo")
st.write("---")

def processar_xml(arquivo):
    try:
        tree = ET.parse(arquivo)
        root = tree.getroot()
        ns = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}
        nf = root.find('.//nfe:nNF', ns).text
        fornecedor = root.find('.//nfe:emit/nfe:xNome', ns).text
        valor_nf = float(root.find('.//nfe:vNF', ns).text)
        crt = root.find('.//nfe:CRT', ns).text
        cfop = root.find('.//nfe:det/nfe:prod/nfe:CFOP', ns).text
        
        mapa_ufs = {'11':'RO','12':'AC','13':'AM','14':'RR','15':'PA','16':'AP','17':'TO','21':'MA','22':'PI','23':'CE','24':'RN','25':'PB','26':'PE','27':'AL','28':'SE','29':'BA','31':'MG','32':'ES','33':'RJ','35':'SP','41':'PR','42':'SC','43':'RS','50':'MS','51':'MT','52':'GO','53':'DF'}
        cod_uf_origem = root.find('.//nfe:cUF', ns).text
        uf_origem = mapa_ufs.get(cod_uf_origem, '??')
        uf_destino = root.find('.//nfe:dest/nfe:UF', ns).text

        justificativa = ""; tratativa = "Nenhuma ação necessária"; percentual = 0.0
        cfops_remessa = ['6923', '6949', '6910', '6808', '6902']

        if uf_origem == uf_destino:
            justificativa = f'Operação Interna ({uf_origem}-{uf_destino})'
        elif cfop in cfops_remessa:
            justificativa = 'Remessa de Mercadoria'
        elif cfop.startswith('6'):
            percentual = 0.0735
            tratativa = 'Gerar e recolher guia de DIFAL para MG'
            justificativa = f'Venda Interestadual ({"Simples" if crt=="1" else "Normal"})'
        
        dif_aliq = round(valor_nf * percentual, 2)
        return {
            'NF': nf, 'FORNECEDOR': fornecedor, 'VALOR NF': valor_nf,
            '%': f"{percentual*100:.2f}%", 'DIF ALIQUOTA': dif_aliq,
            'VALOR REAL': round(valor_nf + dif_aliq, 2),
            'JUSTIFICATIVA': justificativa, 'TRATATIVA': tratativa
        }
    except: return None

# --- UPLOAD ---
arquivos_xml = st.file_uploader("📥 Arraste seus arquivos XML aqui", type=['xml'], accept_multiple_files=True)

if arquivos_xml:
    dados = [res for res in [processar_xml(x) for x in arquivos_xml] if res]
    if dados:
        df = pd.DataFrame(dados)
        st.success(f"✅ {len(dados)} notas processadas!")
        st.dataframe(df, use_container_width=True)

        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='DIFAL')
        
        st.download_button(
            label="💾 Baixar Relatório Grupo Santo Anjo",
            data=output.getvalue(),
            file_name="Relatorio_DIFAL_SantoAnjo.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# --- RODAPÉ COM CRÉDITOS ---
st.write("---")
st.markdown(
    """
    <div class="footer-text">
        🛡️ Sistema de Apoio Fiscal - <b>Grupo Santo Anjo</b><br>
        👨‍💻 Desenvolvido por <b>Estevão Henrique</b>
    </div>
    """, 
    unsafe_allow_html=True
)