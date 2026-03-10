import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime
from supabase import create_client, Client
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO

# =========================================================
# CONFIG
# =========================================================
st.set_page_config(
    page_title="Calculadora de Condición Física",
    page_icon="💪",
    layout="centered"
)

# =========================================================
# SUPABASE
# =========================================================
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# =========================================================
# TABLAS NORMATIVAS
# =========================================================
TABLA_CAMINATA_6M = {
    150: {
        40: {2.5: 436, 10: 470, 25: 511, 50: 555, 75: 592, 90: 631, 97.5: 679},
        50: {2.5: 434, 10: 468, 25: 509, 50: 553, 75: 590, 90: 629, 97.5: 677},
        60: {2.5: 414, 10: 448, 25: 489, 50: 533, 75: 570, 90: 609, 97.5: 656},
        70: {2.5: 364, 10: 397, 25: 439, 50: 483, 75: 520, 90: 558, 97.5: 606},
        80: {2.5: 313, 10: 347, 25: 388, 50: 432, 75: 469, 90: 508, 97.5: 556},
    },
    160: {
        40: {2.5: 455, 10: 489, 25: 530, 50: 574, 75: 611, 90: 650, 97.5: 697},
        50: {2.5: 453, 10: 487, 25: 528, 50: 572, 75: 609, 90: 648, 97.5: 695},
        60: {2.5: 433, 10: 466, 25: 508, 50: 552, 75: 588, 90: 627, 97.5: 675},
        70: {2.5: 382, 10: 416, 25: 457, 50: 501, 75: 538, 90: 577, 97.5: 625},
        80: {2.5: 332, 10: 366, 25: 407, 50: 451, 75: 488, 90: 526, 97.5: 574},
    },
    170: {
        40: {2.5: 474, 10: 507, 25: 549, 50: 593, 75: 629, 90: 668, 97.5: 716},
        50: {2.5: 472, 10: 505, 25: 546, 50: 590, 75: 627, 90: 666, 97.5: 714},
        60: {2.5: 451, 10: 485, 25: 526, 50: 570, 75: 607, 90: 646, 97.5: 694},
        70: {2.5: 401, 10: 435, 25: 476, 50: 520, 75: 557, 90: 595, 97.5: 643},
        80: {2.5: 351, 10: 384, 25: 425, 50: 469, 75: 506, 90: 545, 97.5: 593},
    },
    180: {
        40: {2.5: 492, 10: 526, 25: 567, 50: 611, 75: 648, 90: 687, 97.5: 735},
        50: {2.5: 490, 10: 524, 25: 565, 50: 609, 75: 646, 90: 685, 97.5: 733},
        60: {2.5: 470, 10: 503, 25: 545, 50: 589, 75: 626, 90: 664, 97.5: 712},
        70: {2.5: 419, 10: 453, 25: 494, 50: 538, 75: 575, 90: 614, 97.5: 662},
        80: {2.5: 369, 10: 403, 25: 444, 50: 488, 75: 525, 90: 564, 97.5: 611},
    },
    190: {
        40: {2.5: 511, 10: 544, 25: 586, 50: 630, 75: 667, 90: 705, 97.5: 753},
        50: {2.5: 509, 10: 542, 25: 584, 50: 628, 75: 665, 90: 703, 97.5: 751},
        60: {2.5: 488, 10: 522, 25: 563, 50: 607, 75: 644, 90: 683, 97.5: 731},
        70: {2.5: 438, 10: 472, 25: 513, 50: 557, 75: 594, 90: 633, 97.5: 680},
        80: {2.5: 388, 10: 421, 25: 463, 50: 507, 75: 544, 90: 582, 97.5: 630},
    }
}

