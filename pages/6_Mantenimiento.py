import streamlit as st
import pandas as pd
from google_connector import get_worksheets
from datetime import datetime

# 1. SEGURIDAD: Bloquear acceso si no ha iniciado sesión
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.error("⚠️ Acceso denegado. Por favor, inicia sesión en la página principal (Home).")
    st.stop()

# Inicializar variable de control para la doble confirmación si no existe
if "esperando_confirmacion" not in st.session_state:
    st.session_state.esperando_confirmacion = False

# --- SISTEMA DE NOTIFICACIONES DE MANTENIMIENTO ---
if "mensaje_mantenimiento" in st.session_state:
    st.success(st.session_state.mensaje_mantenimiento)
    st.toast(st.session_state.mensaje_mantenimiento, icon="⚙️")
    del st.session_state.mensaje_mantenimiento
# --------------------------------------------------

# 2. ENCABEZADO Y ADVERTENCIA CRÍTICA INSTITUCIONAL
st.markdown("<h1 style='color: #BC1B1B; margin-top: 0;'>⚙️ Panel de Mantenimiento y Auditoría</h1>", unsafe_allow_html=True)
st.write("Módulo especializado para la depuración, optimización y trazabilidad legal de la base de datos de asistencias.")

st.error("### ⚠️ ZONA DE ALTO RIESGO - OPERACIONES IRREVERSIBLES\n"
         "Las acciones ejecutadas en esta página removerán información de forma definitiva de Google Sheets.\n\n"
         "* **Trazabilidad Obligatoria:** Cada operación quedará sellada con fecha, hora, registros afectados y justificación en la bitácora de **Auditoría**.\n"
         "* **Seguro de Vida Activo:** El sistema requerirá una doble confirmación visual antes de ejecutar cualquier borrado en el servidor.")

st.markdown("---")

# 3. CONEXIÓN A GOOGLE SHEETS
sheet_usuarios, sheet_asistencias = get_worksheets()

