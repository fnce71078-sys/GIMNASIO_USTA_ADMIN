import gspread
import streamlit as st
import os

def get_worksheets():
    try:
        gc = None

        # 1. TU CONEXIÓN MAESTRA COMPROBADA (Nube - Streamlit Secrets)
        if "gcp_service_account" in st.secrets:
            credenciales = dict(st.secrets["gcp_service_account"])
            
            # Tu truco técnico de oro para limpiar los saltos de línea de la clave
            if "private_key" in credenciales:
                credenciales["private_key"] = credenciales["private_key"].replace("\\n", "\n")
            
            # Conecta usando tu método exitoso directo de gspread
            gc = gspread.service_account_from_dict(credenciales)

        # 2. PLAN B: ENTORNO LOCAL (Tu computador de pruebas)
        elif os.path.exists('credenciales.json'):
            gc = gspread.service_account(filename='credenciales.json')

        # Validación de control
        if gc is None:
            st.error("❌ Error: No se encontró el archivo 'credenciales.json' de forma local ni los Secretos en la nube.")
            return None, None

        # ⚠️ OJO AQUÍ: Verifica cuál es el nombre exacto de tu archivo de Google Sheets del Gimnasio.
        # Si se llama "Gimnasio_USTA_Data" déjalo así, si se llama "Gimnasio_USTA_DB" lo cambias aquí:
        spreadsheet = gc.open("Gimnasio_USTA_Data") 
        
        # Extraemos las dos pestañas que consumen tus 6 páginas de la app
        sheet_usuarios = spreadsheet.worksheet("Usuarios")
        sheet_asistencias = spreadsheet.worksheet("Asistencias")
        
        return sheet_usuarios, sheet_asistencias

    except Exception as e:
        st.error(f"❌ Error al conectar con la base de datos de Google Sheets: {e}")
        return None, None