import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import norm

# --- PARÁMETROS FIJOS (DEL PROFESOR) ---
# μ: Media poblacional secreta que intentamos capturar
MU_POBLACIONAL = 100.0
# σ: Desviación Estándar poblacional (conocida) que usaremos
SIGMA_POBLACIONAL = 3.0
# n: Tamaño de la muestra
TAMANO_MUESTRA = 30
# --- PARÁMETROS DE VALIDACIÓN (NUEVOS) ---
# Rango mínimo y máximo para los datos de la muestra (para evitar errores extremos)
MIN_DATO_PERMITIDO = 90.0
MAX_DATO_PERMITIDO = 110.0

# Columnas para el repositorio de resultados
COLUMNAS = ['ID_Estudiante', 'Nivel_Confianza', 'Media_Muestral', 
            'Margen_Error', 'LI', 'LS', 'Captura_Mu']

# Inicializa el repositorio de resultados en el estado de la sesión
if 'resultados_df' not in st.session_state:
    st.session_state.resultados_df = pd.DataFrame(columns=COLUMNAS)

# --- FUNCIÓN DE CÁLCULO DE INTERVALO DE CONFIANZA ---
def calcular_ic(media_muestral, nc_porcentaje):
    """Calcula el IC al Z con sigma conocido."""
    
    # 1. Convertir el nivel de confianza a decimal (ej: 95 -> 0.95)
    nc = nc_porcentaje / 100.0
    
    # 2. Calcular el valor crítico Z_alpha/2 (función INV.NORM.ESTAND)
    probabilidad_acumulada = 1 - (1 - nc) / 2
    z_critico = norm.ppf(probabilidad_acumulada) 
    
    # 3. Calcular el error estándar
    error_estandar = SIGMA_POBLACIONAL / np.sqrt(TAMANO_MUESTRA)
    
    # 4. Calcular el Margen de Error (E)
    margen_error = z_critico * error_estandar
    
    # 5. Calcular los límites del intervalo
    li = media_muestral - margen_error
    ls = media_muestral + margen_error
    
    # 6. Verificar si captura la media poblacional (μ=100)
    captura = 'SÍ' if (li <= MU_POBLACIONAL <= ls) else 'NO'
    
    return margen_error, li, ls, captura

# --- INTERFAZ DE STREAMLIT ---

st.set_page_config(layout="wide") 
st.title("📊 Simulación Interactiva: Intervalos de Confianza")
st.markdown("---")

# 1. Columna lateral de Parámetros
with st.sidebar:
    st.header("⚙️ Parámetros Fijos")
    st.info(f"**Media Poblacional (μ):** {MU_POBLACIONAL}")
    st.info(f"**Desviación Estándar (σ):** {SIGMA_POBLACIONAL}")
    st.info(f"**Tamaño de Muestra (n):** {TAMANO_MUESTRA}")
    
    # Selector de Nivel de Confianza
    nc_seleccionado = st.selectbox(
        "Nivel de Confianza (1 - α)",
        options=[90, 95, 99],
        index=1, 
        help="El porcentaje de veces que el método debe capturar la media poblacional (μ)."
    )

# 2. Área de Entrada de Datos del Estudiante
st.header("Entrada de Datos del Estudiante")
col1, col2 = st.columns([1, 3])

with col1:
    id_estudiante = st.text_input("Ingresa tu Nombre / ID de Muestra:", key="id_input")

with col2:
    datos_input = st.text_area(
        "Pega aquí los 30 datos de tu muestra (separados por comas o espacios):",
        height=100,
        key="datos_input"
    )

# 3. Botón de Ejecución del Cálculo
boton_enviar = st.button("Calcular IC y Enviar Resultados", type="primary")

# --- LÓGICA DE PROCESAMIENTO AL PRESIONAR EL BOTÓN ---

if boton_enviar:
    # a. Validación y Limpieza de Datos
    if not id_estudiante or not datos_input:
        st.error("Por favor, ingresa tu ID/Nombre y los datos de la muestra.")
    else:
        try:
            datos_limpios = datos_input.replace(',', ' ').split()
            datos_numericos = [float(d) for d in datos_limpios]
            
            # Validación de tamaño
            if len(datos_numericos) != TAMANO_MUESTRA:
                st.error(f"Se esperaba exactamente {TAMANO_MUESTRA} datos, pero ingresaste {len(datos_numericos)}.")
            else:
                # --- LÓGICA DE PROCESAMIENTO AL PRESIONAR EL BOTÓN ---

