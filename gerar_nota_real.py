import os

# Conteúdo de uma Nota Fiscal Realística (Interestadual)
conteudo_xml = """<?xml version="1.0" encoding="UTF-8"?>
<nfeProc xmlns="http://www.portalfiscal.inf.br/nfe" versao="4.00">
    <NFe>
        <infNFe versao="4.00" Id="NFe35230600000000000000550010000001011000001011">
            <ide>
                <cUF>35</cUF>
                <nNF>101</nNF>
            </ide>
            <emit>
                <xNome>FORNECEDOR DE SAO PAULO</xNome>
                <CRT>3</CRT>
            </emit>
            <dest>
                <UF>MG</UF>
            </dest>
            <det nItem="1">
                <prod>
                    <CFOP>6102</CFOP>
                </prod>
            </det>
            <total>
                <ICMSTot>
                    <vNF>1000.00</vNF>
                </ICMSTot>
            </total>
        </infNFe>
    </NFe>
</nfeProc>"""

# Salva o arquivo com o nome correto
with open("NOTA_PARA_LORRAYNE.xml", "w", encoding="utf-8") as f:
    f.write(conteudo_xml)

print("✅ Arquivo 'NOTA_PARA_LORRAYNE.xml' criado com sucesso!")