import streamlit as st
import google.generativeai as genai
import os
os.environ["GOOGLE_API_USE_MTLS_ENDPOINT"] = "never"
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

       try:
            # Tentativa com o modelo 8B (mais leve e com maior compatibilidade de acesso)
            model_name = "gemini-1.5-flash-8b" 
            
            model = genai.GenerativeModel(
                model_name=model_name,
                system_instruction="Você é assistente da SAP-SC. Responda com base nos PDFs fornecidos."
            )
            
            # O restante do código de conteúdo permanece igual
            conteudo = st.session_state.base_docs + [prompt]
            response = model.generate_content(conteudo)
            st.markdown(response.text)
            
        except Exception as e:
            # Se ainda der erro, usamos o 1.0 Pro (O cavalo de batalha do Google)
            st.warning("Ajustando protocolo de conexão...")
            model = genai.GenerativeModel(model_name="gemini-1.0-pro")
            # Nota: O 1.0 Pro pode ter dificuldade com PDFs muito grandes, 
            # então enviamos apenas o prompt se os arquivos falharem.
            response = model.generate_content(prompt)
            st.markdown(response.text)
            
        except Exception as e:
            if "404" in str(e):
                # Se der 404, tentamos o caminho completo que a v1beta às vezes exige
                try:
                    model = genai.GenerativeModel(model_name="models/gemini-1.5-flash")
                    response = model.generate_content(st.session_state.base_docs + [prompt])
                    st.markdown(response.text)
                except:
                    st.error("O Google está recusando a conexão com este modelo específico. Verifique se sua chave API no AI Studio tem permissão para o 'Gemini 1.5 Flash'.")
            else:
                st.error(f"Erro técnico: {e}")
