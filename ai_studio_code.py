import streamlit as st
import google.generativeai as genai
import os
import time

# 1. Configuração da Página e Estilo
st.set_page_config(page_title="Assistente SAP-SC", layout="centered")
st.title("⚖️ Assistente do Sistema Penal - SC")
st.caption("Protótipo de Extensão Universitária - Administração")

# 2. Configuração da Chave API
# Certifique-se de que o nome no Streamlit Secrets é exatamente GEMINI_API_KEY
api_key = os.environ.get("GEMINI_API_KEY")

if not api_key:
    st.error("Chave API não encontrada! Configure GEMINI_API_KEY nos Secrets do Streamlit.")
    st.stop()

genai.configure(api_key=api_key)

# 3. Função Robusta para Carregar os PDFs
def carregar_arquivos():
    pasta = "documentos"
    if not os.path.exists(pasta):
        os.makedirs(pasta)
        return []
    
    arquivos_pdf = [f for f in os.listdir(pasta) if f.lower().endswith(".pdf")]
    referencias = []
    
    if not arquivos_pdf:
        st.info("Nenhum PDF encontrado na pasta 'documentos'.")
        return []
    
    for nome in arquivos_pdf:
        caminho = os.path.join(pasta, nome)
        try:
            with st.status(f"Lendo {nome}...", expanded=False) as s:
                # Upload para o Google
                file_ref = genai.upload_file(path=caminho, display_name=nome)
                
                # Loop de espera (Check de estado)
                timeout = 0
                while file_ref.state.name == "PROCESSING" and timeout < 30:
                    time.sleep(2)
                    file_ref = genai.get_file(file_ref.name)
                    timeout += 2
                
                if file_ref.state.name == "ACTIVE":
                    referencias.append(file_ref)
                    s.update(label=f"✅ {nome} pronto", state="complete")
                else:
                    st.error(f"O arquivo {nome} falhou no processamento.")
        except Exception as e:
            st.error(f"Erro no upload de {nome}: {e}")
            
    return referencias

# 4. Inicialização de Memória do Chat
if "base_docs" not in st.session_state:
    st.session_state.base_docs = carregar_arquivos()
    st.session_state.messages = []

# Exibe histórico das mensagens
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 5. Lógica de Resposta com Fallback de Modelos
if prompt := st.chat_input("Como posso ajudar?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # Tentamos os modelos em ordem de compatibilidade para evitar erro 404
        modelos_para_testar = ["gemini-1.5-flash", "gemini-1.5-flash-8b", "gemini-1.0-pro"]
        sucesso = False

        for nome_modelo in modelos_para_testar:
            if sucesso: break
            try:
                # Se for o 1.0 Pro, ele não aceita arquivos PDF diretamente no contents
                # Então fazemos essa distinção
                model = genai.GenerativeModel(
                    model_name=nome_modelo,
                    system_instruction="Você é assistente da SAP-SC. Use os PDFs como base. Se não souber, peça para contatarem um servidor."
                )
                
                if nome_modelo == "gemini-1.0-pro":
                    # O 1.0 Pro lê apenas texto
                    response = model.generate_content(prompt)
                else:
                    # Modelos 1.5 aceitam PDF + Texto
                    conteudo = st.session_state.base_docs + [prompt]
                    response = model.generate_content(conteudo)
                
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
                sucesso = True
                
            except Exception as e:
                if "404" in str(e) or "not found" in str(e).lower():
                    continue # Tenta o próximo modelo da lista
                else:
                    st.error(f"Erro técnico: {e}")
                    break
        
        if not sucesso:
            st.error("Não foi possível conectar aos modelos do Google. Verifique sua cota e sua Chave API.") 	
