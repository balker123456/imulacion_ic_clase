import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import norm
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURACIÓN DE LA PLANILLA (BASE DE DATOS) ---
# Asegúrate de que la planilla tenga acceso de "Editor" para cualquier persona con el enlace.
URL_PLANILLA = "https://docs.google.com/spreadsheets/d/1ClW79PcyF7cUvkR_8H0aSZNlHiQWM_KU6LoXUTQMDEY/edit?usp=sharing"

# Crear la conexión
conn = st.connection("gsheets", type=GSheetsConnection)

# --- PARÁMETROS FIJOS (DEL PROFESOR) ---
MU_POBLACIONAL = 100.0
SIGMA_POBLACIONAL = 3.0
TAMANO_MUESTRA = 30
MIN_DATO_PERMITIDO = 90.0
MAX_DATO_PERMITIDO = 110.0

# --- FUNCIÓN DE CÁLCULO DE INTERVALO DE CONFIANZA ---
def calcular_ic(media_muestral, nc_porcentaje):
    nc = nc_porcentaje / 100.0
    probabilidad_acumulada = 1 - (1 - nc) / 2
    z_critico = norm.ppf(probabilidad_acumulada) 
    error_estandar = SIGMA_POBLACIONAL / np.sqrt(TAMANO_MUESTRA)
    margen_error = z_critico * error_estandar
    li = media_muestral - margen_error
    ls = media_muestral + margen_error
    captura = 'SÍ' if (li <= MU_POBLACIONAL <= ls) else 'NO'
    return margen_error, li, ls, captura

# --- INTERFAZ DE STREAMLIT ---
st.set_page_config(layout="wide", page_title="Simulación IC - Clase") 
st.title("📊 Simulación Interactiva: Intervalos de Confianza")
st.markdown("---")

# 1. Columna lateral de Parámetros
with st.sidebar:
    st.header("⚙️ Parámetros Fijos")
    st.info(f"**Media Poblacional (μ):** {MU_POBLACIONAL}")
    st.info(f"**Desviación Estándar (σ):** {SIGMA_POBLACIONAL}")
    st.info(f"**Tamaño de Muestra (n):** {TAMANO_MUESTRA}")
    
    nc_seleccionado = st.selectbox(
        "Nivel de Confianza (1 - α)",
        options=[90, 95, 99],
        index=0, 
        help="90% significa que esperamos que 1 de cada 10 intervalos falle."
    )

# 2. Área de Entrada de Datos del Estudiante
st.header("Entrada de Datos del Estudiante")
col_id, col_txt = st.columns([1, 3])

with col_id:
    id_estudiante = st.text_input("Tu Nombre / ID de Muestra:", key="id_input")

with col_txt:
    datos_input = st.text_area(
        "Pega los 30 datos de tu muestra (separados por comas o espacios):",
        height=100,
        key="datos_input"
    )

boton_enviar = st.button("Calcular IC y Enviar Resultados", type="primary")

# --- LÓGICA DE PROCESAMIENTO ---
if boton_enviar:
    if not id_estudiante or not datos_input:
        st.error("Por favor, ingresa tu ID y los datos.")
    else:
        try:
            datos_limpios = datos_input.replace(',', ' ').split()
            datos_numericos = [float(d) for d in datos_limpios]
            
            if len(datos_numericos) != TAMANO_MUESTRA:
                st.error(f"Se esperaba exactamente {TAMANO_MUESTRA} datos.")
            elif not all(MIN_DATO_PERMITIDO <= x <= MAX_DATO_PERMITIDO for x in datos_numericos):
                st.error(f"Error: Datos fuera de rango ({MIN_DATO_PERMITIDO} - {MAX_DATO_PERMITIDO}).")
            else:
                # Cálculos
                media_muestral = np.mean(datos_numericos)
                margen_error, li, ls, captura = calcular_ic(media_muestral, nc_seleccionado)

                # Mostrar Resultados Individuales
                st.success(f"Cálculo completado para {id_estudiante}")
                st.markdown(f"**Media (x̄):** `{media_muestral:.3f}` | **IC:** `{li:.3f}` a `{ls:.3f}` | **Captura:** **{captura}**")
                
                # Enviar a Google Sheets
                nuevo_resultado = pd.DataFrame([{
                    'ID_Estudiante': id_estudiante,
                    'Nivel_Confianza': f"{nc_seleccionado}%",
                    'Media_Muestral': media_muestral,
                    'Margen_Error': margen_error,
                    'LI': li,
                    'LS': ls,
                    'Captura_Mu': captura
                }])
                
                df_existente = conn.read(spreadsheet=URL_PLANILLA, ttl=0)
                df_actualizado = pd.concat([df_existente, nuevo_resultado], ignore_index=True)
                conn.update(spreadsheet=URL_PLANILLA, data=df_actualizado)
                st.balloons()
        
        except ValueError:
            st.error("Asegúrate de que todos los datos sean números válidos.")

# --- FASE III: VISUALIZACIÓN DE RESULTADOS ---
st.markdown("---")
st.header("📈 Resultados de la Clase (En Tiempo Real)")

if st.button('🔄 Actualizar Pizarra de la Clase'):
    st.cache_data.clear()
    st.rerun()

try:
    resultados_df = conn.read(spreadsheet=URL_PLANILLA, ttl=0)
    resultados_df = resultados_df.dropna(subset=['ID_Estudiante'])

    if resultados_df.empty:
        st.warning("Esperando los primeros resultados de la clase...")
    else:
        # Métricas
        conteo = resultados_df['Captura_Mu'].value_counts().reindex(['SÍ', 'NO'], fill_value=0)
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Muestras", len(resultados_df))
        c2.metric("Capturaron μ", f"{conteo['SÍ']}")
        c3.metric("Fuera de Rango", f"{conteo['NO']}", delta_color="inverse")

        # Gráfico 1: Histograma
        import plotly.express as px
        st.subheader("1. Distribución de Medias (Teorema Límite Central)")
        fig_hist = px.histogram(resultados_df, x='Media_Muestral', nbins=10, 
                               title='¿Cómo se agrupan las medias de los alumnos?',
                               color_discrete_sequence=['#636EFA'], opacity=0.7)
        fig_hist.add_vline(x=MU_POBLACIONAL, line_dash="dash", line_color="green", annotation_text="μ real")
        st.plotly_chart(fig_hist, use_container_width=True)

        # Gráfico 2: Cobertura
        import plotly.graph_objects as go
        st.subheader("2. Cobertura de Intervalos")
        resultados_df['ID_Muestra'] = range(1, len(resultados_df) + 1)
        fig_cob = go.Figure()

        for _, row in resultados_df.iterrows():
            color = '#00CC96' if row['Captura_Mu'] == 'SÍ' else '#EF553B'
            fig_cob.add_trace(go.Scatter(
                x=[row['LI'], row['LS']], y=[row['ID_Muestra'], row['ID_Muestra']],
                mode='lines+markers', line=dict(color=color, width=3), showlegend=False
            ))

        fig_cob.add_vline(x=MU_POBLACIONAL, line_width=2, line_dash="dash", line_color="green")
        fig_cob.update_layout(xaxis_title="Valor", yaxis_title="Estudiante", height=400)
        st.plotly_chart(fig_cob, use_container_width=True)

except Exception as e:
    st.error(f"Esperando conexión con la base de datos...")