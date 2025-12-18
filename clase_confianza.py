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

with st.sidebar:
    st.header("⚙️ Parámetros")
    st.info(f"μ: {MU_POBLACIONAL} | σ: {SIGMA_POBLACIONAL} | n: {TAMANO_MUESTRA}")
    nc_sel = st.selectbox("Nivel de Confianza", options=[90, 95, 99], index=0)

# Entrada de Datos
st.header("Entrada de Datos del Estudiante")
c1, c2 = st.columns([1, 3])

with c1:
    id_est = st.text_input("Tu Nombre:", placeholder="Ej: Juan Pérez")

with c2:
    txt_input = st.text_area("Pega tus 30 datos:", height=100, help="Separados por espacios o comas")
    datos_lista = txt_input.replace(',', ' ').split()
    st.caption(f"Cantidad detectada: {len(datos_lista)} datos.")

# BOTÓN SIEMPRE DISPONIBLE
btn_enviar = st.button("Enviar a Pizarra", type="primary")

if btn_enviar:
    # 1. VALIDADORES AL MOMENTO DE HACER CLIC
    if not id_est:
        st.error("❌ Error: Debes ingresar tu nombre.")
    elif len(datos_lista) != TAMANO_MUESTRA:
        st.error(f"❌ Error: Se requieren exactamente {TAMANO_MUESTRA} datos. Detectamos {len(datos_lista)}.")
    else:
        try:
            nums = [float(d) for d in datos_lista]
            # 2. VALIDADOR DE RANGO (90 - 110)
            if not all(MIN_VAL <= x <= MAX_VAL for x in nums):
                st.error(f"❌ Error: Hay datos fuera del rango permitido ({MIN_VAL} - {MAX_VAL}).")
            else:
                # Si todo está bien, procesamos y subimos
                med = np.mean(nums)
                me, li, ls, cap = calcular_ic(med, nc_sel)
                
                nueva_fila = pd.DataFrame([{
                    'ID_Estudiante': id_est, 
                    'Nivel_Confianza': f"{nc_sel}%",
                    'Media_Muestral': round(med, 3), 
                    'Margen_Error': round(me, 3),
                    'LI': round(li, 3), 
                    'LS': round(ls, 3), 
                    'Captura_Mu': cap
                }])
                
                # Escritura en la nube
                df_ex = conn.read(spreadsheet=URL_PLANILLA, ttl="1d") # Cache largo para evitar lentitud
                df_up = pd.concat([df_ex.dropna(how='all'), nueva_fila], ignore_index=True)
                conn.update(spreadsheet=URL_PLANILLA, data=df_up)
                
                st.success("✅ ¡Datos enviados con éxito!")
                st.balloons()
                st.rerun()
                
        except ValueError:
            st.error("❌ Error: Asegúrate de que todos los datos sean números válidos.")

# --- VISUALIZACIÓN ---
st.markdown("---")
st.header("📈 Pizarra de Resultados")

# Único punto de actualización manual
if st.button('🔄 Actualizar Pizarra'):
    st.cache_data.clear()
    st.rerun()

try:
    # Lectura con caché para que la app no se sienta lenta
    df = conn.read(spreadsheet=URL_PLANILLA, ttl="1d").dropna(subset=['ID_Estudiante'])
    
    if not df.empty:
        si = (df['Captura_Mu'] == 'SÍ').sum()
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Muestras", len(df))
        m2.metric("Capturaron μ", si)
        m3.metric("Fallaron", len(df) - si)

        # Gráfico de Intervalos
        df['Muestra'] = range(1, len(df) + 1)
        fig = go.Figure()
        for _, r in df.iterrows():
            col = '#00CC96' if r['Captura_Mu'] == 'SÍ' else '#EF553B'
            fig.add_trace(go.Scatter(
                x=[r['LI'], r['LS']], y=[r['Muestra'], r['Muestra']], 
                mode='lines+markers', line=dict(color=col, width=3),
                name=str(r['ID_Estudiante']), showlegend=False
            ))
        
        fig.add_vline(x=MU_POBLACIONAL, line_dash="dash", line_color="black", line_width=2)
        fig.update_layout(title="Intervalos de Confianza (Verde = Captura μ)", height=500)
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("📋 Registro de la Clase")
        st.dataframe(df.iloc[::-1], use_container_width=True, hide_index=True)
    else:
        st.info("No hay datos en la pizarra todavía.")
except Exception:
    st.warning("Conectando con la base de datos...")