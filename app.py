import streamlit as st
import pandas as pd
import xml.etree.ElementTree as ET
from io import BytesIO
import os

# Configuração da página
st.set_page_config(page_title="Identificador de DIFAL", page_icon="📊", layout="wide")

# Estilo Grupo Santo Anjo
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { width: 100%; border-radius: 8px; background-color: #ff4b4b; color: white; font-weight: bold; }
    .footer-text { text-align: center; color: #666; padding: 30px; font-family: sans-serif; }
    </style>
    """, unsafe_allow_html=True)

if os.path.exists("logo.png"):
    st.sidebar.image("logo.png", use_container_width=True)

st.sidebar.divider()
st.sidebar.info("🛡️ Sistema de Apoio Fiscal - **Grupo Santo Anjo**")

st.title("🎯 Identificador Automático de DIFAL")
st.markdown("#### Inteligência Fiscal - Grupo Santo Anjo")
st.write("---")

def processar_xml(arquivo):
    try:
        conteudo = arquivo.read()
        root = ET.fromstring(conteudo)
        ns = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}
        tag_root = root.tag
        
        # --- SE FOR UM EVENTO (Ciência, Cancelamento, etc.) ---
        if "procEvento" in tag_root or "retEvento" in tag_root or "evento" in tag_root.lower():
            chave_node = root.find('.//nfe:chNFe', ns)
            chave = chave_node.text if chave_node is not None else "Chave não encontrada"
            return {
                'NF': 'EVENTO',
                'FORNECEDOR': "⚠️ Arquivo de Evento (Sem Nome)",
                'VALOR NF': 0.0,
                '%': "0.00%",
                'DIF ALIQUOTA': 0.0,
                'VALOR REAL': 0.0,
                'JUSTIFICATIVA': f"Evento de Ciência/Correção da Chave: {chave}",
                'TRATATIVA': "Para calcular, suba o arquivo XML da NOTA (procNFe)"
            }

        # --- SE FOR UMA NOTA FISCAL (procNFe) ---
        # Busca específica dentro do grupo EMITENTE (Fornecedor)
        emitente = root.find('.//nfe:emit', ns)
        
        if emitente is not None:
            fornecedor = emitente.find('nfe:xNome', ns).text
        else:
            # Caso o XML tenha uma estrutura sem namespace direto (comum em alguns sistemas)
            emitente_alt = root.find('.//emit')
            fornecedor = emitente_alt.find('xNome').text if emitente_alt is not None else "FORNECEDOR NÃO LOCALIZADO"

        nf_node = root.find('.//nfe:nNF', ns)
        valor_node = root.find('.//nfe:vNF', ns)
        cfop_node = root.find('.//nfe:det/nfe:prod/nfe:CFOP', ns)
        uf_orig_node = root.find('.//nfe:cUF', ns)
        uf_dest_node = root.find('.//nfe:dest/nfe:UF', ns)
        crt_node = root.find('.//nfe:CRT', ns)

        if nf_node is None or valor_node is None:
            return f"⚠️ O arquivo {arquivo.name} não contém dados de faturamento."

        nf = nf_node.text
        valor_nf = float(valor_node.text)
        cfop = cfop_node.text if cfop_node is not None else "0000"
        crt = crt_node.text if crt_node is not None else "3"
        
        mapa_ufs = {'11':'RO','12':'AC','13':'AM','14':'RR','15':'PA','16':'AP','17':'TO','21':'MA','22':'PI','23':'CE','24':'RN','25':'PB','26':'PE','27':'AL','28':'SE','29':'BA','31':'MG','32':'ES','33':'RJ','35':'SP','41':'PR','42':'SC','43':'RS','50':'MS','51':'MT','52':'GO','53':'DF'}
        uf_origem = mapa_ufs.get(uf_orig_node.text, '??')
        uf_destino = uf_dest_node.text if uf_dest_node is not None else "??"

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
        
        dif_aliq = round(valor_nf * percentual, 2)
        return {
            'NF': nf, 'FORNECEDOR': fornecedor, 'VALOR NF': valor_nf,
            '%': f"{percentual*100:.2f}%", 'DIF ALIQUOTA': dif_aliq,
            'VALOR REAL': round(valor_nf + dif_aliq, 2),
            'JUSTIFICATIVA': justificativa, 'TRATATIVA': tratativa
        }
    except Exception as e:
        return f"❌ Erro no arquivo {arquivo.name}: {str(e)}"

# Interface
arquivos_xml = st.file_uploader("📥 Arraste seus arquivos XML aqui", type=['xml'], accept_multiple_files=True)

if arquivos_xml:
    dados_finais = []
    avisos = []
    for xml in arquivos_xml:
        resultado = processar_xml(xml)
        if isinstance(resultado, dict):
            dados_finais.append(resultado)
        else:
            avisos.append(resultado)
    
    if avisos:
        with st.expander("🔍 Ver avisos de arquivos ignorados"):
            for aviso in avisos:
                st.warning(aviso)

    if dados_finais:
        df = pd.DataFrame(dados_finais)
        st.success(f"✅ {len(dados_finais)} itens processados!")
        st.dataframe(df, use_container_width=True)

        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='DIFAL')
        
        st.download_button(label="💾 Baixar Relatório Grupo Santo Anjo", data=output.getvalue(), file_name="Relatorio_DIFAL_SantoAnjo.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

st.write("---")
st.markdown("""<div class="footer-text">🛡️ Sistema de Apoio Fiscal - <b>Grupo Santo Anjo</b><br>👨‍💻 Desenvolvido por <b>Estevão Henrique</b></div>""", unsafe_allow_html=True)