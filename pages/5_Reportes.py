import streamlit as st
import pandas as pd
import io
from google_connector import get_worksheets
from datetime import datetime

# 1. SEGURIDAD: Bloquear acceso si no ha iniciado sesión
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.error("⚠️ Acceso denegado. Por favor, inicia sesión en la página principal (Home).")
    st.stop()

# 2. ENCABEZADOS Y TÍTULOS
st.markdown("<h1 style='color: #1E3A8A; margin-top: 0;'>📥 Exportación de Reportes Oficiales</h1>", unsafe_allow_html=True)
st.write("Genera y descarga el consolidado gerencial del Gimnasio USTA en formato Excel con diseño institucional y filtros a la medida.")
st.markdown("---")

# 3. PANEL INSTRUCTIVO ESTÉTICO (UX OPTIMIZADO)
st.info("### 📖 ¿Qué incluye este documento oficial?\n"
        "El sistema construirá un archivo Excel altamente estético con **3 pestañas organizadas** que se adaptarán dinámicamente al período de tiempo que selecciones:\n\n"
        "1. 📊 **Resumen Ejecutivo:** Tabla gerencial con los indicadores clave (KPIs) recalculados según las fechas elegidas.\n"
        "2. 👥 **Directorio de Usuarios:** La base de datos completa de las personas inscritas en el sistema con formato premium.\n"
        "3. 📅 **Historial de Asistencias:** El registro cronológico detallado de los ingresos correspondientes al período seleccionado.\n\n"
        "*Todo el documento se genera con la paleta de colores institucional, columnas auto-ajustadas y filtros listos para auditorías directivas.*")

st.markdown("<br>", unsafe_allow_html=True)

# 4. EXTRACCIÓN DE DATOS DE GOOGLE SHEETS
sheet_usuarios, sheet_asistencias = get_worksheets()

