import streamlit as st
import pandas as pd
import xml.etree.ElementTree as ET
from io import BytesIO
import os

# Configuração Institucional - Grupo Santo Anjo
st.set_page_config(page_title="Auditoria DIFAL - Grupo Santo Anjo", page_icon="🛡️", layout="wide")

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

if os.path.exists("logo.png"):
    st.sidebar.image("logo.png", use_container_width=True)

st.sidebar.divider()
st.sidebar.markdown("### 📊 Status: Modo Auditoria")
st.sidebar.info("Modo de conferência total (1 arquivo enviado = 1 linha na tabela).")

st.title("🎯 Identificador Inteligente de DIFAL")
st.markdown("#### Divisão de Apoio Fiscal — **Grupo Santo Anjo**")
st.write("---")

def processar_xml(arquivo):
    nome_do_arquivo = arquivo.name
    try:
        conteudo = arquivo.read()
        root = ET.fromstring(conteudo)
        ns = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}
        tag_root = root.tag

        # --- CASO 1: ARQUIVO DE EVENTO ---
        if "procEvento" in tag_root or "retEvento" in tag_root or "evento" in tag_root.lower():
            ch_node = root.find('.//nfe:chNFe', ns)
            ev_node = root.find('.//nfe:xEvento', ns)
            chave = ch_node.text if ch_node is not None else "N/A"
            evento = ev_node.text if ev_node is not None else "Evento/Ciência"
            
            return {
                'ARQUIVO': nome_do_arquivo, 'SITUAÇÃO': "INFORMATIVO", 'NF': 'EVENTO',
                'FORNECEDOR': f"Chave: {chave}", 'VALOR NF': 0.0,
                '%': "0.00%", 'VLR DIFAL': 0.0, 'TOTAL REAL': 0.0,
                'JUSTIFICATIVA': f"Log: {evento}", 'PROCEDIMENTO': "Manter arquivado"
            }

        # --- CASO 2: NOTA FISCAL (procNFe) ---
        nf_node = root.find('.//nfe:nNF', ns)
        if nf_node is not None:
            emit = root.find('.//nfe:emit', ns)
            forn = emit.find('nfe:xNome', ns).text if emit is not None else "NOME NÃO ENCONTRADO"
            v_nf = float(root.find('.//nfe:vNF', ns).text)
            cfop = root.find('.//nfe:det/nfe:prod/nfe:CFOP', ns).text
            
            # Mapeamento UFs
            map_ufs = {'11':'RO','12':'AC','13':'AM','14':'RR','15':'PA','16':'AP','17':'TO','21':'MA','22':'PI','23':'CE','24':'RN','25':'PB','26':'PE','27':'AL','28':'SE','29':'BA','31':'MG','32':'ES','33':'RJ','35':'SP','41':'PR','42':'SC','43':'RS','50':'MS','51':'MT','52':'GO','53':'DF'}
            u_orig = map_ufs.get(root.find('.//nfe:cUF', ns).text, '??')
            u_dest = root.find('.//nfe:dest/nfe:UF', ns).text if root.find('.//nfe:dest/nfe:UF', ns) is not None else "??"

            perc = 0.0
            situ = "ISENTO"
            trata = "OK"
            remessas = ['6923', '6949', '6910', '6808', '6902', '6911', '6912', '6917']

            if u_orig == u_dest:
                just = f"Interna ({u_orig}-{u_dest})"
            elif cfop in remessas:
                just = f"Remessa (CFOP {cfop})"
            elif cfop.startswith('6'):
                perc = 0.0735
                situ = "DIFAL"
                trata = "CALCULAR GUIA"
                just = "Interestadual (Pagar DIFAL)"
            else:
                just = f"CFOP {cfop}"

            v_difal = round(v_nf * perc, 2)
            return {
                'ARQUIVO': nome_do_arquivo, 'SITUAÇÃO': situ, 'NF': nf_node.text, 
                'FORNECEDOR': forn, 'VALOR NF': v_nf,
                '%': f"{perc*100:.2f}%", 'VLR DIFAL': v_difal,
                'TOTAL REAL': round(v_nf + v_difal, 2),
                'JUSTIFICATIVA': just, 'PROCEDIMENTO': trata
            }

        return {'ARQUIVO': nome_do_arquivo, 'SITUAÇÃO': "XML INVÁLIDO", 'NF': '-', 'FORNECEDOR': '-', 'VALOR NF': 0.0, '%': '0%', 'VLR DIFAL': 0, 'TOTAL REAL': 0, 'JUSTIFICATIVA': 'Fora do padrão SEFAZ', 'PROCEDIMENTO': '-'}
    except:
        return {'ARQUIVO': nome_do_arquivo, 'SITUAÇÃO': "ERRO", 'NF': '-', 'FORNECEDOR': 'Falha na leitura', 'VALOR NF': 0.0, '%': '0%', 'VLR DIFAL': 0, 'TOTAL REAL': 0, 'JUSTIFICATIVA': 'Erro técnico', 'PROCEDIMENTO': '-'}

# Área de Upload
xmls_subidos = st.file_uploader("📥 Arraste os XMLs (conferência 1:1 habilitada)", type=['xml'], accept_multiple_files=True)

if xmls_subidos:
    resultado_final = []
    for x in xmls_subidos:
        resultado_final.append(processar_xml(x))
    
    if resultado_final:
        df = pd.DataFrame(resultado_final)
        
        total_arquivos = len(df)
        total_difal = len(df[df['SITUAÇÃO'] == "DIFAL"])
        
        st.success(f"✅ Análise de {total_arquivos} arquivos concluída! ({total_difal} notas de DIFAL identificadas)")

        # Mostra a tabela (usando .map que é compatível com versões novas)
        def destacar_difal(val):
            if val == 'DIFAL': return 'background-color: #fff2f2; color: #721c24; font-weight: bold'
            if val == 'INFORMATIVO': return 'color: #95a5a6'
            return ''

        # Renderização simples para evitar erros de versão do Pandas
        st.dataframe(df, use_container_width=True)

        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Auditoria_Total')
        
        st.download_button(
            label=f"💾 Baixar Relatório com {total_arquivos} Linhas",
            data=output.getvalue(),
            file_name=f"Relatorio_Total_68_arquivos.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# Rodapé Institucional
st.markdown("""<div class="footer-text">© 2026 Grupo Santo Anjo — Tecnologia de Apoio à Gestão Fiscal | Auditoria 1:1 habilitada</div>""", unsafe_allow_html=True)