import os

pasta = 'NOTAS_FISCAIS_XML'
os.makedirs(pasta, exist_ok=True)

# 1. Nota de SP (Regime Normal - CRT 3) - COM DIFAL
xml1 = """<nfeProc xmlns="http://www.portalfiscal.inf.br/nfe"><NFe><infNFe><ide><cUF>35</cUF><nNF>101</nNF></ide><emit><xNome>FORNECEDOR SP NORMAL</xNome><CRT>3</CRT></emit><dest><UF>MG</UF></dest><det><prod><CFOP>6102</CFOP></prod></det><total><ICMSTot><vNF>1000.00</vNF></ICMSTot></total></infNFe></NFe></nfeProc>"""

# 2. Nota de RJ (Simples Nacional - CRT 1) - COM DIFAL
xml2 = """<nfeProc xmlns="http://www.portalfiscal.inf.br/nfe"><NFe><infNFe><ide><cUF>33</cUF><nNF>102</nNF></ide><emit><xNome>FORNECEDOR RJ SIMPLES</xNome><CRT>1</CRT></emit><dest><UF>MG</UF></dest><det><prod><CFOP>6102</CFOP></prod></det><total><ICMSTot><vNF>2000.00</vNF></ICMSTot></total></infNFe></NFe></nfeProc>"""

# 3. Nota de PR (Remessa - CFOP 6949) - SEM DIFAL
xml3 = """<nfeProc xmlns="http://www.portalfiscal.inf.br/nfe"><NFe><infNFe><ide><cUF>41</cUF><nNF>103</nNF></ide><emit><xNome>FORNECEDOR PR REMESSA</xNome><CRT>3</CRT></emit><dest><UF>MG</UF></dest><det><prod><CFOP>6949</CFOP></prod></det><total><ICMSTot><vNF>500.00</vNF></ICMSTot></total></infNFe></NFe></nfeProc>"""

# 4. Nota de MG (Interna - CFOP 5102) - SEM DIFAL
xml4 = """<nfeProc xmlns="http://www.portalfiscal.inf.br/nfe"><NFe><infNFe><ide><cUF>31</cUF><nNF>104</nNF></ide><emit><xNome>FORNECEDOR MG INTERNO</xNome><CRT>3</CRT></emit><dest><UF>MG</UF></dest><det><prod><CFOP>5102</CFOP></prod></det><total><ICMSTot><vNF>800.00</vNF></ICMSTot></total></infNFe></NFe></nfeProc>"""

# Criando os arquivos
notas = [xml1, xml2, xml3, xml4]
for i, conteudo in enumerate(notas):
    with open(f'{pasta}/nota_teste_{i+1}.xml', 'w') as f:
        f.write(conteudo)

print(f"Sucesso! Criamos 4 cenários diferentes na pasta '{pasta}'!")