import streamlit as st
from google import genai
from google.genai import types
import os
import time

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Consultoria Técnica - SAP-SC", layout="wide", page_icon="⚖️")

# Estilização básica para o cabeçalho
st.title("⚖️ Sistema de Apoio Técnico - SAP/SEJURI")
st.markdown(f"**Foco:** Portaria 2189/2025 - Procedimentos Operacionais DPP")
st.divider()

# --- AUTENTICAÇÃO ---
# Prioriza Secrets do Streamlit, depois variáveis de ambiente locais
api_key = st.secrets.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY")

if not api_key:
    st.error("❌ Erro de Configuração: Chave API não detectada. Adicione 'GEMINI_API_KEY' nos Secrets do Streamlit.")
    st.stop()

# Inicializa o cliente oficial v2
client = genai.Client(api_key=api_key)

# --- FUNÇÕES DE SUPORTE ---
def carregar_documentos():
    """Lê PDFs da pasta 'documentos' e faz o upload para o Gemini."""
    pasta = "documentos"
    if not os.path.exists(pasta):
        os.makedirs(pasta)
        return []

    arquivos = [f for f in os.listdir(pasta) if f.lower().endswith(".pdf")]
    referencias_google = []

    if not arquivos:
        st.sidebar.warning("⚠️ Nenhum PDF encontrado na pasta 'documentos'.")
        return []

    for nome in arquivos:
        caminho = os.path.join(pasta, nome)
        try:
            with st.sidebar.status(f"Processando {nome}...", expanded=False) as status:
                # No SDK v2, usamos 'file=' e não 'path='
                file_uploaded = client.files.upload(file=caminho)
                
                # Aguarda o processamento no servidor do Google
                while file_uploaded.state.name == "PROCESSING":
                    time.sleep(2)
                    file_uploaded = client.files.get(name=file_uploaded.name)
                
                if file_uploaded.state.name == "ACTIVE":
                    referencias_google.append(file_uploaded)
                    status.update(label=f"✅ {nome} pronto", state="complete")
                else:
                    status.update(label=f"❌ Erro em {nome}", state="error")
        except Exception as e:
            st.sidebar.error(f"Erro no upload de {nome}: {e}")
            
    return referencias_google

# --- INICIALIZAÇÃO DO SISTEMA ---
if "base_docs" not in st.session_state:
    st.session_state.base_docs = carregar_documentos()

if "messages" not in st.session_state:
    st.session_state.messages = []

# Exibe histórico de chat
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- INTERFACE DE CHAT ---
if prompt := st.chat_input("Como posso ajudar na interpretação da Portaria 2189/2025?"):
    # Adiciona pergunta do usuário
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # Lista de modelos para fallback (tentar o Flash primeiro por ser mais rápido e barato)
        modelos = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash"]
        sucesso = False
        
        # Configuração da Persona e Regras
        config_ia = types.GenerateContentConfig(
            system_instruction=(
                "Você é um consultor jurídico especializado da Secretaria de Administração Prisional (SAP-SC). "
                "Sua única fonte de verdade são os documentos PDF fornecidos sobre a Portaria 2189/2025. "
                "Responda de forma técnica, formal e objetiva. "
                "Se a resposta não estiver nos documentos, diga explicitamente que a norma é omissa e "
                "recomende a consulta ao setor de Corregedoria ou DPP."
            ),
            temperature=0.2, # Menos criatividade, mais precisão técnica
        )

        for model_id in modelos:
            if sucesso: break
            try:
                # Prepara o conteúdo (Documentos + Pergunta)
                conteudo = st.session_state.base_docs + [prompt]
                
                response = client.models.generate_content(
                    model=model_id,
                    contents=conteudo,
                    config=config_ia
                )
                
                full_response = response.text
                st.markdown(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response})
                sucesso = True
                
            except Exception as e:
                # Trata erro 404 de modelo ou 429 de cota
                if "404" in str(e) or "quota" in str(e).lower():
                    continue 
                st.error(f"Erro técnico: {e}")
                break
        
        if not sucesso:
            st.error("Desculpe, não consegui acessar os modelos de IA agora. Verifique se a 'Generative Language API' está ativa no Google Cloud.")
