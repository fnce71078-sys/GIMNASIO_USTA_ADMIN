import streamlit as st
import pandas as pd
from google_connector import get_worksheets

# 1. SEGURIDAD: Bloquear acceso si no ha iniciado sesión
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.error("⚠️ Acceso denegado. Por favor, inicia sesión en la página principal (Home).")
    st.stop()

# 2. Títulos y encabezados
st.markdown("<h1 style='color: #1E3A8A;'>👥 Gestión de Usuarios Registrados</h1>", unsafe_allow_html=True)
st.write("Visualiza la base de datos actual. Selecciona un usuario desde la lista predictiva para modificar sus datos o eliminarlo.")
st.markdown("---")

# 3. Conectar a Google Sheets y obtener ambas pestañas
sheet_usuarios, sheet_asistencias = get_worksheets()

if sheet_usuarios:
    try:
        # Traer todos los datos frescos de usuarios
        datos_usuarios = sheet_usuarios.get_all_records()
        
        if datos_usuarios:
            df_usuarios = pd.DataFrame(datos_usuarios)
            
            # Convertir Código a texto para evitar formatos numéricos extraños
            if 'Código Institucional o Cédula' in df_usuarios.columns:
                df_usuarios['Código Institucional o Cédula'] = df_usuarios['Código Institucional o Cédula'].astype(str).str.strip()
            
            # --- SECCIÓN A: MOSTRAR LA TABLA EN PANTALLA ---
            st.subheader("📋 Base de Datos Actual")
            st.dataframe(df_usuarios, use_container_width=True, hide_index=True)
            
            st.markdown("---")
            
            # --- SECCIÓN B: BUSCAR, EDITAR Y ELIMINAR ---
            st.subheader("🛠️ Modificar o Eliminar un Registro")
            st.info("💡 Haz clic abajo y escribe los últimos dígitos de la cédula o el nombre para buscar al usuario.")
            
            # Unificamos los datos para crear la etiqueta de autocompletado inteligente
            df_usuarios['Etiqueta_Busqueda'] = (
                df_usuarios['Código Institucional o Cédula'] + " - " + 
                df_usuarios['Nombre Completo'].astype(str).str.strip() + " (" + 
                df_usuarios['Rol'].astype(str).str.strip() + ")"
            )
            
            lista_opciones = df_usuarios['Etiqueta_Busqueda'].tolist()
            
            # Buscador inteligente desplegable sin temporizador para trabajar con calma
            seleccion = st.selectbox(
                "Seleccione o escriba para buscar el usuario a modificar:",
                options=lista_opciones,
                index=None,
                placeholder="Escriba cédula, código o nombre para autocompletar..."
            )
            
            # Si el administrador selecciona un usuario de la lista predictiva
            if seleccion:
                usuario_encontrado = df_usuarios[df_usuarios['Etiqueta_Busqueda'] == seleccion]
                datos_actuales = usuario_encontrado.iloc[0]
                buscar_codigo = str(datos_actuales['Código Institucional o Cédula']).strip()
                
                # Encontrar la fila exacta en Google Sheets basándonos en el código original
                celda_encontrada = sheet_usuarios.find(buscar_codigo, in_column=1)
                fila_sheet = celda_encontrada.row
                
                # Desplegar el formulario con los datos precargados
                with st.form("form_editar_usuario"):
                    st.write(f"Editando registro en la fila: **{fila_sheet}**")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        nuevo_codigo = st.text_input("Código Institucional o Cédula", value=str(datos_actuales.get("Código Institucional o Cédula", "")))
                        nuevo_nombre = st.text_input("Nombre Completo", value=str(datos_actuales.get("Nombre Completo", "")))
                        
                        roles = ["Estudiante", "Docente", "Administrativo", "Egresado", "Externo"]
                        rol_actual = str(datos_actuales.get("Rol", "Estudiante")).strip()
                        idx_rol = roles.index(rol_actual) if rol_actual in roles else 0
                        nuevo_rol = st.selectbox("Rol", roles, index=idx_rol)
                        
                        nueva_facultad = st.text_input("Facultad / Área", value=str(datos_actuales.get("Facultad / Área", "")))
                        
                    with col2:
                        nuevo_rh = st.text_input("RH", value=str(datos_actuales.get("RH", "")))
                        
                        edad_str = str(datos_actuales.get("Edad", "0")).replace(",", "")
                        edad_actual = int(float(edad_str)) if edad_str.strip() else 0
                        nueva_edad = st.number_input("Edad", value=edad_actual, step=1)
                        
                        generos = ["Hombre", "Mujer", "Otro"]
                        genero_actual = str(datos_actuales.get("Género", "Hombre")).strip()
                        idx_gen = generos.index(genero_actual) if genero_actual in generos else 0
                        nuevo_genero = st.selectbox("Género", generos, index=idx_gen)
                        
                        nuevo_contacto = st.text_input("Contacto de Emergencia", value=str(datos_actuales.get("Contacto de Emergencia", "")))
                        nuevo_tel = st.text_input("Teléfono de Emergencia", value=str(datos_actuales.get("Teléfono de Emergencia", "")))
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        btn_actualizar = st.form_submit_button("💾 Actualizar Registro", type="primary", use_container_width=True)
                    with col_btn2:
                        btn_eliminar = st.form_submit_button("🗑️ Eliminar Registro", use_container_width=True)
                        
                    # --- LÓGICA PARA GUARDAR CAMBIOS (CON EFECTO CASCADA) ---
                    if btn_actualizar:
                        valores_actualizados = [
                            str(nuevo_codigo).strip(), nuevo_nombre, nuevo_rol, nueva_facultad, 
                            nuevo_rh, nueva_edad, nuevo_genero, nuevo_contacto, nuevo_tel, 
                            str(datos_actuales.get("Fecha de Registro", ""))
                        ]
                        
                        # 1. Actualizar los datos maestros en la pestaña Usuarios
                        sheet_usuarios.update(f"A{fila_sheet}:J{fila_sheet}", [valores_actualizados])
                        
                        # 2. Verificar si hubo cambio de Cédula/Código para detonar la cascada
                        codigo_viejo_limpio = buscar_codigo
                        codigo_nuevo_limpio = str(nuevo_codigo).strip()
                        
                        hubo_cambio_cedula = codigo_nuevo_limpio != codigo_viejo_limpio
                        asistencias_corregidas = 0
                        
                        if hubo_cambio_cedula and sheet_asistencias:
                            celdas_asistencias = sheet_asistencias.findall(codigo_viejo_limpio, in_column=1)
                            
                            if celdas_asistencias:
                                for celda in celdas_asistencias:
                                    celda.value = codigo_nuevo_limpio
                                sheet_asistencias.update_cells(celdas_asistencias)
                                asistencias_corregidas = len(celdas_asistencias)
                        
                        # 3. Personalizar la notificación formal según el resultado de la operación
                        if hubo_cambio_cedula:
                            st.session_state.mensaje_crud = (
                                f"📋 **Notificación del Sistema:** El documento de identidad de '{nuevo_nombre}' ha sido modificado exitosamente a {codigo_nuevo_limpio}. "
                                f"Se ha aplicado el *Efecto Cascada* corrigiendo satisfactoriamente {asistencias_corregidas} registros de asistencias históricas vinculadas."
                            )
                        else:
                            st.session_state.mensaje_crud = f"📋 **Notificación del Sistema:** Los datos correspondientes a '{nuevo_nombre}' han sido modificados y actualizados de manera exitosa en la base de datos del Gimnasio USTA."
                        
                        st.session_state.tipo_mensaje = "exito"
                        st.rerun()
                        
                    # --- LÓGICA PARA BORRAR USUARIO ---
                    if btn_eliminar:
                        sheet_usuarios.delete_rows(fila_sheet)
                        
                        st.session_state.mensaje_crud = f"🚨 **Notificación del Sistema:** El registro del usuario ha sido removido de forma permanente y satisfactoria de la base de datos institucional del Gimnasio USTA."
                        st.session_state.tipo_mensaje = "eliminado"
                        st.rerun()
                        
        else:
            st.info("📌 La base de datos de usuarios actualmente está vacía.")
            
    except Exception as e:
        st.error(f"❌ Ocurrió un error al procesar los datos: {e}")
else:
    st.error("❌ No se pudo conectar a la base de datos de Usuarios.")


# --- SECCIÓN C: SISTEMA DE NOTIFICACIONES FORMALES AL FINAL DE LA PÁGINA ---
if "mensaje_crud" in st.session_state:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.session_state.tipo_mensaje == "exito":
        st.success(st.session_state.mensaje_crud)
        st.toast(st.session_state.mensaje_crud, icon="✅")
    elif st.session_state.tipo_mensaje == "eliminado":
        st.error(st.session_state.mensaje_crud)
        st.toast(st.session_state.mensaje_crud, icon="🚨")
    
    # Limpiar de la memoria inmediatamente para evitar repeticiones
    del st.session_state.mensaje_crud
    del st.session_state.tipo_mensaje