if boton_enviar:
    # a. Validación y Limpieza de Datos
    if not id_estudiante or not datos_input:
        st.error("Por favor, ingresa tu ID/Nombre y los datos de la muestra.")
    else:
        try:
            datos_limpios = datos_input.replace(',', ' ').split()
            datos_numericos = [float(d) for d in datos_limpios]
            
            # Validación de tamaño
            if len(datos_numericos) != TAMANO_MUESTRA:
                st.error(f"Se esperaba exactamente {TAMANO_MUESTRA} datos, pero ingresaste {len(datos_numericos)}.")
            
            # >>>>>>> NUEVA VALIDACIÓN: RANGO DE DATOS <<<<<<<<
            elif not all(MIN_DATO_PERMITIDO <= x <= MAX_DATO_PERMITIDO for x in datos_numericos):
                st.error(f"ERROR: Al menos un dato está fuera del rango permitido. Los datos deben estar entre {MIN_DATO_PERMITIDO} y {MAX_DATO_PERMITIDO}.")
            # >>>>>>> FIN NUEVA VALIDACIÓN <<<<<<<<
            
            else:
                # b. Cálculos
                media_muestral = np.mean(datos_numericos)
                margen_error, li, ls, captura = calcular_ic(media_muestral, nc_seleccionado)

                # c. Mostrar Resultados Individuales
                st.success(f"Cálculo completado para {id_estudiante} al {nc_seleccionado}%.")
                st.markdown(f"**Media Muestral (x̄):** `{media_muestral:.3f}`")
                st.markdown(f"**Margen de Error (E):** `{margen_error:.3f}`")
                st.markdown(f"**Intervalo de Confianza:** `{li:.3f}` a `{ls:.3f}`")
                st.markdown(f"**¿Captura μ={MU_POBLACIONAL}?** **{captura}**")
                
                # d. Almacenar el resultado en el repositorio
                # ... (El código de almacenamiento sigue igual) ...
        
        except ValueError:
            st.error("Asegúrate de que todos los datos ingresados sean números válidos.")

            # --- VISUALIZACIÓN DE RESULTADOS ---
st.markdown("---")
st.header("📈 Resultados de la Clase (Repositorio)")

resultados_df = st.session_state.resultados_df

if resultados_df.empty:
    st.warning("Aún no hay resultados para mostrar. ¡Ingresa tu primera muestra!")
else:
    # 1. Mostrar la tabla de resultados
    st.subheader("Tabla de Medias e Intervalos de la Clase")
    st.dataframe(resultados_df, use_container_width=True)

    # 2. Resumen de Éxito vs. Fracaso
    conteo = resultados_df['Captura_Mu'].value_counts().reindex(['SÍ', 'NO'], fill_value=0)
    
    col_conteo_1, col_conteo_2 = st.columns(2)
    with col_conteo_1:
        st.metric(
            label="Intervalos Exitosos (Capturan μ)",
            value=f"{conteo['SÍ']} de {len(resultados_df)}"
        )
    with col_conteo_2:
        # Calcular el porcentaje de error (alpha)
        porcentaje_error = (conteo['NO'] / len(resultados_df)) * 100
        st.metric(
            label="Intervalos Fallidos (Tasa de Error)",
            value=f"{conteo['NO']} de {len(resultados_df)}",
            delta=f"{porcentaje_error:.1f}% de α (Esperado 5%)"
        )


    # 3. Generación del Gráfico de Cobertura con Plotly
    import plotly.graph_objects as go
    
    # Crear la columna de 'ID_Muestra' para el eje Y
    resultados_df['ID_Muestra'] = resultados_df.index + 1
    
    # Columna para pintar los fallos de rojo
    color_map = {'SÍ': 'blue', 'NO': 'red'}
    
    fig = go.Figure()
    
    # A. Agregar los intervalos de confianza (lineas horizontales)
    for index, row in resultados_df.iterrows():
        fig.add_trace(go.Scatter(
            x=[row['LI'], row['LS']],
            y=[row['ID_Muestra'], row['ID_Muestra']],
            mode='lines',
            line=dict(color=color_map[row['Captura_Mu']], width=3),
            name=f"IC Muestra {row['ID_Muestra']}",
            hoverinfo='text',
            hovertext=f"ID: {row['ID_Estudiante']}<br>IC: [{row['LI']:.3f}, {row['LS']:.3f}]<br>Media: {row['Media_Muestral']:.3f}<br>Captura μ: {row['Captura_Mu']}",
            showlegend=False
        ))
        
    # B. Agregar la línea vertical de la media poblacional (μ)
    fig.add_shape(type="line",
        x0=MU_POBLACIONAL, y0=0, x1=MU_POBLACIONAL, y1=len(resultados_df) + 1,
        line=dict(color="green", width=2, dash="dash"),
        name=f"μ={MU_POBLACIONAL}"
    )
    
    # C. Configuración del diseño del gráfico
    fig.update_layout(
        title="Visualización de Intervalos de Confianza (95% Cobertura)",
        xaxis_title=f"Valor de la Media (μ={MU_POBLACIONAL})",
        yaxis_title="Muestra",
        yaxis=dict(
            tickmode='array',
            tickvals=resultados_df['ID_Muestra'],
            ticktext=[f"Muestra {i}" for i in resultados_df['ID_Muestra']],
            autorange="reversed" 
        ),
        height=min(800, 100 + 40 * len(resultados_df)) 
    )
    
    # Mostrar el gráfico en Streamlit
    st.plotly_chart(fig, use_container_width=True)