import streamlit as st
import google.generativeai as genai
from fpdf import FPDF
import tempfile
import os

st.set_page_config(page_title="U-formes", page_icon="🎓")
st.title("🎓 U-formes (Motor: Gemini)")

API_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

universidad = st.selectbox("Selecciona tu Universidad", ["UCE", "UDLA", "UPS", "PUCE", "UTE", "Otra"])
tema = st.text_area("¿De qué trata este informe?", placeholder="Ej: Práctica de laboratorio sobre...")

# --- SECCIÓN: ESTRUCTURA DEL INFORME ---
st.markdown("### Estructura del Informe")
opcion_formato = st.radio(
    "¿Cómo quieres estructurar tu informe?", 
    ["Seleccionar secciones manualmente", "Subir mi propio formato (.txt)"]
)

formato_personalizado = ""
secciones_seleccionadas = []

if opcion_formato == "Seleccionar secciones manualmente":
    opciones_secciones = [
        "Título", "Objetivos", "Introducción", "Desarrollo", 
        "Conclusiones", "Bibliografía", "Tabla de Riesgos", 
        "Tabla de Materiales", "Recomendaciones", "Anexos"
    ]
    secciones_seleccionadas = st.multiselect(
        "Elige las secciones que debe llevar tu informe:", 
        opciones_secciones, 
        default=["Título", "Objetivos", "Introducción", "Desarrollo", "Conclusiones"]
    )
else:
    archivo_formato = st.file_uploader("Sube tu guía o formato (.txt)", type=["txt"])
    if archivo_formato is not None:
        formato_personalizado = archivo_formato.getvalue().decode("utf-8")
        st.success("¡Formato cargado correctamente!")

# --- BOTÓN DE GENERAR ---
if st.button("Generar Informe (Gratis)"):
    if not tema:
        st.warning("Por favor, escribe de qué trata el informe.")
    elif opcion_formato == "Seleccionar secciones manualmente" and not secciones_seleccionadas:
         st.warning("Por favor, selecciona al menos una sección.")
    elif opcion_formato == "Subir mi propio formato (.txt)" and not formato_personalizado:
         st.warning("Por favor, sube un archivo con tu formato.")
    else:
        with st.spinner("Redactando tu informe..."):
            try:
                if opcion_formato == "Seleccionar secciones manualmente":
                    lista_secciones = ", ".join(secciones_seleccionadas)
                    instruccion_estructura = f"El informe debe incluir estrictamente las siguientes secciones: {lista_secciones}."
                else:
                    instruccion_estructura = f"El informe debe seguir ESTRICTAMENTE esta estructura y formato:\n{formato_personalizado}"

                # --- EL NUEVO PROMPT PEDAGÓGICO Y HUMANO ---
                prompt_maestro = f"""
                Eres un estudiante universitario de la {universidad} elaborando un documento académico. 
                Tu tarea es desarrollar un informe sobre el siguiente tema: "{tema}".
                
                {instruccion_estructura}
                
                REGLAS DE ESTILO Y TONO (ESTRICTAS):
                1. Tono pedagógico y semiformal: Explica los conceptos de forma clara, profesional y didáctica, como si le estuvieras enseñando a alguien, pero manteniendo el rigor técnico.
                2. Lenguaje 100% humano: Está estrictamente prohibido usar lenguaje típico de inteligencia artificial. No uses muletillas robóticas (ej: "es fundamental destacar", "en resumen", "podemos concluir", "cabe mencionar").
                3. Cero redundancia: Ve directo al grano. Si ya explicaste una idea, no la repitas con otras palabras. Mantén los párrafos densos en información y concisos.
                """
                
                respuesta = model.generate_content(prompt_maestro)
                informe_texto = respuesta.text
                
                st.success("¡Listo!")
                st.write(informe_texto)

                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", size=11)
                texto_limpio = informe_texto.encode('latin-1', 'replace').decode('latin-1')
                pdf.multi_cell(0, 7, txt=texto_limpio)
                
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                    pdf.output(tmp_file.name)
                    pdf_path = tmp_file.name

                with open(pdf_path, "rb") as pdf_file:
                    st.download_button(
                        label="Descargar PDF",
                        data=pdf_file,
                        file_name="Uforme_Generado.pdf",
                        mime="application/pdf"
                    )
            except Exception as e:
                st.error(f"Error de conexión: {e}")
st.markdown("### Datos de la Portada")
col1, col2 = st.columns(2)
with col1:
    nombre = st.text_input("Tu Nombre")
    curso_semestre = st.text_input("Curso / Semestre")
    nivel = st.text_input("Nivel")
    docente = st.text_input("Nombre del Docente")
with col2:
    materia = st.text_input("Materia")
    fecha = st.text_input("Fecha")
    num_informe = st.text_input("Número de Informe")
  # Crea el PDF con Times New Roman
pdf = FPDF()
pdf.add_page()
pdf.set_font("Times", size=12)

# --- PORTADA / ENCABEZADO ---
encabezado = f"""
Universidad: {universidad}
Nombre: {nombre}
Curso/Semestre: {curso_semestre}
Nivel: {nivel}
Docente: {docente}
Materia: {materia}
Fecha: {fecha}
Informe No.: {num_informe}
"""
# Escribe el encabezado alineado a la izquierda
pdf.multi_cell(0, 10, txt=encabezado.encode('latin-1', 'replace').decode('latin-1'), align='L')
pdf.ln(10) # Salto de línea

# --- CUERPO DEL INFORME (Formato APA modificado) ---
# Separamos el texto por párrafos para aplicar sangría
parrafos = informe_texto.split('\n')
for p in parrafos:
    if p.strip() != "":
        texto_limpio = p.encode('latin-1', 'replace').decode('latin-1')
        # Sangría manual (5 espacios) y justificado (J) con interlineado 2.0 (altura 10)
        pdf.multi_cell(0, 10, txt="     " + texto_limpio, align='J')
