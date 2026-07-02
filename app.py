import streamlit as st
import pandas as pd
import xml.etree.ElementTree as ET
from io import BytesIO
import os

# Configuração da página - GRUPO SANTO ANJO
st.set_page_config(page_title="DIFAL Grupo Santo Anjo", page_icon="👼", layout="wide")

# Estilo Profissional
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
st.sidebar.info("🎯 **Inteligência Fiscal**\n\nEste sistema processa apenas as Invasões Fiscais Reais para garantir 100% de precisão nos nomes e cálculos.")

st.title("🎯 Identificador Automático de DIFAL")
st.markdown("#### Grupo Santo Anjo - Processamento de Notas Fiscais Eletrônicas")
st.write("---")

def processar_xml(arquivo):
    try:
        # Lê o arquivo
        conteudo = arquivo.read()
        root = ET.fromstring(conteudo)
        ns = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}
        
        # --- FILTRO DE SEGURANÇA: Só processa Notas Fiscais (NFe ou procNFe) ---
        # Se for Evento, Canc, Ciência, o robô vai retornar None para não "sujar" o Excel
        tag_root = root.tag
        if "procEvento" in tag_root or "retEvento" in tag_root or "evento" in tag_root.lower():
            return None 

        # --- COLETA DE DADOS FISCAIS ---
        # Nome do Fornecedor (Focado estritamente na tag EMITENTE)
        fornecedor = "FORNECEDOR NÃO ENCONTRADO"
        emitente = root.find('.//nfe:emit', ns)
        if emitente is not None:
            node_nome = emitente.find('nfe:xNome', ns)
            if node_nome is not None:
                fornecedor = node_nome.text

        nf_node = root.find('.//nfe:nNF', ns)
        valor_node = root.find('.//nfe:vNF', ns)
        cfop_node = root.find('.//nfe:det/nfe:prod/nfe:CFOP', ns)
        uf_orig_node = root.find('.//nfe:cUF', ns)
        uf_dest_node = root.find('.//nfe:dest/nfe:UF', ns)
        crt_node = root.find('.//nfe:CRT', ns)

        if nf_node is None or valor_node is None:
            return None # Ignora se não tiver o básico de uma nota

        nf = nf_node.text
        valor_nf = float(valor_node.text)
        cfop = cfop_node.text if cfop_node is not None else "0000"
        crt = crt_node.text if crt_node is not None else "3"
        
        # Lógica Fiscal de MG
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
            percentual = 0.0735 # 7.35% fixo conforme combinado
            tratativa = 'Gerar e recolher guia de DIFAL para o estado de MG'
            if crt == "1":
                justificativa = 'Venda Interestadual - Fornecedor Simples Nacional (DIFAL recolhido pelo comprador)'
            else:
                justificativa = 'Venda Interestadual - Fornecedor Regime Normal'
        else:
            justificativa = 'Outras operações/Devolução'

        dif_aliq = round(valor_nf * percentual, 2)
        
        return {
            'NF': nf, 'FORNECEDOR': fornecedor, 'VALOR NF': valor_nf,
            '%': f"{percentual*100:.2f}%", 'DIF ALIQUOTA': dif_aliq,
            'VALOR REAL': round(valor_nf + dif_aliq, 2),
            'JUSTIFICATIVA': justificativa, 'TRATATIVA': tratativa
        }
    except:
        return None

# --- INTERFACE DE LANÇAMENTO ---
arquivos_xml = st.file_uploader("📥 Arraste TODOS os seus XMLs aqui", type=['xml'], accept_multiple_files=True)

if arquivos_xml:
    dados_totais = []
    
    for xml in arquivos_xml:
        res = processar_xml(xml)
        if res:
            dados_totais.append(res)
    
    if dados_totais:
        df = pd.DataFrame(dados_totais)
        # Tira as duplicatas se a mesma nota foi enviada duas vezes
        df = df.drop_duplicates(subset=['NF', 'FORNECEDOR', 'VALOR NF'])
        
        st.success(f"📊 Relatório gerado! {len(df)} Notas Fiscais identificadas com sucesso.")
        st.dataframe(df, use_container_width=True)

        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='DIFAL')
        
        st.download_button(label="💾 Baixar Relatório Grupo Santo Anjo", data=output.getvalue(), file_name="Relatorio_DIFAL_Limpo_SantoAnjo.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else:
        st.error("Nenhuma Nota Fiscal Real (procNFe) foi encontrada no lote de arquivos enviado.")

# RODAPÉ COM TEUS CRÉDITOS
st.markdown("""<div class="footer-text">🛡️ Apoio Fiscal - <b>Grupo Santo Anjo</b> | 👨‍💻 Desenvolvido por <b>Estevão Henrique</b></div>""", unsafe_allow_html=True)