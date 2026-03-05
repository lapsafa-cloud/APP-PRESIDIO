import streamlit as st
import google.generativeai as genai
import os
import time

# 1. Configuração de Interface Institucional
st.set_page_config(page_title="Consultoria Técnica - SAP-SC", layout="wide")
st.title("⚖️ Sistema de Apoio Técnico - SAP/SEJURI")
st.subheader("Consulta Integrada: Portaria 2189/2025")

# 2. Protocolo de Segurança e Chave API
# A chave deve estar configurada nos 'Secrets' do Streamlit Cloud como GEMINI_API_KEY
api_key = st.secrets.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY")

if not api_key:
    st.error("Erro de Configuração: Chave API não detectada no ambiente.")
    st.stop()

genai.configure(api_key=api_key)

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
                # Upload para o motor de IA
                file_ref = genai.upload_file(path=caminho, display_name=nome)
                
                # Aguarda validação do arquivo
                tentativas = 0
                while file_ref.state.name == "PROCESSING" and tentativas < 15:
                    time.sleep(2)
                    file_ref = genai.get_file(file_ref.name)
                    tentativas += 1
                
                if file_ref.state.name == "ACTIVE":
                    referencias.append(file_ref)
                    s.update(label=f"Arquivo {nome} carregado", state="complete")
        except Exception as e:
            st.error(f"Falha no processamento do ficheiro {nome}: {e}")
            
    return referencias

# 4. Gestão de Memória e Sessão
if "base_docs" not in st.session_state:
    st.session_state.base_docs = processar_base_legal()
    st.session_state.messages = []

# Histórico de Consultas
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 5. Interface de Consulta e Processamento de Respostas
if prompt := st.chat_input("Digite sua dúvida técnica sobre a Portaria:"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # Modelos disponíveis conforme plano de faturamento ativo
        modelos_disponiveis = ["gemini-1.5-pro", "gemini-1.5-flash"]
        sucesso = False

        for model_id in modelos_disponiveis:
            if sucesso: break
            try:
                model = genai.GenerativeModel(
                    model_name=model_id,
                    system_instruction=(
                        "Você é um assistente técnico especializado na Secretaria de Administração Prisional (SAP-SC). "
                        "Sua função é fornecer informações precisas com base na Portaria 2189/2025. "
                        "Responda de forma formal e técnica. Se a informação não constar nos documentos fornecidos, "
                        "instrua o usuário a consultar o Diário Oficial ou o setor responsável pelo DPP."
                    )
                )
                
                # Executa a geração com os documentos anexados
                payload = st.session_state.base_docs + [prompt]
                response = model.generate_content(payload)
                
                resposta = response.text
                st.markdown(resposta)
                st.session_state.messages.append({"role": "assistant", "content": resposta})
                sucesso = True
                
            except Exception as e:
                # Caso o modelo Pro falhe por cota ou ativação, o Flash assume o processamento
                if "429" in str(e) or "quota" in str(e).lower():
                    continue
                elif "404" in str(e):
                    continue
                else:
                    st.error(f"Erro operacional: {e}")
                    break
        
        if not sucesso:
            st.warning("Sistema temporariamente indisponível. Verifique a conta de faturamento no console de gestão.")
