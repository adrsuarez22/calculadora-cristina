import streamlit as st
import pandas as pd
import unicodedata
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

service_account_info = dict(st.secrets["gcp_service_account"])
service_account_info["private_key"] = service_account_info["private_key"].replace("\\n", "\n")

credentials = Credentials.from_service_account_info(
    service_account_info,
    scopes=scope
)

client = gspread.authorize(credentials)
sheet = client.open("Evaluaciones_Funcionales").sheet1

st.set_page_config(page_title="Calculadora de Condición Física", layout="centered")

scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

credentials = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=scope
)
client = gspread.authorize(credentials)
sheet = client.open("Evaluaciones_Funcionales").sheet1

st.set_page_config(page_title="Calculadora de Condición Física", layout="centered")

# =========================
# Utilidades generales
# =========================
def normalizar_texto(texto):
    texto = str(texto).strip().lower()
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
    texto = texto.replace("(", "").replace(")", "")
    texto = texto.replace("%", "")
    texto = texto.replace(".", "").replace(",", "")
    texto = texto.replace("-", "_").replace("/", "_")
    texto = "_".join(texto.split())
    return texto


def normalizar_columnas(df):
    df = df.copy()
    df.columns = [normalizar_texto(c) for c in df.columns]
    return df


def buscar_columna(df, candidatos, fallback_index=None, obligatoria=True):
    columnas = list(df.columns)
    columnas_set = set(columnas)

    for c in candidatos:
        c_norm = normalizar_texto(c)
        if c_norm in columnas_set:
            return c_norm

    if fallback_index is not None and len(columnas) > fallback_index:
        return columnas[fallback_index]

    if obligatoria:
        raise ValueError(
            f"No se encontró ninguna de estas columnas: {candidatos}. "
            f"Columnas disponibles: {columnas}"
        )
    return None


def convertir_numerico(df, columnas):
    for c in columnas:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def normalizar_sexo_serie(serie):
    return (
        serie.astype(str)
        .str.strip()
        .str.lower()
        .replace({
            "hombres": "hombre",
            "mujeres": "mujer",
            "male": "hombre",
            "female": "mujer",
            "m": "hombre",
            "f": "mujer"
        })
    )


def formatear_sexo_ui(valor):
    v = str(valor).strip().lower()
    if v == "hombre":
        return "hombre"
    if v == "mujer":
        return "mujer"
    return v


def edad_a_grupo_silla(edad):
    if 65 <= edad <= 69:
        return "AG1"
    elif 70 <= edad <= 74:
        return "AG2"
    elif 75 <= edad <= 79:
        return "AG3"
    elif 80 <= edad <= 84:
        return "AG4"
    elif edad >= 85:
        return "AG5"
    return None


def parsear_rango_edad(texto):
    t = str(texto).strip().replace(" ", "")
    if "-" in t:
        partes = t.split("-")
        try:
            return int(partes[0]), int(partes[1])
        except:
            return None
    if t.startswith("+"):
        try:
            inicio = int(t[1:])
            return inicio, 999
        except:
            return None
    return None


def buscar_rango_edad_prension(edad, rangos_disponibles):
    for r in rangos_disponibles:
        parsed = parsear_rango_edad(r)
        if parsed is None:
            continue
        desde, hasta = parsed
        if desde <= edad <= hasta:
            return r
    return None


def formatear_percentil(p):
    if p is None:
        return "N/D"
    if float(p).is_integer():
        return str(int(p))
    return f"{p:.1f}"


def obtener_color_percentil(p):
    if p is None:
        return "#9E9E9E"
    if p < 10:
        return "#D32F2F"
    elif p < 25:
        return "#F57C00"
    elif p <= 75:
        return "#388E3C"
    else:
        return "#1976D2"


def obtener_etiqueta_semaforo(p):
    if p is None:
        return "Sin clasificación"
    if p < 10:
        return "Muy bajo"
    elif p < 25:
        return "Bajo"
    elif p <= 75:
        return "Normal"
    else:
        return "Alto"


