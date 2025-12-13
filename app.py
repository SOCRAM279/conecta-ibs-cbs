import streamlit as st
import pandas as pd
import io
from datetime import datetime
import openpyxl
import requests
from bs4 import BeautifulSoup
import time

# Configuração da página
st.set_page_config(
    page_title="Conecta IBS/CBS",
    page_icon="📊",
    layout="wide"
)

# ============================================================================
# AUTENTICAÇÃO
# ============================================================================

# Dicionário de usuários e senhas
USERS = {
    "Conecta": "Conecta%$#@!2025",
    "Wesley": "Wesley%$#@!2025"
}

def check_password():
    """Retorna True se o usuário/senha estiverem corretos."""
    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["username"] in USERS and st.session_state["password"] == USERS[st.session_state["username"]]:
            st.session_state["authenticated"] = True
            del st.session_state["password"]  # Não manter senha na sessão
            del st.session_state["username"]
        else:
            st.session_state["authenticated"] = False

    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if not st.session_state["authenticated"]:
        # CSS específico para a tela de login
        st.markdown("""
        <style>
        .stTextInput > div > div > input {
            background-color: #f0f2f6;
            color: #000000;
        }
        .main {
            background-color: #f5f5f5;
        }
        .login-box {
            padding: 2rem;
            border-radius: 10px;
            background-color: white;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            max-width: 400px;
            margin: 0 auto;
        }
        h1 {
            color: #FF6B35 !important;
            text-align: center;
        }
        .stButton button {
            background-color: #FF6B35;
            color: white;
            width: 100%;
        }
        </style>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("<br><br>", unsafe_allow_html=True)
            st.title("🔒 Conecta IBS/CBS")
            st.markdown("### Acesso Restrito")
            
            st.text_input("Usuário", key="username")
            st.text_input("Senha", type="password", key="password")
            st.button("Entrar", on_click=password_entered)
            
            if "authenticated" in st.session_state and st.session_state["authenticated"] == False:
                st.error("Usuário ou senha incorretos")
            
            st.markdown("<br><br><br>", unsafe_allow_html=True)
            
        return False
    
    return True

# Verificar autenticação antes de carregar o resto do app
if not check_password():
    st.stop()

# ============================================================================
# APP PRINCIPAL (Carrega apenas se autenticado)
# ============================================================================

# Mapeamento NCM → CST
NCM_CST_MAP = {
    # Carnes e derivados
    "02": "200",  # Carnes - alíquota reduzida
    
    # Bebidas alcoólicas
    "2203": "620",  # Cervejas - tributação monofásica
    "2204": "000",  # Vinhos
    "2205": "000",  # Vermute
    "2206": "000",  # Outras bebidas fermentadas
    "2207": "620",  # Álcool etílico - monofásica
    "2208": "620",  # Destilados - monofásica
    
    # Bebidas não alcoólicas
    "2201": "410",  # Águas - possível não incidência
    "2202": "000",  # Refrigerantes - tributação normal
    "2209": "000",  # Vinagres
    
    # Tabaco
    "2402": "620",  # Cigarros - tributação monofásica
    "2403": "620",  # Outros tabacos
    
    # Cereais e farinhas
    "10": "200",  # Cereais - alíquota reduzida
    "11": "200",  # Farinhas - alíquota reduzida
    "19": "000",  # Produtos de padaria
    
    # Açúcares
    "17": "000",  # Açúcares e confeitaria
    
    # Óleos
    "15": "000",  # Óleos e gorduras
    
    # Laticínios
    "04": "200",  # Leite e laticínios - possível redução
    
    # Plásticos
    "39": "000",  # Plásticos
    
    # Outros
    "21": "000",  # Preparações alimentícias diversas
    "22": "000",  # Bebidas em geral (fallback)
}

# Tabela de reduções por categoria NCM
REDUCAO_MAP = {
    # Alimentos básicos (60% de redução)
    "02": {"pRedIBS": 60, "pRedCBS": 60},  # Carnes
    "04": {"pRedIBS": 60, "pRedCBS": 60},  # Leite
    "07": {"pRedIBS": 60, "pRedCBS": 60},  # Legumes
    "10": {"pRedIBS": 60, "pRedCBS": 60},  # Cereais
    "15070": {"pRedIBS": 60, "pRedCBS": 60},  # Óleo de soja
    
    # Água (100% - isento)
    "2201": {"pRedIBS": 100, "pRedCBS": 100},
    
    # Tributação normal (0%)
    "default": {"pRedIBS": 0, "pRedCBS": 0}
}

# Mapeamento CST → Tipo de Alíquota
TIPO_ALIQUOTA_MAP = {
    "000": "Normal",
    "010": "Uniforme",
    "011": "Uniforme Reduzida",
    "200": "Reduzida",
    "210": "Reduzida com Redutor",
    "220": "Fixa",
    "221": "Fixa Proporcional",
    "222": "Redução de BC",
    "400": "Isento",
    "410": "Não Incidência",
    "510": "Diferido",
    "550": "Suspenso",
    "620": "Monofásica",
    "800": "Transferência Crédito",
    "810": "Ajustes",
    "820": "Regime Específico",
    "830": "Exclusão de BC"
}

# ============================================================================
# CSS CUSTOMIZADO
# ============================================================================

st.markdown("""
    <style>
    /* Cores principais */
    :root {
        --primary-orange: #FF6B35;
        --secondary-gray: #808080;
        --primary-black: #000000;
    }
    
    /* Estilo geral */
    .stApp {
        background-color: #f5f5f5;
    }
    
    /* Título principal */
    h1 {
        color: #FF6B35 !important;
        font-weight: 700;
        text-align: center;
        padding: 20px 0;
    }
    
    h2, h3 {
        color: #000000 !important;
    }
    
    /* Botões principais */
    .stButton > button {
        background-color: #FF6B35;
        color: white;
        font-weight: 600;
        font-size: 18px;
        padding: 15px 30px;
        border-radius: 10px;
        border: none;
        width: 100%;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        background-color: #e65a2e;
        box-shadow: 0 4px 8px rgba(255, 107, 53, 0.3);
        transform: translateY(-2px);
    }
    
    /* Área de upload */
    .uploadedFile {
        background-color: white;
        border: 2px solid #FF6B35;
        border-radius: 8px;
        padding: 10px;
    }
    
    /* Cards */
    .upload-card {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 10px 0;
    }
    
    /* Mensagens de sucesso */
    .success-message {
        background-color: #d4edda;
        color: #155724;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #28a745;
        margin: 10px 0;
    }
    
    /* Progresso */
    .stProgress > div > div {
        background-color: #FF6B35;
    }
    
    /* Download button */
    .stDownloadButton > button {
        background-color: #28a745;
        color: white;
        font-weight: 600;
        padding: 12px 25px;
        border-radius: 8px;
        border: none;
    }
    
    .stDownloadButton > button:hover {
        background-color: #218838;
    }
    
    /* Info boxes */
    .info-box {
        background-color: #e8f4f8;
        color: #000000 !important;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #FF6B35;
        margin: 15px 0;
    }
    
    .info-box h3, .info-box h4, .info-box p {
        color: #000000 !important;
    }
    
    .info-box a {
        color: #FF6B35 !important;
        text-decoration: underline;
    }
    
    /* Streamlit native alerts - force black text on light backgrounds */
    .stAlert {
        color: #000000 !important;
    }
    
    .stSuccess, .stWarning, .stInfo {
        color: #000000 !important;
    }
    
    .stSuccess > div, .stWarning > div, .stInfo > div {
        color: #000000 !important;
    }
    
    /* All paragraphs in light backgrounds */
    .element-container p {
        color: #000000;
    }
    
    /* Expander content */
    .streamlit-expanderContent {
        color: #000000 !important;
    }
    
    /* Métricas do Streamlit - FORÇAR TEXTO PRETO */
    .stMetric {
        color: #000000 !important;
    }
    
    .stMetric label, .stMetric [data-testid="stMetricLabel"] {
        color: #000000 !important;
    }
    
    .stMetric [data-testid="stMetricValue"] {
        color: #000000 !important;
    }
    
    .stMetric [data-testid="stMetricDelta"] {
        color: #000000 !important;
    }
    
    /* Captions e textos pequenos - MAS NÃO dentro do uploader */
    .upload-card .stCaption {
        color: #000000 !important;
    }
    
    /* Info, success, warning messages */
    [data-testid="stMarkdownContainer"] p {
        color: #000000 !important;
    }
    
    /* Forçar labels - EXCETO dentro do file uploader */
    label:not([data-testid*="fileUploader"] label) {
        color: #000000 !important;
    }
    
    /* Markdown containers - EXCETO file uploader */
    .stMarkdown p:not(.stFileUploader p), 
    .stMarkdown span:not(.stFileUploader span), 
    .stMarkdown div:not(.stFileUploader div) {
        color: #000000 !important;
    }
    
    /* Área de FILE UPLOADER - Permitir texto BRANCO (fundo escuro) */
    [data-testid="stFileUploader"] {
        color: inherit !important;
    }
    
    [data-testid="stFileUploader"] label,
    [data-testid="stFileUploader"] span,
    [data-testid="stFileUploader"] div,
    [data-testid="stFileUploader"] p {
        color: inherit !important;
    }
    
    .stFileUploader section {
        color: #FFFFFF !important;
    }
    
    .stFileUploader section small {
        color: #CCCCCC !important;
    }
    
    /* ARQUIVO UPLOADADO (fundo claro) - Texto PRETO */
    .uploadedFile {
        background-color: white !important;
        color: #000000 !important;
        border: 2px solid #FF6B35;
        border-radius: 8px;
        padding: 10px;
    }
    
    .uploadedFile span,
    .uploadedFile div,
    .uploadedFile button {
        color: #000000 !important;
    }
    
    [data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"] + div {
        color: #000000 !important;
    }
    
    [data-testid="stFileUploader"] section + div span {
        color: #000000 !important;
    }
    </style>
""", unsafe_allow_html=True)

# Header
st.title("📊 Conecta IBS/CBS")
st.markdown("""
<div class="info-box">
    <h3 style="margin-top: 0;">Sistema de Classificação Tributária Automática</h3>
    <p>Faça upload de seus arquivos e receba automaticamente a classificação dos códigos tributários IBS/CBS 
    com base na tabela oficial. O sistema identifica o código mais específico para cada item e preenche 
    <strong>TODOS os campos tributários</strong> automaticamente!</p>
</div>
""", unsafe_allow_html=True)

# Inicializar session state
if 'processed' not in st.session_state:
    st.session_state.processed = False
if 'result_df' not in st.session_state:
    st.session_state.result_df = None
if 'result_filename' not in st.session_state:
    st.session_state.result_filename = None

# Seção de Upload
st.markdown("---")
st.header("1️⃣ Upload dos Arquivos")

col1, col2 = st.columns(2)

with col1:
    st.markdown('<div class="upload-card">', unsafe_allow_html=True)
    st.subheader("📋 Planilha de Itens")
    st.caption("Seus produtos/serviços")
    planilha_itens = st.file_uploader(
        "Upload (.xlsx ou .csv)",
        type=['xlsx', 'csv'],
        key='planilha_itens',
        help="Tabela com os itens que você deseja classificar"
    )
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="upload-card">', unsafe_allow_html=True)
    st.subheader("📑 Tabela Oficial")
    st.caption("Códigos IBS/CBS oficiais")
    tabela_oficial = st.file_uploader(
        "Upload (.xlsx ou .csv)",
        type=['xlsx', 'csv'],
        key='tabela_oficial',
        help="Tabela oficial com códigos cClassTrib e CST"
    )
    st.markdown('</div>', unsafe_allow_html=True)

# Informação sobre o Termo de Referência automático
st.markdown("""<div class="info-box" style="margin-top: 20px;">
    <h4 style="margin-top: 0;">📖 Termo de Referência Automático</h4>
    <p>✅ O sistema consulta automaticamente a <strong>Lei Complementar 214</strong> do Planalto em tempo real.</p>
    <p style="font-size: 13px; margin-bottom: 0;">🔗 Fonte: <a href="https://www.planalto.gov.br/ccivil_03/leis/lcp/lcp214.htm" target="_blank">planalto.gov.br/ccivil_03/leis/lcp/lcp214.htm</a></p>
</div>""", unsafe_allow_html=True)

# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

@st.cache_data(ttl=3600)  # Cache por 1 hora
def fetch_termo_referencia():
    """Faz web scraping da Lei Complementar 214 do Planalto"""
    url = "https://www.planalto.gov.br/ccivil_03/leis/lcp/lcp214.htm"
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'utf-8'
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'lxml')
            # Extrair todo o texto da lei
            texto_lei = soup.get_text(separator=' ', strip=True)
            return texto_lei, True
        else:
            return f"Erro ao acessar o site: Status {response.status_code}", False
    except Exception as e:
        return f"Erro ao fazer web scraping: {str(e)}", False

def load_file(file):
    """Carrega um arquivo Excel ou CSV em um DataFrame"""
    try:
        if file.name.endswith('.csv'):
            return pd.read_csv(file)
        else:
            return pd.read_excel(file)
    except Exception as e:
        st.error(f"Erro ao carregar {file.name}: {str(e)}")
        return None

def determinar_cst_por_ncm(ncm, descricao=""):
    """Determina CST baseado no NCM do produto"""
    if pd.isna(ncm) or not ncm:
        return "000"  # Padrão
    
    ncm_str = str(ncm).replace(".", "").replace(",", "")
    
    # Tentar match com prefixos mais específicos primeiro (4 dígitos)
    for prefix_len in [4, 2]:
        prefix = ncm_str[:prefix_len]
        if prefix in NCM_CST_MAP:
            return NCM_CST_MAP[prefix]
    
    return "000"  # Padrão se não encontrar

def calcular_reducoes(cst, ncm):
    """Calcula pRedIBS e pRedCBS baseado em CST e NCM"""
    cst = str(cst).zfill(3)
    
    # CST específicos
    if cst == "000":  # Tributação integral
        return 0, 0
    elif cst in ["400", "410"]:  # Isenção/Imunidade
        return 100, 100
    elif cst == "200":  # Alíquota reduzida
        # Buscar redução específica por NCM
        if pd.isna(ncm) or not ncm:
            return 0, 0
            
        ncm_str = str(ncm).replace(".", "").replace(",", "")
        
        # Verificar mapeamentos específicos
        for prefix_len in [5, 4, 2]:
            prefix = ncm_str[:prefix_len]
            if prefix in REDUCAO_MAP:
                red = REDUCAO_MAP[prefix]
                return red["pRedIBS"], red["pRedCBS"]
        
        # Padrão para alíquota reduzida sem mapeamento específico
        return 0, 0
    else:
        # Outros CSTs
        return 0, 0

def definir_tipo_aliquota(cst):
    """Define tipo de alíquota baseado no CST"""
    cst = str(cst).zfill(3)
    return TIPO_ALIQUOTA_MAP.get(cst, "Normal")

def buscar_cclass_especifico(ncm, cclass_atual, descricao=""):
    """
    Determina cClassTrib específico
    - Se já tem um código válido (não "000001"), usa ele
    - Se é genérico, usa o próprio NCM
    """
    # Se já tem um cClassTrib específico (não genérico), mantém
    if cclass_atual and str(cclass_atual) not in ["000001", "000", ""] and not pd.isna(cclass_atual):
        return str(cclass_atual)
    
    # Se tem NCM, usa como cClassTrib
    if ncm and not pd.isna(ncm):
        ncm_str = str(ncm).replace(".", "").replace(",", "")
        if len(ncm_str) >= 8:
            return ncm_str[:8]
        return ncm_str
    
    # Fallback
    return "00000000"

def classificar_itens(df_itens, df_oficial):
    """
    Classifica os itens cruzando com a tabela oficial e preenchendo TODOS os campos
    Retorna o DataFrame com as colunas tributárias adicionadas
    """
    result_df = df_itens.copy()
    
    # Detectar nomes de colunas (case-insensitive e variations)
    col_map = {}
    for col in df_itens.columns:
        col_lower = col.lower()
        if any(x in col_lower for x in ['prod', 'desc', 'nome', 'item']):
            col_map['descricao'] = col
        elif 'ncm' in col_lower:
            col_map['ncm'] = col
        elif 'cst' in col_lower and 'ibs' in col_lower:
            col_map['cst'] = col
        elif 'class' in col_lower or 'cclas' in col_lower:
            col_map['cclass'] = col
    
    # Inicializar novas colunas
    result_df['CST_IBS_CBS'] = ''
    result_df['cClassTrib'] = ''
    result_df['pRedIBS'] = 0
    result_df['pRedCBS'] = 0
    result_df['tipoAliquota'] = ''
    result_df['Observacoes'] = ''
    result_df['Confianca'] = ''
    
    total_items = len(result_df)
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for idx, row in result_df.iterrows():
        # Atualizar progresso
        progress = (idx + 1) / total_items
        progress_bar.progress(progress)
        status_text.text(f"Processando {idx + 1} de {total_items} itens...")
        
        # Extrair dados do produto
        descricao = row.get(col_map.get('descricao', df_itens.columns[1] if len(df_itens.columns) > 1 else df_itens.columns[0]), "")
        ncm = row.get(col_map.get('ncm', 'NCM'), "")
        cst_atual = row.get(col_map.get('cst', 'CST IBS/CBS'), "")
        cclass_atual = row.get(col_map.get('cclass', 'cCLASS'), "")
        
        # 1. DETERMINAR CST
        if cst_atual and not pd.isna(cst_atual) and str(cst_atual).strip():
            cst = str(cst_atual).zfill(3)
            confianca = "Alta"
            obs = "CST fornecido na planilha"
        else:
            cst = determinar_cst_por_ncm(ncm, descricao)
            confianca = "Média"
            obs = f"CST determinado por NCM ({ncm})"
        
        # 2. DETERMINAR cClassTrib ESPECÍFICO
        cclass = buscar_cclass_especifico(ncm, cclass_atual, descricao)
        if str(cclass_atual) in ["000001", "000"]:
            obs += " | cClassTrib genérico substituído por NCM"
        
        # 3. CALCULAR REDUÇÕES
        pred_ibs, pred_cbs = calcular_reducoes(cst, ncm)
        
        # 4. DEFINIR TIPO DE ALÍQUOTA
        tipo_aliq = definir_tipo_aliquota(cst)
        
        # Preencher resultado
        result_df.at[idx, 'CST_IBS_CBS'] = cst
        result_df.at[idx, 'cClassTrib'] = cclass
        result_df.at[idx, 'pRedIBS'] = pred_ibs
        result_df.at[idx, 'pRedCBS'] = pred_cbs
        result_df.at[idx, 'tipoAliquota'] = tipo_aliq
        result_df.at[idx, 'Observacoes'] = obs
        result_df.at[idx, 'Confianca'] = confianca
    
    progress_bar.empty()
    status_text.empty()
    
    return result_df

# Botão de processamento
st.markdown("---")
st.header("2️⃣ Processar Classificação")

if planilha_itens and tabela_oficial:
    if st.button("🚀 Classificar Itens", use_container_width=True):
        with st.spinner("Carregando arquivos..."):
            df_itens = load_file(planilha_itens)
            df_oficial = load_file(tabela_oficial)
        
        if df_itens is not None and df_oficial is not None:
            st.success("✅ Arquivos carregados com sucesso!")
            
            # Buscar termo de referência via web scraping
            with st.spinner("🌐 Consultando Lei Complementar 214 do Planalto..."):
                termo_texto, termo_sucesso = fetch_termo_referencia()
                
                if termo_sucesso:
                    st.success("✅ Termo de referência carregado com sucesso!")
                    # Mostrar um preview do termo
                    with st.expander("📄 Preview do Termo de Referência (Lei Complementar 214)"):
                        st.text(termo_texto[:1000] + "..." if len(termo_texto) > 1000 else termo_texto)
                else:
                    st.warning(f"⚠️ Não foi possível carregar o termo de referência: {termo_texto}")
                    st.info("ℹ️ O sistema continuará a classificação com base na tabela oficial e mapeamentos NCM.")
            
            with st.spinner("Processando classificação completa..."):
                result_df = classificar_itens(df_itens, df_oficial)
            
            st.session_state.processed = True
            st.session_state.result_df = result_df
            
            # Gerar nome do arquivo com data/hora
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            st.session_state.result_filename = f"resultado_classificacao_{timestamp}.xlsx"
            
            st.success("✅ Classificação concluída com sucesso! Todos os campos foram preenchidos automaticamente!")
else:
    st.info("ℹ️ Por favor, faça upload dos dois arquivos obrigatórios (Planilha de Itens e Tabela Oficial) para continuar.")

# Seção de resultados
if st.session_state.processed and st.session_state.result_df is not None:
    st.markdown("---")
    st.header("3️⃣ Resultados da Classificação")
    
    result_df = st.session_state.result_df
    
    # Estatísticas
    col1, col2, col3, col4 = st.columns(4)
    
    total = len(result_df)
    alta_conf = len(result_df[result_df['Confianca'] == 'Alta'])
    media_conf = len(result_df[result_df['Confianca'] == 'Média'])
    
    # Contar produtos com redução
    com_reducao = len(result_df[result_df['pRedIBS'] > 0])
    
    with col1:
        st.metric("Total de Itens", total)
    with col2:
        st.metric("Alta Confiança", alta_conf, delta=f"{(alta_conf/total*100):.1f}%")
    with col3:
        st.metric("Média Confiança", media_conf, delta=f"{(media_conf/total*100):.1f}%")
    with col4:
        st.metric("Com Redução IBS/CBS", com_reducao, delta=f"{(com_reducao/total*100):.1f}%")
    
    # Preview da tabela
    st.subheader("📊 Preview dos Resultados")
    
    # Mostrar colunas relevantes
    colunas_preview = [col for col in result_df.columns if col in ['Código', 'Produto', 'NCM', 'CST_IBS_CBS', 'cClassTrib', 'pRedIBS', 'pRedCBS', 'tipoAliquota', 'Confianca', 'Observacoes']]
    if not colunas_preview:
        colunas_preview = result_df.columns.tolist()
        
    st.dataframe(result_df[colunas_preview].head(20), use_container_width=True)
    
    st.info(f"ℹ️ Todos os {total} itens foram classificados com CST, cClassTrib, reduções e tipo de alíquota!")
    
    # Botão de download
    st.subheader("💾 Baixar Planilha Classificada")
    
    # Converter para Excel
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        result_df.to_excel(writer, index=False, sheet_name='Classificação')
        
        # Formatação básica
        workbook = writer.book
        worksheet = writer.sheets['Classificação']
        
        # Auto-ajustar largura das colunas
        for column in worksheet.columns:
            max_length = 0
            column = [cell for cell in column]
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(cell.value)
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            worksheet.column_dimensions[column[0].column_letter].width = adjusted_width
    
    excel_data = output.getvalue()
    
    st.download_button(
        label="📥 Baixar Planilha Classificada (Excel)",
        data=excel_data,
        file_name=st.session_state.result_filename,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #808080; padding: 20px;">
    <p><strong>Conecta IBS/CBS</strong> - Sistema de Classificação Tributária Automática</p>
    <p style="font-size: 12px;">Desenvolvido para simplificar a classificação de códigos tributários IBS/CBS</p>
    <p style="font-size: 11px; margin-top: 10px;">✅ Preenche automaticamente: CST, cClassTrib, pRedIBS, pRedCBS e tipoAliquota</p>
</div>
""", unsafe_allow_html=True)
