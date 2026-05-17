import streamlit as st
import os

# 1. Configuración de la página (Debe ser lo primero)
st.set_page_config(
    page_title="Panel Administrativo - Gimnasio USTA",
    page_icon="🏋️‍♂️",
    layout="wide"
)

# 2. Inicializar el estado de la sesión para el Login
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# 3. Formulario de Login (Si no está logueado, bloquea todo)
if not st.session_state.logged_in:
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>🔐 Acceso Administrativo</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #64748B;'>Gimnasio Universidad Santo Tomás - Sede Villavicencio</p>", unsafe_allow_html=True)
    st.markdown("<hr style='border: 1px solid #CBD5E1;'>", unsafe_allow_html=True)
    
    # Centrar el formulario usando columnas
    col1, col2, col3 = st.columns([1, 1.2, 1])
    
    with col2:
        with st.form("login_admin"):
            st.markdown("<h4 style='text-align: center;'>Ingresa la Contraseña Maestra</h4>", unsafe_allow_html=True)
            password = st.text_input("Contraseña", type="password", label_visibility="collapsed")
            btn_ingresar = st.form_submit_button("Ingresar al Sistema", use_container_width=True)
            
            if btn_ingresar:
                # Contraseña profesional configurada
                if password == "GimnasioUstaPro":
                    st.session_state.logged_in = True
                    st.success("¡Acceso concedido exitosamente!")
                    st.rerun()
                else:
                    st.error("❌ Contraseña incorrecta. Intenta nuevamente.")
                    
    # st.stop() evita que se ejecute el código de abajo si no ha iniciado sesión
    st.stop()

# --- SI LLEGA AQUÍ, SIGNIFICA QUE YA INICIÓ SESIÓN CORRECTAMENTE ---

# 4. Diseño de la Página de Bienvenida (Home)
col_logo, col_titulo = st.columns([1, 4])

with col_logo:
    # Validamos que el logo exista en tu carpeta assets antes de mostrarlo
    ruta_logo = "assets/usta.jpg"
    if os.path.exists(ruta_logo):
        st.image(ruta_logo, width=150)
    else:
        st.warning("⚠️ Logo 'usta.jpg' no encontrado en assets/")

with col_titulo:
    st.markdown("<h1 style='color: #1E3A8A; margin-bottom: 0;'>Sistema de Gestión Deportiva</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='color: #B59410; margin-top: 0;'>Panel de Control del Administrador</h3>", unsafe_allow_html=True)

st.markdown("<hr style='border: 1px solid #1E3A8A;'>", unsafe_allow_html=True)

# 5. Panel de Información e Instructivos
st.markdown("### 📋 Instructivo de Uso General")
st.write(
    "Bienvenido al panel central de administración del Gimnasio USTA Villavicencio. "
    "Desde el menú lateral izquierdo puedes navegar de forma segura por los diferentes módulos de la aplicación:"
)

# --- NUEVA DISTRIBUCIÓN DE TARJETAS EN CUADRÍCULA ---

# Fila 1: 3 Columnas para los primeros tres módulos
row1_col1, row1_col2, row1_col3 = st.columns(3)

with row1_col1:
    with st.container(border=True):
        st.markdown("#### 👥 Gestión de Usuarios")
        st.write("Permite visualizar la base de datos de inscritos. "
                 "Cuenta con herramientas integradas para **buscar**, **editar datos erróneos** o **eliminar registros** en tiempo real.")

with row1_col2:
    with st.container(border=True):
        st.markdown("#### 📅 Historial Asistencias")
        st.write("Módulo para rastrear los ingresos. Cruza los datos automáticamente para mostrar **Nombres** y **Facultades** junto a la hora de entrada.")

with row1_col3:
    with st.container(border=True):
        st.markdown("#### 👤 Perfil Individual")
        st.write("Buscador especializado por código. Genera una **Ficha Técnica** con datos de emergencia, RH y un **contador total** de asistencias por usuario.")

# Espacio entre filas
st.markdown("<br>", unsafe_allow_html=True)

# Fila 2: Ahora con 3 Columnas para incluir el módulo de Mantenimiento
row2_col1, row2_col2, row2_col3 = st.columns(3)

with row2_col1:
    with st.container(border=True):
        st.markdown("#### 📊 Dashboard Estadístico")
        st.write("Muestra de forma gráfica la analítica global del gimnasio: distribución por géneros, "
                 "porcentaje de asistencia según facultades y picos de afluencia por horarios.")

with row2_col2:
    with st.container(border=True):
        st.markdown("#### 📥 Descargar Reportes")
        st.write("Sección optimizada para la exportación de información. Genera y descarga los archivos en formato "
                 "Excel (.xlsx) listos para informes institucionales.")

with row2_col3:
    with st.container(border=True):
        st.markdown("#### 🛡️ Auditoría y Control")
        st.write("Módulo de mantenimiento seguro para depuración de datos históricos. Cuenta con doble verificación y bitácora de trazabilidad legal.")

# Botón para cerrar sesión en la barra lateral
st.sidebar.markdown("---")
if st.sidebar.button("🚪 Cerrar Sesión", use_container_width=True):
    st.session_state.logged_in = False
    st.rerun()