def interpretar_clinicamente(p, prueba):
    if p is None:
        return "No se pudo estimar el percentil."

    if prueba == "Caminata 6 minutos":
        if p < 10:
            return "Capacidad aeróbica muy disminuida para su referencia. Conviene seguimiento clínico y plan de intervención."
        elif p < 25:
            return "Capacidad aeróbica por debajo de lo esperado. Sugiere margen claro de mejora funcional."
        elif p <= 75:
            return "Capacidad aeróbica dentro del rango funcional esperado."
        else:
            return "Capacidad aeróbica por encima de lo esperado para su referencia."

    if prueba == "Fuerza prensión":
        if p < 10:
            return "Fuerza de prensión muy baja para su referencia. Puede sugerir fragilidad o pérdida de fuerza significativa."
        elif p < 25:
            return "Fuerza de prensión baja. Conviene seguimiento y trabajo específico de fuerza."
        elif p <= 75:
            return "Fuerza de prensión dentro del rango esperado."
        else:
            return "Fuerza de prensión por encima de la media para su referencia."

    if prueba == "Levantarse de silla":
        if p < 10:
            return "Rendimiento funcional muy bajo en miembros inferiores. Sugiere menor fuerza funcional y necesidad de intervención."
        elif p < 25:
            return "Rendimiento bajo para su referencia. Conviene seguimiento y entrenamiento funcional."
        elif p <= 75:
            return "Rendimiento funcional dentro del rango esperado."
        else:
            return "Rendimiento funcional por encima de lo esperado."

    return "Interpretación no disponible."


def estimar_percentil(valor_medido, df_ref, col_valor, col_percentil):
    ref = df_ref[[col_valor, col_percentil]].dropna().copy()
    ref = ref.sort_values(by=col_valor).drop_duplicates(subset=[col_valor, col_percentil])

    if ref.empty:
        return None, "Sin datos de referencia.", None

    valores = ref[col_valor].tolist()
    percentiles = ref[col_percentil].tolist()

    exactos = ref[ref[col_valor] == valor_medido]
    if not exactos.empty:
        p = float(exactos.iloc[0][col_percentil])
        return p, f"Percentil exacto: P{formatear_percentil(p)}", f"P{formatear_percentil(p)}"

    if valor_medido < min(valores):
        p = float(percentiles[0])
        return p, "Por debajo del percentil mínimo disponible.", f"< P{formatear_percentil(p)}"

    if valor_medido > max(valores):
        p = float(percentiles[-1])
        return p, "Por encima del percentil máximo disponible.", f"> P{formatear_percentil(p)}"

    for i in range(len(ref) - 1):
        v1 = float(ref.iloc[i][col_valor])
        v2 = float(ref.iloc[i + 1][col_valor])
        p1 = float(ref.iloc[i][col_percentil])
        p2 = float(ref.iloc[i + 1][col_percentil])

        if v1 <= valor_medido <= v2:
            if v2 == v1:
                p_est = p1
            else:
                p_est = p1 + ((valor_medido - v1) / (v2 - v1)) * (p2 - p1)

            texto = f"Percentil estimado: P{p_est:.1f}"
            rango = f"Entre P{formatear_percentil(p1)} y P{formatear_percentil(p2)}"
            return p_est, texto, rango

    return None, "No se pudo estimar el percentil.", None


def mostrar_semaforo(p):
    color = obtener_color_percentil(p)
    etiqueta = obtener_etiqueta_semaforo(p)

    st.markdown(
        f"""
        <div style="
            background-color:{color};
            color:white;
            padding:14px 18px;
            border-radius:10px;
            font-weight:700;
            margin-top:8px;
            margin-bottom:12px;
            text-align:center;
            font-size:18px;">
            {etiqueta}
        </div>
        """,
        unsafe_allow_html=True
    )


def guardar_evaluacion(paciente, sexo, edad, prueba, valor_medido, percentil, clasificacion):
    sheet.append_row([
        datetime.now().strftime("%Y-%m-%d"),
        paciente,
        sexo,
        int(edad),
        prueba,
        float(valor_medido),
        round(float(percentil), 1) if percentil is not None else "",
        clasificacion
    ])


# =========================
# Carga de datos
# =========================
@st.cache_data
def cargar_caminata():
    df = pd.read_csv("caminata_6min_long.csv")
    df = normalizar_columnas(df)

    col_altura = buscar_columna(df, ["altura_cm", "altura", "talla", "height"], fallback_index=0)
    col_edad = buscar_columna(df, ["edad_anos", "edad", "anos", "age"], fallback_index=1)
    col_percentil = buscar_columna(df, ["percentil", "percentil_ref", "p"], fallback_index=2)
    col_resultado = buscar_columna(df, ["distancia_m", "distancia", "metros", "resultado"], fallback_index=3)

    df = convertir_numerico(df, [col_altura, col_edad, col_percentil, col_resultado])
    df = df.dropna(subset=[col_altura, col_edad, col_percentil, col_resultado])

    return df, {"altura": col_altura, "edad": col_edad, "percentil": col_percentil, "resultado": col_resultado}


