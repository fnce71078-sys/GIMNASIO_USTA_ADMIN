import gspread
import streamlit as st
from google.oauth2.service_account import Credentials

def get_worksheets():
    try:
        # 1. CONEXIÓN EN LA NUBE (Streamlit Cloud Secrets)
        if "private_key" in st.secrets:
            creds_dict = {
                "type": st.secrets["type"],
                "project_id": st.secrets["project_id"],
                "private_key_id": st.secrets["private_key_id"],
                "private_key": st.secrets["private_key"],
                "client_email": st.secrets["client_email"],
                "client_id": st.secrets["client_id"],
                "auth_uri": st.secrets["auth_uri"],
                "token_uri": st.secrets["token_uri"],
                "auth_provider_x509_cert_url": st.secrets["auth_provider_x509_cert_url"],
                "client_x509_cert_url": st.secrets["client_x509_cert_url"],
                "universe_domain": st.secrets["universe_domain"]
            }
            scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
            creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
            gc = gspread.authorize(creds)
        
        # 2. CONEXIÓN LOCAL (Tu computador de pruebas)
        else:
            gc = gspread.service_account(filename='credenciales.json')

        # ⚠️ RECUERDA: Coloca aquí el nombre exacto de tu archivo de Google Sheets
        # Si tu archivo se llama diferente a "Gimnasio_USTA_Data", cambia este texto:
        spreadsheet = gc.open("Gimnasio_USTA_Data") 
        
        sheet_usuarios = spreadsheet.worksheet("Usuarios")
        sheet_asistencias = spreadsheet.worksheet("Asistencias")
        
        return sheet_usuarios, sheet_asistencias
        
    except Exception as e:
        st.error(f"❌ Error de conexión a la base de datos: {e}")
        return None, None