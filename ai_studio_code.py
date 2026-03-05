# --- LOGO APÓS A CRIAÇÃO DO CLIENT ---
client = genai.Client(api_key=api_key)

# INICIALIZAÇÃO DO SESSION STATE (Adicione isso aqui)
if "base_docs" not in st.session_state:
    st.session_state.base_docs = []  # Começa vazia para evitar o erro de atributo

if "messages" not in st.session_state:
    st.session_state.messages = []

# --- SÓ AGORA CHAME A FUNÇÃO DE CARREGAMENTO ---
# Isso garante que se a função falhar, a variável ao menos existe como uma lista vazia
if not st.session_state.base_docs:
    with st.sidebar:
        st.session_state.base_docs = processar_base_legal()
