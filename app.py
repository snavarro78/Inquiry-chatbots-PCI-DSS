import streamlit as st
import sys
from pathlib import Path

# Para que Python encuentre los módulos en src/
sys.path.append(str(Path(__file__).resolve().parent / "src"))

from src.chatbot import PCIChatbot

st.set_page_config(
    page_title="Chatbot PCI DSS",
    page_icon="🔒",
    layout="wide"
)

st.title("🔒 Asistente PCI DSS v4.0.1")
st.caption("Consultas sobre requisitos, controles y auditoría — basadas en documentación oficial del PCI SSC")

# Inicializar el chatbot una sola vez por sesión
if "chatbot" not in st.session_state:
    with st.spinner("Cargando base de conocimiento..."):
        st.session_state.chatbot = PCIChatbot()

if "mensajes" not in st.session_state:
    st.session_state.mensajes = []

# Mostrar historial de la conversación
for msg in st.session_state.mensajes:
    with st.chat_message(msg["rol"]):
        st.write(msg["texto"])
        if "fuentes" in msg and msg["fuentes"]:
            with st.expander("📄 Ver fuentes"):
                for f in msg["fuentes"]:
                    st.caption(f"**{f['archivo']}** — p.{f['pagina']}: {f['fragmento']}")

# Input del usuario
if pregunta := st.chat_input("Ej: ¿Qué exige el requisito 8 sobre autenticación?"):

    # Mostrar pregunta del usuario
    st.session_state.mensajes.append({"rol": "user", "texto": pregunta})
    with st.chat_message("user"):
        st.write(pregunta)

    # Generar y mostrar respuesta
    with st.chat_message("assistant"):
        with st.spinner("Buscando en documentos PCI DSS..."):
            resultado = st.session_state.chatbot.responder(pregunta)

        st.write(resultado["respuesta"])

        with st.expander("📄 Ver fuentes"):
            for f in resultado["fuentes"]:
                st.caption(f"**{f['archivo']}** — p.{f['pagina']}: {f['fragmento']}")

    st.session_state.mensajes.append({
        "rol": "assistant",
        "texto": resultado["respuesta"],
        "fuentes": resultado["fuentes"]
    })