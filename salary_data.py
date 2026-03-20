import streamlit as st
import pandas as pd
import re
import os
import io
import streamlit.components.v1 as components

try:
    import plotly.express as px
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

# 1. إعداد الصفحة
st.set_page_config(page_title="IDA Payroll System Pro", layout="wide", page_icon="IDA_logo_(1).ico")

# 2. تصميم CSS (تنسيق مخصص للداشبورد والجداول)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif !important; direction: rtl; text-align: center; }
    .main { background-color: #f0f2f6; }
    
    /* تنسيق الكروت العلوية في الداشبورد */
    .kpi-card { background: white; padding: 20px; border-radius: 15px; border-right: 5px solid #003366; box-shadow: 0 4px 15px rgba(0,0,0,0.05); text-align: right; }
    .kpi-label { color: #666; font-size: 16px; font-weight: 600; }
    .kpi-value { color: #003366; font-size: 26px; font-weight: 800; display: block; margin-top: 5px; }

    /* الكروت الملونة في الاستعلام */
    .stats-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-bottom: 20px; }
    .stat-card { padding: 20px; border-radius: 15px; color: white !important; text-align: center; }
    .stat-value { font-size: 22px !important; font-weight: 800; display: block; color: white !important; }
    
    @media (max-width: 768px) { .stats-grid { grid-template-columns: repeat(2, 1fr); } }

    .custom-table-container { width: 100%; overflow-x: auto; border-radius: 12px; background: white; padding: 10px; box-shadow: 0 5px 15px rgba(0,0,0,0.05); }
    .custom-table { width: 100%; border-collapse: collapse; }
    .custom-table th { background-color: #003366; color: white; padding: 12px; white-space: nowrap; }
    .custom-table td { padding: 10px; border: 1px solid #ddd; font-weight: 600; white-space: nowrap; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# 3. محرك البيانات
@st.cache_data
def load_v53_data():
    f = 'MAR2026.csv'
    if not os.path.exists(f): return None, None, []
    try:
        df = pd.read_csv(f, header=0, encoding='utf-8-sig', low_memory=False, dtype={'National_ID': str, 'Employee_Code': str})
        df.columns = [c.strip() for c in df.columns]
        p = {
            'name': 'Name_Employee', 'code': 'Employee_Code', 'date': 'Date',
            'mang': 'Mangment', 'ent': 'أجمالى الاستحقاقات', 'ded': 'الأجمالى الاستقطاعات',
            'net': 'الصافي', 'desc': 'وصف', 'type': 'نوع الصرف'
        }
        cols = {k: v for k, v in p.items() if v in df.columns}
        num_cols = df.select_dtypes(include=['number']).columns.tolist()
        for c in num_cols:
            df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
        
        fin_items = [c for c in num_cols if c not in [p['ent'], p['ded'], p['net']]]
        df['Search_Key'] = df[p['name']].astype(str).str.replace(r'[أإآ]', 'ا', regex=True).str.replace('ى', 'ي').str.replace('ة', 'ه').str.strip()
        return df, cols, fin_items
    except Exception as e:
        st.error(f"Error: {e}"); return None, None, []

df_raw, cols, fin_cols = load_v53_data()

if df_raw is not None:
    with st.sidebar:
        st.image("IDA_logo_(1).ico", width=120)
        st.markdown("<h3 style='text-align:center;'>IDA SYSTEM PRO</h3>", unsafe_allow_html=True)
        dates = sorted([str(d) for d in df_raw[cols['date']].unique() if pd.notna(d)], reverse=True)
        target_month = st.selectbox("📅 الفترة الضريبية:", ["الكل"] + dates)
        menu = st.radio("القائمة الرئيسية:", ["🔍 الاستعلام السريع", "👤 تحليل الموظف", "📖 تحليل الحسابات", "📊 داشبورد الإدارة", "📥 التصدير"])

    df_f = df_raw if target_month == "الكل" else df_raw[df_raw[cols['date']].astype(str) == target_month]

    # --- 1. الاستعلام السريع ---
    if menu == "🔍 الاستعلام السريع":
        q = st.text_input("✍️ ابحث بالاسم أو الكود:")
        if q:
            q_c = re.sub(r'[أإآ]', 'ا', q).replace('ى', 'ي').replace('ة', 'ه').strip()
            res = df_f[(df_f['Search_Key'].str.contains(q_c, na=False)) | (df_f[cols['code']] == q.strip())]
            if not res.empty:
                for name, gp in res.groupby(cols['name']):
                    st.markdown(f'<div class="personal-card" style="background: #003366; color:white; padding:15px; border-radius:15px; margin-bottom:10px;"><h3>{name}</h3><p>🆔 {gp.iloc[0][cols["code"]]} | 🏢 {gp.iloc[0][cols["mang"]]}</p></div>', unsafe_allow_html=True)
                    tax_val = gp[[c for c in gp.columns if any(w in c for w in ['ضريبة', 'دمغة'])]].sum().sum()
                    st.markdown(f"""<div class="stats-grid">
                        <div class="stat-card" style="background:#28a745;"><span class="stat-label">المستحق</span><span class="stat-value">{gp[cols['ent']].sum():,.2f}</span></div>
                        <div class="stat-card" style="background:#ffc107;"><span class="stat-label" style="color:black">الضرائب</span><span class="stat-value" style="color:black">{tax_val:,.2f}</span></div>
                        <div class="stat-card" style="background:#dc3545;"><span class="stat-label">الاستقطاع</span><span class="stat-value">{gp[cols['ded']].sum():,.2f}</span></div>
                        <div class="stat-card" style="background:#007bff;"><span class="stat-label">الصافي</span><span class="stat-value">{gp[cols['net']].sum():,.2f}</span></div>
                    </div>""", unsafe_allow_html=True)
                    disp = gp[[cols['date'], cols['type'], cols['desc'], cols['ent'], cols['net']]].copy()
                    disp.insert(0, 'م', range(1, len(disp)+1))
                    st.markdown(f'<div class="custom-table-container">{disp.style.format({cols["ent"]: "{:,.2f}", cols["net"]: "{:,.2f}"}).to_html(index=False, classes="custom-table")}</div>', unsafe_allow_html=True)

    # --- 2. تحليل الموظف (البحث الذكي) ---
    elif menu == "👤 تحليل الموظف":
        q_emp = st.text_input("🔍 ابحث عن موظف (بالكود أو الاسم) لمشاهدة تاريخه المالي:")
        if q_emp:
            q_e = re.sub(r'[أإآ]', 'ا', q_emp).replace('ى', 'ي').replace('ة', 'ه').strip()
            e_res = df_raw[(df_raw['Search_Key'].str.contains(q_e, na=False)) | (df_raw[cols['code']] == q_emp.strip())]
            if not e_res.empty:
                emp_name = e_res.iloc[0][cols['name']]
                e_data = df_raw[df_raw[cols['name']] == emp_name].sort_values(cols['date'])
                e_fin = e_data[fin_cols].loc[:, (e_data[fin_cols] != 0).any(axis=0)]
                st.subheader(f"تحليل بيانات: {emp_name}")
                st.dataframe(e_fin.assign(الفترة=e_data[cols['date']]).set_index('الفترة').style.format("{:,.2f}"), use_container_width=True)
                if PLOTLY_AVAILABLE:
                    st.plotly_chart(px.line(e_data.groupby(cols['date'])[cols['net']].sum().reset_index(), x=cols['date'], y=cols['net'], markers=True, title="مسار الدخل"), use_container_width=True)

    # --- 3. تحليل الحسابات (إضافة فواصل الآلاف) ---
    elif menu == "📖 تحليل الحسابات":
        st.title(f"📖 ميزانية البنود المالية - {target_month}")
        acc_summary = df_f[fin_cols].sum().reset_index()
        acc_summary.columns = ['الحساب المالي', 'المبلغ الإجمالي']
        acc_summary = acc_summary[acc_summary['المبلغ الإجمالي'] > 0].sort_values('المبلغ الإجمالي', ascending=False)
        # التنسيق بفواصل الآلاف
        st.markdown(f'<div class="custom-table-container">{acc_summary.style.format({"المبلغ الإجمالي": "{:,.2f}"}).to_html(index=False, classes="custom-table")}</div>', unsafe_allow_html=True)

    # --- 4. داشبورد الإدارة (بروفيشنال 100%) ---
    elif menu == "📊 داشبورد الإدارة":
        st.title(f"📊 لوحة تحكم القيادة - {target_month}")
        # كروت علوية (KPIs)
        k1, k2, k3, k4 = st.columns(4)
        with k1: st.markdown(f'<div class="kpi-card"><span class="kpi-label">👤 عدد الموظفين</span><span class="kpi-value">{len(df_f[cols["name"]].unique()):,}</span></div>', unsafe_allow_html=True)
        with k2: st.markdown(f'<div class="kpi-card"><span class="kpi-label">💰 إجمالي الميزانية</span><span class="kpi-value">{df_f[cols["ent"]].sum():,.0f}</span></div>', unsafe_allow_html=True)
        with k3: st.markdown(f'<div class="kpi-card"><span class="kpi-label">✂️ إجمالي الاستقطاع</span><span class="kpi-value">{df_f[cols["ded"]].sum():,.0f}</span></div>', unsafe_allow_html=True)
        with k4: st.markdown(f'<div class="kpi-card"><span class="kpi-label">💵 صافي المنصرف</span><span class="kpi-value">{df_f[cols["net"]].sum():,.0f}</span></div>', unsafe_allow_html=True)
        
        st.markdown("---")
        
        if PLOTLY_AVAILABLE:
            row1_1, row1_2 = st.columns([2, 1])
            with row1_1:
                # ترتيب الإدارات حسب الصرف
                mang_data = df_f.groupby(cols['mang'])[cols['net']].sum().reset_index().sort_values(cols['net'], ascending=False)
                fig_mang = px.bar(mang_data, x=cols['mang'], y=cols['net'], color=cols['net'], title="صافي الصرف لكل إدارة", color_continuous_scale='Blues')
                st.plotly_chart(fig_mang, use_container_width=True)
            with row1_2:
                # هيكل الميزانية
                fig_pie = px.pie(names=['الصافي', 'الاستقطاعات'], values=[df_f[cols['net']].sum(), df_f[cols['ded']].sum()], hole=0.5, color_discrete_sequence=['#003366', '#dc3545'], title="تحليل الكتلة المالية")
                st.plotly_chart(fig_pie, use_container_width=True)
            
            # أعلى 5 بنود صرف في المؤسسة
            st.markdown("### 🔝 أكبر 5 بنود صرف (بدون الرواتب الأساسية)")
            top_items = df_f[fin_cols].sum().sort_values(ascending=False).head(5).reset_index()
            top_items.columns = ['البند', 'المبلغ']
            fig_top = px.bar(top_items, x='المبلغ', y='البند', orientation='h', color='المبلغ', color_continuous_scale='Greens')
            st.plotly_chart(fig_top, use_container_width=True)

    elif menu == "📥 التصدير":
        st.title("📥 مركز تحميل التقارير")
        buf = io.BytesIO(); df_f.to_excel(buf, index=False)
        st.download_button("💾 تحميل شيت الإكسيل الحالي", buf.getvalue(), f"IDA_Report_{target_month}.xlsx")

else: st.error("❌ ملف MAR2026.csv مفقود!")
