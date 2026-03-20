import streamlit as st
import pandas as pd
import re
import os
import io
import streamlit.components.v1 as components

# 1. إعداد الصفحة
st.set_page_config(page_title="نظام IDA للمستحقات", layout="wide", page_icon="IDA_logo_(1).ico")

# 2. تصميم CSS (الفخامة والثبات)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif !important; direction: rtl; text-align: center; }
    .personal-card { background: linear-gradient(135deg, #003366 0%, #005bb7 100%); color: white; padding: 25px; border-radius: 20px; margin-bottom: 25px; border: 2px solid #ffffff; width: 100%; box-shadow: 0 10px 30px rgba(0,0,0,0.2); }
    .personal-card h1 { font-size: 38px !important; font-weight: 800; color: white !important; margin: 0; }
    .stat-card { padding: 20px; border-radius: 15px; color: white !important; text-align: center; margin-bottom: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); min-height: 120px; }
    .stat-value { font-size: 28px !important; font-weight: 800; display: block; }
    .stat-label { font-size: 16px; font-weight: 600; }
    .custom-table-container { width: 100%; overflow-x: auto; border-radius: 15px; background: white; padding: 10px; box-shadow: 0 5px 15px rgba(0,0,0,0.05); }
    .custom-table { width: 100%; border-collapse: collapse; text-align: center; font-size: 19px !important; }
    .custom-table th { background-color: #003366; color: white; padding: 15px; }
    .custom-table td { padding: 15px; border: 1px solid #ddd; font-weight: 700; color: #333; }
    </style>
    """, unsafe_allow_html=True)

# 3. محرك البيانات المطور (مطابق لملف MAR2026.csv بالظبط)
@st.cache_data(ttl=60)
def load_v59_data():
    f = 'MAR2026.csv'
    if not os.path.exists(f): return None, None
    try:
        df = pd.read_csv(f, header=0, encoding='utf-8-sig', low_memory=False)
        df.columns = [c.strip() for c in df.columns]
        
        # ربط الأعمدة الفعلية من ملفك
        cols = {
            'name': 'Name_Employee',
            'code': 'Employee_Code',
            'date': 'NON',
            'mang': 'Mangment',
            'type': 'نوع الصرف',
            'ent': 'أجمالى الاستحقاقات',
            'ded': 'الأجمالى الاستقطاعات',
            'net': 'الصافي',
            'tax_income': 'ضريبة الدخل',
            'tax_stamp': 'ضريبة الدمغة',
            'desc': 'وصف'
        }
        
        # تنظيف وتحويل المبالغ
        money_cols = [cols['ent'], cols['ded'], cols['net'], cols['tax_income'], cols['tax_stamp']]
        for c in money_cols:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c].astype(str).str.replace(',', ''), errors='coerce').fillna(0)

        # عمود البحث الذكي
        df['Search_Key'] = df[cols['name']].astype(str).str.replace(r'[أإآ]', 'ا', regex=True).str.replace('ى', 'ي').str.replace('ة', 'ه').str.strip()
        
        return df, cols
    except: return None, None

df, cols = load_v59_data()

if df is not None:
    st.markdown("<h2 style='color: #003366;'>💰 IDA SYSTEM</h2>", unsafe_allow_html=True)
    
    with st.sidebar:
        st.image("IDA_logo_(1).ico", width=150)
        menu = st.radio("القائمة:", ["🔍 استعلام", "📊 إحصائيات", "📥 تصدير"])

    if menu == "🔍 استعلام":
        q = st.text_input("✍️ ابحث بالاسم أو كود الموظف:")
        if q:
            q_clean = re.sub(r'[أإآ]', 'ا', q).replace('ى', 'ي').replace('ة', 'ه').strip()
            # البحث في الاسم أو الكود
            res = df[(df['Search_Key'].str.contains(q_clean, na=False)) | (df[cols['code']].astype(str).str.contains(q.strip()))]
            
            if not res.empty:
                for name, group in res.groupby(cols['name']):
                    st.markdown(f'<div class="personal-card"><h1>{name}</h1><p>🆔 {group.iloc[0][cols["code"]]} | 🏢 {group.iloc[0][cols["mang"]]}</p></div>', unsafe_allow_html=True)
                    
                    # الحسابات الـ 4 المطلوبة بدقة:
                    s_ent = group[cols['ent']].sum()
                    s_tax_stamp = group[cols['tax_income']].sum() + group[cols['tax_stamp']].sum() # مجموع الضرائب والدمغة
                    s_ded = group[cols['ded']].sum()
                    s_net = group[cols['net']].sum()
                    
                    c1, c2, c3, c4 = st.columns(4)
                    c1.markdown(f'<div class="stat-card" style="background:#28a745;"><span class="stat-label">إجمالي المستحق</span><br><span class="stat-value">{s_ent:,.2f}</span></div>', unsafe_allow_html=True)
                    c2.markdown(f'<div class="stat-card" style="background:#ffc107;"><span class="stat-label" style="color:black">ضرائب ودمغة</span><br><span class="stat-value" style="color:black">{s_tax_stamp:,.2f}</span></div>', unsafe_allow_html=True)
                    c3.markdown(f'<div class="stat-card" style="background:#dc3545;"><span class="stat-label">إجمالي استقطاع</span><br><span class="stat-value">{s_ded:,.2f}</span></div>', unsafe_allow_html=True)
                    c4.markdown(f'<div class="stat-card" style="background:#007bff;"><span class="stat-label">الصافي النهائي</span><br><span class="stat-value">{s_net:,.2f}</span></div>', unsafe_allow_html=True)
                    
                    # جدول التفاصيل
                    t_df = group[[cols['type'], cols['desc'], cols['ent'], cols['net']]].copy()
                    t_df.insert(0, 'م', range(1, len(t_df)+1))
                    st.markdown(f"<div class='custom-table-container'>{t_df.to_html(index=False, classes='custom-table')}</div>", unsafe_allow_html=True)
                    
                    if st.button(f"🖨️ طباعة مفردات {name}"):
                        components.html("<script>window.parent.print();</script>")
            else: st.warning("🔍 لا توجد نتائج.")

    elif menu == "📊 إحصائيات":
        st.metric("إجمالي صافي المنصرف", f"{df[cols['net']].sum():,.2f} ج.م")
        st.bar_chart(df.groupby(cols['mang'])[cols['net']].sum())

    elif menu == "📥 تصدير":
        buffer = io.BytesIO()
        df.to_excel(buffer, index=False)
        st.download_button("💾 تحميل Excel", buffer.getvalue(), "IDA_Report.xlsx")

else: st.error("❌ ملف البيانات غير موجود.")
