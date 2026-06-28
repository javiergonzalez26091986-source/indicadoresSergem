import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from datetime import timedelta

# 1. CONFIGURACIÓN DE LA PÁGINA
st.set_page_config(
    page_title="Tablero Mensajería - Constructora Bolívar",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. ESTILOS CSS PERSONALIZADOS
st.markdown("""
    <style>
    .stApp { background-color: #EAF4EC; } /* Fondo verde clarito de la imagen */
    
    /* Estilo para la tarjeta verde de bienvenida */
    .tarjeta-verde {
        background-color: #008037;
        color: white;
        padding: 40px;
        border-radius: 10px;
        height: 100%;
        min-height: 400px;
    }
    
    /* Estilo para los botones del menú simulando la imagen */
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

# 3. CONTROL DE NAVEGACIÓN (Para moverse entre pantallas)
if 'pagina_actual' not in st.session_state:
    st.session_state['pagina_actual'] = 'Inicio'

def cambiar_pagina(nombre_pagina):
    st.session_state['pagina_actual'] = nombre_pagina

# 4. CARGA Y PROCESAMIENTO DE DATOS (Panel Lateral)
with st.sidebar:
    if st.session_state['pagina_actual'] != 'Inicio':
        if st.button("🏠 Volver al Menú Principal"):
            cambiar_pagina('Inicio')
        st.markdown("---")
        
    st.header("1. Cargar Datos")
    archivo_subido = st.file_uploader("Subir archivo ORIGINAL WIP", type=['xlsx', 'xls', 'csv'])
    
    df_filtrado = pd.DataFrame() # DataFrame vacío por defecto
    
    if archivo_subido is not None:
        try:
            if archivo_subido.name.endswith('.csv'):
                df = pd.read_csv(archivo_subido, sep=';', encoding='utf-8', on_bad_lines='skip')
            else:
                df = pd.read_excel(archivo_subido)
                
            df.columns = df.columns.str.strip().str.upper()
            
            if 'FECHA DE CREACION' in df.columns:
                df['FECHA DE CREACION'] = pd.to_datetime(df['FECHA DE CREACION'], errors='coerce')
                df = df.dropna(subset=['FECHA DE CREACION'])
                dias_esp = {'Monday':'Lunes', 'Tuesday':'Martes', 'Wednesday':'Miércoles', 
                            'Thursday':'Jueves', 'Friday':'Viernes', 'Saturday':'Sábado', 'Sunday':'Domingo'}
                df['DIA_SEMANA'] = df['FECHA DE CREACION'].dt.day_name().map(dias_esp)
                df['MES'] = df['FECHA DE CREACION'].dt.to_period('M').astype(str)
                df['AÑO'] = df['FECHA DE CREACION'].dt.year.astype(str)

            # Filtros Globales que aplican a todas las vistas
            st.header("2. Filtros Globales")
            
            ciudades = df['UNIDAD DE NEGOCIO'].dropna().unique().tolist() if 'UNIDAD DE NEGOCIO' in df.columns else []
            ciudad_sel = st.multiselect("Ciudad / Unidad de Negocio", ciudades, default=ciudades)
            
            meses = sorted(df['MES'].dropna().unique().tolist()) if 'MES' in df.columns else []
            mes_sel = st.multiselect("Meses", meses, default=meses)

            # Aplicar filtros
            df_filtrado = df.copy()
            if ciudad_sel:
                df_filtrado = df_filtrado[df_filtrado['UNIDAD DE NEGOCIO'].isin(ciudad_sel)]
            if mes_sel:
                df_filtrado = df_filtrado[df_filtrado['MES'].isin(mes_sel)]

        except Exception as e:
            st.error(f"Error procesando el archivo: {e}")

# ==========================================
# VISTA 1: MENÚ PRINCIPAL (Idéntico a la imagen)
# ==========================================
if st.session_state['pagina_actual'] == 'Inicio':
    st.markdown("<br><br>", unsafe_allow_html=True)
    col_izq, col_espacio, col_der = st.columns([1.2, 0.2, 1.5])
    
    with col_izq:
        st.markdown("""
            <div class="tarjeta-verde">
                <h2 style="color: white; text-align: center;">SERGEM</h2>
                <hr style="border-top: 2px solid white;">
                <h1 style="color: white; font-size: 50px;">Hola</h1>
                <p style="font-size: 18px; line-height: 1.6;">
                    Esta Herramienta Tecnológica de trabajo colaborativo podrás encontrar toda la 
                    información relacionada a las solicitudes y tiempos en los temas de mensajería 
                    y sus colaboradores.
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
# CÁLCULOS MAESTROS PARA LAS VISTAS (Según Audio 2 y 3)
# ==========================================
elif not df_filtrado.empty:
    # 1. Total de Vueltas
    total_solicitudes = len(df_filtrado)
    
    # 2. Días Hábiles (LUNES A SÁBADO: '1111110')
    dias_habiles = 0
    if 'FECHA DE CREACION' in df_filtrado.columns and total_solicitudes > 0:
        fecha_min = df_filtrado['FECHA DE CREACION'].min().date()
        fecha_max = df_filtrado['FECHA DE CREACION'].max().date()
        # Se suma 1 día al max para que np.busday_count lo incluya en el rango
        dias_habiles = np.busday_count(fecha_min, fecha_max + timedelta(days=1), weekmask='1111110')
    
    # 3. Eficacia (Excluyendo "Fallido")
    eficacia = 0
    if 'ESTADO' in df_filtrado.columns and total_solicitudes > 0:
        fallidos = df_filtrado['ESTADO'].str.contains('Fallido', case=False, na=False).sum()
        eficacia = ((total_solicitudes - fallidos) / total_solicitudes) * 100
        
    # 4. Productividad Mensajeros (Total / Días / Número de mensajeros)
    promedio_diario = 0
    productividad_mensajero_dia = 0
    if dias_habiles > 0:
        promedio_diario = total_solicitudes / dias_habiles
        if 'COLABORADOR' in df_filtrado.columns:
            num_mensajeros = df_filtrado['COLABORADOR'].nunique()
            if num_mensajeros > 0:
                productividad_mensajero_dia = promedio_diario / num_mensajeros

    # ==========================================
    # VISTA 2: INDICADORES (KPIs Gerenciales)
    # ==========================================
    if st.session_state['pagina_actual'] == 'Indicadores':
        st.title("📊 Indicadores Generales de Productividad")
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("📦 Total Vueltas", f"{total_solicitudes:,}")
        col2.metric("🎯 Eficacia Operativa", f"{eficacia:.1f}%", help="Porcentaje de diligencias NO fallidas.")
        col3.metric("📅 Días Laborados (Lun-Sáb)", f"{dias_habiles}")
        col4.metric("🛵 Promedio Vueltas / Día", f"{promedio_diario:.1f}")
        
        st.markdown("---")
        st.subheader("Productividad por Colaborador")
        st.info(f"Cada mensajero realiza en promedio **{productividad_mensajero_dia:.1f} vueltas diarias**.")
        
        if 'COLABORADOR' in df_filtrado.columns:
            resumen_mensajeros = df_filtrado.groupby('COLABORADOR').size().reset_index(name='Total Vueltas')
            resumen_mensajeros['Vueltas / Día'] = resumen_mensajeros['Total Vueltas'] / dias_habiles
            # Ordenar de mayor a menor
            resumen_mensajeros = resumen_mensajeros.sort_values(by='Total Vueltas', ascending=False)
            
            fig_colab = px.bar(resumen_mensajeros, x='COLABORADOR', y='Total Vueltas', text='Total Vueltas',
                               color='Total Vueltas', color_continuous_scale='Greens',
                               title="Volumen Total por Mensajero")
            st.plotly_chart(fig_colab, use_container_width=True)

    # ==========================================
    # VISTA 3: SOLICITUDES
    # ==========================================
    elif st.session_state['pagina_actual'] == 'Solicitudes':
        st.title("🛵 Comportamiento de Solicitudes")
        if 'MES' in df_filtrado.columns and 'UNIDAD DE NEGOCIO' in df_filtrado.columns:
            resumen_volumen = df_filtrado.groupby(['MES', 'UNIDAD DE NEGOCIO']).size().reset_index(name='Total')
            fig_barras = px.bar(resumen_volumen, x='MES', y='Total', color='UNIDAD DE NEGOCIO',
                                barmode='group', color_discrete_sequence=['#008037', '#FFC20E', '#808080'],
                                title="Solicitudes por Mes y Sede")
            st.plotly_chart(fig_barras, use_container_width=True)

    # ==========================================
    # VISTA 4: PARTICIPACIÓN
    # ==========================================
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
                resumen_cc = resumen_cc[resumen_cc['Total'] > 1]
                fig_tree = px.treemap(resumen_cc, path=['CENTRO DE COSTOS'], values='Total',
                                      color='Total', color_continuous_scale='Greens',
                                      title="Volumen por Centro de Costos")
                st.plotly_chart(fig_tree, use_container_width=True)

    # ==========================================
    # VISTA 5: TIEMPO
    # ==========================================
    elif st.session_state['pagina_actual'] == 'Tiempo':
        st.title("⏱️ Medición de Tiempos")
        st.write("Doña Yesenia mencionó: *'tenemos que llegar a medir el tiempo de cada trámite, que haga una gráfica de dónde es que se va la mayor cantidad de tiempo'*.")
        
        # Validación de columna de tiempos
        columnas_tiempo = [col for col in df_filtrado.columns if 'TIEMPO' in col or 'HORA' in col]
        if columnas_tiempo:
            st.success(f"Se detectaron columnas para analizar tiempos: {', '.join(columnas_tiempo)}. Aquí podremos cruzar Trámite vs Tiempo.")
            # Aquí irá la lógica futura cuando confirmemos el nombre de la columna de tiempos en el excel
        else:
            st.warning("Aún no se ha detectado una columna de 'TIEMPOS' en el reporte para generar esta gráfica. Una vez confirmemos cómo SERGEM mide la duración en el Excel, activaremos este panel.")

elif st.session_state['pagina_actual'] != 'Inicio':
    st.info("👈 Por favor carga el archivo **ORIGINAL WIP** en el panel izquierdo para ver esta sección.")
