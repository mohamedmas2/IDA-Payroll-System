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

# 1. إعداد الصفحة واللوجو
st.set_page_config(page_title="نظام IDA للمستحقات - النسخة الاحترافية", layout="wide", page_icon="IDA_logo_(1).ico")

# 2. تصميم CSS الشامل (حماية الموبايل + تنسيق الجداول الضخمة)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif !important; direction: rtl; text-align: center; }
    .main { background-color: #f4f7f9; }
    
    /* منع الكلام بالطول في الموبايل */
    [data-testid="stSidebar"] * { white-space: nowrap !important; }
    .sidebar-title { color: #003366; text-align: center; font-weight: 800; font-size: 22px; margin-bottom: 10px; }

    /* الكروت الذكية (الشبكة) */
    .stats-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-bottom: 20px; }
    .stat-card { padding: 15px; border-radius: 15px; color: white !important; text-align: center; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
    .stat-value { font-size: 22px !important; font-weight: 800; display: block; color: white !important; }
    .stat-label { color: white !important; font-size: 14px; font-weight: 600; }

    @media (max-width: 768px) { .stats-grid { grid-template-columns: repeat(2, 1fr); } }

    .personal-card { background: linear-gradient(135deg, #003366 0%, #005bb7 100%); color: white; padding: 20px; border-radius: 20px; margin-bottom: 20px; border: 2px solid #ffffff; }
    
    /* تنسيق الجداول الضخمة */
    .custom-table-container { width: 100%; overflow-x: auto; border-radius: 15px; background: white; padding: 10px; box-shadow: 0 5px 15px rgba(0,0,0,0.05); margin-bottom: 20px; }
    .custom-table { width: 100%; border-collapse: collapse; text-align: center; font-size: 15px !important; }
    .custom-table th { background-color: #003366; color: white; padding: 10px; white-space: nowrap; }
    .custom-table td { padding: 8px; border: 1px solid #ddd; font-weight: 600; white-space: nowrap; }

    /* تمييز الصفوف الملونة في تحليل الحسابات */
    .row-highlight { background-color: #f0f8ff; font-weight: 800; color: #003366; }
    </style>
    """, unsafe_allow_html=True)

# 3. محرك البيانات المطور (التعامل مع الـ 109 حساب)
@st.cache_data
def load_v50_data():
    file_name = 'MAR2026.csv'
    if not os.path.exists(file_name): return None, None, [], []
    try:
        df = pd.read_csv(file_name, header=0, encoding='utf-8-sig', low_memory=False, dtype={'National_ID': str, 'Employee_Code': str, 'NON': str})
        df.columns = [c.strip() for c in df.columns]
        
        # تعريف الأعمدة الأساسية
        p = {
            'name': ['name_employee', 'اسم الموظف'], 'code': ['employee_code', 'كود'], 
            'date': ['التاريخ', 'Date', 'NON'], 'mang': ['mangment', 'الإدارة'],
            'ent_total': ['أجمالى الاستحقاقات'], 'ded_total': ['الأجمالى الاستقطاعات'], 'net': ['الصافي']
        }
        cols = {k: next((c for c in df.columns if any(w.lower() in c.lower() for w in p[k])), None) for k in p}

        # تحديد تلقائي للأعمدة المالية (الـ 109 حساب)
        # أي عمود مادي (أرقام) مش من الأعمدة الأساسية هنعتبره "بند مالي"
        exclude = [cols['name'], cols['code'], cols['date'], cols['mang'], 'Search_Key', 'Level', 'وصف', 'نوع الصرف', 'National_ID']
        financial_cols = [c for c in df.columns if c not in exclude and df[c].dtype in ['float64', 'int64']]
        
        # تنظيف البيانات
        df[cols['name']] = df[cols['name']].astype(str).str.strip()
        df['Search_Key'] = df[cols['name']].str.replace(r'[أإآ]', 'ا', regex=True).str.replace('ى', 'ي').str.replace('ة', 'ه')
        
        for c in financial_cols + [cols['ent_total'], cols['ded_total'], cols['net']]:
            df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)

        return df, cols, financial_cols
    except Exception as e:
        st.error(f"خطأ في التحميل: {e}"); return None, None, [], []

df_raw, cols, fin_cols = load_v50_data()

if df_raw is not None:
    with st.sidebar:
        st.image("IDA_logo_(1).ico", width=120)
        st.markdown("<div class='sidebar-title'>IDA SYSTEM PRO</div>", unsafe_allow_html=True)
        st.markdown("---")
        
        unique_dates = sorted([str(d) for d in df_raw[cols['date']].unique() if pd.notna(d)], reverse=True)
        target_month = st.selectbox("📅 اختر الفترة:", ["الكل"] + unique_dates)
        
        menu = st.radio("📌 القائمة الرئيسية:", 
                        ["🔍 الاستعلام السريع", "👤 ملف الموظف التفصيلي", "📖 تحليل الحسابات (109)", "📊 لوحة التحكم", "📥 التصدير"])

    # تصفية البيانات حسب الشهر
    df_f = df_raw if target_month == "الكل" else df_raw[df_raw[cols['date']].astype(str) == target_month]

    # ---------------------------------------------------------------------
    # 1. الاستعلام السريع (الهيكل القديم المحبوب)
    # ---------------------------------------------------------------------
    if menu == "🔍 الاستعلام السريع":
        st.title(f"🔍 استعلام - {target_month}")
        q = st.text_input("✍️ ابحث بالاسم أو الكود:")
        if q:
            q_clean = re.sub(r'[أإآ]', 'ا', q).replace('ى', 'ي').replace('ة', 'ه').strip()
            res = df_f[(df_f['Search_Key'].str.contains(q_clean, na=False)) | (df_f[cols['code']] == q.strip())]
            if not res.empty:
                for name, group in res.groupby(cols['name']):
                    st.markdown(f'<div class="personal-card"><h1>{name}</h1><p>🆔 {group.iloc[0][cols["code"]]} | 🏢 {group.iloc[0][cols["mang"]]}</p></div>', unsafe_allow_html=True)
                    
                    s_ent, s_net = group[cols['ent_total']].sum(), group[cols['net']].sum()
                    s_ded = group[cols['ded_total']].sum()
                    # حساب ضرائب افتراضي من الأعمدة (دمغة + دخل)
                    tax_cols = [c for c in group.columns if 'ضريبة' in c]
                    s_tax = group[tax_cols].sum().sum()

                    st.markdown(f"""
                    <div class="stats-grid">
                        <div class="stat-card" style="background:#28a745;"><span class="stat-label">إجمالي المستحق</span><span class="stat-value">{s_ent:,.2f}</span></div>
                        <div class="stat-card" style="background:#ffc107;"><span class="stat-label" style="color:black">ضرائب ودمغة</span><span class="stat-value" style="color:black">{s_tax:,.2f}</span></div>
                        <div class="stat-card" style="background:#dc3545;"><span class="stat-label">إجمالي استقطاع</span><span class="stat-value">{s_ded:,.2f}</span></div>
                        <div class="stat-card" style="background:#007bff;"><span class="stat-label">الصافي النهائي</span><span class="stat-value">{s_net:,.2f}</span></div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # الجدول مع المسلسل
                    disp = group[[cols['date'], 'نوع الصرف', 'وصف', cols['ent_total'], cols['net']]].copy()
                    disp.insert(0, 'م', range(1, len(disp)+1))
                    st.markdown(f'<div class="custom-table-container">{disp.to_html(index=False, classes="custom-table")}</div>', unsafe_allow_html=True)
            else: st.warning("🔍 لا توجد نتائج.")

    # ---------------------------------------------------------------------
    # 2. ملف الموظف التفصيلي (الـ 61 عمود)
    # ---------------------------------------------------------------------
    elif menu == "👤 ملف الموظف التفصيلي":
        st.title("👤 التحليل التفصيلي لبيانات موظف")
        emp_list = sorted(df_raw[cols['name']].unique())
        selected_emp = st.selectbox("اختر الموظف لعرض ملفه الكامل:", emp_list)
        
        if selected_emp:
            emp_data = df_raw[df_raw[cols['name']] == selected_emp]
            st.info(f"عرض كافة البيانات المالية المسجلة للموظف في جميع الشهور")
            
            # عرض الأعمدة التي تحتوي على قيم فقط (إخفاء الـ 0)
            emp_fin = emp_data[fin_cols].loc[:, (emp_data[fin_cols] != 0).any(axis=0)]
            
            tab1, tab2 = st.tabs(["💰 كافة البنود المالية (استحقاق/استقطاع)", "📉 تطور الدخل"])
            with tab1:
                st.write("البنود التي صرفت/استقطعت فعلياً للموظف:")
                st.dataframe(emp_fin.assign(الفترة=emp_data[cols['date']]).set_index('الفترة'), use_container_width=True)
            with tab2:
                if PLOTLY_AVAILABLE:
                    fig = px.line(emp_data, x=cols['date'], y=cols['net'], title="تطور الصافي الشهري للموظف", markers=True)
                    st.plotly_chart(fig, use_container_width=True)

    # ---------------------------------------------------------------------
    # 3. تحليل الحسابات (الـ 109 حساب)
    # ---------------------------------------------------------------------
    elif menu == "📖 تحليل الحسابات (109)":
        st.title(f"📖 ميزانية الحسابات والبنود - {target_month}")
        
        # تجميع مبالغ كل عمود مالي
        acc_summary = df_f[fin_cols].sum().reset_index()
        acc_summary.columns = ['البند المالي / الحساب', 'إجمالي المبلغ']
        acc_summary = acc_summary[acc_summary['إجمالي المبلغ'] > 0].sort_values(by='إجمالي المبلغ', ascending=False)
        
        col_acc1, col_acc2 = st.columns([2, 1])
        with col_acc1:
            st.markdown(f"<div class='custom-table-container'>{acc_summary.to_html(index=False, classes='custom-table')}</div>", unsafe_allow_html=True)
        with col_acc2:
            st.metric("إجمالي بنود الصرف", f"{acc_summary['إجمالي المبلغ'].sum():,.2f}")
            if PLOTLY_AVAILABLE:
                st.plotly_chart(px.pie(acc_summary.head(10), names='البند المالي / الحساب', values='إجمالي المبلغ', title="أكبر 10 بنود صرف"), use_container_width=True)

    # ---------------------------------------------------------------------
    # 4. لوحة التحكم و 5. التصدير (ثابتين)
    # ---------------------------------------------------------------------
    elif menu == "📊 لوحة التحكم":
        st.title("📊 تحليلات الإدارة العليا")
        c1, c2 = st.columns(2)
        c1.metric("إجمالي القوة البشرية", len(df_f[cols['name']].unique()))
        c2.metric("إجمالي صافي المنصرف", f"{df_f[cols['net']].sum():,.2f}")
        st.bar_chart(df_f.groupby(cols['mang'])[cols['net']].sum())

    elif menu == "📥 التصدير":
        st.title("📥 مركز تصدير البيانات")
        buffer = io.BytesIO()
        df_f.to_excel(buffer, index=False)
        st.download_button("💾 تحميل التقرير الحالي (Excel)", buffer.getvalue(), f"IDA_Report_{target_month}.xlsx")

else: st.error("❌ ملف MAR2026.csv غير موجود بجانب الكود.")
