import gspread
import streamlit as st
import os

def get_worksheets():
    try:
        # # 1. Si la app está en internet (Streamlit Cloud), usa los Secrets virtuales
        if "gcp_service_account" in st.secrets:
            credenciales = dict(st.secrets["gcp_service_account"])
            
            # Truco técnico: Se asegura de que los saltos de línea de la clave privada se lean bien
            if "private_key" in credenciales:
                credenciales["private_key"] = credenciales["private_key"].replace("\\n", "\n")
            
            # Conecta usando el diccionario de secretos
            gc = gspread.service_account_from_dict(credenciales)
            spreadsheet = gc.open("Gimnasio_USTA_DB")

        # # 2. Si estás probando en tu computador local, usa el archivo físico credenciales.json
        elif os.path.exists('credenciales.json'):
            gc = gspread.service_account(filename='credenciales.json')
            spreadsheet = gc.open("Gimnasio_USTA_DB")
            
        else:
            st.error("❌ Error: No se encontró el archivo 'credenciales.json' de forma local ni los Secretos en la nube.")
            return None, None

        # Separamos las pestañas que consumen las páginas del gimnasio
        sheet_usuarios = spreadsheet.worksheet("Usuarios")
        sheet_asistencias = spreadsheet.worksheet("Asistencias")
        
        return sheet_usuarios, sheet_asistencias

    except Exception as e:
        st.error(f"❌ Error al conectar con la base de datos de Google Sheets: {e}")
        return None, None