TABLA_PRENSION = {
    "Hombre": {
        "20-24": {5: 33.9, 10: 36.8, 20: 40.5, 30: 43.2, 40: 45.7, 50: 48.0, 60: 50.4, 70: 52.9, 80: 56.0, 90: 60.1, 95: 63.6},
        "25-29": {5: 35.5, 10: 38.5, 20: 42.1, 30: 44.8, 40: 47.1, 50: 49.3, 60: 51.5, 70: 53.9, 80: 56.7, 90: 60.7, 95: 64.0},
        "30-34": {5: 35.0, 10: 38.3, 20: 42.2, 30: 45.0, 40: 47.4, 50: 49.7, 60: 52.0, 70: 54.4, 80: 57.4, 90: 61.5, 95: 64.9},
        "35-39": {5: 33.8, 10: 37.3, 20: 41.5, 30: 44.5, 40: 47.1, 50: 49.5, 60: 51.9, 70: 54.4, 80: 57.5, 90: 61.8, 95: 65.3},
        "40-44": {5: 32.3, 10: 36.0, 20: 40.4, 30: 43.6, 40: 46.3, 50: 48.8, 60: 51.2, 70: 53.9, 80: 57.1, 90: 61.5, 95: 65.1},
        "45-49": {5: 30.6, 10: 34.4, 20: 39.0, 30: 42.3, 40: 45.1, 50: 47.6, 60: 50.2, 70: 52.9, 80: 56.2, 90: 60.7, 95: 64.4},
        "50-54": {5: 28.9, 10: 32.8, 20: 37.4, 30: 40.7, 40: 43.5, 50: 46.2, 60: 48.8, 70: 51.6, 80: 54.8, 90: 59.4, 95: 63.1},
        "55-59": {5: 27.2, 10: 31.0, 20: 35.6, 30: 38.9, 40: 41.7, 50: 44.4, 60: 47.0, 70: 49.8, 80: 53.1, 90: 57.7, 95: 61.4},
        "60-64": {5: 25.5, 10: 29.1, 20: 33.6, 30: 36.9, 40: 39.7, 50: 42.4, 60: 45.0, 70: 47.8, 80: 51.1, 90: 55.6, 95: 59.3},
        "65-69": {5: 23.7, 10: 27.2, 20: 31.5, 30: 34.7, 40: 37.5, 50: 40.1, 60: 42.8, 70: 45.6, 80: 48.8, 90: 53.2, 95: 56.8},
        "70-74": {5: 21.9, 10: 25.2, 20: 29.3, 30: 32.4, 40: 35.1, 50: 37.7, 60: 40.3, 70: 43.1, 80: 46.3, 90: 50.6, 95: 54.1},
        "75-79": {5: 20.0, 10: 23.1, 20: 27.0, 30: 29.9, 40: 32.5, 50: 35.1, 60: 37.6, 70: 40.3, 80: 43.5, 90: 47.7, 95: 51.1},
        "80-84": {5: 18.0, 10: 20.8, 20: 24.5, 30: 27.3, 40: 29.8, 50: 32.3, 60: 34.8, 70: 37.5, 80: 40.5, 90: 44.7, 95: 48.0},
        "85-89": {5: 15.9, 10: 18.5, 20: 21.9, 30: 24.6, 40: 27.0, 50: 29.4, 60: 31.8, 70: 34.4, 80: 37.4, 90: 41.5, 95: 44.6},
        "90-94": {5: 13.7, 10: 16.1, 20: 19.2, 30: 21.7, 40: 24.0, 50: 26.3, 60: 28.7, 70: 31.2, 80: 34.2, 90: 38.1, 95: 41.2},
        "95-99": {5: 11.3, 10: 13.5, 20: 16.4, 30: 18.8, 40: 20.9, 50: 23.1, 60: 25.4, 70: 27.9, 80: 30.8, 90: 34.6, 95: 37.5},
        "+100": {5: 8.8, 10: 10.8, 20: 13.5, 30: 15.7, 40: 17.8, 50: 19.8, 60: 22.0, 70: 24.5, 80: 27.2, 90: 30.9, 95: 33.8},
    },
    "Mujer": {
        "20-24": {5: 19.7, 10: 21.7, 20: 24.0, 30: 25.7, 40: 27.2, 50: 28.6, 60: 30.0, 70: 31.6, 80: 33.6, 90: 36.6, 95: 39.1},
        "25-29": {5: 20.0, 10: 22.0, 20: 24.5, 30: 26.3, 40: 27.9, 50: 29.4, 60: 30.9, 70: 32.6, 80: 34.6, 90: 37.4, 95: 39.7},
        "30-34": {5: 19.6, 10: 21.8, 20: 24.4, 30: 26.4, 40: 28.1, 50: 29.7, 60: 31.3, 70: 33.1, 80: 35.2, 90: 38.0, 95: 40.4},
        "35-39": {5: 19.0, 10: 21.3, 20: 24.1, 30: 26.2, 40: 28.0, 50: 29.7, 60: 31.4, 70: 33.2, 80: 35.4, 90: 38.4, 95: 40.8},
        "40-44": {5: 18.3, 10: 20.7, 20: 23.7, 30: 25.8, 40: 27.6, 50: 29.4, 60: 31.1, 70: 33.0, 80: 35.2, 90: 38.3, 95: 40.8},
        "45-49": {5: 17.6, 10: 20.1, 20: 23.1, 30: 25.2, 40: 27.1, 50: 28.9, 60: 30.6, 70: 32.5, 80: 34.8, 90: 37.9, 95: 40.4},
        "50-54": {5: 16.9, 10: 19.4, 20: 22.4, 30: 24.5, 40: 26.4, 50: 28.2, 60: 29.9, 70: 31.8, 80: 34.0, 90: 37.1, 95: 39.7},
        "55-59": {5: 16.1, 10: 18.5, 20: 21.5, 30: 23.7, 40: 25.5, 50: 27.3, 60: 29.0, 70: 30.9, 80: 33.0, 90: 36.1, 95: 38.6},
        "60-64": {5: 15.2, 10: 17.6, 20: 20.6, 30: 22.7, 40: 24.5, 50: 26.2, 60: 27.9, 70: 29.7, 80: 31.8, 90: 34.9, 95: 37.4},
        "65-69": {5: 14.3, 10: 16.6, 20: 19.5, 30: 21.6, 40: 23.3, 50: 25.0, 60: 26.6, 70: 28.4, 80: 30.5, 90: 33.4, 95: 35.8},
        "70-74": {5: 13.2, 10: 15.5, 20: 18.3, 30: 20.3, 40: 22.0, 50: 23.6, 60: 25.2, 70: 26.9, 80: 28.9, 90: 31.8, 95: 34.1},
        "75-79": {5: 12.0, 10: 14.3, 20: 17.0, 30: 18.9, 40: 20.5, 50: 22.1, 60: 23.6, 70: 25.2, 80: 27.2, 90: 29.9, 95: 32.2},
        "80-84": {5: 10.7, 10: 12.9, 20: 15.5, 30: 17.4, 40: 18.9, 50: 20.4, 60: 21.9, 70: 23.5, 80: 25.3, 90: 28.0, 95: 30.2},
        "85-89": {5: 9.3, 10: 11.4, 20: 13.9, 30: 15.7, 40: 17.2, 50: 18.6, 60: 20.0, 70: 21.5, 80: 23.3, 90: 25.9, 95: 28.0},
        "90-94": {5: 7.8, 10: 9.8, 20: 12.2, 30: 13.9, 40: 15.3, 50: 16.7, 60: 18.0, 70: 19.5, 80: 21.2, 90: 23.6, 95: 25.7},
        "95-99": {5: 6.1, 10: 8.0, 20: 10.3, 30: 11.9, 40: 13.3, 50: 14.6, 60: 15.9, 70: 17.3, 80: 18.9, 90: 21.2, 95: 23.2},
        "+100": {5: 4.2, 10: 6.1, 20: 8.3, 30: 9.8, 40: 11.2, 50: 12.4, 60: 13.6, 70: 14.9, 80: 16.5, 90: 18.7, 95: 20.6},
    }
}

