import streamlit as st
import pandas as pd
import unicodedata
from datetime import datetime
from supabase import create_client, Client

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
# UTILIDADES
# =========================================================
def normalizar_texto(texto):
    texto = str(texto).strip().lower()
    texto = unicodedata.normalize("NFKD", texto)
    texto = texto.encode("ascii", "ignore").decode("utf-8")
    texto = texto.replace("(", "").replace(")", "")
    texto = texto.replace("%", "")
    return texto


def guardar_evaluacion(paciente, sexo, edad, prueba, valor_medido, percentil, clasificacion):
    payload = {
        "fecha": datetime.now().strftime("%Y-%m-%d"),
        "paciente": str(paciente).strip(),
        "sexo": str(sexo).strip().lower(),
        "edad": int(edad),
        "prueba": str(prueba).strip(),
        "valor_medido": float(valor_medido),
        "percentilo": round(float(percentil), 1) if percentil is not None else None,
        "clasificacion": str(clasificacion).strip()
    }

    respuesta = supabase.table("evaluaciones").insert(payload).execute()
    return respuesta


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


def obtener_pacientes_existentes():
    try:
        respuesta = supabase.table("evaluaciones").select("paciente").execute()

        if not respuesta.data:
            return []

        df = pd.DataFrame(respuesta.data)

        if "paciente" not in df.columns:
            return []

        pacientes = (
            df["paciente"]
            .dropna()
            .astype(str)
            .str.strip()
            .replace("", pd.NA)
            .dropna()
            .drop_duplicates()
            .sort_values()
            .tolist()
        )

        return pacientes

    except Exception:
        return []


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
    mapa = {
        "Muy bajo": "#d32f2f",
        "Bajo": "#f57c00",
        "Ligeramente bajo": "#fbc02d",
        "Normal": "#388e3c",
        "Bueno": "#1976d2",
        "Muy bueno": "#00796b",
        "Sin clasificar": "#757575"
    }
    return mapa.get(clasificacion, "#757575")


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
    mapa = {
        "Muy bajo": "Capacidad aeróbica marcadamente por debajo del rango funcional esperado.",
        "Bajo": "Capacidad aeróbica por debajo del rango funcional esperado.",
        "Ligeramente bajo": "Capacidad aeróbica levemente inferior al rango esperado.",
        "Normal": "Capacidad aeróbica dentro del rango funcional esperado.",
        "Bueno": "Capacidad aeróbica superior al promedio esperado.",
        "Muy bueno": "Capacidad aeróbica claramente superior al rango esperado."
    }
    return mapa.get(clasificacion, "Sin interpretación disponible.")


