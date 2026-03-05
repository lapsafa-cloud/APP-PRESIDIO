import streamlit as st
from google import genai
from google.genai import types
import os
import time

# --- 1. INICIALIZAÇÃO DO ESTADO DA SESSÃO ---
# Deve ser a primeira coisa para evitar erros de "attribute not found"
if "base_docs" not in st.session_state:
    st.session_state.base_docs = []
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 2. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Consultoria Técnica - SAP-SC", layout="wide")
st.title("⚖️ Sistema de Apoio Técnico - SAP/SEJURI")
st.subheader("Consulta Integrada: Portaria 2189/2025")

# --- 3. AUTENTICAÇÃO E CLIENTE ---
api_key = st.secrets.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY")

if not api_key:
    st.error("Erro: GEMINI_API_KEY não encontrada nos Secrets do Streamlit.")
    st.stop()

# Inicialização correta para o SDK v2 (google-genai)
client = genai.Client(api_key=api_key)

# --- 4. PROCESSAMENTO DE DOCUMENTOS ---
def processar_base_legal():
    pasta = "documentos"
    # Criar pasta se não existir no servidor
    if not os.path.exists(pasta):
        os.makedirs(pasta)
        return []

    arquivos_pdf = [f for f in os.listdir(pasta) if f.lower().endswith(".pdf")]
    referencias = []

    if not arquivos_pdf:
        st.sidebar.info("Aguardando PDFs na pasta 'documentos'.")
        return []

    for nome in arquivos_pdf:
        caminho = os.path.join(pasta, nome)
        try:
            with st.sidebar.status(f"Lendo: {nome}", expanded=False) as s:
                # Upload para a API do Google (argumento correto: file)
                file_ref = client.files.upload(file=caminho)
                
                # Aguarda o processamento do arquivo
                tentativas = 0
                while file_ref.state.name == "PROCESSING" and tentativas < 15:
                    time.sleep(2)
                    file_ref = client.files.get(name=file_ref.name)
                    tentativas += 1
                
                if file_ref.state.name == "ACTIVE":
                    referencias.append(file_ref)
                    s.update(label=f"✅ {nome} pronto", state="complete")
        except Exception as e:
            st.sidebar.error(f"Erro no PDF {nome}: {e}")
            
    return referencias

# Carrega os documentos apenas se a lista estiver vazia
if not st.session_state.base_docs:
    st.session_state.base_docs = processar_base_legal()

# --- 5. INTERFACE DE CHAT ---
# Exibe mensagens anteriores
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Entrada do usuário
if prompt := st.chat_input("Digite sua dúvida técnica:"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # Ranking de modelos ativos na sua conta (Março/2026)
        # O 2.5 Flash é o mais estável para o seu projeto no momento.
        modelos_disponiveis = ["gemini-2.5-flash", "gemini-3-flash-preview", "gemini-2.5-pro"]
        sucesso = False

        for model_id in modelos_disponiveis:
            if sucesso: break
            try:
                # Configuração da Persona SAP-SC
                config_ia = types.GenerateContentConfig(
                    system_instruction=(
                        "Você é um consultor técnico da Secretaria de Administração Prisional (SAP-SC). "
                        "Sua base de conhecimento é estritamente a Portaria 2189/2025 e documentos anexados. "
                        "Responda de forma formal. Se a resposta não estiver nos arquivos, oriente o usuário "
                        "a procurar o Diário Oficial ou o DPP."
                    ),
                    temperature=0.1
                )

                # Combina documentos indexados com a pergunta
                payload = st.session_state.base_docs + [prompt]
                
                response = client.models.generate_content(
                    model=model_id,
                    contents=payload,
                    config=config_ia
                )
                
                resposta = response.text
                st.markdown(resposta)
                st.session_state.messages.append({"role": "assistant", "content": resposta})
                sucesso = True
                
            except Exception as e:
                # Se o erro for de modelo indisponível (404), pula para o próximo da lista
                if "404" in str(e):
                    continue
                st.error(f"Erro operacional: {e}")
                break
        
        if not sucesso:
            st.warning("IA temporariamente fora de área. Verifique a Generative Language API no Google Cloud.")
