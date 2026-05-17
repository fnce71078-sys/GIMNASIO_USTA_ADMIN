import streamlit as st
import pandas as pd
import altair as alt
from google_connector import get_worksheets
from datetime import datetime

# 1. SEGURIDAD: Bloquear acceso si no ha iniciado sesión
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.error("⚠️ Acceso denegado. Por favor, inicia sesión en la página principal (Home).")
    st.stop()

# 2. ENCABEZADO Y BOTÓN DE ACTUALIZACIÓN
col_titulo, col_btn = st.columns([3, 1])

with col_titulo:
    st.markdown("<h1 style='color: #1E3A8A; margin-top: 0;'>📊 Dashboard Analítico y Estadístico</h1>", unsafe_allow_html=True)
    st.write("Análisis de afluencia e impacto del Gimnasio USTA. Usa los filtros para recalcular las gráficas.")
    
with col_btn:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔄 Actualizar Tablero", use_container_width=True, type="primary"):
        st.rerun()

st.markdown("---")

# 3. CONEXIÓN A GOOGLE SHEETS
sheet_usuarios, sheet_asistencias = get_worksheets()

if sheet_usuarios and sheet_asistencias:
    try:
        datos_usuarios = sheet_usuarios.get_all_records()
        datos_asistencias = sheet_asistencias.get_all_records()
        
        df_usu = pd.DataFrame(datos_usuarios) if datos_usuarios else pd.DataFrame()
        df_asis = pd.DataFrame(datos_asistencias) if datos_asistencias else pd.DataFrame()

        if not df_asis.empty and not df_usu.empty:
            
            # --- 4. LIMPIEZA EXTREMA DE CÓDIGOS ANTES DEL CRUCE ---
            # Quitamos el '.0' si Python lo interpretó como decimal, y eliminamos espacios laterales
            df_asis['Código / Cédula'] = df_asis['Código / Cédula'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
            df_usu['Código Institucional o Cédula'] = df_usu['Código Institucional o Cédula'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
            
            # Formatear fechas para el calendario
            df_asis['Fecha_dt'] = pd.to_datetime(df_asis['Fecha'], errors='coerce').dt.date
            
            # Cruzar asistencias con los datos de los usuarios
            df_cruce = pd.merge(
                df_asis, 
                df_usu[['Código Institucional o Cédula', 'Rol', 'Facultad / Área', 'Género']], 
                left_on='Código / Cédula', 
                right_on='Código Institucional o Cédula', 
                how='left'
            )
            
            # Llenar vacíos solo por si entra alguien verdaderamente nuevo que no se ha registrado
            df_cruce['Rol'] = df_cruce['Rol'].fillna("Externo/No Registrado")
            df_cruce['Facultad / Área'] = df_cruce['Facultad / Área'].fillna("No Registrada")
            df_cruce['Género'] = df_cruce['Género'].fillna("No Registrado")

            # 5. BARRA DE FILTROS INTELIGENTES
            st.subheader("🔍 Filtros Dinámicos del Tablero")
            
            fechas_validas = df_cruce['Fecha_dt'].dropna()
            min_date = fechas_validas.min() if not fechas_validas.empty else datetime.today().date()
            max_date = fechas_validas.max() if not fechas_validas.empty else datetime.today().date()
            
            roles_disponibles = ["Todos"] + sorted(df_cruce['Rol'].unique().tolist())
            
            f_col1, f_col2 = st.columns(2)
            with f_col1:
                rango_fechas = st.date_input("📅 Rango de Fechas:", value=(min_date, max_date), min_value=min_date, max_value=max_date)
            with f_col2:
                rol_seleccionado = st.selectbox("👤 Filtrar por Rol:", options=roles_disponibles)

            # Aplicar Filtros
            df_filtrado = df_cruce.copy()
            
            if len(rango_fechas) == 2:
                df_filtrado = df_filtrado[(df_filtrado['Fecha_dt'] >= rango_fechas[0]) & (df_filtrado['Fecha_dt'] <= rango_fechas[1])]
            elif len(rango_fechas) == 1:
                df_filtrado = df_filtrado[df_filtrado['Fecha_dt'] == rango_fechas[0]]
                
            if rol_seleccionado != "Todos":
                df_filtrado = df_filtrado[df_filtrado['Rol'] == rol_seleccionado]

            st.markdown("<br>", unsafe_allow_html=True)

            # 6. BLOQUE A: INDICADORES CLAVE (KPIs)
            st.subheader(f"📈 Indicadores del Período Seleccionado")
            
            afluencia_total = len(df_filtrado)
            usuarios_unicos = df_filtrado['Código / Cédula'].nunique()
            frecuencia_promedio = round(afluencia_total / usuarios_unicos, 1) if usuarios_unicos > 0 else 0
            
            kpi1, kpi2, kpi3 = st.columns(3)
            with kpi1:
                st.metric(label="Total Asistencias (Afluencia)", value=f"{afluencia_total}")
            with kpi2:
                st.metric(label="Usuarios Únicos Activos", value=f"{usuarios_unicos}")
            with kpi3:
                st.metric(label="Frecuencia Promedio", value=f"{frecuencia_promedio} visitas/usuario")

            st.markdown("---")

            # 7. BLOQUE B: GRÁFICAS DEMOGRÁFICAS Y DE CONSUMO CON ALTAIR
            col_graf1, col_graf2 = st.columns(2)
            
            with col_graf1:
                st.markdown("#### 🚻 Afluencia por Género")
                if afluencia_total > 0:
                    df_gen = df_filtrado['Género'].value_counts().reset_index()
                    df_gen.columns = ['Género', 'Cantidad']
                    
                    # Crear gráfica Premium
                    graf_genero = alt.Chart(df_gen).mark_bar(color="#1E3A8A", cornerRadiusTopLeft=5, cornerRadiusTopRight=5).encode(
                        x=alt.X('Género', sort='-y', title=None, axis=alt.Axis(labelAngle=0)),
                        y=alt.Y('Cantidad', title='Asistencias'),
                        tooltip=['Género', 'Cantidad']
                    ).properties(height=350)
                    
                    # Poner número sobre la barra
                    texto_genero = graf_genero.mark_text(align='center', baseline='bottom', dy=-5, fontSize=14, fontWeight='bold', color='black').encode(text='Cantidad')
                    
                    st.altair_chart(graf_genero + texto_genero, use_container_width=True)
                else:
                    st.info("No hay datos en este rango.")
                    
            with col_graf2:
                st.markdown("#### 🏫 Impacto por Facultad / Área")
                if afluencia_total > 0:
                    df_fac = df_filtrado['Facultad / Área'].value_counts().reset_index()
                    df_fac.columns = ['Facultad', 'Cantidad']
                    
                    graf_facultad = alt.Chart(df_fac).mark_bar(color="#B59410", cornerRadiusTopLeft=5, cornerRadiusTopRight=5).encode(
                        x=alt.X('Facultad', sort='-y', title=None, axis=alt.Axis(labelAngle=-45)),
                        y=alt.Y('Cantidad', title='Asistencias'),
                        tooltip=['Facultad', 'Cantidad']
                    ).properties(height=350)
                    
                    texto_facultad = graf_facultad.mark_text(align='center', baseline='bottom', dy=-5, fontSize=14, fontWeight='bold', color='black').encode(text='Cantidad')
                    
                    st.altair_chart(graf_facultad + texto_facultad, use_container_width=True)
                else:
                    st.info("No hay datos en este rango.")

            st.markdown("---")

            # 8. BLOQUE C: TABLA EJECUTIVA (RESUMEN POR ROLES)
            st.subheader("📋 Resumen de Participación por Roles")
            if afluencia_total > 0:
                resumen_roles = df_filtrado.groupby('Rol').agg(
                    Total_Asistencias=('Código / Cédula', 'count'),
                    Usuarios_Unicos=('Código / Cédula', 'nunique')
                ).reset_index()
                
                resumen_roles.columns = ['Rol del Usuario', 'Asistencias Registradas', 'Personas Diferentes']
                st.dataframe(resumen_roles, use_container_width=True, hide_index=True)
            else:
                st.info("No hay participaciones para mostrar con los filtros actuales.")

        else:
            st.warning("⚠️ Faltan datos. Se requiere que existan usuarios inscritos y registros de asistencia para calcular las estadísticas.")

    except Exception as e:
        st.error(f"❌ Error al procesar las métricas analíticas: {e}")
else:
    st.error("❌ No se pudo establecer conexión con Google Sheets.")