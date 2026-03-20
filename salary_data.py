import streamlit as st
import pandas as pd
import re
import os
import io
import streamlit.components.v1 as components

# --- 1. إدارة المستخدمين ---
USER_DB_FILE = 'users_db.csv'
def load_users():
    if not os.path.exists(USER_DB_FILE):
        df = pd.DataFrame([
            {"email": "admin@ida.gov.eg", "pass": "admin123", "role": "admin", "name": "المدير العام"},
            {"email": "user1@ida.gov.eg", "pass": "user123", "role": "viewer", "name": "محلل بيانات"},
            {"email": "user2@ida.gov.eg", "pass": "pass123", "role": "searcher", "name": "موظف استعلام"}
        ])
        df.to_csv(USER_DB_FILE, index=False, encoding='utf-8-sig')
        return df
    return pd.read_csv(USER_DB_FILE, encoding='utf-8-sig')

def update_password(email, new_pass):
    df = load_users()
    if email in df['email'].values:
        df.loc[df['email'] == email, 'pass'] = str(new_pass)
        df.to_csv(USER_DB_FILE, index=False, encoding='utf-8-sig')
        return True
    return False

# --- 2. إعدادات الصفحة ---
st.set_page_config(page_title="نظام IDA للمستحقات", layout="wide", page_icon="IDA_logo_(1).ico")

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