TABLA_SILLA = {
    "Hombre": {
        "65-69": {10: 12, 20: 13, 30: 14, 40: 15, 50: 16, 60: 16, 70: 17, 80: 19, 90: 21, 100: 28},
        "70-74": {10: 11, 20: 13, 30: 14, 40: 15, 50: 15, 60: 16, 70: 17, 80: 18, 90: 20, 100: 29},
        "75-79": {10: 10, 20: 12, 30: 13, 40: 14, 50: 14, 60: 15, 70: 16, 80: 17, 90: 19, 100: 25},
        "80-84": {10: 9, 20: 10, 30: 11, 40: 12, 50: 14, 60: 15, 70: 16, 80: 17, 90: 18, 100: 22},
        "+84": {10: 9, 20: 9, 30: 12, 40: 13, 50: 14, 60: 14, 70: 16, 80: 18, 90: 20, 100: 21},
    },
    "Mujer": {
        "65-69": {10: 11, 20: 12, 30: 13, 40: 14, 50: 15, 60: 15, 70: 16, 80: 17, 90: 19, 100: 30},
        "70-74": {10: 10, 20: 12, 30: 12, 40: 13, 50: 14, 60: 15, 70: 16, 80: 17, 90: 19, 100: 27},
        "75-79": {10: 10, 20: 11, 30: 12, 40: 13, 50: 14, 60: 14, 70: 15, 80: 16, 90: 18, 100: 24},
        "80-84": {10: 9, 20: 10, 30: 11, 40: 12, 50: 13, 60: 14, 70: 15, 80: 16, 90: 18, 100: 24},
        "+84": {10: 6, 20: 8, 30: 9, 40: 11, 50: 12, 60: 14, 70: 14, 80: 16, 90: 17, 100: 18},
    }
}

