import streamlit as st
import pandas as pd
import re
import os
import io
import glob
import streamlit.components.v1 as components

try:
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

# 1. إعداد الصفحة
st.set_page_config(page_title="نظام IDA للمستحقات", layout="wide", page_icon="IDA_logo_(1).ico")

# 2. CSS (تم إضافة جزء الطباعة 👇)
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;800&display=swap');
html, body, [class*="css"] { font-family: 'Cairo', sans-serif !important; direction: rtl; text-align: center; }

/* إخفاء أدوات Streamlit */
[data-testid="stHeader"] { background-color: rgba(0,0,0,0) !important; }
.stAppDeployButton, #MainMenu, footer { display: none !important; }

/* سهم السايدبار */
[data-testid="stSidebarCollapsedControl"] {
    background-color: #003366 !important;
    color: white !important;
    border-radius: 5px !important;
    top: 15px !important;
    right: 15px !important;
}

.main { background-color: #f4f7f9; }

.sidebar-title {
    color: #003366;
    text-align: center;
    font-weight: 800;
    margin-top: -10px;
    margin-bottom: 10px;
    font-size: 24px;
}

.stats-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 15px;
    margin-bottom: 20px;
}

.stat-card {
    padding: 15px;
    border-radius: 15px;
    color: white !important;
    text-align: center;
}

.personal-card {
    background: linear-gradient(135deg, #003366 0%, #005bb7 100%);
    color: white;
    padding: 25px;
    border-radius: 20px;
    margin-bottom: 25px;
}

.custom-table {
    width: 100%;
    border-collapse: collapse;
}

.custom-table th {
    background-color: #003366;
    color: white;
    padding: 10px;
}

.custom-table td {
    padding: 8px;
    border: 1px solid #ddd;
}

/* 🔥🔥🔥 الحل هنا */
@media print {

    /* اخفاء السايدبار بالكامل */
    section[data-testid="stSidebar"] {
        display: none !important;
    }

    /* اخفاء زر السهم */
    [data-testid="stSidebarCollapsedControl"] {
        display: none !important;
    }

    /* توسيع الصفحة */
    .main {
        width: 100% !important;
        margin: 0 !important;
        padding: 0 !important;
    }

    .block-container {
        max-width: 100% !important;
        padding: 0 !important;
    }

    /* تحسين شكل الطباعة */
    body {
        zoom: 90%;
    }
}

</style>
""", unsafe_allow_html=True)

# باقي الكود زي ما هو 👇

@st.cache_data
def load_all_csv_data():
    all_files = glob.glob("*.csv")
    if not all_files: return None, None
    full_df_list = []
    p = {
        'name': ['name_employee', 'اسم الموظف'], 'code': ['employee_code', 'كود'], 
        'date': ['التاريخ', 'date', 'Date'], 'mang': ['mangment', 'الإدارة'],
        'type': ['نوع الصرف'], 'ent': ['أجمالى الاستحقاقات'], 'tax': ['ضريبة الدخل'],
        'stamp': ['ضريبة الدمغة'], 'ded': ['الأجمالى الاستقطاعات'], 'net': ['الصافي'],
        'nat': ['national_id', 'الرقم القومي'], 'desc': ['وصف']
    }

    for f in all_files:
        temp_df = pd.read_csv(f)
        full_df_list.append(temp_df)

    df = pd.concat(full_df_list, ignore_index=True)
    cols = {k: next((c for c in df.columns if any(w in c for w in p[k])), None) for k in p}

    return df, cols

df_raw, cols = load_all_csv_data()

if df_raw is not None:
    with st.sidebar:
        target_month = "الكل"
        df = df_raw

    st.title(f"🔍 استعلام - {target_month}")

    q = st.text_input("ابحث:")

    if q:
        res = df[df[cols['name']].astype(str).str.contains(q)]

        for emp_code, group in res.groupby(cols['code']):
            emp_name = group.iloc[0][cols['name']]

            st.markdown(f'<div class="personal-card"><h1>{emp_name}</h1></div>', unsafe_allow_html=True)

            if st.button(f"🖨️ طباعة {emp_name}", key=f"p_{emp_code}"):
                components.html(f"<script>window.parent.print();</script>")
