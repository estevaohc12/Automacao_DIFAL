import streamlit as st
import pandas as pd
import xml.etree.ElementTree as ET
from io import BytesIO
import os

# Configuração Institucional
st.set_page_config(page_title="Auditoria Fiscal - Grupo Santo Anjo", page_icon="🛡️", layout="wide")

# Estilo Corporativo Minimalista
st.markdown("""
    <style>
    .main { background-color: #fcfcfc; }
    .stButton>button { width: 100%; border-radius: 5px; background-color: #2c3e50; color: white; font-weight: bold; }
    .footer-text { text-align: center; color: #95a5a6; padding: 20px; font-size: 0.8em; border-top: 1px solid #eee; margin-top: 50px; }
    </style>
    """, unsafe_allow_html=True)

if os.path.exists("logo.png"):
    st.sidebar.image("logo.png", use_container_width=True)

st.sidebar.divider()
st.sidebar.markdown("### 📊 Status: Modo Auditoria")
st.sidebar.info("Neste modo, todos os arquivos enviados são listados individualmente para conferência total (1 para 1).")

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

        # --- CASO 1: ARQUIVO DE EVENTO (CIÊNCIA, CORREÇÃO, ETC) ---
        if "procEvento" in tag_root or "retEvento" in tag_root or "evento" in tag_root.lower():
            chave_node = root.find('.//nfe:chNFe', ns)
            desc_node = root.find('.//nfe:xEvento', ns)
            chave = chave_node.text if chave_node is not None else "N/A"
            descricao = desc_node.text if desc_node is not None else "Registro de Evento"
            
            return {
                'ARQUIVO': nome_do_arquivo, 'SITUAÇÃO': "INFORMATIVO", 'NF': 'EVENTO',
                'FORNECEDOR': f"Chave: {chave}", 'VALOR NF': 0.0,
                '%': "0.00%", 'VLR DIFAL': 0.0, 'TOTAL REAL': 0.0,
                'JUSTIFICATIVA': f"LOG: {descricao}", 'PROCEDIMENTO': "Manter em arquivo"
            }

        # --- CASO 2: NOTA FISCAL (procNFe) ---
        nf_node = root.find('.//nfe:nNF', ns)
        if nf_node is not None:
            emitente = root.find('.//nfe:emit', ns)
            fornecedor = emitente.find('nfe:xNome', ns).text if emitente is not None else "NOME NÃO ENCONTRADO"
            nf = nf_node.text
            valor_nf = float(root.find('.//nfe:vNF', ns).text)
            cfop = root.find('.//nfe:det/nfe:prod/nfe:CFOP', ns).text
            crt = root.find('.//nfe:CRT', ns).text if root.find('.//nfe:CRT', ns) is not None else "3"
            
            mapa_ufs = {'11':'RO','12':'AC','13':'AM','14':'RR','15':'PA','16':'AP','17':'TO','21':'MA','22':'PI','23':'CE','24':'RN','25':'PB','26':'PE','27':'AL','28':'SE','29':'BA','31':'MG','32':'ES','33':'RJ','35':'SP','41':'PR','42':'SC','43':'RS','50':'MS','51':'MT','52':'GO','53':'DF'}
            uf_origem = mapa_ufs.get(root.find('.//nfe:cUF', ns).text, '??')
            uf_destino = root.find('.//nfe:dest/nfe:UF', ns).text if root.find('.//nfe:dest/nfe:UF', ns) is not None else "??"

            # Lógica DIFAL
            percentual = 0.0
            status_situacao = "ISENTO"
            tratativa = "Sem ações"
            cfops_remessa = ['6923', '6949', '6910', '6808', '6902', '6911', '6912', '6917']

            if uf_origem == uf_destino:
                justificativa = f"Interna ({uf_origem}-{uf_destino})"
            elif cfop in cfops_remessa:
                justificativa = f"Remessa/Outros (CFOP {cfop})"
            elif cfop.startswith('6'):
                percentual = 0.0735
                status_situacao = "DIFAL"
                tratativa = "CALCULAR GUIA"
                justificativa = f"Interestadual (Forn. CRT {crt})"
            else:
                justificativa = f"Análise Manual (CFOP {cfop})"

            dif_aliq = round(valor_nf * percentual, 2)
            
            return {
                'ARQUIVO': nome_do_arquivo, 'SITUAÇÃO': status_situacao, 'NF': nf, 
                'FORNECEDOR': fornecedor, 'VALOR NF': valor_nf,
                '%': f"{percentual*100:.2f}%", 'VLR DIFAL': dif_aliq,
                'TOTAL REAL': round(valor_nf + dif_aliq, 2),
                'JUSTIFICATIVA': justificativa, 'PROCEDIMENTO': tratativa
            }

        # --- CASO 3: ARQUIVO ESTRANHO ---
        return {
            'ARQUIVO': nome_do_arquivo, 'SITUAÇÃO': "NÃO RECONHECIDO", 'NF': '-',
            'FORNECEDOR': "Estrutura XML fora do padrão SEFAZ", 'VALOR NF': 0.0,
            '%': "0.00%", 'VLR DIFAL': 0.0, 'TOTAL REAL': 0.0,
            'JUSTIFICATIVA': "Arquivo não processável pelo motor DIFAL", 'PROCEDIMENTO': "Verificar manual"
        }

    except Exception as e:
        return {
            'ARQUIVO': nome_do_arquivo, 'SITUAÇÃO': "ERRO", 'NF': '-',
            'FORNECEDOR': f"Falha na leitura", 'VALOR NF': 0.0,
            '%': "0.00%", 'VLR DIFAL': 0.0, 'TOTAL REAL': 0.0,
            'JUSTIFICATIVA': f"Erro: {str(e)[:50]}", 'PROCEDIMENTO': "Ignorar arquivo"
        }

# Upload
arquivos_xml = st.file_uploader("📥 Carregue os XMLs para Auditoria Total", type=['xml'], accept_multiple_files=True)

if arquivos_xml:
    lista_final = []
    for xml in arquivos_xml:
        lista_final.append(processar_xml(xml))
    
    if lista_final:
        df = pd.DataFrame(lista_final)
        
        n_total = len(df)
        n_difal = len(df[df['SITUAÇÃO'] == "DIFAL"])
        
        st.success(f"Concluído: {n_total} arquivos analisados. (Sendo {n_difal} registros de DIFAL).")
        
        # Colorir DIFAL em Vermelho claro e INFORMATIVO em cinza
        def colorir_tabela(val):
            if val == 'DIFAL': return 'background-color: #fff2f2; color: #721c24; font-weight: bold'
            if val == 'INFORMATIVO': return 'color: #95a5a6'
            return ''

        st.dataframe(df.style.applymap(colorir_tabela, subset=['SITUAÇÃO']), use_container_width=True)

        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Auditoria_Completa')
        
        st.download_button(
            label=f"💾 Baixar Relatório de {n_total} Itens (.xlsx)",
            data=output.getvalue(),
            file_name=f"Relatorio_Auditoria_GrupoSantoAnjo.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# Rodapé Institucional
st.markdown("""<div class="footer-text">© 2026 Grupo Santo Anjo — Tecnologia de Apoio à Gestão Fiscal | Auditoria 1:1 habilitada</div>""", unsafe_allow_html=True)