# =========================================================
# UTILIDADES
# =========================================================
def guardar_evaluacion(paciente_nombre, sexo, edad, prueba, valor_medido, percentil, clasificacion):
    payload = {
        "fecha": datetime.now().strftime("%Y-%m-%d"),
        "paciente": str(paciente_nombre).strip(),
        "sexo": str(sexo).strip().lower(),
        "edad": int(edad),
        "prueba": str(prueba).strip(),
        "valor_medido": float(valor_medido),
        "percentil": round(float(percentil), 1) if percentil is not None else None,
        "clasificacion": str(clasificacion).strip()
    }
    return supabase.table("evaluaciones").insert(payload).execute()


def guardar_paciente(nombre, sexo):
    nombre_limpio = str(nombre).strip()
    sexo_limpio = str(sexo).strip().lower()

    if not nombre_limpio:
        raise ValueError("El nombre del paciente está vacío.")

    respuesta = supabase.table("pacientes").select("id,nombre").execute()
    existentes = respuesta.data if respuesta.data else []

    for p in existentes:
        if str(p["nombre"]).strip().lower() == nombre_limpio.lower():
            raise ValueError("Ese paciente ya existe.")

    payload = {
        "nombre": nombre_limpio,
        "sexo": sexo_limpio
    }
    return supabase.table("pacientes").insert(payload).execute()


def eliminar_evaluacion(id_registro):
    return supabase.table("evaluaciones").delete().eq("id", id_registro).execute()


def generar_pdf_historial(paciente, df):
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)

    y = 750

    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(50, y, "Historial de condición física")

    y -= 30

    pdf.setFont("Helvetica", 12)
    pdf.drawString(50, y, f"Paciente: {paciente}")

    y -= 40

    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(50, y, "Fecha")
    pdf.drawString(130, y, "Prueba")
    pdf.drawString(300, y, "Valor")
    pdf.drawString(360, y, "Percentil")
    pdf.drawString(440, y, "Clasificación")

    y -= 20
    pdf.setFont("Helvetica", 10)

    for _, row in df.iterrows():
        pdf.drawString(50, y, str(row.get("fecha", "")))
        pdf.drawString(130, y, str(row.get("prueba", "")))
        pdf.drawString(300, y, str(row.get("valor_medido", "")))
        pdf.drawString(360, y, str(row.get("percentil", "")))
        pdf.drawString(440, y, str(row.get("clasificacion", "")))

        y -= 18

        if y < 100:
            pdf.showPage()
            pdf.setFont("Helvetica", 10)
            y = 750

    pdf.save()
    buffer.seek(0)

    return buffer


def obtener_historial_paciente(paciente):
    try:
        respuesta = (
            supabase.table("evaluaciones")
            .select("*")
            .eq("paciente", str(paciente).strip())
            .order("fecha")
            .execute()
        )
        if respuesta.data:
            return pd.DataFrame(respuesta.data)
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error al leer historial: {e}")
        return pd.DataFrame()


def obtener_pacientes():
    try:
        respuesta = (
            supabase.table("pacientes")
            .select("id,nombre,sexo")
            .order("nombre")
            .execute()
        )
        return respuesta.data if respuesta.data else []
    except Exception as e:
        st.error(f"Error al leer pacientes: {e}")
        return []


def obtener_ficha_paciente(paciente_nombre):
    try:
        paciente_nombre = str(paciente_nombre).strip()

        respuesta_paciente = (
            supabase.table("pacientes")
            .select("nombre, sexo, created_at")
            .eq("nombre", paciente_nombre)
            .limit(1)
            .execute()
        )

        datos_paciente = respuesta_paciente.data[0] if respuesta_paciente.data else {}
        df_historial = obtener_historial_paciente(paciente_nombre)

        cantidad_evaluaciones = 0
        ultima_fecha = "-"
        ultima_clasificacion = "-"
        ultima_prueba = "-"

        if not df_historial.empty:
            if "fecha" in df_historial.columns:
                df_historial["fecha"] = pd.to_datetime(df_historial["fecha"], errors="coerce")
                df_historial = df_historial.sort_values("fecha", ascending=False)

            cantidad_evaluaciones = len(df_historial)

            if "fecha" in df_historial.columns and pd.notna(df_historial.iloc[0]["fecha"]):
                ultima_fecha = df_historial.iloc[0]["fecha"].strftime("%d-%m-%Y")

            if "clasificacion" in df_historial.columns and pd.notna(df_historial.iloc[0]["clasificacion"]):
                ultima_clasificacion = str(df_historial.iloc[0]["clasificacion"])

            if "prueba" in df_historial.columns and pd.notna(df_historial.iloc[0]["prueba"]):
                ultima_prueba = str(df_historial.iloc[0]["prueba"])

        return {
            "nombre": datos_paciente.get("nombre", paciente_nombre),
            "sexo": datos_paciente.get("sexo", "-"),
            "cantidad_evaluaciones": cantidad_evaluaciones,
            "ultima_fecha": ultima_fecha,
            "ultima_clasificacion": ultima_clasificacion,
            "ultima_prueba": ultima_prueba
        }

    except Exception as e:
        st.error(f"Error al cargar ficha del paciente: {e}")
        return {
            "nombre": paciente_nombre,
            "sexo": "-",
            "cantidad_evaluaciones": 0,
            "ultima_fecha": "-",
            "ultima_clasificacion": "-",
            "ultima_prueba": "-"
        }


