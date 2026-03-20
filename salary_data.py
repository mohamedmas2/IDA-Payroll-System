import streamlit as st
import pandas as pd
import re
import os
import io
import streamlit.components.v1 as components

# 1. إعداد الصفحة
st.set_page_config(page_title="نظام IDA للمستحقات", layout="wide", page_icon="IDA_logo_(1).ico")

# 2. تصميم CSS (الفخامة والدقة)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif !important; direction: rtl; text-align: center; }
    [data-testid="stSidebar"] * { white-space: nowrap !important; }
    .app-main-title { color: #003366; font-size: 32px; font-weight: 800; border-bottom: 3px solid #003366; display: inline-block; padding-bottom: 10px; }
    .personal-card { background: linear-gradient(135deg, #003366 0%, #005bb7 100%); color: white; padding: 25px; border-radius: 20px; margin-bottom: 25px; border: 2px solid #ffffff; width: 100%; box-shadow: 0 10px 30px rgba(0,0,0,0.2); }
    .personal-card h1 { font-size: 38px !important; font-weight: 800; color: white !important; margin: 0; }
    .stat-card { padding: 20px; border-radius: 15px; color: white !important; text-align: center; margin-bottom: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
    .stat-value { font-size: 30px !important; font-weight: 800; display: block; }
    .custom-table-container { width: 100%; overflow-x: auto; border-radius: 15px; background: white; padding: 10px; box-shadow: 0 5px 15px rgba(0,0,0,0.05); }
    .custom-table { width: 100%; border-collapse: collapse; text-align: center; font-size: 19px !important; }
    .custom-table th { background-color: #003366; color: white; padding: 15px; }
    .custom-table td { padding: 15px; border: 1px solid #ddd; font-weight: 700; color: #333; }
    </style>
    """, unsafe_allow_html=True)

# 3. محرك البيانات المطور (الدقة الحسابية)
@st.cache_data(ttl=60)
def load_v57_data():
    f = 'MAR2026.csv'
    if not os.path.exists(f): return None, None
    try:
        df = pd.read_csv(f, header=0, encoding='utf-8-sig', low_memory=False, dtype={'National_ID': str, 'Employee_Code': str})
        df.columns = [c.strip() for c in df.columns]
        
        # خريطة الأعمدة
        p = {
            'name': ['name_employee', 'اسم'], 'code': ['employee_code', 'كود'], 
            'date': ['التاريخ', 'date'], 'mang': ['mangment', 'الإدارة'],
            'type': ['نوع الصرف'], 'ent': ['أجمالى الاستحقاقات'], 
            'tax': ['ضريبة الدخل', 'ضريبة'], 'stamp': ['ضريبة الدمغة', 'دمغة'], 
            'ded': ['الأجمالى الاستقطاعات'], 'net': ['الصافي'], 
            'nat': ['national_id', 'الرقم القومي'], 'desc': ['وصف']
        }
        cols = {k: next((c for c in df.columns if any(w.lower() in c.lower() for w in p[k])), None) for k in p}
        
        # تنظيف الأسماء للبحث
        if cols['name']:
            df['Search_Key'] = df[cols['name']].astype(str).str.replace(r'[أإآ]', 'ا', regex=True).str.replace('ى', 'ي').str.replace('ة', 'ه').str.strip()
            
        # دالة تنظيف الأرقام الصارمة
        def strict_numeric(val):
            if pd.isna(val): return 0.0
            v = str(val).replace(',', '').strip()
            try: return float(v)
            except: return 0.0
            
        # تطبيق التنظيف على كل أعمدة المبالغ
        money_keys = ['ent', 'tax', 'stamp', 'ded', 'net']
        for k in money_keys:
            if cols[k]:
                df[cols[k]] = df[cols[k]].apply(strict_numeric)
            else:
                # لو العمود مش موجود أصلاً في الإكسيل، ننشئه بقيمة صفر عشان الحسابات متفصلش
                df[k] = 0.0
                cols[k] = k

        return df, cols
    except: return None, None

df_raw, cols = load_v57_data()

if df_raw is not None:
    st.markdown("<div class='app-main-title'>💰 IDA SYSTEM</div>", unsafe_allow_html=True)
    
    with st.sidebar:
        st.image("IDA_logo_(1).ico", width=150)
        st.markdown("---")
        if cols['date']:
            months = ["الكل"] + sorted(df_raw[cols['date']].unique(), reverse=True)
            target_month = st.selectbox("📅 اختر الفترة:", months)
            df = df_raw if target_month == "الكل" else df_raw[df_raw[cols['date']] == target_month]
        else:
            target_month = "الكل"
            df = df_raw
        menu = st.radio("📂 القائمة:", ["🔍 استعلام", "📊 إحصائيات", "📥 تصدير"])

    if menu == "🔍 استعلام":
        c1, c2 = st.columns([1, 2])
        with c1: mode = st.selectbox("بحث بـ:", ["👤 الاسم", "🆔 الكود"])
        with c2: q = st.text_input("✍️ ابحث هنا:")
        
        if q:
            if "الاسم" in mode:
                q_n = re.sub(r'[أإآ]', 'ا', q).replace('ى', 'ي').replace('ة', 'ه').strip()
                res = df[df['Search_Key'].str.contains(q_n, na=False, regex=True, flags=re.IGNORECASE)]
            else:
                res = df[df[cols['code']].astype(str).str.contains(q.strip(), na=False)]
            
            if not res.empty:
                for name, group in res.groupby(cols['name']):
                    st.markdown(f'<div class="personal-card"><h1>{name}</h1><p>🆔 كود: {group.iloc[0][cols["code"]]} | 🏢 {group.iloc[0][cols["mang"]]}</p></div>', unsafe_allow_html=True)
                    
                    # الحسابات الدقيقة
                    total_ent = group[cols['ent']].sum()
                    total_taxes = group[cols['tax']].sum() + group[cols['stamp']].sum()
                    total_ded = group[cols['ded']].sum()
                    total_net = group[cols['net']].sum()
                    
                    i1, i2, i3, i4 = st.columns(4)
                    i1.markdown(f'<div class="stat-card" style="background:#28a745;"><span class="stat-label">إجمالي المستحق</span><br><span class="stat-value">{total_ent:,.2f}</span></div>', unsafe_allow_html=True)
                    i2.markdown(f'<div class="stat-card" style="background:#ffc107;"><span class="stat-label" style="color:black">ضرائب ودمغة</span><br><span class="stat-value" style="color:black">{total_taxes:,.2f}</span></div>', unsafe_allow_html=True)
                    i3.markdown(f'<div class="stat-card" style="background:#dc3545;"><span class="stat-label">إجمالي استقطاع</span><br><span class="stat-value">{total_ded:,.2f}</span></div>', unsafe_allow_html=True)
                    i4.markdown(f'<div class="stat-card" style="background:#007bff;"><span class="stat-label">الصافي النهائي</span><br><span class="stat-value">{total_net:,.2f}</span></div>', unsafe_allow_html=True)
                    
                    # الجدول
                    d_cols = ([cols['date']] if target_month == "الكل" else []) + [cols['type'], cols['desc'], cols['ent'], cols['net']]
                    final_df = group[d_cols].copy()
                    final_df.insert(0, 'م', range(1, len(final_df)+1))
                    st.markdown(f"<div class='custom-table-container'>{final_df.to_html(index=False, classes='custom-table', escape=False)}</div>", unsafe_allow_html=True)
                    
                    if st.button(f"🖨️ طباعة {name}"):
                        components.html("<script>window.parent.print();</script>")
            else: st.warning("🔍 لا توجد نتائج.")

    elif menu == "📊 إحصائيات":
        st.subheader(f"📊 ملخص {target_month}")
        k1, k2, k3 = st.columns(3)
        k1.metric("الموظفين", f"{df['Search_Key'].nunique():,}")
        k2.metric("الإجمالي", f"{df[cols['ent']].sum():,.2f}")
        k3.metric("الصافي", f"{df[cols['net']].sum():,.2f}")
        st.bar_chart(df.groupby(cols['mang'])[cols['net']].sum())

    elif menu == "📥 تصدير":
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df.drop(columns=['Search_Key']).to_excel(writer, index=False)
        st.download_button("💾 تحميل Excel", buffer.getvalue(), f"IDA_Report_{target_month}.xlsx")

else: st.error("❌ ملف MAR2026.csv غير موجود.")
