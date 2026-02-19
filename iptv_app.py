import streamlit as st
import pandas as pd
import os, glob
from datetime import datetime, timedelta

st.set_page_config(page_title="IPTV Admin Pro", layout="wide")
BASE = os.path.dirname(os.path.abspath(__file__))
FIN_F = os.path.join(BASE, "finanzas.csv")

def get_db():
    fs = glob.glob(os.path.join(BASE, "*.csv"))
    for f in fs:
        if any(x in f.lower() for x in ["database","iptv","bd"]) and "finanzas" not in f.lower():
            return f
    return fs[0] if fs else None

DB_P = get_db()

def load_f():
    if os.path.exists(FIN_F):
        df = pd.read_csv(FIN_F)
        # CORRECCIÓN: Asegurar que no haya valores vacíos en Fecha o Detalle
        df['Fecha'] = df['Fecha'].fillna("S/F")
        df['Detalle'] = df['Detalle'].fillna("Sin Detalle")
        return df
    return pd.DataFrame(columns=["Fecha","Tipo","Detalle","Monto"])

def load_c():
    if not DB_P: return pd.DataFrame()
    try: df = pd.read_csv(DB_P, encoding='utf-8')
    except: df = pd.read_csv(DB_P, encoding='latin-1')
    df.columns = df.columns.str.strip()
    cols = ['Usuario','Servicio','Vencimiento','WhatsApp','Observaciones']
    for c in cols:
        if c not in df.columns: df[c] = ""
    return df.fillna("")

if 'df' not in st.session_state: st.session_state.df = load_c()

st.title("🖥️ Gestión IPTV Pro")

if not DB_P:
    st.error("Base de datos no encontrada.")
else:
    df_act = st.session_state.df.copy()
    t1, t2, t3 = st.tabs(["📋 Clientes", "🛒 Ventas", "📊 Finanzas"])

    with t1:
        st.dataframe(df_act[['Usuario','Servicio','Vencimiento','WhatsApp','Observaciones']], use_container_width=True, hide_index=True)
        st.divider()
        u_del = st.selectbox("Usuario a ELIMINAR:", ["---"] + list(df_act['Usuario'].unique()))
        if st.button("❌ Confirmar Eliminación"):
            if u_del != "---":
                st.session_state.df = st.session_state.df[st.session_state.df['Usuario'] != u_del]
                st.session_state.df.to_csv(DB_P, index=False)
                st.rerun()

    with t2:
        c1, c2, c3 = st.columns(3)
        with c1:
            st.subheader("🛒 Renovación")
            u_s = st.selectbox("Elegir:", df_act['Usuario'].unique())
            with st.form("f1"):
                pr, vl = st.selectbox("Prod:", ["M327","LEDTV","SMARTBOX","ALFA TV"]), st.number_input("Precio:", min_value=0.0)
                if st.form_submit_button("💰 Registrar Venta"):
                    idx = st.session_state.df[st.session_state.df['Usuario']==u_s].index[0]
                    fv = (datetime.now()+timedelta(days=30)).strftime('%d-%b').lower()
                    st.session_state.df.at[idx,'Vencimiento'], st.session_state.df.at[idx,'Servicio'] = fv, pr
                    st.session_state.df.to_csv(DB_P, index=False)
                    df_fin = load_f()
                    nv = pd.DataFrame([{"Fecha":datetime.now().strftime("%y-%m-%d %H:%M"),"Tipo":"Ingreso","Detalle":f"Renov {pr}: {u_s}","Monto":vl}])
                    pd.concat([df_fin, nv], ignore_index=True).to_csv(FIN_F, index=False)
                    st.rerun()
        with c2:
            st.subheader("➕ Nuevo Registro")
            with st.form("f2"):
                nu, np = st.text_input("Nombre"), st.selectbox("Panel", ["M327","LEDTV","SMARTBOX","ALFA TV"])
                nw, ni = st.text_input("WhatsApp"), st.number_input("Precio:", min_value=0.0)
                # CORRECCIÓN: Botón de envío obligatorio para Streamlit
                if st.form_submit_button("💾 Crear Registro"):
                    if nu:
                        fv = (datetime.now()+timedelta(days=30)).strftime('%d-%b').lower()
                        nr = pd.DataFrame([{"Usuario":nu,"Servicio":np,"Vencimiento":fv,"WhatsApp":nw,"Observaciones":""}])
                        st.session_state.df = pd.concat([st.session_state.df, nr], ignore_index=True)
                        st.session_state.df.to_csv(DB_P, index=False)
                        df_fin = load_f()
                        nv = pd.DataFrame([{"Fecha":datetime.now().strftime("%y-%m-%d %H:%M"),"Tipo":"Ingreso","Detalle":f"Nuevo: {nu}","Monto":ni}])
                        pd.concat([df_fin, nv], ignore_index=True).to_csv(FIN_F, index=False)
                        st.rerun()
        with c3:
            st.subheader("💳 Créditos")
            with st.form("f3"):
                det_c, val_c = st.text_input("Detalle"), st.number_input("Costo:", min_value=0.0)
                if st.form_submit_button("📦 Registrar Compra"):
                    if det_c:
                        df_fin = load_f()
                        nv = pd.DataFrame([{"Fecha":datetime.now().strftime("%y-%m-%d %H:%M"),"Tipo":"Egreso","Detalle":det_c,"Monto":val_c}])
                        pd.concat([df_fin, nv], ignore_index=True).to_csv(FIN_F, index=False)
                        st.rerun()

    with t3:
        st.subheader("📊 Reporte Financiero")
        fdf = load_f()
        if not fdf.empty:
            i, e = fdf[fdf['Tipo']=="Ingreso"]['Monto'].sum(), fdf[fdf['Tipo']=="Egreso"]['Monto'].sum()
            m1, m2, m3 = st.columns(3)
            m1.metric("Ingresos", f"${i:,.2f}"); m2.metric("Egresos", f"${e:,.2f}"); m3.metric("Utilidad", f"${i-e:,.2f}")
            st.write("### Historial")
            st.dataframe(fdf.sort_values("Fecha", ascending=False), use_container_width=True, hide_index=True)
            st.subheader("🗑️ Borrar Registro")
            # CORRECCIÓN: Convertir a String para evitar el error UFuncNoLoopError
            fdf['opcion'] = fdf['Fecha'].astype(str) + " | " + fdf['Detalle'].astype(str)
            reg_del = st.selectbox("Selecciona registro:", ["---"] + list(fdf['opcion']))
            if st.button("🗑️ Borrar"):
                if reg_del != "---":
                    fdf = fdf[fdf['opcion'] != reg_del]
                    fdf.drop(columns=['opcion']).to_csv(FIN_F, index=False)
                    st.rerun()
        else: st.info("Historial vacío.")