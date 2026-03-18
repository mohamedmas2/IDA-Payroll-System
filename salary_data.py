import streamlit as st
import pandas as pd
import re
import os
import io
import streamlit.components.v1 as components

# 1. إعداد الصفحة (هذا السطر يجب أن يكون أول أمر في الكود)
st.set_page_config(page_title="نظام IDA للمستحقات", layout="wide", page_icon="💰")

# 2. تصميم CSS احترافي (يحل مشكلة الموبايل والطباعة)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif !important; direction: rtl; text-align: center; }
    .main { background-color: #f4f7f9; }
    
    /* تنسيق الكروت لتناسب الموبايل */
    .personal-card { background: linear-gradient(135deg, #003366 0%, #005bb7 100%); color: white; padding: 15px; border-radius: 15px; margin-bottom: 20px; border: 2px solid #ffffff; width: 100%; }
    .personal-card h1 { font-size: 28px !important; font-weight: 800; color: white !important; margin: 0; }
    
    .stat-card { padding: 15px; border-radius: 12px; color: white !important; text-align: center; margin-bottom: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
    .stat-value { font-size: 22px !important; font-weight: 800; display: block; color: white !important; }
    .stat-label { color: white !important; font-size: 14px; font-weight: 600; }

    .custom-table-container { width: 100%; overflow-x: auto; border-radius: 12px; background: white; padding: 5px; box-shadow: 0 5px 15px rgba(0,0,0,0.05); }
    .custom-table { width: 100%; border-collapse: collapse; text-align: center; font-size: 14px; }
    .custom-table th { background-color: #003366; color: white; padding: 10px; }
    .custom-table td { padding: 8px; border: 1px solid #ddd; font-weight: 600; }

    /* إخفاء العناصر عند الطباعة وتنسيق الورقة */
    @media print {
        @page { size: A4 portrait; margin: 10mm; }
        section[data-testid="stSidebar"], .stDownloadButton, button, iframe, header, [data-testid="stHeader"], .stTextInput, .stSelectbox, .stHeader, h1:first-of-type, .stExpander { display: none !important; }
        .main, .block-container { background-color: white !important; padding: 0 !important; margin: 0 !important; }
        * { -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }
        .personal-card { background: transparent !important; color: #003366 !important; border: none !important; text-align: center !important; }
        .personal-card h1 { color: #003366 !important; font-size: 30px !important; text-align: center !important; margin: 0 auto !important; display: block !important; }
        .stat-card { border: 1px solid #ddd !important; margin-bottom: 5px !important; padding: 8px !important; background-color: #eee !important; }
        .stat-value, .stat-label { color: black !important; }
    }
    </style>
    """, unsafe_allow_html=True)

# 3. محرك قراءة البيانات
@st.cache_data
def load_data_final():
    file_name = 'MAR2026.csv'
    if not os.path.exists(file_name): return None, None
    try:
        df = pd.read_csv(file_name, header=0, encoding='utf-8-sig', low_memory=False, dtype={'National_ID': str, 'Employee_Code': str, 'NON': str})
        df.columns = [c.strip() for c in df.columns]
        
        # ربط الأعمدة (Mapping)
        p = {
            'name': ['name_employee', 'اسم الموظف'], 'code': ['employee_code', 'كود'], 
            'date': ['التاريخ', 'date', 'Date'], 'mang': ['mangment', 'الإدارة'],
            'type': ['نوع الصرف'], 'ent': ['أجمالى الاستحقاقات'], 'tax': ['ضريبة الدخل'],
            'stamp': ['ضريبة الدمغة'], 'ded': ['الأجمالى الاستقطاعات'], 'net': ['الصافي'],
            'nat': ['national_id', 'الرقم القومي'], 'desc': ['وصف'], 'non': ['NON']
        }
        cols = {k: next((c for c in df.columns if any(w.lower() in c.lower() for w in p[k])), None) for k in p}
        
        # تنظيف البيانات
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
        st.error(f"خطأ: {e}"); return None, None

df_raw, cols = load_data_final()

if df_raw is not None:
    # القائمة الجانبية (تصحيح الاسم ليظهر بشكل صحيح على الموبايل)
    with st.sidebar:
        st.markdown("<h2 style='color: #003366; text-align:center; font-size: 22px; font-weight: 800; border-bottom: 2px solid #003366; padding-bottom: 10px;'>IDA SYSTEM</h2>", unsafe_allow_html=True)
        
        if cols['date']:
            available_months = sorted(df_raw[cols['date']].unique(), reverse=True)
            target_month = st.selectbox("📅 اختر شهر الصرف:", available_months)
            df = df_raw[df_raw[cols['date']] == target_month]
        else:
            df = df_raw
            target_month = "غير محدد"
        
        menu = st.radio("📌 القائمة الرئيسية:", ["🔍 استعلام الموظفين", "📊 إحصائيات عامة", "🏢 تحليل الإدارات", "📥 تصدير التقارير"])

    # 1. شاشة الاستعلام
    if menu == "🔍 استعلام الموظفين":
        st.title(f"🔍 مستحقات {target_month}")
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
                    st.markdown(f'<div class="personal-card"><h1>{name}</h1><p style="margin:0;">🆔 كود: {group.iloc[0][cols["code"]]} | 🏢 {group.iloc[0][cols["mang"]]}</p></div>', unsafe_allow_html=True)
                    m1, m2, m3, m4 = st.columns(4)
                    s_ent, s_tax, s_ded, s_net = group[cols['ent']].sum(), (group[cols['tax']].sum()+group[cols['stamp']].sum()), group[cols['ded']].sum(), group[cols['net']].sum()
                    
                    m1.markdown(f'<div class="stat-card" style="background:#28a745;"><span class="stat-label">إجمالي المستحق</span><span class="stat-value">{s_ent:,.2f}</span></div>', unsafe_allow_html=True)
                    m2.markdown(f'<div class="stat-card" style="background:#ffc107;"><span class="stat-label" style="color:black">ضرائب ودمغة</span><span class="stat-value" style="color:black">{s_tax:,.2f}</span></div>', unsafe_allow_html=True)
                    m3.markdown(f'<div class="stat-card" style="background:#dc3545;"><span class="stat-label">إجمالي استقطاع</span><span class="stat-value">{s_ded:,.2f}</span></div>', unsafe_allow_html=True)
                    m4.markdown(f'<div class="stat-card" style="background:#007bff;"><span class="stat-label">الصافي النهائي</span><span class="stat-value">{s_net:,.2f}</span></div>', unsafe_allow_html=True)
                    
                    st.markdown(f'<div class="custom-table-container">{group[[cols["type"], cols["desc"], cols["ent"], cols["net"]]].to_html(index=False, classes="custom-table", escape=False)}</div>', unsafe_allow_html=True)
                    if st.button(f"🖨️ طباعة مفردات {name}"):
                        components.html(f"<script>window.parent.document.title='مستحقات - {name}'; window.parent.print();</script>")
            else: st.warning("🔍 لا توجد نتائج.")

    # 2. الإحصائيات العامة
    elif menu == "📊 إحصائيات عامة":
        st.title(f"📊 مؤشرات شهر {target_month}")
        c1, c2, c3 = st.columns(3)
        c1.metric("👥 الموظفين", f"{df['Search_Key'].nunique():,}")
        c2.metric("💰 الميزانية", f"{df[cols['ent']].sum():,.0f} ج.م")
        c3.metric("💵 الصافي الكلي", f"{df[cols['net']].sum():,.0f} ج.م")
        
        st.markdown("---")
        try:
            with st.expander("📈 انقر لعرض توزيع الميزانية"):
                fig = px.pie(names=['الصافي', 'الاستقطاعات'], values=[df[cols['net']].sum(), df[cols['ded']].sum()], hole=0.5, color_discrete_sequence=['#007bff', '#dc3545'])
                st.plotly_chart(fig, use_container_width=True)
        except: st.info("الرسوم البيانية غير متاحة حالياً.")

    # 3. تصدير التقارير (إصلاح خطأ الإكسيل)
    elif menu == "📥 تصدير التقارير":
        st.title(f"📥 تصدير بيانات {target_month}")
        buffer = io.BytesIO()
        try:
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                # البيانات التفصيلية
                df.drop(columns=['Search_Key']).to_excel(writer, index=False, sheet_name='بيانات الشهر')
                # تحليل الإدارات
                df.groupby(cols['mang']).agg(موظفين=('Search_Key','nunique'), صافي=(cols['net'],'sum')).to_excel(writer, sheet_name='تحليل الإدارات')
            
            st.success(f"تم تجهيز ملف إكسيل لشهر {target_month}")
            st.download_button(label="💾 تحميل ملف Excel الشامل", data=buffer.getvalue(), file_name=f"IDA_Report_{target_month}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        except Exception as e:
            st.error(f"خطأ في إنشاء ملف الإكسيل: {e}")

else:
    st.error("❌ ملف MAR2026.csv غير موجود على GitHub.")
