import streamlit as st
import pandas as pd
import re
import os
import io
import streamlit.components.v1 as components

# محاولة استيراد Plotly للرسوم التفاعلية
try:
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

# 1. إعداد الصفحة واللوجو (أول أمر)
st.set_page_config(page_title="نظام IDA للمستحقات", layout="wide", page_icon="💰")

# 2. تصميم CSS المتطور (تنسيق الشاشة والطباعة والعودة للشكل القديم)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif !important; direction: rtl; text-align: center; }
    .main { background-color: #f4f7f9; }
    
    /* تنسيق العنوان الرئيسي في الصفحة (للموبايل والكمبيوتر) */
    .app-main-title {
        color: #003366;
        font-size: 30px;
        font-weight: 800;
        margin-bottom: 25px;
        text-align: center;
        white-space: nowrap;
        border-bottom: 3px solid #003366;
        display: inline-block;
        padding-bottom: 10px;
    }

    /* كروت البيانات الكبيرة (الشكل القديم الفخم) */
    .personal-card { background: linear-gradient(135deg, #003366 0%, #005bb7 100%); color: white; padding: 25px; border-radius: 20px; margin-bottom: 25px; border: 2px solid #ffffff; width: 100%; box-shadow: 0 10px 30px rgba(0,0,0,0.2); }
    .personal-card h1 { font-size: 35px !important; font-weight: 800; color: white !important; margin: 0; }
    
    /* كروت الإحصائيات الملونة (الأربعة القديمة) */
    .stat-card { padding: 20px; border-radius: 15px; color: white !important; text-align: center; margin-bottom: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
    .stat-value { font-size: 28px !important; font-weight: 800; display: block; color: white !important; }
    .stat-label { color: white !important; font-size: 16px; font-weight: 600; }

    /* جداول البيانات (بدون أرقام الصفوف) */
    .custom-table-container { width: 100%; overflow-x: auto; border-radius: 15px; background: white; padding: 10px; box-shadow: 0 5px 15px rgba(0,0,0,0.05); }
    .custom-table { width: 100%; border-collapse: collapse; text-align: center; }
    .custom-table th { background-color: #003366; color: white; padding: 12px; }
    .custom-table td { padding: 10px; border: 1px solid #ddd; font-weight: 600; }

    /* تنسيق الـ Expander (للفتح والطي) */
    .st-emotion-cache-16i36v { border: 1px solid #003366 !important; border-radius: 12px !important; }

    /* إعدادات الطباعة الملكية */
    @media print {
        @page { size: A4 portrait; margin: 10mm; }
        section[data-testid="stSidebar"], .stDownloadButton, button, iframe, header, [data-testid="stHeader"], .stTextInput, .stSelectbox, .stHeader, h1:first-of-type, .stExpander { display: none !important; }
        .main, .block-container { background-color: white !important; padding: 0 !important; margin: 0 !important; }
        * { -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }
        .personal-card { background: transparent !important; color: #003366 !important; border: none !important; text-align: center !important; }
        .personal-card h1 { color: #003366 !important; font-size: 32px !important; text-align: center !important; margin: 0 auto !important; display: block !important; }
        .stat-card { border: 1px solid #ddd !important; margin-bottom: 5px !important; padding: 10px !important; background-color: #eee !important; }
        .stat-value, .stat-label { color: black !important; }
    }
    </style>
    """, unsafe_allow_html=True)

# 3. محرك البيانات المطور
@st.cache_data
def load_v49_data():
    file_path = 'MAR2026.csv' # تأكد من اسم الملف
    if not os.path.exists(file_path): return None, None
    try:
        # قراءة الرقم القومي كعنوان (Text) لعدم تحويله لأرقام
        df = pd.read_csv(file_path, header=0, encoding='utf-8-sig', low_memory=False, dtype={'National_ID': str, 'Employee_Code': str})
        df.columns = [c.strip() for c in df.columns]
        
        # خريطة الأعمدة
        p = {
            'name': ['name_employee', 'اسم الموظف'], 'code': ['employee_code', 'كود الموظف'], 
            'date': ['التاريخ', 'date', 'Date'], 'mang': ['mangment', 'الإدارة'],
            'type': ['نوع الصرف'], 'ent': ['أجمالى الاستحقاقات'], 'tax': ['ضريبة الدخل'],
            'stamp': ['ضريبة الدمغة'], 'ded': ['الأجمالى الاستقطاعات'], 'net': ['الصافي'],
            'nat': ['national_id', 'الرقم القومي'], 'desc': ['وصف البند']
        }
        cols = {k: next((c for c in df.columns if any(w.lower() in c.lower() for w in p[k])), None) for k in p}
        
        # توحيد الأسماء للبحث
        if cols['name']:
            df[cols['name']] = df[cols['name']].astype(str).str.replace(r'\s+', ' ', regex=True).str.strip()
            df['Search_Key'] = df[cols['name']].str.replace(r'[أإآ]', 'ا', regex=True).str.replace('ى', 'ي').str.replace('ة', 'ه')
            
        # تنظيف وتحويل المبالغ المالية
        def clean_money(val):
            v = str(val).replace(',', '').strip()
            if v in ["", "-", "0", "nan"]: return 0.0
            try: return float(v)
            except: return 0.0
            
        for k in ['ent', 'tax', 'stamp', 'ded', 'net']:
            if cols[k]: df[cols[k]] = df[cols[k]].apply(clean_money)
            
        return df, cols
    except Exception as e:
        st.error(f"خطأ في قراءة ملف MAR2026.csv: {e}")
        return None, None

df_raw, cols = load_v49_data()

if df_raw is not None:
    # --- رأس الصفحة (Main Page) لحل مشكلة الموبايل والتصدير ---
    st.markdown("<div class='app-main-title'>💰 IDA SYSTEM</div>", unsafe_allow_html=True)
    
    # فلتر التاريخ والمنيو في الصفحة الرئيسية
    c_head1, c_head2 = st.columns(2)
    with c_head1:
        if cols['date']:
            available_months = sorted(df_raw[cols['date']].unique(), reverse=True)
            target_month = st.selectbox("📅 اختر شهر الصرف:", available_months)
            df = df_raw[df_raw[cols['date']] == target_month]
        else:
            df = df_raw
            target_month = ""
    with c_head2:
        menu = st.selectbox("📌 القائمة الرئيسية:", ["🔍 1. استعلام الموظفين", "📊 2. إحصائيات وتحليلات مالية", "📥 3. تصدير تقارير الإدارة"])

    st.markdown("---")

    # ================= 🔍 1. استعلام الموظفين (الشكل القديم المحمي) =================
    if menu == "🔍 1. استعلام الموظفين":
        st.title(f"🔍 مستحقات شهر {target_month}")
        c_search1, c_search2 = st.columns([1, 2])
        with c_search1: mode = st.selectbox("بحث بـ:", ["الاسم", "الكود"])
        with c_search2: q = st.text_input("✍️ ابدأ الكتابة هنا:")
        
        if q:
            if mode == "الاسم":
                q_n = re.sub(r'[أإآ]', 'ا', q).replace('ى', 'ي').replace('ة', 'ه').replace('*', '.*').strip()
                res = df[df['Search_Key'].str.contains(q_n, na=False, regex=True, flags=re.IGNORECASE)]
            else:
                # التأكد من البحث عن الكود كنص
                res = df[df[cols['code']].astype(str).str.contains(q.strip(), na=False)]
            
            if not res.empty:
                for name, group in res.groupby(cols['name']):
                    # كارت الموظف القديم
                    st.markdown(f'<div class="personal-card"><h1>{name}</h1><p>🆔 كود: {group.iloc[0][cols["code"]]} | 🏢 {group.iloc[0][cols["mang"]]}</p></div>', unsafe_allow_html=True)
                    
                    # الكروت الملونة الأربعة القديمة
                    m1, m2, m3, m4 = st.columns(4)
                    s_ent, s_tax, s_ded, s_net = group[cols['ent']].sum(), (group[cols['tax']].sum()+group[cols['stamp']].sum()), group[cols['ded']].sum(), group[cols['net']].sum()
                    m1.markdown(f'<div class="stat-card" style="background:#28a745;"><span class="stat-label">إجمالي المستحق</span><span class="stat-value">{s_ent:,.2f}</span></div>', unsafe_allow_html=True)
                    m2.markdown(f'<div class="stat-card" style="background:#ffc107;"><span class="stat-label" style="color:black">ضرائب ودمغة</span><span class="stat-value" style="color:black">{s_tax:,.2f}</span></div>', unsafe_allow_html=True)
                    m3.markdown(f'<div class="stat-card" style="background:#dc3545;"><span class="stat-label">إجمالي استقطاع</span><span class="stat-value">{s_ded:,.2f}</span></div>', unsafe_allow_html=True)
                    m4.markdown(f'<div class="stat-card" style="background:#007bff;"><span class="stat-label">الصافي النهائي</span><span class="stat-value">{s_net:,.2f}</span></div>', unsafe_allow_html=True)
                    
                    # الجدول المنسق القديم (بدون أرقام الصفوف)
                    d_df = group[[cols['type'], cols['ent'], cols['net']]].copy()
                    # إضافة عمود مسلسل تلقائي
                    d_df.insert(0, 'م', range(1, len(d_df)+1))
                    
                    # تنسيق الجدول (إخفاء الـ Index)
                    st.markdown(f'<div class="custom-table-container">{d_df.to_html(index=False, classes="custom-table", escape=False)}</div>', unsafe_allow_html=True)
                    
                    # زر الطباعة القديم
                    if st.button(f"🖨️ طباعة مفردات {name}"):
                        components.html(f"<script>window.parent.document.title='مستحقات - {name}'; window.parent.print();</script>")
            else: st.warning(f"🔍 لم يتم العثور على نتائج للبحث في شهر {target_month}")

    # ================= 📊 2. إحصائيات وتحليلات مالية (تطوير الإدارة) =================
    elif menu == "📊 2. إحصائيات وتحليلات مالية":
        st.title(f"📊 التحليل المالي لشهر {target_month}")
        
        # كروت سريعة
        c1, c2, c3 = st.columns(3)
        c1.metric("👥 إجمالي الموظفين", f"{df['Search_Key'].nunique():,}")
        c2.metric("💰 الميزانية (الاستحقاق)", f"{df[cols['ent']].sum():,.0f} ج.م")
        c3.metric("💵 صافي المنصرف", f"{df[cols['net']].sum():,.0f} ج.م")
        
        st.markdown("---")

        if PLOTLY_AVAILABLE:
            # رسوم تفاعلية (للفتح والطي)
            with st.expander("📈 رسم بياني: توزيع الصرف الكلي (الصافي vs الخصومات)"):
                fig1 = px.pie(names=['الصافي', 'الخصومات'], values=[df[cols['net']].sum(), df[cols['ded']].sum()], hole=0.5, color_discrete_sequence=['#007bff', '#dc3545'])
                st.plotly_chart(fig1, use_container_width=True)

            with st.expander("🏢 رسم بياني: إجمالي الصافي لكل إدارة (تفاعلي)"):
                # تحليل الإدارات
                dept_analysis = df.groupby(cols['mang']).agg(عدد_الموظفين=('Search_Key','nunique'), الصافي=(cols['net'],'sum')).reset_index()
                fig2 = px.bar(dept_analysis, x=cols['mang'], y='الصافي', color='عدد_الموظفين', title="صافي المنصرف لكل إدارة")
                st.plotly_chart(fig2, use_container_width=True)
        
        # جدول تحليل الإدارات والبنود
        st.subheader("📋 تحليل صرف الإدارات حسب بنود الصرف (تفاعلي)")
        dept_item_analysis = df.groupby([cols['mang'], cols['type']]).agg(عدد_الموظفين=('Search_Key','nunique'), إجمالي_المستحق=(cols['ent'],'sum')).reset_index()
        st.dataframe(dept_item_analysis, use_container_width=True, hide_index=True)

    # ================= 📥 3. تصدير تقارير الإدارة (شيت شامل 3 صفحات) =================
    elif menu == "📥 3. تصدير تقارير الإدارة":
        st.title(f"📥 تصدير تقارير الإدارة لشهر {target_month}")
        
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            # الصفحة 1: البيانات الخام (كل الموظفين)
            df.drop(columns=['Search_Key']).to_excel(writer, index=False, sheet_name='البيانات التفصيلية')
            
            # الصفحة 2: تحليل الإدارات والبنود (Pivot Table جاهز للإدارة)
            dept_analysis = df.groupby([cols['mang'], cols['type']]).agg(عدد_الموظفين=('Search_Key','nunique'), إجمالي_المستحق=(cols['ent'],'sum'), الصافي=(cols['net'],'sum'))
            dept_analysis.to_excel(writer, sheet_name='تحليل الإدارات')
            
            # الصفحة 3: ملخص بنود الصرف (عدد المستفيدين من كل بند)
            item_sum = df.groupby(cols['type']).agg(عدد_المستفيدين=(cols['name'],'nunique'), إجمالي_المبلغ=(cols['ent'],'sum'))
            item_sum.to_excel(writer, sheet_name='ملخص البنود العام')
            
        st.success("✅ تم تجهيز التقرير التحليلي الشامل.")
        st.download_button("💾 تحميل ملف Excel الشامل لشهر المختار", buffer.getvalue(), f"IDA_Analysis_{target_month}.xlsx")

else:
    # رسالة خطأ واضحة
    st.error("❌ ملف البيانات الأساسي MAR2026.csv غير موجود في المسار الصحيح.")