# --- 3. CSS "الطباعة الملونة" + "الموبايل المفرود" ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;800&display=swap');
    
    /* الأساسيات */
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif !important; direction: rtl !important; text-align: right !important; }
    .main .block-container { max-width: 100% !important; padding: 1rem !important; }

    /* شبكة الكروت */
    .stats-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin: 20px 0; width: 100%; }
    .stat-card { padding: 15px; border-radius: 12px; text-align: center; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
    .stat-value { font-size: 24px !important; font-weight: 800; display: block; color: white !important; }
    .stat-label { font-size: 15px; font-weight: 600; color: white !important; }

    /* الكارت الشخصي */
    .personal-card { 
        background: linear-gradient(135deg, #003366 0%, #005bb7 100%) !important; 
        color: white !important; padding: 25px; border-radius: 20px; margin-bottom: 20px; 
        border: 2px solid #fff; -webkit-print-color-adjust: exact; 
    }
    .personal-card h1 { color: white !important; font-size: 28px !important; margin: 0; }
    .personal-card p { color: #eee !important; font-size: 16px !important; }

    /* الجدول */
    .custom-table-container { width: 100%; overflow-x: auto; border-radius: 12px; background: white; box-shadow: 0 5px 15px rgba(0,0,0,0.05); }
    .custom-table { width: 100%; border-collapse: collapse; min-width: 600px; }
    .custom-table th { background-color: #003366 !important; color: white !important; padding: 12px; -webkit-print-color-adjust: exact; }
    .custom-table td { padding: 10px; border: 1px solid #ddd; text-align: center; font-weight: 600; }

    /* ضبط الموبايل 📱 */
    @media (max-width: 768px) {
        .stats-grid { grid-template-columns: repeat(2, 1fr) !important; gap: 10px !important; }
        .stat-value { font-size: 18px !important; }
        .personal-card h1 { font-size: 22px !important; }
    }

    /* 🔥 نظام الطباعة الملونة بالكامل 🖨️ */
    @media print {
        /* إخفاء عناصر الموقع */
        section[data-testid="stSidebar"], header, footer, .stButton, button, [data-testid="stHeader"], .stTextInput {
            display: none !important;
        }
        
        /* فرد الصفحة */
        .main .block-container { max-width: 100% !important; padding: 0 !important; margin: 0 !important; }

        /* إجبار الألوان على الظهور */
        * { -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }

        /* تنسيق الكروت في الطباعة */
        .stats-grid { grid-template-columns: repeat(4, 1fr) !important; display: grid !important; }
        .stat-card { border: none !important; box-shadow: none !important; }
        .stat-value { color: white !important; font-size: 22px !important; }
        .stat-label { color: white !important; }
        
        /* التأكد من خلفية الجدول */
        .custom-table th { background-color: #003366 !important; color: white !important; }
    }
    </style>
""", unsafe_allow_html=True)

# --- 4. تسجيل الدخول ---
if not st.session_state["logged_in"]:
    st.image("IDA_logo_(1).ico", width=120)
    st.title("🔐 دخول النظام")
    e_in = st.text_input("البريد الإلكتروني")
    p_in = st.text_input("كلمة المرور", type="password")
    if st.button("دخول", use_container_width=True):
        udf = load_users()
        match = udf[(udf['email'] == e_in) & (udf['pass'].astype(str) == p_in)]
        if not match.empty:
            st.session_state["logged_in"] = True
            st.session_state["u_info"] = match.iloc[0].to_dict()
            st.rerun()
        else: st.error("خطأ في البيانات")
else:
    u = st.session_state["u_info"]
    with st.sidebar:
        st.image("IDA_logo_(1).ico", width=100)
        st.markdown(f"**مرحباً: {u['name']}**")
        with st.expander("⚙️ الحساب"):
            new_p = st.text_input("باسورد جديد", type="password")
            if st.button("حفظ"):
                update_password(u['email'], new_p)
                st.success("تم")
        if st.button("🚪 خروج", use_container_width=True):
            st.session_state["logged_in"] = False
            st.rerun()
        st.markdown("---")

        @st.cache_data
        def get_data():
            f = 'MAR2026.csv'
            if os.path.exists(f):
                df = pd.read_csv(f, low_memory=False, dtype={'National_ID': str, 'Employee_Code': str})
                df.columns = [c.strip() for c in df.columns]
                p = {'name':['name_employee','اسم الموظف'],'code':['employee_code','كود'],'date':['التاريخ','date','Date'],'net':['الصافي'],'ent':['أجمالى الاستحقاقات'],'ded':['الأجمالى الاستقطاعات'],'nat':['national_id','الرقم القومي'],'tax':['ضريبة الدخل'],'stamp':['ضريبة الدمغة'],'type':['نوع الصرف'],'desc':['وصف'],'mang':['mangment','الإدارة']}
                cols = {k: next((c for c in df.columns if any(w.lower() in c.lower() for w in p[k])), None) for k in p}
                for k in ['ent','net','ded','tax','stamp']:
                    if cols[k]: df[cols[k]] = pd.to_numeric(df[cols[k]].astype(str).str.replace(',',''), errors='coerce').fillna(0)
                df['Search_Key'] = df[cols['name']].astype(str).str.replace(r'[أإآ]','ا',regex=True).str.replace('ى','ي').str.replace('ة','ه').str.strip()
                return df, cols
            return None, None

        df_raw, cols = get_data()
        if df_raw is not None:
            unique_dates = sorted([str(d) for d in df_raw[cols['date']].unique() if pd.notna(d)], reverse=True)
            t_month = st.selectbox("📅 الشهر:", ["الكل"] + unique_dates)
            menu = st.radio("📌 التنقل:", ["🔍 استعلام", "📊 إحصائيات", "🏢 الإدارات", "📥 تصدير"])

    # --- 5. منطقة العرض المفرودة ---
    if df_raw is not None:
        df_f = df_raw if t_month == "الكل" else df_raw[df_raw[cols['date']].astype(str) == t_month]
        
        if menu == "🔍 استعلام":
            q = st.text_input("ابحث بالاسم أو الكود:", key="search_main")
            if q:
                q_c = re.sub(r'[أإآ]','ا', q).replace('ى','ي').replace('ة','ه').strip()
                res = df_f[(df_f['Search_Key'].str.contains(q_c, na=False)) | (df_f[cols['code']] == q.strip())]
                if not res.empty:
                    for n, gp in res.groupby(cols['name']):
                        st.markdown(f'<div class="personal-card"><h1>{n}</h1><p>🆔 {gp.iloc[0][cols["code"]]} | 📄 {gp.iloc[0][cols["nat"]]}</p></div>', unsafe_allow_html=True)
                        
                        s_ent, s_tax, s_ded, s_net = gp[cols['ent']].sum(), (gp[cols['tax']].sum()+gp[cols['stamp']].sum()), gp[cols['ded']].sum(), gp[cols['net']].sum()
                        # الكروت الملونة
                        st.markdown(f"""<div class="stats-grid">
                            <div class="stat-card" style="background:#28a745;"><span class="stat-label">المستحق</span><span class="stat-value">{s_ent:,.2f}</span></div>
                            <div class="stat-card" style="background:#ffc107;"><span class="stat-label" style="color:black">ضرائب</span><span class="stat-value" style="color:black">{s_tax:,.2f}</span></div>
                            <div class="stat-card" style="background:#dc3545;"><span class="stat-label">استقطاع</span><span class="stat-value">{s_ded:,.2f}</span></div>
                            <div class="stat-card" style="background:#007bff;"><span class="stat-label">الصافي</span><span class="stat-value">{s_net:,.2f}</span></div>
                        </div>""", unsafe_allow_html=True)
                        
                        disp = gp[[cols['date'], cols['type'], cols['desc'], cols['ent'], cols['net']]].copy()
                        disp.insert(0, 'م', range(1, len(disp)+1))
                        st.markdown(f'<div class="custom-table-container">{disp.to_html(index=False, classes="custom-table")}</div>', unsafe_allow_html=True)
                        if st.button(f"🖨️ طباعة {n}"): components.html("<script>window.parent.print();</script>")
                else: st.warning("لا توجد نتائج.")