# =========================================================
# CALCULO CAMINATA 6 MINUTOS
# Basado en la tabla que compartiste
# =========================================================
def calcular_resultado(prueba, sexo, edad, altura, valor_medido):

    if prueba != "Caminata 6 minutos":
        return None, "Sin clasificar", "-"

    tabla = {
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

    altura = int(altura)
    edad = int(edad)
    distancia = float(valor_medido)

    altura_ref = min(tabla.keys(), key=lambda x: abs(x - altura))
    edad_ref = min(tabla[altura_ref].keys(), key=lambda x: abs(x - edad))

    percentiles = tabla[altura_ref][edad_ref]
    percentiles_ordenados = sorted(percentiles.items(), key=lambda x: x[1])

    percentil_estimado = None

    for i in range(len(percentiles_ordenados) - 1):
        p1, v1 = percentiles_ordenados[i]
        p2, v2 = percentiles_ordenados[i + 1]

        if v1 <= distancia <= v2:
            if v2 == v1:
                percentil_estimado = p1
            else:
                percentil_estimado = p1 + (distancia - v1) * (p2 - p1) / (v2 - v1)
            break

    if distancia < percentiles_ordenados[0][1]:
        percentil_estimado = percentiles_ordenados[0][0]

    if distancia > percentiles_ordenados[-1][1]:
        percentil_estimado = percentiles_ordenados[-1][0]

    if percentil_estimado is None:
        return None, "Sin clasificar", "-"

    percentil_estimado = round(percentil_estimado, 1)
    clasificacion = clasificar_percentil(percentil_estimado)
    referencia_p50 = percentiles[50]

    return percentil_estimado, clasificacion, f"{referencia_p50} m"


# =========================================================
# UI
# =========================================================
st.title("Calculadora de Condición Física")

pacientes_existentes = obtener_pacientes_existentes()
opciones_paciente = [""] + pacientes_existentes + ["Otro / escribir nuevo"]

paciente_opcion = st.selectbox("Paciente", options=opciones_paciente, index=0)

if paciente_opcion == "Otro / escribir nuevo":
    paciente = st.text_input("Nombre del paciente")
else:
    paciente = paciente_opcion

sexo = st.selectbox("Sexo", ["Hombre", "Mujer"])
prueba = st.selectbox("Seleccionar prueba", ["Caminata 6 minutos"])
edad = st.selectbox("Edad", list(range(40, 81)), index=20)
altura = st.selectbox("Altura (cm)", [150, 160, 170, 180, 190], index=2)

distancia = st.number_input(
    "Distancia caminada (metros)",
    min_value=0.0,
    max_value=2000.0,
    value=600.0,
    step=1.0,
    format="%.2f"
)

valor_medido = distancia

percentil, clasificacion, referencia_p50 = calcular_resultado(
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
        padding:16px;
        border-radius:10px;
        text-align:center;
        font-size:28px;
        font-weight:700;
        margin-top:20px;
        margin-bottom:15px;
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
        padding:14px;
        border-radius:10px;
        font-size:22px;
        margin-bottom:20px;
    ">
        Percentil estimado: <b>P{percentil if percentil is not None else "-"}</b>
    </div>
    """,
    unsafe_allow_html=True
)

st.write(f"**Rango percentilar:** {rango_percentilar(percentil)}")
st.write(f"**Referencia P50:** {referencia_p50}")
st.write(f"**Interpretación clínica:** {interpretacion_clinica(clasificacion)}")

# =========================================================
# GUARDADO
# =========================================================
if st.button("Guardar evaluación"):
    if not paciente or str(paciente).strip() == "":
        st.warning("Ingresá el nombre del paciente antes de guardar.")
    elif percentil is None:
        st.warning("No se pudo calcular el percentil.")
    else:
        try:
            guardar_evaluacion(
                paciente=paciente,
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
# HISTORIAL
# =========================================================
if paciente and str(paciente).strip() != "":
    st.markdown("### Historial del paciente")

    df_historial = obtener_historial_paciente(paciente)

    if not df_historial.empty:
        columnas_mostrar = ["fecha", "prueba", "valor_medido", "percentilo", "clasificacion"]
        columnas_existentes = [c for c in columnas_mostrar if c in df_historial.columns]
        df_historial_mostrar = df_historial[columnas_existentes].copy()

        if "fecha" in df_historial_mostrar.columns:
            df_historial_mostrar["fecha"] = pd.to_datetime(
                df_historial_mostrar["fecha"],
                errors="coerce"
            ).dt.strftime("%Y-%m-%d")

        st.dataframe(
            df_historial_mostrar,
            use_container_width=True,
            hide_index=True
        )

        if "fecha" in df_historial.columns and "percentilo" in df_historial.columns:
            df_graf = df_historial.copy()
            df_graf["fecha"] = pd.to_datetime(df_graf["fecha"], errors="coerce")
            df_graf["percentilo"] = pd.to_numeric(df_graf["percentilo"], errors="coerce")
            df_graf = df_graf.dropna(subset=["fecha", "percentilo"]).sort_values("fecha")

            if not df_graf.empty:
                st.markdown("### Evolución del percentil")
                st.line_chart(
                    df_graf.set_index("fecha")["percentilo"],
                    use_container_width=True
                )
    else:
        st.info("Todavía no hay evaluaciones guardadas para este paciente.")
