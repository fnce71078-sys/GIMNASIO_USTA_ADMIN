import gspread
from google.oauth2.service_account import Credentials
import streamlit as st

# 1. Definir los permisos necesarios para leer y escribir
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# 2. Usamos cache de Streamlit para no reconectarnos en cada clic y hacer la app más rápida
@st.cache_resource(show_spinner=False)
def init_connection():
    """Inicializa la conexión a Google Sheets usando el archivo JSON."""
    try:
        # Cargar credenciales desde el archivo
        credentials = Credentials.from_service_account_file(
            "credenciales.json",
            scopes=SCOPES
        )
        # Autorizar el cliente
        client = gspread.authorize(credentials)
        
        # Abrir el documento (Debe llamarse exactamente igual en tu Google Drive)
        sheet_document = client.open("Gimnasio_USTA_DB")
        return sheet_document
        
    except Exception as e:
        st.error(f"❌ Error de conexión a la base de datos: {e}")
        return None

# 3. Función para entregar las pestañas listas para usar
def get_worksheets():
    """Obtiene y retorna las pestañas 'Usuarios' y 'Asistencias'."""
    doc = init_connection()
    if doc:
        try:
            sheet_usuarios = doc.worksheet("Usuarios")
            sheet_asistencias = doc.worksheet("Asistencias")
            return sheet_usuarios, sheet_asistencias
        except Exception as e:
            st.error(f"❌ Error al abrir las pestañas (verifica que los nombres coincidan): {e}")
            return None, None
    return None, None