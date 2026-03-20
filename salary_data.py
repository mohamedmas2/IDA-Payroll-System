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

# 1. إعداد الصفحة واللوجو (تعديل الأيقونة لتكون ملفك)
st.set_page_config(page_title="نظام IDA للمستحقات", layout="wide", page_icon="IDA_logo_(1).ico")

# 2. تصميم CSS المتطور
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif !important; direction: rtl; text-align: center; }
    .main { background-color: #f4f7f9; }
    
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
        .personal-card { background: transparent !important; color: #003366 !important; border: none !important; text-align: center !important; }
        .personal-card h1 { color: #003366 !important; font-size: 32px !important; }
    }
    </style>
    """, unsafe_allow_html=True)

# 3. محرك البيانات
@st.cache_data
def load_data():
    file_name = 'MAR2026.csv'
    if not os.path.exists(file_name): return None, None
    try:
        # قراءة التاريخ والكود كنصوص لمنع التخريف
        df = pd.read_csv(file_name, header=0, encoding='utf-8-sig', low_memory=False, dtype={'NON': str, 'Employee_Code': str, 'National_ID': str})
        df.columns = [c.strip() for c in df.columns]
        
        p = {
            'name': ['Name_Employee'], 'code': ['Employee_Code'], 
            'date': ['NON'], 'mang': ['Mangment'],
            'type': ['نوع الصرف'], 'ent': ['أجمالى الاستحقاقات'], 'tax': ['ضريبة الدخل'],
            'stamp': ['ضريبة الدمغة'], 'ded': ['الأجمالى الاستقطاعات'], 'net': ['الصافي'],
            'nat': ['National_ID'], 'desc': ['وصف']
        }
        cols = {k: next((c for c in df.columns if any(w in c for w in p[k])), None) for k in p}
        
        # تنظيف الأسماء للبحث
        if cols['name']:
            df['Search_Key'] = df[cols['name']].astype(str).str.replace(r'[أإآ]', 'ا', regex=True).str.replace('ى', 'ي').str.replace('ة', 'ه').str.strip()
            
        # تنظيف المبالغ
        for k in ['ent', 'tax', 'stamp', 'ded', 'net']:
            if cols[k]:
                df[cols[k]] = pd.to_numeric(df[cols[k]].astype(str).str.replace(',', ''), errors='coerce').fillna(0.0)
                
        return df, cols
    except: return None, None

df_raw, cols = load_data()

if df_raw is not None:
    with st.sidebar:
        st.image("IDA_logo_(1).ico", width=150) # إضافة اللوجو الخاص بك
        st.markdown("---")
        
        # إضافة خيار "الكل" في التاريخ
        if cols['date']:
            available_months = ["الكل"] + sorted(df_raw[cols['date']].unique().tolist(), reverse=True)
            target_month = st.selectbox("📅 اختر شهر الصرف:", available_months)
            
            if target_month == "الكل":
                df = df_raw
            else:
                df = df_raw[df_raw[cols['date']] == target_month]
        else:
            df = df_raw
            target_month = "الكل"
        
        menu = st.radio("📌 القائمة الرئيسية:", ["🔍 استعلام الموظفين", "📊 إحصائيات عامة", "📥 تصدير التقارير"])

    if menu == "🔍 استعلام الموظفين":
        st.title(f"🔍 استعلام - {target_month}")
        c_search1, c_search2 = st.columns([1, 2])
        with c_search1: mode = st.selectbox("بحث بـ:", ["الاسم", "الكود"])
        with c_search2: q = st.text_input("✍️ ابحث هنا:")
        
        if q:
            if mode == "الاسم":
                q_n = re.sub(r'[أإآ]', 'ا', q).replace('ى', 'ي').replace('ة', 'ه').strip()
                res = df[df['Search_Key'].str.contains(q_n, na=False)]
            else:
                res = df[df[cols['code']].astype(str) == q.strip()]
            
            if not res.empty:
                for name, group in res.groupby(cols['name']):
                    st.markdown(f'<div class="personal-card"><h1>{name}</h1><p>🆔 كود: {group.iloc[0][cols["code"]]} | 🏢 {group.iloc[0][cols["mang"]]}</p></div>', unsafe_allow_html=True)
                    
                    s_ent = group[cols['ent']].sum()
                    s_tax = group[cols['tax']].sum() + group[cols['stamp']].sum()
                    s_ded = group[cols['ded']].sum()
                    s_net = group[cols['net']].sum()
                    
                    m1, m2, m3, m4 = st.columns(4)
                    m1.markdown(f'<div class="stat-card" style="background:#28a745;"><span class="stat-label">إجمالي المستحق</span><span class="stat-value">{s_ent:,.2f}</span></div>', unsafe_allow_html=True)
                    m2.markdown(f'<div class="stat-card" style="background:#ffc107;"><span class="stat-label" style="color:black">ضرائب ودمغة</span><span class="stat-value" style="color:black">{s_tax:,.2f}</span></div>', unsafe_allow_html=True)
                    m3.markdown(f'<div class="stat-card" style="background:#dc3545;"><span class="stat-label">إجمالي استقطاع</span><span class="stat-value">{s_ded:,.2f}</span></div>', unsafe_allow_html=True)
                    m4.markdown(f'<div class="stat-card" style="background:#007bff;"><span class="stat-label">الصافي النهائي</span><span class="stat-value">{s_net:,.2f}</span></div>', unsafe_allow_html=True)
                    
                    # عرض الجدول (بإضافة عمود التاريخ لو اخترنا "الكل")
                    display_cols = ([cols['date']] if target_month == "الكل" else []) + [cols['type'], cols['desc'], cols['ent'], cols['net']]
                    st.markdown(f'<div class="custom-table-container">{group[display_cols].to_html(index=False, classes="custom-table")}</div>', unsafe_allow_html=True)
                    
                    if st.button(f"🖨️ طباعة {name}"):
                        components.html(f"<script>window.parent.print();</script>")
            else: st.warning("🔍 لا توجد نتائج.")

    elif menu == "📊 إحصائيات عامة":
        st.title(f"📊 مؤشرات - {target_month}")
        st.metric("💵 إجمالي صافي المنصرف", f"{df[cols['net']].sum():,.2f}")
        if PLOTLY_AVAILABLE:
            st.plotly_chart(px.pie(df, values=cols['net'], names=cols['mang'], title="توزيع الرواتب حسب الإدارات"))

    elif menu == "📥 تصدير التقارير":
        buffer = io.BytesIO()
        df.to_excel(buffer, index=False)
        st.download_button(f"💾 تحميل ملف {target_month}", buffer.getvalue(), f"IDA_{target_month}.xlsx")

else: st.error("❌ ملف MAR2026.csv غير موجود.")
