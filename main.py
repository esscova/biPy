"""
APLICACAO WEB - CHATBOT COM GROQ E STREAMLIT 
"""

# --- IMPORTS
import streamlit as st
from groq import Groq, AuthenticationError, APIConnectionError, RateLimitError

# --- CONFIGURACAO STREAMLIT
st.set_page_config(
    page_title='ChatBot Python',
    page_icon='^_^',
    layout='centered',
    initial_sidebar_state='collapsed'
)

if "messages" not in st.session_state:
    st.session_state.messages = []

# --- CONFIGURACAO LLM
SYSTEM_PROMPT='Você é um assistente útil.'
groq_api_key=''
model = ''
temperatura=1.0
client = None
LLM_MODELOS = [
    'llama-3.1-8b-instant',
    'llama-3.3-70b-versatile',
    'meta-llama/llama-4-maverick-17b-128e-instruct',
    'moonshotai/kimi-k2-instruct',
    'openai/gpt-oss-20b',
    'openai/gpt-oss-120b',
    'qwen/qwen3-32b'
]

# --- SIDEBAR
with st.sidebar:
    st.title('⚙️ Configurações')
    st.markdown('---')

    groq_api_key = st.text_input(
        label='Insira sua API KEY da Groq',
        type='password',
        help='Obtenha sua chave em https://console.groq.com/keys'
    )

    model = st.selectbox(
        label='Selecione seu modelo',
        options=LLM_MODELOS,
        index=0,
        help='Consulte detalhes em https://console.groq.com/docs/models'
    )

    temperatura = st.slider(
        label='Temperatura',
        min_value=0.1,
        max_value=1.0,
        step=0.1,
        value=0.7
    )

# --- INICIALIZAR CLIENT COM API
if groq_api_key:
    try:
        client = Groq(api_key=groq_api_key)
    except Exception as e:
        st.sidebar.error(f'Erro ao inicializar o cliente Groq: {e}')
        st.stop()
elif st.session_state.messages:
    st.warning('Por favor insira sua API KEY da Groq.')

# --- INTERFACE PRINCIPAL
st.title('OPA')
st.caption('Faça sua pergunta sobre Python.')
st.markdown('---')

for message in st.session_state.messages:
    with st.chat_message(message['role']):
        st.markdown(message['content'])

if prompt := st.chat_input("Digite sua mensagem ..."):
    if not client:
        st.warning("Por favor, insira a API KEY na barra lateral.")
        st.stop()
    if not model:
        st.warning("Por favor, defina o modelo na barra lateral.")
        st.stop()
    
    st.session_state.messages.append({
        'role':'user',
        'content':prompt
    })
    with st.chat_message('user'):
        st.markdown(prompt)

    messages_payload = [{
        'role':'system',
        'content': SYSTEM_PROMPT
    }] + st.session_state.messages

    with st.chat_message("assistant"):
        with st.spinner('Pensando...'):
            try:
                chat = client.chat.completions.create(
                    messages=messages_payload,
                    model=model,
                    temperature=temperatura
                )
                response = chat.choices[0].message.content
                st.markdown(response)
                st.session_state.messages.append({
                    'role':'assistant',
                    'content': response
                })
            except AuthenticationError:
                st.error('Erro de Autenticação, sua API key é inválida ou expirou. Verifique a chave inserida na barra lateral.')
                st.stop()
            except RateLimitError:
                st.error('Você atingiu o limite de mensagens gratuitas.')
                st.stop()
            except APIConnectionError:
                st.error('Falha na conexão com o servidor Groq.')
                st.stop()
            except Exception as e:
                st.error(f'Erro na API: {e}')
            