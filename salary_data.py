import streamlit as st
import pandas as pd
import re
import os
import io
import streamlit.components.v1 as components

# 1. إعداد الصفحة
st.set_page_config(page_title="نظام IDA للمستحقات", layout="wide", page_icon="💎")

# 2. لمسات CSS السحرية (الجمالية والاحترافية)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;900&display=swap');
    
    /* الخلفية العامة */
    .stApp { background-color: #f0f2f6; font-family: 'Cairo', sans-serif; }
    
    /* العنوان الرئيسي المطور */
    .main-header {
        background: linear-gradient(90deg, #003366, #005bb7);
        color: white;
        padding: 20px;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 30px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }

    /* الكروت الشخصية مع تأثير الحركة */
    .personal-card {
        background: white;
        border-right: 8px solid #003366;
        padding: 25px;
        border-radius: 15px;
        margin-bottom: 25px;
        box-shadow: 0 10px 20px rgba(0,0,0,0.05);
        transition: transform 0.3s ease;
    }
    .personal-card:hover { transform: translateY(-5px); box-shadow: 0 15px 30px rgba(0,0,0,0.1); }
    .personal-card h1 { color: #003366 !important; font-weight: 900; margin:0; }

    /* كروت الإحصائيات الملونة (Glassmorphism style) */
    .stat-box {
        padding: 20px;
        border-radius: 20px;
        color: white;
        text-align: center;
        transition: 0.3s;
        border: 1px solid rgba(255,255,255,0.3);
    }
    .stat-box:hover { filter: brightness(1.1); }
    
    /* الجداول الاحترافية */
    .custom-table-container { border-radius: 20px; overflow: hidden; border: 1px solid #ddd; }
    .stTable { background-color: white; }
    
    /* تعديل الـ Sidebar */
    [data-testid="stSidebar"] { background-color: #ffffff; border-left: 1px solid #eee; }
    
    @media print {
        [data-testid="stSidebar"], .stDownloadButton, button, header { display: none !important; }
        .personal-card { border: 2px solid #003366 !important; box-shadow: none !important; }
    }
    </style>
    """, unsafe_allow_html=True)

# 3. محرك البيانات المطور
@st.cache_data(ttl=60)
def load_v52_data():
    file_path = 'MAR2026.csv'
    if not os.path.exists(file_path): return None, None
    try:
        df = pd.read_csv(file_path, header=0, encoding='utf-8-sig', low_memory=False, dtype={'National_ID': str, 'Employee_Code': str})
        df.columns = [c.strip() for c in df.columns]
        p = {
            'name': ['name_employee', 'اسم'], 'code': ['employee_code', 'كود'], 
            'date': ['التاريخ', 'date'], 'mang': ['mangment', 'الإدارة'],
            'type': ['نوع الصرف'], 'ent': ['أجمالى الاستحقاقات'], 
            'tax': ['ضريبة'], 'stamp': ['دمغة'], 'ded': ['الأجمالى الاستقطاعات'], 
            'net': ['الصافي'], 'nat': ['national_id'], 'desc': ['وصف', 'desc']
        }
        cols = {k: next((c for c in df.columns if any(w.lower() in c.lower() for w in p[k])), None) for k in p}
        
        if cols['name']:
            df['Search_Key'] = df[cols['name']].astype(str).str.replace(r'[أإآ]', 'ا', regex=True).str.replace('ى', 'ي').str.replace('ة', 'ه').str.strip()
            
        for k in ['ent', 'tax', 'stamp', 'ded', 'net']:
            if cols[k]: df[cols[k]] = pd.to_numeric(df[cols[k]].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
        
        if cols['date']: df[cols['date']] = df[cols['date']].astype(str).str.strip()
        return df, cols
    except: return None, None

df_raw, cols = load_v52_data()

if df_raw is not None:
    # رأس الصفحة الجمالي
    st.markdown("<div class='main-header'><h1>💎 IDA PAYROLL DASHBOARD</h1><p>نظام الإدارة المالية المتكامل</p></div>", unsafe_allow_html=True)
    
    # القائمة الجانبية
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/3135/3135706.png", width=100) # أيقونة افتراضية
        st.markdown("### 🛠️ التحكم")
        if cols['date']:
            months = ["الكل"] + sorted(df_raw[cols['date']].unique(), reverse=True)
            target_month = st.selectbox("📅 الفترة الضريبية:", months)
            df = df_raw if target_month == "الكل" else df_raw[df_raw[cols['date']] == target_month]
        else:
            target_month = "الكل"
            df = df_raw
            
        menu = st.radio("📂 الانتقال سريعاً:", ["🔍 استعلام الموظفين", "📊 التحليلات المالية", "📥 تحميل التقارير"])

    # --- 1. استعلام الموظفين ---
    if menu == "🔍 استعلام الموظفين":
        c1, c2 = st.columns([1, 2])
        with c1: mode = st.selectbox("بحث بـ:", ["👤 الاسم", "🆔 الكود"])
        with c2: q = st.text_input("✍️ ابدأ البحث هنا...")
        
        if q:
            mode_clean = "الاسم" if "الاسم" in mode else "الكود"
            if mode_clean == "الاسم":
                q_n = re.sub(r'[أإآ]', 'ا', q).replace('ى', 'ي').replace('ة', 'ه').strip()
                res = df[df['Search_Key'].str.contains(q_n, na=False, regex=True, flags=re.IGNORECASE)]
            else:
                res = df[df[cols['code']].astype(str).str.contains(q.strip(), na=False)]
            
            if not res.empty:
                for name, group in res.groupby(cols['name']):
                    st.markdown(f"""
                    <div class="personal-card">
                        <h1>{name}</h1>
                        <p style='color:#666;'>كود: {group.iloc[0][cols['code']]} | إدارة: {group.iloc[0][cols['mang']]}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # كروت إحصائيات الموظف الملونة
                    i1, i2, i3, i4 = st.columns(4)
                    i1.markdown(f"<div class='stat-box' style='background:#2ecc71;'><small>المستحق</small><br><b style='font-size:22px;'>{group[cols['ent']].sum():,.2f}</b></div>", unsafe_allow_html=True)
                    i2.markdown(f"<div class='stat-box' style='background:#f1c40f; color:#333;'><small>الضرائب</small><br><b style='font-size:22px;'>{group[cols['tax']].sum()+group[cols['stamp']].sum():,.2f}</b></div>", unsafe_allow_html=True)
                    i3.markdown(f"<div class='stat-box' style='background:#e74c3c;'><small>الاستقطاع</small><br><b style='font-size:22px;'>{group[cols['ded']].sum():,.2f}</b></div>", unsafe_allow_html=True)
                    i4.markdown(f"<div class='stat-box' style='background:#3498db;'><small>الصافي</small><br><b style='font-size:22px;'>{group[cols['net']].sum():,.2f}</b></div>", unsafe_allow_html=True)
                    
                    # عرض الجدول
                    d_cols = ([cols['date']] if target_month == "الكل" else []) + [cols['type'], cols['desc'], cols['ent'], cols['net']]
                    final_df = group[d_cols].copy()
                    final_df.insert(0, 'م', range(1, len(final_df)+1))
                    st.table(final_df)
                    
                    if st.button(f"🖨️ طباعة بيان {name}"):
                        components.html("<script>window.parent.print();</script>")
            else: st.warning("🔍 لم نجد بيانات مطابقة لهذا البحث.")

    # --- 2. التحليلات المالية (شكل Dashboard حقيقي) ---
    elif menu == "📊 التحليلات المالية":
        st.markdown(f"### 📈 ملخص الأداء المالي - {target_month}")
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("عدد الموظفين", f"{df['Search_Key'].nunique():,}")
        k2.metric("إجمالي الميزانية", f"{df[cols['ent']].sum():,.0f}")
        k3.metric("إجمالي الصافي", f"{df[cols['net']].sum():,.0f}")
        k4.metric("عدد الإدارات", f"{df[cols['mang']].nunique():,}")
        
        st.markdown("---")
        st.subheader("🏢 توزيع الصرف لكل إدارة")
        dept_data = df.groupby(cols['mang']).agg(الصافي=(cols['net'], 'sum')).reset_index()
        st.bar_chart(data=dept_data, x=cols['mang'], y='الصافي')

    # --- 3. تحميل التقارير ---
    elif menu == "📥 تحميل التقارير":
        st.markdown("### 📂 مركز تحميل التقارير")
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='البيانات')
        st.download_button("💾 تحميل ملف Excel الشامل", buffer.getvalue(), f"IDA_Report_{target_month}.xlsx")

else:
    st.error("❌ ملف MAR2026.csv غير موجود.")
