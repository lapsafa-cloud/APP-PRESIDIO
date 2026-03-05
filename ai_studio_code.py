import streamlit as st
from google import genai
from google.genai import types
import os
import time

# 1. Configuração de Interface Institucional
st.set_page_config(page_title="Consultoria Técnica - SAP-SC", layout="wide")
st.title("⚖️ Sistema de Apoio Técnico - SAP/SEJURI")
st.subheader("Consulta Integrada: Portaria 2189/2025 (SDK v2)")

# 2. Protocolo de Segurança e Chave API
api_key = st.secrets.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY")

if not api_key:
    st.error("Erro de Configuração: Chave API não detectada.")
    st.stop()

# Inicializa o cliente novo
client = genai.Client(api_key=api_key)

# 3. Processamento da Base Normativa (PDFs)
def processar_base_legal():
    pasta = "documentos"
    if not os.path.exists(pasta):
        os.makedirs(pasta)
        return []
    
    arquivos_pdf = [f for f in os.listdir(pasta) if f.lower().endswith(".pdf")]
    referencias = []
    
    if not arquivos_pdf:
        st.info("Aguardando inserção de documentos normativos na base.")
        return []
    
    for nome in arquivos_pdf:
        caminho = os.path.join(pasta, nome)
        try:
            with st.status(f"Indexando: {nome}", expanded=False) as s:
                # CORREÇÃO AQUI: 'file' em vez de 'path'
                file_ref = client.files.upload(file=caminho)
                
                # Aguarda validação do arquivo
                tentativas = 0
                while file_ref.state.name == "PROCESSING" and tentativas < 15:
                    time.sleep(2)
                    file_ref = client.files.get(name=file_ref.name)
                    tentativas += 1
                
                if file_ref.state.name == "ACTIVE":
                    referencias.append(file_ref)
                    s.update(label=f"Arquivo {nome} carregado", state="complete")
                else:
                    st.error(f"Arquivo {nome} está em estado: {file_ref.state.name}")
        except Exception as e:
            st.error(f"Falha no processamento do ficheiro {nome}: {e}")
            
    return referencias

# 4. Gestão de Memória
if "base_docs" not in st.session_state:
    st.session_state.base_docs = processar_base_legal()
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 5. Interface de Consulta
if prompt := st.chat_input("Digite sua dúvida técnica:"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        modelos_disponiveis = ["gemini-1.5-pro", "gemini-1.5-flash"]
        sucesso = False

        # Instrução do sistema agora é um objeto de configuração
        config_instrucao = types.GenerateContentConfig(
            system_instruction=(
                "Você é um assistente técnico especializado na Secretaria de Administração Prisional (SAP-SC). "
                "Forneça informações precisas com base na Portaria 2189/2025. "
                "Se a informação não constar nos documentos, instrua a consultar o Diário Oficial."
            )
        )

        for model_id in modelos_disponiveis:
            if sucesso: break
            try:
                # Monta a lista de conteúdos (PDFs + Prompt)
                conteudo_final = st.session_state.base_docs + [prompt]
                
                response = client.models.generate_content(
                    model=model_id,
                    contents=conteudo_final,
                    config=config_instrucao
                )
                
                resposta = response.text
                st.markdown(resposta)
                st.session_state.messages.append({"role": "assistant", "content": resposta})
                sucesso = True
                
            except Exception as e:
                if "429" in str(e) or "quota" in str(e).lower():
                    continue
                st.error(f"Erro operacional: {e}")
                break
        
        if not sucesso:
            st.warning("Sistema indisponível no momento. Verifique as cotas no Google Cloud.")
