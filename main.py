"""
APLICACAO WEB COM GROQ E STREAMLIT - CHATBOT INTELIGENTE PARA ANALISAR SCRIPTS PYTHON USANDO DIFERENTES MODELOS DE LLM 
Assistente especializado em análise de código Python
"""
# --- IMPORTS
import streamlit as st
from groq import Groq, AuthenticationError, APIConnectionError, RateLimitError

# --- CONFIGURACAO STREAMLIT
st.set_page_config(
    page_title='BiPy - Python Code Assistant',
    page_icon='🐍',
    layout='wide',
    initial_sidebar_state='expanded'
)

# --- INICIALIZAR SESSION STATE
if "messages" not in st.session_state:
    st.session_state.messages = []

if "arquivo_carregado" not in st.session_state:
    st.session_state.arquivo_carregado = None

if "codigo_python" not in st.session_state:
    st.session_state.codigo_python = ""

if "uploaded_file_key" not in st.session_state:
    st.session_state.uploaded_file_key = 0

# --- CONFIGURACOES
MODELOS = [
    'llama-3.3-70b-versatile',
    'llama-3.1-8b-instant',
    'meta-llama/llama-4-maverick-17b-128e-instruct',
    'moonshotai/kimi-k2-instruct',
    'openai/gpt-oss-20b',
    'openai/gpt-oss-120b',
    'qwen/qwen3-32b'
]

SYSTEM_PROMPT_BASE = """Você é um especialista em Python focado em análise de código.

INSTRUÇÕES IMPORTANTES:
- Seja DIRETO e CONCISO
- Use bullet points quando possível
- Limite respostas a 200-300 palavras
- Priorize informações PRÁTICAS e ACIONÁVEIS
- Evite explicações longas ou repetitivas
- Forneça exemplos de código APENAS quando essencial
- Se não houver problemas, diga isso diretamente
- NUNCA fale sobre outras linguagens de programação, se solicitado diga que é especialista em Python."""

PROMPT_ANALISE_ARQUIVO = """Analise este código Python de forma CONCISA:

**Forneça APENAS:**
1. Resumo (1 linha do que faz)
2. Problemas críticos (bugs, vulnerabilidades) - máximo 3 itens
3. Melhorias prioritárias (performance/boas práticas) - máximo 3 itens
4. 1 sugestão principal de refatoração (se necessário)

Seja DIRETO. Use bullet points. Máximo 200 palavras."""

# --- FUNCOES AUXILIARES
def validar_api_key(key):
    """Valida formato da API key da Groq."""
    if not key:
        return False, "API key não pode estar vazia."
    if not key.startswith('gsk_'):
        return False, "API key da Groq deve começar com 'gsk_'"
    if len(key) < 50:
        return False, "API key parece muito curta."
    return True, "API key válida."


def processar_arquivo_python(uploaded_file):
    """Processa arquivo .py e retorna conteúdo."""
    try:
        codigo = uploaded_file.read().decode('utf-8')
        return codigo, True, f"Arquivo {uploaded_file.name} carregado!"
    except UnicodeDecodeError:
        return None, False, "Erro ao decodificar arquivo. Use UTF-8."
    except Exception as e:
        return None, False, f"Erro: {str(e)}"


def gerar_resposta_stream(client, messages, model, temperatura, col_name):
    """Gera resposta com streaming. col_name previne transbordo entre colunas."""
    try:
        stream = client.chat.completions.create(
            messages=messages,
            model=model,
            temperature=temperatura,
            stream=True,
            max_tokens=800
        )
        
        message_placeholder = st.empty()
        full_response = ""
        
        for chunk in stream:
            if chunk.choices[0].delta.content:
                full_response += chunk.choices[0].delta.content
                message_placeholder.markdown(full_response + "▌")
        
        message_placeholder.markdown(full_response)
        return full_response
    
    except AuthenticationError:
        st.error('API key inválida ou expirada.')
        return None
    except RateLimitError:
        st.error('Limite de requisições atingido.')
        return None
    except APIConnectionError:
        st.error('Falha na conexão com Groq.')
        return None
    except Exception as e:
        st.error(f'Erro: {str(e)}')
        return None


def criar_contexto_codigo(codigo, prompt_usuario):
    """Cria mensagem com contexto do código."""
    return f"""📄 **Código Python carregado:**
```python
{codigo}
```

---

**Pergunta:** {prompt_usuario}"""


