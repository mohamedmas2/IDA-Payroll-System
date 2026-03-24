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

# 2. تصميم CSS (إخفاء أدوات Streamlit وتحسين المظهر)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif !important; direction: rtl; text-align: center; }
    
    /* إخفاء أدوات Streamlit للمستخدم النهائي */
    header {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stAppDeployButton {display:none !important;}
    [data-testid="stHeader"] {display:none !important;}
    .block-container {padding-top: 2rem !important;}

    .main { background-color: #f4f7f9; }
    [data-testid="stSidebar"] * { white-space: nowrap !important; overflow: hidden !important; text-overflow: ellipsis !important; }
    .sidebar-title { color: #003366; text-align: center; font-weight: 800; margin-top: -10px; margin-bottom: 10px; font-size: 24px; }
    
    .stats-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-bottom: 20px; }
    .stat-card { padding: 15px; border-radius: 15px; color: white !important; text-align: center; box-shadow: 0 4px 10px rgba(0,0,0,0.1); height: 100%; display: flex; flex-direction: column; justify-content: center; }
    .stat-value { font-size: 24px !important; font-weight: 800; display: block; color: white !important; margin-top: 5px; }
    .stat-label { color: white !important; font-size: 15px; font-weight: 600; }
    
    @media (max-width: 768px) { 
        .stats-grid { grid-template-columns: repeat(2, 1fr); } 
        .sidebar-title { font-size: 20px !important; } 
        .personal-card h1 { font-size: 24px !important; } 
    }
    
    .personal-card { background: linear-gradient(135deg, #003366 0%, #005bb7 100%); color: white; padding: 25px; border-radius: 20px; margin-bottom: 25px; border: 2px solid #ffffff; width: 100%; box-shadow: 0 10px 30px rgba(0,0,0,0.2); }
    .personal-card h1 { font-size: 30px !important; font-weight: 800; color: white !important; margin: 0; }
    
    .custom-table-container { width: 100%; overflow-x: auto; border-radius: 15px; background: white; padding: 10px; box-shadow: 0 5px 15px rgba(0,0,0,0.05); }
    .custom-table { width: 100%; border-collapse: collapse; text-align: center; }
    .custom-table th { background-color: #003366; color: white; padding: 12px; white-space: nowrap; }
    .custom-table td { padding: 10px; border: 1px solid #ddd; font-weight: 600; white-space: nowrap; }
    
    @media print {
        @page { size: A4 portrait; margin: 10mm; }
        section[data-testid="stSidebar"], .stDownloadButton, button, iframe, header, [data-testid="stHeader"], .stTextInput, .stSelectbox, .stHeader, h1:first-of-type, .stExpander { display: none !important; }
        .main, .block-container { background-color: white !important; padding: 0 !important; margin: 0 !important; }
        .personal-card { background: transparent !important; color: #003366 !important; border: none !important; text-align: center !important; }
        .personal-card h1 { color: #003366 !important; font-size: 32px !important; text-align: center !important; }
        .stats-grid { display: grid !important; grid-template-columns: repeat(4, 1fr) !important; gap: 5px !important; }
        .stat-card { border: 1px solid #ddd !important; padding: 5px !important; box-shadow: none !important; }
        .stat-value, .stat-label { color: black !important; font-size: 14px !important; }
    }
    </style>
""", unsafe_allow_html=True)

# 3. محرك البيانات المطور
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
    
    try:
        for f in all_files:
            temp_df = pd.read_csv(f, header=0, encoding='utf-8-sig', low_memory=False, dtype={'National_ID': str, 'Employee_Code': str})
            temp_df.columns = [c.strip() for c in temp_df.columns]
            full_df_list.append(temp_df)
            
        df = pd.concat(full_df_list, ignore_index=True)
        cols = {k: next((c for c in df.columns if any(w.lower() in c.lower() for w in p[k])), None) for k in p}
        
        if cols['date']:
            df[cols['date']] = pd.to_datetime(df[cols['date']], errors='coerce')
            df['Month_Year'] = df[cols['date']].dt.strftime('%Y-%m')
            
        if cols['name']:
            df[cols['name']] = df[cols['name']].astype(str).str.replace(r'\s+', ' ', regex=True).str.strip()
            df['Search_Key'] = df[cols['name']].str.replace(r'[أإآ]', 'ا', regex=True).str.replace('ى', 'ي').str.replace('ة', 'ه')
            
        def clean_money(val):
            v = str(val).replace(',', '').strip()
            if v in ["", "-", "0", "nan"]: return 0.0
            try: return float(v)
            except: return 0.0
            
        for k in ['ent', 'tax', 'stamp', 'ded', 'net']:
            if cols[k]: df[cols[k]] = df[cols[k]].apply(clean_money)
            
        return df, cols
    except Exception as e:
        st.error(f"خطأ في تحميل الملفات: {e}"); return None, None

df_raw, cols = load_all_csv_data()

if df_raw is not None:
    with st.sidebar:
        st.image("IDA_logo_(1).ico", width=150)
        st.markdown("<div class='sidebar-title'>IDA SYSTEM</div>", unsafe_allow_html=True)
        st.markdown("---")
        
        if cols['date']:
            unique_months = sorted(df_raw['Month_Year'].dropna().unique(), reverse=True)
            available_options = ["الكل"] + unique_months
            target_month = st.selectbox("📅 اختر شهر الصرف:", available_options)
            df = df_raw if target_month == "الكل" else df_raw[df_raw['Month_Year'] == target_month]
        else:
            df, target_month = df_raw, "غير محدد"
        
        menu = st.radio("📌 القائمة الرئيسية:", ["🔍 استعلام الموظفين", "📊 إحصائيات عامة", "🏢 تحليل الإدارات", "📥 تصدير التقارير"])

    if menu == "🔍 استعلام الموظفين":
        st.title(f"🔍 استعلام - {target_month}")
        c_search1, c_search2 = st.columns([1, 2])
        with c_search1: mode = st.selectbox("بحث بـ:", ["الاسم", "الكود"])
        with c_search2: q = st.text_input("✍️ ابدأ الكتابة هنا:")
        
        if q:
            if mode == "الاسم":
                q_n = re.sub(r'[أإآ]', 'ا', q).replace('ى', 'ي').replace('ة', 'ه').replace('*', '.*').strip()
                res = df[df['Search_Key'].str.contains(q_n, na=False, regex=True, flags=re.IGNORECASE)]
            else:
                res = df[df[cols['code']].astype(str).str.contains(q.strip(), na=False)]
            
            if not res.empty:
                for emp_code, group in res.groupby(cols['code']):
                    emp_name = group.iloc[0][cols['name']]
                    emp_nat = group.iloc[0][cols['nat']]
                    st.markdown(f'<div class="personal-card"><h1>{emp_name}</h1><p>🆔 كود: {emp_code} | 📄 رقم قومي: {emp_nat}</p></div>', unsafe_allow_html=True)
                    
                    s_ent, s_tax, s_ded, s_net = group[cols['ent']].sum(), (group[cols['tax']].sum() + group[cols['stamp']].sum()), group[cols['ded']].sum(), group[cols['net']].sum()
                    
                    st.markdown(f"""
                    <div class="stats-grid">
                        <div class="stat-card" style="background:#28a745;"><span class="stat-label">إجمالي المستحق</span><span class="stat-value">{s_ent:,.2f}</span></div>
                        <div class="stat-card" style="background:#ffc107;"><span class="stat-label" style="color:black">ضرائب ودمغة</span><span class="stat-value" style="color:black">{s_tax:,.2f}</span></div>
                        <div class="stat-card" style="background:#dc3545;"><span class="stat-label">إجمالي استقطاع</span><span class="stat-value">{s_ded:,.2f}</span></div>
                        <div class="stat-card" style="background:#007bff;"><span class="stat-label">الصافي النهائي</span><span class="stat-value">{s_net:,.2f}</span></div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    display_cols = [cols['date'], cols["type"], cols["desc"], cols["ent"], cols["net"]]
                    disp_df = group[display_cols].copy()
                    if cols['date']: disp_df[cols['date']] = disp_df[cols['date']].dt.strftime('%Y-%m-%d')
                    disp_df.insert(0, 'م', range(1, len(disp_df) + 1))
                    
                    st.markdown(f'<div class="custom-table-container">{disp_df.to_html(index=False, classes="custom-table", escape=False)}</div>', unsafe_allow_html=True)
                    if st.button(f"🖨️ طباعة {emp_name}", key=f"print_{emp_code}"):
                        components.html(f"<script>window.parent.document.title='مستحقات - {emp_name}'; window.parent.print();</script>")
                    st.markdown("---")
            else: st.warning(f"🔍 لا توجد نتائج.")
    # باقي القوائم (إحصائيات، تحليل، تصدير) تكمل هنا بنفس النمط...
