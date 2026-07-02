import os
import xml.etree.ElementTree as ET
import pandas as pd
from tkinter import filedialog, Tk, messagebox

def selecionar_pasta():
    root = Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    pasta = filedialog.askdirectory(title='Selecione a pasta com os XMLs')
    root.destroy()
    return pasta

def extrair_dados_xml(caminho_xml):
    try:
        tree = ET.parse(caminho_xml)
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
            justificativa = f'Venda Interestadual - Fornecedor {"Simples Nacional" if crt=="1" else "Regime Normal"}'
        else:
            justificativa = 'Outras operações'

        dif_aliquota = valor_nf * percentual
        return {
            'NF': nf, 'FORNECEDOR': fornecedor, 'VALOR DA NF': valor_nf,
            '%': f"{percentual*100:.2f}%", 'DIF ALIQUOTA': round(dif_aliquota, 2),
            'VALOR REAL': round(valor_nf + dif_aliquota, 2),
            'JUSTIFICATIVA': justificativa, 'TRATATIVA': tratativa
        }
    except: return None

def iniciar():
    pasta = selecionar_pasta()
    if not pasta: return
    arquivos = [os.path.join(pasta, f) for f in os.listdir(pasta) if f.lower().endswith('.xml')]
    if not arquivos:
        messagebox.showwarning("Aviso", "Nenhum XML encontrado!")
        return
    dados = [res for res in [extrair_dados_xml(a) for a in arquivos] if res]
    pd.DataFrame(dados).to_excel('Relatorio_Controle_DIFAL.xlsx', index=False)
    messagebox.showinfo("Sucesso", "Relatório Gerado!")
    os.startfile(os.getcwd())

if __name__ == "__main__":
    iniciar()