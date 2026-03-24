st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif !important; direction: rtl; text-align: center; }
    
    /* إخفاء أدوات Streamlit للمستخدم النهائي */
    header {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stAppDeployButton {display:none !important;}
    [data-testid="stHeader"] {display:none !important;}
    .block-container {padding-top: 2rem !important;}

    .main { background-color: #f4f7f9; }
    [data-testid="stSidebar"] * { white-space: nowrap !important; overflow: hidden !important; text-overflow: ellipsis !important; }
    .sidebar-title { color: #003366; text-align: center; font-weight: 800; margin-top: -10px; margin-bottom: 10px; font-size: 24px; }
    .stats-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-bottom: 20px; }
    .stat-card { padding: 15px; border-radius: 15px; color: white !important; text-align: center; box-shadow: 0 4px 10px rgba(0,0,0,0.1); height: 100%; display: flex; flex-direction: column; justify-content: center; }
    .stat-value { font-size: 24px !important; font-weight: 800; display: block; color: white !important; margin-top: 5px; }
    .stat-label { color: white !important; font-size: 15px; font-weight: 600; }
    
    @media (max-width: 768px) { 
        .stats-grid { grid-template-columns: repeat(2, 1fr); } 
        .sidebar-title { font-size: 20px !important; } 
        .personal-card h1 { font-size: 24px !important; } 
    }
    
    .personal-card { background: linear-gradient(135deg, #003366 0%, #005bb7 100%); color: white; padding: 25px; border-radius: 20px; margin-bottom: 25px; border: 2px solid #ffffff; width: 100%; box-shadow: 0 10px 30px rgba(0,0,0,0.2); }
    .personal-card h1 { font-size: 30px !important; font-weight: 800; color: white !important; margin: 0; }
    .custom-table-container { width: 100%; overflow-x: auto; border-radius: 15px; background: white; padding: 10px; box-shadow: 0 5px 15px rgba(0,0,0,0.05); }
    .custom-table { width: 100%; border-collapse: collapse; text-align: center; }
    .custom-table th { background-color: #003366; color: white; padding: 12px; white-space: nowrap; }
    .custom-table td { padding: 10px; border: 1px solid #ddd; font-weight: 600; white-space: nowrap; }
    
    @media print {
        @page { size: A4 portrait; margin: 10mm; }
        section[data-testid="stSidebar"], .stDownloadButton, button, iframe, header, [data-testid="stHeader"], .stTextInput, .stSelectbox, .stHeader, h1:first-of-type, .stExpander { display: none !important; }
        .main, .block-container { background-color: white !important; padding: 0 !important; margin: 0 !important; }
        .personal-card { background: transparent !important; color: #003366 !important; border: none !important; text-align: center !important; }
        .personal-card h1 { color: #003366 !important; font-size: 32px !important; text-align: center !important; }
        .stats-grid { display: grid !important; grid-template-columns: repeat(4, 1fr) !important; gap: 5px !important; }
        .stat-card { border: 1px solid #ddd !important; padding: 5px !important; box-shadow: none !important; }
        .stat-value, .stat-label { color: black !important; font-size: 14px !important; }
    }
    </style>
    """, unsafe_allow_html=True)
