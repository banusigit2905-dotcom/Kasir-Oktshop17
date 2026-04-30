import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta

# Pengaturan Halaman
st.set_page_config(page_title="OKTSHOP17", layout="centered")

# --- DATABASE ---
def init_db():
    conn = sqlite3.connect('oktshop.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS sales (id INTEGER PRIMARY KEY, total REAL, method TEXT, items TEXT, date TIMESTAMP)')
    conn.commit()
    conn.close()

init_db()

# --- LOGIN SESSIONS ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# --- TAMPILAN LOGIN ---
if not st.session_state.logged_in:
    st.markdown("<h2 style='text-align: center;'>OKTSHOP17 LOGIN</h2>", unsafe_allow_html=True)
    user_id = st.text_input("ID User")
    password = st.text_input("Kata Sandi", type="password")
    if st.button("Login", use_container_width=True):
        if user_id == "admin" and password == "1234": # Ganti sesuai keinginan
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("ID atau Password Salah")

# --- APLIKASI UTAMA ---
else:
    # Menu Profil Pojok Kanan Atas
    col_t, col_p = st.columns([3, 1])
    with col_t:
        st.write(f"### OKTSHOP17")
    with col_p:
        with st.expander("👤 Menu"):
            st.write("ID: admin")
            if st.button("Rekap 3 Bln"):
                st.session_state.page = "rekap"
            if st.button("Keluar"):
                st.session_state.logged_in = False
                st.rerun()

    # Navigasi Halaman
    page = st.session_state.get('page', 'kasir')

    if page == "kasir":
        st.divider()
        if 'cart' not in st.session_state: st.session_state.cart = []
        
        # Input HP Friendly
        item = st.text_input("Nama Barang")
        price = st.number_input("Harga (Rp)", min_value=0, step=1000)
        
        if st.button("➕ Tambah Barang", use_container_width=True):
            if item and price > 0:
                st.session_state.cart.append({"Barang": item, "Harga": price})
        
        if st.session_state.cart:
            st.write("---")
            df = pd.DataFrame(st.session_state.cart)
            st.table(df)
            total = df['Harga'].sum()
            st.write(f"**Total: Rp {total:,.0f}**")
            
            method = st.radio("Metode Bayar", ["Tunai", "QRIS"], horizontal=True)
            
            if st.button("✅ Proses & Cetak Nota", use_container_width=True):
                # Simpan DB
                conn = sqlite3.connect('oktshop.db')
                c = conn.cursor()
                items_text = ", ".join([i['Barang'] for i in st.session_state.cart])
                c.execute('INSERT INTO sales (total, method, items, date) VALUES (?, ?, ?, ?)',
                          (total, method, items_text, datetime.now()))
                conn.commit()
                conn.close()
                
                # Tampilan Nota
                st.success("Transaksi Berhasil!")
                nota = f"OKTSHOP17\n----------\n{items_text}\nTotal: Rp {total:,.0f}\nBayar: {method}\n----------"
                st.code(nota)
                st.session_state.cart = [] # Reset

    elif page == "rekap":
        st.subheader("Rekap Penjualan (3 Bulan)")
        if st.button("Kembali ke Kasir"):
            st.session_state.page = "kasir"
            st.rerun()
            
        conn = sqlite3.connect('oktshop.db')
        try:
            df_sales = pd.read_sql_query('SELECT * FROM sales', conn)
            if not df_sales.empty:
                st.dataframe(df_sales, use_container_width=True)
                st.write(f"Total Omzet: Rp {df_sales['total'].sum():,.0f}")
            else:
                st.info("Belum ada data")
        except:
            st.info("Belum ada transaksi")
        conn.close()
