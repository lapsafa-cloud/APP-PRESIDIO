# To run this code you need to install the following dependencies:
# pip install google-genai

import streamlit as st
import os
import time
from google import genai
from google.genai import types

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
            # 1. Definimos o nome do modelo sem o prefixo "models/"
            nome_modelo = "gemini-1.5-flash"
            
            # 2. Criamos o conteúdo: Arquivos + Pergunta do Usuário
            # Certifique-se de que 'base_conhecimento' seja uma lista
            conteudo = st.session_state.base_conhecimento + [prompt]
            
            # 3. Chamada da API com a configuração explícita
            response = client.models.generate_content(
                model=nome_modelo,
                contents=conteudo,
                config=types.GenerateContentConfig(
                    system_instruction="""Você é um assistente do sistema penal de SC. 
                    Responda para familiares (simples) e advogados (técnico). 
                    Baseie-se APENAS nos PDFs. Se não souber, peça para falar com um servidor.""",
                    temperature=0.1, # Mantém a resposta focada no documento
                )
            )
            
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})

        except Exception as e:
            # Se o erro 404 persistir, vamos tentar o modelo 2.0 que é nativo desta biblioteca
            if "404" in str(e):
                st.warning("Tentando conexão alternativa com modelo estável...")
                try:
                    response = client.models.generate_content(
                        model="gemini-2.0-flash-exp", # Versão mais compatível com a biblioteca nova
                        contents=st.session_state.base_conhecimento + [prompt]
                    )
                    st.markdown(response.text)
                except Exception as e2:
                    st.error(f"Erro persistente: {e2}")
            else:
                st.error(f"Erro ao gerar resposta: {e}")
