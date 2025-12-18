import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import norm
from streamlit_gsheets import GSheetsConnection
import plotly.graph_objects as go

# --- CONFIGURACIÓN ---
URL_PLANILLA = "https://docs.google.com/spreadsheets/d/1ClW79PcyF7cUvkR_8H0aSZNlHiQWM_KU6LoXUTQMDEY/edit?usp=sharing"
conn = st.connection("gsheets", type=GSheetsConnection)

MU_POBLACIONAL = 100.0
SIGMA_POBLACIONAL = 3.0
TAMANO_MUESTRA = 30
MIN_VAL, MAX_VAL = 90.0, 110.0

def calcular_ic(media, nc_porcentaje):
    nc = nc_porcentaje / 100.0
    z = norm.ppf(1 - (1 - nc) / 2)
    ee = SIGMA_POBLACIONAL / np.sqrt(TAMANO_MUESTRA)
    me = z * ee
    li, ls = media - me, media + me
    captura = 'SÍ' if (li <= MU_POBLACIONAL <= ls) else 'NO'
    return me, li, ls, captura

# --- INTERFAZ ---
st.set_page_config(layout="wide", page_title="Simulación IC")
st.title("📊 Simulación: Intervalos de Confianza")

# Botón de refrescar manual (Fase III solicitada)
if st.button('🔄 Actualizar Pizarra y Datos'):
    st.cache_data.clear()
    st.rerun()

with st.sidebar:
    st.header("⚙️ Parámetros")
    st.info(f"μ: {MU_POBLACIONAL} | σ: {SIGMA_POBLACIONAL} | n: {TAMANO_MUESTRA}")
    # Ajustado a 90% por defecto según tu instrucción
    nc_sel = st.selectbox("Nivel de Confianza", options=[90, 95, 99], index=0)

# Entrada de Datos
st.header("Entrada de Datos del Estudiante")
c1, c2 = st.columns([1, 3])

with c1:
    id_est = st.text_input("Tu Nombre:", placeholder="Ej: Juan Pérez")

with c2:
    txt_input = st.text_area("Pega tus 30 datos:", height=100)
    
    # Contador dinámico
    datos_lista = txt_input.replace(',', ' ').split()
    n_actual = len(datos_lista)
    
    # Validación de Rango (90-110)
    datos_fuera_de_rango = False
    try:
        nums_temp = [float(d) for d in datos_lista]
        if any(x < MIN_VAL or x > MAX_VAL for x in nums_temp):
            datos_fuera_de_rango = True
    except ValueError:
        pass

    if n_actual > 0:
        if datos_fuera_de_rango:
            st.error(f"❌ ERROR: Tienes datos fuera del rango permitido ({MIN_VAL} - {MAX_VAL}).")
            puede_enviar = False
        elif n_actual == TAMANO_MUESTRA:
            st.success(f"✅ ¡Listo! Tienes los {TAMANO_MUESTRA} datos correctos.")
            puede_enviar = True
        else:
            st.info(f"🔢 Llevas {n_actual} de {TAMANO_MUESTRA} datos...")
            puede_enviar = False
    else:
        st.write("Esperando datos...")
        puede_enviar = False

# El botón AHORA SÍ bloquea si los datos están fuera de rango
btn = st.button("Enviar a Pizarra", type="primary", disabled=not (puede_enviar and id_est))

if btn:
    try:
        nums = [float(d) for d in datos_lista]
        # Doble validación de seguridad antes de subir a la nube
        if all(MIN_VAL <= x <= MAX_VAL for x in nums):
            med = np.mean(nums)
            me, li, ls, cap = calcular_ic(med, nc_sel)
            
            nueva_fila = pd.DataFrame([{
                'ID_Estudiante': id_est, 'Nivel_Confianza': f"{nc_sel}%",
                'Media_Muestral': round(med, 3), 'Margen_Error': round(me, 3),
                'LI': round(li, 3), 'LS': round(ls, 3), 'Captura_Mu': cap
            }])
            
            df_ex = conn.read(spreadsheet=URL_PLANILLA, ttl=0)
            df_up = pd.concat([df_ex.dropna(how='all'), nueva_fila], ignore_index=True)
            conn.update(spreadsheet=URL_PLANILLA, data=df_up)
            st.balloons()
            st.rerun()
        else:
            st.error("No se pudo enviar: Hay valores fuera de rango.")
    except ValueError:
        st.error("Error en el formato de los números.")

# --- VISUALIZACIÓN ---
st.markdown("---")
try:
    df = conn.read(spreadsheet=URL_PLANILLA, ttl=0).dropna(subset=['ID_Estudiante'])
    if not df.empty:
        # Métricas
        si = (df['Captura_Mu'] == 'SÍ').sum()
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Muestras", len(df))
        m2.metric("Capturaron μ", si)
        m3.metric("Fallaron", len(df) - si)

        # Gráfico Único: Cobertura de Intervalos (Se eliminó el histograma)
        st.subheader("Intervalos de Confianza vs μ Real")
        df['Muestra'] = range(1, len(df) + 1)
        fig2 = go.Figure()
        for _, r in df.iterrows():
            col = '#00CC96' if r['Captura_Mu'] == 'SÍ' else '#EF553B' # Verde / Rojo
            fig2.add_trace(go.Scatter(
                x=[r['LI'], r['LS']], 
                y=[r['Muestra'], r['Muestra']], 
                mode='lines+markers', 
                line=dict(color=col, width=3),
                name=str(r['ID_Estudiante']),
                showlegend=False
            ))
        
        # Línea de la Media Poblacional
        fig2.add_vline(x=MU_POBLACIONAL, line_dash="dash", line_color="black", line_width=2,
                      annotation_text="μ REAL", annotation_position="top")
        
        fig2.update_layout(xaxis_title="Valor", yaxis_title="ID Muestra", height=500)
        st.plotly_chart(fig2, use_container_width=True)

        st.subheader("📋 Registro de la Clase (Últimos ingresos primero)")
        st.dataframe(df.iloc[::-1], use_container_width=True, hide_index=True)
except Exception:
    st.info("Conectando con la base de datos...")