def clasificar_percentil(percentil):
    if percentil is None:
        return "Sin clasificar"
    if percentil < 10:
        return "Muy bajo"
    if percentil < 25:
        return "Bajo"
    if percentil < 50:
        return "Ligeramente bajo"
    if percentil < 75:
        return "Normal"
    if percentil < 90:
        return "Bueno"
    return "Muy bueno"


def color_clasificacion(clasificacion):
    colores = {
        "Muy bajo": "#d32f2f",
        "Bajo": "#f57c00",
        "Ligeramente bajo": "#fbc02d",
        "Normal": "#388e3c",
        "Bueno": "#1976d2",
        "Muy bueno": "#00796b",
        "Sin clasificar": "#757575"
    }
    return colores.get(clasificacion, "#757575")


def rango_percentilar(percentil):
    if percentil is None:
        return "Sin rango"
    if percentil < 3:
        return "Menor a P3"
    if percentil < 10:
        return "Entre P3 y P10"
    if percentil < 25:
        return "Entre P10 y P25"
    if percentil < 50:
        return "Entre P25 y P50"
    if percentil < 75:
        return "Entre P50 y P75"
    if percentil < 90:
        return "Entre P75 y P90"
    if percentil < 97:
        return "Entre P90 y P97"
    return "Mayor a P97"


def interpretacion_clinica(clasificacion):
    textos = {
        "Muy bajo": "Resultado marcadamente por debajo del rango funcional esperado.",
        "Bajo": "Resultado por debajo del rango funcional esperado.",
        "Ligeramente bajo": "Resultado levemente inferior al rango esperado.",
        "Normal": "Resultado dentro del rango funcional esperado.",
        "Bueno": "Resultado superior al promedio esperado.",
        "Muy bueno": "Resultado claramente superior al rango esperado."
    }
    return textos.get(clasificacion, "Sin interpretación disponible.")


def interpolar_percentil(valor_medido, tabla_percentiles):
    puntos = sorted(tabla_percentiles.items(), key=lambda x: x[1])

    if valor_medido < puntos[0][1]:
        return float(puntos[0][0])

    if valor_medido > puntos[-1][1]:
        return float(puntos[-1][0])

    for i in range(len(puntos) - 1):
        p1, v1 = puntos[i]
        p2, v2 = puntos[i + 1]

        if v1 <= valor_medido <= v2:
            if v2 == v1:
                return float(p1)
            return float(p1 + (valor_medido - v1) * (p2 - p1) / (v2 - v1))

    return None


