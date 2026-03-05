import streamlit as st
from google import genai
import os

st.title("Teste de Conexão SAP-SC")

# Garanta que a chave esteja nos Secrets do Streamlit como GEMINI_API_KEY
api_key = st.secrets.get("GEMINI_API_KEY")

if not api_key:
    st.error("Chave não encontrada nos Secrets!")
    st.stop()

client = genai.Client(api_key=api_key)

if st.button("Testar Conexão com Gemini"):
    try:
        # Teste simples sem documentos
        response = client.models.generate_content(
            model="gemini-1.5-flash", 
            contents="Olá! Você está ativo para a SAP-SC?"
        )
        st.success("✅ Conexão estabelecida!")
        st.write("Resposta da IA:", response.text)
    except Exception as e:
        st.error(f"❌ Erro ainda persiste: {e}")
        st.info("Se aparecer 404, volte ao Google Cloud Console e ative a 'Generative Language API'.")
