import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime, timedelta

# Configuración de página
st.set_page_config(page_title="IPTV Cloud Admin", layout="wide")

# Conexión a Google Sheets (Base de Datos en la Nube)
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    # Carga las dos pestañas de tu Google Sheet
    df_c = conn.read(worksheet="Clientes", ttl="0")
    df_f = conn.read(worksheet="Finanzas", ttl="0")
    return df_c.fillna(""), df_f.fillna("")

df_cli, df_fin = load_data()

st.title("🖥️ IPTV Cloud Pro")

t1, t2, t3 = st.tabs(["📋 Clientes", "🛒 Ventas", "📊 Finanzas"])

with t1:
    st.subheader("Base de Datos en Tiempo Real")
    st.dataframe(df_cli[['Usuario','Servicio','Vencimiento','WhatsApp','Observaciones']], use_container_width=True, hide_index=True)
    
    st.divider()
    st.subheader("🗑️ Eliminar Usuario")
    u_del = st.selectbox("Selecciona para borrar:", ["---"] + list(df_cli['Usuario'].unique()))
    if st.button("❌ Confirmar Eliminación"):
        if u_del != "---":
            new_df = df_cli[df_cli['Usuario'] != u_del]
            conn.update(worksheet="Clientes", data=new_df)
            st.success(f"Usuario {u_del} eliminado.")
            st.rerun()

with t2:
    c1, c2, c3 = st.columns(3)
    with c1:
        st.subheader("🛒 Renovación")
        u_s = st.selectbox("Elegir:", df_cli['Usuario'].unique())
        with st.form("f1"):
            pr = st.selectbox("Producto:", ["M327","LEDTV","SMARTBOX","ALFA TV"])
            vl = st.number_input("Precio:", min_value=0.0)
            if st.form_submit_button("💰 Registrar Venta"):
                idx = df_cli[df_cli['Usuario']==u_s].index[0]
                fv = (datetime.now()+timedelta(days=30)).strftime('%d-%b').lower()
                df_cli.at[idx,'Vencimiento'], df_cli.at[idx,'Servicio'] = fv, pr
                conn.update(worksheet="Clientes", data=df_cli)
                # Registro financiero
                nv = pd.DataFrame([{"Fecha":datetime.now().strftime("%y-%m-%d %H:%M"),"Tipo":"Ingreso","Detalle":f"Renov {pr}: {u_s}","Monto":vl}])
                conn.update(worksheet="Finanzas", data=pd.concat([df_fin, nv], ignore_index=True))
                st.rerun()

    with c2:
        st.subheader("➕ Nuevo Registro")
        with st.form("f2"):
            nu = st.text_input("Nombre")
            np = st.selectbox("Panel", ["M327","LEDTV","SMARTBOX","ALFA TV"])
            nw = st.text_input("WhatsApp")
            ni = st.number_input("Precio inicial:", min_value=0.0)
            if st.form_submit_button("💾 Crear"):
                if nu:
                    fv = (datetime.now()+timedelta(days=30)).strftime('%d-%b').lower()
                    nr = pd.DataFrame([{"Usuario":nu,"Servicio":np,"Vencimiento":fv,"WhatsApp":nw,"Observaciones":""}])
                    conn.update(worksheet="Clientes", data=pd.concat([df_cli, nr], ignore_index=True))
                    nv_f = pd.DataFrame([{"Fecha":datetime.now().strftime("%y-%m-%d %H:%M"),"Tipo":"Ingreso","Detalle":f"Nuevo: {nu}","Monto":ni}])
                    conn.update(worksheet="Finanzas", data=pd.concat([df_fin, nv_f], ignore_index=True))
                    st.rerun()

    with c3:
        st.subheader("💳 Créditos")
        with st.form("f3"):
            dc = st.text_input("Detalle")
            vc = st.number_input("Costo:", min_value=0.0)
            if st.form_submit_button("📦 Comprar"):
                if dc:
                    nv_f = pd.DataFrame([{"Fecha":datetime.now().strftime("%y-%m-%d %H:%M"),"Tipo":"Egreso","Detalle":dc,"Monto":vc}])
                    conn.update(worksheet="Finanzas", data=pd.concat([df_fin, nv_f], ignore_index=True))
                    st.rerun()

with t3:
    st.subheader("📊 Reporte")
    if not df_fin.empty:
        i, e = df_fin[df_fin['Tipo']=="Ingreso"]['Monto'].sum(), df_fin[df_fin['Tipo']=="Egreso"]['Monto'].sum()
        st.metric("Utilidad", f"${i-e:,.2f}", delta=f"Ingresos: ${i}")
        st.dataframe(df_fin.sort_values("Fecha", ascending=False), use_container_width=True, hide_index=True)
        st.divider()
        df_fin['opcion'] = df_fin['Fecha'].astype(str) + " | " + df_fin['Detalle'].astype(str)
        reg_del = st.selectbox("Borrar registro:", ["---"] + list(df_fin['opcion']))
        if st.button("🗑️ Borrar"):
            if reg_del != "---":
                new_f = df_fin[df_fin['opcion'] != reg_del].drop(columns=['opcion'])
                conn.update(worksheet="Finanzas", data=new_f)
                st.rerun()
