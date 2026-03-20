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
st.set_page_config(page_title="نظام IDA للمستحقات", layout="wide", page_icon="IDA_logo_(1).ico")

# 2. تصميم CSS المتطور (مع الشبكة الذكية للموبايل)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif !important; direction: rtl; text-align: center; }
    .main { background-color: #f4f7f9; }
    
    .personal-card { background: linear-gradient(135deg, #003366 0%, #005bb7 100%); color: white; padding: 25px; border-radius: 20px; margin-bottom: 25px; border: 2px solid #ffffff; width: 100%; box-shadow: 0 10px 30px rgba(0,0,0,0.2); }
    .personal-card h1 { font-size: 30px !important; font-weight: 800; color: white !important; margin: 0; }
    
    /* ---- الشبكة الذكية للكروت عشان الموبايل ---- */
    .stats-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 15px;
        margin-bottom: 20px;
    }
    .stat-card { padding: 15px; border-radius: 15px; color: white !important; text-align: center; box-shadow: 0 4px 10px rgba(0,0,0,0.1); height: 100%; display: flex; flex-direction: column; justify-content: center; }
    .stat-value { font-size: 24px !important; font-weight: 800; display: block; color: white !important; margin-top: 5px; }
    .stat-label { color: white !important; font-size: 15px; font-weight: 600; }
    
    /* لما تفتح من موبايل، خلي الكروت 2 جنب بعض بدل 4 تحت بعض */
    @media (max-width: 768px) {
        .stats-grid {
            grid-template-columns: repeat(2, 1fr);
        }
        .personal-card h1 { font-size: 24px !important; }
    }
    /* ------------------------------------------ */

    .custom-table-container { width: 100%; overflow-x: auto; border-radius: 15px; background: white; padding: 10px; box-shadow: 0 5px 15px rgba(0,0,0,0.05); }
    .custom-table { width: 100%; border-collapse: collapse; text-align: center; }
    .custom-table th { background-color: #003366; color: white; padding: 12px; white-space: nowrap; }
    .custom-table td { padding: 10px; border: 1px solid #ddd; font-weight: 600; white-space: nowrap; }

    @media print {
        @page { size: A4 portrait; margin: 10mm; }
        section[data-testid="stSidebar"], .stDownloadButton, button, iframe, header, [data-testid="stHeader"], .stTextInput, .stSelectbox, .stHeader, h1:first-of-type, .stExpander { display: none !important; }
        .main, .block-container { background-color: white !important; padding: 0 !important; margin: 0 !important; }
        * { -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }
        .personal-card { background: transparent !important; color: #003366 !important; border: none !important; text-align: center !important; }
        .personal-card h1 { color: #003366 !important; font-size: 32px !important; text-align: center !important; margin: 0 auto !important; display: block !important; }
        .stats-grid { display: grid !important; grid-template-columns: repeat(4, 1fr) !important; gap: 5px !important; }
        .stat-card { border: 1px solid #ddd !important; padding: 5px !important; box-shadow: none !important; }
        .stat-value, .stat-label { color: black !important; font-size: 14px !important; }
    }
    </style>
    """, unsafe_allow_html=True)

# 3. محرك البيانات المطور
@st.cache_data
def load_v40_data():
    file_name = 'MAR2026.csv'
    if not os.path.exists(file_name): return None, None
    try:
        df = pd.read_csv(file_name, header=0, encoding='utf-8-sig', low_memory=False, dtype={'National_ID': str, 'Employee_Code': str})
        df.columns = [c.strip() for c in df.columns]
        
        p = {
            'name': ['name_employee', 'اسم الموظف'], 'code': ['employee_code', 'كود'], 
            'date': ['التاريخ', 'date', 'Date'], 'mang': ['mangment', 'الإدارة'],
            'type': ['نوع الصرف'], 'ent': ['أجمالى الاستحقاقات'], 'tax': ['ضريبة الدخل'],
            'stamp': ['ضريبة الدمغة'], 'ded': ['الأجمالى الاستقطاعات'], 'net': ['الصافي'],
            'nat': ['national_id', 'الرقم القومي'], 'desc': ['وصف']
        }
        cols = {k: next((c for c in df.columns if any(w.lower() in c.lower() for w in p[k])), None) for k in p}
        
        if cols['name']:
            df[cols['name']] = df[cols['name']].astype(str).str.replace(r'\s+', ' ', regex=True).str.strip()
            df['Search_Key'] = df[cols['name']].str.replace(r'[أإآ]', 'ا', regex=True).str.replace('ى', 'ي').str.replace('ة', 'ه')
            
        def clean_money(val):
            v = str(val).replace(',', '').strip()
            if v in ["", "-", "0", "nan"]: return 0.0
            try: return float(v)
            except: return 0.0
            
        for k in ['ent', 'tax', 'stamp', 'ded', 'net']:
            if cols[k]: df[cols[k]] = df[cols[k]].apply(clean_money)
            
        return df, cols
    except Exception as e:
        st.error(f"خطأ في تحميل الملف: {e}"); return None, None

df_raw, cols = load_v40_data()

if df_raw is not None:
    with st.sidebar:
        st.image("IDA_logo_(1).ico", width=150)
        st.markdown("<h3 style='color: #003366; text-align:center;'>IDA SYSTEM</h3>", unsafe_allow_html=True)
        st.markdown("---")
        
        if cols['date']:
            unique_dates = sorted([str(d) for d in df_raw[cols['date']].unique() if pd.notna(d)], reverse=True)
            available_months = ["الكل"] + unique_dates
            target_month = st.selectbox("📅 اختر شهر الصرف:", available_months)
            
            if target_month == "الكل":
                df = df_raw
            else:
                df = df_raw[df_raw[cols['date']].astype(str) == target_month]
        else:
            df = df_raw
            target_month = "غير محدد"
        
        menu = st.radio("📌 القائمة الرئيسية:", ["🔍 استعلام الموظفين", "📊 إحصائيات عامة", "🏢 تحليل الإدارات", "📥 تصدير التقارير"])

    # 1. استعلام الموظفين
    if menu == "🔍 استعلام الموظفين":
        st.title(f"🔍 استعلام - {target_month}")
        c_search1, c_search2 = st.columns([1, 2])
        with c_search1: mode = st.selectbox("بحث بـ:", ["الاسم", "الكود"])
        with c_search2: q = st.text_input("✍️ ابدأ الكتابة هنا:")
        
        if q:
            if mode == "الاسم":
                q_n = re.sub(r'[أإآ]', 'ا', q).replace('ى', 'ي').replace('ة', 'ه').replace('*', '.*').strip()
                res = df[df['Search_Key'].str.contains(q_n, na=False, regex=True, flags=re.IGNORECASE)]
            else:
                res = df[df[cols['code']].astype(str).str.contains(q.strip(), na=False)]
            
            if not res.empty:
                for name, group in res.groupby(cols['name']):
                    st.markdown(f'<div class="personal-card"><h1>{name}</h1><p>🆔 كود: {group.iloc[0][cols["code"]]} | 📄 رقم قومي: {group.iloc[0][cols["nat"]]}</p></div>', unsafe_allow_html=True)
                    
                    s_ent, s_tax, s_ded, s_net = group[cols['ent']].sum(), (group[cols['tax']].sum()+group[cols['stamp']].sum()), group[cols['ded']].sum(), group[cols['net']].sum()
                    
                    # ---- الكود الذكي للكروت (هيعمل شكل مربع في الموبايل وميفرش بالطول) ----
                    html_stats = f"""
                    <div class="stats-grid">
                        <div class="stat-card" style="background:#28a745;"><span class="stat-label">إجمالي المستحق</span><span class="stat-value">{s_ent:,.2f}</span></div>
                        <div class="stat-card" style="background:#ffc107;"><span class="stat-label" style="color:black">ضرائب ودمغة</span><span class="stat-value" style="color:black">{s_tax:,.2f}</span></div>
                        <div class="stat-card" style="background:#dc3545;"><span class="stat-label">إجمالي استقطاع</span><span class="stat-value">{s_ded:,.2f}</span></div>
                        <div class="stat-card" style="background:#007bff;"><span class="stat-label">الصافي النهائي</span><span class="stat-value">{s_net:,.2f}</span></div>
                    </div>
                    """
                    st.markdown(html_stats, unsafe_allow_html=True)
                    # -------------------------------------------------------------------------
                    
                    display_cols = [cols["type"], cols["desc"], cols["ent"], cols["net"]]
                    if target_month == "الكل" and cols['date']:
                        display_cols.insert(0, cols['date'])
                    
                    disp_df = group[display_cols].copy()
                    disp_df.insert(0, 'م', range(1, len(disp_df) + 1))
                    
                    st.markdown(f'<div class="custom-table-container">{disp_df.to_html(index=False, classes="custom-table", escape=False)}</div>', unsafe_allow_html=True)
                    if st.button(f"🖨️ طباعة {name}"):
                        components.html(f"<script>window.parent.document.title='مستحقات - {name}'; window.parent.print();</script>")
            else: st.warning(f"🔍 لا توجد نتائج.")

    # 2. إحصائيات عامة
    elif menu == "📊 إحصائيات عامة":
        st.title(f"📊 مؤشرات - {target_month}")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("👥 الموظفين", f"{df['Search_Key'].nunique():,}")
        c2.metric("💰 الميزانية", f"{df[cols['ent']].sum():,.0f}")
        c3.metric("✂️ الخصومات", f"{df[cols['ded']].sum():,.0f}")
        c4.metric("💵 الصافي", f"{df[cols['net']].sum():,.0f}")
        if PLOTLY_AVAILABLE:
            with st.expander("📈 عرض رسم الميزانية"):
                st.plotly_chart(px.pie(names=['الصافي', 'الخصومات'], values=[df[cols['net']].sum(), df[cols['ded']].sum()], hole=0.5), use_container_width=True)

    # 3. تحليل الإدارات
    elif menu == "🏢 تحليل الإدارات":
        st.title(f"🏢 تحليل الإدارات - {target_month}")
        mang_df = df.groupby(cols['mang'])[[cols['ent'], cols['net']]].sum().reset_index()
        st.dataframe(mang_df, use_container_width=True)

    # 4. تصدير التقارير
    elif menu == "📥 تصدير التقارير":
        st.title(f"📥 تصدير بيانات - {target_month}")
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df.drop(columns=['Search_Key']).to_excel(writer, index=False, sheet_name='البيانات')
        st.download_button(f"💾 تحميل ملف Excel الشامل", buffer.getvalue(), f"IDA_Report_{target_month}.xlsx")

else: st.error("❌ ملف MAR2026.csv غير موجود بجانب الكود.")
