import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from datetime import timedelta
import re

# 1. CONFIGURACIÓN DE LA PÁGINA
st.set_page_config(
    page_title="Tablero Mensajería - Sergem Mensajería",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. ESTILOS CSS PERSONALIZADOS
st.markdown("""
    <style>
    .stApp { background-color: #EAF4EC; } 
    
    .tarjeta-verde {
        background-color: #008037;
        color: white;
        padding: 40px;
        border-radius: 10px;
        height: 100%;
        min-height: 400px;
    }
    
    div.stButton > button {
        width: 100%;
        background-color: white;
        color: #008037;
        border: 2px solid #008037;
        padding: 15px 32px;
        text-align: center;
        font-size: 18px;
        font-weight: bold;
        border-radius: 8px;
        margin-bottom: 10px;
        transition: 0.3s;
    }
    div.stButton > button:hover {
        background-color: #008037;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

# 3. CONTROL DE NAVEGACIÓN
if 'pagina_actual' not in st.session_state:
    st.session_state['pagina_actual'] = 'Inicio'

def cambiar_pagina(nombre_pagina):
    st.session_state['pagina_actual'] = nombre_pagina

# Función para convertir "6d 15h 5min" a minutos totales
def convertir_a_minutos(texto_tiempo):
    if pd.isna(texto_tiempo) or texto_tiempo == '':
        return 0
    
    texto = str(texto_tiempo).lower()
    minutos_totales = 0
    
    # Buscar patrones de días, horas y minutos
    dias = re.search(r'(\d+)\s*d', texto)
    horas = re.search(r'(\d+)\s*h', texto)
    mins = re.search(r'(\d+)\s*min', texto)
    
    if dias: minutos_totales += int(dias.group(1)) * 1440  # 1 día = 1440 min
    if horas: minutos_totales += int(horas.group(1)) * 60   # 1 hora = 60 min
    if mins: minutos_totales += int(mins.group(1))
    
    return minutos_totales

# 4. CARGA Y PROCESAMIENTO DE DATOS (Panel Lateral)
with st.sidebar:
    if st.session_state['pagina_actual'] != 'Inicio':
        if st.button("🏠 Volver al Menú Principal"):
            cambiar_pagina('Inicio')
        st.markdown("---")
        
    st.header("1. Cargar Datos")
    archivo_subido = st.file_uploader("Subir archivo ORIGINAL WIP", type=['xlsx', 'xls', 'csv'])
    
    df_filtrado = pd.DataFrame() 
    
    if archivo_subido is not None:
        try:
            if archivo_subido.name.endswith('.csv'):
                df = pd.read_csv(archivo_subido, sep=';', encoding='utf-8', on_bad_lines='skip')
            else:
                df = pd.read_excel(archivo_subido)
                
            df.columns = df.columns.str.strip().str.upper()
            
            # Formateo de fechas
            if 'FECHA DE CREACION' in df.columns:
                df['FECHA DE CREACION'] = pd.to_datetime(df['FECHA DE CREACION'], errors='coerce')
                df = df.dropna(subset=['FECHA DE CREACION'])
                dias_esp = {'Monday':'Lunes', 'Tuesday':'Martes', 'Wednesday':'Miércoles', 
                            'Thursday':'Jueves', 'Friday':'Viernes', 'Saturday':'Sábado', 'Sunday':'Domingo'}
                
                # Para ordenar correctamente los días en los filtros
                orden_dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
                df['DIA_SEMANA'] = pd.Categorical(df['FECHA DE CREACION'].dt.day_name().map(dias_esp), categories=orden_dias, ordered=True)
                df['MES'] = df['FECHA DE CREACION'].dt.to_period('M').astype(str)

            # Conversión de la columna de tiempos
            if 'TIEMPO EJECUCIÓN REAL' in df.columns:
                df['TIEMPO_MINUTOS'] = df['TIEMPO EJECUCIÓN REAL'].apply(convertir_a_minutos)
                # Creamos una columna en horas para que las gráficas sean más fáciles de leer
                df['TIEMPO_HORAS'] = df['TIEMPO_MINUTOS'] / 60 

            # FILTROS GLOBALES
            st.header("2. Filtros Globales")
            
            ciudades = df['UNIDAD DE NEGOCIO'].dropna().unique().tolist() if 'UNIDAD DE NEGOCIO' in df.columns else []
            ciudad_sel = st.multiselect("Ciudad / Unidad de Negocio", ciudades, default=ciudades)
            
            meses = sorted(df['MES'].dropna().unique().tolist()) if 'MES' in df.columns else []
            mes_sel = st.multiselect("Meses", meses, default=meses)

            dias = sorted(df['DIA_SEMANA'].dropna().unique().tolist(), key=lambda x: orden_dias.index(x)) if 'DIA_SEMANA' in df.columns else []
            dia_sel = st.multiselect("Días de la Semana", dias, default=dias)

            # Aplicar filtros maestros
            df_filtrado = df.copy()
            if ciudad_sel:
                df_filtrado = df_filtrado[df_filtrado['UNIDAD DE NEGOCIO'].isin(ciudad_sel)]
            if mes_sel:
                df_filtrado = df_filtrado[df_filtrado['MES'].isin(mes_sel)]
            if dia_sel:
                df_filtrado = df_filtrado[df_filtrado['DIA_SEMANA'].isin(dia_sel)]

        except Exception as e:
            st.error(f"Error procesando el archivo: {e}")

# ==========================================
# VISTA 1: MENÚ PRINCIPAL
# ==========================================
if st.session_state['pagina_actual'] == 'Inicio':
    st.markdown("<br><br>", unsafe_allow_html=True)
    col_izq, col_espacio, col_der = st.columns([1.2, 0.2, 1.5])
    
    with col_izq:
        st.markdown("""
            <div class="tarjeta-verde">
                <h2 style="color: white; text-align: center;">SERGEM MENSAJERÍA</h2>
                <hr style="border-top: 2px solid white;">
                <h1 style="color: white; font-size: 50px;">Bienvenido (a)</h1>
                <p style="font-size: 18px; line-height: 1.6;">
                    Este aplicativo permite visualizar la productividad y la efectividad de nuestros colaboradores. 
                </p>
            </div>
        """, unsafe_allow_html=True)
        
    with col_der:
        st.markdown("<h2 style='text-align: center; color: #333;'>Tablero Mensajería</h2><br>", unsafe_allow_html=True)
        
        if st.button("📊 Indicadores"): cambiar_pagina("Indicadores")
        if st.button("🛵 Solicitudes"): cambiar_pagina("Solicitudes")
        if st.button("🥧 Participación"): cambiar_pagina("Participación")
        if st.button("⏱️ Tiempo"): cambiar_pagina("Tiempo")

# ==========================================
# CÁLCULOS MAESTROS PARA LAS VISTAS
# ==========================================
elif not df_filtrado.empty:
    total_solicitudes = len(df_filtrado)
    
    dias_habiles = 0
    if 'FECHA DE CREACION' in df_filtrado.columns and total_solicitudes > 0:
        fecha_min = df_filtrado['FECHA DE CREACION'].min().date()
        fecha_max = df_filtrado['FECHA DE CREACION'].max().date()
        dias_habiles = np.busday_count(fecha_min, fecha_max + timedelta(days=1), weekmask='1111110')
    
    eficacia = 0
    if 'ESTADO' in df_filtrado.columns and total_solicitudes > 0:
        fallidos = df_filtrado['ESTADO'].str.contains('Fallido', case=False, na=False).sum()
        eficacia = ((total_solicitudes - fallidos) / total_solicitudes) * 100
        
    promedio_diario = total_solicitudes / dias_habiles if dias_habiles > 0 else 0

    # VISTA 2: INDICADORES
    if st.session_state['pagina_actual'] == 'Indicadores':
        st.title("📊 Indicadores Generales de Productividad")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("📦 Total Vueltas", f"{total_solicitudes:,}")
        col2.metric("🎯 Eficacia Operativa", f"{eficacia:.1f}%")
        col3.metric("📅 Días Laborados (Filtro)", f"{dias_habiles}")
        col4.metric("🛵 Promedio Vueltas / Día", f"{promedio_diario:.1f}")
        
        st.markdown("---")
        if 'COLABORADOR' in df_filtrado.columns:
            resumen_mensajeros = df_filtrado.groupby('COLABORADOR').size().reset_index(name='Total Vueltas')
            resumen_mensajeros = resumen_mensajeros.sort_values(by='Total Vueltas', ascending=False)
            fig_colab = px.bar(resumen_mensajeros, x='COLABORADOR', y='Total Vueltas', text='Total Vueltas',
                               color='Total Vueltas', color_continuous_scale='Greens',
                               title="Volumen Total por Mensajero")
            st.plotly_chart(fig_colab, use_container_width=True)

    # VISTA 3: SOLICITUDES
    elif st.session_state['pagina_actual'] == 'Solicitudes':
        st.title("🛵 Comportamiento de Solicitudes")
        if 'MES' in df_filtrado.columns and 'UNIDAD DE NEGOCIO' in df_filtrado.columns:
            resumen_volumen = df_filtrado.groupby(['MES', 'UNIDAD DE NEGOCIO']).size().reset_index(name='Total')
            fig_barras = px.bar(resumen_volumen, x='MES', y='Total', color='UNIDAD DE NEGOCIO',
                                barmode='group', color_discrete_sequence=['#008037', '#FFC20E', '#808080'],
                                title="Solicitudes por Mes y Sede")
            st.plotly_chart(fig_barras, use_container_width=True)

    # VISTA 4: PARTICIPACIÓN
    elif st.session_state['pagina_actual'] == 'Participación':
        st.title("🥧 Participación Operativa")
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            if 'DIA_SEMANA' in df_filtrado.columns:
                resumen_dias = df_filtrado['DIA_SEMANA'].value_counts().reset_index()
                resumen_dias.columns = ['Día', 'Total']
                fig_dona = px.pie(resumen_dias, values='Total', names='Día', hole=0.5,
                                  color_discrete_sequence=px.colors.sequential.Greens_r,
                                  title="Participación por Día de la Semana")
                st.plotly_chart(fig_dona, use_container_width=True)
                
        with col_g2:
            if 'CENTRO DE COSTOS' in df_filtrado.columns:
                resumen_cc = df_filtrado.groupby('CENTRO DE COSTOS').size().reset_index(name='Total')
                resumen_cc = resumen_cc.sort_values(by='Total', ascending=False).head(15) # Mostrar top 15 para no saturar
                fig_tree = px.treemap(resumen_cc, path=['CENTRO DE COSTOS'], values='Total',
                                      color='Total', color_continuous_scale='Greens',
                                      title="Top 15 Centros de Costos con más volumen")
                st.plotly_chart(fig_tree, use_container_width=True)

    # VISTA 5: TIEMPO (NUEVO REQUERIMIENTO)
    elif st.session_state['pagina_actual'] == 'Tiempo':
        st.title("⏱️ Medición de Tiempos")
        
        if 'TIEMPO_HORAS' in df_filtrado.columns and 'TRAMITE' in df_filtrado.columns:
            
            # Gráfica 1: Dónde se va la mayor cantidad de tiempo (Total por Trámite)
            st.subheader("Tiempo Total Invertido por Trámite")
            st.write("Identifica qué gestiones consumen la mayor cantidad de horas operativas.")
            
            resumen_tiempo = df_filtrado.groupby('TRAMITE')['TIEMPO_HORAS'].sum().reset_index()
            resumen_tiempo = resumen_tiempo.sort_values(by='TIEMPO_HORAS', ascending=False).head(10) # Top 10
            
            fig_tramite = px.bar(resumen_tiempo, x='TIEMPO_HORAS', y='TRAMITE', orientation='h',
                                 text=resumen_tiempo['TIEMPO_HORAS'].apply(lambda x: f"{x:.1f} hrs"),
                                 color='TIEMPO_HORAS', color_continuous_scale='Reds',
                                 labels={'TIEMPO_HORAS': 'Horas Totales', 'TRAMITE': 'Tipo de Gestión'})
            fig_tramite.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_tramite, use_container_width=True)

            st.markdown("---")

            # Gráfica 2: Comparativo de tiempo por Ciudad (Línea de Tendencia)
            st.subheader("Tendencia de Tiempo Promedio por Sede")
            if 'MES' in df_filtrado.columns and 'UNIDAD DE NEGOCIO' in df_filtrado.columns:
                tendencia_tiempo = df_filtrado.groupby(['MES', 'UNIDAD DE NEGOCIO'])['TIEMPO_HORAS'].mean().reset_index()
                
                fig_tendencia = px.line(tendencia_tiempo, x='MES', y='TIEMPO_HORAS', color='UNIDAD DE NEGOCIO',
                                        markers=True, color_discrete_sequence=['#008037', '#FFC20E', '#808080'],
                                        labels={'TIEMPO_HORAS': 'Promedio en Horas por Solicitud', 'MES': 'Mes'})
                st.plotly_chart(fig_tendencia, use_container_width=True)
        else:
            st.warning("Asegúrese de cargar un archivo que contenga las columnas 'TIEMPO EJECUCIÓN REAL' y 'TRAMITE'.")

elif st.session_state['pagina_actual'] != 'Inicio':
    st.info("👈 Por favor carga el archivo **ORIGINAL WIP** en el panel izquierdo para ver esta sección.")
