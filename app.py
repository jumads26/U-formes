import streamlit as st
import google.generativeai as genai
from fpdf import FPDF
import tempfile
import os
from datetime import datetime

try:
    import pypdf
except ImportError:
    pypdf = None

try:
    import docx
except ImportError:
    docx = None

st.set_page_config(page_title="U-formes UPS Full Tablas", page_icon="🎓")
st.title("🎓 U-formes: Generador UPS con Tablas a Color")

# Conexión con Gemini
API_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# --- DATOS DE LA ASIGNATURA ---
st.markdown("### 📋 Datos de la Asignatura (Encabezado Oficial)")
universidad = "Universidad Politécnica Salesiana"

col1, col2 = st.columns(2)
with col1:
    nombre_estudiante = st.text_input("Nombre del Estudiante")
    laboratorio = st.text_input("Laboratorio / Escenario")
    asignatura = st.text_input("Asignatura")
with col2:
    nivel_grupo = st.text_input("Nivel / Grupo")
    docente = st.text_input("Nombre del Docente")
    periodo = st.text_input("Periodo Académico")

col3, col4 = st.columns(2)
with col3:
    fecha_actual_default = datetime.now().strftime("%d/%m/%Y")
    fecha = st.text_input("Fecha", value=fecha_actual_default)
with col4:
    num_informe = st.text_input("Número de Taller / Práctica")

tema = st.text_area("Tema del Taller o Práctica", placeholder="Ej: Práctica de laboratorio sobre...")

# --- OPCIÓN DE GUÍA ---
st.markdown("### 📄 Guía de Laboratorio (Opcional)")
archivo_guia = st.file_uploader("Sube tu archivo de guía", type=["txt", "pdf", "docx"])

contenido_guia = ""
if archivo_guia is not None:
    extension = archivo_guia.name.split(".")[-1].lower()
    if extension == "txt":
        contenido_guia = archivo_guia.getvalue().decode("utf-8")
    elif extension == "pdf" and pypdf:
        reader = pypdf.PdfReader(archivo_guia)
        for page in reader.pages:
            contenido_guia += page.extract_text() or ""
    elif extension == "docx" and docx:
        doc = docx.Document(archivo_guia)
        for para in doc.paragraphs:
            contenido_guia += para.text + "\n"
    st.success("¡Guía leída con éxito!")

