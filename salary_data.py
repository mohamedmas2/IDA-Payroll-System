import streamlit as st
import pandas as pd
import re
import os
import io
import streamlit.components.v1 as components

# 1. إعداد الصفحة
st.set_page_config(page_title="نظام IDA للمستحقات", layout="wide", page_icon="💰")

# 2. تصميم CSS (إخفاء Sidebar في الموبايل وتنسيق الواجهة)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif !important; direction: rtl; text-align: center; }
    .main { background-color: #f4f7f9; }
    
    /* إخفاء القائمة الجانبية تماماً في الشاشات الصغيرة (الموبايل) لمنع الكلمات الطولية */
    @media (max-width: 768px) {
        [data-testid="stSidebar"] { display: none !important; }
    }

    .personal-card { background: linear-gradient(135deg, #003366 0%, #005bb7 100%); color: white; padding: 25px; border-radius: 20px; margin-bottom: 25px; border: 2px solid #ffffff; width: 100%; box-shadow: 0 10px 30px rgba(0,0,0,0.2); }
    .personal-card h1 { font-size: 32px !important; font-weight: 800; color: white !important; margin: 0; }
    
    .stat-card { padding: 20px; border-radius: 15px; color: white !important; text-align: center; margin-bottom: 15px; }
    .stat-value { font-size: 26px !important; font-weight: 800; display: block; color: white !important; }
    .stat-label { color: white !important; font-size: 15px; font-weight: 600; }

    .custom-table-container { width: 100%; overflow-x: auto; border-radius: 15px; background: white; padding: 10px; box-shadow: 0 5px 15px rgba(0,0,0,0.05); }
    .custom-table { width: 100%; border-collapse: collapse; text-align: center; }
    .custom-table th { background-color: #003366; color: white; padding: 12px; }
    .custom-table td { padding: 10px; border: 1px solid #ddd; font-weight: 600; }

    @media print {
        section[data-testid="stSidebar"], .stDownloadButton, button, iframe, header, [data-testid="stHeader"], .stTextInput, .stSelectbox, .stHeader { display: none !important; }
        .main, .block-container { background-color: white !important; padding: 0 !important; margin: 0 !important; }
        .personal-card { background: transparent !important; color: #003366 !important; border: none !important; }
        .personal-card h1 { color: #003366 !important; font-size: 30px !important; }
    }
    </style>
    """, unsafe_allow_html=True)

# 3. محرك البيانات
@st.cache_data
def load_data_v47():
    f = 'MAR2026.csv'
    if not os.path.exists(f): return None, None
    try:
        df = pd.read_csv(f, header=0, encoding='utf-8-sig', low_memory=False, dtype={'National_ID': str, 'Employee_Code': str})
        df.columns = [c.strip() for c in df.columns]
        p = {'name': ['name_employee', 'اسم'], 'code': ['employee_code', 'كود'], 'date': ['التاريخ', 'date'], 'mang': ['mangment', 'الإدارة'], 'type': ['نوع الصرف'], 'ent': ['أجمالى الاستحقاقات'], 'net': ['الصافي'], 'nat': ['national_id'], 'ded': ['الأجمالى الاستقطاعات'], 'tax': ['ضريبة'], 'stamp': ['دمغة'], 'desc': ['وصف']}
        cols = {k: next((c for c in df.columns if any(w.lower() in c.lower() for w in p[k])), None) for k in p}
        if cols['name']:
            df['Search_Key'] = df[cols['name']].astype(str).str.replace(r'[أإآ]', 'ا', regex=True).str.replace('ى', 'ي').str.replace('ة', 'ه').str.strip()
        
        for k in ['ent', 'net', 'ded', 'tax', 'stamp']:
            if cols[k]: df[cols[k]] = pd.to_numeric(df[cols[k]].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
        return df, cols
    except: return None, None

df_raw, cols = load_data_v47()

if df_raw is not None:
    # --- الصفحة الرئيسية (شاملة كل شيء) ---
    st.markdown("<h2 style='color: #003366;'>💰 نظام مستحقات IDA</h2>", unsafe_allow_html=True)
    
    # فلتر الشهر والتنقل (جوه الصفحة الرئيسية عشان الموبايل)
    c_top1, c_top2 = st.columns(2)
    with c_top1:
        if cols['date']:
            available_months = sorted(df_raw[cols['date']].unique(), reverse=True)
            target_month = st.selectbox("📅 اختر الشهر الضريبي:", available_months)
            df = df_raw[df_raw[cols['date']] == target_month]
        else:
            df = df_raw
            target_month = "غير محدد"
    with c_top2:
        menu = st.selectbox("📌 القائمة الرئيسية:", ["🔍 استعلام الموظفين", "📊 إحصائيات عامة", "📥 تصدير التقارير"])

    st.markdown("---")

    # 1. شاشة الاستعلام
    if menu == "🔍 استعلام الموظفين":
        c_s1, c_s2 = st.columns([1, 2])
        with c_s1: 
            mode = st.selectbox("بحث بـ:", ["الاسم", "الكود"])
        with c_s2: 
            q = st.text_input("✍️ ابحث هنا:") 
        
        if q:
            if mode == "الاسم":
                q_n = re.sub(r'[أإآ]', 'ا', q).replace('ى', 'ي').replace('ة', 'ه').strip()
                res = df[df['Search_Key'].str.contains(q_n, na=False, regex=True, flags=re.IGNORECASE)]
            else:
                res = df[df[cols['code']].astype(str).str.contains(q.strip(), na=False)]
            
            if not res.empty:
                for name, group in res.groupby(cols['name']):
                    st.markdown(f'<div class="personal-card"><h1>{name}</h1><p>🆔 كود: {group.iloc[0][cols["code"]]} | 🏢 {group.iloc[0][cols["mang"]]}</p></div>', unsafe_allow_html=True)
                    m1, m2, m3, m4 = st.columns(4)
                    s_ent, s_tax, s_ded, s_net = group[cols['ent']].sum(), (group[cols['tax']].sum()+group[cols['stamp']].sum()), group[cols['ded']].sum(), group[cols['net']].sum()
                    
                    m1.markdown(f'<div class="stat-card" style="background:#28a745;"><span class="stat-label">إجمالي المستحق</span><span class="stat-value">{s_ent:,.2f}</span></div>', unsafe_allow_html=True)
                    m2.markdown(f'<div class="stat-card" style="background:#ffc107;"><span class="stat-label" style="color:black">ضرائب ودمغة</span><span class="stat-value" style="color:black">{s_tax:,.2f}</span></div>', unsafe_allow_html=True)
                    m3.markdown(f'<div class="stat-card" style="background:#dc3545;"><span class="stat-label">إجمالي استقطاع</span><span class="stat-value">{s_ded:,.2f}</span></div>', unsafe_allow_html=True)
                    m4.markdown(f'<div class="stat-card" style="background:#007bff;"><span class="stat-label">الصافي النهائي</span><span class="stat-value">{s_net:,.2f}</span></div>', unsafe_allow_html=True)
                    
                    st.markdown(f'<div class="custom-table-container">{group[[cols["type"], cols["ent"], cols["net"]]].to_html(index=False, classes="custom-table", escape=False)}</div>', unsafe_allow_html=True)
                    if st.button(f"🖨️ طباعة {name}"):
                        components.html("<script>window.parent.print();</script>")
            else: st.warning("🔍 لا توجد نتائج لهذا الشهر.")

    # 2. الإحصائيات
    elif menu == "📊 إحصائيات عامة":
        c1, c2 = st.columns(2)
        c1.metric("👥 الموظفين", f"{df['Search_Key'].nunique():,}")
        c2.metric("💵 الصافي الكلي", f"{df[cols['net']].sum():,.0f} ج.م")

    # 3. التصدير
    elif menu == "📥 تصدير التقارير":
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False)
        st.download_button("💾 تحميل ملف Excel الشامل", buffer.getvalue(), f"IDA_{target_month}.xlsx")

else:
    st.error("❌ ملف MAR2026.csv غير موجود.")
