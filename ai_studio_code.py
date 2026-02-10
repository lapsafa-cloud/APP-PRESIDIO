# To run this code you need to install the following dependencies:
# pip install google-genai

import os
import time
import streamlit as st
from google import genai

def preparar_contexto():
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    pasta_docs = "documentos"
    
    if not os.path.exists(pasta_docs):
        os.makedirs(pasta_docs)
        return []

    arquivos_gemini = []
    lista_arquivos = [f for f in os.listdir(pasta_docs) if f.lower().endswith(".pdf")]
    
    for nome_arquivo in lista_arquivos:
        caminho_completo = os.path.join(pasta_docs, nome_arquivo)
        try:
            with st.spinner(f"Fazendo upload de {nome_arquivo}..."):
                # MUDANÇA AQUI: Usamos 'file' em vez de 'path'
                file_ref = client.files.upload(file=caminho_completo)
                
                # ESPERA O PROCESSAMENTO: A IA precisa de tempo para ler o PDF
                while file_ref.state.name == "PROCESSING":
                    time.sleep(2)
                    file_ref = client.files.get(name=file_ref.name)
                
                if file_ref.state.name == "FAILED":
                    st.error(f"Erro ao processar {nome_arquivo}")
                    continue
                    
                arquivos_gemini.append(file_ref)
                st.success(f"{nome_arquivo} pronto!")
        except Exception as e:
            st.error(f"Erro no upload de {nome_arquivo}: {e}")
    
    return arquivos_gemini
