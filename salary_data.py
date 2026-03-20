import streamlit as st
import pandas as pd
import re
import os
import io
import streamlit.components.v1 as components

try:
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

# 1. إعداد الصفحة
st.set_page_config(page_title="نظام IDA للمستحقات - Pro", layout="wide", page_icon="IDA_logo_(1).ico")

# 2. تصميم CSS (نفس التنسيق اللي ظبطناه للموبايل)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif !important; direction: rtl; text-align: center; }
    [data-testid="stSidebar"] * { white-space: nowrap !important; }
    .sidebar-title { color: #003366; text-align: center; font-weight: 800; font-size: 20px; }
    .stats-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 20px; }
    .stat-card { padding: 15px; border-radius: 12px; color: white !important; text-align: center; }
    .stat-value { font-size: 20px !important; font-weight: 800; display: block; color: white !important; }
    .stat-label { color: white !important; font-size: 13px; font-weight: 600; }
    @media (max-width: 768px) { .stats-grid { grid-template-columns: repeat(2, 1fr); } }
    .personal-card { background: linear-gradient(135deg, #003366 0%, #005bb7 100%); color: white; padding: 20px; border-radius: 15px; margin-bottom: 15px; }
    .custom-table-container { width: 100%; overflow-x: auto; border-radius: 10px; background: white; padding: 5px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }
    .custom-table { width: 100%; border-collapse: collapse; text-align: center; font-size: 14px; }
    .custom-table th { background-color: #003366; color: white; padding: 10px; }
    .custom-table td { padding: 8px; border: 1px solid #ddd; font-weight: 600; }
    </style>
    """, unsafe_allow_html=True)

# 3. تحميل البيانات (مع حل مشكلة التاريخ و NON)
@st.cache_data
def load_v51_data():
    file_name = 'MAR2026.csv'
    if not os.path.exists(file_name): return None, None, []
    try:
        df = pd.read_csv(file_name, header=0, encoding='utf-8-sig', low_memory=False, dtype={'National_ID': str, 'Employee_Code': str})
        df.columns = [c.strip() for c in df.columns]
        
        # تحديد الأعمدة الأساسية (إجبارياً)
        p = {
            'name': ['name_employee', 'اسم الموظف'],
            'code': ['employee_code', 'كود'],
            'date': ['التاريخ', 'Date'], # لغينا NON تماماً هنا
            'mang': ['mangment', 'الإدارة'],
            'ent': ['أجمالى الاستحقاقات'],
            'ded': ['الأجمالى الاستقطاعات'],
            'net': ['الصافي'],
            'nat': ['national_id', 'الرقم القومي']
        }
        
        cols = {k: next((c for c in df.columns if any(w.lower() in c.lower() for w in p[k])), None) for k in p}
        
        # تحويل الأعمدة المالية لأرقام
        all_numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        for c in all_numeric_cols:
            df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
            
        # تحديد الـ 109 حساب (أي عمود رقمي مش المجموع الكلي)
        exclude_from_fin = [cols['ent'], cols['ded'], cols['net']]
        fin_cols = [c for c in all_numeric_cols if c not in exclude_from_fin]
        
        # تنظيف الأسماء للبحث
        df[cols['name']] = df[cols['name']].astype(str).str.strip()
        df['Search_Key'] = df[cols['name']].str.replace(r'[أإآ]', 'ا', regex=True).str.replace('ى', 'ي').str.replace('ة', 'ه')
        
        return df, cols, fin_cols
    except Exception as e:
        st.error(f"خطأ: {e}"); return None, None, []

df_raw, cols, fin_cols = load_v51_data()

if df_raw is not None:
    with st.sidebar:
        st.image("IDA_logo_(1).ico", width=120)
        st.markdown("<div class='sidebar-title'>IDA SYSTEM PRO</div>", unsafe_allow_html=True)
        st.markdown("---")
        
        # حل مشكلة التاريخ
        dates = sorted([str(d) for d in df_raw[cols['date']].unique() if pd.notna(d) and str(d).lower() != 'nan'], reverse=True)
        target_period = st.selectbox("📅 اختر الفترة:", ["الكل"] + dates)
        
        menu = st.radio("📌 القائمة:", ["🔍 الاستعلام السريع", "👤 ملف الموظف التفصيلي", "📖 تحليل الحسابات", "📊 لوحة التحكم", "📥 التصدير"])

    # تصفية البيانات
    df_f = df_raw if target_period == "الكل" else df_raw[df_raw[cols['date']].astype(str) == target_period]

    # --- 1. الاستعلام السريع ---
    if menu == "🔍 الاستعلام السريع":
        st.title(f"🔍 استعلام - {target_period}")
        q = st.text_input("✍️ ابحث بالاسم أو الكود:")
        if q:
            q_c = re.sub(r'[أإآ]', 'ا', q).replace('ى', 'ي').replace('ة', 'ه').strip()
            res = df_f[(df_f['Search_Key'].str.contains(q_c, na=False)) | (df_f[cols['code']].astype(str) == q.strip())]
            if not res.empty:
                for name, gp in res.groupby(cols['name']):
                    st.markdown(f'<div class="personal-card"><h1>{name}</h1><p>🆔 {gp.iloc[0][cols["code"]]} | 🏢 {gp.iloc[0][cols["mang"]]}</p></div>', unsafe_allow_html=True)
                    # الكروت الملونة
                    st.markdown(f"""<div class="stats-grid">
                        <div class="stat-card" style="background:#28a745;"><span class="stat-label">المستحق</span><span class="stat-value">{gp[cols['ent']].sum():,.2f}</span></div>
                        <div class="stat-card" style="background:#dc3545;"><span class="stat-label">الاستقطاع</span><span class="stat-value">{gp[cols['ded']].sum():,.2f}</span></div>
                        <div class="stat-card" style="background:#007bff;"><span class="stat-label">الصافي</span><span class="stat-value">{gp[cols['net']].sum():,.2f}</span></div>
                        <div class="stat-card" style="background:#6c757d;"><span class="stat-label">العمليات</span><span class="stat-value">{len(gp)}</span></div>
                    </div>""", unsafe_allow_html=True)
                    # الجدول المعتاد
                    disp = gp[[cols['date'], 'نوع الصرف', cols['ent'], cols['net']]].copy()
                    disp.insert(0, 'م', range(1, len(disp)+1))
                    st.markdown(f'<div class="custom-table-container">{disp.to_html(index=False, classes="custom-table")}</div>', unsafe_allow_html=True)
            else: st.warning("🔍 لا توجد نتائج.")

    # --- 2. ملف الموظف (تم إصلاح تطور الدخل) ---
    elif menu == "👤 ملف الموظف التفصيلي":
        st.title("👤 تحليل ملف الموظف")
        emp_name = st.selectbox("اختر الموظف:", sorted(df_raw[cols['name']].unique()))
        if emp_name:
            e_data = df_raw[df_raw[cols['name']] == emp_name].sort_values(cols['date'])
            t1, t2 = st.tabs(["📊 كافة البنود المالية", "📈 تطور الدخل الشهري"])
            with t1:
                # عرض الأعمدة اللي فيها مبالغ بس (الـ 61 عمود)
                e_fin = e_data[fin_cols].loc[:, (e_data[fin_cols] != 0).any(axis=0)]
                st.dataframe(e_fin.assign(التاريخ=e_data[cols['date']]).set_index('التاريخ'), use_container_width=True)
            with t2:
                if PLOTLY_AVAILABLE and not e_data.empty:
                    # تجميع الصافي حسب التاريخ للرسم
                    history = e_data.groupby(cols['date'])[cols['net']].sum().reset_index()
                    fig = px.line(history, x=cols['date'], y=cols['net'], title=f"مسار الصافي لـ {emp_name}", markers=True)
                    st.plotly_chart(fig, use_container_width=True)

    # --- 3. تحليل الحسابات (الـ 109 حساب) ---
    elif menu == "📖 تحليل الحسابات":
        st.title(f"📖 إجماليات الحسابات - {target_period}")
        acc_vals = df_f[fin_cols].sum().reset_index()
        acc_vals.columns = ['الحساب', 'الإجمالي']
        acc_vals = acc_vals[acc_vals['الإجمالي'] > 0].sort_values('الإجمالي', ascending=False)
        st.dataframe(acc_vals, use_container_width=True, height=400)

    # --- باقي التابات ---
    elif menu == "📊 لوحة التحكم":
        st.title("📊 مؤشرات عامة")
        st.bar_chart(df_f.groupby(cols['mang'])[cols['net']].sum())
    elif menu == "📥 التصدير":
        st.title("📥 تحميل البيانات")
        buf = io.BytesIO(); df_f.to_excel(buf, index=False)
        st.download_button("💾 Excel", buf.getvalue(), "IDA_Report.xlsx")

else: st.error("❌ تأكد من وجود ملف MAR2026.csv")
