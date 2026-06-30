import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import timedelta
import re
import os
import requests
import json

# 1. CONFIGURACIÓN
st.set_page_config(page_title="Tablero Mensajería - Sergem", page_icon="📊", layout="wide", initial_sidebar_state="expanded")
st.markdown('<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">', unsafe_allow_html=True)

# URL
URL_APPSCRIPT = "https://script.google.com/macros/s/AKfycbwnn_iCYyaASqNXRN5zTA7Ey_-PedPJCasBg3aVpUpwI0Cwtx6l90PbJK9x1JaQFrJGJw/exec"

def cargar_css(archivo):
    if os.path.exists(archivo):
        with open(archivo, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

cargar_css("styles.css")

if 'pagina_actual' not in st.session_state:
    st.session_state['pagina_actual'] = 'Inicio'

def cambiar_pagina(nombre_pagina):
    st.session_state['pagina_actual'] = nombre_pagina

def convertir_a_minutos(texto):
    if pd.isna(texto) or texto == '': return 0
    t = str(texto).lower()
    mins = 0
    dias = re.search(r'(\d+)\s*d', t)
    horas = re.search(r'(\d+)\s*h', t)
    m = re.search(r'(\d+)\s*min', t)
    if dias: mins += int(dias.group(1)) * 1440 
    if horas: mins += int(horas.group(1)) * 60 
    if m: mins += int(m.group(1))
    return mins

def extraer_ciudad(texto):
    if pd.isna(texto): return 'Sin Ciudad'
    t = str(texto).upper()
    ciudades = ['BOGOTA', 'CALI', 'BARRANQUILLA', 'CARTAGENA', 'SANTA MARTA', 'MEDELLIN', 'IBAGUE']
    for c in ciudades:
        if c in t: return c.capitalize()
    return 'Otra'

@st.cache_data(ttl=300) # Se actualiza cada 5 minutos
def obtener_datos_bd():
    try:
        req = requests.get(URL_APPSCRIPT)
        if req.status_code == 200:
            datos = req.json()
            if datos: return pd.DataFrame(datos)
    except: pass
    return pd.DataFrame()

# ==========================================
# MENSAJEROS Y CONFIGURACIÓN (Panel Lateral)
# ==========================================
with st.sidebar:
    st.markdown("### ⚙️ Configuración Operativa")
    st.write("Ajuste el número de mensajeros para el cálculo del promedio:")
    
    mensajeros_config = {
        'Bogota': st.number_input("Bogotá", value=7.0, step=0.5),
        'Barranquilla': st.number_input("Barranquilla", value=3.0, step=0.5),
        'Cali': st.number_input("Cali", value=4.0, step=0.5),
        'Medellin': st.number_input("Medellín", value=1.0, step=0.5),
        'Santa Marta': st.number_input("Santa Marta", value=1.0, step=0.5),
        'Cartagena': st.number_input("Cartagena", value=1.0, step=0.5),
        'Ibague': st.number_input("Ibagué", value=0.5, step=0.5)
    }
    
    st.markdown("---")
    st.markdown("### 📥 Actualizar Base de Datos")
    archivo_subido = st.file_uploader("Subir nuevo ORIGINAL WIP", type=['xlsx', 'xls', 'csv'])
    if archivo_subido is not None and st.button("Procesar y Subir"):
        with st.spinner("Subiendo y actualizando datos..."):
            if archivo_subido.name.endswith('.csv'): df_nuevo = pd.read_csv(archivo_subido, sep=';', encoding='utf-8')
            else: df_nuevo = pd.read_excel(archivo_subido)
            
            df_nuevo.columns = df_nuevo.columns.str.strip().str.upper()
            df_nuevo['FECHA DE CREACION'] = df_nuevo['FECHA DE CREACION'].astype(str)
            
            payload = df_nuevo.to_dict(orient='records')
            requests.post(URL_APPSCRIPT, json=payload)
            st.cache_data.clear()
            st.success("¡Base de datos actualizada! Los duplicados fueron eliminados automáticamente.")
            st.rerun()

# 4. CARGA DE DATOS PRINCIPAL
df = obtener_datos_bd()
df_filtrado = pd.DataFrame() 

if not df.empty:
    df['FECHA DE CREACION'] = pd.to_datetime(df['FECHA DE CREACION'], errors='coerce')
    df = df.dropna(subset=['FECHA DE CREACION'])
    
    meses_es = {1:'Enero', 2:'Febrero', 3:'Marzo', 4:'Abril', 5:'Mayo', 6:'Junio', 7:'Julio', 8:'Agosto', 9:'Septiembre', 10:'Octubre', 11:'Noviembre', 12:'Diciembre'}
    df['AÑO'] = df['FECHA DE CREACION'].dt.year.astype(str)
    df['MES_NUM'] = df['FECHA DE CREACION'].dt.month
    df['MES_NOMBRE'] = df['MES_NUM'].map(meses_es)
    
    dias_esp = {'Monday':'Lunes', 'Tuesday':'Martes', 'Wednesday':'Miércoles', 'Thursday':'Jueves', 'Friday':'Viernes', 'Saturday':'Sábado', 'Sunday':'Domingo'}
    orden_dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
    df['DIA_SEMANA'] = pd.Categorical(df['FECHA DE CREACION'].dt.day_name().map(dias_esp), categories=orden_dias, ordered=True)
    
    if 'TIEMPO EJECUCIÓN REAL' in df.columns:
        df['TIEMPO_MINUTOS'] = df['TIEMPO EJECUCIÓN REAL'].apply(convertir_a_minutos)
        df['TIEMPO_HORAS'] = df['TIEMPO_MINUTOS'] / 60 

    if 'TIPO DE SERVICIO' in df.columns:
        df['CIUDAD_REAL'] = df['TIPO DE SERVICIO'].apply(extraer_ciudad)

if st.session_state['pagina_actual'] == 'Inicio':
    st.markdown("<br><br>", unsafe_allow_html=True)
    col_izq, col_espacio, col_der = st.columns([1.2, 0.2, 1.5])
    
    with col_izq:
        st.markdown("""
        <div class="tarjeta-roja">
            <h2 style="text-align: center;">SERGEM MENSAJERÍA</h2>
            <hr style="border-top: 2px solid white; opacity: 0.5;">
            <h1 style="font-size: 50px;">Bienvenido (a)</h1>
            <p style="font-size: 18px; line-height: 1.6;">El aplicativo ya está conectado a su base de datos. Los indicadores están listos para visualizarse.</p>
        </div>
        """, unsafe_allow_html=True)
        
    with col_der:
        st.markdown("<h2 style='text-align: center;'>Menú Principal</h2><br>", unsafe_allow_html=True)
        if df.empty:
            st.warning("⚠️ La base de datos está vacía. Use el panel lateral izquierdo para subir el primer archivo WIP.")
        else:
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                st.button("📊 Tablero General", on_click=cambiar_pagina, args=('Tablero',))
                st.button("📝 Solicitudes", on_click=cambiar_pagina, args=('Solicitudes',))
            with col_btn2:
                st.button("⏱️ Medición de Tiempos", on_click=cambiar_pagina, args=('Tiempo',))
                st.button("📈 Participación", on_click=cambiar_pagina, args=('Participacion',))

elif not df.empty and st.session_state['pagina_actual'] != 'Inicio':
    
    # FILTROS SUPERIORES
    st.button("🏠 Volver al Menú Principal", on_click=cambiar_pagina, args=('Inicio',))
    st.markdown("<div style='background-color: #1D3557; padding: 15px; border-radius: 8px;'><h3 style='color: white !important; margin:0;'>Filtros Globales de Control</h3></div><br>", unsafe_allow_html=True)
    
    col_f0, col_f1, col_f2, col_f3, col_f4 = st.columns(5)
    
    with col_f0:
        años = sorted(df['AÑO'].dropna().unique().tolist())
        ano_sel = st.multiselect("Año", años, default=años)
    with col_f1:
        meses_disp = df[['MES_NUM', 'MES_NOMBRE']].drop_duplicates().sort_values('MES_NUM')['MES_NOMBRE'].tolist()
        mes_sel = st.multiselect("Mes", meses_disp, placeholder="Selección múltiple")
    with col_f2:
        ciudades = sorted(df['CIUDAD_REAL'].dropna().unique().tolist())
        ciudad_sel = st.multiselect("Ciudad / Sede", ciudades, placeholder="Todas")
    with col_f3:
        centros = sorted(df['CENTRO DE COSTOS'].dropna().astype(str).unique().tolist()) if 'CENTRO DE COSTOS' in df.columns else []
        centro_sel = st.multiselect("Centro de Costos", centros, placeholder="Todas")
    with col_f4:
        tramites = sorted(df['TRAMITE'].dropna().unique().tolist()) if 'TRAMITE' in df.columns else []
        tramite_sel = st.multiselect("Trámite", tramites, placeholder="Todas")

    # APLICAR FILTROS
    df_filtrado = df.copy()
    if ano_sel: df_filtrado = df_filtrado[df_filtrado['AÑO'].isin(ano_sel)]
    if mes_sel: df_filtrado = df_filtrado[df_filtrado['MES_NOMBRE'].isin(mes_sel)]
    if ciudad_sel: df_filtrado = df_filtrado[df_filtrado['CIUDAD_REAL'].isin(ciudad_sel)]
    if centro_sel: df_filtrado = df_filtrado[df_filtrado['CENTRO DE COSTOS'].astype(str).isin(centro_sel)]
    if tramite_sel: df_filtrado = df_filtrado[df_filtrado['TRAMITE'].isin(tramite_sel)]

    paleta_datos = ['#1D3557', '#457B9D', '#A8DADC', '#C1121F', '#F4A261', '#2A9D8F', '#E9C46A']

    # ==========================================
    # VISTA 1: TABLERO GENERAL (INDICADORES)
    # ==========================================
    if st.session_state['pagina_actual'] == 'Tablero':
        total_solicitudes = len(df_filtrado)
        dias_habiles = 1
        if 'FECHA DE CREACION' in df_filtrado.columns and total_solicitudes > 0:
            fecha_min = df_filtrado['FECHA DE CREACION'].min().date()
            fecha_max = df_filtrado['FECHA DE CREACION'].max().date()
            dias_habiles = np.busday_count(fecha_min, fecha_max + timedelta(days=1), weekmask='1111110')
            if dias_habiles == 0: dias_habiles = 1
        
        # CÁLCULO MATEMÁTICO EXACTO DE DOÑA YESENIA
        ciudades_en_pantalla = df_filtrado['CIUDAD_REAL'].unique()
        mensajeros_activos = sum([mensajeros_config.get(c, 0) for c in ciudades_en_pantalla])
        if mensajeros_activos == 0: mensajeros_activos = 1
        
        promedio_diario = total_solicitudes / dias_habiles / mensajeros_activos
        
        eficacia = 0
        if 'ESTADO' in df_filtrado.columns and total_solicitudes > 0:
            fallidos = df_filtrado['ESTADO'].str.contains('Fallido', case=False, na=False).sum()
            eficacia = ((total_solicitudes - fallidos) / total_solicitudes) * 100

        st.markdown("<hr>", unsafe_allow_html=True)
        col_kpis, col_graficos = st.columns([1.5, 5])
        
        with col_kpis:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">🛵 Solicitudes Totales</div>
                <div class="kpi-value">{total_solicitudes:,}</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-title">📈 Vueltas / Mensajero / Día</div>
                <div class="kpi-value">{promedio_diario:.1f}</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-title">✅ Efectividad Operativa</div>
                <div class="kpi-value">{eficacia:.1f}%</div>
            </div>
            """, unsafe_allow_html=True)

        with col_graficos:
            st.markdown("<b>Solicitudes por Fecha y Ciudad</b>", unsafe_allow_html=True)
            res_mes_ciudad = df_filtrado.groupby(['MES_NOMBRE', 'CIUDAD_REAL']).size().reset_index(name='Total')
            fig_combo = px.bar(res_mes_ciudad, x='MES_NOMBRE', y='Total', color='CIUDAD_REAL', color_discrete_sequence=paleta_datos)
            fig_combo.update_layout(margin=dict(t=10, b=10, l=10, r=10), plot_bgcolor='white', paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_combo, use_container_width=True)

    # ==========================================
    # VISTA 2: MEDICIÓN DE TIEMPOS
    # ==========================================
    elif st.session_state['pagina_actual'] == 'Tiempo':
        st.title("⏱️ Análisis Gerencial de Tiempos Operativos")
        if 'TIEMPO_HORAS' in df_filtrado.columns and 'TRAMITE' in df_filtrado.columns:
            col_t1, col_t2 = st.columns(2)
            with col_t1:
                st.markdown("<b>Horas Totales Invertidas por Tipo de Gestión</b>", unsafe_allow_html=True)
                res_tiempo = df_filtrado.groupby('TRAMITE')['TIEMPO_HORAS'].sum().reset_index().sort_values(by='TIEMPO_HORAS', ascending=True).tail(10)
                fig_tramite = px.bar(res_tiempo, x='TIEMPO_HORAS', y='TRAMITE', orientation='h', text=res_tiempo['TIEMPO_HORAS'].apply(lambda x: f"{x:.0f} h"), color='TIEMPO_HORAS', color_continuous_scale='Blues')
                st.plotly_chart(fig_tramite, use_container_width=True)
            
            with col_t2:
                st.markdown("<b>Evolución del Tiempo Promedio (Horas) por Sede</b>", unsafe_allow_html=True)
                tendencia = df_filtrado.groupby(['MES_NOMBRE', 'CIUDAD_REAL'])['TIEMPO_HORAS'].mean().reset_index()
                fig_tend = px.line(tendencia, x='MES_NOMBRE', y='TIEMPO_HORAS', color='CIUDAD_REAL', markers=True, color_discrete_sequence=paleta_datos)
                st.plotly_chart(fig_tend, use_container_width=True)

    # ==========================================
    # VISTA 3: SOLICITUDES
    # ==========================================
    elif st.session_state['pagina_actual'] == 'Solicitudes':
        st.title("📝 Análisis Detallado de Volúmenes")
        col_graf_s1, col_graf_s2 = st.columns(2)
        with col_graf_s1:
            st.markdown("<b>Crecimiento Mensual de Solicitudes</b>", unsafe_allow_html=True)
            res_mes = df_filtrado.groupby('MES_NOMBRE').size().reset_index(name='Cantidad')
            fig_mes = px.area(res_mes, x='MES_NOMBRE', y='Cantidad', color_discrete_sequence=['#457B9D'])
            st.plotly_chart(fig_mes, use_container_width=True)
            
        with col_graf_s2:
            st.markdown("<b>Distribución Absoluta de Servicios por Sede</b>", unsafe_allow_html=True)
            res_un = df_filtrado.groupby('CIUDAD_REAL').size().reset_index(name='Solicitudes').sort_values(by='Solicitudes', ascending=False)
            fig_un = px.bar(res_un, x='CIUDAD_REAL', y='Solicitudes', color='CIUDAD_REAL', color_discrete_sequence=paleta_datos)
            fig_un.update_layout(showlegend=False)
            st.plotly_chart(fig_un, use_container_width=True)

    # ==========================================
    # VISTA 4: PARTICIPACIÓN
    # ==========================================
    elif st.session_state['pagina_actual'] == 'Participacion':
        st.title("📈 Análisis de Cuotas de Participación")
        col_p1, col_p2 = st.columns(2)
        
        with col_p1:
            st.markdown("<b>Participación Porcentual por Sede</b>", unsafe_allow_html=True)
            res_part_un = df_filtrado['CIUDAD_REAL'].value_counts().reset_index()
            res_part_un.columns = ['Sede', 'Total']
            fig_part_un = px.pie(res_part_un, values='Total', names='Sede', hole=0.4, color_discrete_sequence=paleta_datos)
            st.plotly_chart(fig_part_un, use_container_width=True)
            
        with col_p2:
            st.markdown("<b>Participación por Centro de Costos</b>", unsafe_allow_html=True)
            if 'CENTRO DE COSTOS' in df_filtrado.columns:
                res_part_cc = df_filtrado.groupby('CENTRO DE COSTOS').size().reset_index(name='Total')
                fig_part_tree = px.treemap(res_part_cc, path=['CENTRO DE COSTOS'], values='Total', color='Total', color_continuous_scale='Blues')
                st.plotly_chart(fig_part_tree, use_container_width=True)
