import streamlit as st
import pandas as pd
import xml.etree.ElementTree as ET
from io import BytesIO
from PIL import Image
import os

# Configuração da página
st.set_page_config(page_title="Identificador de DIFAL", page_icon="📊", layout="wide")

# Estilo CSS para melhorar a aparência
st.markdown("""
    <style>
    .main {
        background-color: #f5f5f5;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #FF4B4B;
        color: white;
    }
    footer {
        visibility: hidden;
    }
    .footer-text {
        text-align: center;
        color: #999;
        padding: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# Exibição do Logo na Barra Lateral
if os.path.exists("logo.png"):
    logo = Image.open("logo.png")
    st.sidebar.image(logo, use_container_width=True)

st.sidebar.divider()
st.sidebar.markdown("### ⚙️ Configurações")
st.sidebar.info("Arraste os arquivos XML extraídos do seu sistema fiscal para processar o DIFAL de Minas Gerais.")

# Título Principal Atualizado
st.title("🎯 Identificador Automático de DIFAL")
st.write("---")

# Função de extração
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
            justificativa = f'Operação Interna ({uf_origem}-{uf_destino}) - Sem DIFAL'
        elif cfop in cfops_remessa:
            justificativa = 'Remessa de Mercadoria - Sem DIFAL'
        elif cfop.startswith('6'):
            percentual = 0.0735
            tratativa = 'Gerar e recolher guia de DIFAL para o estado de MG'
            justificativa = f'Venda Interestadual - Fornecedor {"Simples" if crt=="1" else "Normal"}'
        else:
            justificativa = 'Outras operações'

        return {
            'NF': nf, 'FORNECEDOR': fornecedor, 'VALOR DA NF': valor_nf,
            '%': f"{percentual*100:.2f}%", 'DIF ALIQUOTA': round(valor_nf * percentual, 2),
            'VALOR REAL': round(valor_nf * (1 + percentual), 2),
            'JUSTIFICATIVA': justificativa, 'TRATATIVA': tratativa
        }
    except: return None

# Área de Upload
arquivos_xml = st.file_uploader("📥 Arraste seus arquivos XML aqui", type=['xml'], accept_multiple_files=True)

if arquivos_xml:
    dados_finais = []
    for xml in arquivos_xml:
        resultado = processar_xml(xml)
        if resultado:
            dados_finais.append(resultado)
    
    if dados_finais:
        df = pd.DataFrame(dados_finais)
        st.success(f"✅ {len(dados_finais)} notas processadas!")
        
        # Exibe a tabela
        st.dataframe(df, use_container_width=True)

        # Download do Excel
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='DIFAL')
        
        st.download_button(
            label="💾 Baixar Relatório Excel",
            data=output.getvalue(),
            file_name="Relatorio_DIFAL_GrupoS.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.error("Nenhum dado válido encontrado.")

# Rodapé com Créditos
st.write("---")
st.markdown(
    """
    <div class="footer-text">
        🔒 Sistema de Apoio Fiscal - Grupo S<br>
        <b>Desenvolvido por Estevão Henrique</b>
    </div>
    """, 
    unsafe_allow_html=True
)