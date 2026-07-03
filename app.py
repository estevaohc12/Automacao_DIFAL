import streamlit as st
import pandas as pd
import xml.etree.ElementTree as ET
from io import BytesIO
import os

# Configuração Institucional
st.set_page_config(page_title="Identificador de DIFAL - Grupo Santo Anjo", page_icon="🛡️", layout="wide")

# Estilo Corporativo Minimalista
st.markdown("""
    <style>
    .main { background-color: #fcfcfc; }
    .stButton>button { 
        width: 100%; 
        border-radius: 5px; 
        background-color: #2c3e50; 
        color: white; 
        font-weight: bold;
    }
    .footer-text { 
        text-align: center; 
        color: #95a5a6; 
        padding: 30px; 
        font-size: 0.8em; 
        border-top: 1px solid #eee;
        margin-top: 50px;
    }
    </style>
    """, unsafe_allow_html=True)

# Logo na Barra Lateral
if os.path.exists("logo.png"):
    st.sidebar.image("logo.png", use_container_width=True)

st.sidebar.divider()
st.sidebar.markdown("### 📊 Status do Sistema")
st.sidebar.success("Servidor Ativo")
st.sidebar.info("Apenas Notas Fiscais processáveis (procNFe) são consideradas neste relatório.")

# Título do Sistema
st.title("🎯 Identificador Inteligente de DIFAL")
st.markdown("#### Divisão de Apoio Fiscal — **Grupo Santo Anjo**")
st.write("---")

def processar_xml(arquivo):
    try:
        conteudo = arquivo.read()
        root = ET.fromstring(conteudo)
        ns = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}
        
        # Filtro de arquivos de serviço ou evento
        tag_root = root.tag
        if "procEvento" in tag_root or "retEvento" in tag_root:
            return None 

        # Coleta de informações do Emitente
        emitente = root.find('.//nfe:emit', ns)
        fornecedor = emitente.find('nfe:xNome', ns).text if emitente is not None else "NÃO LOCALIZADO"

        nf = root.find('.//nfe:nNF', ns).text
        valor_nf = float(root.find('.//nfe:vNF', ns).text)
        cfop = root.find('.//nfe:det/nfe:prod/nfe:CFOP', ns).text
        crt = root.find('.//nfe:CRT', ns).text if root.find('.//nfe:CRT', ns) is not None else "3"
        
        mapa_ufs = {'11':'RO','12':'AC','13':'AM','14':'RR','15':'PA','16':'AP','17':'TO','21':'MA','22':'PI','23':'CE','24':'RN','25':'PB','26':'PE','27':'AL','28':'SE','29':'BA','31':'MG','32':'ES','33':'RJ','35':'SP','41':'PR','42':'SC','43':'RS','50':'MS','51':'MT','52':'GO','53':'DF'}
        uf_orig_node = root.find('.//nfe:cUF', ns)
        uf_origem = mapa_ufs.get(uf_orig_node.text, '??')
        uf_destino_node = root.find('.//nfe:dest/nfe:UF', ns)
        uf_destino = uf_destino_node.text if uf_destino_node is not None else "??"

        # Lógica Técnica DIFAL MG
        percentual = 0.0
        status_situacao = "ISENTO"
        tratativa = "Sem ações pendentes"
        cfops_remessa = ['6923', '6949', '6910', '6808', '6902', '6911', '6912', '6917']

        if uf_origem == uf_destino:
            justificativa = f"Operação Interna ({uf_origem}-{uf_destino})"
        elif cfop in cfops_remessa:
            justificativa = "Remessa / Isenção"
        elif cfop.startswith('6'):
            percentual = 0.0735
            status_situacao = "DIFAL"
            tratativa = "CALCULAR E RECOLHER GUIA DIFAL MG"
            tipo_crt = "Simples Nacional" if crt == "1" else "Regime Normal"
            justificativa = f"Venda Interestadual - {tipo_crt}"
        else:
            justificativa = f"Outras classificações (CFOP {cfop})"

        dif_aliq = round(valor_nf * percentual, 2)
        
        return {
            'SITUAÇÃO': status_situacao,
            'NF': nf, 
            'FORNECEDOR': fornecedor, 
            'VALOR NF': valor_nf,
            '% APLICAÇÃO': f"{percentual*100:.2f}%", 
            'VLR DIFAL': dif_aliq,
            'TOTAL + DIFAL': round(valor_nf + dif_aliq, 2),
            'JUSTIFICATIVA TÉCNICA': justificativa, 
            'PROCEDIMENTO': tratativa
        }
    except:
        return None

# Módulo de Upload
arquivos_xml = st.file_uploader("📥 Carregue os XMLs para análise automatizada", type=['xml'], accept_multiple_files=True)

if arquivos_xml:
    lista_processada = []
    for xml in arquivos_xml:
        dados = processar_xml(xml)
        if dados:
            lista_processada.append(dados)
    
    if lista_processada:
        df = pd.DataFrame(lista_processada)
        df = df.drop_duplicates(subset=['NF', 'FORNECEDOR', 'VALOR NF'])
        
        n_difal = len(df[df['SITUAÇÃO'] == "DIFAL"])
        st.success(f"Concluído: {len(df)} registros processados. Foram identificadas {n_difal} guias de DIFAL pendentes.")
        
        # Colorir linhas DIFAL para atenção do operador
        st.dataframe(df.style.apply(lambda x: ['background-color: #fff2f2; color: #721c24' if x['SITUAÇÃO'] == 'DIFAL' else '' for i in x], axis=1), use_container_width=True)

        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Controle_DIFAL')
        
        st.download_button(
            label="💾 Baixar Planilha Consolidada (.xlsx)",
            data=output.getvalue(),
            file_name="Relatorio_Geral_Fiscal_GrupoSantoAnjo.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.error("Os arquivos enviados não possuem dados fiscais de faturamento válidos.")

# Rodapé Técnico e Limpo
st.markdown("""<div class="footer-text">© 2026 Grupo Santo Anjo — Tecnologia de Apoio à Gestão Fiscal | v1.0.4</div>""", unsafe_allow_html=True)