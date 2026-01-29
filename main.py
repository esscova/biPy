"""
APLICACAO WEB - CHATBOT COM GROQ E STREAMLIT 
"""

# --- IMPORTS
import streamlit as st
from groq import Groq

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
GROQ_API_KEY=''
MODEL = ''
TEMPERATURA=1.0
CLIENT = None

# --- SIDEBAR
with st.sidebar:
    st.title('⚙️ Configurações')
    st.markdown('---')

    GROQ_API_KEY = st.text_input(
        label='Insira sua API KEY da Groq',
        type='password',
        help='Obtenha sua chave m https://console.groq.com/keys'
    )

    MODEL = st.text_input(
        label='Selecione seu modelo',
        placeholder='Ex.llama-3.1-8b-instant',
        value='llama-3.1-8b-instant',
        type='default',
        help='Consulte modelos em https://console.groq.com/docs/rate-limits'
    )

    TEMPERATURA = st.slider(
        label='Temperatura',
        min_value=0.1,
        max_value=1.0,
        step=0.1,
        value=0.7
    )

# --- INICIALIZAR CLIENT COM API
if GROQ_API_KEY:
    try:
        CLIENT = Groq(api_key=GROQ_API_KEY)
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
    if not CLIENT:
        st.warning("Por favor, insira a API KEY na barra lateral.")
        st.stop()
    if not MODEL:
        st.warning("Por favor, defina o modelo na barra lateral.")
        st.stop()
    
    st.session_state.messages.append({
        'role':'system',
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
                chat = CLIENT.chat.completions.create(
                    messages=messages_payload,
                    model=MODEL,
                    temperature=TEMPERATURA
                )
                response = chat.choices[0].message.content
                st.markdown(response)
                st.session_state.messages.append({
                    'role':'assistant',
                    'content': response
                })
            except Exception as e:
                st.error(f'Erro na API: {e}')
            