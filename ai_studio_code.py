import streamlit as st
from google import genai
from google.genai import types
# ... (restante dos imports)

# 1. Lista de modelos em ordem de preferência (conforme sua lista de acesso)
# O 2.5 Flash é o equilíbrio perfeito para documentos jurídicos da SAP.
MODELOS_RANKING = ["gemini-2.5-flash", "gemini-3-flash-preview", "gemini-2.0-flash-lite"]

# ... (função processar_base_legal continua igual)

if prompt := st.chat_input("Dúvida sobre a Portaria 2189/2025:"):
    # ... (lógica de exibição de mensagens)
    
    with st.chat_message("assistant"):
        sucesso = False
        for model_id in MODELOS_RANKING:
            if sucesso: break
            try:
                config = types.GenerateContentConfig(
                    system_instruction="Você é assistente técnico da SAP-SC. Baseie-se apenas na Portaria 2189/2025.",
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
                sucesso = True
                
            except Exception as e:
                # Se o erro for 404 (modelo indisponível), tenta o próximo da lista
                if "404" in str(e):
                    continue
                else:
                    st.error(f"Erro: {e}")
                    break