if sheet_usuarios and sheet_asistencias:
    try:
        # Traer datos crudos de las hojas
        datos_usuarios = sheet_usuarios.get_all_records()
        datos_asistencias = sheet_asistencias.get_all_records()
        
        df_usu = pd.DataFrame(datos_usuarios) if datos_usuarios else pd.DataFrame()
        df_asis = pd.DataFrame(datos_asistencias) if datos_asistencias else pd.DataFrame()

        if not df_usu.empty and not df_asis.empty:
            
            # Formatear la columna de fechas de asistencias internamente para poder filtrar
            df_asis['Fecha_dt'] = pd.to_datetime(df_asis['Fecha'], errors='coerce').dt.date
            
            # Determinar los límites reales de las asistencias para el calendario
            fechas_validas = df_asis['Fecha_dt'].dropna()
            min_date = fechas_validas.min() if not fechas_validas.empty else datetime.today().date()
            max_date = fechas_validas.max() if not fechas_validas.empty else datetime.today().date()

            # --- SECCIÓN DE FILTROS INTERACTIVOS ---
            st.subheader("📅 Configuración del Alcance del Reporte")
            opcion_reporte = st.radio(
                "Selecciona el período de tiempo que deseas incluir en el documento de Excel:",
                options=["Todo el Historial Registrado", "Filtrar por Rango de Fechas Específico"],
                index=0
            )

            # Inicializamos las variables de control
            df_asis_filtrado = df_asis.copy()
            periodo_texto = "Todo el historial desde el inicio de operaciones"

            if opcion_reporte == "Filtrar por Rango de Fechas Específico":
                rango_fechas = st.date_input(
                    "Selecciona la fecha de inicio y fin para el reporte:",
                    value=(min_date, max_date),
                    min_value=min_date,
                    max_value=max_date
                )
                
                # Controlar que el administrador haya seleccionado ambas fechas antes de filtrar
                if isinstance(rango_fechas, tuple) and len(rango_fechas) == 2:
                    df_asis_filtrado = df_asis[(df_asis['Fecha_dt'] >= rango_fechas[0]) & (df_asis['Fecha_dt'] <= rango_fechas[1])]
                    periodo_texto = f"Desde {rango_fechas[0]} hasta {rango_fechas[1]}"
                elif isinstance(rango_fechas, tuple) and len(rango_fechas) == 1:
                    df_asis_filtrado = df_asis[df_asis['Fecha_dt'] == rango_fechas[0]]
                    periodo_texto = f"Día específico: {rango_fechas[0]}"

            # Eliminar la columna de control interno para que no salga en el Excel definitivo
            if 'Fecha_dt' in df_asis_filtrado.columns:
                df_asis_filtrado = df_asis_filtrado.drop(columns=['Fecha_dt'])
            if 'Fecha_dt' in df_asis.columns:
                df_asis = df_asis.drop(columns=['Fecha_dt'])

            st.markdown("<br>", unsafe_allow_html=True)

            # --- A. RECALCULAR EL RESUMEN EJECUTIVO SEGÚN EL FILTRO ---
            total_usu_maestro = len(df_usu)
            total_asis_periodo = len(df_asis_filtrado)
            usuarios_activos_periodo = df_asis_filtrado['Código / Cédula'].nunique() if total_asis_periodo > 0 else 0
            
            datos_resumen = {
                "Métrica Gerencial": [
                    "Alcance Cronológico del Reporte",
                    "Total de Usuarios Registrados en el Sistema", 
                    "Total de Asistencias en este Período", 
                    "Usuarios Únicos que Entrenaron en este Período",
                    "Frecuencia Promedio en este Período (Visitas/Usuario)",
                    "Fecha y Hora de Emisión del Documento"
                ],
                "Valor Calculado": [
                    periodo_texto,
                    total_usu_maestro,
                    total_asis_periodo,
                    usuarios_activos_periodo,
                    round(total_asis_periodo / usuarios_activos_periodo, 1) if usuarios_activos_periodo > 0 else 0,
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ]
            }
            df_resumen = pd.DataFrame(datos_resumen)

            # --- B. CREACIÓN DEL ARCHIVO EXCEL EN MEMORIA (EL ROBOT XLSXWRITER) ---
            buffer = io.BytesIO()
            
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                
                # Inyectar los DataFrames en cada pestaña mapeada
                df_resumen.to_excel(writer, sheet_name='Resumen Ejecutivo', index=False)
                df_usu.to_excel(writer, sheet_name='Directorio Usuarios', index=False)
                
                # Ordenamos el historial a descargar para que las últimas asistencias aparezcan arriba
                df_asis_descarga = df_asis_filtrado.iloc[::-1].reset_index(drop=True)
                df_asis_descarga.to_excel(writer, sheet_name='Historial Asistencias', index=False)
                
                # Configurar estilos avanzados con la paleta de la Universidad Santo Tomás
                workbook = writer.book
                formato_encabezado = workbook.add_format({
                    'bg_color': '#1E3A8A',      # Azul Marino Institucional
                    'font_color': '#FFFFFF',    # Texto Blanco Puro
                    'bold': True,               # Letra en Negrita
                    'border': 1,                # Bordes definidos
                    'valign': 'vcenter',        # Alineación vertical centrada
                    'align': 'center'           # Alineación horizontal centrada
                })
                
                formato_celda = workbook.add_format({
                    'border': 1, 
                    'valign': 'vcenter'
                })

                # Maquillar y formatear cada pestaña del libro automáticamente
                for sheet_name in writer.sheets:
                    worksheet = writer.sheets[sheet_name]
                    
                    # 1. Fijar filas superiores (Inmovilizar encabezados al hacer scroll)
                    worksheet.freeze_panes(1, 0)
                    
                    # 2. Definir el DataFrame objetivo de la iteración para calcular dimensiones
                    if sheet_name == 'Resumen Ejecutivo':
                        df_target = df_resumen
                    elif sheet_name == 'Directorio Usuarios':
                        df_target = df_usu
                    else:
                        df_target = df_asis_descarga
                    
                    # 3. Activar los filtros desplegables automáticos de Excel en la fila 1
                    worksheet.autofilter(0, 0, len(df_target), len(df_target.columns) - 1)

                    # 4. Ajustar el ancho de las columnas de forma matemática según el texto más largo
                    for col_num, value in enumerate(df_target.columns.values):
                        # Reescribir el encabezado aplicando el formato Azul Premium
                        worksheet.write(0, col_num, value, formato_encabezado)
                        
                        # Evaluar el largo del elemento más extenso en esa columna para estirarla
                        max_len = df_target[value].astype(str).map(len).max() if not df_target.empty else 0
                        col_ancho = max(max_len, len(value)) + 5
                        
                        # Aplicar el ancho calculado junto con el borde gris limpio
                        worksheet.set_column(col_num, col_num, col_ancho, formato_celda)

            # --- C. BOTÓN DE DESCARGA FINAL ---
            st.markdown("---")
            st.success("✅ **¡Documento compilado y estructurado con éxito!** Presiona el botón de abajo para guardarlo.")
            
            # Nombre de archivo dinámico basado en la fecha actual para evitar confusiones
            fecha_archivo = datetime.now().strftime("%Y%m%d")
            nombre_archivo = f"Reporte_Oficial_Gimnasio_USTA_{fecha_archivo}.xlsx"
            
            st.download_button(
                label="📥 Descargar Reporte Oficial en Excel",
                data=buffer.getvalue(),
                file_name=nombre_archivo,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                type="primary"
            )

        else:
            st.warning("⚠️ Base de datos insuficiente. Se requiere que existan registros en ambas hojas de Google Sheets para estructurar el reporte.")
            
    except Exception as e:
        st.error(f"❌ Ocurrió un error inesperado al procesar el reporte analítico: {e}")
else:
    st.error("❌ Error de comunicación: No se logró conectar con el servidor de Google Sheets.")