import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import timedelta
import re

# 1. CONFIGURACIÓN DE LA PÁGINA
st.set_page_config(
    page_title="Tablero Mensajería - Sergem Mensajería",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. INTEGRACIÓN DE CSS (PEGADO A LA IZQUIERDA PARA EVITAR QUE MARKDOWN LO IMPRIMA)
st.markdown("""
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
<style>
/* Forzar Fondo general profesional */
.stApp { 
    background-color: #F4F7F6 !important; 
}

/* Forzar texto oscuro general para evitar el Modo Oscuro de los navegadores */
.stApp p, .stApp span, .stApp label, .stApp div[data-testid="stMarkdownContainer"] {
    color: #1D3557 !important;
}

/* Tarjeta de Bienvenida */
.tarjeta-roja {
    background: linear-gradient(135deg, #C1121F 0%, #7A0A12 100%) !important;
    padding: 40px;
    border-radius: 12px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    height: 100%;
    min-height: 400px;
}

/* Excepción: Forzar que los textos DENTRO de la tarjeta roja sean blancos */
.tarjeta-roja p, .tarjeta-roja h1, .tarjeta-roja h2, .tarjeta-roja span, .tarjeta-roja div {
    color: white !important;
}

/* Botones del menú principal */
.stButton > button {
    width: 100%;
    background-color: white !important;
    color: #1D3557 !important;
    border: 2px solid #E5E5E5 !important;
    padding: 15px 32px;
    font-size: 18px;
    font-weight: 600;
    border-radius: 8px;
    transition: all 0.3s ease-in-out;
    box-shadow: 0 2px 5px rgba(0,0,0,0.05);
}
.stButton > button:hover, .stButton > button:active {
    background-color: #C1121F !important;
    color: white !important;
    border-color: #C1121F !important;
    transform: translateY(-2px);
}

/* Tarjetas de KPIs laterales tipo Bootstrap */
.kpi-card {
    background-color: white !important;
    padding: 20px;
    border-radius: 10px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    text-align: center;
    margin-bottom: 20px;
    border-left: 5px solid #C1121F !important;
}
.kpi-title { font-size: 16px !important; color: #6c757d !important; font-weight: 600; margin-bottom: 5px; }
.kpi-value { font-size: 32px !important; color: #1D3557 !important; font-weight: 700; margin: 0; }

/* Estilos de encabezados */
h1, h2, h3 { color: #1D3557 !important; font-weight: 700; }
</style>
""", unsafe_allow_html=True)

# 3. CONTROL DE NAVEGACIÓN (CALLBACKS)
if 'pagina_actual' not in st.session_state:
    st.session_state['pagina_actual'] = 'Inicio'

def cambiar_pagina(nombre_pagina):
    st.session_state['pagina_actual'] = nombre_pagina

def convertir_a_minutos(texto_tiempo):
    if pd.isna(texto_tiempo) or texto_tiempo == '': return 0
    texto = str(texto_tiempo).lower()
    minutos_totales = 0
    dias = re.search(r'(\d+)\s*d', texto)
    horas = re.search(r'(\d+)\s*h', texto)
    mins = re.search(r'(\d+)\s*min', texto)
    if dias: minutos_totales += int(dias.group(1)) * 1440 
    if horas: minutos_totales += int(horas.group(1)) * 60 
    if mins: minutos_totales += int(mins.group(1))
    return minutos_totales

# 4. CARGA DE DATOS Y FLUJO PRINCIPAL
df_filtrado = pd.DataFrame() 

if st.session_state['pagina_actual'] == 'Inicio':
    st.markdown("<br><br>", unsafe_allow_html=True)
    col_izq, col_espacio, col_der = st.columns([1.2, 0.2, 1.5])
    
    with col_izq:
        st.markdown("""
<div class="tarjeta-roja">
    <h2 style="text-align: center;">SERGEM MENSAJERÍA</h2>
    <hr style="border-top: 2px solid white; opacity: 0.5;">
    <h1 style="font-size: 50px;">Bienvenido (a)</h1>
    <p style="font-size: 18px; line-height: 1.6;">
        Este aplicativo gerencial permite visualizar la productividad, la efectividad 
        y los tiempos operativos de nuestros colaboradores a nivel nacional.
    </p>
    <br>
    <p style="font-size: 14px; opacity: 0.8;">Cargue el archivo ORIGINAL WIP a la derecha para comenzar.</p>
</div>
""", unsafe_allow_html=True)
        
    with col_der:
        st.markdown("<h2 style='text-align: center;'>Menú Principal</h2><br>", unsafe_allow_html=True)
        st.button("📊 Tablero General (Indicadores)", on_click=cambiar_pagina, args=('Tablero',))
        st.button("⏱️ Medición de Tiempos", on_click=cambiar_pagina, args=('Tiempo',))
        
        st.markdown("<br><hr>", unsafe_allow_html=True)
        archivo_subido = st.file_uploader("📥 Subir archivo ORIGINAL WIP", type=['xlsx', 'xls', 'csv'])
        if archivo_subido is not None:
            st.session_state['archivo_cargado'] = archivo_subido
            st.success("¡Archivo cargado en memoria exitosamente! Seleccione un tablero arriba.")

# Si hay un archivo cargado y salimos del menú Inicio, se renderiza el Dashboard
if 'archivo_cargado' in st.session_state and st.session_state['pagina_actual'] != 'Inicio':
    try:
        # LECTURA DEL ARCHIVO
        if st.session_state['archivo_cargado'].name.endswith('.csv'):
            df = pd.read_csv(st.session_state['archivo_cargado'], sep=';', encoding='utf-8', on_bad_lines='skip')
        else:
            df = pd.read_excel(st.session_state['archivo_cargado'])
            
        df.columns = df.columns.str.strip().str.upper()
        
        # PROCESAMIENTO DE FECHAS
        if 'FECHA DE CREACION' in df.columns:
            df['FECHA DE CREACION'] = pd.to_datetime(df['FECHA DE CREACION'], errors='coerce')
            df = df.dropna(subset=['FECHA DE CREACION'])
            dias_esp = {'Monday':'Lunes', 'Tuesday':'Martes', 'Wednesday':'Miércoles', 'Thursday':'Jueves', 'Friday':'Viernes', 'Saturday':'Sábado', 'Sunday':'Domingo'}
            orden_dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
            df['DIA_SEMANA'] = pd.Categorical(df['FECHA DE CREACION'].dt.day_name().map(dias_esp), categories=orden_dias, ordered=True)
            df['MES'] = df['FECHA DE CREACION'].dt.to_period('M').astype(str)

        # PROCESAMIENTO DE TIEMPOS
        if 'TIEMPO EJECUCIÓN REAL' in df.columns:
            df['TIEMPO_MINUTOS'] = df['TIEMPO EJECUCIÓN REAL'].apply(convertir_a_minutos)
            df['TIEMPO_HORAS'] = df['TIEMPO_MINUTOS'] / 60 

        # FILTROS SUPERIORES
        st.button("🏠 Volver al Menú", on_click=cambiar_pagina, args=('Inicio',))
        st.markdown("""
<div style='background-color: #1D3557; padding: 15px; border-radius: 8px;'>
    <h3 style='color: white !important; margin:0;'>Filtros Globales</h3>
</div><br>
""", unsafe_allow_html=True)
        
        col_f1, col_f2, col_f3, col_f4, col_f5 = st.columns(5)
        
        with col_f1:
            meses = sorted(df['MES'].dropna().unique().tolist()) if 'MES' in df.columns else []
            mes_sel = st.multiselect("Fecha (Mes)", meses, placeholder="Selección múltiple")
        with col_f2:
            ciudades = sorted(df['UNIDAD DE NEGOCIO'].dropna().unique().tolist()) if 'UNIDAD DE NEGOCIO' in df.columns else []
            ciudad_sel = st.multiselect("Ciudad", ciudades, placeholder="Todas")
        with col_f3:
            centros = sorted(df['CENTRO DE COSTOS'].dropna().astype(str).unique().tolist()) if 'CENTRO DE COSTOS' in df.columns else []
            centro_sel = st.multiselect("Centro de Costos", centros, placeholder="Todas")
        with col_f4:
            colab = sorted(df['COLABORADOR'].dropna().unique().tolist()) if 'COLABORADOR' in df.columns else []
            colab_sel = st.multiselect("Colaborador", colab, placeholder="Todas")
        with col_f5:
            tramites = sorted(df['TRAMITE'].dropna().unique().tolist()) if 'TRAMITE' in df.columns else []
            tramite_sel = st.multiselect("Trámite", tramites, placeholder="Todas")

        # APLICAR FILTROS
        df_filtrado = df.copy()
        if mes_sel: df_filtrado = df_filtrado[df_filtrado['MES'].isin(mes_sel)]
        if ciudad_sel: df_filtrado = df_filtrado[df_filtrado['UNIDAD DE NEGOCIO'].isin(ciudad_sel)]
        if centro_sel: df_filtrado = df_filtrado[df_filtrado['CENTRO DE COSTOS'].astype(str).isin(centro_sel)]
        if colab_sel: df_filtrado = df_filtrado[df_filtrado['COLABORADOR'].isin(colab_sel)]
        if tramite_sel: df_filtrado = df_filtrado[df_filtrado['TRAMITE'].isin(tramite_sel)]

        # PALETA DE COLORES PROFESIONAL
        paleta_datos = ['#1D3557', '#457B9D', '#A8DADC', '#C1121F', '#F4A261', '#2A9D8F', '#E9C46A']

        # ==========================================
        # VISTA: TABLERO GERENCIAL
        # ==========================================
        if st.session_state['pagina_actual'] == 'Tablero':
            
            total_solicitudes = len(df_filtrado)
            dias_habiles = 0
            if 'FECHA DE CREACION' in df_filtrado.columns and total_solicitudes > 0:
                fecha_min = df_filtrado['FECHA DE CREACION'].min().date()
                fecha_max = df_filtrado['FECHA DE CREACION'].max().date()
                dias_habiles = np.busday_count(fecha_min, fecha_max + timedelta(days=1), weekmask='1111110')
            
            promedio_diario = total_solicitudes / dias_habiles if dias_habiles > 0 else 0
            
            eficacia = 0
            if 'ESTADO' in df_filtrado.columns and total_solicitudes > 0:
                fallidos = df_filtrado['ESTADO'].str.contains('Fallido', case=False, na=False).sum()
                eficacia = ((total_solicitudes - fallidos) / total_solicitudes) * 100 if total_solicitudes > 0 else 0

            st.markdown("<hr>", unsafe_allow_html=True)
            col_kpis, col_graficos = st.columns([1.5, 5])
            
            # LADO IZQUIERDO: KPIs
            with col_kpis:
                st.markdown(f"""
<div class="kpi-card">
    <div class="kpi-title">🛵 Solicitudes Totales</div>
    <div class="kpi-value">{total_solicitudes:,}</div>
</div>
<div class="kpi-card">
    <div class="kpi-title">📈 Promedio Diario</div>
    <div class="kpi-value">{promedio_diario:.1f}</div>
</div>
<div class="kpi-card">
    <div class="kpi-title">✅ Efectividad Operativa</div>
    <div class="kpi-value">{eficacia:.1f}%</div>
</div>
""", unsafe_allow_html=True)
                
                if 'DIA_SEMANA' in df_filtrado.columns:
                    res_dias = df_filtrado['DIA_SEMANA'].value_counts().reset_index()
                    res_dias.columns = ['Día', 'Total']
                    fig_dias = px.pie(res_dias, values='Total', names='Día', hole=0.6, 
                                      color_discrete_sequence=paleta_datos,
                                      title="Participación por Día")
                    fig_dias.update_layout(margin=dict(t=40, b=0, l=0, r=0), showlegend=False)
                    st.plotly_chart(fig_dias, use_container_width=True)

            # LADO DERECHO: GRÁFICOS
            with col_graficos:
                if 'MES' in df_filtrado.columns and 'UNIDAD DE NEGOCIO' in df_filtrado.columns:
                    st.markdown("<b>Solicitudes por Fecha y Ciudad</b>", unsafe_allow_html=True)
                    res_mes_ciudad = df_filtrado.groupby(['MES', 'UNIDAD DE NEGOCIO']).size().reset_index(name='Total')
                    
                    if 'COLABORADOR' in df_filtrado.columns:
                        res_promedio = df_filtrado.groupby(['MES']).apply(lambda x: len(x) / x['COLABORADOR'].nunique() if x['COLABORADOR'].nunique() > 0 else 0).reset_index(name='Promedio')
                    else:
                        res_promedio = df_filtrado.groupby(['MES']).size().reset_index(name='Promedio')

                    fig_combo = px.bar(res_mes_ciudad, x='MES', y='Total', color='UNIDAD DE NEGOCIO', 
                                       color_discrete_sequence=paleta_datos)
                    
                    fig_combo.add_trace(go.Scatter(x=res_promedio['MES'], y=res_promedio['Promedio'], 
                                                   mode='lines+markers', name='Promedio por Trabajador',
                                                   line=dict(color='#C1121F', width=3), yaxis='y2'))
                    
                    fig_combo.update_layout(
                        yaxis2=dict(overlaying='y', side='right', showgrid=False),
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                        margin=dict(t=0, b=0, l=0, r=0),
                        plot_bgcolor='white',
                        paper_bgcolor='rgba(0,0,0,0)'
                    )
                    st.plotly_chart(fig_combo, use_container_width=True)

                col_graf_izq, col_graf_der = st.columns(2)
                
                with col_graf_izq:
                    st.markdown("<br><b>Participación por Centro de Costos</b>", unsafe_allow_html=True)
                    if 'CENTRO DE COSTOS' in df_filtrado.columns:
                        res_cc = df_filtrado.groupby('CENTRO DE COSTOS').size().reset_index(name='Total')
                        res_cc = res_cc.sort_values(by='Total', ascending=False).head(10)
                        fig_tree = px.treemap(res_cc, path=['CENTRO DE COSTOS'], values='Total',
                                              color='Total', color_continuous_scale='Blues')
                        fig_tree.update_layout(margin=dict(t=0, b=0, l=0, r=0), paper_bgcolor='rgba(0,0,0,0)')
                        st.plotly_chart(fig_tree, use_container_width=True)

                with col_graf_der:
                    st.markdown("<br><b>Top Solicitudes por Trámite</b>", unsafe_allow_html=True)
                    if 'TRAMITE' in df_filtrado.columns:
                        res_tramite = df_filtrado.groupby('TRAMITE').size().reset_index(name='Solicitudes')
                        res_tramite['Participación'] = (res_tramite['Solicitudes'] / total_solicitudes * 100).map("{:.1f}%".format)
                        res_tramite = res_tramite.sort_values(by='Solicitudes', ascending=False).head(8)
                        st.dataframe(res_tramite, use_container_width=True, hide_index=True)

        # ==========================================
        # VISTA: TIEMPOS
        # ==========================================
        elif st.session_state['pagina_actual'] == 'Tiempo':
            st.title("⏱️ Análisis Gerencial de Tiempos")
            if 'TIEMPO_HORAS' in df_filtrado.columns and 'TRAMITE' in df_filtrado.columns:
                col_t1, col_t2 = st.columns(2)
                with col_t1:
                    st.markdown("<b>Horas Totales Invertidas por Tipo de Gestión</b>", unsafe_allow_html=True)
                    res_tiempo = df_filtrado.groupby('TRAMITE')['TIEMPO_HORAS'].sum().reset_index().sort_values(by='TIEMPO_HORAS', ascending=True).tail(10)
                    fig_tramite = px.bar(res_tiempo, x='TIEMPO_HORAS', y='TRAMITE', orientation='h',
                                         text=res_tiempo['TIEMPO_HORAS'].apply(lambda x: f"{x:.0f} h"),
                                         color='TIEMPO_HORAS', color_continuous_scale='Blues')
                    fig_tramite.update_layout(margin=dict(t=0, b=0, l=0, r=0), plot_bgcolor='white', paper_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(fig_tramite, use_container_width=True)
                
                with col_t2:
                    st.markdown("<b>Evolución del Tiempo Promedio (Horas) por Sede</b>", unsafe_allow_html=True)
                    if 'MES' in df_filtrado.columns:
                        tendencia = df_filtrado.groupby(['MES', 'UNIDAD DE NEGOCIO'])['TIEMPO_HORAS'].mean().reset_index()
                        fig_tend = px.line(tendencia, x='MES', y='TIEMPO_HORAS', color='UNIDAD DE NEGOCIO',
                                           markers=True, color_discrete_sequence=paleta_datos)
                        fig_tend.update_layout(margin=dict(t=0, b=0, l=0, r=0), plot_bgcolor='white', paper_bgcolor='rgba(0,0,0,0)')
                        st.plotly_chart(fig_tend, use_container_width=True)
            else:
                st.warning("Faltan las columnas de Tiempo o Trámite para calcular esta vista.")

    except Exception as e:
        st.error(f"Error procesando el archivo. Verifique el formato. Detalle: {e}")
