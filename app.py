import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import timedelta
import re
import os
import base64
import requests
import json
import time

# 1. CONFIGURACIÓN DE LA PÁGINA
st.set_page_config(
    page_title="Tablero Mensajería - Sergem", 
    page_icon="sergemLogo.ico", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# 2. OCULTAR INTERFAZ POR DEFECTO Y APLICAR ESTILOS
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
[data-testid="stAppHeader"] {display: none !important;}
div[data-testid="stToolbar"] { visibility: hidden !important; display: none !important; }
.stAppDeployButton {display: none !important;}
header {display: none !important;}
.block-container {padding-top: 2rem !important;}
</style>
""", unsafe_allow_html=True)

st.markdown('<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">', unsafe_allow_html=True)

def cargar_css(archivo):
    if os.path.exists(archivo):
        with open(archivo, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

cargar_css("styles.css")

# 3. VARIABLES Y FUNCIONES BASE
URL_APPSCRIPT = "https://script.google.com/macros/s/AKfycbwnn_iCYyaASqNXRN5zTA7Ey_-PedPJCasBg3aVpUpwI0Cwtx6l90PbJK9x1JaQFrJGJw/exec"

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

# ==========================================
# 4. PROCESAMIENTO EN CACHÉ
# ==========================================
@st.cache_data(ttl=300, show_spinner=False)
def obtener_y_procesar_datos():
    try:
        req = requests.get(URL_APPSCRIPT, timeout=60)
        if req.status_code == 200:
            datos = req.json()
            if datos and len(datos) > 0:
                df = pd.DataFrame(datos)
                
                df.columns = df.columns.str.strip().str.upper()
                
                if 'FECHA DE CREACION' in df.columns:
                    df['FECHA DE CREACION'] = pd.to_datetime(df['FECHA DE CREACION'], dayfirst=True, errors='coerce')
                    df['FECHA DE CREACION'] = df['FECHA DE CREACION'].fillna(pd.Timestamp.now())
                    
                    meses_es = {1:'Enero', 2:'Febrero', 3:'Marzo', 4:'Abril', 5:'Mayo', 6:'Junio', 7:'Julio', 8:'Agosto', 9:'Septiembre', 10:'Octubre', 11:'Noviembre', 12:'Diciembre'}
                    df['AÑO'] = df['FECHA DE CREACION'].dt.year.astype(str)
                    df['MES_NUM'] = df['FECHA DE CREACION'].dt.month
                    df['MES_NOMBRE'] = df['MES_NUM'].map(meses_es).fillna("Desconocido")
                    
                    dias_esp = {'Monday':'Lunes', 'Tuesday':'Martes', 'Wednesday':'Miércoles', 'Thursday':'Jueves', 'Friday':'Viernes', 'Saturday':'Sábado', 'Sunday':'Domingo'}
                    orden_dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
                    df['DIA_SEMANA'] = pd.Categorical(df['FECHA DE CREACION'].dt.day_name().map(dias_esp), categories=orden_dias, ordered=True)
                
                if 'TIEMPO EJECUCIÓN REAL' in df.columns:
                    df['TIEMPO_MINUTOS'] = df['TIEMPO EJECUCIÓN REAL'].apply(convertir_a_minutos)
                    df['TIEMPO_HORAS'] = df['TIEMPO_MINUTOS'] / 60 
                else:
                    df['TIEMPO_HORAS'] = 0

                if 'TIPO DE SERVICIO' in df.columns:
                    df['CIUDAD_REAL'] = df['TIPO DE SERVICIO'].apply(extraer_ciudad)
                elif 'UNIDAD DE NEGOCIO' in df.columns:
                    df['CIUDAD_REAL'] = df['UNIDAD DE NEGOCIO'].apply(extraer_ciudad)
                else:
                    df['CIUDAD_REAL'] = 'Sede Central'
                    
                return df
    except Exception as e:
        st.error(f"Error cargando la base de datos remota: {e}")
    
    return pd.DataFrame()

df = obtener_y_procesar_datos()

# ==========================================
# 5. MENSAJEROS Y CONFIGURACIÓN (Panel Lateral)
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
        if archivo_subido.name.endswith('.csv'): 
            df_nuevo = pd.read_csv(archivo_subido, sep=';', encoding='utf-8')
        else: 
            df_nuevo = pd.read_excel(archivo_subido)
        
        df_nuevo.columns = df_nuevo.columns.str.strip().str.upper()
        df_nuevo = df_nuevo.fillna("") 
        df_nuevo = df_nuevo.astype(str)
        
        total_filas = len(df_nuevo)
        tamano_lote = 500 
        
        st.markdown("⏳ **Sincronizando con Google Sheets...**")
        barra_progreso = st.progress(0)
        texto_progreso = st.empty()
        
        exito = True
        for i in range(0, total_filas, tamano_lote):
            lote = df_nuevo.iloc[i:i+tamano_lote]
            json_str = lote.to_json(orient='records')
            payload_limpio = json.loads(json_str)
            
            try:
                respuesta = requests.post(URL_APPSCRIPT, json=payload_limpio)
                if respuesta.status_code not in [200, 302]:
                    exito = False
                    st.error(f"Error en el servidor. HTTP: {respuesta.status_code}")
                    break
            except Exception as e:
                exito = False
                st.error(f"Error de conexión: {e}")
                break
                
            progreso_actual = min(1.0, (i + tamano_lote) / total_filas)
            barra_progreso.progress(progreso_actual)
            texto_progreso.text(f"Subiendo: {int(progreso_actual * 100)}% procesado")
            time.sleep(0.5)
        
        if exito:
            st.cache_data.clear()
            st.success("✅ ¡Base de datos sincronizada exitosamente!")
            time.sleep(1.5)
            st.rerun()

# ==========================================
# 6. RENDERIZADO DE LA INTERFAZ
# ==========================================
df_filtrado = pd.DataFrame() 

if st.session_state['pagina_actual'] == 'Inicio':
    st.markdown("<br>", unsafe_allow_html=True)
    col_izq, col_espacio, col_der = st.columns([1.2, 0.1, 1.5])
    
    with col_izq:
        logo_b64 = ""
        if os.path.exists("sergemLogo.png"):
            with open("sergemLogo.png", "rb") as img_file:
                logo_b64 = base64.b64encode(img_file.read()).decode()
        
        logo_html = f'<img src="data:image/png;base64,{logo_b64}" style="width: 250px; display: block; margin: 0 auto 15px auto; border-radius: 12px;">' if logo_b64 else '<h2 style="text-align: center;">SERGEM MENSAJERÍA</h2>'

        st.markdown(f"""
        <div class="tarjeta-roja">
            {logo_html}
            <hr style="border-top: 2px solid white; opacity: 0.5;">
            <h1 style="font-size: 50px; font-weight: 800;">Bienvenido (a)</h1>
            <p style="font-size: 18px; line-height: 1.6; opacity: 0.95;">Este aplicativo permite visualizar la operatividad y la eficiencia de nuestra operación.</p>
        </div>
        """, unsafe_allow_html=True)
        
    with col_der:
        st.markdown("<h2 style='text-align: center; margin-top: 0px; margin-bottom: 25px; font-size: 34px; font-weight: 700;'>Menú Principal</h2>", unsafe_allow_html=True)
        if df.empty:
            st.warning("⚠️ La base de datos está vacía o cargando. Use el panel lateral izquierdo para subir el archivo inicial (ORIGINAL WIP) a Google Sheets.")
        else:
            st.button("📊 Tablero General", on_click=cambiar_pagina, args=('Tablero',))
            st.markdown("<div style='margin-bottom: 14px;'></div>", unsafe_allow_html=True)
            st.button("📝 Volúmenes de Solicitud", on_click=cambiar_pagina, args=('Solicitudes',))
            st.markdown("<div style='margin-bottom: 14px;'></div>", unsafe_allow_html=True)
            st.button("⏱️ Medición de Tiempos", on_click=cambiar_pagina, args=('Tiempo',))
            st.markdown("<div style='margin-bottom: 14px;'></div>", unsafe_allow_html=True)
            st.button("📈 Cuotas de Participación", on_click=cambiar_pagina, args=('Participacion',))

elif not df.empty and st.session_state['pagina_actual'] != 'Inicio':
    
    st.button("🏠 Volver al Menú Principal", on_click=cambiar_pagina, args=('Inicio',))
    st.markdown("<div style='background-color: #99C2E2; padding: 15px; border-radius: 8px;'><h3 style='color: #FFFFFF !important; margin:0; font-weight:700;'>Filtros Globales de Control</h3></div><br>", unsafe_allow_html=True)
    
    col_f0, col_f1, col_f2, col_f3, col_f4 = st.columns(5)
    
    with col_f0:
        años = sorted(df['AÑO'].dropna().unique().tolist()) if 'AÑO' in df.columns else []
        ano_sel = st.multiselect("Año", años, default=años)
    with col_f1:
        meses_disp = df[['MES_NUM', 'MES_NOMBRE']].drop_duplicates().sort_values('MES_NUM')['MES_NOMBRE'].tolist() if 'MES_NUM' in df.columns else []
        mes_sel = st.multiselect("Mes", meses_disp, placeholder="Selección múltiple")
    with col_f2:
        ciudades = sorted(df['CIUDAD_REAL'].dropna().unique().tolist()) if 'CIUDAD_REAL' in df.columns else []
        ciudad_sel = st.multiselect("Ciudad / Sede", ciudades, placeholder="Todas")
    with col_f3:
        centros = sorted(df['CENTRO DE COSTOS'].dropna().astype(str).unique().tolist()) if 'CENTRO DE COSTOS' in df.columns else []
        centro_sel = st.multiselect("Centro de Costos", centros, placeholder="Todas")
    with col_f4:
        tramites = sorted(df['TRAMITE'].dropna().unique().tolist()) if 'TRAMITE' in df.columns else []
        tramite_sel = st.multiselect("Trámite", tramites, placeholder="Todas")

    df_filtrado = df.copy()
    if ano_sel and 'AÑO' in df_filtrado.columns: df_filtrado = df_filtrado[df_filtrado['AÑO'].isin(ano_sel)]
    if mes_sel and 'MES_NOMBRE' in df_filtrado.columns: df_filtrado = df_filtrado[df_filtrado['MES_NOMBRE'].isin(mes_sel)]
    if ciudad_sel and 'CIUDAD_REAL' in df_filtrado.columns: df_filtrado = df_filtrado[df_filtrado['CIUDAD_REAL'].isin(ciudad_sel)]
    if centro_sel and 'CENTRO DE COSTOS' in df_filtrado.columns: df_filtrado = df_filtrado[df_filtrado['CENTRO DE COSTOS'].astype(str).isin(centro_sel)]
    if tramite_sel and 'TRAMITE' in df_filtrado.columns: df_filtrado = df_filtrado[df_filtrado['TRAMITE'].isin(tramite_sel)]

    paleta_datos = ['#1D3557', '#457B9D', '#A8DADC', '#E30613', '#F4A261', '#2A9D8F', '#E9C46A']

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
        
        ciudades_en_pantalla = df_filtrado['CIUDAD_REAL'].unique() if 'CIUDAD_REAL' in df_filtrado.columns else []
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
            if 'MES_NOMBRE' in df_filtrado.columns and 'CIUDAD_REAL' in df_filtrado.columns:
                st.markdown("<b>Solicitudes por Fecha y Ciudad</b>", unsafe_allow_html=True)
                res_mes_ciudad = df_filtrado.groupby(['MES_NUM', 'MES_NOMBRE', 'CIUDAD_REAL']).size().reset_index(name='Total')
                res_mes_ciudad = res_mes_ciudad.sort_values('MES_NUM')
                
                # Modificado a Gráfico de Barras Agrupadas con cantidades (Requerimiento de Doña Yesenia)
                fig_combo = px.bar(res_mes_ciudad, x='MES_NOMBRE', y='Total', color='CIUDAD_REAL', 
                                   barmode='group', text='Total',
                                   color_discrete_sequence=paleta_datos)
                fig_combo.update_traces(textposition='outside')
                fig_combo.update_layout(margin=dict(t=30, b=10, l=10, r=10), plot_bgcolor='white', paper_bgcolor='rgba(0,0,0,0)')
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
                if 'MES_NOMBRE' in df_filtrado.columns and 'CIUDAD_REAL' in df_filtrado.columns:
                    st.markdown("<b>Evolución del Tiempo Promedio (Horas) por Sede</b>", unsafe_allow_html=True)
                    tendencia = df_filtrado.groupby(['MES_NUM', 'MES_NOMBRE', 'CIUDAD_REAL'])['TIEMPO_HORAS'].mean().reset_index()
                    tendencia = tendencia.sort_values('MES_NUM')
                    fig_tend = px.line(tendencia, x='MES_NOMBRE', y='TIEMPO_HORAS', color='CIUDAD_REAL', markers=True, color_discrete_sequence=paleta_datos)
                    st.plotly_chart(fig_tend, use_container_width=True)

    # ==========================================
    # VISTA 3: SOLICITUDES
    # ==========================================
    elif st.session_state['pagina_actual'] == 'Solicitudes':
        st.title("📝 Análisis Detallado de Volúmenes")
        
        # Eliminada la gráfica de área. Añadida la Tabla Dinámica (Matriz) cruzando Sedes vs Meses
        if 'MES_NOMBRE' in df_filtrado.columns and 'CIUDAD_REAL' in df_filtrado.columns:
            st.markdown("<b>Matriz Operativa: Solicitudes por Sede y Mes</b>", unsafe_allow_html=True)
            
            pivot_df = pd.pivot_table(df_filtrado, index='CIUDAD_REAL', columns='MES_NOMBRE', aggfunc='size', fill_value=0)
            
            meses_orden = [m for m in ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'] if m in pivot_df.columns]
            pivot_df = pivot_df[meses_orden]
            
            pivot_df['Total General'] = pivot_df.sum(axis=1)
            pivot_df.loc['Total General'] = pivot_df.sum(axis=0)
            
            pivot_df = pivot_df.reset_index().rename(columns={'CIUDAD_REAL': 'SEDE / MES'})
            
            st.dataframe(pivot_df, use_container_width=True, hide_index=True)
            
        st.markdown("<hr>", unsafe_allow_html=True)
            
        if 'CIUDAD_REAL' in df_filtrado.columns:
            st.markdown("<b>Distribución Absoluta de Servicios por Sede</b>", unsafe_allow_html=True)
            res_un = df_filtrado.groupby('CIUDAD_REAL').size().reset_index(name='Solicitudes').sort_values(by='Solicitudes', ascending=False)
            fig_un = px.bar(res_un, x='CIUDAD_REAL', y='Solicitudes', color='CIUDAD_REAL', color_discrete_sequence=paleta_datos, text='Solicitudes')
            fig_un.update_traces(textposition='outside')
            fig_un.update_layout(margin=dict(t=30, b=10, l=10, r=10), showlegend=False, plot_bgcolor='white', paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_un, use_container_width=True)

    # ==========================================
    # VISTA 4: PARTICIPACIÓN
    # ==========================================
    elif st.session_state['pagina_actual'] == 'Participacion':
        st.title("📈 Análisis de Cuotas de Participación")
        col_p1, col_p2 = st.columns(2)
        
        with col_p1:
            if 'CIUDAD_REAL' in df_filtrado.columns:
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
