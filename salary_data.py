import streamlit as st
import pandas as pd
import re
import os
import io
import streamlit.components.v1 as components

# 1. إعداد الصفحة
st.set_page_config(page_title="نظام IDA للمستحقات", layout="wide", page_icon="IDA_logo_(1).ico")

# 2. تصميم CSS (التنسيق القديم الفخم - بدون تغيير)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif !important; direction: rtl; text-align: center; }
    .app-main-title { color: #003366; font-size: 30px; font-weight: 800; margin-bottom: 25px; border-bottom: 3px solid #003366; display: inline-block; padding-bottom: 10px; }
    .personal-card { background: linear-gradient(135deg, #003366 0%, #005bb7 100%); color: white; padding: 25px; border-radius: 20px; margin-bottom: 25px; border: 2px solid #ffffff; width: 100%; box-shadow: 0 10px 30px rgba(0,0,0,0.2); }
    .personal-card h1 { font-size: 35px !important; font-weight: 800; color: white !important; margin: 0; }
    .stat-card { padding: 20px; border-radius: 15px; color: white !important; text-align: center; margin-bottom: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
    .stat-value { font-size: 28px !important; font-weight: 800; display: block; }
    .custom-table-container { width: 100%; overflow-x: auto; border-radius: 15px; background: white; padding: 10px; box-shadow: 0 5px 15px rgba(0,0,0,0.05); }
    .custom-table { width: 100%; border-collapse: collapse; text-align: center; font-size: 18px !important; }
    .custom-table th { background-color: #003366; color: white; padding: 15px; }
    .custom-table td { padding: 12px; border: 1px solid #ddd; font-weight: 600; color: #333; }
    </style>
    """, unsafe_allow_html=True)

# 3. محرك البيانات الدقيق
@st.cache_data(ttl=60)
def load_v63_data():
    f = 'MAR2026.csv'
    if not os.path.exists(f): return None, None
    try:
        df = pd.read_csv(f, header=0, encoding='utf-8-sig', low_memory=False)
        df.columns = [c.strip() for c in df.columns]
        
        # ربط الأعمدة الفعلية
        cols = {
            'name': 'Name_Employee',
            'code': 'Employee_Code',
            'date': 'NON',
            'mang': 'Mangment',
            'type': 'نوع الصرف',
            'ent': 'أجمالى الاستحقاقات',
            'tax_income': 'ضريبة الدخل',
            'tax_stamp': 'ضريبة الدمغة',
            'ded': 'الأجمالى الاستقطاعات',
            'net': 'الصافي',
            'desc': 'وصف'
        }
        
        # تحويل المبالغ لأرقام
        for k in ['ent', 'tax_income', 'tax_stamp', 'ded', 'net']:
            df[cols[k]] = pd.to_numeric(df[cols[k]].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
        
        # تنظيف كود الموظف (إزالة الفواصل لو وجدت)
        df[cols['code']] = df[cols['code']].astype(str).str.split('.').str[0].str.strip()
        
        # مفتاح البحث عن الاسم
        df['Search_Name'] = df[cols['name']].astype(str).str.replace(r'[أإآ]', 'ا', regex=True).str.replace('ى', 'ي').str.replace('ة', 'ه').str.strip()
        
        return df, cols
    except: return None, None

df_raw, cols = load_v63_data()

if df_raw is not None:
    st.markdown("<div class='app-main-title'>💰 IDA SYSTEM</div>", unsafe_allow_html=True)
    
    with st.sidebar:
        st.image("IDA_logo_(1).ico", width=150)
        st.markdown("---")
        available_months = ["الكل"] + sorted(df_raw[cols['date']].unique().astype(str), reverse=True)
        target_month = st.selectbox("📅 اختر الفترة:", available_months)
        menu = st.radio("📂 القائمة:", ["🔍 استعلام الموظفين", "📊 إحصائيات", "📥 تصدير"])

    # تصفية البيانات حسب الشهر
    df_filtered = df_raw if target_month == "الكل" else df_raw[df_raw[cols['date']].astype(str) == target_month]

    if menu == "🔍 استعلام الموظفين":
        q = st.text_input("✍️ ابحث هنا (بالاسم أو الكود الشخصي فقط):")
        
        if q:
            q_clean = q.strip()
            # فحص إذا كان البحث رقمي (كود) أو نصي (اسم)
            if q_clean.isdigit():
                # بحث دقيق بالكود الشخصي فقط
                res = df_filtered[df_filtered[cols['code']] == q_clean]
            else:
                # بحث بالاسم مع تنظيف الحروف
                name_q = re.sub(r'[أإآ]', 'ا', q_clean).replace('ى', 'ي').replace('ة', 'ه')
                res = df_filtered[df_filtered['Search_Name'].str.contains(name_q, na=False)]
            
            if not res.empty:
                for name, group in res.groupby(cols['name']):
                    st.markdown(f'<div class="personal-card"><h1>{name}</h1><p>🆔 كود: {group.iloc[0][cols["code"]]} | 🏢 {group.iloc[0][cols["mang"]]}</p></div>', unsafe_allow_html=True)
                    
                    s_ent = group[cols['ent']].sum()
                    s_tax = group[cols['tax_income']].sum() + group[cols['tax_stamp']].sum()
                    s_ded = group[cols['ded']].sum()
                    s_net = group[cols['net']].sum()
                    
                    m1, m2, m3, m4 = st.columns(4)
                    m1.markdown(f'<div class="stat-card" style="background:#28a745;"><span class="stat-label">إجمالي المستحق</span><br><span class="stat-value">{s_ent:,.2f}</span></div>', unsafe_allow_html=True)
                    m2.markdown(f'<div class="stat-card" style="background:#ffc107;"><span class="stat-label" style="color:black">ضرائب ودمغة</span><br><span class="stat-value" style="color:black">{s_tax:,.2f}</span></div>', unsafe_allow_html=True)
                    m3.markdown(f'<div class="stat-card" style="background:#dc3545;"><span class="stat-label">إجمالي استقطاع</span><br><span class="stat-value">{s_ded:,.2f}</span></div>', unsafe_allow_html=True)
                    m4.markdown(f'<div class="stat-card" style="background:#007bff;"><span class="stat-label">الصافي النهائي</span><br><span class="stat-value">{s_net:,.2f}</span></div>', unsafe_allow_html=True)
                    
                    d_cols = ([cols['date']] if target_month == "الكل" else []) + [cols['type'], cols['desc'], cols['ent'], cols['net']]
                    final_df = group[d_cols].copy()
                    final_df.insert(0, 'م', range(1, len(final_df)+1))
                    st.markdown(f"<div class='custom-table-container'>{final_df.to_html(index=False, classes='custom-table')}</div>", unsafe_allow_html=True)
                    if st.button(f"🖨️ طباعة {name}"):
                        components.html("<script>window.parent.print();</script>")
            else: st.warning("🔍 لا توجد نتائج مطابقة لهذا الموظف.")

    elif menu == "📊 إحصائيات":
        st.metric("صافي المنصرف", f"{df_filtered[cols['net']].sum():,.2f}")
        st.bar_chart(df_filtered.groupby(cols['mang'])[cols['net']].sum())

    elif menu == "📥 تصدير":
        buffer = io.BytesIO()
        df_filtered.to_excel(buffer, index=False)
        st.download_button("💾 تحميل Excel", buffer.getvalue(), f"IDA_Report.xlsx")

else: st.error("❌ تأكد من ملف MAR2026.csv")
