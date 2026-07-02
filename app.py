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
import holidays

# 1. CONFIGURACIÓN DE LA PÁGINA
st.set_page_config(
    page_title="Tablero Operativo - Sergem", 
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
# 4. PROCESAMIENTO EN CACHÉ (OPTIMIZADO)
# ==========================================
@st.cache_data(ttl=3600, show_spinner=False)
def obtener_y_procesar_datos():
    try:
        req = requests.get(URL_APPSCRIPT, timeout=60)
        if req.status_code == 200:
            datos = req.json()
            if datos and len(datos) > 0:
                df = pd.DataFrame(datos)
                df.columns = df.columns.str.strip().str.upper()
                
                # --- NUEVA LÓGICA: NORMALIZAR NOMBRES DE COLABORADORES ---
                for col_n in ['COLABORADOR', 'MENSAJERO', 'RESPONSABLE', 'USUARIO']:
                    if col_n in df.columns:
                        df[col_n] = df[col_n].fillna('')
                        # strip elimina espacios a los lados, title pone la primera en mayúscula, 
                        # y join(split()) elimina espacios dobles entre nombres.
                        df[col_n] = df[col_n].astype(str).str.strip().str.title().apply(lambda x: ' '.join(x.split()))
                        df[col_n] = df[col_n].replace('Nan', '') 
                # ---------------------------------------------------------

                if 'FECHA DE CREACION' in df.columns:
                    df['FECHA DE CREACION'] = pd.to_datetime(df['FECHA DE CREACION'], dayfirst=True, errors='coerce')
                    df['FECHA DE CREACION'] = df['FECHA DE CREACION'].fillna(pd.Timestamp.now())
                    meses_es = {1:'Enero', 2:'Febrero', 3:'Marzo', 4:'Abril', 5:'Mayo', 6:'Junio', 7:'Julio', 8:'Agosto', 9:'Septiembre', 10:'Octubre', 11:'Noviembre', 12:'Diciembre'}
                    df['AÑO'] = df['FECHA DE CREACION'].dt.year.astype(str)
                    df['MES_NUM'] = df['FECHA DE CREACION'].dt.month
                    df['MES_NOMBRE'] = df['MES_NUM'].map(meses_es).fillna("Desconocido")
                    
                    df['SEMANA_NUM'] = df['FECHA DE CREACION'].dt.isocalendar().week
                    df['SEMANA'] = "Semana " + df['SEMANA_NUM'].astype(str).str.zfill(2)
                    
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
                    df['CANTIDAD_DESTINOS'] = df['TIPO DE SERVICIO'].astype(str).str.extract(r'(\d+)')[0].fillna(1).astype(int)
                elif 'UNIDAD DE NEGOCIO' in df.columns:
                    df['CIUDAD_REAL'] = df['UNIDAD DE NEGOCIO'].apply(extraer_ciudad)
                    df['CANTIDAD_DESTINOS'] = 1
                else:
                    df['CIUDAD_REAL'] = 'Sede Central'
                    df['CANTIDAD_DESTINOS'] = 1
                    
                return df
    except Exception as e:
        st.error(f"Error cargando la base de datos remota: {e}")
    return pd.DataFrame()

df = obtener_y_procesar_datos()

# ==========================================
# 5. CONFIGURACIÓN (Panel Lateral)
# ==========================================
with st.sidebar:
    st.markdown("### ■ Configuración Operativa")
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
    st.markdown("### ■ Actualizar Base de Datos")
    archivo_subido = st.file_uploader("Subir archivo de origen", type=['xlsx', 'xls', 'csv'])
    
    if archivo_subido is not None and st.button("Procesar y Subir"):
        if archivo_subido.name.endswith('.csv'): df_nuevo = pd.read_csv(archivo_subido, sep=';', encoding='utf-8')
        else: df_nuevo = pd.read_excel(archivo_subido)
        
        df_nuevo.columns = df_nuevo.columns.str.strip().str.upper()
        
        if '#WIP' in df_nuevo.columns and not df.empty and '#WIP' in df.columns:
            wips_existentes = set(df['#WIP'].astype(str).str.strip())
            df_nuevo['#WIP_TEMP'] = df_nuevo['#WIP'].astype(str).str.strip()
            
            registros_originales = len(df_nuevo)
            df_nuevo = df_nuevo[~df_nuevo['#WIP_TEMP'].isin(wips_existentes)]
            df_nuevo = df_nuevo.drop(columns=['#WIP_TEMP'])
            
            registros_nuevos = len(df_nuevo)
            registros_omitidos = registros_originales - registros_nuevos
            
            if registros_nuevos == 0:
                st.warning(f"⚠️ Los {registros_originales} registros del archivo ya existen en la base de datos. No hay duplicados que subir.")
                st.stop()
            elif registros_omitidos > 0:
                st.info(f"ℹ️ Se evitaron {registros_omitidos} duplicados. Subiendo únicamente {registros_nuevos} registros nuevos.")
        elif '#WIP' not in df_nuevo.columns:
            st.warning("⚠️ El archivo subido no contiene la columna '#WIP'. Se subirán los datos sin validar duplicados.")

        df_nuevo = df_nuevo.fillna("") 
        df_nuevo = df_nuevo.astype(str)
        
        total_filas = len(df_nuevo)
        tamano_lote = 500 
        
        st.markdown("Sincronizando registros nuevos...")
        barra_progreso = st.progress(0)
        
        exito = True
        for i in range(0, total_filas, tamano_lote):
            lote = df_nuevo.iloc[i:i+tamano_lote]
            json_str = lote.to_json(orient='records')
            payload_limpio = json.loads(json_str)
            try:
                respuesta = requests.post(URL_APPSCRIPT, json=payload_limpio)
                if respuesta.status_code not in [200, 302]:
                    exito = False; break
            except Exception as e:
                exito = False; break
            barra_progreso.progress(min(1.0, (i + tamano_lote) / total_filas))
            time.sleep(0.5)
        
        if exito:
            st.cache_data.clear()
            st.success("Base de datos sincronizada exitosamente.")
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
            <h1 style="font-size: 50px; font-weight: 800;">Bienvenido</h1>
            <p style="font-size: 18px; line-height: 1.6; opacity: 0.95;">Tablero de control y medición de eficiencia operativa.</p>
        </div>
        """, unsafe_allow_html=True)
        
    with col_der:
        st.markdown("<h2 style='text-align: center; margin-top: 0px; margin-bottom: 25px; font-size: 34px; font-weight: 700;'>Menú Principal</h2>", unsafe_allow_html=True)
        if df.empty:
            st.warning("La base de datos se encuentra vacía. Cargue un archivo en el panel de configuración.")
        else:
            st.button("► Tablero General", on_click=cambiar_pagina, args=('Tablero',))
            st.markdown("<div style='margin-bottom: 14px;'></div>", unsafe_allow_html=True)
            st.button("► Volúmenes de Solicitud", on_click=cambiar_pagina, args=('Solicitudes',))
            st.markdown("<div style='margin-bottom: 14px;'></div>", unsafe_allow_html=True)
            st.button("► Medición de Tiempos", on_click=cambiar_pagina, args=('Tiempo',))
            st.markdown("<div style='margin-bottom: 14px;'></div>", unsafe_allow_html=True)
            st.button("► Cuotas de Participación", on_click=cambiar_pagina, args=('Participacion',))
            st.markdown("<div style='margin-bottom: 14px;'></div>", unsafe_allow_html=True)
            st.button("► Análisis de Colaboradores", on_click=cambiar_pagina, args=('Mensajeros',))

elif not df.empty and st.session_state['pagina_actual'] != 'Inicio':
    st.button("◄ Volver al Menú Principal", on_click=cambiar_pagina, args=('Inicio',))
    st.markdown("<div style='background-color: #99C2E2; padding: 15px; border-radius: 8px;'><h3 style='color: #FFFFFF !important; margin:0; font-weight:700;'>Filtros Globales de Control</h3></div><br>", unsafe_allow_html=True)
    
    col_f0, col_f1, col_sem, col_f2, col_f3, col_f4 = st.columns(6)
    
    with col_f0: 
        ano_sel = st.multiselect("Año", sorted(df['AÑO'].dropna().unique()), default=sorted(df['AÑO'].dropna().unique()))
    
    df_temp_ano = df[df['AÑO'].isin(ano_sel)] if ano_sel else df
    
    with col_f1: 
        meses_disp = df_temp_ano[['MES_NUM', 'MES_NOMBRE']].dropna().drop_duplicates().sort_values('MES_NUM')['MES_NOMBRE'].tolist()
        mes_sel = st.multiselect("Mes", meses_disp, placeholder="Todos")
        
    df_temp_mes = df_temp_ano[df_temp_ano['MES_NOMBRE'].isin(mes_sel)] if mes_sel else df_temp_ano
    
    with col_sem: 
        semanas_disp = sorted(df_temp_mes['SEMANA'].dropna().unique()) if 'SEMANA' in df.columns else []
        semana_sel = st.multiselect("Semana", semanas_disp, placeholder="Todas")
        
    with col_f2: 
        ciudad_sel = st.multiselect("Ciudad / Sede", sorted(df['CIUDAD_REAL'].dropna().unique()), placeholder="Todas")
        
    with col_f3: 
        centro_sel = st.multiselect("Centro de Costos", sorted(df['CENTRO DE COSTOS'].dropna().astype(str).unique()) if 'CENTRO DE COSTOS' in df.columns else [], placeholder="Todos")
        
    with col_f4: 
        tramite_sel = st.multiselect("Trámite", sorted(df['TRAMITE'].dropna().unique()) if 'TRAMITE' in df.columns else [], placeholder="Todos")

    df_filtrado = df.copy()
    if ano_sel: df_filtrado = df_filtrado[df_filtrado['AÑO'].isin(ano_sel)]
    if mes_sel: df_filtrado = df_filtrado[df_filtrado['MES_NOMBRE'].isin(mes_sel)]
    if semana_sel and 'SEMANA' in df_filtrado.columns: df_filtrado = df_filtrado[df_filtrado['SEMANA'].isin(semana_sel)]
    if ciudad_sel: df_filtrado = df_filtrado[df_filtrado['CIUDAD_REAL'].isin(ciudad_sel)]
    if centro_sel and 'CENTRO DE COSTOS' in df_filtrado.columns: df_filtrado = df_filtrado[df_filtrado['CENTRO DE COSTOS'].astype(str).isin(centro_sel)]
    if tramite_sel and 'TRAMITE' in df_filtrado.columns: df_filtrado = df_filtrado[df_filtrado['TRAMITE'].isin(tramite_sel)]

    paleta_datos = ['#1D3557', '#457B9D', '#A8DADC', '#E30613', '#F4A261', '#2A9D8F', '#E9C46A']

    # ==========================================
    # CÁLCULO GLOBAL DE DÍAS HÁBILES (NUEVA LÓGICA PARAMETRIZADA)
    # ==========================================
    dias_habiles = 1
    if not df_filtrado.empty and 'FECHA DE CREACION' in df_filtrado.columns:
        try:
            # Obtener festivos de Colombia para los años filtrados
            anos_unicos = df_filtrado['FECHA DE CREACION'].dt.year.unique().tolist()
            festivos_co = holidays.CO(years=anos_unicos)
            lista_festivos = list(festivos_co.keys())
            
            if mes_sel:
                # Si filtran por mes, calculamos los días de todos los meses seleccionados en su totalidad
                fechas_periodos = df_filtrado['FECHA DE CREACION'].dt.to_period('M').unique()
                total_dias = 0
                for periodo in fechas_periodos:
                    inicio_mes = periodo.start_time.date()
                    fin_mes = periodo.end_time.date()
                    # weekmask '1111110' cuenta Lunes a Sábado. Los festivos se restan automáticamente.
                    total_dias += np.busday_count(inicio_mes, fin_mes + timedelta(days=1), weekmask='1111110', holidays=lista_festivos)
                dias_habiles = total_dias
            else:
                # Si no hay meses filtrados, tomamos el rango de fechas existente
                fecha_min = df_filtrado['FECHA DE CREACION'].min().date()
                fecha_max = df_filtrado['FECHA DE CREACION'].max().date()
                dias_habiles = np.busday_count(fecha_min, fecha_max + timedelta(days=1), weekmask='1111110', holidays=lista_festivos)
                
            if dias_habiles <= 0: dias_habiles = 1
        except Exception as e:
            # Respaldo en caso de que holidays falle
            fecha_min = df_filtrado['FECHA DE CREACION'].min().date()
            fecha_max = df_filtrado['FECHA DE CREACION'].max().date()
            dias_habiles = np.busday_count(fecha_min, fecha_max + timedelta(days=1), weekmask='1111110')
            if dias_habiles == 0: dias_habiles = 1

    # ==========================================
    # VISTA 1: TABLERO GENERAL
    # ==========================================
    if st.session_state['pagina_actual'] == 'Tablero':
        total_solicitudes = int(df_filtrado['CANTIDAD_DESTINOS'].sum()) if 'CANTIDAD_DESTINOS' in df_filtrado.columns else len(df_filtrado)
        
        ciudades_en_pantalla = df_filtrado['CIUDAD_REAL'].unique()
        mensajeros_activos = sum([mensajeros_config.get(c, 0) for c in ciudades_en_pantalla])
        if mensajeros_activos == 0: mensajeros_activos = 1
        
        promedio_diario = total_solicitudes / dias_habiles / mensajeros_activos
        
        eficacia = 0
        fallidos_df = pd.DataFrame() # Inicializamos la variable para usarla en el desglose
        
        if 'ESTADO' in df_filtrado.columns and total_solicitudes > 0:
            fallidos_df = df_filtrado[df_filtrado['ESTADO'].str.contains('Fallido', case=False, na=False)]
            fallidos = fallidos_df['CANTIDAD_DESTINOS'].sum() if 'CANTIDAD_DESTINOS' in fallidos_df.columns else len(fallidos_df)
            eficacia = ((total_solicitudes - fallidos) / total_solicitudes) * 100

        col_kpis, col_graficos = st.columns([1.5, 5])
        with col_kpis:
            st.markdown(f"""<div class="kpi-card"><div class="kpi-title">Total Solicitudes</div><div class="kpi-value">{total_solicitudes:,}</div></div>
            <div class="kpi-card"><div class="kpi-title">Promedio (Vueltas/Día)</div><div class="kpi-value">{promedio_diario:.1f}</div></div>
            <div class="kpi-card"><div class="kpi-title">Efectividad Operativa</div><div class="kpi-value">{eficacia:.1f}%</div></div>""", unsafe_allow_html=True)

        with col_graficos:
            st.markdown("<b>Solicitudes por Fecha y Ciudad</b>", unsafe_allow_html=True)
            res_mes_ciudad = df_filtrado.groupby(['MES_NUM', 'MES_NOMBRE', 'CIUDAD_REAL'])['CANTIDAD_DESTINOS'].sum().reset_index(name='Total')
            res_mes_ciudad['Etiqueta'] = res_mes_ciudad['CIUDAD_REAL'] + ' - ' + res_mes_ciudad['Total'].astype(str)
            fig_combo = px.bar(res_mes_ciudad.sort_values('MES_NUM'), x='MES_NOMBRE', y='Total', color='CIUDAD_REAL', barmode='group', text='Etiqueta', color_discrete_sequence=paleta_datos)
            fig_combo.update_traces(textposition='outside')
            st.plotly_chart(fig_combo, use_container_width=True)

        # --- SECCIÓN: DESGLOSE DE AFECTACIÓN DE EFECTIVIDAD ---
        if 'ESTADO' in df_filtrado.columns:
            st.markdown("<br>", unsafe_allow_html=True)
            if not fallidos_df.empty:
                with st.expander("🔍 Ver detalle de servicios que afectaron la Efectividad (Fallidos)"):
                    st.markdown("<p style='color: #64748B;'>A continuación se listan los servicios marcados como 'Fallido' para analizar la causa raíz.</p>", unsafe_allow_html=True)
                    
                    col_mensajero = next((col for col in ['COLABORADOR', 'MENSAJERO', 'RESPONSABLE', 'USUARIO'] if col in df_filtrado.columns), None)
                    
                    columnas_deseadas = ['FECHA DE CREACION', 'CIUDAD_REAL', col_mensajero, 'TRAMITE', 'ESTADO', 'CANTIDAD_DESTINOS', 'OBSERVACIONES']
                    columnas_a_mostrar = [col for col in columnas_deseadas if col and col in fallidos_df.columns]
                    
                    if columnas_a_mostrar:
                        st.dataframe(fallidos_df[columnas_a_mostrar].sort_values('FECHA DE CREACION', ascending=False), use_container_width=True, hide_index=True)
                    else:
                        st.dataframe(fallidos_df, use_container_width=True, hide_index=True)
            else:
                st.success("🎉 ¡Excelente! No hay servicios fallidos en los filtros seleccionados. La efectividad es del 100%.")

    # ==========================================
    # VISTA 2: MEDICIÓN DE TIEMPOS
    # ==========================================
    elif st.session_state['pagina_actual'] == 'Tiempo':
        st.title("■ Análisis Gerencial de Tiempos Operativos")
        if 'TIEMPO_HORAS' in df_filtrado.columns and 'TRAMITE' in df_filtrado.columns:
            col_t1, col_t2 = st.columns(2)
            with col_t1:
                st.markdown("<b>Horas Invertidas por Tipo de Gestión</b>", unsafe_allow_html=True)
                res_tiempo = df_filtrado.groupby('TRAMITE')['TIEMPO_HORAS'].sum().reset_index().sort_values(by='TIEMPO_HORAS', ascending=True).tail(10)
                fig_tramite = px.bar(res_tiempo, x='TIEMPO_HORAS', y='TRAMITE', orientation='h', text=res_tiempo['TIEMPO_HORAS'].apply(lambda x: f"{x:.0f} h"))
                fig_tramite.update_traces(marker_color='#457B9D', textposition='outside')
                st.plotly_chart(fig_tramite, use_container_width=True)
            
            with col_t2:
                st.markdown("<b>Evolución del Tiempo Promedio (Horas) por Sede</b>", unsafe_allow_html=True)
                tendencia = df_filtrado.groupby(['MES_NUM', 'MES_NOMBRE', 'CIUDAD_REAL'])['TIEMPO_HORAS'].mean().reset_index()
                tendencia['Etiqueta'] = tendencia['CIUDAD_REAL'] + ' (' + tendencia['TIEMPO_HORAS'].round(1).astype(str) + 'h)'
                fig_tend = px.line(tendencia.sort_values('MES_NUM'), x='MES_NOMBRE', y='TIEMPO_HORAS', color='CIUDAD_REAL', markers=True, text='Etiqueta', color_discrete_sequence=paleta_datos)
                fig_tend.update_traces(textposition='top center')
                st.plotly_chart(fig_tend, use_container_width=True)

    # ==========================================
    # VISTA 3: SOLICITUDES
    # ==========================================
    elif st.session_state['pagina_actual'] == 'Solicitudes':
        st.title("■ Análisis Detallado de Volúmenes")
        
        st.markdown("<b>Matriz Operativa: Solicitudes por Sede y Mes</b>", unsafe_allow_html=True)
        pivot_df = pd.pivot_table(df_filtrado, index='CIUDAD_REAL', columns='MES_NOMBRE', values='CANTIDAD_DESTINOS', aggfunc='sum', fill_value=0)
        meses_orden = [m for m in ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'] if m in pivot_df.columns]
        pivot_df = pivot_df[meses_orden]
        
        pivot_df['Total General'] = pivot_df.sum(axis=1)
        totales_mes = pivot_df.sum(axis=0)
        
        pivot_df = pivot_df.reset_index().rename(columns={'CIUDAD_REAL': 'SEDE / MES'})
        
        st.dataframe(pivot_df, use_container_width=True, hide_index=True)
        
        st.markdown(f"""
        <div style='background-color: #1D3557; color: white; padding: 12px; border-radius: 0px 0px 8px 8px; font-weight: bold; margin-top: -16px; text-align: right;'>
            📌 TOTAL GENERAL DE SOLICITUDES: {int(totales_mes['Total General'])}
        </div>
        """, unsafe_allow_html=True)
            
        st.markdown("<hr>", unsafe_allow_html=True)
            
        st.markdown("<b>Distribución Absoluta de Servicios por Sede</b>", unsafe_allow_html=True)
        res_un = df_filtrado.groupby('CIUDAD_REAL')['CANTIDAD_DESTINOS'].sum().reset_index(name='Solicitudes').sort_values(by='Solicitudes', ascending=False)
        res_un['Etiqueta'] = res_un['CIUDAD_REAL'] + ' - ' + res_un['Solicitudes'].astype(str)
        fig_un = px.bar(res_un, x='CIUDAD_REAL', y='Solicitudes', color='CIUDAD_REAL', color_discrete_sequence=paleta_datos, text='Etiqueta')
        fig_un.update_traces(textposition='outside')
        fig_un.update_layout(margin=dict(t=30, b=10, l=10, r=10), showlegend=False, plot_bgcolor='white', paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_un, use_container_width=True)

    # ==========================================
    # VISTA 4: PARTICIPACIÓN
    # ==========================================
    elif st.session_state['pagina_actual'] == 'Participacion':
        st.title("■ Análisis de Cuotas de Participación")
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            st.markdown("<b>Participación Porcentual por Sede</b>", unsafe_allow_html=True)
            res_part_un = df_filtrado.groupby('CIUDAD_REAL')['CANTIDAD_DESTINOS'].sum().reset_index().rename(columns={'CANTIDAD_DESTINOS': 'Total'})
            fig_part_un = px.pie(res_part_un, values='Total', names='CIUDAD_REAL', hole=0.4, color_discrete_sequence=paleta_datos)
            fig_part_un.update_traces(textposition='inside', textinfo='percent+label') 
            st.plotly_chart(fig_part_un, use_container_width=True)
            
        with col_p2:
            st.markdown("<b>Participación por Trámite (Top 15)</b>", unsafe_allow_html=True)
            if 'TRAMITE' in df_filtrado.columns:
                res_part_tr = df_filtrado.groupby('TRAMITE')['CANTIDAD_DESTINOS'].sum().reset_index(name='Total').sort_values('Total', ascending=False).head(15).sort_values('Total', ascending=True)
                fig_part_bar = px.bar(res_part_tr, x='Total', y='TRAMITE', orientation='h', text='Total')
                fig_part_bar.update_traces(marker_color='#2A9D8F', textposition='outside')
                st.plotly_chart(fig_part_bar, use_container_width=True)

    # ==========================================
    # VISTA 5: ANÁLISIS DE COLABORADORES
    # ==========================================
    elif st.session_state['pagina_actual'] == 'Mensajeros':
        st.title("■ Análisis de Productividad y Eficiencia")
        st.markdown("<p style='color: #64748B;'>Medición de volumen de entregas ponderadas y tiempos promedios para detectar cuellos de botella en la operación.</p>", unsafe_allow_html=True)
        
        col_mensajero = next((col for col in ['COLABORADOR', 'MENSAJERO', 'RESPONSABLE', 'USUARIO'] if col in df_filtrado.columns), None)
        
        if col_mensajero and 'TIEMPO_HORAS' in df_filtrado.columns:
            res_mensajero = df_filtrado.groupby(col_mensajero).agg(
                Total_Vueltas=('CANTIDAD_DESTINOS', 'sum'),
                Tiempo_Promedio_Hrs=('TIEMPO_HORAS', 'mean')
            ).reset_index().sort_values('Total_Vueltas', ascending=False)
            
            res_mensajero = res_mensajero[res_mensajero[col_mensajero].str.strip() != ""]
            
            st.markdown("<br><b>► Índice de Productividad (Volumen de Vueltas)</b>", unsafe_allow_html=True)
            fig_prod = px.bar(res_mensajero.head(15).sort_values('Total_Vueltas', ascending=True), 
                              x='Total_Vueltas', y=col_mensajero, orientation='h', text='Total_Vueltas')
            fig_prod.update_traces(marker_color='#1D3557', textposition='outside')
            st.plotly_chart(fig_prod, use_container_width=True)
            
            st.markdown("<hr style='opacity: 0.2;'>", unsafe_allow_html=True)
            
            st.markdown("<b>► Control de Eficiencia (Mayor Tiempo Promedio)</b>", unsafe_allow_html=True)
            
            res_demoras = res_mensajero.sort_values('Tiempo_Promedio_Hrs', ascending=False).head(15).sort_values('Tiempo_Promedio_Hrs', ascending=True)
            fig_ef = px.bar(res_demoras, x='Tiempo_Promedio_Hrs', y=col_mensajero, orientation='h', 
                            text=res_demoras['Tiempo_Promedio_Hrs'].apply(lambda x: f"{x:.1f} h"))
            fig_ef.update_traces(marker_color='#E30613', textposition='outside')
            st.plotly_chart(fig_ef, use_container_width=True)
            
            st.markdown("<hr style='opacity: 0.2;'>", unsafe_allow_html=True)
            st.markdown("<b>► Consolidado General por Colaborador</b>", unsafe_allow_html=True)
            
            num_mensajeros = len(res_mensajero)
            
            # --- LÓGICA DE DÍAS HÁBILES EN EL CÁLCULO FINAL ---
            res_mensajero['Promedio Vueltas/Día'] = (res_mensajero['Total_Vueltas'] / dias_habiles).round(1)
            res_mensajero['Tiempo_Promedio_Hrs'] = res_mensajero['Tiempo_Promedio_Hrs'].round(2)
            
            res_mensajero.columns = ['Colaborador', 'Total Vueltas Ponderadas', 'Tiempo Promedio (Horas)', 'Promedio Vueltas/Día']
            
            if not res_mensajero.empty:
                total_v_sum = res_mensajero['Total Vueltas Ponderadas'].sum()
                tiempo_mean = res_mensajero['Tiempo Promedio (Horas)'].mean()
                promedio_total = total_v_sum / dias_habiles / num_mensajeros if num_mensajeros > 0 else 0
                
                st.dataframe(res_mensajero, use_container_width=True, hide_index=True)
                
                st.markdown(f"""
                <div style="display: flex; background-color: #1D3557; color: white; padding: 12px 15px; border-radius: 0px 0px 8px 8px; font-weight: bold; margin-top: -16px; font-size: 14px;">
                    <div style="flex: 1; text-align: left;">📌 TOTAL GENERAL</div>
                    <div style="flex: 1; text-align: right;">{total_v_sum}</div>
                    <div style="flex: 1; text-align: right;">{round(tiempo_mean, 2)}</div>
                    <div style="flex: 1; text-align: right;">{round(promedio_total, 1)}</div>
                </div>
                """, unsafe_allow_html=True)
            
        else:
            st.warning("No se encontró la columna de Colaborador en la base de datos para generar este reporte.")
