import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import norm
from streamlit_gsheets import GSheetsConnection
import plotly.express as px
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

with st.sidebar:
    st.header("⚙️ Parámetros")
    st.info(f"μ: {MU_POBLACIONAL} | σ: {SIGMA_POBLACIONAL} | n: {TAMANO_MUESTRA}")
    nc_sel = st.selectbox("Nivel de Confianza", options=[90, 95, 99], index=1)

# Entrada de Datos
st.header("Entrada de Datos del Estudiante")
c1, c2 = st.columns([1, 3])

with c1:
    id_est = st.text_input("Tu Nombre:", placeholder="Ej: Profe de Mate")

with c2:
    txt_input = st.text_area("Pega tus 30 datos:", height=100)
    
    # Contador dinámico
    datos_lista = txt_input.replace(',', ' ').split()
    n_actual = len(datos_lista)
    
    if n_actual > 0:
        if n_actual == TAMANO_MUESTRA:
            st.success(f"✅ ¡Listo! Tienes los {TAMANO_MUESTRA} datos.")
            puede_enviar = True
        elif n_actual > TAMANO_MUESTRA:
            st.error(f"⚠️ Tienes {n_actual} datos. ¡Sobran {n_actual - TAMANO_MUESTRA}!")
            puede_enviar = False
        else:
            st.info(f"🔢 Llevas {n_actual} de {TAMANO_MUESTRA} datos...")
            puede_enviar = False
    else:
        st.write("Esperando datos...")
        puede_enviar = False

btn = st.button("Enviar a Pizarra", type="primary", disabled=not (puede_enviar and id_est))

if btn:
    try:
        nums = [float(d) for d in datos_lista]
        if not all(MIN_VAL <= x <= MAX_VAL for x in nums):
            st.error("Hay datos fuera de rango (90-110).")
        else:
            med = np.mean(nums)
            me, li, ls, cap = calcular_ic(med, nc_sel)
            
            # Guardar
            nueva_fila = pd.DataFrame([{
                'ID_Estudiante': id_est, 'Nivel_Confianza': f"{nc_sel}%",
                'Media_Muestral': round(med, 3), 'Margen_Error': round(me, 3),
                'LI': round(li, 3), 'LS': round(ls, 3), 'Captura_Mu': cap
            }])
            
            df_ex = conn.read(spreadsheet=URL_PLANILLA, ttl=0)
            # [cite_start]Manejo de Futurewarning para concatenación [cite: 7, 20]
            df_up = pd.concat([df_ex.dropna(how='all'), nueva_fila], ignore_index=True)
            conn.update(spreadsheet=URL_PLANILLA, data=df_up)
            st.balloons()
            st.rerun()
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

        # Gráficos
        g1, g2 = st.columns(2)
        with g1:
            fig1 = px.histogram(df, x='Media_Muestral', title="Distribución de Medias", nbins=10)
            fig1.add_vline(x=MU_POBLACIONAL, line_dash="dash", line_color="red")
            st.plotly_chart(fig1, use_container_width=True)
        with g2:
            df['Muestra'] = range(1, len(df) + 1)
            fig2 = go.Figure()
            for _, r in df.iterrows():
                col = 'green' if r['Captura_Mu'] == 'SÍ' else 'red'
                fig2.add_trace(go.Scatter(x=[r['LI'], r['LS']], y=[r['Muestra'], r['Muestra']], 
                                         mode='lines+markers', line=dict(color=col), showlegend=False))
            fig2.add_vline(x=MU_POBLACIONAL, line_dash="dash", line_color="black")
            fig2.update_layout(title="Intervalos vs μ Real", height=400)
            st.plotly_chart(fig2, use_container_width=True)

        st.subheader("📋 Registro de la Clase")
        st.dataframe(df.iloc[::-1], use_container_width=True, hide_index=True)
except Exception:
    st.warning("Conectando con la pizarra...")