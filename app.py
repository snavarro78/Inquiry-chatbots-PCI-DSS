import sys
from pathlib import Path
import streamlit as st

# Para que Python encuentre los módulos en src/
sys.path.append(str(Path(__file__).resolve().parent / "src"))

from src.chatbot import PCIChatbot


st.set_page_config(
    page_title="Chatbot PCI DSS",
    page_icon="🔒",
    layout="wide"
)

st.title("🔒 Asistente PCI DSS v4.0.1")
st.caption(
    "Consultas sobre requisitos, controles y auditoría — "
    "basadas en documentación oficial del PCI SSC"
)

# Barra lateral
with st.sidebar:

    st.subheader("Acerca del sistema")

    st.caption(
        "Este chatbot responde consultas sobre PCI DSS v4.0.1 "
        "utilizando búsqueda semántica en ChromaDB y el modelo "
        "de lenguaje Groq."
    )

    st.divider()

    st.header("Acciones")

    if st.button("Limpiar conversación"):
        st.session_state.mensajes = []
        st.rerun()
        
# Inicializar el chatbot una sola vez por sesión
if "chatbot" not in st.session_state:
    with st.spinner("Cargando base de conocimiento..."):
        st.session_state.chatbot = PCIChatbot()

# Inicializar el historial
if "mensajes" not in st.session_state:
    st.session_state.mensajes = []

# Mensaje de bienvenida
if len(st.session_state.mensajes) == 0:
    with st.chat_message("assistant"):
        st.markdown(
            """
¡Bienvenido!

Puedes hacer preguntas como:

- ¿Qué exige el requisito 8 sobre autenticación?
- ¿Qué controles establece el requisito 10?
- ¿Qué dice PCI DSS sobre el cifrado de datos?
- ¿Qué establece el requisito 3?
- ¿Qué es la autenticación multifactor (MFA)?

Las respuestas se generan exclusivamente a partir de la documentación oficial de PCI DSS v4.0.1.
"""
        )

# Mostrar historial de la conversación
for mensaje in st.session_state.mensajes:
    with st.chat_message(mensaje["rol"]):
        st.write(mensaje["texto"])

        if mensaje.get("fuentes"):
            with st.expander("📄 Ver fuentes"):
                for i, fuente in enumerate(mensaje["fuentes"], start=1):
                    st.markdown(f"**Fuente {i}**")
                    st.write(f"**Documento:** {fuente['archivo']}")
                    st.write(f"**Página:** {fuente['pagina']}")
                    st.info(fuente["fragmento"])

# Entrada del usuario
pregunta = st.chat_input(
    "Ej: ¿Qué exige el requisito 8 sobre autenticación?"
)

if pregunta:
    # Guardar y mostrar la pregunta
    st.session_state.mensajes.append(
        {
            "rol": "user",
            "texto": pregunta
        }
    )

    with st.chat_message("user"):
        st.write(pregunta)

    # Generar y mostrar la respuesta
    with st.chat_message("assistant"):
        with st.spinner("Buscando en documentos PCI DSS..."):
            resultado = st.session_state.chatbot.responder(pregunta)

        respuesta = resultado.get("respuesta", "")
        fuentes = resultado.get("fuentes", [])

        if respuesta:
            st.write(respuesta)
        else:
            st.warning(
                "No se encontró información suficiente en la documentación "
                "para responder esa consulta."
            )

        if fuentes:
            with st.expander("📄 Ver fuentes"):
                for i, fuente in enumerate(fuentes, start=1):
                    st.markdown(f"**Fuente {i}**")
                    st.write(f"**Documento:** {fuente['archivo']}")
                    st.write(f"**Página:** {fuente['pagina']}")
                    st.info(fuente["fragmento"])

    # Guardar la respuesta en el historial
    st.session_state.mensajes.append(
        {
            "rol": "assistant",
            "texto": respuesta,
            "fuentes": fuentes
        }
    )