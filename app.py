import streamlit as st
import pandas as pd
import xml.etree.ElementTree as ET
from io import BytesIO
import os

# Configuração da página - FOCO EXCLUSIVO EM DIFAL
st.set_page_config(page_title="Calculador de DIFAL MG", page_icon="💸", layout="wide")

# Estilo Premium
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { width: 100%; border-radius: 8px; background-color: #ff4b4b; color: white; font-weight: bold; height: 3em;}
    .footer-text { text-align: center; color: #666; padding: 20px; border-top: 1px solid #ddd; margin-top: 50px;}
    </style>
    """, unsafe_allow_html=True)

if os.path.exists("logo.png"):
    st.sidebar.image("logo.png", use_container_width=True)

st.sidebar.divider()
st.sidebar.warning("⚡ **Filtro Ativo: Apenas DIFAL**\n\nEste sistema está configurado para exibir apenas notas de fora do estado que geram imposto a recolher.")

st.title("🎯 Identificador Automático de DIFAL")
st.markdown("#### Grupo Santo Anjo - Relatório de Notas para Recolhimento")
st.write("---")

def processar_xml(arquivo):
    try:
        conteudo = arquivo.read()
        root = ET.fromstring(conteudo)
        ns = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}
        
        # Ignora Eventos (Ciência, Cancelamento, etc.)
        tag_root = root.tag
        if "procEvento" in tag_root or "retEvento" in tag_root or "evento" in tag_root.lower():
            return None 

        # Coleta básica
        nf_node = root.find('.//nfe:nNF', ns)
        emit_node = root.find('.//nfe:emit', ns)
        valor_node = root.find('.//nfe:vNF', ns)
        cfop_node = root.find('.//nfe:det/nfe:prod/nfe:CFOP', ns)
        uf_orig_node = root.find('.//nfe:cUF', ns)
        uf_dest_node = root.find('.//nfe:dest/nfe:UF', ns)
        crt_node = root.find('.//nfe:CRT', ns)

        if nf_node is None or valor_node is None:
            return None

        # --- LÓGICA FILTRANTE ---
        mapa_ufs = {'11':'RO','12':'AC','13':'AM','14':'RR','15':'PA','16':'AP','17':'TO','21':'MA','22':'PI','23':'CE','24':'RN','25':'PB','26':'PE','27':'AL','28':'SE','29':'BA','31':'MG','32':'ES','33':'RJ','35':'SP','41':'PR','42':'SC','43':'RS','50':'MS','51':'MT','52':'GO','53':'DF'}
        uf_origem = mapa_ufs.get(uf_orig_node.text, '??')
        uf_destino = uf_dest_node.text if uf_dest_node is not None else "??"
        cfop = cfop_node.text if cfop_node is not None else "0000"

        # REGRA 1: Se for operação INTERNA (Minas para Minas), descarta.
        if uf_origem == uf_destino:
            return None
        
        # REGRA 2: Se o CFOP não começar com 6 (Venda Interestadual), descarta.
        if not cfop.startswith('6'):
            return None
            
        # REGRA 3: Se for CFOP de Remessa (que não paga imposto), descarta.
        cfops_remessa = ['6923', '6949', '6910', '6808', '6902', '6911', '6912', '6917']
        if cfop in cfops_remessa:
            return None

        # Se chegou aqui, é DIFAL!
        fornecedor = emit_node.find('nfe:xNome', ns).text if emit_node is not None else "NÃO LOCALIZADO"
        valor_nf = float(valor_node.text)
        crt = crt_node.text if crt_node is not None else "3"
        percentual = 0.0735
        
        tratativa = 'Gerar e recolher guia de DIFAL para MG'
        justificativa = f'Venda Interestadual ({uf_origem}->{uf_dest_node.text}) - Fornecedor {"Simples" if crt=="1" else "Normal"}'
        
        dif_aliq = round(valor_nf * percentual, 2)
        
        return {
            'NF': nf, 'FORNECEDOR': fornecedor, 'VALOR NF': valor_nf,
            '%': f"{percentual*100:.2f}%", 'DIF ALIQUOTA': dif_aliq,
            'VALOR REAL': round(valor_nf + dif_aliq, 2),
            'JUSTIFICATIVA': justificativa, 'TRATATIVA': tratativa
        }
    except:
        return None

# --- INTERFACE ---
arquivos_xml = st.file_uploader("📥 Arraste TODOS os seus XMLs aqui", type=['xml'], accept_multiple_files=True)

if arquivos_xml:
    dados_totais = []
    for xml in arquivos_xml:
        res = processar_xml(xml)
        if res:
            dados_totais.append(res)
    
    if dados_totais:
        df = pd.DataFrame(dados_totais)
        df = df.drop_duplicates(subset=['NF', 'FORNECEDOR', 'VALOR NF'])
        
        st.success(f"💸 Pronto! {len(df)} Notas de DIFAL identificadas.")
        st.dataframe(df, use_container_width=True)

        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='DIFAL_A_RECOLHER')
        
        st.download_button(label="💾 Baixar Lista de DIFAL - Grupo Santo Anjo", data=output.getvalue(), file_name="DIFAL_PARA_RECOLHER_SANTOANJO.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else:
        st.info("Nenhuma operação de DIFAL (Venda Interestadual) foi encontrada nos arquivos enviados.")

# RODAPÉ
st.markdown("""<div class="footer-text">🛡️ Controle de Arrecadação - <b>Grupo Santo Anjo</b> | 👨‍💻 Desenvolvido por <b>Estevão Henrique</b></div>""", unsafe_allow_html=True)