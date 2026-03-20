import streamlit as st
import pandas as pd
import re
import os
import io
import streamlit.components.v1 as components

# محاولة استيراد Plotly للرسوم التفاعلية
try:
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

# 1. إعداد الصفحة واللوجو
st.set_page_config(page_title="نظام IDA للمستحقات", layout="wide", page_icon="IDA_logo_(1).ico")

# 2. تصميم CSS المتطور (تنسيق الشاشة والطباعة + حماية الموبايل)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif !important; direction: rtl; text-align: center; }
    .main { background-color: #f4f7f9; }
    
    /* ------------- حل مشكلة الكلام بالطول في الموبايل ------------- */
    [data-testid="stSidebar"] * {
        white-space: nowrap !important;
    }
    .custom-table th, .custom-table td {
        white-space: nowrap !important;
    }
    /* ------------------------------------------------------------- */
    
    .personal-card { background: linear-gradient(135deg, #003366 0%, #005bb7 100%); color: white; padding: 25px; border-radius: 20px; margin-bottom: 25px; border: 2px solid #ffffff; width: 100%; }
    .personal-card h1 { font-size: 35px !important; font-weight: 800; color: white !important; margin: 0; }
    
    .stat-card { padding: 20px; border-radius: 15px; color: white !important; text-align: center; margin-bottom: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
    .stat-value { font-size: 28px !important; font-weight: 800; display: block; color: white !important; }
    .stat-label { color: white !important; font-size: 16px; font-weight: 600; }

    .custom-table-container { width: 100%; overflow-x: auto; border-radius: 15px; background: white; padding: 10px; box-shadow: 0 5px 15px rgba(0,0,0,0.05); }
    .custom-table { width: 100%; border-collapse: collapse; text-align: center; }
    .custom-table th { background-color: #003366; color: white; padding: 12px; }
    .custom-table td { padding: 10px; border: 1px solid #ddd; font-weight: 600; }

    @media print {
        @page { size: A4 portrait; margin: 10mm; }
        section[data-testid="stSidebar"], .stDownloadButton, button, iframe, header, [data-testid="stHeader"], .stTextInput, .stSelectbox, .stHeader, h1:first-of-type, .stExpander { display: none !important; }
        .main, .block-container { background-color: white !important; padding: 0 !important; margin: 0 !important; }
        * { -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }
        .personal-card { background: transparent !important; color: #003366 !important; border: none !important; text-align: center !important; }
        .personal-card h1 { color: #003366 !important; font-size: 32px !important; text-align: center !important; margin: 0 auto !important; display: block !important; }
        .stat-card { border: 1px solid #ddd !important; margin-bottom: 5px !important; padding: 10px !important; }
        .stat-value, .stat-label { color: black !important; }
    }
    </style>
    """, unsafe_allow_html=True)

# 3. محرك البيانات المطور
@st.cache_data
def load_v40_data():
    file_name = 'MAR2026.csv'
    if not os.path.exists(file_name): return None, None
    try:
        df = pd.read_csv(file_name, header=0, encoding='utf-8-sig', low_memory=False, dtype={'National_ID': str, 'Employee_Code': str})
        df.columns = [c.strip() for c in df.columns]
        
        p = {
            'name': ['name_employee', 'اسم الموظف'], 'code': ['employee_code', 'كود'], 
            'date': ['التاريخ', 'date', 'Date'], 'mang