def grupo_edad_prension(edad):
    edad = int(edad)
    if edad >= 100:
        return "+100"
    inicio = max(20, min(95, 20 + ((edad - 20) // 5) * 5))
    fin = inicio + 4
    return f"{inicio}-{fin}"


def grupo_edad_silla(edad):
    edad = int(edad)
    if edad >= 85:
        return "+84"
    if 65 <= edad <= 69:
        return "65-69"
    if 70 <= edad <= 74:
        return "70-74"
    if 75 <= edad <= 79:
        return "75-79"
    if 80 <= edad <= 84:
        return "80-84"
    return None


def calcular_resultado(prueba, sexo, edad, altura, valor_medido):
    sexo = str(sexo).strip()
    edad = int(edad)
    valor_medido = float(valor_medido)

    if prueba == "Caminata 6 minutos":
        altura = int(altura)
        altura_ref = min(TABLA_CAMINATA_6M.keys(), key=lambda x: abs(x - altura))
        edad_ref = min(TABLA_CAMINATA_6M[altura_ref].keys(), key=lambda x: abs(x - edad))

        percentiles = TABLA_CAMINATA_6M[altura_ref][edad_ref]
        percentil_estimado = interpolar_percentil(valor_medido, percentiles)

        if percentil_estimado is None:
            return None, "Sin clasificar", "-", "-", "-"

        percentil_estimado = round(percentil_estimado, 1)
        clasificacion = clasificar_percentil(percentil_estimado)
        referencia_p50 = percentiles[50]

        return (
            percentil_estimado,
            clasificacion,
            f"{referencia_p50} m",
            f"Altura ref.: {altura_ref} cm",
            f"Edad ref.: {edad_ref} años"
        )

    if prueba == "Prensión manual":
        grupo = grupo_edad_prension(edad)
        percentiles = TABLA_PRENSION[sexo][grupo]
        percentil_estimado = interpolar_percentil(valor_medido, percentiles)

        if percentil_estimado is None:
            return None, "Sin clasificar", "-", "-", "-"

        percentil_estimado = round(percentil_estimado, 1)
        clasificacion = clasificar_percentil(percentil_estimado)
        referencia_p50 = percentiles[50]

        return (
            percentil_estimado,
            clasificacion,
            f"{referencia_p50} kg",
            "-",
            f"Grupo etario: {grupo}"
        )

    if prueba == "Levantarse de la silla":
        grupo = grupo_edad_silla(edad)

        if grupo is None:
            return None, "Sin clasificar", "-", "-", "Edad fuera del rango de la tabla (65+ años)"

        percentiles = TABLA_SILLA[sexo][grupo]
        percentil_estimado = interpolar_percentil(valor_medido, percentiles)

        if percentil_estimado is None:
            return None, "Sin clasificar", "-", "-", "-"

        percentil_estimado = round(percentil_estimado, 1)
        clasificacion = clasificar_percentil(percentil_estimado)
        referencia_p50 = percentiles[50]

        return (
            percentil_estimado,
            clasificacion,
            f"{referencia_p50} rep",
            "-",
            f"Grupo etario: {grupo}"
        )

    return None, "Sin clasificar", "-", "-", "-"


# =========================================================
# UI
# =========================================================
st.title("Calculadora de Condición Física")
st.markdown("""
<style>
div[data-testid="stMetricValue"] {
    font-size: 1.35rem !important;
}
div[data-testid="stMetricLabel"] {
    font-size: 0.80rem !important;
}
div[data-testid="stMetric"] {
    padding-top: 0.2rem !important;
    padding-bottom: 0.2rem !important;
}
</style>
""", unsafe_allow_html=True)

with st.expander("➕ Nuevo paciente"):
    nuevo_nombre = st.text_input("Nombre del nuevo paciente", key="nuevo_nombre_alta")
    nuevo_sexo = st.selectbox(
        "Sexo del nuevo paciente",
        ["hombre", "mujer"],
        key="nuevo_sexo_alta"
    )

    if st.button("Guardar paciente", key="btn_guardar_paciente"):
        if not nuevo_nombre.strip():
            st.warning("Ingresá el nombre del paciente.")
        else:
            try:
                guardar_paciente(nuevo_nombre, nuevo_sexo)
                st.success("Paciente agregado correctamente.")
                st.rerun()
            except Exception as e:
                st.error(f"Error al guardar paciente: {e}")

pacientes = obtener_pacientes()
opciones_pacientes = [p["nombre"] for p in pacientes]

if not opciones_pacientes:
    st.warning("No hay pacientes cargados. Agregá uno desde '➕ Nuevo paciente'.")
    st.stop()

paciente_nombre = st.selectbox(
    "Seleccionar paciente",
    opciones_pacientes,
    key="selector_paciente"
)

# =========================================================
# FICHA DEL PACIENTE
# =========================================================
ficha = obtener_ficha_paciente(paciente_nombre)

st.markdown("### Ficha del paciente")
st.caption(
    f"Paciente: {ficha['nombre']} | "
    f"Sexo: {str(ficha['sexo']).capitalize() if ficha['sexo'] != '-' else '-'} | "
    f"Evaluaciones: {ficha['cantidad_evaluaciones']} | "
    f"Última evaluación: {ficha['ultima_fecha']} | "
    f"Última clasificación: {ficha['ultima_clasificacion']} | "
    f"Última prueba: {ficha['ultima_prueba']}"
)

st.divider()
paciente_sexo_guardado = next((p["sexo"] for p in pacientes if p["nombre"] == paciente_nombre), None)

prueba = st.selectbox(
    "Seleccionar prueba",
    ["Caminata 6 minutos", "Prensión manual", "Levantarse de la silla"],
    key="selector_prueba"
)

sexo_default = "Hombre"
if paciente_sexo_guardado == "mujer":
    sexo_default = "Mujer"
elif paciente_sexo_guardado == "hombre":
    sexo_default = "Hombre"

sexo = st.selectbox(
    "Sexo",
    ["Hombre", "Mujer"],
    index=0 if sexo_default == "Hombre" else 1,
    key="selector_sexo"
)

altura = None
valor_medido = None

if prueba == "Caminata 6 minutos":
    edad = st.selectbox("Edad", list(range(40, 81)), index=20, key="edad_caminata")
    altura = st.selectbox("Altura (cm)", [150, 160, 170, 180, 190], index=2, key="altura_caminata")
    valor_medido = st.number_input(
        "Distancia caminada (metros)",
        min_value=0.0,
        max_value=2000.0,
        value=600.0,
        step=1.0,
        format="%.2f",
        key="valor_caminata"
    )

elif prueba == "Prensión manual":
    edad = st.selectbox("Edad", list(range(20, 101)), index=45, key="edad_prension")
    valor_medido = st.number_input(
        "Fuerza de prensión (kg)",
        min_value=0.0,
        max_value=100.0,
        value=25.0,
        step=0.1,
        format="%.1f",
        key="valor_prension"
    )

elif prueba == "Levantarse de la silla":
    edad = st.selectbox("Edad", list(range(65, 101)), index=10, key="edad_silla")
    valor_medido = st.number_input(
        "Cantidad de repeticiones",
        min_value=0.0,
        max_value=60.0,
        value=12.0,
        step=1.0,
        format="%.0f",
        key="valor_silla"
    )

percentil, clasificacion, referencia_p50, referencia_altura, referencia_edad = calcular_resultado(
    prueba=prueba,
    sexo=sexo,
    edad=edad,
    altura=altura,
    valor_medido=valor_medido
)

# =========================================================
# RESULTADO
# =========================================================
color = color_clasificacion(clasificacion)

st.markdown(
    f"""
    <div style="
        background-color:{color};
        color:white;
        padding:10px 12px;
        border-radius:8px;
        text-align:center;
        font-size:18px;
        font-weight:600;
        margin-top:18px;
        margin-bottom:10px;
    ">
        {clasificacion}
    </div>
    """,
    unsafe_allow_html=True
)
st.markdown(
    f"""
    <div style="
        background-color:#dff0e6;
        color:#1b5e20;
        padding:8px 12px;
        border-radius:8px;
        font-size:15px;
        margin-bottom:14px;
    ">
        Percentil estimado: <b>P{percentil if percentil is not None else "-"}</b>
    </div>
    """,
    unsafe_allow_html=True
)
st.write(f"**Rango percentilar:** {rango_percentilar(percentil)}")
st.write(f"**Referencia P50:** {referencia_p50}")

if referencia_altura != "-":
    st.write(f"**Referencia de altura:** {referencia_altura}")

if referencia_edad != "-":
    st.write(f"**Referencia etaria:** {referencia_edad}")

st.write(f"**Interpretación clínica:** {interpretacion_clinica(clasificacion)}")

# =========================================================
# GUARDADO
# =========================================================
if st.button("Guardar evaluación", key="btn_guardar_evaluacion"):
    if not paciente_nombre:
        st.warning("Seleccioná un paciente antes de guardar.")
    elif percentil is None:
        st.warning("No se pudo calcular el percentil.")
    else:
        try:
            guardar_evaluacion(
                paciente_nombre=paciente_nombre,
                sexo=sexo,
                edad=edad,
                prueba=prueba,
                valor_medido=valor_medido,
                percentil=percentil,
                clasificacion=clasificacion
            )
            st.success("Evaluación guardada correctamente.")
            st.rerun()
        except Exception as e:
            st.error(f"Error al guardar: {e}")

# =========================================================
# HISTORIAL Y GRAFICOS
# =========================================================
if paciente_nombre:
    st.markdown("### Historial del paciente")

    df_historial = obtener_historial_paciente(paciente_nombre)

    if not df_historial.empty:
        prueba_filtro = st.selectbox(
            "Filtrar historial por prueba",
            options=["Todas", "Caminata 6 minutos", "Prensión manual", "Levantarse de la silla"],
            index=0,
            key="filtro_historial_prueba"
        )

        if prueba_filtro == "Todas":
            df_historial_filtrado = df_historial.copy()
        else:
            df_historial_filtrado = df_historial[
                df_historial["prueba"].astype(str).str.strip() == prueba_filtro
            ].copy()

        columnas_mostrar = ["id", "fecha", "prueba", "valor_medido", "percentil", "clasificacion"]
        columnas_existentes = [c for c in columnas_mostrar if c in df_historial_filtrado.columns]
        df_historial_mostrar = df_historial_filtrado[columnas_existentes].copy()

        if "fecha" in df_historial_mostrar.columns:
            df_historial_mostrar["fecha"] = pd.to_datetime(
                df_historial_mostrar["fecha"],
                errors="coerce"
            ).dt.strftime("%Y-%m-%d")

        df_historial_mostrar = df_historial_mostrar.sort_values(by="fecha", ascending=False)

        st.markdown("**Fecha | Prueba | Valor | Percentil | Clasificación | Eliminar**")

        for _, row in df_historial_mostrar.iterrows():
            col1, col2, col3, col4, col5, col6 = st.columns([1, 2, 1, 1, 1, 0.5])

            col1.write(row.get("fecha", ""))
            col2.write(row.get("prueba", ""))
            col3.write(row.get("valor_medido", ""))
            col4.write(row.get("percentil", ""))
            col5.write(row.get("clasificacion", ""))

            if col6.button("🗑", key=f"del_{row['id']}"):
                try:
                    eliminar_evaluacion(row["id"])
                    st.success("Evaluación eliminada.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al eliminar: {e}")

        csv_historial = (
            df_historial_mostrar
            .drop(columns=["id"], errors="ignore")
            .to_csv(index=False)
            .encode("utf-8")
        )

        st.download_button(
            label="Descargar historial CSV",
            data=csv_historial,
            file_name=f"historial_{paciente_nombre.replace(' ', '_')}.csv",
            mime="text/csv",
            key="btn_descargar_csv"
        )

        pdf_df = df_historial_mostrar.drop(columns=["id"], errors="ignore").copy()
        pdf_buffer = generar_pdf_historial(paciente_nombre, pdf_df)

        st.download_button(
            label="Descargar historial PDF",
            data=pdf_buffer,
            file_name=f"historial_{paciente_nombre.replace(' ', '_')}.pdf",
            mime="application/pdf",
            key="btn_descargar_pdf"
        )

        if {"fecha", "percentil", "prueba"}.issubset(df_historial.columns):
            df_graf_base = df_historial.copy()

            df_graf_base["fecha"] = pd.to_datetime(df_graf_base["fecha"], errors="coerce").dt.date
            df_graf_base["percentil"] = pd.to_numeric(df_graf_base["percentil"], errors="coerce")
            df_graf_base["prueba"] = df_graf_base["prueba"].astype(str).str.strip()

            df_graf_base = df_graf_base.dropna(subset=["fecha", "percentil", "prueba"])

            pruebas_orden = [
                "Caminata 6 minutos",
                "Prensión manual",
                "Levantarse de la silla"
            ]

            if prueba_filtro != "Todas":
                pruebas_orden = [prueba_filtro]

            for prueba_graf in pruebas_orden:
                df_prueba = df_graf_base[df_graf_base["prueba"] == prueba_graf].copy()

                if not df_prueba.empty:
                    df_prueba = (
                        df_prueba.groupby("fecha", as_index=False)["percentil"]
                        .mean()
                        .sort_values("fecha")
                    )

                    df_prueba["Etiqueta"] = df_prueba["percentil"].apply(lambda x: f"P{round(x, 1)}")

                    ultimo = df_prueba["percentil"].iloc[-1]

                    if len(df_prueba) >= 2:
                        anterior = df_prueba["percentil"].iloc[-2]
                        diferencia = round(ultimo - anterior, 1)
                        texto_cambio = f"{diferencia:+.1f}"
                    else:
                        diferencia = None
                        texto_cambio = "N/D"

                    st.caption(f"Percentil actual: P{round(ultimo, 1)} | Cambio vs anterior: {texto_cambio}")
                    st.markdown(f"### Evolución del percentil - {prueba_graf}")

                    linea = alt.Chart(df_prueba).mark_line(point=False).encode(
                        x=alt.X(
                            "yearmonthdate(fecha):T",
                            title="Fecha",
                            axis=alt.Axis(format="%d-%m-%Y")
                        ),
                        y=alt.Y("percentil:Q", title="Percentil")
                    )

                    puntos = alt.Chart(df_prueba).mark_circle(size=90).encode(
                        x=alt.X("yearmonthdate(fecha):T"),
                        y=alt.Y("percentil:Q")
                    )

                    etiquetas = alt.Chart(df_prueba).mark_text(
                        dy=-12,
                        fontSize=12
                    ).encode(
                        x=alt.X("yearmonthdate(fecha):T"),
                        y=alt.Y("percentil:Q"),
                        text="Etiqueta:N"
                    )

                    grafico = (linea + puntos + etiquetas).properties(height=260)

                    st.altair_chart(grafico, use_container_width=True)

                    if diferencia is not None:
                        if diferencia > 0:
                            st.success(f"↑ Mejora de {diferencia} percentiles desde la evaluación anterior")
                        elif diferencia < 0:
                            st.warning(f"↓ Disminución de {abs(diferencia)} percentiles desde la evaluación anterior")
                        else:
                            st.info("Sin cambios respecto a la evaluación anterior")
    else:
        st.info("Todavía no hay evaluaciones guardadas para este paciente.")









