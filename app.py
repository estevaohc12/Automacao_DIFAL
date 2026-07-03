import streamlit as st
import pandas as pd
import xml.etree.ElementTree as ET
from io import BytesIO
import os

# Configuração Institucional
st.set_page_config(page_title="DIFAL - Grupo Santo Anjo", page_icon="📊", layout="wide")

# Estilo Corporativo
st.markdown("""
    <style>
    .main { background-color: #ffffff; }
    .stButton>button { 
        width: 100%; border-radius: 5px; background-color: #2c3e50; color: white; font-weight: bold;
    }
    .footer-text { 
        text-align: center; color: #95a5a6; padding: 20px; font-size: 0.8em; border-top: 1px solid #eee; margin-top: 50px; 
    }
    </style>
    """, unsafe_allow_html=True)

if os.path.exists("logo.png"):
    st.sidebar.image("logo.png", use_container_width=True)

st.sidebar.divider()
st.sidebar.markdown("### ⚙️ Menu Principal")
st.sidebar.info("Processamento de Notas Fiscais para cálculo de DIFAL (Minas Gerais).")

st.title("🎯 Identificador Automático de DIFAL")
st.markdown("#### Grupo Santo Anjo - Apoio Fiscal")
st.write("---")

def processar_xml(arquivo):
    try:
        conteudo = arquivo.read()
        root = ET.fromstring(conteudo)
        ns = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}
        tag_root = root.tag

        # Ignorar Eventos e arquivos de logística que não têm dados fiscais (purgar as 43 linhas)
        if "procEvento" in tag_root or "retEvento" in tag_root or "evento" in tag_root.lower():
            return None

        # Identificação das Tags conforme NF-e nacional
        nf_node = root.find('.//nfe:nNF', ns)
        emit_node = root.find('.//nfe:emit/nfe:xNome', ns)
        valor_node = root.find('.//nfe:vNF', ns)
        cfop_node = root.find('.//nfe:det/nfe:prod/nfe:CFOP', ns)
        crt_node = root.find('.//nfe:CRT', ns)
        uf_orig_node = root.find('.//nfe:cUF', ns)
        uf_dest_node = root.find('.//nfe:dest/nfe:UF', ns)

        if nf_node is None or valor_node is None:
            return None

        nf = nf_node.text
        fornecedor = emit_node.text if emit_node is not None else "FORNECEDOR NÃO ENCONTRADO"
        valor_nf = float(valor_node.text)
        cfop = cfop_node.text
        crt = crt_node.text if crt_node is not None else "3"

        mapa_ufs = {'11':'RO','12':'AC','13':'AM','14':'RR','15':'PA','16':'AP','17':'TO','21':'MA','22':'PI','23':'CE','24':'RN','25':'PB','26':'PE','27':'AL','28':'SE','29':'BA','31':'MG','32':'ES','33':'RJ','35':'SP','41':'PR','42':'SC','43':'RS','50':'MS','51':'MT','52':'GO','53':'DF'}
        uf_origem = mapa_ufs.get(uf_orig_node.text, '??')
        uf_destino = uf_dest_node.text if uf_dest_node is not None else "??"

        # LÓGICA DE CALCULO
        percentual = 0.0
        justificativa = "Outras operações/Interna"
        tratativa = "Nenhuma ação necessária"
        
        remessas = ['6923', '6949', '6910', '6808', '6902', '6911', '6912', '6917']

        if uf_origem == uf_destino:
            justificativa = f"Operação Interna ({uf_origem}-{uf_destino}) - Sem DIFAL"
        elif cfop in remessas:
            justificativa = "Remessa de Mercadoria - Sem DIFAL"
        elif cfop.startswith('6'):
            percentual = 0.0735
            justificativa = f"Venda Interestadual - Fornecedor {'Simples Nacional' if crt == '1' else 'Regime Normal'}"
            tratativa = "Gerar e recolher guia de DIFAL para o estado de MG"
        
        dif_aliq = round(valor_nf * percentual, 2)
        
        # Ordem das colunas exatamente conforme o print do usuário
        return {
            'NF': nf,
            'FORNECEDOR': fornecedor,
            'VALOR NF': valor_nf,
            '%': f"{percentual*100:.2f}%",
            'DIF ALIQUOTA': dif_aliq,
            'VALOR REAL': round(valor_nf + dif_aliq, 2),
            'JUSTIFICATIVA': justificativa,
            'TRATATIVA': tratativa
        }
    except:
        return None

# Upload de Arquivos
arquivos = st.file_uploader("📥 Arraste os XMLs aqui", type=['xml'], accept_multiple_files=True)

if arquivos:
    dados = []
    for f in arquivos:
        resultado = processar_xml(f)
        if resultado:
            dados.append(resultado)
    
    if dados:
        df = pd.DataFrame(dados)
        # Reordenar para garantir a ordem exata do print
        colunas_ordem = ['NF', 'FORNECEDOR', 'VALOR NF', '%', 'DIF ALIQUOTA', 'VALOR REAL', 'JUSTIFICATIVA', 'TRATATIVA']
        df = df[colunas_ordem]

        st.success(f"✅ {len(df)} Notas Fiscais processadas com sucesso.")
        
        # Exibição na Tela
        st.dataframe(df, use_container_width=True)

        # Geração do arquivo para download
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        
        st.download_button(
            label="📥 Baixar Excel Estilo Original",
            data=output.getvalue(),
            file_name="Controle_DIFAL_GrupoSantoAnjo.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.error("Nenhuma nota fiscal processável encontrada nos arquivos enviados.")

st.markdown("""<div class="footer-text">© 2026 Grupo Santo Anjo — Tecnologia Fiscal Corporativa</div>""", unsafe_allow_html=True)