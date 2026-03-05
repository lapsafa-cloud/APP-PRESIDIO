import streamlit as st
from google import genai
from google.genai import types
import os
import time

# --- CONFIGURAÇÃO SAP-SC ---
st.set_page_config(page_title="Consultoria Técnica - SAP-SC", layout="wide")
st.title("⚖️ Sistema de Apoio Técnico - SAP/SEJURI")
st.subheader("Consulta Integrada: Portaria 2189/2025")

# Inicializa o cliente com a sua chave que já está em 'Nível 1'
client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

def processar_base_legal():
    pasta = "documentos"
    if not os.path.exists(pasta): return []
    
    arquivos = [f for f in os.listdir(pasta) if f.lower().endswith(".pdf")]
    referencias = []
    
    for nome in arquivos:
        caminho = os.path.join(pasta, nome)
        try:
            with st.status(f"Indexando: {nome}", expanded=False) as s:
                file_ref = client.files.upload(file=caminho)
                while file_ref.state.name == "PROCESSING":
                    time.sleep(2)
                    file_ref = client.files.get(name=file_ref.name)
                
                if file_ref.state.name == "ACTIVE":
                    referencias.append(file_ref)
                    s.update(label=f"✅ {nome} carregado", state="complete")
        except Exception as e:
            st.error(f"Erro em {nome}: {e}")
    return referencias

if "base_docs" not in st.session_state:
    st.session_state.base_docs = processar_base_legal()
    st.session_state.messages = []

# Interface de Chat
if prompt := st.chat_input("Sua dúvida sobre a Portaria:"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("assistant"):
        # MODELOS ATUALIZADOS CONFORME SUA LISTA
        model_id = "gemini-2.0-flash" 
        
        try:
            config = types.GenerateContentConfig(
                system_instruction="Você é assistente técnico da SAP-SC. Use a Portaria 2189/2025 como base única.",
                temperature=0.1
            )
            
            conteudo = st.session_state.base_docs + [prompt]
            response = client.models.generate_content(
                model=model_id,
                contents=conteudo,
                config=config
            )
            
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            
        except Exception as e:
            st.error(f"Erro operacional: {e}")
