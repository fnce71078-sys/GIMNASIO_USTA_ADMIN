import gspread
import streamlit as st
from google.oauth2.service_account import Credentials
import os

def get_worksheets():
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds_dict = None
        
        # 1. ESCANEO DE SECRETS EN LA NUBE
        if len(st.secrets) > 0:
            if "private_key" in st.secrets:
                creds_dict = dict(st.secrets)
            else:
                # Buscar si las llaves están dentro de alguna sección del cuadro negro
                for seccion in st.secrets.keys():
                    if isinstance(st.secrets[seccion], dict) and "private_key" in st.secrets[seccion]:
                        creds_dict = dict(st.secrets[seccion])
                        break

        # 2. EVALUACIÓN LOGICA DE ENRUTAMIENTO
        if creds_dict is not None:
            # Si encontró los Secrets en la nube, se conecta de forma virtual
            creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
            gc = gspread.authorize(creds)
        elif os.path.exists('credenciales.json'):
            # Si está en tu computador local y existe el archivo físico, lo usa
            gc = gspread.service_account(filename='credenciales.json')
        else:
            # DIAGNÓSTICO REAL: Si está en la nube y los Secrets fallan, te lo avisa con total claridad
            st.error("❌ Los Secrets de Streamlit están vacíos, no se guardaron con el botón verde, o la llave 'private_key' quedó mal copiada en el cuadro negro de la plataforma.")
            return None, None

        # CONEXIÓN AL LIBRO MAESTRO DE GOOGLE SHEETS
        spreadsheet = gc.open("Gimnasio_USTA_Data") 
        sheet_usuarios = spreadsheet.worksheet("Usuarios")
        sheet_asistencias = spreadsheet.worksheet("Asistencias")
        
        return sheet_usuarios, sheet_asistencias
        
    except Exception as e:
        st.error(f"❌ Error de conexión a la base de datos: {e}")
        return None, None