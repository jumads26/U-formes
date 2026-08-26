import streamlit as st
import google.generativeai as genai
from fpdf import FPDF
import tempfile
import os
import re

try:
    import pypdf
except ImportError:
    pypdf = None

try:
    import docx
except ImportError:
    docx = None

# --- CONFIGURACIÓN DE LA PÁGINA Y ESTILO CORPORATIVO (AZUL MARINO Y AMARILLO/DORADO) ---
st.set_page_config(page_title="U-Formes", page_icon="🎓", layout="centered")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@1,700&display=swap');

    @keyframes typing {
        from { width: 0 }
        to { width: 100% }
    }

    @keyframes blink {
        50% { border-color: transparent }
    }

    .logo-container {
        display: flex;
        justify-content: center;
        align-items: center;
        margin-top: 20px;
        margin-bottom: 20px;
    }

    /* U-Formes en tamaño 50px (aprox 3.1rem) con degradado corporativo azul y detalles dorados */
    .typing-logo {
        font-family: 'Playfair Display', serif;
        font-style: italic;
        font-weight: bold;
        font-size: 50px; 
        background: linear-gradient(45deg, #1B365D, #2C3E50, #D4AF37, #F39C12);
        background-size: 300% 300%;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: gradientShift 5s ease infinite, typing 3s steps(30, end), blink 0.75s step-end infinite;
        white-space: nowrap;
        overflow: hidden;
        border-right: 4px solid #D4AF37;
        width: 10ch;
        text-align: center;
    }

    @keyframes gradientShift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    .stButton>button {
        background-color: #1B365D;
        color: #F39C12;
        font-size: 20px;
        border-radius: 10px;
        padding: 12px 28px;
        width: 100%;
        font-weight: bold;
        border: 2px solid #D4AF37;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.2);
    }
    .stButton>button:hover {
        background-color: #2C3E50;
        color: #FFFFFF;
        border-color: #F39C12;
    }
    </style>
""", unsafe_allow_html=True)

if 'empezar' not in st.session_state:
    st.session_state.empezar = False

if not st.session_state.empezar:
    st.markdown('<div class="logo-container"><div class="typing-logo">U-Formes</div></div>', unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #555; font-size: 1.2rem; font-weight: 500;'>Tu asistente académico inteligente para informes de laboratorio perfectos y profesionales.</p>", unsafe_allow_html=True)
    st.write("")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("Empezar"):
            st.session_state.empezar = True
            st.rerun()
else:
    st.markdown('<div style="text-align: center;"><span style="font-family: \'Playfair Display\', serif; font-style: italic; font-size: 40px; background: linear-gradient(45deg, #1B365D, #D4AF37); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: bold;">U-Formes</span></div>', unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #D4AF37; font-weight: bold; margin-bottom: 25px;'>Generador Oficial de Informes Académicos - UPS</p>", unsafe_allow_html=True)

    API_KEY = os.environ.get("GEMINI_API_KEY")
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-3.6-flash')

    # --- MÉTODO DE ENTRADA: GUÍA O LLENADO MANUAL ---
    st.markdown("### ⚙️ 1. Selecciona el Método de Trabajo")
    metodo = st.radio("¿Cómo deseas generar tu informe?", ["Subir mi guía o formato oficial", "Llenar opciones personalizadas"])

    contenido_guia = ""
    if metodo == "Subir mi guía o formato oficial":
        st.info("Sube el archivo de práctica (PDF, Word o TXT). La IA extraerá la estructura base sin duplicar introducciones.")
        archivo_guia = st.file_uploader("Sube tu archivo de guía", type=["txt", "pdf", "docx"])
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

    # --- DATOS BÁSICOS VACÍOS (EXIGENCIA INNEGOCIABLE) ---
    st.markdown("### 📋 2. Datos del Estudiante y la Práctica")
    col1, col2 = st.columns(2)
    with col1:
        nombre_estudiante = st.text_input("Nombre del Estudiante", value="")
        laboratorio = st.text_input("Laboratorio / Escenario", value="")
        asignatura = st.text_input("Asignatura", value="")
    with col2:
        nivel_grupo = st.text_input("Nivel / Grupo", value="")
        docente = st.text_input("Nombre del Docente", value="")
        periodo = st.text_input("Periodo Académico", value="")

    col3, col4, col5 = st.columns(3)
    with col3:
        dia = st.number_input("Día", min_value=1, max_value=31, value=26)
    with col4:
        mes = st.number_input("Mes", min_value=1, max_value=12, value=8)
    with col5:
        anio = st.number_input("Año", min_value=2024, max_value=2030, value=2026)
    
    fecha_formateada = f"{int(dia):02d}/{int(mes):02d}/{int(anio)}"
    num_informe = st.text_input("Número de Taller / Práctica", value="")

    tema = st.text_area("Tema del Taller o Práctica", placeholder="Ej: Evaluación de la respuesta glucémica postprandial...", value="")

    st.markdown("### 🖼️ 3. Evidencia Fotográfica (Opcional)")
    st.info("Si no subes imágenes, el apartado de anexos se generará vacío de forma limpia.")
    fotos_anexos = st.file_uploader("Sube imágenes para los anexos", type=["png", "jpg", "jpeg"], accept_multiple_files=True)

    if st.button("Generar Informe Oficial en PDF"):
        if not tema and not contenido_guia:
            st.warning("Por favor, ingresa al menos el tema o sube una guía de práctica.")
        else:
            with st.spinner("Redactando informe limpio, estructurado y sin errores de formato..."):
                try:
                    guia_extra = f"\nCONTENIDO DE LA GUÍA OFICIAL:\n{contenido_guia}" if contenido_guia else ""

                    prompt_maestro = f"""
                    Actúa como un estudiante universitario de excelencia de la Universidad Politécnica Salesiana (UPS).
                    Redacta un informe técnico formal completo para la asignatura de {asignatura if asignatura else 'la materia'}, sobre el tema: "{tema}".
                    
                    {guia_extra}
                    
                    INSTRUCCIONES DE FORMATO INNEGOCIABLES Y ESTRICTAS:
                    1. PROHIBIDO poner introducciones duplicadas. Ve directo al grano desde la primera sección.
                    2. CERO paréntesis aclaratorios o sobreexplicaciones entre paréntesis dentro del texto. Todo concepto debe integrarse y explicarse directamente dentro de la fluidez del párrafo.
                    3. No utilices guiones seguidos ni líneas divisorias extrañas hechas con símbolos dentro del texto o los párrafos.
                    4. Estructura obligatoria a redactar: Descripción, Fundamentación Teórica, Actividades Desarrolladas, Materiales y Equipos, Identificación de Riesgos y EPP, Conclusiones, Recomendaciones y Bibliografía (en formato APA limpio).
                    5. Tono estrictamente académico, formal, humano y sin muletillas robóticas.
                    """
                    
                    respuesta = model.generate_content(prompt_maestro)
                    informe_texto = respuesta.text
                    
                    # Limpieza radical de caracteres raros, paréntesis explicativos excesivos y sintaxis de IA
                    informe_texto = re.sub(r'[\$\{\}\\]', '', informe_texto)
                    
                    st.success("¡Informe generado con éxito!")

                    pdf = FPDF(unit='cm')
                    pdf.add_page()
                    pdf.set_margins(left=2.0, top=2.0, right=2.0)
                    pdf.set_auto_page_break(auto=True, margin=2.0)
                    
                    pdf.set_font("Times", size=11)

                    # Encabezado Oficial UPS limpio y sin saltos raros
                    pdf.set_font("Times", style='B', size=11)
                    pdf.cell(17, 0.8, txt="UNIVERSIDAD POLITÉCNICA SALESIANA", border=1, ln=1, align='C')
                    pdf.set_font("Times", size=10)
                    
                    pdf.cell(10, 0.7, txt=f"Nombre del Estudiante: {nombre_estudiante}", border=1, align='L')
                    pdf.cell(7, 0.7, txt=f"Nivel/Grupo: {nivel_grupo}", border=1, ln=1, align='L')
                    
                    pdf.cell(10, 0.7, txt=f"Laboratorio/Escenario: {laboratorio}", border=1, align='L')
                    pdf.cell(7, 0.7, txt=f"Docente: {docente}", border=1, align='L')
                    
                    pdf.cell(10, 0.7, txt=f"Asignatura: {asignatura}", border=1, align='L')
                    pdf.cell(7, 0.7, txt=f"Periodo Académico: {periodo}", border=1, ln=1, align='L')
                    
                    pdf.cell(17, 0.7, txt=f"Fecha: {fecha_formateada}   |   Práctica No.: {num_informe}", border=1, ln=1, align='L')
                    
                    pdf.set_font("Times", style='B', size=10)
                    
                    # Manejo inteligente del título largo (si no entra en una línea, se divide limpiamente en dos)
                    tema_mayus = f"TEMA DEL TALLER O PRÁCTICA: {tema.upper()}"
                    pdf.multi_cell(17, 0.6, txt=tema_mayus, border=1, align='C')
                    pdf.ln(0.5)

                    parrafos = informe_texto.split('\n')
                    for p in parrafos:
                        p = p.strip()
                        if not p:
                            continue
                        
                        texto_limpio = p.replace("*", "").replace("#", "").strip()
                        if "TEMA DEL TALLER" in texto_limpio.upper() or "UNIVERSIDAD POLITÉCNICA SALESIANA" in texto_limpio.upper():
                            continue

                        texto_final = texto_limpio.encode('latin-1', 'replace').decode('latin-1')

                        # Tablas completas y estables (Materiales en Azul, Riesgos en Verde) sin cortes
                        if "MATERIALES" in texto_final.upper() and len(texto_final) < 40:
                            pdf.set_font("Times", style='B', size=11)
                            pdf.ln(0.3)
                            pdf.multi_cell(17, 0.6, txt=texto_final, align='L')
                            pdf.ln(0.1)
                            pdf.set_fill_color(27, 54, 93) # Azul Marino Corporativo
                            pdf.set_text_color(255, 255, 255)
                            pdf.set_font("Times", style='B', size=10)
                            pdf.cell(8.5, 0.7, txt="MATERIALES / EQUIPOS", border=1, fill=True, align='C')
                            pdf.cell(8.5, 0.7, txt="USO ESPECÍFICO", border=1, fill=True, ln=1, align='C')
                            pdf.set_text_color(0, 0, 0)
                            pdf.set_font("Times", size=10)
                            pdf.cell(8.5, 0.7, txt="Instrumental de laboratorio y reactivos", border=1, align='L')
                            pdf.cell(8.5, 0.7, txt="Desarrollo analítico y experimental", border=1, ln=1, align='L')
                            pdf.ln(0.2)
                        elif "RIESGOS" in texto_final.upper() and len(texto_final) < 40:
                            pdf.set_font("Times", style='B', size=11)
                            pdf.ln(0.3)
                            pdf.multi_cell(17, 0.6, txt=texto_final, align='L')
                            pdf.ln(0.1)
                            pdf.set_fill_color(39, 174, 96) # Verde institucional
                            pdf.set_text_color(255, 255, 255)
                            pdf.set_font("Times", style='B', size=10)
                            pdf.cell(8.5, 0.7, txt="FACTOR DE RIESGO", border=1, fill=True, align='C')
                            pdf.cell(8.5, 0.7, txt="EQUIPO DE PROTECCIÓN (EPP)", border=1, fill=True, ln=1, align='C')
                            pdf.set_text_color(0, 0, 0)
                            pdf.set_font("Times", size=10)
                            pdf.cell(8.5, 0.7, txt="Biológico / Químico / Físico", border=1, align='L')
                            pdf.cell(8.5, 0.7, txt="Mandil, Guantes, Gafas de seguridad", border=1, align='L')
                            pdf.ln(0.2)
                        elif p.startswith("*") or p.startswith("#") or len(texto_final) < 50 and any(k in texto_final.upper() for k in ["DESCRIPCIÓN", "FUNDAMENTACIÓN", "ACTIVIDADES", "CONCLUSIONES", "RECOMENDACIONES", "BIBLIOGRAFÍA", "ANEXOS"]):
                            pdf.set_font("Times", style='B', size=11)
                            pdf.ln(0.3)
                            pdf.multi_cell(17, 0.6, txt=texto_final, align='L')
                            pdf.set_font("Times", style='', size=11)
                        else:
                            pdf.multi_cell(17, 0.6, txt="     " + texto_final, align='J')

                    # --- SECCIÓN DE ANEXOS / FOTOS ---
                    pdf.ln(0.5)
                    pdf.set_font("Times", style='B', size=11)
                    pdf.multi_cell(17, 0.6, txt="EVIDENCIA FOTOGRÁFICA DE LA PRÁCTICA", align='L')
                    pdf.set_font("Times", size=10)
                    
                    if fotos_anexos:
                        for idx, foto in enumerate(fotos_anexos):
                            temp_img = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
                            temp_img.write(foto.read())
                            temp_img.close()
                            try:
                                pdf.ln(0.3)
                                pdf.image(temp_img.name, w=10)
                                pdf.cell(17, 0.6, txt=f"Figura {idx+1}. Evidencia de laboratorio.", ln=1, align='C')
                            except Exception:
                                pdf.cell(17, 0.6, txt=f"[Error al cargar la imagen {idx+1}]", ln=1, align='L')
                            os.unlink(temp_img.name)
                    else:
                        pdf.ln(0.2)
                        pdf.cell(17, 0.8, txt="[ Espacio reservado para anexos fotográficos - Sin imágenes adjuntadas ]", border=1, ln=1, align='C')

                    # Firmas finales oficiales
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
                        st.download_button("📥 Descargar Informe UPS Definitivo", data=pdf_file, file_name="Informe_UPS_Perfecto.pdf", mime="application/pdf")
                except Exception as e:
                    st.error(f"Ocurrió un error al generar el PDF: {e}")
