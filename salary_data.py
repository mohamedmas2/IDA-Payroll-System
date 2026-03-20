import streamlit as st
import pandas as pd
import re
import os
import io
import streamlit.components.v1 as components

# --- 1. إعدادات الأمان (المستخدمين) ---
# ملاحظة: في الواقع يفضل استخدام قاعدة بيانات، لكن هنا هنعملهم كقاموس للتبسيط
USERS = {
    "admin@ida.gov.eg": {"pass": "admin123", "role": "admin", "name": "المدير العام"},
    "user1@ida.gov.eg": {"pass": "user123", "role": "viewer", "name": "محلل بيانات"},
    "user2@ida.gov.eg": {"pass": "pass123", "role": "searcher", "name": "موظف استعلام"}
}

def login_screen():
    st.markdown("""
        <style>
        .login-box {
            background-color: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            max-width: 400px;
            margin: auto;
            text-align: center;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.image("IDA_logo_(1).ico", width=100)
    st.title("🔐 تسجيل الدخول - نظام IDA")
    
    with st.container():
        email = st.text_input("البريد الإلكتروني")
        password = st.text_input("كلمة المرور", type="password")
        if st.button("دخول"):
            if email in USERS and USERS[email]["pass"] == password:
                st.session_state["logged_in"] = True
                st.session_state["user_info"] = USERS[email]
                st.rerun()
            else:
                st.error("❌ بيانات الدخول غير صحيحة")

# --- بداية البرنامج ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    login_screen()
else:
    # لو مسجل دخول، يعرض البرنامج الأصلي
    user = st.session_state["user_info"]
    
    try:
        import plotly.express as px
        PLOTLY_AVAILABLE = True
    except ImportError:
        PLOTLY_AVAILABLE = False

    st.set_page_config(page_title="نظام IDA للمستحقات", layout="wide", page_icon="IDA_logo_(1).ico")

    # [كود الـ CSS القديم بتاعك هنا]
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;800&display=swap');
        html, body, [class*="css"] { font-family: 'Cairo', sans-serif !important; direction: rtl; text-align: center; }
        .main { background-color: #f4f7f9; }
        [data-testid="stSidebar"] * { white-space: nowrap !important; overflow: hidden !important; text-overflow: ellipsis !important; }
        .sidebar-title { color: #003366; text-align: center; font-weight: 800; margin-top: -10px; margin-bottom: 10px; font-size: 24px; }
        .stats-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-bottom: 20px; }
        .stat-card { padding: 15px; border-radius: 15px; color: white !important; text-align: center; box-shadow: 0 4px 10px rgba(0,0,0,0.1); height: 100%; display: flex; flex-direction: column; justify-content: center; }
        .stat-value { font-size: 24px !important; font-weight: 800; display: block; color: white !important; margin-top: 5px; }
        .stat-label { color: white !important; font-size: 15px; font-weight: 600; }
        @media (max-width: 768px) { .stats-grid { grid-template-columns: repeat(2, 1fr); } }
        .personal-card { background: linear-gradient(135deg, #003366 0%, #005bb7 100%); color: white; padding: 25px; border-radius: 20px; margin-bottom: 25px; border: 2px solid #ffffff; width: 100%; box-shadow: 0 10px 30px rgba(0,0,0,0.2); }
        .personal-card h1 { font-size: 30px !important; font-weight: 800; color: white !important; margin: 0; }
        .custom-table-container { width: 100%; overflow-x: auto; border-radius: 15px; background: white; padding: 10px; box-shadow: 0 5px 15px rgba(0,0,0,0.05); }
        .custom-table { width: 100%; border-collapse: collapse; text-align: center; }
        .custom-table th { background-color: #003366; color: white; padding: 12px; white-space: nowrap; }
        .custom-table td { padding: 10px; border: 1px solid #ddd; font-weight: 600; white-space: nowrap; }
        </style>
    """, unsafe_allow_html=True)

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
                v = str(val).replace(',', '').strip(); return float(v) if v not in ["", "-", "0", "nan"] else 0.0
            for k in ['ent', 'tax', 'stamp', 'ded', 'net']:
                if cols[k]: df[cols[k]] = df[cols[k]].apply(clean_money)
            return df, cols
        except Exception as e: return None, None

    df_raw, cols = load_v40_data()

    if df_raw is not None:
        with st.sidebar:
            st.image("IDA_logo_(1).ico", width=100)
            st.markdown(f"<div class='sidebar-title'>{user['name']}</div>", unsafe_allow_html=True)
            if st.button("🚪 تسجيل خروج"):
                st.session_state["logged_in"] = False
                st.rerun()
            st.markdown("---")
            
            # فلترة التواريخ
            unique_dates = sorted([str(d) for d in df_raw[cols['date']].unique() if pd.notna(d)], reverse=True)
            target_month = st.selectbox("📅 اختر شهر الصرف:", ["الكل"] + unique_dates)
            df = df_raw if target_month == "الكل" else df_raw[df_raw[cols['date']].astype(str) == target_month]

            # --- التحكم في القائمة حسب الصلاحية ---
            options = ["🔍 استعلام الموظفين"]
            if user["role"] in ["admin", "viewer"]:
                options.append("📊 إحصائيات عامة")
            if user["role"] == "admin":
                options.extend(["🏢 تحليل الإدارات", "📥 تصدير التقارير"])
            
            menu = st.radio("📌 القائمة الرئيسية:", options)

        # 1. استعلام الموظفين (متاح للكل)
        if menu == "🔍 استعلام الموظفين":
            st.title(f"🔍 استعلام - {target_month}")
            c_search1, c_search2 = st.columns([1, 2])
            with c_search1: mode = st.selectbox("بحث بـ:", ["الاسم", "الكود"])
            with c_search2: q = st.text_input("✍️ ابدأ الكتابة هنا:")
            if q:
                if mode == "الاسم":
                    q_n = re.sub(r'[أإآ]', 'ا', q).replace('ى', 'ي').replace('ة', 'ه').strip()
                    res = df[df['Search_Key'].str.contains(q_n, na=False)]
                else:
                    res = df[df[cols['code']].astype(str).str.contains(q.strip(), na=False)]
                
                if not res.empty:
                    for name, group in res.groupby(cols['name']):
                        st.markdown(f'<div class="personal-card"><h1>{name}</h1><p>🆔 كود: {group.iloc[0][cols["code"]]} | 📄 رقم قومي: {group.iloc[0][cols["nat"]]}</p></div>', unsafe_allow_html=True)
                        s_ent, s_tax, s_ded, s_net = group[cols['ent']].sum(), (group[cols['tax']].sum()+group[cols['stamp']].sum()), group[cols['ded']].sum(), group[cols['net']].sum()
                        st.markdown(f"""<div class="stats-grid">
                            <div class="stat-card" style="background:#28a745;"><span class="stat-label">المستحق</span><span class="stat-value">{s_ent:,.2f}</span></div>
                            <div class="stat-card" style="background:#ffc107;"><span class="stat-label" style="color:black">ضرائب</span><span class="stat-value" style="color:black">{s_tax:,.2f}</span></div>
                            <div class="stat-card" style="background:#dc3545;"><span class="stat-label">استقطاع</span><span class="stat-value">{s_ded:,.2f}</span></div>
                            <div class="stat-card" style="background:#007bff;"><span class="stat-label">الصافي</span><span class="stat-value">{s_net:,.2f}</span></div>
                        </div>""", unsafe_allow_html=True)
                        disp_df = group[[cols["type"], cols["desc"], cols["ent"], cols["net"]]].copy()
                        if target_month == "الكل": disp_df.insert(0, cols['date'], group[cols['date']])
                        disp_df.insert(0, 'م', range(1, len(disp_df) + 1))
                        st.markdown(f'<div class="custom-table-container">{disp_df.to_html(index=False, classes="custom-table")}</div>', unsafe_allow_html=True)
                else: st.warning("🔍 لا توجد نتائج.")

        # 2. إحصائيات عامة
        elif menu == "📊 إحصائيات عامة":
            st.title(f"📊 مؤشرات - {target_month}")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("👥 الموظفين", f"{df['Search_Key'].nunique():,}")
            c2.metric("💰 الميزانية", f"{df[cols['ent']].sum():,.0f}")
            c3.metric("✂️ الخصومات", f"{df[cols['ded']].sum():,.0f}")
            c4.metric("💵 الصافي", f"{df[cols['net']].sum():,.0f}")

        # 3. تحليل الإدارات (Admin فقط)
        elif menu == "🏢 تحليل الإدارات":
            st.title("🏢 ميزانية الإدارات")
            st.dataframe(df.groupby(cols['mang'])[[cols['ent'], cols['net']]].sum(), use_container_width=True)

        # 4. التصدير (Admin فقط)
        elif menu == "📥 تصدير التقارير":
            st.title("📥 مركز التحميل")
            buffer = io.BytesIO()
            df.to_excel(buffer, index=False)
            st.download_button("💾 Excel الشامل", buffer.getvalue(), "IDA_Report.xlsx")

    else: st.error("❌ ملف MAR2026.csv غير موجود.")
