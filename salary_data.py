import streamlit as st
import pandas as pd
import re
import os
import io
import streamlit.components.v1 as components

# 1. إعداد الصفحة
st.set_page_config(page_title="نظام IDA للمستحقات", layout="wide", page_icon="💰")

# 2. تصميم CSS (إخفاء Sidebar في الموبايل + تنسيق الجداول)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif !important; direction: rtl; text-align: center; }
    @media (max-width: 768px) { [data-testid="stSidebar"] { display: none !important; } }
    .personal-card { background: linear-gradient(135deg, #003366 0%, #005bb7 100%); color: white; padding: 20px; border-radius: 15px; margin-bottom: 20px; border: 2px solid #ffffff; }
    .stat-card { padding: 15px; border-radius: 12px; color: white !important; text-align: center; margin-bottom: 10px; }
    .stat-value { font-size: 24px !important; font-weight: 800; display: block; }
    .custom-table { width: 100%; border-collapse: collapse; text-align: center; font-size: 14px; }
    .custom-table th { background-color: #003366; color: white; padding: 10px; }
    .custom-table td { padding: 8px; border: 1px solid #ddd; }
    </style>
    """, unsafe_allow_html=True)

# 3. محرك البيانات
@st.cache_data
def load_data_pro():
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

df_raw, cols = load_data_pro()

if df_raw is not None:
    # القائمة الرئيسية في الواجهة
    st.markdown("<h2 style='color: #003366;'>💰 لوحة تحكم IDA الذكية</h2>", unsafe_allow_html=True)
    c_top1, c_top2 = st.columns(2)
    with c_top1:
        target_month = st.selectbox("📅 اختر الشهر الضريبي:", sorted(df_raw[cols['date']].unique(), reverse=True)) if cols['date'] else "الكل"
        df = df_raw[df_raw[cols['date']] == target_month] if cols['date'] else df_raw
    with c_top2:
        menu = st.selectbox("📌 اختر المهمة:", ["🔍 استعلام الموظفين", "📊 إحصائيات عامة وتحليلية", "📥 تصدير التقارير الذكية"])

    st.markdown("---")

    # 1. استعلام الموظفين (نفس النظام القديم)
    if menu == "🔍 استعلام الموظفين":
        c_s1, c_s2 = st.columns([1, 2])
        with c_s1: mode = st.selectbox("بحث بـ:", ["الاسم", "الكود"])
        with c_s2: q = st.text_input("✍️ ابحث هنا:")
        if q:
            if mode == "الاسم":
                q_n = re.sub(r'[أإآ]', 'ا', q).replace('ى', 'ي').replace('ة', 'ه').strip()
                res = df[df['Search_Key'].str.contains(q_n, na=False, regex=True, flags=re.IGNORECASE)]
            else:
                res = df[df[cols['code']].astype(str).str.contains(q.strip(), na=False)]
            if not res.empty:
                for name, group in res.groupby(cols['name']):
                    st.markdown(f'<div class="personal-card"><h1>{name}</h1><p>🆔 {group.iloc[0][cols["code"]]} | 🏢 {group.iloc[0][cols["mang"]]}</p></div>', unsafe_allow_html=True)
                    st.table(group[[cols['type'], cols['ent'], cols['net']]])
            else: st.warning("🔍 لا توجد نتائج.")

    # 2. إحصائيات عامة وتحليلية (التطوير الجديد)
    elif menu == "📊 إحصائيات عامة وتحليلية":
        # كروت سريعة
        k1, k2, k3 = st.columns(3)
        k1.metric("👥 إجمالي الموظفين", f"{df['Search_Key'].nunique():,}")
        k2.metric("💵 إجمالي الصافي", f"{df[cols['net']].sum():,.0f}")
        k3.metric("🏗️ عدد الإدارات", f"{df[cols['mang']].nunique():,}")

        # أ. تحليل الإدارات والبنود
        st.subheader("🏢 تحليل صرف الإدارات حسب بنود الصرف")
        dept_item_analysis = df.groupby([cols['mang'], cols['type']]).agg(
            عدد_الموظفين=(cols['name'], 'nunique'),
            إجمالي_المبلغ=(cols['ent'], 'sum')
        ).reset_index()
        st.dataframe(dept_item_analysis, use_container_width=True)

        # ب. تحليل البنود العام
        st.subheader("📝 ملخص بنود الصرف (على مستوى المؤسسة)")
        item_summary = df.groupby(cols['type']).agg(
            عدد_المستفيدين=(cols['name'], 'nunique'),
            إجمالي_المنصرف=(cols['ent'], 'sum')
        ).sort_values(by='إجمالي_المنصرف', ascending=False)
        st.table(item_summary)

        # ج. رسوم بيانية
        st.subheader("📈 رسم بياني لتوزيع الصرف")
        st.bar_chart(data=dept_item_analysis, x=cols['mang'], y='إجمالي_المبلغ')

    # 3. تصدير التقارير (3 صفحات في ملف واحد)
    elif menu == "📥 تصدير التقارير الذكية":
        st.info("سيتم تصدير ملف إكسيل يحتوي على 3 صفحات: البيانات الخام، تحليل الإدارات، وملخص البنود.")
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            # Sheet 1
            df.drop(columns=['Search_Key']).to_excel(writer, index=False, sheet_name='1-البيانات التفصيلية')
            # Sheet 2
            dept_analysis = df.groupby([cols['mang'], cols['type']]).agg(الموظفين=(cols['name'], 'nunique'), المبلغ=(cols['ent'], 'sum'))
            dept_analysis.to_excel(writer, sheet_name='2-تحليل الإدارات والبنود')
            # Sheet 3
            item_sum = df.groupby(cols['type']).agg(عدد_المستفيدين=(cols['name'], 'nunique'), إجمالي_المبلغ=(cols['ent'], 'sum'))
            item_sum.to_excel(writer, sheet_name='3-ملخص البنود العام')
            
        st.download_button("💾 تحميل التقرير التحليلي الشامل (Excel)", buffer.getvalue(), f"IDA_Full_Analysis_{target_month}.xlsx")

else:
    st.error("❌ ملف MAR2026.csv غير موجود.")
