# To run this code you need to install the following dependencies:
# pip install google-genai

import streamlit as st
import os
import time
from google import genai

# --- CONFIGURAÇÃO INICIAL DA PÁGINA (Deve ser a primeira coisa!) ---
st.set_page_config(page_title="Assistente SAP-SC", layout="centered")
st.title("⚖️ Assistente do Sistema Penal - SC")
st.caption("Protótipo de Extensão Universitária - 7º Período Administração")

# --- INICIALIZAÇÃO DO CLIENTE ---
if "GEMINI_API_KEY" not in os.environ:
    st.error("Erro: A chave GEMINI_API_KEY não foi encontrada nos Secrets do Streamlit.")
    st.stop()

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# --- FUNÇÃO DE CARREGAMENTO ---
def carregar_documentos():
    pasta = "documentos"
    if not os.path.exists(pasta):
        os.makedirs(pasta)
        return []
    
    arquivos_locais = [f for f in os.listdir(pasta) if f.lower().endswith(".pdf")]
    referencias_gemini = []
    
    for nome in arquivos_locais:
        caminho = os.path.join(pasta, nome)
        with st.status(f"Processando {nome}...", expanded=True) as status:
            try:
                # Upload do arquivo
                meu_arquivo = client.files.upload(file=caminho)
                
                # Loop de espera com limite de tentativas (para evitar tela branca infinita)
                tentativas = 0
                while meu_arquivo.state.name == "PROCESSING" and tentativas < 15:
                    time.sleep(2)
                    meu_arquivo = client.files.get(name=meu_arquivo.name)
                    tentativas += 1
                
                if meu_arquivo.state.name == "ACTIVE":
                    referencias_gemini.append(meu_arquivo)
                    status.update(label=f"✅ {nome} carregado!", state="complete")
                else:
                    status.update(label=f"❌ Erro no processamento de {nome}", state="error")
            except Exception as e:
                st.error(f"Falha no upload de {nome}: {e}")
                
    return referencias_gemini

# --- LÓGICA DE ESTADO (Para não recarregar os PDFs toda hora) ---
if "base_conhecimento" not in st.session_state:
    st.session_state.base_conhecimento = carregar_documentos()
    st.session_state.messages = []

# --- INTERFACE DE CHAT ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Como posso ajudar com as normas do presídio?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            # Monta o contexto enviando os arquivos + a pergunta
            conteudo_completo = st.session_state.base_conhecimento + [prompt]
            
            response = client.models.generate_content(
                model="gemini-1.5-flash",
                contents=conteudo_completo,
                config={'system_instruction': "Você é um assistente jurídico/administrativo do sistema penal de SC. Use uma linguagem clara para familiares e técnica para advogados. Baseie-se APENAS nos PDFs fornecidos. Se não souber, peça para contatarem um servidor."}
            )
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
        except Exception as e:
            st.error(f"Erro ao gerar resposta: {e}")
