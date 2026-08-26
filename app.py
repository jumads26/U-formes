import streamlit as st
import google.generativeai as genai
from fpdf import FPDF
import tempfile
import os

st.set_page_config(page_title="U-formes", page_icon="🎓")
st.title("🎓 U-formes (Motor: Gemini)")

# Conexión segura
API_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash-latest')

# --- FORMULARIO DE PORTADA ---
st.markdown("### Datos del Informe")
universidad = st.selectbox("Universidad", ["UCE", "UDLA", "UPS", "PUCE", "UTE", "Otra"])

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

tema = st.text_area("¿De qué trata este informe?", placeholder="Ej: Práctica de laboratorio sobre...")

# --- ESTRUCTURA ---
st.markdown("### Estructura")
opcion_formato = st.radio("Formato:", ["Seleccionar secciones", "Subir formato (.txt)"])

formato_personalizado = ""
secciones_seleccionadas = []

if opcion_formato == "Seleccionar secciones":
    # ¡LISTA DE OPCIONES AMPLIADA!
    opciones = [
        "Título", "Objetivo General", "Objetivos Específicos", 
        "Introducción", "Justificación", "Marco Teórico", 
        "Materiales", "Metodología", "Desarrollo", 
        "Resultados", "Discusión", "Conclusiones", 
        "Recomendaciones", "Tabla de Riesgos", 
        "Bibliografía", "Anexos"
    ]
    secciones_seleccionadas = st.multiselect(
        "Secciones:", 
        opciones, 
        default=["Título", "Objetivo General", "Introducción", "Marco Teórico", "Metodología", "Conclusiones", "Bibliografía"]
    )
else:
    archivo_formato = st.file_uploader("Sube tu formato (.txt)", type=["txt"])
    if archivo_formato:
        formato_personalizado = archivo_formato.getvalue().decode("utf-8")

# --- GENERACIÓN ---
if st.button("Generar Informe (Gratis)"):
    if not tema:
        st.warning("Falta el tema del informe.")
    else:
        with st.spinner("Redactando (Anti-IA activado)..."):
            try:
                if opcion_formato == "Seleccionar secciones":
                    instruccion_est = f"Incluye estrictamente: {', '.join(secciones_seleccionadas)}."
                else:
                    instruccion_est = f"Sigue ESTRICTAMENTE este formato:\n{formato_personalizado}"

                # PROMPT MAESTRO ANTI-DETECTORES IA
                prompt_maestro = f"""
                Actúa como un estudiante universitario ecuatoriano redactando un informe de {materia}.
                Tema: "{tema}".
                {instruccion_est}
                
                REGLAS ANTI-IA Y FORMATO (ESTRICTAS):
                1. Tono humano y pedagógico: Explica los conceptos de forma clara y profesional, sin sonar a máquina.
                2. Perplejidad y ráfaga (Burstiness): Intercala oraciones muy cortas y directas con párrafos más largos y analíticos. Evita estructuras simétricas.
                3. Prohibido usar conectores predecibles: No uses "En resumen", "Es importante destacar", "En conclusión", "Cabe mencionar", "Adicionalmente".
                4. Formato de Títulos: Escribe TODOS los títulos de sección entre dobles asteriscos (ejemplo: **Introducción**). No uses asteriscos para nada más.
                """
                
                respuesta = model.generate_content(prompt_maestro)
                informe_texto = respuesta.text
                
                st.success("¡Informe generado con éxito!")

                # --- CREACIÓN DEL PDF ESTILO APA 7 MODIFICADO ---
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Times", size=12)

                # Portada
                encabezado = f"Universidad: {universidad}\nNombre: {nombre}\nCurso/Semestre: {curso_semestre}\nNivel: {nivel}\nDocente: {docente}\nMateria: {materia}\nFecha: {fecha}\nInforme No.: {num_informe}\n\n"
                pdf.multi_cell(0, 10, txt=encabezado.encode('latin-1', 'replace').decode('latin-1'), align='L')

                # Cuerpo del informe
                parrafos = informe_texto.split('\n')
                for p in parrafos:
                    p = p.strip()
                    if not p:
                        continue
                    
                    texto_limpio = p.replace("**", "").replace("#", "").strip()
                    texto_final = texto_limpio.encode('latin-1', 'replace').decode('latin-1')

                    # Detectar si es título para aplicar negrita
                    if p.startswith("**") or p.startswith("#"):
                        pdf.set_font("Times", style='B', size=12)
                        pdf.multi_cell(0, 10, txt=texto_final, align='L')
                        pdf.set_font("Times", style='', size=12) # Volver a normal
                    else:
                        # Sangría de 5 espacios y justificado (J) con interlineado 2.0 (altura 10)
                        pdf.multi_cell(0, 10, txt="     " + texto_final, align='J')
                
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                    pdf.output(tmp_file.name)
                    
                with open(tmp_file.name, "rb") as pdf_file:
                    st.download_button("Descargar PDF en formato APA", data=pdf_file, file_name="Uforme_Oficial.pdf", mime="application/pdf")
            except Exception as e:
                st.error(f"Error: {e}")
