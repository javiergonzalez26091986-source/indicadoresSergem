import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# 1. CONFIGURACIÓN DE LA PÁGINA (Colores y estilo)
st.set_page_config(
    page_title="Tablero Mensajería - Constructora Bolívar",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados para usar los colores de la marca
st.markdown("""
    <style>
    .stApp { background-color: #F8F9FA; }
    h1, h2, h3 { color: #008037; } /* Verde Constructora Bolívar */
    .st-emotion-cache-1wivap2 { background-color: #FFC20E; } /* Acentos Amarillos */
    </style>
""", unsafe_allow_html=True)

st.title("📊 Tablero Gerencial de Mensajería")
st.markdown("Cargue el archivo **ORIGINAL WIP** para visualizar los indicadores de efectividad.")

# 2. CARGA DEL ARCHIVO EN MEMORIA
archivo_subido = st.file_uploader("Seleccione el archivo Excel (.xlsx o .xls)", type=['xlsx', 'xls', 'csv'])

if archivo_subido is not None:
    # 3. LECTURA Y PROCESAMIENTO DE DATOS
    try:
        # Validar si es Excel o CSV
        if archivo_subido.name.endswith('.csv'):
            df = pd.read_csv(archivo_subido)
        else:
            df = pd.read_excel(archivo_subido)
            
        # IMPORTANTE: Aquí debes poner los nombres EXACTOS de las columnas del Excel de Doña Yesenia
        # Ejemplo de estandarización de nombres (Asumiendo algunas columnas)
        df.columns = df.columns.str.strip().str.upper() # Limpiar espacios y mayúsculas
        
        # Asegurarnos de que la columna de fecha sea formato DateTime
        # Cambia 'FECHA' por el nombre real de tu columna
        if 'FECHA' in df.columns:
            df['FECHA'] = pd.to_datetime(df['FECHA'], errors='coerce')
            df['DIA_SEMANA'] = df['FECHA'].dt.day_name()
            df['MES'] = df['FECHA'].dt.to_period('M').astype(str)

        # 4. FILTROS LATERALES (Sidebar)
        st.sidebar.header("Filtros Globales")
        
        # Filtro de Ciudad (Separar Cali de Nacional, como en el audio)
        ciudades = df['CIUDAD'].dropna().unique().tolist() if 'CIUDAD' in df.columns else []
        ciudad_sel = st.sidebar.multiselect("Seleccione Ciudad/Sede", ciudades, default=ciudades)
        
        # Filtro de Mes
        meses = df['MES'].dropna().unique().tolist() if 'MES' in df.columns else []
        mes_sel = st.sidebar.multiselect("Seleccione Mes", meses, default=meses)

        # APLICAR FILTROS AL DATAFRAME
        df_filtrado = df.copy()
        if 'CIUDAD' in df.columns and ciudad_sel:
            df_filtrado = df_filtrado[df_filtrado['CIUDAD'].isin(ciudad_sel)]
        if 'MES' in df.columns and mes_sel:
            df_filtrado = df_filtrado[df_filtrado['MES'].isin(mes_sel)]

        # 5. CÁLCULO DE INDICADORES (KPIs)
        st.markdown("---")
        col1, col2, col3 = st.columns(3)

        # A. Total de Solicitudes
        total_solicitudes = len(df_filtrado)
        
        # B. Efectividad (Excluyendo 'Fallidos')
        # Cambia 'ESTADO' y 'FALLIDO' por los valores reales del Excel
        if 'ESTADO' in df_filtrado.columns:
            fallidos = len(df_filtrado[df_filtrado['ESTADO'].str.contains('FALLIDO', case=False, na=False)])
            efectividad = ((total_solicitudes - fallidos) / total_solicitudes) * 100 if total_solicitudes > 0 else 0
        else:
            efectividad = 100 # Default si no hay columna estado

        # C. Promedio Diario (Usando días hábiles)
        if 'FECHA' in df_filtrado.columns and not df_filtrado.empty:
            fecha_min = df_filtrado['FECHA'].min()
            fecha_max = df_filtrado['FECHA'].max()
            # np.busday_count cuenta días de Lunes a Viernes (excluye fines de semana)
            dias_habiles = np.busday_count(fecha_min.date(), fecha_max.date()) + 1 
            promedio_diario = total_solicitudes / dias_habiles if dias_habiles > 0 else 0
        else:
            promedio_diario = 0

        # Mostrar KPIs en pantalla
        col1.metric("📦 Total Solicitudes", f"{total_solicitudes:,}")
        col2.metric("🎯 Efectividad (Excluyendo Fallidos)", f"{efectividad:.1f}%")
        col3.metric("📅 Promedio Solicitudes / Día Hábil", f"{promedio_diario:.1f}")

        st.markdown("---")

        # 6. GRÁFICOS GERENCIALES (Basados en las imágenes)
        col_graf1, col_graf2 = st.columns([2, 1])

        # Gráfico 1: Barras de Volumen por Ciudad/Mes
        with col_graf1:
            st.subheader("Volumen de Solicitudes por Mes y Ciudad")
            if 'MES' in df_filtrado.columns and 'CIUDAD' in df_filtrado.columns:
                resumen_volumen = df_filtrado.groupby(['MES', 'CIUDAD']).size().reset_index(name='Total')
                fig_barras = px.bar(resumen_volumen, x='MES', y='Total', color='CIUDAD',
                                    barmode='group', color_discrete_sequence=['#008037', '#FFC20E', '#808080'])
                st.plotly_chart(fig_barras, use_container_width=True)
            else:
                st.info("No se encontraron las columnas MES y CIUDAD para esta gráfica.")

        # Gráfico 2: Dona de Días de la semana
        with col_graf2:
            st.subheader("Concentración por Día")
            if 'DIA_SEMANA' in df_filtrado.columns:
                # Traducir días al español si es necesario o usar el conteo directo
                resumen_dias = df_filtrado['DIA_SEMANA'].value_counts().reset_index()
                resumen_dias.columns = ['Día', 'Total']
                fig_dona = px.pie(resumen_dias, values='Total', names='Día', hole=0.5,
                                  color_discrete_sequence=px.colors.sequential.Greens_r)
                st.plotly_chart(fig_dona, use_container_width=True)

        # Gráfico 3: Treemap (Mapa de Árbol) por Centro de Costos
        st.subheader("Distribución por Centro de Costos")
        if 'CENTRO_COSTO' in df_filtrado.columns:
            resumen_cc = df_filtrado.groupby('CENTRO_COSTO').size().reset_index(name='Total')
            fig_tree = px.treemap(resumen_cc, path=['CENTRO_COSTO'], values='Total',
                                  color='Total', color_continuous_scale='Greens')
            st.plotly_chart(fig_tree, use_container_width=True)
        else:
            st.info("Falta la columna CENTRO_COSTO (o similar) en el archivo para generar este mapa.")

        # 7. VISUALIZACIÓN DE LA TABLA LIMPIA (Opcional)
        with st.expander("Ver tabla de datos detallada"):
            st.dataframe(df_filtrado.head(100)) # Mostramos los primeros 100 para no saturar

    except Exception as e:
        st.error(f"Ocurrió un error al procesar el archivo. Verifique la estructura. Detalle: {e}")

else:
    st.info("Esperando a que subas el archivo Excel para calcular los indicadores...")
