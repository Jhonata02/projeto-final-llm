# streamlit_app.py
import streamlit as st
from src.pipeline import run_pipeline

st.set_page_config(
    page_title="Assistente do Estudante",
    page_icon="🎓",
    layout="wide"
)

st.title("🎓 Assistente do Estudante")
st.markdown(
    "Este assistente ajuda você a entender **regulamentos acadêmicos** "
    "e a **planejar sua matrícula**.\n\n"
)

tab1, tab2 = st.tabs(["💬 Chat Regulamentos", "📅 Automação: Planejador de Matrícula"])

with tab1:
    st.subheader("💬 Tire suas dúvidas sobre o curso")
    st.markdown("Pergunte sobre faltas, créditos, pré-requisitos e jubilamento.")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_q = st.chat_input("Ex: Qual o limite de faltas na disciplina de NLP?")
    if user_q:
        st.chat_message("user").markdown(user_q)
        st.session_state.chat_history.append({"role": "user", "content": user_q})

        with st.chat_message("assistant"):
            with st.spinner("Buscando no regulamento..."):
                try:
                    answer = run_pipeline("chat", user_q, history=st.session_state.chat_history)
                except Exception as e:
                    answer = f"⚠️ Erro ao processar pergunta: {e}"

            st.markdown(answer)
            st.session_state.chat_history.append({"role": "assistant", "content": answer})

with tab2:
    st.subheader("📅 Planejador de Matrícula (Integração MCP)")
    st.markdown("Digite quais matérias você quer cursar neste semestre. O agente irá validar as regras e gerar um plano físico na sua máquina.")

    user_msg = st.text_area("Disciplinas pretendidas:", placeholder="Ex: Quero cursar Percepção Computacional e Engenharia de Software.")
    
    if st.button("Gerar Plano de Matrícula") and user_msg:
        with st.spinner("Analisando regras e salvando plano via MCP..."):
            try:
                analysis = run_pipeline("automation", user_msg)
                st.success("Processo concluído!")
                st.markdown(analysis)
            except Exception as e:
                st.error(f"Erro na automação: {e}")