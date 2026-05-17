import gspread
import streamlit as st
from google.oauth2.service_account import Credentials

def get_worksheets():
    try:
        gc = None
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        
        # 1. INTENTAR CONEXIÓN GERENCIAL (Nube - Streamlit Secrets)
        if len(st.secrets) > 0:
            # Caso A: Las llaves están sueltas en la raíz del cuadro negro
            if "private_key" in st.secrets:
                creds_dict = dict(st.secrets)
                creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
                gc = gspread.authorize(creds)
            
            # Caso B: Las llaves están metidas dentro de una sección (ej: [gcp_service_account])
            else:
                for seccion in st.secrets.keys():
                    # Si encontramos una sección que por dentro tenga la clave privada
                    if isinstance(st.secrets[seccion], dict) and "private_key" in st.secrets[seccion]:
                        creds_dict = dict(st.secrets[seccion])
                        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
                        gc = gspread.authorize(creds)
                        break # Encontrada y conectada con éxito
        
        # 2. PLAN B (Local - Tu computador de escritorio)
        if gc is None:
            gc = gspread.service_account(filename='credenciales.json')

        # ⚠️ IMPORTANTE: Verifica que este sea el nombre exacto de tu Google Sheets
        spreadsheet = gc.open("Gimnasio_USTA_Data") 
        
        sheet_usuarios = spreadsheet.worksheet("Usuarios")
        sheet_asistencias = spreadsheet.worksheet("Asistencias")
        
        return sheet_usuarios, sheet_asistencias
        
    except Exception as e:
        st.error(f"❌ Error de conexión a la base de datos: {e}")
        return None, None