@st.cache_data
def cargar_prension():
    df = pd.read_csv("prension_manual_long.csv")
    df = normalizar_columnas(df)

    col_sexo = buscar_columna(df, ["sexo", "genero", "sex"], fallback_index=0)
    col_edad = buscar_columna(df, ["edad_rango", "edad", "edad_anos", "anos", "age"], fallback_index=1)
    col_percentil = buscar_columna(df, ["percentil", "percentil_ref", "p"], fallback_index=2)
    col_resultado = buscar_columna(df, ["fuerza_kg", "fuerza", "kg", "prension", "prension_kg"], fallback_index=3)

    df[col_sexo] = normalizar_sexo_serie(df[col_sexo])
    df[col_edad] = df[col_edad].astype(str).str.strip()
    df = convertir_numerico(df, [col_percentil, col_resultado])
    df = df.dropna(subset=[col_percentil, col_resultado])

    return df, {"sexo": col_sexo, "edad": col_edad, "percentil": col_percentil, "resultado": col_resultado}


@st.cache_data
def cargar_silla():
    df = pd.read_csv("silla_long.csv")
    df = normalizar_columnas(df)

    col_sexo = buscar_columna(df, ["sexo", "genero", "sex"], fallback_index=0)
    col_grupo = buscar_columna(df, ["grupo_edad", "grupoedad", "grupo", "ag"], fallback_index=1)
    col_percentil = buscar_columna(df, ["percentil", "percentil_ref", "p"], fallback_index=4)
    col_resultado = buscar_columna(df, ["valor_repeticiones", "repeticiones", "resultado", "levantadas"], fallback_index=5)

    df[col_sexo] = normalizar_sexo_serie(df[col_sexo])
    df[col_grupo] = df[col_grupo].astype(str).str.strip().str.upper()
    df = convertir_numerico(df, [col_percentil, col_resultado])
    df = df.dropna(subset=[col_percentil, col_resultado])

    return df, {"sexo": col_sexo, "grupo": col_grupo, "percentil": col_percentil, "resultado": col_resultado}


# =========================
# Interfaz
# =========================
st.title("Calculadora de Condición Física")

paciente = st.text_input("Paciente")
sexo_ui_global = st.selectbox("Sexo", ["Hombre", "Mujer"])
sexo_global = formatear_sexo_ui(sexo_ui_global)

prueba = st.selectbox(
    "Seleccionar prueba",
    ["Caminata 6 minutos", "Fuerza prensión", "Levantarse de silla"]
)

if prueba == "Caminata 6 minutos":
    df, cols = cargar_caminata()

    edades = sorted(df[cols["edad"]].dropna().astype(int).unique().tolist())
    alturas = sorted(df[cols["altura"]].dropna().astype(int).unique().tolist())

    edad = st.selectbox("Edad", edades)
    altura = st.selectbox("Altura (cm)", alturas)
    valor_medido = st.number_input("Distancia caminada (metros)", min_value=0.0, value=451.0, step=1.0)

    ref = df[(df[cols["edad"]] == edad) & (df[cols["altura"]] == altura)].copy()

    if ref.empty:
        st.warning("No hay datos de referencia para esa combinación.")
    else:
        p50 = ref.loc[ref[cols["percentil"]] == 50, cols["resultado"]]
        p50_texto = f"{float(p50.iloc[0]):.0f} m" if not p50.empty else "No disponible"

        p_est, texto_p, rango_p = estimar_percentil(valor_medido, ref, cols["resultado"], cols["percentil"])
        clasificacion = obtener_etiqueta_semaforo(p_est)

        mostrar_semaforo(p_est)
        st.success(texto_p)
        if rango_p:
            st.write(f"**Rango percentilar:** {rango_p}")
        st.write(f"**Referencia P50:** {p50_texto}")
        st.write(f"**Interpretación clínica:** {interpretar_clinicamente(p_est, prueba)}")

        if st.button("Guardar evaluación", key="guardar_caminata"):
            if paciente.strip() == "":
                st.error("Debés completar el nombre del paciente antes de guardar.")
            else:
                guardar_evaluacion(
                    paciente=paciente.strip(),
                    sexo=sexo_global,
                    edad=edad,
                    prueba=prueba,
                    valor_medido=valor_medido,
                    percentil=p_est,
                    clasificacion=clasificacion
                )
                st.success("Evaluación guardada correctamente.")

