import streamlit as st
from src.pipeline import get_app

# 1. Configuração da Página (Deve ser a primeira linha)
st.set_page_config(
    page_title="Assistente Acadêmico | UFCG",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Estilização CSS Customizada
st.markdown("""
    <style>
    .stTextArea textarea { font-size: 16px; }
    .stChatMessage { border-radius: 10px; }
    </style>
""", unsafe_allow_html=True)

# 3. Barra Lateral (Sidebar) com informações do projeto corrigidas
with st.sidebar:
    st.title("⚙️ Sobre o Sistema")
    st.markdown("""
    Este assistente utiliza IA Local com arquitetura **Zero-Trust RAG** (Confiança Zero).
    
    **Componentes:**
    - 🧠 **LLM:** Llama 3 / Mistral Local
    - 📚 **Retriever:** ChromaDB (Busca Vetorial Densa)
    - 🛡️ **Segurança:** Nó de *Self-Check* Anti-alucinação
    - 🔌 **Automação:** Integração MCP (Model Context Protocol)
    """)
    
    st.divider()
    
    if st.button("🗑️ Limpar Histórico do Chat", use_container_width=True):
        st.session_state.chat_history = []
        st.rerun()

# 4. Cabeçalho Principal
st.title("🎓 Assistente Acadêmico Inteligente")
st.markdown(
    "Consulte regulamentos da universidade com segurança baseada em documentos oficiais "
    "e planeje sua matrícula de forma automatizada."
)

# 5. Organização em Abas
tab1, tab2 = st.tabs(["💬 Chat de Regulamentos", "📅 Automação: Planejador de Matrícula"])

# ==========================================
# ABA 1: CHAT RAG (ZERO-TRUST)
# ==========================================
with tab1:
    st.info("💡 **Dica:** Pergunte sobre faltas, créditos, pré-requisitos, jubilamento ou revisão de notas.")

    # Inicializa o histórico se não existir
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Renderiza o histórico de mensagens
    for msg in st.session_state.chat_history:
        avatar = "🧑‍🎓" if msg["role"] == "user" else "🤖"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])
            
            # Se for o bot e tiver evidências, mostra o Expander de métricas
            if msg.get("evidences"):
                with st.expander("🔍 Ver Fontes e Evidências Recuperadas"):
                    evs = msg["evidences"]
                    avg_sim = sum(e.get("similarity", 0) for e in evs) / len(evs)
                    st.caption(f"📊 **Similaridade Média das Evidências:** `{avg_sim:.1%}`")
                    
                    for i, ev in enumerate(evs, 1):
                        meta = ev.get("meta", {})
                        src = meta.get("source", "Documento")
                        page = meta.get("page", "-")
                        sim = ev.get("similarity", 0)
                        snippet = ev.get("text", "")[:250].replace("\n", " ") + "..."
                        
                        st.markdown(f"**{i}. {src}** (Pág: {page}) | *Score: {sim:.1%}*")
                        st.info(f"\"{snippet}\"")

    # Caixa de entrada do usuário
    user_q = st.chat_input("Ex: Qual o limite de faltas na disciplina de NLP?")
    
    if user_q:
        # Exibe a pergunta do usuário na tela e salva no histórico
        with st.chat_message("user", avatar="🧑‍🎓"):
            st.markdown(user_q)
        st.session_state.chat_history.append({"role": "user", "content": user_q})

        # Processa a resposta do Assistente
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("Buscando vetores e analisando regulamentos..."):
                try:
                    # Chama o grafo diretamente para conseguirmos capturar as evidências
                    app = get_app()
                    state_out = app.invoke(
                        {"question": user_q, "mode": "chat", "history": st.session_state.chat_history},
                        config={"configurable": {"thread_id": "main"}}
                    )
                    
                    answer = state_out.get("final") or state_out.get("draft") or "NÃO ENCONTREI BASE"
                    evidences = state_out.get("evidences", [])
                    
                    # Filtro de Interface para UX
                    if answer.strip() == "REBUSCAR":
                        answer = "Desculpe, a busca vetorial encontrou trechos com baixa similaridade ou a informação não está explícita nos regulamentos. O *Self-Check* bloqueou a resposta por segurança. Tente reformular a pergunta."
                        
                except Exception as e:
                    answer = f"⚠️ **Erro ao processar pergunta:** {e}"
                    evidences = []

            # Mostra a resposta principal
            st.markdown(answer)
            
            # Desenha as evidências ao vivo (igual no loop do histórico)
            if evidences:
                with st.expander("🔍 Ver Fontes e Evidências Recuperadas"):
                    avg_sim = sum(e.get("similarity", 0) for e in evidences) / len(evidences)
                    st.caption(f"📊 **Similaridade Média das Evidências:** `{avg_sim:.1%}`")
                    for i, ev in enumerate(evidences, 1):
                        meta = ev.get("meta", {})
                        src = meta.get("source", "Documento")
                        page = meta.get("page", "-")
                        sim = ev.get("similarity", 0)
                        snippet = ev.get("text", "")[:250].replace("\n", " ") + "..."
                        
                        st.markdown(f"**{i}. {src}** (Pág: {page}) | *Score: {sim:.1%}*")
                        st.info(f"\"{snippet}\"")
            
            # Salva resposta e evidências no histórico
            st.session_state.chat_history.append({
                "role": "assistant", 
                "content": answer,
                "evidences": evidences
            })

# ==========================================
# ABA 2: AUTOMAÇÃO MCP
# ==========================================
with tab2:
    st.markdown("### 📝 Criador de Plano de Estudos")
    st.write(
        "Digite de forma natural quais matérias você deseja cursar neste semestre. "
        "O agente inteligente irá extrair as disciplinas e se comunicar com o servidor MCP "
        "para validar as regras e salvar o arquivo físico no seu computador."
    )

    user_msg = st.text_area(
        "Disciplinas pretendidas:", 
        placeholder="Ex: Gostaria de cursar Percepção Computacional, Engenharia de Software e Banco de Dados neste semestre.",
        height=150
    )
    
    if st.button("🚀 Gerar e Salvar Plano via MCP", type="primary"):
        if not user_msg.strip():
            st.warning("Por favor, digite as disciplinas que deseja cursar antes de gerar o plano.")
        else:
            with st.spinner("Extraindo entidades e conectando ao Servidor MCP via stdio..."):
                try:
                    app = get_app()
                    out_auto = app.invoke(
                        {"question": user_msg, "mode": "automation"}, 
                        config={"configurable": {"thread_id": "main"}}
                    )
                    analysis = out_auto.get("final", "⚠️ Erro ao gerar resposta.")
                    
                    st.success("✅ Processo de automação concluído com sucesso!")
                    
                    # Exibe o resultado em um container destacado
                    with st.container(border=True):
                        st.markdown(analysis)
                except Exception as e:
                    st.error(f"❌ Erro na automação: {e}")