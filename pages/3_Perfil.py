import streamlit as st
import pandas as pd
from google_connector import get_worksheets

# 1. SEGURIDAD: Bloquear acceso si no ha iniciado sesión
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.error("⚠️ Acceso denegado. Por favor, inicia sesión en la página principal (Home).")
    st.stop()

# 2. Títulos
st.markdown("<h1 style='color: #1E3A8A;'>👤 Perfil Individual del Asistente</h1>", unsafe_allow_html=True)
st.write("Consulta la ficha técnica y el historial completo de ingresos seleccionando un usuario de la lista predictiva.")
st.markdown("---")

# 3. Conexión a la base de datos
sheet_usuarios, sheet_asistencias = get_worksheets()

if sheet_usuarios and sheet_asistencias:
    try:
        # Cargar los datos de los usuarios en la memoria temporal
        datos_usuarios = sheet_usuarios.get_all_records()
        
        if datos_usuarios:
            df_usuarios = pd.DataFrame(datos_usuarios)
            
            # Limpiar y estandarizar códigos y nombres
            df_usuarios['Código Institucional o Cédula'] = df_usuarios['Código Institucional o Cédula'].astype(str).str.strip()
            df_usuarios['Nombre Completo'] = df_usuarios['Nombre Completo'].astype(str).str.strip()
            df_usuarios['Rol'] = df_usuarios['Rol'].astype(str).str.strip()
            
            # --- CREACIÓN DE LA ETIQUETA PREDICTIVA ---
            # Combinamos Código + Nombre + Rol en una sola línea de texto para que sea fácil buscar por cualquier campo
            df_usuarios['Etiqueta_Busqueda'] = (
                df_usuarios['Código Institucional o Cédula'] + " - " + 
                df_usuarios['Nombre Completo'] + " (" + df_usuarios['Rol'] + ")"
            )
            
            lista_opciones = df_usuarios['Etiqueta_Busqueda'].tolist()
            
            # --- BUSCADOR DESPLEGABLE INTELIGENTE ---
            st.subheader("🔍 Buscador de Asistentes")
            st.info("💡 Haz clic abajo y empieza a escribir los últimos números de la cédula o el nombre del usuario.")
            
            seleccion = st.selectbox(
                "Seleccione o escriba para buscar el usuario:",
                options=lista_opciones,
                index=None, # Inicia vacío para que no cargue a nadie por defecto
                placeholder="Escriba cédula, código o nombre para autocompletar..."
            )
            
            # Si el administrador seleccionó una opción de la lista predictiva
            if seleccion:
                st.markdown("---")
                
                # Extraer el registro exacto que coincide con la etiqueta seleccionada
                usuario_seleccionado = df_usuarios[df_usuarios['Etiqueta_Busqueda'] == seleccion]
                user_data = usuario_seleccionado.iloc[0]
                codigo_buscado = user_data['Código Institucional o Cédula']
                
                # --- DISEÑO DE LA TARJETA DE PERFIL ---
                st.markdown(f"### 🪪 Información de: {user_data['Nombre Completo']}")
                
                with st.container(border=True):
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        st.markdown("**Código / Cédula:**")
                        st.code(codigo_buscado, language="text")
                        st.markdown("**Edad:**")
                        st.write(f"{user_data.get('Edad', 'N/A')} años")
                    with c2:
                        st.markdown("**Rol:**")
                        st.info(user_data.get('Rol', 'N/A'))
                        st.markdown("**Género:**")
                        st.write(user_data.get('Género', 'N/A'))
                    with c3:
                        st.markdown("**Facultad / Área:**")
                        st.info(user_data.get('Facultad / Área', 'N/A'))
                        st.markdown("**RH:**")
                        st.write(user_data.get('RH', 'N/A'))
                
                # Datos de emergencia en un menú desplegable limpio
                with st.expander("🚨 Datos de Contacto y Emergencia"):
                    ce1, ce2 = st.columns(2)
                    with ce1:
                        st.write(f"**Contacto de Emergencia:** {user_data.get('Contacto de Emergencia', 'N/A')}")
                    with ce2:
                        st.write(f"**Teléfono de Emergencia:** {user_data.get('Teléfono de Emergencia', 'N/A')}")
                    st.write(f"*Fecha en la que se inscribió al sistema:* {user_data.get('Fecha de Registro', 'N/A')}")

                # --- HISTORIAL ESPECÍFICO DEL USUARIO ---
                st.markdown("<br>", unsafe_allow_html=True)
                st.subheader("📈 Historial Personal de Ingresos")
                
                # Cargar asistencias
                datos_asistencias = sheet_asistencias.get_all_records()
                
                if datos_asistencias:
                    df_asistencias = pd.DataFrame(datos_asistencias)
                    df_asistencias['Código / Cédula'] = df_asistencias['Código / Cédula'].astype(str).str.strip()
                    
                    # Filtrar los ingresos que pertenecen únicamente a esta persona
                    asistencias_personales = df_asistencias[df_asistencias['Código / Cédula'] == codigo_buscado]
                    
                    if not asistencias_personales.empty:
                        # Invertir orden para que los ingresos más recientes se vean arriba
                        asistencias_personales = asistencias_personales.iloc[::-1]
                        
                        total_visitas = len(asistencias_personales)
                        st.metric(label="Total de ingresos registrados", value=f"{total_visitas} visitas")
                        
                        # Mostrar la tabla limpia con sus horas y fechas de entrada
                        st.dataframe(
                            asistencias_personales[['Fecha', 'Hora']], 
                            use_container_width=True, 
                            hide_index=True
                        )
                    else:
                        st.warning("⚠️ Este usuario está registrado en el sistema pero aún no registra ingresos en la planilla de asistencia.")
                else:
                    st.info("📌 La planilla general de asistencias se encuentra vacía actualmente.")
                    
        else:
            st.info("📌 La base de datos de usuarios registrados está vacía.")
            
    except Exception as e:
        st.error(f"❌ Error al procesar el perfil del asistente: {e}")
else:
    st.error("❌ No se pudo conectar a la base de datos de Google Sheets.")