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
st.set_page_config(page_title="IDA Payroll System Pro", layout="wide", page_icon="IDA_logo_(1).ico")

# 2. تصميم CSS الاحترافي (حماية الموبايل + تنسيق الجداول)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif !important; direction: rtl; text-align: center; }
    .main { background-color: #f8f9fa; }
    
    /* منع الكلام بالطول وتنسيق الـ Sidebar */
    [data-testid="stSidebar"] * { white-space: nowrap !important; }
    .sidebar-title { color: #003366; text-align: center; font-weight: 800; font-size: 20px; margin-bottom: 20px; }

    /* شبكة الكروت الذكية (للموبايل والكمبيوتر) */
    .stats-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-bottom: 20px; }
    .stat-card { padding: 20px; border-radius: 15px; color: white !important; text-align: center; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
    .stat-value { font-size: 24px !important; font-weight: 800; display: block; color: white !important; }
    .stat-label { color: white !important; font-size: 14px; font-weight: 600; }

    @media (max-width: 768px) { .stats-grid { grid-template-columns: repeat(2, 1fr); } }

    .personal-card { background: linear-gradient(135deg, #003366 0%, #005bb7 100%); color: white; padding: 25px; border-radius: 20px; margin-bottom: 20px; border: 2px solid #ffffff; }
    .personal-card h1 { font-size: 28px !important; color: white !important; margin: 0; }
    
    .custom-table-container { width: 100%; overflow-x: auto; border-radius: 12px; background: white; padding: 10px; box-shadow: 0 5px 15px rgba(0,0,0,0.05); }
    .custom-table { width: 100%; border-collapse: collapse; text-align: center; }
    .custom-table th { background-color: #003366; color: white; padding: 12px; white-space: nowrap; }
    .custom-table td { padding: 10px; border: 1px solid #ddd; font-weight: 600; white-space: nowrap; }
    </style>
    """, unsafe_allow_html=True)

# 3. محرك البيانات المستقر
@st.cache_data
def load_v52_data():
    f = 'MAR2026.csv'
    if not os.path.exists(f): return None, None, []
    try:
        df = pd.read_csv(f, header=0, encoding='utf-8-sig', low_memory=False, dtype={'National_ID': str, 'Employee_Code': str})
        df.columns = [c.strip() for c in df.columns]
        
        # ربط الأعمدة (التاريخ ثابت على Date)
        p = {
            'name': 'Name_Employee', 'code': 'Employee_Code', 'date': 'Date',
            'mang': 'Mangment', 'ent': 'أجمالى الاستحقاقات', 'ded': 'الأجمالى الاستقطاعات',
            'net': 'الصافي', 'desc': 'وصف', 'type': 'نوع الصرف'
        }
        cols = {k: v for k, v in p.items() if v in df.columns}
        
        # تحويل الأعمدة المالية وتحديد الـ 109 حساب
        num_cols = df.select_dtypes(include=['number']).columns.tolist()
        for c in num_cols:
            df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
            
        fin_items = [c for c in num_cols if c not in [p['ent'], p['ded'], p['net']]]
        df['Search_Key'] = df[p['name']].astype(str).str.replace(r'[أإآ]', 'ا', regex=True).str.replace('ى', 'ي').str.replace('ة', 'ه').str.strip()
        
        return df, cols, fin_items
    except Exception as e:
        st.error(f"Error: {e}"); return None, None, []

df_raw, cols, fin_cols = load_v52_data()

if df_raw is not None:
    with st.sidebar:
        st.image("IDA_logo_(1).ico", width=130)
        st.markdown("<div class='sidebar-title'>IDA PAYROLL PRO</div>", unsafe_allow_html=True)
        st.markdown("---")
        dates = sorted([str(d) for d in df_raw[cols['date']].unique() if pd.notna(d)], reverse=True)
        target_month = st.selectbox("📅 اختر الفترة:", ["الكل"] + dates)
        menu = st.radio("📌 القائمة:", ["🔍 الاستعلام السريع", "👤 ملف الموظف التفصيلي", "📖 تحليل الحسابات", "📊 لوحة التحكم", "📥 التصدير"])

    df_f = df_raw if target_month == "الكل" else df_raw[df_raw[cols['date']].astype(str) == target_month]

    # --- 1. الاستعلام السريع (رجوع الوصف والضرائب) ---
    if menu == "🔍 الاستعلام السريع":
        q = st.text_input("✍️ ابحث بالاسم أو الكود:")
        if q:
            q_c = re.sub(r'[أإآ]', 'ا', q).replace('ى', 'ي').replace('ة', 'ه').strip()
            res = df_f[(df_f['Search_Key'].str.contains(q_c, na=False)) | (df_f[cols['code']] == q.strip())]
            if not res.empty:
                for name, gp in res.groupby(cols['name']):
                    st.markdown(f'<div class="personal-card"><h1>{name}</h1><p>🆔 {gp.iloc[0][cols["code"]]} | 🏢 {gp.iloc[0][cols["mang"]]}</p></div>', unsafe_allow_html=True)
                    
                    # حساب الضرائب والدمغة من الأعمدة
                    tax_val = gp[[c for c in gp.columns if any(w in c for w in ['ضريبة', 'دمغة'])]].sum().sum()
                    
                    st.markdown(f"""<div class="stats-grid">
                        <div class="stat-card" style="background:#28a745;"><span class="stat-label">إجمالي المستحق</span><span class="stat-value">{gp[cols['ent']].sum():,.2f}</span></div>
                        <div class="stat-card" style="background:#ffc107;"><span class="stat-label" style="color:black">ضرائب ودمغة</span><span class="stat-value" style="color:black">{tax_val:,.2f}</span></div>
                        <div class="stat-card" style="background:#dc3545;"><span class="stat-label">إجمالي استقطاع</span><span class="stat-value">{gp[cols['ded']].sum():,.2f}</span></div>
                        <div class="stat-card" style="background:#007bff;"><span class="stat-label">الصافي النهائي</span><span class="stat-value">{gp[cols['net']].sum():,.2f}</span></div>
                    </div>""", unsafe_allow_html=True)
                    
                    disp = gp[[cols['date'], cols['type'], cols['desc'], cols['ent'], cols['net']]].copy()
                    disp.insert(0, 'م', range(1, len(disp)+1))
                    st.markdown(f'<div class="custom-table-container">{disp.to_html(index=False, classes="custom-table")}</div>', unsafe_allow_html=True)

    # --- 2. ملف الموظف (بحث بالاسم والكود) ---
    elif menu == "👤 ملف الموظف التفصيلي":
        st.title("👤 التحليل التفصيلي للموظف")
        search_emp = st.text_input("🔍 ابحث عن الموظف (اسم أو كود) لفتح ملفه:")
        if search_emp:
            q_e = re.sub(r'[أإآ]', 'ا', search_emp).replace('ى', 'ي').replace('ة', 'ه').strip()
            e_res = df_raw[(df_raw['Search_Key'].str.contains(q_e, na=False)) | (df_raw[cols['code']] == search_emp.strip())]
            if not e_res.empty:
                emp_name = e_res.iloc[0][cols['name']]
                e_data = df_raw[df_raw[cols['name']] == emp_name].sort_values(cols['date'])
                st.subheader(f"الملف المالي لـ: {emp_name}")
                t1, t2 = st.tabs(["💰 تفاصيل الـ 109 بند", "📈 منحنى الدخل"])
                with t1:
                    e_fin = e_data[fin_cols].loc[:, (e_data[fin_cols] != 0).any(axis=0)]
                    st.dataframe(e_fin.assign(التاريخ=e_data[cols['date']]).set_index('التاريخ'), use_container_width=True)
                with t2:
                    if PLOTLY_AVAILABLE:
                        fig = px.line(e_data.groupby(cols['date'])[cols['net']].sum().reset_index(), x=cols['date'], y=cols['net'], markers=True, title="تطور الصافي")
                        st.plotly_chart(fig, use_container_width=True)
            else: st.error("الموظف غير موجود")

    # --- 3. تحليل الحسابات (إخفاء الـ Index) ---
    elif menu == "📖 تحليل الحسابات":
        st.title(f"📖 إجماليات الحسابات - {target_month}")
        acc_summary = df_f[fin_cols].sum().reset_index()
        acc_summary.columns = ['الحساب / البند المالي', 'المبلغ الإجمالي']
        acc_summary = acc_summary[acc_summary['المبلغ الإجمالي'] > 0].sort_values('المبلغ الإجمالي', ascending=False)
        st.markdown(f'<div class="custom-table-container">{acc_summary.to_html(index=False, classes="custom-table")}</div>', unsafe_allow_html=True)

    # --- 4. لوحة التحكم (بروفيشنال) ---
    elif menu == "📊 لوحة التحكم":
        st.title(f"📊 داشبورد الإدارة - {target_month}")
        m1, m2, m3 = st.columns(3)
        m1.metric("عدد الموظفين", f"{len(df_f[cols['name']].unique()):,}")
        m2.metric("إجمالي الميزانية", f"{df_f[cols['ent']].sum():,.0f}")
        m3.metric("صافي السيولة", f"{df_f[cols['net']].sum():,.0f}")
        
        if PLOTLY_AVAILABLE:
            c_a, c_b = st.columns(2)
            with c_a:
                st.plotly_chart(px.bar(df_f.groupby(cols['mang'])[cols['net']].sum().reset_index(), x=cols['mang'], y=cols['net'], title="الصافي حسب الإدارة"), use_container_width=True)
            with c_b:
                st.plotly_chart(px.pie(names=['الصافي', 'الاستقطاعات'], values=[df_f[cols['net']].sum(), df_f[cols['ded']].sum()], hole=0.4, title="تحليل الميزانية"), use_container_width=True)

    elif menu == "📥 التصدير":
        st.title("📥 مركز التحميل")
        buf = io.BytesIO(); df_f.to_excel(buf, index=False)
        st.download_button("💾 تحميل ملف Excel الشامل", buf.getvalue(), f"IDA_{target_month}.xlsx")

else: st.error("❌ ملف MAR2026.csv مفقود")
