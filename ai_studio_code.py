import streamlit as st
import google.generativeai as genai
import os
import time

# 1. Configuração da Página
st.set_page_config(page_title="Assistente SAP-SC", layout="centered")
st.title("⚖️ Assistente do Sistema Penal - SC")
st.caption("Protótipo de Extensão Universitária - Administração")

# 2. Configuração da Chave API
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    st.error("Chave API não configurada nos Secrets!")
    st.stop()

genai.configure(api_key=api_key)

# 3. Função para Carregar os PDFs
def carregar_arquivos():
    pasta = "documentos"
    if not os.path.exists(pasta):
        os.makedirs(pasta)
        return []
    
    arquivos_pdf = [f for f in os.listdir(pasta) if f.lower().endswith(".pdf")]
    referencias = []
    
    for nome in arquivos_pdf:
        caminho = os.path.join(pasta, nome)
        with st.status(f"Lendo {nome}...", expanded=False) as s:
            # Faz o upload para o Google
            file_ref = genai.upload_file(path=caminho, display_name=nome)
            
            # Espera o processamento (Estado ACTIVE)
            while file_ref.state.name == "PROCESSING":
                time.sleep(2)
                file_ref = genai.get_file(file_ref.name)
            
            referencias.append(file_ref)
            s.update(label=f"✅ {nome} carregado", state="complete")
    return referencias

# 4. Inicialização do Chat
if "base_docs" not in st.session_state:
    st.session_state.base_docs = carregar_arquivos()
    st.session_state.messages = []

# Exibe histórico
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 5. Lógica de Resposta
if prompt := st.chat_input("Como posso ajudar?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            # O coração do seu projeto: RAG (Arquivos + Instrução + Pergunta)
            model = genai.GenerativeModel(
                model_name="gemini-1.5-flash",
                system_instruction="Você é um assistente da SAP-SC. Responda APENAS com base nos PDFs fornecidos. Se a informação não estiver lá, peça para contatarem um servidor oficial."
            )
            
            # Criamos a lista de conteúdo enviando os arquivos primeiro e depois o prompt
            conteudo = []
            for f in st.session_state.base_docs:
                conteudo.append(f)
            conteudo.append(prompt)
            
            response = model.generate_content(conteudo)
            
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            
        except Exception as e:
            st.error(f"Erro técnico: {e}")
