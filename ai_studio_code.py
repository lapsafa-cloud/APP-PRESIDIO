# To run this code you need to install the following dependencies:
# pip install google-genai

import streamlit as st
from google import genai
import os

# 1. Configuração do Cliente
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

def preparar_contexto():
    # Caminho onde seus PDFs estão
    pasta_docs = "documentos"
    arquivos_gemini = []

    # Faz o upload de cada PDF para o Gemini processar
    for nome_arquivo in os.listdir(pasta_docs):
        if nome_arquivo.endswith(".pdf"):
            caminho_completo = os.path.join(pasta_docs, nome_arquivo)
            # O Gemini "lê" o arquivo e cria uma referência
            file_ref = client.files.upload(path=caminho_completo)
            arquivos_gemini.append(file_ref)
    
    return arquivos_gemini

# --- Interface Streamlit ---
st.title("⚖️ Assistente do Sistema Penal - SC")

if "processado" not in st.session_state:
    with st.spinner("Lendo normativas e leis..."):
        st.session_state.arquivos = preparar_contexto()
        st.session_state.processado = True
    st.success("Base de dados carregada!")

user_input = st.chat_input("Diga sua dúvida (ex: documentos para visita)")

if user_input:
    # O Gemini recebe a pergunta + os arquivos como referência
    response = client.models.generate_content(
        model="gemini-1.5-flash",
        contents=[st.session_state.arquivos[0], user_input], # Aqui ele lê o PDF e a pergunta
        config={'system_instruction': "Responda apenas com base nos documentos fornecidos."}
    )
    st.chat_message("assistant").write(response.text)


