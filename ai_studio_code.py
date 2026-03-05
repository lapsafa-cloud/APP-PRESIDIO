import streamlit as st
from google import genai
import os

# 1. Use o cliente padrão
client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

try:
    # Tente forçar o caminho completo do modelo
    response = client.models.generate_content(
        model="gemini-1.5-flash", # Se der 404, tente "models/gemini-1.5-flash"
        contents="Oi! Se você ler isso, a SAP-SC está conectada."
    )
    st.success("✅ Finalmente conectado!")
    st.write(response.text)
except Exception as e:
    st.error(f"Erro: {e}")
    # Se ainda der 404, o comando abaixo vai listar o que VOCÊ pode usar:
    st.write("Modelos que sua chave enxerga:")
    for m in client.models.list():
        st.text(m.name)
