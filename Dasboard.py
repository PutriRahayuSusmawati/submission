import pandas as pd
import streamlit as st
import plotly.express as px
import seaborn as sns

sns.set(style='dark')

def create_daily_orders_df(orders_df):
    # Mengonversi kolom 'order_purchase_timestamp' ke format datetime
    orders_df['order_purchase_timestamp'] = pd.to_datetime(orders_df['order_purchase_timestamp'])

    # Menambahkan kolom tanggal saja untuk mempermudah agregasi harian
    orders_df['order_date'] = orders_df['order_purchase_timestamp'].dt.date

    # Mengelompokkan berdasarkan 'order_date' dan menghitung jumlah pesanan per hari
    daily_orders_df = orders_df.groupby('order_date').agg(
        total_orders=('order_id', 'count'),
        total_order_value=('order_value', 'sum') 
    ).reset_index()

    return daily_orders_df

def create_payment_summary_df(payments_df):
    # Mengelompokkan berdasarkan 'payment_type' dan menghitung frekuensi dan total nilai pembayaran
    payment_summary_df = payments_df.groupby('payment_type').agg(
        payment_count=('payment_value', 'count'),
        total_payment_value=('payment_value', 'sum')
    ).reset_index()

    return payment_summary_df

def create_order_status_summary(orders_df):
    # Mengelompokkan berdasarkan 'order_status' untuk menghitung jumlah pesanan per status
    order_status_summary_df = orders_df['order_status'].value_counts().reset_index()
    order_status_summary_df.columns = ['order_status', 'count']

    return order_status_summary_df

def merge_orders_payments(orders_df, payments_df):
    # Menggabungkan orders_df dan payments_df berdasarkan 'order_id'
    merged_df = pd.merge(orders_df, payments_df, on='order_id', how='inner')
    return merged_df

def create_daily_revenue_df(merged_df):
    # Memfilter data hanya untuk pesanan yang berhasil (status = 'delivered')
    delivered_df = merged_df[merged_df['order_status'] == 'delivered']

    # Mengonversi 'order_purchase_timestamp' ke format datetime
    delivered_df['order_purchase_timestamp'] = pd.to_datetime(delivered_df['order_purchase_timestamp'])

    # Mengelompokkan berdasarkan tanggal dan menghitung total pendapatan harian
    delivered_df['order_date'] = delivered_df['order_purchase_timestamp'].dt.date
    daily_revenue_df = delivered_df.groupby('order_date').agg(
        daily_revenue=('payment_value', 'sum')
    ).reset_index()

    return daily_revenue_df

all_df = pd.read_csv('all_data.csv')
all_df['order_purchase_timestamp'] = pd.to_datetime(all_df['order_purchase_timestamp'])

st.sidebar.image('shop_logo.png', width=150)
st.header('E-Store :sparkles:')

st.sidebar.header("Filter Berdasarkan Tanggal")
start_date = st.sidebar.date_input("Tanggal Mulai", all_df['order_purchase_timestamp'].min().date())
end_date = st.sidebar.date_input("Tanggal Akhir", all_df['order_purchase_timestamp'].max().date())

# Filter data berdasarkan rentang tanggal yang dipilih
filtered_data = all_df[
    (all_df['order_purchase_timestamp'] >= pd.to_datetime(start_date)) &
    (all_df['order_purchase_timestamp'] <= pd.to_datetime(end_date))
]

# Tampilkan data yang sudah difilter untuk pengecekan
st.write("Data yang sudah difilter berdasarkan rentang tanggal:")
st.dataframe(filtered_data)

# Menghitung jumlah order harian
daily_orders_df = filtered_data.groupby(filtered_data['order_purchase_timestamp'].dt.date).size().reset_index(name='order_count')
daily_orders_df.columns = ['order_date', 'order_count']

# Membuat visualisasi jumlah order harian
fig = px.line(daily_orders_df, x='order_date', y='order_count', title='Jumlah Order Harian', labels={'order_date': 'Tanggal', 'order_count': 'Jumlah Order'})

st.title("Dashboard Informasi Jumlah Order Harian")
st.write("Visualisasi jumlah order harian berdasarkan rentang tanggal yang dipilih.")
st.plotly_chart(fig)

st.subheader("Data Jumlah Order Harian")
st.write(daily_orders_df)

st.subheader("Analisis Metode Pembayaran")

# Menampilkan metode pembayaran yang paling sering digunakan
payment_summary = filtered_data['payment_type'].value_counts().reset_index()
payment_summary.columns = ['payment_type', 'count']

fig_payment = px.bar(payment_summary, x='payment_type', y='count', title="Metode Pembayaran Terpopuler")
st.plotly_chart(fig_payment)

# Hubungan metode pembayaran dengan status pesanan
payment_status_summary = filtered_data.groupby(['payment_type', 'order_status']).size().reset_index(name='count')
fig_payment_status = px.bar(payment_status_summary, x='payment_type', y='count', color='order_status',
                            title="Hubungan Metode Pembayaran dengan Status Pesanan")
st.plotly_chart(fig_payment_status)

# Analisis RFM (Recency, Frequency, Monetary)
st.subheader("Analisis RFM (Recency, Frequency, Monetary)")

# Menghitung Recency, Frequency, dan Monetary untuk setiap customer_id
rfm_df = filtered_data.groupby('customer_id').agg(
    recency=('order_purchase_timestamp', lambda x: (filtered_data['order_purchase_timestamp'].max() - x.max()).days),
    frequency=('order_id', 'nunique'),
    monetary=('payment_value', 'sum')
).reset_index()

# Menampilkan rata-rata Frequency dan Monetary
average_frequency = rfm_df['frequency'].mean()
average_monetary = rfm_df['monetary'].mean()

st.metric(label="Rata-rata Frequency", value=round(average_frequency, 2))
st.metric(label="Rata-rata Monetary", value=f"Rp{round(average_monetary, 2):,.2f}")