elif prueba == "Fuerza prensión":
    df, cols = cargar_prension()

    sexo = sexo_global
    edad = st.number_input("Edad", min_value=20, max_value=110, value=60, step=1)
    valor_medido = st.number_input("Fuerza medida (kg)", min_value=0.0, value=25.0, step=0.1)

    rangos = sorted(df[cols["edad"]].dropna().astype(str).unique().tolist())
    rango_edad = buscar_rango_edad_prension(edad, rangos)

    if rango_edad is None:
        st.warning("No hay un rango de edad válido para esa edad.")
    else:
        ref = df[(df[cols["sexo"]] == sexo) & (df[cols["edad"]].astype(str) == str(rango_edad))].copy()

        if ref.empty:
            st.warning("No hay datos de referencia para esa combinación.")
        else:
            p50 = ref.loc[ref[cols["percentil"]] == 50, cols["resultado"]]
            p50_texto = f"{float(p50.iloc[0]):.1f} kg" if not p50.empty else "No disponible"

            p_est, texto_p, rango_p = estimar_percentil(valor_medido, ref, cols["resultado"], cols["percentil"])
            clasificacion = obtener_etiqueta_semaforo(p_est)

            mostrar_semaforo(p_est)
            st.success(texto_p)
            if rango_p:
                st.write(f"**Rango percentilar:** {rango_p}")
            st.write(f"**Rango de edad utilizado:** {rango_edad}")
            st.write(f"**Referencia P50:** {p50_texto}")
            st.write(f"**Interpretación clínica:** {interpretar_clinicamente(p_est, prueba)}")

            if st.button("Guardar evaluación", key="guardar_prension"):
                if paciente.strip() == "":
                    st.error("Debés completar el nombre del paciente antes de guardar.")
                else:
                    guardar_evaluacion(
                        paciente=paciente.strip(),
                        sexo=sexo,
                        edad=edad,
                        prueba=prueba,
                        valor_medido=valor_medido,
                        percentil=p_est,
                        clasificacion=clasificacion
                    )
                    st.success("Evaluación guardada correctamente.")

elif prueba == "Levantarse de silla":
    df, cols = cargar_silla()

    sexo = sexo_global
    edad = st.number_input("Edad", min_value=65, max_value=110, value=70, step=1)
    valor_medido = st.number_input("Repeticiones realizadas", min_value=0.0, value=11.0, step=1.0)

    grupo = edad_a_grupo_silla(edad)

    if grupo is None:
        st.warning("No hay grupo etario válido para esa edad.")
    else:
        ref = df[(df[cols["sexo"]] == sexo) & (df[cols["grupo"]] == grupo)].copy()

        if ref.empty:
            st.warning("No hay datos de referencia para esa combinación.")
        else:
            p50 = ref.loc[ref[cols["percentil"]] == 50, cols["resultado"]]
            p50_texto = f"{float(p50.iloc[0]):.0f}" if not p50.empty else "No disponible"

            p_est, texto_p, rango_p = estimar_percentil(valor_medido, ref, cols["resultado"], cols["percentil"])
            clasificacion = obtener_etiqueta_semaforo(p_est)

            mostrar_semaforo(p_est)
            st.success(texto_p)
            if rango_p:
                st.write(f"**Rango percentilar:** {rango_p}")
            st.write(f"**Grupo de edad utilizado:** {grupo}")
            st.write(f"**Referencia P50:** {p50_texto} repeticiones")
            st.write(f"**Interpretación clínica:** {interpretar_clinicamente(p_est, prueba)}")

            if st.button("Guardar evaluación", key="guardar_silla"):
                if paciente.strip() == "":
                    st.error("Debés completar el nombre del paciente antes de guardar.")
                else:
                    guardar_evaluacion(
                        paciente=paciente.strip(),
                        sexo=sexo,
                        edad=edad,
                        prueba=prueba,
                        valor_medido=valor_medido,
                        percentil=p_est,
                        clasificacion=clasificacion
                    )
                    st.success("Evaluación guardada correctamente.")



