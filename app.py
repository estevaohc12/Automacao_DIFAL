import streamlit as st
import pandas as pd
import xml.etree.ElementTree as ET
from io import BytesIO

# Configuração da página
st.set_page_config(page_title="Automação DIFAL MG", page_icon="📊", layout="wide")

st.title("🚀 Automação de Controle de DIFAL - MG")
st.markdown("### Transforme seus XMLs de NF-e em planilhas de controle instantaneamente.")

# Função de extração (a mesma lógica do seu robô anterior)
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
        
        return {
            'NF': nf, 'FORNECEDOR': fornecedor, 'VALOR NF': valor_nf,
            '%': f"{percentual*100:.2f}%", 'DIFAL': round(valor_nf * percentual, 2),
            'TOTAL': round(valor_nf * (1 + percentual), 2),
            'JUSTIFICATIVA': justificativa, 'TRATATIVA': tratativa
        }
    except: return None

# Área de Upload no site
st.sidebar.header("Configurações")
arquivos_xml = st.file_uploader("Arraste seus arquivos XML aqui", type=['xml'], accept_multiple_files=True)

if arquivos_xml:
    dados_finais = []
    for xml in arquivos_xml:
        resultado = processar_xml(xml)
        if resultado:
            dados_finais.append(resultado)
    
    if dados_finais:
        df = pd.DataFrame(dados_finais)
        
        # Exibe a tabela bonitona no navegador
        st.success(f"✅ {len(dados_finais)} notas processadas com sucesso!")
        st.dataframe(df, use_container_width=True)

        # Botão para baixar o Excel
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='DIFAL')
        
        st.download_button(
            label="📥 Baixar Planilha Excel",
            data=output.getvalue(),
            file_name="Relatorio_DIFAL_MG.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.error("Nenhum dado válido encontrado nos XMLs.")