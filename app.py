import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import io
from PIL import Image

# Pengaturan Halaman
st.set_page_config(page_title="OKTSHOP17", layout="centered")

# --- DATABASE ---
def init_db():
    conn = sqlite3.connect('oktshop.db')
    c = conn.cursor()
    # Tabel Penjualan
    c.execute('CREATE TABLE IF NOT EXISTS sales (id INTEGER PRIMARY KEY, total REAL, method TEXT, items TEXT, date TIMESTAMP)')
    # Tabel Produk (Baru)
    c.execute('CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY, name TEXT, price REAL, image BLOB)')
    conn.commit()
    conn.close()

init_db()

# --- LOGIN SESSIONS ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'page' not in st.session_state:
    st.session_state.page = "kasir"

# --- TAMPILAN LOGIN ---
if not st.session_state.logged_in:
    st.markdown("<h2 style='text-align: center;'>OKTSHOP17 LOGIN</h2>", unsafe_allow_html=True)
    user_id = st.text_input("ID User")
    password = st.text_input("Kata Sandi", type="password")
    if st.button("Login", use_container_width=True):
        if user_id == "admin" and password == "1234":
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("ID atau Password Salah")

# --- APLIKASI UTAMA ---
else:
    # Menu Profil & Navigasi
    col_t, col_p = st.columns([3, 1])
    with col_t:
        st.write(f"### OKTSHOP17")
    with col_p:
        with st.expander("👤 Menu"):
            st.write(f"User: admin")
            if st.button("🛒 Kasir"):
                st.session_state.page = "kasir"
                st.rerun()
            if st.button("📊 Rekap 3 Bln"):
                st.session_state.page = "rekap"
                st.rerun()
            if st.button("⚙️ Pengaturan"):
                st.session_state.page = "pengaturan"
                st.rerun()
            if st.button("🚪 Keluar"):
                st.session_state.logged_in = False
                st.rerun()

    # --- HALAMAN KASIR ---
    if st.session_state.page == "kasir":
        st.divider()
        if 'cart' not in st.session_state: st.session_state.cart = []
        
        # Ambil daftar produk dari DB untuk pilihan
        conn = sqlite3.connect('oktshop.db')
        df_p = pd.read_sql_query('SELECT name, price FROM products', conn)
        conn.close()

        st.subheader("Kasir")
        
        # Pilihan input: Manual atau dari Daftar Produk
        tab1, tab2 = st.tabs(["Pilih Produk", "Input Manual"])
        
        with tab1:
            if not df_p.empty:
                selected_prod = st.selectbox("Pilih Produk", df_p['name'].tolist())
                price_auto = df_p[df_p['name'] == selected_prod]['price'].values[0]
                if st.button("➕ Tambah Ke Keranjang", use_container_width=True):
                    st.session_state.cart.append({"Barang": selected_prod, "Harga": price_auto})
            else:
                st.info("Belum ada produk di database. Tambahkan di menu Pengaturan.")

        with tab2:
            item_manual = st.text_input("Nama Barang Baru")
            price_manual = st.number_input("Harga (Rp)", min_value=0, step=1000, key="manual_p")
            if st.button("➕ Tambah Manual", use_container_width=True):
                if item_manual and price_manual > 0:
                    st.session_state.cart.append({"Barang": item_manual, "Harga": price_manual})
        
        if st.session_state.cart:
            st.write("---")
            df_cart = pd.DataFrame(st.session_state.cart)
            st.table(df_cart)
            total = df_cart['Harga'].sum()
            st.write(f"**Total: Rp {total:,.0f}**")
            
            method = st.radio("Metode Bayar", ["Tunai", "QRIS"], horizontal=True)
            
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                if st.button("✅ Proses Transaksi", use_container_width=True):
                    conn = sqlite3.connect('oktshop.db')
                    c = conn.cursor()
                    items_text = ", ".join([i['Barang'] for i in st.session_state.cart])
                    c.execute('INSERT INTO sales (total, method, items, date) VALUES (?, ?, ?, ?)',
                              (total, method, items_text, datetime.now()))
                    conn.commit()
                    conn.close()
                    st.success("Berhasil Disimpan!")
                    st.session_state.cart = []
                    st.rerun()
            with col_b2:
                if st.button("🗑️ Kosongkan", use_container_width=True):
                    st.session_state.cart = []
                    st.rerun()

    # --- HALAMAN REKAP ---
    elif st.session_state.page == "rekap":
        st.subheader("📊 Rekap Penjualan")
        conn = sqlite3.connect('oktshop.db')
        try:
            df_sales = pd.read_sql_query('SELECT * FROM sales ORDER BY date DESC', conn)
            if not df_sales.empty:
                st.dataframe(df_sales, use_container_width=True)
                st.metric("Total Omzet", f"Rp {df_sales['total'].sum():,.0f}")
            else:
                st.info("Belum ada data transaksi.")
        except:
            st.error("Gagal memuat data.")
        conn.close()

    # --- HALAMAN PENGATURAN (TAMBAH PRODUK) ---
    elif st.session_state.page == "pengaturan":
        st.subheader("⚙️ Pengaturan Produk")
        
        with st.form("tambah_produk", clear_on_submit=True):
            st.write("### Tambah Produk Baru")
            p_name = st.text_input("Nama Produk")
            p_price = st.number_input("Harga Jual (Rp)", min_value=0, step=500)
            p_file = st.file_uploader("Foto Produk", type=['jpg', 'jpeg', 'png'])
            
            submit = st.form_submit_button("Simpan Produk", use_container_width=True)
            
            if submit:
                if p_name and p_price > 0:
                    img_byte = None
                    if p_file is not None:
                        img = Image.open(p_file)
                        # Resize agar database tidak terlalu berat
                        img.thumbnail((300, 300))
                        buf = io.BytesIO()
                        img.save(buf, format='PNG')
                        img_byte = buf.getvalue()
                    
                    conn = sqlite3.connect('oktshop.db')
                    c = conn.cursor()
                    c.execute('INSERT INTO products (name, price, image) VALUES (?, ?, ?)', 
                              (p_name, p_price, img_byte))
                    conn.commit()
                    conn.close()
                    st.success(f"Produk '{p_name}' berhasil ditambahkan!")
                else:
                    st.error("Nama dan Harga harus diisi!")

        # Menampilkan Daftar Produk yang ada
        st.write("---")
        st.write("### Daftar Produk Tersedia")
        conn = sqlite3.connect('oktshop.db')
        df_view = pd.read_sql_query('SELECT * FROM products', conn)
        conn.close()

        if not df_view.empty:
            for index, row in df_view.iterrows():
                with st.container():
                    c1, c2, c3 = st.columns([1, 2, 1])
                    with c1:
                        if row['image']:
                            st.image(row['image'], width=80)
                        else:
                            st.write("No Image")
                    with c2:
                        st.write(f"**{row['name']}**")
                        st.write(f"Rp {row['price']:,.0f}")
                    with c3:
                        # Opsi hapus produk (tambahan)
                        if st.button("Hapus", key=f"del_{row['id']}"):
                            conn = sqlite3.connect('oktshop.db')
                            c = conn.cursor()
                            c.execute('DELETE FROM products WHERE id = ?', (row['id'],))
                            conn.commit()
                            conn.close()
                            st.rerun()
                st.divider()
        else:
            st.info("Belum ada produk.")    # Menu Profil Pojok Kanan Atas
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
