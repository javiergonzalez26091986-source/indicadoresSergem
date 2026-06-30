import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import timedelta
import re
import os

# 1. CONFIGURACIÓN DE LA PÁGINA
st.set_page_config(
    page_title="Tablero Mensajería - Sergem Mensajería",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. INTEGRACIÓN DE CSS (Llamando al archivo styles.css externo)
st.markdown('<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">', unsafe_allow_html=True)

def cargar_css(archivo):
    if os.path.exists(archivo):
        with open(archivo, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        st.warning(f"No se encontró el archivo {archivo}")

cargar_css("styles.css")

# 3. CONTROL DE NAVEGACIÓN (CALLBACKS)
if 'pagina_actual' not in st.session_state:
    st.session_state['pagina_actual'] = 'Inicio'

def cambiar_pagina(nombre_pagina):
    # Validación: Si intenta ir a un tablero sin haber cargado el archivo
    if nombre_pagina != 'Inicio' and 'archivo_cargado' not in st.session_state:
        st.session_state['alerta_archivo'] = True
    else:
        st.session_state['alerta_archivo'] = False
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
        
        # Alerta de validación si intentan navegar sin archivo
        if st.session_state.get('alerta_archivo', False):
            st.warning("⚠️ Para poder continuar, debe cargar previamente el archivo ORIGINAL WIP.")
        
        # Grid de botones para los 4 menús solicitados
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            st.button("📊 Tablero General", on_click=cambiar_pagina, args=('Tablero',))
            st.button("📝 Solicitudes", on_click=cambiar_pagina, args=('Solicitudes',))
        with col_btn2:
            st.button("⏱️ Medición de Tiempos", on_click=cambiar_pagina, args=('Tiempo',))
            st.button("📈 Participación", on_click=cambiar_pagina, args=('Participacion',))
        
        st.markdown("<br><hr>", unsafe_allow_html=True)
        archivo_subido = st.file_uploader("📥 Subir archivo ORIGINAL WIP", type=['xlsx', 'xls', 'csv'])
        if archivo_subido is not None:
            st.session_state['archivo_cargado'] = archivo_subido
            st.session_state['alerta_archivo'] = False # Limpiamos la alerta al cargar el archivo exitosamente
            st.success("¡Archivo cargado en memoria exitosamente! Seleccione un tablero arriba.")

# Si hay un archivo cargado en memoria y estamos en un tablero secundario
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

        # FILTROS SUPERIORES COMUNES
        st.button("🏠 Volver al Menú Principal", on_click=cambiar_pagina, args=('Inicio',))
        st.markdown("""
<div style='background-color: #1D3557; padding: 15px; border-radius: 8px;'>
    <h3 style='color: white !important; margin:0;'>Filtros Globales de Control</h3>
</div><br>
""", unsafe_allow_html=True)
        
        col_f1, col_f2, col_f3, col_f4, col_f5 = st.columns(5)
        
        with col_f1:
            meses = sorted(df['MES'].dropna().unique().tolist()) if 'MES' in df.columns else []
            mes_sel = st.multiselect("Fecha (Mes)", meses, placeholder="Selección múltiple")
        with col_f2:
            ciudades = sorted(df['UNIDAD DE NEGOCIO'].dropna().unique().tolist()) if 'UNIDAD DE NEGOCIO' in df.columns else []
            ciudad_sel = st.multiselect("Ciudad / Sede", ciudades, placeholder="Todas")
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

        # PALETA DE COLORES CORPORATIVA
        paleta_datos = ['#1D3557', '#457B9D', '#A8DADC', '#C1121F', '#F4A261', '#2A9D8F', '#E9C46A']

        # ==========================================================
        # VISTA 1: TABLERO GENERAL (INDICADORES)
        # ==========================================================
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

            with col_graficos:
                if 'MES' in df_filtrado.columns and 'UNIDAD DE NEGOCIO' in df_filtrado.columns:
                    st.markdown("<b>Solicitudes por Fecha y Ciudad</b>", unsafe_allow_html=True)
                    res_mes_ciudad = df_filtrado.groupby(['MES', 'UNIDAD DE NEGOCIO']).size().reset_index(name='Total')
                    fig_combo = px.bar(res_mes_ciudad, x='MES', y='Total', color='UNIDAD DE NEGOCIO', color_discrete_sequence=paleta_datos)
                    fig_combo.update_layout(margin=dict(t=10, b=10, l=10, r=10), plot_bgcolor='white', paper_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(fig_combo, use_container_width=True)

        # ==========================================================
        # VISTA 2: MEDICIÓN DE TIEMPOS
        # ==========================================================
        elif st.session_state['pagina_actual'] == 'Tiempo':
            st.title("⏱️ Análisis Gerencial de Tiempos Operativos")
            if 'TIEMPO_HORAS' in df_filtrado.columns and 'TRAMITE' in df_filtrado.columns:
                col_t1, col_t2 = st.columns(2)
                with col_t1:
                    st.markdown("<b>Horas Totales Invertidas por Tipo de Gestión</b>", unsafe_allow_html=True)
                    res_tiempo = df_filtrado.groupby('TRAMITE')['TIEMPO_HORAS'].sum().reset_index().sort_values(by='TIEMPO_HORAS', ascending=True).tail(10)
                    fig_tramite = px.bar(res_tiempo, x='TIEMPO_HORAS', y='TRAMITE', orientation='h', text=res_tiempo['TIEMPO_HORAS'].apply(lambda x: f"{x:.0f} h"), color='TIEMPO_HORAS', color_continuous_scale='Blues')
                    fig_tramite.update_layout(margin=dict(t=10, b=10, l=10, r=10), plot_bgcolor='white', paper_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(fig_tramite, use_container_width=True)
                
                with col_t2:
                    st.markdown("<b>Evolución del Tiempo Promedio (Horas) por Sede</b>", unsafe_allow_html=True)
                    if 'MES' in df_filtrado.columns:
                        tendencia = df_filtrado.groupby(['MES', 'UNIDAD DE NEGOCIO'])['TIEMPO_HORAS'].mean().reset_index()
                        fig_tend = px.line(tendencia, x='MES', y='TIEMPO_HORAS', color='UNIDAD DE NEGOCIO', markers=True, color_discrete_sequence=paleta_datos)
                        fig_tend.update_layout(margin=dict(t=10, b=10, l=10, r=10), plot_bgcolor='white', paper_bgcolor='rgba(0,0,0,0)')
                        st.plotly_chart(fig_tend, use_container_width=True)
            else:
                st.warning("Faltan las columnas de Tiempo o Trámite para calcular esta vista.")

        # ==========================================================
        # VISTA 3: NUEVO MENÚ - SOLICITUDES (ANÁLISIS DETALLADO)
        # ==========================================================
        elif st.session_state['pagina_actual'] == 'Solicitudes':
            st.title("📝 Análisis Detallado de Volúmenes de Solicitudes")
            
            total_sol = len(df_filtrado)
            colab_unicos = df_filtrado['COLABORADOR'].nunique() if 'COLABORADOR' in df_filtrado.columns else 0
            tramites_unicos = df_filtrado['TRAMITE'].nunique() if 'TRAMITE' in df_filtrado.columns else 0
            
            col_s1, col_s2, col_s3 = st.columns(3)
            with col_s1:
                st.markdown(f'<div class="kpi-card"><div class="kpi-title">📦 Total Servicios Cargados</div><div class="kpi-value">{total_sol:,}</div></div>', unsafe_allow_html=True)
            with col_s2:
                st.markdown(f'<div class="kpi-card"><div class="kpi-title">👥 Repartidores/Colaboradores Activos</div><div class="kpi-value">{colab_unicos}</div></div>', unsafe_allow_html=True)
            with col_s3:
                st.markdown(f'<div class="kpi-card"><div class="kpi-title">📋 Trámites Únicos Operados</div><div class="kpi-value">{tramites_unicos}</div></div>', unsafe_allow_html=True)
                
            st.markdown("<br>", unsafe_allow_html=True)
            col_graf_s1, col_graf_s2 = st.columns(2)
            
            with col_graf_s1:
                st.markdown("<b>Línea de Tendencia: Crecimiento Mensual de Solicitudes</b>", unsafe_allow_html=True)
                if 'MES' in df_filtrado.columns:
                    res_mes = df_filtrado.groupby('MES').size().reset_index(name='Cantidad')
                    fig_mes = px.area(res_mes, x='MES', y='Cantidad', color_discrete_sequence=['#457B9D'])
                    fig_mes.update_layout(margin=dict(t=10, b=10, l=10, r=10), plot_bgcolor='white', paper_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(fig_mes, use_container_width=True)
                    
            with col_graf_s2:
                st.markdown("<b>Distribución Logística por Estado del Servicio</b>", unsafe_allow_html=True)
                if 'ESTADO' in df_filtrado.columns:
                    res_estado = df_filtrado.groupby('ESTADO').size().reset_index(name='Cantidad')
                    fig_estado = px.bar(res_estado, x='Cantidad', y='ESTADO', orientation='h', color='ESTADO', color_discrete_sequence=paleta_datos)
                    fig_estado.update_layout(margin=dict(t=10, b=10, l=10, r=10), plot_bgcolor='white', paper_bgcolor='rgba(0,0,0,0)', showlegend=False)
                    st.plotly_chart(fig_estado, use_container_width=True)
                else:
                    st.info("Columna 'ESTADO' no disponible.")
            
            st.markdown("<br>", unsafe_allow_html=True)
            col_graf_s3, col_graf_s4 = st.columns(2)
            
            with col_graf_s3:
                st.markdown("<b>Top 10 Colaboradores con Mayor Productividad (Servicios)</b>", unsafe_allow_html=True)
                if 'COLABORADOR' in df_filtrado.columns:
                    res_colab = df_filtrado.groupby('COLABORADOR').size().reset_index(name='Solicitudes').sort_values(by='Solicitudes', ascending=False).head(10)
                    fig_colab = px.bar(res_colab, x='Solicitudes', y='COLABORADOR', orientation='h', color='Solicitudes', color_continuous_scale='Reds')
                    fig_colab.update_layout(margin=dict(t=10, b=10, l=10, r=10), plot_bgcolor='white', paper_bgcolor='rgba(0,0,0,0)', yaxis={'categoryorder':'total ascending'})
                    st.plotly_chart(fig_colab, use_container_width=True)
                    
            with col_graf_s4:
                st.markdown("<b>Distribución Absoluta de Servicios por Sede Operativa</b>", unsafe_allow_html=True)
                if 'UNIDAD DE NEGOCIO' in df_filtrado.columns:
                    res_un = df_filtrado.groupby('UNIDAD DE NEGOCIO').size().reset_index(name='Solicitudes').sort_values(by='Solicitudes', ascending=False)
                    fig_un = px.bar(res_un, x='UNIDAD DE NEGOCIO', y='Solicitudes', color='UNIDAD DE NEGOCIO', color_discrete_sequence=paleta_datos)
                    fig_un.update_layout(margin=dict(t=10, b=10, l=10, r=10), plot_bgcolor='white', paper_bgcolor='rgba(0,0,0,0)', showlegend=False)
                    st.plotly_chart(fig_un, use_container_width=True)

        # ==========================================================
        # VISTA 4: NUEVO MENÚ - PARTICIPACIÓN (ANÁLISIS PORCENTUAL)
        # ==========================================================
        elif st.session_state['pagina_actual'] == 'Participacion':
            st.title("📈 Análisis de Cuotas de Participación y Distribución")
            
            col_p1, col_p2 = st.columns(2)
            
            with col_p1:
                st.markdown("<b>Participación Porcentual por Unidad de Negocio (Sede)</b>", unsafe_allow_html=True)
                if 'UNIDAD DE NEGOCIO' in df_filtrado.columns:
                    res_part_un = df_filtrado['UNIDAD DE NEGOCIO'].value_counts().reset_index()
                    res_part_un.columns = ['Sede', 'Total']
                    fig_part_un = px.pie(res_part_un, values='Total', names='Sede', hole=0.4, color_discrete_sequence=paleta_datos)
                    fig_part_un.update_layout(margin=dict(t=20, b=20, l=20, r=20))
                    st.plotly_chart(fig_part_un, use_container_width=True)
                    
            with col_p2:
                st.markdown("<b>Participación de Mercado por Tipo de Trámite (Top 7)</b>", unsafe_allow_html=True)
                if 'TRAMITE' in df_filtrado.columns:
                    res_part_tr = df_filtrado['TRAMITE'].value_counts().reset_index()
                    res_part_tr.columns = ['Trámite', 'Total']
                    if len(res_part_tr) > 7:
                        top_tr = res_part_tr.head(7)
                        otros_tr = pd.DataFrame([{'Trámite': 'Otros Trámites', 'Total': res_part_tr['Total'].iloc[7:].sum()}])
                        res_part_tr = pd.concat([top_tr, otros_tr], ignore_index=True)
                    
                    fig_part_tr = px.pie(res_part_tr, values='Total', names='Trámite', hole=0.4, color_discrete_sequence=paleta_datos)
                    fig_part_tr.update_layout(margin=dict(t=20, b=20, l=20, r=20))
                    st.plotly_chart(fig_part_tr, use_container_width=True)
                    
            st.markdown("<br>", unsafe_allow_html=True)
            col_p3, col_p4 = st.columns(2)
            
            with col_p3:
                st.markdown("<b>Volumen de Operación Distribuido por Día de la Semana</b>", unsafe_allow_html=True)
                if 'DIA_SEMANA' in df_filtrado.columns:
                    res_part_dias = df_filtrado['DIA_SEMANA'].value_counts().reset_index()
                    res_part_dias.columns = ['Día', 'Total']
                    fig_part_dias = px.bar(res_part_dias, x='Día', y='Total', color='Día', color_discrete_sequence=paleta_datos)
                    fig_part_dias.update_layout(margin=dict(t=10, b=10, l=10, r=10), plot_bgcolor='white', paper_bgcolor='rgba(0,0,0,0)', showlegend=False)
                    st.plotly_chart(fig_part_dias, use_container_width=True)
                    
            with col_p4:
                st.markdown("<b>Treemap: Concentración de Demanda por Centro de Costos</b>", unsafe_allow_html=True)
                if 'CENTRO DE COSTOS' in df_filtrado.columns:
                    res_part_cc = df_filtrado.groupby('CENTRO DE COSTOS').size().reset_index(name='Total')
                    fig_part_tree = px.treemap(res_part_cc, path=['CENTRO DE COSTOS'], values='Total', color='Total', color_continuous_scale='Blues')
                    fig_part_tree.update_layout(margin=dict(t=0, b=0, l=0, r=0), paper_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(fig_part_tree, use_container_width=True)

    except Exception as e:
        st.error(f"Error procesando el archivo. Verifique el formato. Detalle: {e}")
