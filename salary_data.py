import streamlit as st
import pandas as pd
import re
import os
import io
import streamlit.components.v1 as components

# محاولة استيراد Plotly
try:
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

# إعداد الصفحة
st.set_page_config(page_title="نظام IDA للمستحقات", layout="wide", page_icon="💰")

# CSS
st.markdown("""
<style>
html, body { direction: rtl; text-align: center; }
</style>
""", unsafe_allow_html=True)

# تحميل البيانات
@st.cache_data
def load_data():
    file_name = 'MAR2026.csv'
    if not os.path.exists(file_name):
        return None, None

    df = pd.read_csv(file_name, encoding='utf-8-sig', dtype=str)
    df.columns = [c.strip() for c in df.columns]

    p = {
        'name': ['name_employee', 'اسم الموظف'],
        'code': ['employee_code', 'كود'],
        'date': ['التاريخ', 'date'],
        'type': ['نوع الصرف'],
        'ent': ['أجمالى الاستحقاقات'],
        'tax': ['ضريبة الدخل'],
        'stamp': ['ضريبة الدمغة'],
        'ded': ['الأجمالى الاستقطاعات'],
        'net': ['الصافي'],
        'nat': ['national_id'],
        'desc': ['وصف']
    }

    cols = {k: next((c for c in df.columns if any(w.lower() in c.lower() for w in p[k])), None) for k in p}

    # تنظيف الاسم
    df[cols['name']] = df[cols['name']].astype(str).str.strip()
    df['Search_Key'] = df[cols['name']]

    # تحويل أرقام
    for k in ['ent', 'tax', 'stamp', 'ded', 'net']:
        if cols[k]:
            df[cols[k]] = pd.to_numeric(df[cols[k]], errors='coerce').fillna(0)

    return df, cols

df_raw, cols = load_data()

if df_raw is not None:

    with st.sidebar:

        # 👇 اختيار الشهر مع "الكل"
        available_months = sorted(df_raw[cols['date']].dropna().unique(), reverse=True)
        available_months = ["الكل"] + available_months

        target_month = st.selectbox("📅 اختر شهر الصرف:", available_months)

        # 👇 الفلترة الصح
        if target_month == "الكل":
            df = df_raw.copy()
        else:
            df = df_raw[df_raw[cols['date']] == target_month]

        menu = st.radio("📌 القائمة:", ["استعلام"])

    # =========================
    # 🔍 البحث
    # =========================
    if menu == "استعلام":

        q = st.text_input("ابحث بالاسم أو الكود")

        if q:

            res = df[
                df[cols['name']].str.contains(q, case=False, na=False) |
                df[cols['code']].astype(str).str.contains(q, na=False)
            ]

            if not res.empty:

                for name, group in res.groupby(cols['name']):

                    st.subheader(name)

                    # إجماليات
                    total_ent = group[cols['ent']].sum()
                    total_ded = group[cols['ded']].sum()
                    total_net = group[cols['net']].sum()

                    col1, col2, col3 = st.columns(3)
                    col1.metric("إجمالي", f"{total_ent:,.0f}")
                    col2.metric("استقطاعات", f"{total_ded:,.0f}")
                    col3.metric("صافي", f"{total_net:,.0f}")

                    # 👇 لو "الكل" نعرض التاريخ
                    if target_month == "الكل":
                        show_cols = [cols['date'], cols['type'], cols['desc'], cols['ent'], cols['net']]
                    else:
                        show_cols = [cols['type'], cols['desc'], cols['ent'], cols['net']]

                    st.dataframe(group[show_cols])

                    if st.button(f"طباعة {name}"):
                        components.html("<script>window.print()</script>")

            else:
                st.warning("لا توجد نتائج")

else:
    st.error("❌ الملف غير موجود")
