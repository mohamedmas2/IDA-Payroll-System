import streamlit as st
import pandas as pd
import re
import os
import io
import streamlit.components.v1 as components

# 1. إعداد الصفحة واللوجو
st.set_page_config(page_title="نظام IDA للمستحقات", layout="wide", page_icon="IDA_logo_(1).ico")

# 2. تصميم CSS (التنسيق القديم الفخم المعتمد)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif !important; direction: rtl; text-align: center; }
    .main { background-color: #f4f7f9; }
    .personal-card { background: linear-gradient(135deg, #003366 0%, #005bb7 100%); color: white; padding: 25px; border-radius: 20px; margin-bottom: 25px; border: 2px solid #ffffff; width: 100%; }
    .personal-card h1 { font-size: 35px !important; font-weight: 800; color: white !important; margin: 0; }
    .stat-card { padding: 20px; border-radius: 15px; color: white !important; text-align: center; margin-bottom: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
    .stat-value { font-size: 28px !important; font-weight: 800; display: block; color: white !important; }
    .custom-table-container { width: 100%; overflow-x: auto; border-radius: 15px; background: white; padding: 10px; box-shadow: 0 5px 15px rgba(0,0,0,0.05); }
    .custom-table { width: 100%; border-collapse: collapse; text-align: center; }
    .custom-table th { background-color: #003366; color: white; padding: 12px; }
    .custom-table td { padding: 10px; border: 1px solid #ddd; font-weight: 600; }
    </style>
    """, unsafe_allow_html=True)

# 3. محرك البيانات المطور (حل مشكلة 392026.0 نهائياً)
@st.cache_data(ttl=60)
def load_v40_data():
    file_name = 'MAR2026.csv'
    if not os.path.exists(file_name): return None, None
    try:
        # قراءة الملف مع إجبار عمود التاريخ والكود على أن يكونوا نصوصاً
        df = pd.read_csv(file_name, header=0, encoding='utf-8-sig', low_memory=False, dtype={'NON': str, 'Employee_Code': str})
        df.columns = [c.strip() for c in df.columns]
        
        cols = {
            'name': 'Name_Employee', 'code': 'Employee_Code', 'date': 'NON',
            'mang': 'Mangment', 'type': 'نوع الصرف', 'ent': 'أجمالى الاستحقاقات',
            'tax': 'ضريبة الدخل', 'stamp': 'ضريبة الدمغة', 'ded': 'الأجمالى الاستقطاعات',
            'net': 'الصافي', 'nat': 'National_ID', 'desc': 'وصف'
        }
        
        # --- السطر السحري لحذف الـ .0 من التاريخ ---
        df[cols['date']] = df[cols['date']].astype(str).str.replace(r'\.0$', '', regex=True).replace('nan', 'غير محدد')
        
        # تنظيف المبالغ
        for k in ['ent', 'tax', 'stamp', 'ded', 'net']:
            df[cols[k]] = pd.to_numeric(df[cols[k]].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
            
        # تنظيف مفتاح البحث
        df['Search_Key'] = df[cols['name']].astype(str).str.replace(r'[أإآ]', 'ا', regex=True).str.replace('ى', 'ي').str.replace('ة', 'ه').str.strip()
        
        return df, cols
    except: return None, None

df_raw, cols = load_v40_data()

if df_raw is not None:
    with st.sidebar:
        st.image("IDA_logo_(1).ico", width=150)
        st.markdown("---")
        
        # قائمة الشهور نظيفة تماماً
        unique_dates = sorted(df_raw[cols['date']].unique().tolist(), reverse=True)
        available_months = ["الكل"] + [d for d in unique_dates if d != "غير محدد"]
        target_month = st.selectbox("📅 اختر شهر الصرف:", available_months)
        
        menu = st.radio("📌 القائمة الرئيسية:", ["🔍 استعلام الموظفين", "📊 إحصائيات عامة", "📥 تصدير التقارير"])

    # تصفية البيانات (لو الكل، ياخد الملف كله)
    df_filtered = df_raw if target_month == "الكل" else df_raw[df_raw[cols['date']] == target_month]

    if menu == "🔍 استعلام الموظفين":
        st.title(f"🔍 استعلام - {target_month}")
        q = st.text_input("✍️ ابحث هنا بالاسم أو الكود:")
        
        if q:
            q_clean = re.sub(r'[أإآ]', 'ا', q).replace('ى', 'ي').replace('ة', 'ه').strip()
            # البحث الذكي: لو رقم يطابق الكود، لو حروف يطابق الاسم
            if q.isdigit():
                res = df_filtered[df_filtered[cols['code']] == q.strip()]
            else:
                res = df_filtered[df_filtered['Search_Key'].str.contains(q_clean, na=False)]
            
            if not res.empty:
                for name, group in res.groupby(cols['name']):
                    st.markdown(f'<div class="personal-card"><h1>{name}</h1><p>🆔 كود: {group.iloc[0][cols["code"]]} | 🏢 {group.iloc[0][cols["mang"]]}</p></div>', unsafe_allow_html=True)
                    
                    s_ent, s_tax, s_ded, s_net = group[cols['ent']].sum(), (group[cols['tax']].sum() + group[cols['stamp']].sum()), group[cols['ded']].sum(), group[cols['net']].sum()
                    
                    m1, m2, m3, m4 = st.columns(4)
                    m1.markdown(f'<div class="stat-card" style="background:#28a745;"><span class="stat-label">إجمالي المستحق</span><span class="stat-value">{s_ent:,.2f}</span></div>', unsafe_allow_html=True)
                    m2.markdown(f'<div class="stat-card" style="background:#ffc107;"><span class="stat-label" style="color:black">ضرائب ودمغة</span><span class="stat-value" style="color:black">{s_tax:,.2f}</span></div>', unsafe_allow_html=True)
                    m3.markdown(f'<div class="stat-card" style="background:#dc3545;"><span class="stat-label">إجمالي استقطاع</span><span class="stat-value">{s_ded:,.2f}</span></div>', unsafe_allow_html=True)
                    m4.markdown(f'<div class="stat-card" style="background:#007bff;"><span class="stat-label">الصافي النهائي</span><span class="stat-value">{s_net:,.2f}</span></div>', unsafe_allow_html=True)
                    
                    # في حالة "الكل"، بنعرض عمود التاريخ في الجدول
                    d_cols = ([cols['date']] if target_month == "الكل" else []) + [cols['type'], cols['desc'], cols['ent'], cols['net']]
                    st.markdown(f'<div class="custom-table-container">{group[d_cols].to_html(index=False, classes="custom-table")}</div>', unsafe_allow_html=True)
                    
                    if st.button(f"🖨️ طباعة {name}"):
                        components.html("<script>window.parent.print();</script>")
            else: st.warning("🔍 لا توجد نتائج.")

    elif menu == "📊 إحصائيات عامة":
        st.metric("💵 إجمالي الصافي للفترة", f"{df_filtered[cols['net']].sum():,.2f}")
        st.bar_chart(df_filtered.groupby(cols['mang'])[cols['net']].sum())

    elif menu == "📥 تصدير التقارير":
        buffer = io.BytesIO()
        df_filtered.to_excel(buffer, index=False)
        st.download_button("💾 تحميل ملف Excel", buffer.getvalue(), f"IDA_Report.xlsx")

else: st.error("❌ ملف MAR2026.csv غير موجود.")