def limpar_arquivo():
    """Limpa completamente o arquivo e histórico."""
    st.session_state.arquivo_carregado = None
    st.session_state.codigo_python = ""
    st.session_state.messages = []
    st.session_state.uploaded_file_key += 1


def preparar_messages_para_api():
    """
    Converte histórico do session_state para formato da API.
    Combina response_1 e response_2 em uma única mensagem assistant.
    """
    api_messages = []
    
    for msg in st.session_state.messages:
        if msg['role'] == 'user':
            api_messages.append({
                'role': 'user',
                'content': msg['content']
            })
        elif msg['role'] == 'assistant':
            combined_response = f"[Modelo 1]: {msg.get('response_1', '')}\n\n[Modelo 2]: {msg.get('response_2', '')}"
            api_messages.append({
                'role': 'assistant',
                'content': combined_response
            })
    
    return api_messages


# --- SIDEBAR
with st.sidebar:
    st.header('⚙️ Configurações')
    st.markdown('---')
    
    groq_api_key = st.text_input(
        label='API KEY da Groq',
        type='password',
        help='Obtenha em https://console.groq.com/keys'
    )
    
    if groq_api_key:
        valida, mensagem = validar_api_key(groq_api_key)
        if valida:
            st.success(f'✅ {mensagem}')
        else:
            st.error(f'❌ {mensagem}')
    
    st.markdown('---')    
    temperatura = st.slider(
        label='🌡️ Temperatura (ambos modelos)',
        min_value=0.0,
        max_value=2.0,
        step=0.1,
        value=0.3,
        help='Valores baixos: mais focado. Valores altos: mais criativo.'
    )
    
    st.markdown('---')    
    st.subheader('📂 Carregar Código Python')
    
    uploaded_file = st.file_uploader(
        label='Upload arquivo .py',
        type=['py'],
        help='Apenas arquivos Python (.py)',
        key=f'file_uploader_{st.session_state.uploaded_file_key}'
    )
    
    if uploaded_file is not None: # arquivo?
        if st.session_state.arquivo_carregado != uploaded_file.name: # mesmo arquivo?
            codigo, sucesso, mensagem = processar_arquivo_python(uploaded_file)
            
            if sucesso:
                st.session_state.messages = []
                st.session_state.arquivo_carregado = uploaded_file.name
                st.session_state.codigo_python = codigo
                
                st.success(mensagem)
                st.info(f'📊 {len(codigo)} caracteres | {len(codigo.splitlines())} linhas')
                
                mensagem_analise = criar_contexto_codigo(codigo, PROMPT_ANALISE_ARQUIVO)
                st.session_state.messages.append({
                    'role': 'user',
                    'content': mensagem_analise,
                    'display': f"🔍 Analisando arquivo: **{uploaded_file.name}**"
                })
                
                st.rerun()
            else:
                st.error(mensagem)
    
    if st.session_state.arquivo_carregado:
        st.markdown('**Arquivo ativo:**')
        st.code(f"📄 {st.session_state.arquivo_carregado}", language=None)
    
    st.markdown('---')
    
    if st.button('🗑️ Limpar Conversa', use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    
    if st.session_state.arquivo_carregado:
        if st.button('❌ Remover Arquivo', use_container_width=True):
            limpar_arquivo()
            st.rerun()
    
    st.markdown('---')
    st.caption(f'💬 Mensagens: {len(st.session_state.messages)}')

# --- INICIALIZAR CLIENT
client = None
if groq_api_key:
    valida, _ = validar_api_key(groq_api_key)
    if valida:
        try:
            client = Groq(api_key=groq_api_key)
        except Exception as e:
            st.sidebar.error(f'Erro ao inicializar: {e}')

# --- INTERFACE PRINCIPAL
col_title1, col_title2 = st.columns([0.1, 0.9], vertical_alignment='center')
with col_title1:
    st.image('https://static.wikia.nocookie.net/lpunb/images/b/b1/Logo_Python.png', width='content')
with col_title2:
    st.title('Python Code Assistant')
    st.header('Analisador de Scripts Python')
st.caption('Carregue um arquivo .py e compare respostas de dois modelos diferentes simultaneamente')
st.markdown('---')

# --- PREVIEW DO ARQUIVO NA TELA PRINCIPAL
if st.session_state.arquivo_carregado and st.session_state.codigo_python:
    with st.expander(f'👁️ Preview: {st.session_state.arquivo_carregado}', expanded=False):
        linhas_preview = st.session_state.codigo_python.splitlines()[:30]
        preview = '\n'.join(linhas_preview)
        total_linhas = len(st.session_state.codigo_python.splitlines())
        
        if len(linhas_preview) < total_linhas:
            preview += f'\n\n... ({total_linhas - len(linhas_preview)} linhas restantes)'
        
        st.code(preview, language='python')
        
        # Informações do arquivo
        col_info1, col_info2, col_info3 = st.columns(3)
        with col_info1:
            st.metric('📏 Linhas', total_linhas)
        with col_info2:
            st.metric('📝 Caracteres', len(st.session_state.codigo_python))
        with col_info3:
            st.metric('📦 Tamanho', f'{len(st.session_state.codigo_python.encode("utf-8")) / 1024:.1f} KB')
    
    st.markdown('---')

# --- LAYOUT DE DUAS COLUNAS
col1, col2 = st.columns(2)

with col1:
    st.subheader('🤖 Modelo 1')
    model_1 = st.selectbox(
        'Escolha o modelo',
        options=MODELOS,
        index=0,
        key='model_1'
    )

with col2:
    st.subheader('🤖 Modelo 2')
    model_2 = st.selectbox(
        'Escolha o modelo',
        options=MODELOS,
        index=1,
        key='model_2'
    )

st.markdown('---')

# --- EXIBIR HISTÓRICO DE MENSAGENS COM CONTAINERS
for idx, message in enumerate(st.session_state.messages):
    if message['role'] == 'user':
        with st.chat_message('user'):
            display_text = message.get('display', message['content'])
            st.markdown(display_text)
    
    elif message['role'] == 'assistant':
        col1, col2 = st.columns(2)
        
        with col1:
            # CONTAINER PARA MODELO 1
            with st.container(border=True):
                st.caption(f'🤖 {message.get("model_1_name", "Modelo 1")}')
                st.markdown(message.get('response_1', ''))
        
        with col2:
            # CONTAINER PARA MODELO 2
            with st.container(border=True):
                st.caption(f'🤖 {message.get("model_2_name", "Modelo 2")}')
                st.markdown(message.get('response_2', ''))

# --- INPUT DO USUARIO
if prompt := st.chat_input("Digite sua pergunta sobre o código..."):
    if not client:
        st.warning("⚠️ Insira uma API KEY válida na barra lateral.")
        st.stop()
    
    if not st.session_state.arquivo_carregado:
        st.warning("⚠️ Carregue um arquivo .py antes de fazer perguntas.")
        st.stop()
    
    mensagem_com_contexto = criar_contexto_codigo(
        st.session_state.codigo_python, 
        prompt
    )
    
    st.session_state.messages.append({
        'role': 'user',
        'content': mensagem_com_contexto,
        'display': prompt
    })
    
    with st.chat_message('user'):
        st.markdown(prompt)
    
    messages_payload = [{
        'role': 'system',
        'content': SYSTEM_PROMPT_BASE
    }] + preparar_messages_para_api()
    
    # --- RESPOSTAS DOS DOIS MODELOS
    col1, col2 = st.columns(2)
    
    responses = {}
    
    # MODELO 1
    with col1:
        with st.container(border=True):
            st.caption(f'🤖 {model_1}')
            response_1 = gerar_resposta_stream(
                client=client,
                messages=messages_payload,
                model=model_1,
                temperatura=temperatura,
                col_name='col1'
            )
            responses['response_1'] = response_1
    
    # MODELO 2
    with col2:
        with st.container(border=True):
            st.caption(f'🤖 {model_2}')
            response_2 = gerar_resposta_stream(
                client=client,
                messages=messages_payload,
                model=model_2,
                temperatura=temperatura,
                col_name='col2'
            )
            responses['response_2'] = response_2
    
    if responses.get('response_1') and responses.get('response_2'):
        st.session_state.messages.append({
            'role': 'assistant',
            'response_1': responses['response_1'],
            'response_2': responses['response_2'],
            'model_1_name': model_1,
            'model_2_name': model_2
        })