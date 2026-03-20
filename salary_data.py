import streamlit as st
import pandas as pd
import re
import os
import io
import streamlit.components.v1 as components

# 1. إعداد الصفحة واللوجو (ثابت)
st.set_page_config(page_title="نظام IDA للمستحقات", layout="wide", page_icon="IDA_logo_(1).ico")

# 2. تصميم CSS (التنسيق القديم الفخم المعتمد - ممنوع اللمس)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif !important; direction: rtl; text-align: center; }
    .app-main-title { color: #003366; font-size: 30px; font-weight: 800; margin-bottom: 25px; border-bottom: 3px solid #003366; display: inline-block; padding-bottom: 10px; }
    
    .personal-card { background: linear-gradient(135deg, #003366 0%, #005bb7 100%); color: white; padding: 25px; border-radius: 20px; margin-bottom: 25px; border: 2px solid #ffffff; width: 100%; box-shadow: 0 10px 30px rgba(0,0,0,0.2); }
    .personal-card h1 { font-size: 35px !important; font-weight: 800; color: white !important; margin: 0; }
    
    .stat-card { padding: 20px; border-radius: 15px; color: white !important; text-align: center; margin-bottom: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
    .stat-value { font-size: 28px !important; font-weight: 800; display: block; color: white !important; }
    .stat-label { color: white !important; font-size: 16px; font-weight: 600; }

    .custom-table-container { width: 100%; overflow-x: auto; border-radius: 15px; background: white; padding: 10px; box-shadow: 0 5px 15px rgba(0,0,0,0.05); }
    .custom-table { width: 100%; border-collapse: collapse; text-align: center; font-size: 18px !important; }
    .custom-table th { background-color: #003366; color: white; padding: 15px; }
    .custom-table td { padding: 12px; border: 1px solid #ddd; font-weight: 600; color: #333; }
    </style>
    """, unsafe_allow_html=True)

# 3. محرك البيانات (تنظيف التاريخ والكود من الـ .0 نهائياً)
@st.cache_data(ttl=60)
def load_v65_data():
    f = 'MAR2026.csv'
    if not os.path.exists(f): return None, None
    try:
        # قراءة أولية
        df = pd.read_csv(f, header=0, encoding='utf-8-sig', low_memory=False)
        df.columns = [c.strip() for c in df.columns]
        
        cols = {
            'name': 'Name_Employee', 'code': 'Employee_Code', 'date': 'NON',
            'mang': 'Mangment', 'type': 'نوع الصرف', 'ent': 'أجمالى الاستحقاقات',
            'tax': 'ضريبة الدخل', 'stamp': 'ضريبة الدمغة', 'ded': 'الأجمالى الاستقطاعات',
            'net': 'الصافي', 'nat': 'National_ID', 'desc': 'وصف'
        }
        
        # الحل القاطع لمشكلة .0 في التاريخ وفي كود الموظف
        for c_key in ['date', 'code']:
            col_name = cols[c_key]
            # نستخدم Regex لحذف أي .0 في نهاية النص غصب عنها
            df[col_name] = df[col_name].astype(str).replace(r'\.0$', '', regex=True).replace('nan', 'غير محدد').str.strip()

        # تحويل المبالغ المالية فقط
        for k in ['ent', 'tax', 'stamp', 'ded', 'net']:
            df[cols[k]] = pd.to_numeric(df[cols[k]].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
        
        # مفتاح البحث عن الاسم
        df['Search_Key'] = df[cols['name']].astype(str).str.replace(r'[أإآ]', 'ا', regex=True).str.replace('ى', 'ي').str.replace('ة', 'ه').str.strip()
        
        return df, cols
    except: return None, None

df_raw, cols = load_v65_data()

if df_raw is not None:
    st.markdown("<div class='app-main-title'>💰 IDA SYSTEM</div>", unsafe_allow_html=True)
    
    with st.sidebar:
        # زرار "مهم جداً" لمسح الذاكرة وتثبيت التواريخ الجديدة
        if st.button("🔄 تحديث البيانات (حل مشكلة التاريخ)"):
            st.cache_data.clear()
            st.rerun()
            
        st.image("IDA_logo_(1).ico", width=150)
        st.markdown("---")
        
        # قائمة الشهور النظيفة (بدون .0)
        unique_dates = sorted([d for d in df_raw[cols['date']].unique() if d != 'غير محدد'], reverse=True)
        available_months = ["الكل"] + unique_dates
        target_month = st.selectbox("📅 اختر شهر الصرف:", available_months)
        
        menu = st.radio("📂 القائمة الرئيسية:", ["🔍 استعلام الموظفين", "📊 إحصائيات عامة", "📥 تصدير التقارير"])

    # تصفية البيانات
    df_filtered = df_raw if target_month == "الكل" else df_raw[df_raw[cols['date']] == target_month]

    if menu == "🔍 استعلام الموظفين":
        q = st.text_input("✍️ ابحث هنا بالاسم أو الكود الشخصي:")
        
        if q:
            q_clean = q.strip()
            # البحث: لو كتبت رقم يبحث في الكود بالظبط، لو حروف يبحث في الاسم
            if q_clean.isdigit():
                res = df_filtered[df_filtered[cols['code']] == q_clean]
            else:
                name_q = re.sub(r'[أإآ]', 'ا', q_clean).replace('ى', 'ي').replace('ة', 'ه')
                res = df_filtered[df_filtered['Search_Key'].str.contains(name_q, na=False)]
            
            if not res.empty:
                for name, group in res.groupby(cols['name']):
                    st.markdown(f'<div class="personal-card"><h1>{name}</h1><p>🆔 كود: {group.iloc[0][cols["code"]]} | 🏢 {group.iloc[0][cols["mang"]]}</p></div>', unsafe_allow_html=True)
                    
                    # الحسابات الدقيقة
                    s_ent = group[cols['ent']].sum()
                    s_tax = group[cols['tax']].sum() + group[cols['stamp']].sum()
                    s_ded = group[cols['ded']].sum()
                    s_net = group[cols['net']].sum()
                    
                    m1, m2, m3, m4 = st.columns(4)
                    m1.markdown(f'<div class="stat-card" style="background:#28a745;"><span class="stat-label">إجمالي المستحق</span><br><span class="stat-value">{s_ent:,.2f}</span></div>', unsafe_allow_html=True)
                    m2.markdown(f'<div class="stat-card" style="background:#ffc107;"><span class="stat-label" style="color:black">ضرائب ودمغة</span><br><span class="stat-value" style="color:black">{s_tax:,.2f}</span></div>', unsafe_allow_html=True)
                    m3.markdown(f'<div class="stat-card" style="background:#dc3545;"><span class="stat-label">إجمالي استقطاع</span><br><span class="stat-value">{s_ded:,.2f}</span></div>', unsafe_allow_html=True)
                    m4.markdown(f'<div class="stat-card" style="background:#007bff;"><span class="stat-label">الصافي النهائي</span><br><span class="stat-value">{s_net:,.2f}</span></div>', unsafe_allow_html=True)
                    
                    # الجدول المعتمد (بدون أرقام صفوف)
                    d_cols = ([cols['date']] if target_month == "الكل" else []) + [cols['type'], cols['desc'], cols['ent'], cols['net']]
                    t_df = group[d_cols].copy()
                    t_df.insert(0, 'م', range(1, len(t_df)+1))
                    st.markdown(f"<div class='custom-table-container'>{t_df.to_html(index=False, classes='custom-table')}</div>", unsafe_allow_html=True)
                    
                    if st.button(f"🖨️ طباعة {name}"):
                        components.html("<script>window.parent.print();</script>")
            else: st.warning("🔍 لا توجد نتائج.")

    elif menu == "📊 إحصائيات عامة":
        st.metric("💵 إجمالي الصافي للفترة", f"{df_filtered[cols['net']].sum():,.2f}")
        st.bar_chart(df_filtered.groupby(cols['mang'])[cols['net']].sum())

    elif menu == "📥 تصدير التقارير":
        buffer = io.BytesIO()
        df_filtered.to_excel(buffer, index=False)
        st.download_button("💾 تحميل Excel", buffer.getvalue(), f"IDA_Report.xlsx")

else: st.error("❌ ملف MAR2026.csv غير موجود.")