# --- GENERADOR DE INFORME ---
if st.button("Generar Informe Completo con Tablas"):
    if not tema:
        st.warning("Por favor, ingresa el tema del taller o práctica.")
    else:
        with st.spinner("Redactando informe y estructurando tablas a color..."):
            try:
                guia_extra = f"\nINFORMACIÓN ADICIONAL DE LA GUÍA OFICIAL:\n{contenido_guia}" if contenido_guia else ""

                prompt_maestro = f"""
                Actúa como un estudiante universitario de excelencia de la Universidad Politécnica Salesiana (UPS).
                Redacta un informe técnico formal completo para la asignatura de {asignatura}, sobre el tema: "{tema}".
                
                Sigue estrictamente la estructura oficial de prácticas de la UPS[cite: 1], asegurando incluir:
                1. Descripción del Taller o Práctica[cite: 1].
                2. Fundamentación Teórica[cite: 1].
                3. Descripción de las Actividades Desarrolladas[cite: 1].
                4. Materiales y Equipos (genera texto claro que detalle materiales y su uso exacto)[cite: 1].
                5. Identificación de Riesgos y EPP (detallando riesgos físicos, químicos, mecánicos y biológicos)[cite: 1].
                6. Conclusiones técnicas[cite: 1].
                7. Recomendaciones[cite: 1].
                8. Bibliografía en formato APA[cite: 1].
                
                {guia_extra}
                
                REGLAS DE ESTILO ESTRICTAS:
                - Tono técnico, académico y pedagógico, redactado con naturalidad humana.
                - Coloca los títulos de las secciones principales claramente usando asteriscos dobles (ejemplo: **Fundamentación Teórica**).
                """
                
                respuesta = model.generate_content(prompt_maestro)
                informe_texto = respuesta.text
                
                st.success("¡Estructura y tablas generadas con éxito!")

                # --- CREACIÓN DEL PDF CON TABLAS COLOREADAS ---
                pdf = FPDF(unit='cm')
                pdf.add_page()
                pdf.set_margins(left=2.0, top=2.0, right=2.0)
                pdf.set_auto_page_break(auto=True, margin=2.0)
                
                pdf.set_font("Times", size=11)

                # Encabezado Oficial UPS
                pdf.set_font("Times", style='B', size=11)
                pdf.cell(17, 0.8, txt="UNIVERSIDAD POLITÉCNICA SALESIANA", border=1, ln=1, align='C')
                pdf.set_font("Times", size=10)
                
                pdf.cell(10, 0.7, txt=f"Nombre del Estudiante: {nombre_estudiante}", border=1, align='L')
                pdf.cell(7, 0.7, txt=f"Nivel/Grupo: {nivel_grupo}", border=1, ln=1, align='L')
                
                pdf.cell(10, 0.7, txt=f"Laboratorio/Escenario: {laboratorio}", border=1, align='L')
                pdf.cell(7, 0.7, txt=f"Docente: {docente}", border=1, ln=1, align='L')
                
                pdf.cell(10, 0.7, txt=f"Asignatura: {asignatura}", border=1, align='L')
                pdf.cell(7, 0.7, txt=f"Periodo Académico: {periodo}", border=1, ln=1, align='L')
                
                pdf.cell(17, 0.7, txt=f"Fecha: {fecha}   |   Práctica No.: {num_informe}", border=1, ln=1, align='L')
                
                pdf.set_font("Times", style='B', size=10)
                pdf.cell(17, 0.7, txt=f"TEMA DEL TALLER O PRÁCTICA: {tema.upper()}", border=1, ln=1, align='C')
                pdf.ln(0.5)

                # Cuerpo del informe con detección de tablas especiales
                parrafos = informe_texto.split('\n')
                for p in parrafos:
                    p = p.strip()
                    if not p:
                        continue
                    
                    texto_limpio = p.replace("**", "").replace("#", "").strip()
                    texto_final = texto_limpio.encode('latin-1', 'replace').decode('latin-1')

                    if p.startswith("**") or p.startswith("#"):
                        pdf.set_font("Times", style='B', size=11)
                        pdf.ln(0.3)
                        
                        # Si es la sección de Materiales, dibujamos una tabla con encabezado AZUL
                        if "MATERIALES" in texto_final.upper():
                            pdf.multi_cell(17, 0.6, txt=texto_final, align='L')
                            pdf.ln(0.1)
                            # Cabecera Azul
                            pdf.set_fill_color(41, 128, 185) # Azul institucional
                            pdf.set_text_color(255, 255, 255) # Texto blanco
                            pdf.set_font("Times", style='B', size=10)
                            pdf.cell(8.5, 0.7, txt="MATERIALES / EQUIPOS", border=1, fill=True, align='C')
                            pdf.cell(8.5, 0.7, txt="USO ESPECÍFICO", border=1, fill=True, ln=1, align='C')
                            # Fila de ejemplo en blanco
                            pdf.set_text_color(0, 0, 0)
                            pdf.set_font("Times", size=10)
                            pdf.cell(8.5, 0.7, txt="Material principal de práctica", border=1, align='L')
                            pdf.cell(8.5, 0.7, txt="Desarrollo experimental", border=1, ln=1, align='L')
                            pdf.ln(0.2)
                        
                        # Si es la sección de Riesgos, dibujamos una tabla con encabezado VERDE
                        elif "RIESGOS" in texto_final.upper():
                            pdf.multi_cell(17, 0.6, txt=texto_final, align='L')
                            pdf.ln(0.1)
                            # Cabecera Verde
                            pdf.set_fill_color(39, 174, 96) # Verde institucional
                            pdf.set_text_color(255, 255, 255) # Texto blanco
                            pdf.set_font("Times", style='B', size=10)
                            pdf.cell(8.5, 0.7, txt="FACTOR DE RIESGO", border=1, fill=True, align='C')
                            pdf.cell(8.5, 0.7, txt="EQUIPO DE PROTECCIÓN (EPP)", border=1, fill=True, ln=1, align='C')
                            # Fila de ejemplo en blanco
                            pdf.set_text_color(0, 0, 0)
                            pdf.set_font("Times", size=10)
                            pdf.cell(8.5, 0.7, txt="Riesgo Físico / Químico", border=1, align='L')
                            pdf.cell(8.5, 0.7, txt="Gafas, Guantes, Mascarilla", border=1, ln=1, align='L')
                            pdf.ln(0.2)
                        else:
                            pdf.multi_cell(17, 0.6, txt=texto_final, align='L')
                            
                        pdf.set_font("Times", style='', size=11)
                    else:
                        pdf.multi_cell(17, 0.6, txt="     " + texto_final, align='J')

                # Sección de Firmas finales
                pdf.ln(1.0)
                pdf.set_font("Times", style='B', size=10)
                pdf.cell(8.5, 0.6, txt="NOMBRES Y APELLIDOS DEL ESTUDIANTE", border=1, align='C')
                pdf.cell(8.5, 0.6, txt="FIRMA", border=1, ln=1, align='C')
                
                pdf.set_font("Times", size=10)
                pdf.cell(8.5, 1.2, txt=f"{nombre_estudiante}", border=1, align='C')
                pdf.cell(8.5, 1.2, txt="", border=1, ln=1, align='C')
                
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                    pdf.output(tmp_file.name)
                    
                with open(tmp_file.name, "rb") as pdf_file:
                    st.download_button("📥 Descargar Informe Completo con Tablas a Color", data=pdf_file, file_name="Informe_UPS_Tablas.pdf", mime="application/pdf")
            except Exception as e:
                st.error(f"Error al generar el PDF: {e}")