if sheet_usuarios and sheet_asistencias:
    try:
        # Conectar o crear la pestaña Auditoría de forma automática
        try:
            sheet_auditoria = sheet_usuarios.spreadsheet.worksheet("Auditoria")
        except Exception:
            sheet_auditoria = sheet_usuarios.spreadsheet.add_worksheet(title="Auditoria", rows=1000, cols=5)
            sheet_auditoria.append_row(["Fecha y Hora", "Acción Realizada", "Registros Afectados", "Alcance / Período", "Motivo de la Operación"])

        # Leer datos reales de asistencias
        datos_asistencias = sheet_asistencias.get_all_records()
        
        if datos_asistencias:
            df_asis = pd.DataFrame(datos_asistencias)
            
            # Formatear la columna de fechas internamente para la segmentación
            df_asis['Fecha_dt'] = pd.to_datetime(df_asis['Fecha'], errors='coerce').dt.date
            
            fechas_validas = df_asis['Fecha_dt'].dropna()
            min_date = fechas_validas.min() if not fechas_validas.empty else datetime.today().date()
            max_date = fechas_validas.max() if not fechas_validas.empty else datetime.today().date()

            # --- SECCIÓN A: CONFIGURACIÓN DEL FILTRO DE DEPURACIÓN ---
            st.subheader("🔍 1. Seleccione los registros que desea depurar")
            
            tipo_depuracion = st.radio(
                "Defina el criterio de selección para la remoción de datos:",
                options=["Por Rango de Fechas (Depuración Semestral o Histórica)", "Por Código Institucional / Cédula Específica"],
                index=0
            )

            asistencias_a_borrar = pd.DataFrame()
            asistencias_a_conservar = pd.DataFrame()
            alcance_texto = ""

            if tipo_depuracion == "Por Rango de Fechas (Depuración Semestral o Histórica)":
                rango_fechas = st.date_input(
                    "Seleccione el rango cronológico a eliminar permanentemente:",
                    value=(min_date, max_date),
                    min_value=min_date,
                    max_value=max_date
                )
                
                if isinstance(rango_fechas, tuple) and len(rango_fechas) == 2:
                    mask_borrar = (df_asis['Fecha_dt'] >= rango_fechas[0]) & (df_asis['Fecha_dt'] <= rango_fechas[1])
                    asistencias_a_borrar = df_asis[mask_borrar]
                    asistencias_a_conservar = df_asis[~mask_borrar]
                    alcance_texto = f"Rango: {rango_fechas[0]} al {rango_fechas[1]}"
                elif isinstance(rango_fechas, tuple) and len(rango_fechas) == 1:
                    mask_borrar = df_asis['Fecha_dt'] == rango_fechas[0]
                    asistencias_a_borrar = df_asis[mask_borrar]
                    asistencias_a_conservar = df_asis[~mask_borrar]
                    alcance_texto = f"Día específico: {rango_fechas[0]}"

            else:
                df_asis['Código_Limpio'] = df_asis['Código / Cédula'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                lista_codigos = sorted(df_asis['Código_Limpio'].unique().tolist())
                
                codigo_seleccionado = st.selectbox(
                    "Seleccione el código o número de documento del usuario a depurar:",
                    options=lista_codigos,
                    index=None,
                    placeholder="Escriba o seleccione un código..."
                )
                
                if codigo_seleccionado:
                    mask_borrar = df_asis['Código_Limpio'] == str(codigo_seleccionado).strip()
                    asistencias_a_borrar = df_asis[mask_borrar]
                    asistencias_a_conservar = df_asis[~mask_borrar]
                    alcance_texto = f"Usuario ID: {codigo_seleccionado}"
                
                df_asis = df_asis.drop(columns=['Código_Limpio'])

            st.markdown("<br>", unsafe_allow_html=True)
            cantidad_impactada = len(asistencias_a_borrar)
            
            if cantidad_impactada > 0:
                st.warning(f"📊 **Análisis del Sistema:** Se han localizado **{cantidad_impactada} registros de asistencia** que califican dentro del filtro.")
                
                # --- SECCIÓN B: PROTOCOLO DE JUSTIFICACIÓN Y DOBLE BOTÓN ---
                st.subheader("🔒 2. Protocolo de Validación y Seguridad")
                
                motivo = st.text_input(
                    "📝 Justificación oficial del borrado (Este argumento se grabará en la Bitácora de Auditoría):",
                    placeholder="Ej: Cierre de ciclo académico, depuración de registros duplicados erróneos..."
                )
                
                # Primer botón: Solicita la depuración
                if not st.session_state.esperando_confirmacion:
                    st.markdown("<br>", unsafe_allow_html=True)
                    btn_solicitar = st.button(
                        "🗑️ Iniciar Depuración de Registros", 
                        type="primary", 
                        use_container_width=True,
                        disabled=not motivo.strip()
                    )
                    if btn_solicitar:
                        st.session_state.esperando_confirmacion = True
                        st.grid() # Forzar refresco para mostrar la confirmación
                        st.rerun()

                # El Doble Botón Interactivo (Tu excelente idea)
                if st.session_state.esperando_confirmacion:
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.error(f"🚨 **¿ESTÁ COMPLETAMENTE SEGURO?** Se eliminarán **{cantidad_impactada} registros** de forma permanente del servidor institucional. Esta acción no se puede deshacer.")
                    
                    col_si, col_no = st.columns(2)
                    with col_si:
                        btn_confirmar_definitivo = st.button("✅ Sí, eliminar permanentemente", type="primary", use_container_width=True)
                    with col_no:
                        btn_cancelar = st.button("❌ Cancelar operación", use_container_width=True)

                    # Si confirma el borrado final
                    if btn_confirmar_definitivo:
                        with st.spinner("Reestructurando base de datos y sellando libro de auditoría..."):
                            if 'Fecha_dt' in asistencias_a_conservar.columns:
                                asistencias_a_conservar = asistencias_a_conservar.drop(columns=['Fecha_dt'])
                            if 'Código_Limpio' in asistencias_a_conservar.columns:
                                asistencias_a_conservar = asistencias_a_conservar.drop(columns=['Código_Limpio'])
                                
                            columnas_originales = [col for col in datos_asistencias[0].keys()]
                            asistencias_a_conservar = asistencias_a_conservar[columnas_originales]
                            
                            # Limpiar y reescribir la hoja de asistencias
                            sheet_asistencias.clear()
                            if not asistencias_a_conservar.empty:
                                sheet_asistencias.update(
                                    "A1",
                                    [asistencias_a_conservar.columns.values.tolist()] + 
                                    asistencias_a_conservar.values.tolist()
                                )
                            else:
                                sheet_asistencias.append_row(columnas_originales)
                                
                            # Grabar rastro perpetuo en la Bitácora de Auditoría
                            registro_auditoria = [
                                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "ELIMINACIÓN_REGISTROS_HISTÓRICOS",
                                f"{cantidad_impactada} filas",
                                alcance_texto,
                                motivo.strip()
                            ]
                            sheet_auditoria.append_row(registro_auditoria)
                            
                            # Resetear estados y avisar éxito
                            st.session_state.esperando_confirmacion = False
                            st.session_state.mensaje_mantenimiento = (
                                f"⚙️ **Notificación de Mantenimiento:** Se depuraron de forma exitosa {cantidad_impactada} registros. "
                                f"La operación fue registrada con éxito en el libro de auditoría institucional del Gimnasio USTA."
                            )
                            st.rerun()

                    # Si cancela la operación
                    if btn_cancelar:
                        st.session_state.esperando_confirmacion = False
                        st.info("Operación cancelada de forma segura por el administrador.")
                        st.rerun()
            else:
                st.session_state.esperando_confirmacion = False
                st.info("📌 No se encontraron asistencias en la base de datos que coincidan con los filtros seleccionados.")
        else:
            st.info("📌 El historial de asistencias de Google Sheets se encuentra totalmente vacío.")
            
    except Exception as e:
        st.error(f"❌ Ocurrió un error inesperado al procesar el mantenimiento: {e}")
else:
    st.error("❌ Error de enlace: No se pudo conectar con el servidor central de Google Sheets.")

# --- SECCIÓN C: TABLA DE VISUALIZACIÓN DE AUDITORÍA (TRANSPARENCIA TOTAL) ---
st.markdown("<br><br>---", unsafe_allow_html=True)
st.subheader("📜 Historial de Auditoría Institucional (Solo Lectura)")
st.write("A continuación se despliega la bitácora de control interno que registra las modificaciones masivas del sistema:")

if sheet_usuarios:
    try:
        sheet_auditoria = sheet_usuarios.spreadsheet.worksheet("Auditoria")
        datos_auditoria = sheet_auditoria.get_all_records()
        if datos_auditoria:
            df_aud = pd.DataFrame(datos_auditoria)
            df_aud = df_aud.iloc[::-1].reset_index(drop=True)
            st.dataframe(df_aud, use_container_width=True, hide_index=True)
        else:
            st.info("📌 La bitácora se encuentra limpia. No se registran operaciones de borrado previas.")
    except Exception:
        st.info("📌 La bitácora se encuentra limpia. No se registran operaciones de borrado previas.")