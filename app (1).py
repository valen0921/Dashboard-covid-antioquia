import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

st.set_page_config(
    page_title="COVID-19 Antioquia",
    page_icon="📊",
    layout="wide"
)

@st.cache_data
def cargar_datos():
    ruta = Path(__file__).parent / "covid_antioquia_resumen.csv"
    datos = pd.read_csv(ruta)

    datos["fecha_diagnostico"] = pd.to_datetime(
        datos["fecha_diagnostico"], errors="coerce"
    )

    for col in [
        "casos", "edad_promedio", "dias_diagnostico_promedio"
    ]:
        datos[col] = pd.to_numeric(datos[col], errors="coerce")

    return datos


df = cargar_datos()

st.title("📊 Dashboard de COVID-19 en Antioquia")
st.write(
    "Análisis interactivo de casos registrados, recuperación, "
    "mortalidad y comportamiento temporal."
)

# Filtros
st.sidebar.header("🔎 Filtros")

fechas = df["fecha_diagnostico"].dropna()
inicio_min = fechas.min().date()
fin_max = fechas.max().date()

rango = st.sidebar.date_input(
    "Periodo de diagnóstico",
    value=(inicio_min, fin_max),
    min_value=inicio_min,
    max_value=fin_max
)

lista_municipios = sorted(
    df["ciudad_municipio_nom"].dropna().unique().tolist()
)
municipios = st.sidebar.multiselect(
    "Municipio", lista_municipios
)

lista_sexos = sorted(df["sexo"].dropna().unique().tolist())
sexos = st.sidebar.multiselect("Sexo", lista_sexos)

lista_estados = sorted(df["estado"].dropna().unique().tolist())
estados = st.sidebar.multiselect("Estado clínico", lista_estados)

# Aplicar filtros
datos = df.copy()

if len(rango) == 2:
    fecha_inicio = pd.Timestamp(rango[0])
    fecha_fin = pd.Timestamp(rango[1]) + pd.Timedelta(days=1)

    datos = datos[
        datos["fecha_diagnostico"].ge(fecha_inicio)
        & datos["fecha_diagnostico"].lt(fecha_fin)
    ]

if municipios:
    datos = datos[datos["ciudad_municipio_nom"].isin(municipios)]

if sexos:
    datos = datos[datos["sexo"].isin(sexos)]

if estados:
    datos = datos[datos["estado"].isin(estados)]

# Indicadores: sumar los casos representados por cada grupo
total = int(datos["casos"].sum())

recuperados = int(
    datos.loc[
        datos["recuperado"].str.lower().eq("recuperado"), "casos"
    ].sum()
)

fallecidos = int(
    datos.loc[
        datos["recuperado"].str.lower().eq("fallecido"), "casos"
    ].sum()
)

letalidad = (fallecidos / total * 100) if total else 0

st.subheader("Indicadores principales")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Casos registrados", f"{total:,}")
c2.metric("Recuperados", f"{recuperados:,}")
c3.metric("Fallecimientos", f"{fallecidos:,}")
c4.metric("Tasa de letalidad", f"{letalidad:.2f}%")

st.caption(
    "La tasa de letalidad se calcula dividiendo los fallecimientos "
    "registrados entre el total de casos filtrados. Los registros "
    "sin información de recuperación se conservan en el total."
)

st.divider()

# Casos por municipio
izq, der = st.columns(2)

with izq:
    st.subheader("Casos por municipio")

    por_municipio = (
        datos.groupby("ciudad_municipio_nom", as_index=False)["casos"]
        .sum()
        .sort_values("casos", ascending=False)
        .head(10)
    )

    fig = px.bar(
        por_municipio,
        x="casos",
        y="ciudad_municipio_nom",
        orientation="h",
        text="casos",
        title="10 municipios con más casos",
        labels={
            "casos": "Casos",
            "ciudad_municipio_nom": "Municipio"
        }
    )
    fig.update_layout(yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig, width="stretch")

# Distribución por sexo
with der:
    st.subheader("Distribución por sexo")

    por_sexo = (
        datos.groupby("sexo", as_index=False)["casos"].sum()
    )

    fig = px.pie(
        por_sexo,
        names="sexo",
        values="casos",
        hole=0.4,
        title="Casos según sexo"
    )
    st.plotly_chart(fig, width="stretch")

# Evolución mensual
st.subheader("Evolución mensual de casos")

mensual = datos.dropna(subset=["fecha_diagnostico"]).copy()
mensual["Mes"] = (
    mensual["fecha_diagnostico"].dt.to_period("M").dt.to_timestamp()
)

mensual = (
    mensual.groupby("Mes", as_index=False)["casos"].sum()
)

fig = px.line(
    mensual,
    x="Mes",
    y="casos",
    markers=True,
    title="Casos por mes de diagnóstico",
    labels={"casos": "Casos", "Mes": "Mes"}
)
st.plotly_chart(fig, width="stretch")

# Edad y tiempo hasta diagnóstico
st.subheader("Edad promedio y días hasta el diagnóstico")

dispersion = datos.dropna(
    subset=["edad_promedio", "dias_diagnostico_promedio"]
).copy()

if not dispersion.empty:
    fig = px.scatter(
        dispersion,
        x="edad_promedio",
        y="dias_diagnostico_promedio",
        size="casos",
        hover_name="ciudad_municipio_nom",
        hover_data=["sexo", "estado", "casos"],
        opacity=0.6,
        title="Edad promedio frente a días hasta el diagnóstico",
        labels={
            "edad_promedio": "Edad promedio",
            "dias_diagnostico_promedio": "Días promedio",
            "casos": "Casos"
        }
    )
    st.plotly_chart(fig, width="stretch")
else:
    st.info("No hay suficientes datos para mostrar esta gráfica.")

# Tabla resumen
with st.expander("Consultar datos resumidos"):
    st.dataframe(datos, width="stretch")
    st.write(f"Casos representados con los filtros actuales: {total:,}")

st.caption(
    "Fuente: conjunto de datos COVID-19 de Antioquia, "
    "previamente procesado y agrupado para este dashboard."
)
