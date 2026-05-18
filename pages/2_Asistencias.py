import streamlit as st
import pandas as pd
from google_connector import get_worksheets
from datetime import datetime

# 1. SEGURIDAD: Bloquear acceso si no ha iniciado sesión
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.error("⚠️ Acceso denegado. Por favor, inicia sesión en la página principal (Home).")
    st.stop()

# 2. Títulos y encabezados
st.markdown("<h1 style='color: #1E3A8A;'>📅 Historial de Asistencias Detallado</h1>", unsafe_allow_html=True)
st.write("Monitorea los ingresos al gimnasio. Esta tabla se actualiza sola automáticamente cada 30 segundos con los datos reales de Google Sheets.")
st.markdown("---")

# 3. CREACIÓN DEL FRAGMENTO DE AUTO-REFRESCO (Cada 30 segundos)
@st.fragment(run_every=30)
def contenedor_asistencias_tiempo_real():
    # Conectar a Google Sheets dentro del fragmento para traer datos frescos
    sheet_usuarios, sheet_asistencias = get_worksheets()

    if sheet_usuarios and sheet_asistencias:
        try:
            # Traemos la información de ambas hojas
            datos_usuarios = sheet_usuarios.get_all_records()
            datos_asistencias = sheet_asistencias.get_all_records()
            
            if datos_asistencias:
                df_asis = pd.DataFrame(datos_asistencias)
                df_usu = pd.DataFrame(datos_usuarios) if datos_usuarios else pd.DataFrame()
                
                # Limpiar los códigos para asegurar que coincidan perfectamente
                if 'Código / Cédula' in df_asis.columns:
                    df_asis['Código / Cédula'] = df_asis['Código / Cédula'].astype(str).str.strip()
                
                if not df_usu.empty and 'Código Institucional o Cédula' in df_usu.columns:
                    df_usu['Código Institucional o Cédula'] = df_usu['Código Institucional o Cédula'].astype(str).str.strip()
                    
                    # Cruzamos los datos (BuscarV interno)
                    df_usu_reducido = df_usu[['Código Institucional o Cédula', 'Nombre Completo', 'Facultad / Área']]
                    df_completo = pd.merge(
                        df_asis, 
                        df_usu_reducido, 
                        left_on='Código / Cédula', 
                        right_on='Código Institucional o Cédula', 
                        how='left'
                    )
                    
                    # Alertas por si acaso
                    df_completo['Nombre Completo'] = df_completo['Nombre Completo'].fillna("⚠️ Usuario no registrado")
                    df_completo['Facultad / Área'] = df_completo['Facultad / Área'].fillna("N/A")
                    
                    # Organizar columnas
                    columnas_finales = ['Código / Cédula', 'Nombre Completo', 'Facultad / Área', 'Fecha', 'Hora']
                    columnas_presentes = [col for col in columnas_finales if col in df_completo.columns]
                    df_completo = df_completo[columnas_presentes]
                    
                else:
                    df_completo = df_asis.copy()
                    
                # Convertimos la columna Fecha para el filtro de calendario
                if 'Fecha' in df_completo.columns:
                    df_completo['Fecha_dt'] = pd.to_datetime(df_completo['Fecha'], errors='coerce').dt.date

                # --- SECCIÓN A: FILTROS DE BÚSQUEDA ---
                st.subheader("🔍 Filtros Avanzados")
                col1, col2 = st.columns(2)
                
                with col1:
                    filtro_texto = st.text_input("🔍 Buscar por Código o Nombre:")
                    
                with col2:
                    if 'Fecha_dt' in df_completo.columns:
                        fechas_unicas = df_completo['Fecha_dt'].dropna().unique()
                        if len(fechas_unicas) > 0:
                            min_date = min(fechas_unicas)
                            max_date = max(fechas_unicas)
                            filtro_fecha = st.date_input(
                                "📅 Filtrar por Rango de Fechas:",
                                value=(min_date, max_date),
                                min_value=min_date,
                                max_value=max_date
                            )
                        else:
                            filtro_fecha = []
                    else:
                        filtro_fecha = []
                        
                # --- APLICAR LOS FILTROS AL DATAFRAME ---
                df_filtrado = df_completo.copy()
                
                if filtro_texto:
                    mask_codigo = df_filtrado['Código / Cédula'].str.contains(filtro_texto, case=False, na=False)
                    if 'Nombre Completo' in df_filtrado.columns:
                        mask_nombre = df_filtrado['Nombre Completo'].str.contains(filtro_texto, case=False, na=False)
                        df_filtrado = df_filtrado[mask_codigo | mask_nombre]
                    else:
                        df_filtrado = df_filtrado[mask_codigo]
                        
                if len(filtro_fecha) == 2:
                    df_filtrado = df_filtrado[(df_filtrado['Fecha_dt'] >= filtro_fecha[0]) & (df_filtrado['Fecha_dt'] <= filtro_fecha[1])]
                elif len(filtro_fecha) == 1:
                    df_filtrado = df_filtrado[df_filtrado['Fecha_dt'] == filtro_fecha[0]]
                    
                # Ocultamos la columna de control de fechas
                if 'Fecha_dt' in df_filtrado.columns:
                    df_filtrado = df_filtrado.drop(columns=['Fecha_dt'])

                # --- SECCIÓN B: MOSTRAR LA TABLA ---
                st.markdown("---")
                st.markdown(f"**Total de registros en pantalla: {len(df_filtrado)}**")
                
                # Ordenar para ver los más recientes arriba
                df_filtrado = df_filtrado.iloc[::-1].reset_index(drop=True)
                
                # Imprimir la tabla en pantalla
                st.dataframe(df_filtrado, use_container_width=True, hide_index=True)
                
            else:
                st.info("📌 Aún no hay registros de asistencia en la base de datos.")
                
        except Exception as e:
            st.error(f"❌ Ocurrió un error al procesar las asistencias: {e}")
    else:
        st.error("❌ No se pudo conectar a la base de datos.")

# 4. ENCIENDE EL MOTOR: Llama a la función para que empiece a trabajar sola
contenedor_asistencias_tiempo_real()