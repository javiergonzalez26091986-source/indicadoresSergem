import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# 1. CONFIGURACIÓN DE LA PÁGINA
st.set_page_config(
    page_title="Tablero Mensajería - Constructora Bolívar",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .stApp { background-color: #F8F9FA; }
    h1, h2, h3 { color: #008037; } 
    .st-emotion-cache-1wivap2 { background-color: #FFC20E; } 
    </style>
""", unsafe_allow_html=True)

st.title("📊 Tablero Gerencial de Mensajería")
st.markdown("Cargue el archivo **ORIGINAL WIP** para visualizar los indicadores de efectividad.")

# 2. CARGA DEL ARCHIVO EN MEMORIA
archivo_subido = st.file_uploader("Seleccione el archivo exportado (.csv o .xlsx)", type=['xlsx', 'xls', 'csv'])

if archivo_subido is not None:
    try:
        # Validar el tipo de archivo
        if archivo_subido.name.endswith('.csv'):
            # Se usa sep=',' pero si el CSV viene con punto y coma en algunos equipos, se puede cambiar a sep=';'
            df = pd.read_csv(archivo_subido, sep=',', encoding='utf-8', on_bad_lines='skip')
        else:
            df = pd.read_excel(archivo_subido)
            
        # Estandarizar nombres de columnas eliminando espacios extra
        df.columns = df.columns.str.strip()
        
        # 3. PROCESAMIENTO DE DATOS EXACTOS DEL ARCHIVO
        # Manejo de Fechas
        if 'FECHA DE CREACION' in df.columns:
            df['FECHA DE CREACION'] = pd.to_datetime(df['FECHA DE CREACION'], errors='coerce')
            df = df.dropna(subset=['FECHA DE CREACION']) # Eliminar filas sin fecha válida
            
            # Mapeo de días en español
            dias_esp = {'Monday':'Lunes', 'Tuesday':'Martes', 'Wednesday':'Miércoles', 
                        'Thursday':'Jueves', 'Friday':'Viernes', 'Saturday':'Sábado', 'Sunday':'Domingo'}
            df['DIA_SEMANA'] = df['FECHA DE CREACION'].dt.day_name().map(dias_esp)
            df['MES'] = df['FECHA DE CREACION'].dt.to_period('M').astype(str)

        # 4. FILTROS LATERALES
        st.sidebar.header("Filtros Globales")
        
        ciudades = df['UNIDAD DE NEGOCIO'].dropna().unique().tolist() if 'UNIDAD DE NEGOCIO' in df.columns else []
        ciudad_sel = st.sidebar.multiselect("Seleccione Unidad de Negocio", ciudades, default=ciudades)
        
        meses = sorted(df['MES'].dropna().unique().tolist()) if 'MES' in df.columns else []
        mes_sel = st.sidebar.multiselect("Seleccione Mes", meses, default=meses)

        centros = sorted(df['CENTRO DE COSTOS'].dropna().astype(str).unique().tolist()) if 'CENTRO DE COSTOS' in df.columns else []
        centro_sel = st.sidebar.multiselect("Seleccione Centro de Costos", centros, default=centros)

        # Aplicar filtros
        df_filtrado = df.copy()
        if ciudad_sel:
            df_filtrado = df_filtrado[df_filtrado['UNIDAD DE NEGOCIO'].isin(ciudad_sel)]
        if mes_sel:
            df_filtrado = df_filtrado[df_filtrado['MES'].isin(mes_sel)]
        if centro_sel:
            df_filtrado = df_filtrado[df_filtrado['CENTRO DE COSTOS'].astype(str).isin(centro_sel)]

        # 5. CÁLCULO DE INDICADORES (KPIs)
        st.markdown("---")
        col1, col2, col3 = st.columns(3)

        total_solicitudes = len(df_filtrado)
        
        # Efectividad: Excluyendo cancelados, rechazados o fallidos
        if 'ESTADO' in df_filtrado.columns:
            # Puedes ajustar las palabras exactas que indican un servicio no efectivo
            no_efectivos = df_filtrado[df_filtrado['ESTADO'].str.contains('Fallido|Cancelado|Rechazado', case=False, na=False)]
            total_no_efectivos = len(no_efectivos)
            efectividad = ((total_solicitudes - total_no_efectivos) / total_solicitudes) * 100 if total_solicitudes > 0 else 0
        else:
            efectividad = 0

        # Promedio Diario (Días hábiles)
        if 'FECHA DE CREACION' in df_filtrado.columns and not df_filtrado.empty:
            fecha_min = df_filtrado['FECHA DE CREACION'].min()
            fecha_max = df_filtrado['FECHA DE CREACION'].max()
            dias_habiles = np.busday_count(fecha_min.date(), fecha_max.date()) + 1 
            promedio_diario = total_solicitudes / dias_habiles if dias_habiles > 0 else 0
        else:
            promedio_diario = 0

        col1.metric("📦 Total Solicitudes", f"{total_solicitudes:,}")
        col2.metric("🎯 Efectividad Operativa", f"{efectividad:.1f}%")
        col3.metric("📅 Promedio Solicitudes / Día Hábil", f"{promedio_diario:.1f}")

        st.markdown("---")

        # 6. GRÁFICOS GERENCIALES
        col_graf1, col_graf2 = st.columns([2, 1])

        with col_graf1:
            st.subheader("Volumen por Mes y Unidad de Negocio")
            if 'MES' in df_filtrado.columns and 'UNIDAD DE NEGOCIO' in df_filtrado.columns:
                resumen_volumen = df_filtrado.groupby(['MES', 'UNIDAD DE NEGOCIO']).size().reset_index(name='Total')
                fig_barras = px.bar(resumen_volumen, x='MES', y='Total', color='UNIDAD DE NEGOCIO',
                                    barmode='group', color_discrete_sequence=['#008037', '#FFC20E', '#808080'])
                st.plotly_chart(fig_barras, use_container_width=True)

        with col_graf2:
            st.subheader("Distribución por Día")
            if 'DIA_SEMANA' in df_filtrado.columns:
                resumen_dias = df_filtrado['DIA_SEMANA'].value_counts().reset_index()
                resumen_dias.columns = ['Día', 'Total']
                fig_dona = px.pie(resumen_dias, values='Total', names='Día', hole=0.5,
                                  color_discrete_sequence=px.colors.sequential.Greens_r)
                st.plotly_chart(fig_dona, use_container_width=True)

        st.subheader("Distribución por Centro de Costos")
        if 'CENTRO DE COSTOS' in df_filtrado.columns:
            resumen_cc = df_filtrado.groupby('CENTRO DE COSTOS').size().reset_index(name='Total')
            # Filtrar los que tienen un volumen representativo para no saturar el gráfico
            resumen_cc = resumen_cc[resumen_cc['Total'] > 1] 
            fig_tree = px.treemap(resumen_cc, path=['CENTRO DE COSTOS'], values='Total',
                                  color='Total', color_continuous_scale='Greens')
            st.plotly_chart(fig_tree, use_container_width=True)

    except Exception as e:
        st.error(f"Ocurrió un error al procesar el archivo. Detalle técnico: {e}")
else:
    st.info("Esperando a que subas el archivo WIP para generar el tablero gerencial...")
