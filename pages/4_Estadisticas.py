import streamlit as st
import pandas as pd
import plotly.express as px
from google_connector import get_worksheets

# 1. SEGURIDAD: Bloquear acceso si no ha iniciado sesión
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.error("⚠️ Acceso denegado. Por favor, inicia sesión en la página principal (Home).")
    st.stop()

# Encabezado de la página
st.markdown("<h1 style='color: #1E3A8A; margin-top: 0;'>📊 Dashboard Analítico y Estadístico</h1>", unsafe_allow_html=True)
st.write("Análisis en tiempo real de la afluencia, demografía e impacto del Gimnasio USTA Sede Villavicencio.")
st.markdown("---")

# Obtener las hojas de trabajo desde tu conector maestro
sheet_usuarios, sheet_asistencias = get_worksheets()

if sheet_usuarios and sheet_asistencias:
    try:
        # Cargar los datos reales desde Google Sheets
        usuarios_data = sheet_usuarios.get_all_records()
        asistencias_data = sheet_asistencias.get_all_records()

        df_usuarios = pd.DataFrame(usuarios_data)
        df_asistencias = pd.DataFrame(asistencias_data)

        # Validar que ambas hojas contengan datos para procesar
        if not df_asistencias.empty and not df_usuarios.empty:
            
            # --- CÁLCULO DE MÉTRICAS ANALÍTICAS ---
            total_asistencias = len(df_asistencias)
            
            # 🔥 AQUÍ ESTÁ TU NUEVA MÉTRICA: Contamos los códigos únicos de la pestaña Usuarios
            total_registros_unicos = df_usuarios['Código Institucional o Cédula'].nunique()
            
            # Calcular horario de mayor actividad (Hora Pico) si existe la columna
            hora_pico = "N/A"
            if 'Hora' in df_asistencias.columns:
                try:
                    df_asistencias['Hora_Clean'] = pd.to_datetime(df_asistencias['Hora'], format='%H:%M:%S', errors='coerce').dt.hour
                    if not df_asistencias['Hora_Clean'].dropna().empty:
                        lbl_hora = df_asistencias['Hora_Clean'].mode()[0]
                        hora_pico = f"{lbl_hora}:00"
                except:
                    pass

            # --- 🛠️ FILA DE INDICADORES CLAVE (AHÍ ARRIBITA) ---
            col1, col2, col3 = st.columns(3)
            
            with col1:
                with st.container(border=True):
                    st.metric(label="🔢 Total Asistencias", value=f"{total_asistencias} ingresos")
            
            with col2:
                with st.container(border=True):
                    # Tu indicador solicitado con diseño institucional
                    st.metric(label="👥 Total Registros Únicos", value=f"{total_registros_unicos} usuarios")
            
            with col3:
                with st.container(border=True):
                    st.metric(label="⏱️ Horario de Mayor Actividad", value=hora_pico)

            st.markdown("<br>", unsafe_allow_html=True)

            # --- SECCIÓN DE GRÁFICAS MAESTRAS ---
            st.subheader("📈 Distribución e Impacto Institucional")
            
            g_col1, g_col2 = st.columns(2)
            
            with g_col1:
                # Estandarizar códigos para el cruce de datos de Facultad
                df_usuarios['Código_Str'] = df_usuarios['Código Institucional o Cédula'].astype(str).str.strip()
                df_asistencias['Código_Str'] = df_asistencias['Código / Cédula'].astype(str).str.strip()
                
                # Cruzar tablas para traer la Facultad al historial de asistencia
                df_merge = pd.merge(df_asistencias, df_usuarios[['Código_Str', 'Facultad / Área']], on='Código_Str', how='left')
                df_asistencias['Facultad / Área'] = df_merge['Facultad / Área']
                
                if not df_asistencias['Facultad / Área'].dropna().empty:
                    df_fac = df_asistencias['Facultad / Área'].value_counts().reset_index()
                    df_fac.columns = ['Facultad', 'Asistencias']
                    fig_fac = px.bar(df_fac, x='Asistencias', y='Facultad', orientation='h', 
                                     title="Asistencias por Facultad / Área",
                                     color_discrete_sequence=['#1E3A8A'])
                    st.plotly_chart(fig_fac, use_container_width=True)
                else:
                    st.info("Aún no hay datos suficientes de facultades para graficar.")

            with g_col2:
                # Cruzar tablas para traer el Género al historial de asistencia
                df_merge_gen = pd.merge(df_asistencias, df_usuarios[['Código_Str', 'Género']], on='Código_Str', how='left')
                df_asistencias['Género'] = df_merge_gen['Género']
                
                if not df_asistencias['Género'].dropna().empty:
                    df_gen = df_asistencias['Género'].value_counts().reset_index()
                    df_gen.columns = ['Género', 'Cantidad']
                    fig_gen = px.pie(df_gen, values='Cantidad', names='Género', 
                                     title="Distribución de Asistencias por Género",
                                     color_discrete_sequence=['#1E3A8A', '#B59410'])
                    st.plotly_chart(fig_gen, use_container_width=True)
                else:
                    st.info("Aún no hay datos suficientes de género para graficar.")

        else:
            st.info("📌 Las hojas de cálculo están enlazadas, pero se requiere que existan registros de usuarios y asistencias para procesar las métricas.")
            
    except Exception as e:
        st.error(f"❌ Error al procesar el módulo de analítica: {e}")
else:
    st.error("❌ Error de enlace: No se pudo conectar con el servidor central de Google Sheets.")