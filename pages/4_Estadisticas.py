import streamlit as st
import pandas as pd
import plotly.express as px
from google_connector import get_worksheets

# 1. SEGURIDAD: Bloquear acceso si no ha iniciado sesión
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.error("⚠️ Acceso denegado. Por favor, inicia sesión en la página principal (Home).")
    st.stop()

# --- ENCABEZADO CON BOTÓN DE ACTUALIZAR (INTACTO) ---
col_titulo, col_btn = st.columns([3, 1])

with col_titulo:
    st.markdown("<h1 style='color: #1E3A8A; margin-top: 0;'>📊 Dashboard Analítico y Estadístico</h1>", unsafe_allow_html=True)
    st.write("Análisis en tiempo real del impacto y afluencia del Gimnasio USTA Sede Villavicencio.")

with col_btn:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔄 Actualizar Datos", use_container_width=True):
        st.cache_data.clear()  # Limpia la caché interna de Streamlit
        st.rerun()             # Fuerza la recarga completa de la página

st.markdown("---")

# Obtener las hojas de trabajo desde el conector maestro
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
            
            # --- PREPROCESAMIENTO DE LLAVES DE CRUCE ---
            df_usuarios['Código_Str'] = df_usuarios['Código Institucional o Cédula'].astype(str).str.strip()
            df_asistencias['Código_Str'] = df_asistencias['Código / Cédula'].astype(str).str.strip()
            
            # --- CÁLCULO DE MÉTRICAS ANALÍTICAS MAESTRAS ---
            total_asistencias = len(df_asistencias)
            total_registros_unicos = df_usuarios['Código_Str'].nunique()
            
            # Lógica de Activos vs Inactivos
            codigos_con_asistencia = set(df_asistencias['Código_Str'].unique())
            df_usuarios['Estado_Actividad'] = df_usuarios['Código_Str'].apply(lambda x: "Sí" if x in codigos_con_asistencia else "No")
            
            usuarios_activos_totales = df_usuarios[df_usuarios['Estado_Actividad'] == "Sí"]['Código_Str'].nunique()
            
            # Calcular horario de mayor actividad (Hora Pico)
            hora_pico = "N/A"
            if 'Hora' in df_asistencias.columns:
                try:
                    df_asistencias['Hora_Clean'] = pd.to_datetime(df_asistencias['Hora'], format='%H:%M:%S', errors='coerce').dt.hour
                    if not df_asistencias['Hora_Clean'].dropna().empty:
                        lbl_hora = df_asistencias['Hora_Clean'].mode()[0]
                        hora_pico = f"{lbl_hora}:00"
                except:
                    pass

            # --- 🛠️ FILA DE 4 INDICADORES CLAVE (AHÍ ARRIBITA - INTACTOS) ---
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                with st.container(border=True):
                    st.metric(label="🔢 Total Asistencias", value=f"{total_asistencias} ingresos")
            
            with col2:
                with st.container(border=True):
                    st.metric(label="👥 Total Registros Únicos", value=f"{total_registros_unicos} inscritos")
            
            with col3:
                with st.container(border=True):
                    st.metric(label="✅ Usuarios Activos", value=f"{usuarios_activos_totales} activos")
            
            with col4:
                with st.container(border=True):
                    st.metric(label="⏱️ Horario Mayor Actividad", value=hora_pico)

            st.markdown("<br>", unsafe_allow_html=True)

            # --- SECCIÓN DE GRÁFICAS MAESTRAS (INTACTAS) ---
            st.subheader("📈 Distribución e Impacto Institucional")
            
            g_col1, g_col2 = st.columns(2)
            
            with g_col1:
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

            st.markdown("<br><hr>", unsafe_allow_html=True)

            # --- 📋 SECCIÓN: TABLA DE CONTROL DE ROLES (INTACTA) ---
            st.subheader("📋 Resumen Estadístico por Rol de Usuario")
            
            df_roles_raw = df_usuarios.groupby(['Rol', 'Estado_Actividad']).size().unstack(fill_value=0)
            if 'Sí' not in df_roles_raw.columns: df_roles_raw['Sí'] = 0
            if 'No' not in df_roles_raw.columns: df_roles_raw['No'] = 0
            
            df_roles_raw['Total Registrados'] = df_roles_raw['Sí'] + df_roles_raw['No']
            df_roles_raw = df_roles_raw.rename(columns={
                'Sí': 'Usuarios Activos (Con Asistencias)', 
                'No': 'Usuarios Inactivos (Registrados sin Asistencia)'
            })
            df_roles_final = df_roles_raw.reset_index()[['Rol', 'Total Registrados', 'Usuarios Activos (Con Asistencias)', 'Usuarios Inactivos (Registrados sin Asistencia)']]

            roles_disponibles = ["Mostrar Todos los Roles"] + list(df_roles_final['Rol'].unique())
            filtro_rol = st.selectbox("🎯 Filtrar la tabla por un Rol específico:", roles_disponibles)

            if filtro_rol != "Mostrar Todos los Roles":
                df_mostrar = df_roles_final[df_roles_final['Rol'] == filtro_rol]
            else:
                df_mostrar = df_roles_final

            st.dataframe(df_mostrar, use_container_width=True, hide_index=True)

            st.markdown("<br><hr>", unsafe_allow_html=True)

            # --- 🎂 SECCIÓN EXPANDIDA: ANÁLISIS COMPLETO DE EDADES ---
            st.subheader("🎂 Reporte Demográfico de Edades")
            st.write("Consulte el desglose detallado año por año y los indicadores de estadística descriptiva de la población.")

            if 'Edad' in df_usuarios.columns:
                # Conversión limpia y remoción de vacíos
                df_usuarios['Edad_Num'] = pd.to_numeric(df_usuarios['Edad'], errors='coerce')
                df_usuarios_filtrado = df_usuarios.dropna(subset=['Edad_Num'])

                if not df_usuarios_filtrado.empty:
                    
                    # Generar columnas de visualización doble para las tablas
                    t_col1, t_col2 = st.columns(2)
                    
                    with t_col1:
                        st.markdown("<p style='font-weight: bold; color: #1E3A8A;'>🧮 Cuadro de Estadística Descriptiva</p>", unsafe_allow_html=True)
                        
                        # Cálculos matemáticos puros sobre el DataFrame
                        media_edad = df_usuarios_filtrado['Edad_Num'].mean()
                        mediana_edad = df_usuarios_filtrado['Edad_Num'].median()
                        min_edad = df_usuarios_filtrado['Edad_Num'].min()
                        max_edad = df_usuarios_filtrado['Edad_Num'].max()
                        std_edad = df_usuarios_filtrado['Edad_Num'].std()
                        
                        # Estructuración de la tabla analítica requested
                        df_descriptiva = pd.DataFrame({
                            "Indicador Estadístico": [
                                "🎯 Edad Promedio (Media)", 
                                "📊 Mediana de Edad", 
                                "📉 Edad Mínima Registrada", 
                                "📈 Edad Máxima Registrada", 
                                "📉 Desviación Estándar"
                            ],
                            "Valor Calculado": [
                                f"{media_edad:.1f} años",
                                f"{mediana_edad:.1f} años",
                                f"{int(min_edad)} años",
                                f"{int(max_edad)} años",
                                f"{std_edad:.1f} años"
                            ]
                        })
                        st.dataframe(df_descriptiva, use_container_width=True, hide_index=True)

                    with t_col2:
                        st.markdown("<p style='font-weight: bold; color: #1E3A8A;'>📅 Distribución Frecuencial de Edades</p>", unsafe_allow_html=True)
                        
                        # Generación de la tabla de control de años
                        df_edades = df_usuarios_filtrado['Edad_Num'].value_counts().reset_index()
                        df_edades.columns = ['Edad (Años)', 'Cantidad de Usuarios Inscritos']
                        df_edades['Edad (Años)'] = df_edades['Edad (Años)'].astype(int)
                        df_edades = df_edades.sort_values(by='Edad (Años)')
                        
                        st.dataframe(df_edades, use_container_width=True, hide_index=True)
                        
                else:
                    st.info("No se encontraron registros numéricos válidos en la columna Edad.")
            else:
                st.warning("⚠️ No se detectó la columna 'Edad' en la base de datos de Usuarios.")

        else:
            st.info("📌 Las hojas de cálculo están enlazadas, pero se requiere que existan registros para procesar las métricas.")
            
    except Exception as e:
        st.error(f"❌ Error al procesar el módulo de analítica: {e}")
else:
    st.error("❌ Error de enlace: No se pudo conectar con el servidor central de Google Sheets.")