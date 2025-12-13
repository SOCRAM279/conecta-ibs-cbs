# Conecta IBS/CBS 📊

Sistema de Classificação Tributária Automática para códigos IBS/CBS com preenchimento completo de todos os campos.

## 📋 Descrição

O **Conecta IBS/CBS** é uma aplicação web desenvolvida com Streamlit que automatiza completamente o processo de classificação tributária de produtos e serviços. O sistema analisa sua planilha de itens, consulta a tabela oficial de códigos IBS/CBS, faz web scraping da Lei Complementar 214, e preenche **TODOS os campos tributários automaticamente**.

## ✨ Funcionalidades

- **Upload Intuitivo**: Interface amigável para upload de 2 arquivos obrigatórios
- **Termo de Referência Automático**: Consulta automática da Lei Complementar 214 do Planalto
- **Mapeamento NCM → CST**: Determina automaticamente o CST baseado no NCM do produto
- **Classificação Inteligente**: 
  - Determina CST se não fornecido
  - Substitui códigos genéricos "000001" por códigos específicos baseados em NCM
  - Calcula reduções IBS/CBS por categoria de produto
  - Define tipo de alíquota automaticamente
- **Preenchimento Completo**: Preenche automaticamente:
  - ✅ **CST-IBS/CBS** - Código de Situação Tributária
  - ✅ **cClassTrib** - Código de Classificação Tributária específico
  - ✅ **pRedIBS** - Percentual de Redução IBS
  - ✅ **pRedCBS** - Percentual de Redução CBS
  - ✅ **tipoAliquota** - Tipo de Alíquota (Normal, Reduzida, Isento, etc.)
- **Tratamento de Exceções**: Identifica e sinaliza itens que precisam revisão
- **Relatório Detalhado**: Estatísticas de confiança e observações
- **Download Formatado**: Planilha Excel completa com todos os dados
- **Cache Inteligente**: Lei Complementar mantida em cache por 1 hora

## 🎨 Design

Interface desenvolvida com as cores da marca:
- **Laranja**: #FF6B35 (botões e destaques)
- **Cinza**: #808080 (elementos secundários)
- **Preto**: #000000 (textos principais)

## 🚀 Instalação

### Pré-requisitos

- Python 3.8 ou superior
- pip (gerenciador de pacotes Python)

### Passos

1. **Instale as dependências**:
```bash
pip install -r requirements.txt
```

## ▶️ Como Usar

1. **Inicie a aplicação**:
```bash
streamlit run app.py
```

Ou via Python:
```bash
python -m streamlit run app.py
```

2. **Acesse no navegador**: A aplicação abrirá automaticamente

3. **Faça upload dos arquivos**:
   - **Planilha de Itens** (obrigatório): Seus produtos/serviços em formato .xlsx ou .csv
   - **Tabela Oficial** (obrigatório): Tabela oficial com códigos IBS/CBS em formato .xlsx ou .csv
   - **Termo de Referência**: Carregado automaticamente do site do Planalto

4. **Clique em "Classificar Itens"** 
   - O sistema buscará automaticamente a Lei Complementar 214 
   - Determinará CST por NCM se necessário
   - Substituirá códigos genéricos por específicos
   - Calculará reduções automaticamente
   - Preencherá todos os campos tributários

5. **Baixe o resultado**: Planilha Excel com a classificação completa

## 📊 Como Funciona

### Determinação de CST

O sistema usa um mapeamento NCM → CST inteligente:
- NCM 02** (Carnes) → CST 200 (Alíquota reduzida)
- NCM 2203** (Cervejas) → CST 620 (Monofásica)
- NCM 2201** (Águas) → CST 410 (Não incidência)
- NCM 2402** (Cigarros) → CST 620 (Monofásica)
- E muito mais...

### Cálculo de Reduções

Reduções aplicadas automaticamente por categoria:
- **Carnes (NCM 02)**: 60% IBS + 60% CBS
- **Leite (NCM 04)**: 60% IBS + 60% CBS
- **Cereais (NCM 10)**: 60% IBS + 60% CBS
- **Águas (NCM 2201)**: 100% IBS + 100% CBS (isento)
- **Tributação normal**: 0% (sem redução)

### Substituição de Códigos Genéricos

Se sua planilha tem `cClassTrib = "000001"` (genérico), o sistema automaticamente:
1. Verifica se há NCM válido
2. Usa o próprio NCM como cClassTrib específico
3. Marca na coluna Observações a substituição feita

## 📁 Formato dos Arquivos

### Planilha de Itens

Deve conter pelo menos:
- **Produto/Descrição**: Nome do produto
- **NCM**: Código NCM (8 dígitos)

Opcionalmente:
- **CST IBS/CBS**: Se já souber (senão será determinado automaticamente)
- **cCLASS**: Código de classificação (se genérico será substituído)

### Tabela Oficial

Deve conter a tabela CST oficial com as colunas:
- CST-IBS/CBS
- Descrição CST-IBS/CBS
- Indicadores diversos

## 📊 Interpretando os Resultados

A planilha gerada conterá:

**Todas as colunas originais** + **Colunas tributárias**:
- `CST_IBS_CBS`: Código de Situação Tributária
- `cClassTrib`: Código de Classificação específico
- `pRedIBS`: Percentual de Redução IBS (0, 60, ou 100)
- `pRedCBS`: Percentual de Redução CBS (0, 60, ou 100)
- `tipoAliquota`: Tipo (Normal, Reduzida, Isento, Monofásica, etc.)
- `Observacoes`: Como foi determinado cada campo
- `Confianca`: Alta (dados fornecidos) ou Média (determinado por NCM)

## ⚠️ Observações Importantes

- Itens com confiança Média devem ser revisados para confirmar a classificação
- O sistema usa o NCM como fonte principal para determinação automática
- Códigos genéricos "000001" são automaticamente substituídos
- Percentuais de redução baseados na Lei Complementar 214

## 🛠️ Tecnologias Utilizadas

- **Streamlit**: Framework web para Python
- **Pandas**: Manipulação e análise de dados
- **OpenPyXL**: Leitura e escrita de arquivos Excel
- **BeautifulSoup + Requests**: Web scraping da Lei 214
- **XlRD**: Suporte para formatos Excel legados

## 📝 Solução de Problemas

### A aplicação não inicia
- Verifique se todas as dependências foram instaladas: `pip install -r requirements.txt`
- Confirme que está usando Python 3.8+: `python --version`

### Erro ao fazer upload
- Verifique se o arquivo está no formato correto (.xlsx ou .csv)
- Certifique-se de que o arquivo não está corrompido

### CST determinado incorretamente
- Verifique se o NCM está correto e completo (8 dígitos)
- Produtos sem NCM recebem CST padrão "000"
- Você pode fornecer o CST manualmente na planilha de entrada

### Reduções não aplicadas
- Verifique se o produto está na categoria correta (NCM)
- Alguns produtos não têm redução prevista em lei

---

**Conecta IBS/CBS** - Simplificando a classificação tributária com automação completa! 🚀
