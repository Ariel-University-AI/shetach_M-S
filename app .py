import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import datetime
import joblib
from main import calculate_target_dates

# ─── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title='מערכת ניהול פרויקטי מדידה',
    page_icon='📐',
    layout='wide',
    initial_sidebar_state='expanded'
)

# ─── Global Plotly font wrapper ─────────────────────────────────────────────────
_original_plotly_chart = st.plotly_chart
def show_large_plotly_chart(fig, *args, **kwargs):
    if hasattr(fig, 'update_layout'):
        fig.update_layout(
            font=dict(size=15, family="Heebo, Arial"),
            title=dict(font=dict(size=19)),
            hoverlabel=dict(font=dict(size=14)),
            xaxis=dict(tickfont=dict(size=13), title=dict(font=dict(size=15))),
            yaxis=dict(tickfont=dict(size=13), title=dict(font=dict(size=15))),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
        )
    return _original_plotly_chart(fig, *args, **kwargs)
st.plotly_chart = show_large_plotly_chart

# ─── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Heebo:wght@300;400;500;600;700;800&display=swap');

/* ── Base ── */
*, *::before, *::after { box-sizing: border-box; }

html, body, [class*="css"] {
    font-family: 'Heebo', sans-serif;
    direction: rtl;
}

/* ── Background ── */
.stApp {
    background: linear-gradient(135deg, #0f1923 0%, #1a2a3a 50%, #0f1923 100%);
    min-height: 100vh;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #111d2b 0%, #162233 100%) !important;
    border-left: 1px solid rgba(56, 189, 248, 0.15);
    border-right: none;
}
[data-testid="stSidebar"] .stRadio label {
    color: #94a3b8 !important;
    font-size: 15px;
    padding: 8px 12px;
    border-radius: 8px;
    transition: all 0.2s;
    direction: rtl;
    text-align: right;
}
[data-testid="stSidebar"] .stRadio label:hover {
    background: rgba(56, 189, 248, 0.1);
    color: #38bdf8 !important;
}
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2 {
    color: #38bdf8 !important;
    font-weight: 700;
    letter-spacing: -0.5px;
    text-align: right;
}

/* ── Text & Headings ── */
h1, h2, h3, h4, h5, h6 {
    font-family: 'Heebo', sans-serif !important;
    direction: rtl;
    text-align: right;
    color: #f1f5f9 !important;
    font-weight: 700;
    letter-spacing: -0.5px;
}
h1 { font-size: 2rem !important; }
h2 { font-size: 1.5rem !important; }
h3 { font-size: 1.2rem !important; }

p, li, span, div, label {
    direction: rtl;
    text-align: right;
    color: #cbd5e1;
}

/* ── Metric Cards ── */
[data-testid="stMetric"] {
    background: linear-gradient(135deg, #1e3a5f 0%, #162d4a 100%);
    border: 1px solid rgba(56, 189, 248, 0.2);
    border-radius: 16px;
    padding: 20px 24px !important;
    text-align: center;
    direction: rtl;
    transition: transform 0.2s, box-shadow 0.2s;
    box-shadow: 0 4px 24px rgba(0,0,0,0.3);
}
[data-testid="stMetric"]:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 32px rgba(56, 189, 248, 0.15);
}
[data-testid="stMetricLabel"] {
    color: #94a3b8 !important;
    font-size: 13px !important;
    font-weight: 500;
    text-align: center !important;
    direction: rtl;
}
[data-testid="stMetricValue"] {
    color: #38bdf8 !important;
    font-size: 2rem !important;
    font-weight: 800;
    text-align: center !important;
}

/* ── Buttons ── */
.stButton > button {
    background: linear-gradient(135deg, #0ea5e9, #0284c7) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 10px 28px !important;
    font-family: 'Heebo', sans-serif !important;
    font-size: 15px !important;
    font-weight: 600 !important;
    direction: rtl;
    transition: all 0.2s !important;
    box-shadow: 0 4px 15px rgba(14, 165, 233, 0.3) !important;
}
.stButton > button:hover {
    background: linear-gradient(135deg, #38bdf8, #0ea5e9) !important;
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(14, 165, 233, 0.4) !important;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #0ea5e9, #7c3aed) !important;
    box-shadow: 0 4px 20px rgba(124, 58, 237, 0.35) !important;
}

/* ── Inputs & Selects ── */
.stSelectbox > div > div,
.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stDateInput > div > div > input {
    background: #1e3a5f !important;
    border: 1px solid rgba(56, 189, 248, 0.25) !important;
    border-radius: 10px !important;
    color: #f1f5f9 !important;
    font-family: 'Heebo', sans-serif !important;
    direction: rtl;
}
.stSelectbox label, .stTextInput label,
.stNumberInput label, .stDateInput label,
.stCheckbox label {
    color: #94a3b8 !important;
    font-size: 14px;
    font-weight: 500;
    direction: rtl;
    text-align: right;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: rgba(30, 58, 95, 0.5);
    border-radius: 12px;
    padding: 4px;
    direction: rtl;
}
.stTabs [data-baseweb="tab"] {
    color: #94a3b8 !important;
    font-family: 'Heebo', sans-serif !important;
    font-weight: 500;
    border-radius: 8px;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #0ea5e9, #0284c7) !important;
    color: white !important;
}

/* ── Dataframe ── */
[data-testid="stDataFrame"] {
    border-radius: 12px;
    overflow: hidden;
    border: 1px solid rgba(56, 189, 248, 0.15);
}

/* ── Alerts ── */
.stSuccess, .stInfo, .stWarning {
    border-radius: 12px !important;
    direction: rtl;
    text-align: right;
    font-family: 'Heebo', sans-serif !important;
}

/* ── Divider ── */
hr {
    border-color: rgba(56, 189, 248, 0.15) !important;
    margin: 24px 0 !important;
}

/* ── Plotly charts background ── */
.js-plotly-plot {
    border-radius: 16px;
    overflow: hidden;
    background: rgba(22, 45, 74, 0.6) !important;
}

/* ── Checkbox ── */
.stCheckbox {
    direction: rtl;
}

/* ── Table ── */
table {
    direction: rtl;
    width: 100%;
    border-collapse: collapse;
    font-family: 'Heebo', sans-serif;
}
th {
    background: rgba(14, 165, 233, 0.15);
    color: #38bdf8 !important;
    padding: 10px 16px;
    text-align: right;
    font-weight: 600;
    font-size: 13px;
    border-bottom: 1px solid rgba(56, 189, 248, 0.2);
}
td {
    padding: 10px 16px;
    color: #cbd5e1;
    border-bottom: 1px solid rgba(255,255,255,0.05);
    font-size: 14px;
}
tr:hover td { background: rgba(56, 189, 248, 0.05); }

/* ── Section card ── */
.section-card {
    background: rgba(22, 45, 74, 0.55);
    border: 1px solid rgba(56, 189, 248, 0.12);
    border-radius: 20px;
    padding: 28px 32px;
    margin-bottom: 24px;
    backdrop-filter: blur(8px);
}

/* ── Page title ── */
.page-title {
    font-size: 2.2rem;
    font-weight: 800;
    color: #f1f5f9;
    direction: rtl;
    text-align: right;
    margin-bottom: 4px;
    letter-spacing: -1px;
}
.page-subtitle {
    font-size: 15px;
    color: #64748b;
    direction: rtl;
    text-align: right;
    margin-bottom: 32px;
}
.accent { color: #38bdf8; }
</style>
""", unsafe_allow_html=True)


# ─── Data ──────────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_csv('data.csv')
    date_cols = ['בדיקת תאריך עדכון של לשרטוט', 'סוף', 'התחלה', 'תאריך סיום צפוי (SLA)']
    for col in date_cols:
        df[col] = pd.to_datetime(df[col], errors='coerce')
    df['משך בפועל (ימים)'] = (df['סוף'] - df['התחלה']).dt.days
    df['Time Spent (שעות)'] = df['Σ Time Spent'] / 3600
    df['חריגה SLA'] = df['משך בפועל (ימים)'] - df['SLA התחייבות (ימים)']
    df['עמידה ב-SLA'] = df['חריגה SLA'] <= 0
    if 'שטח בדונם' in df.columns:
        df['שטח בדונם'] = pd.to_numeric(df['שטח בדונם'], errors='coerce')
        def get_area_group(val):
            if pd.isna(val): return 'לא מוגדר'
            if val <= 5:  return 'קטן (0-5 דונם)'
            elif val <= 10: return 'בינוני (5-10 דונם)'
            else: return 'גדול (10+ דונם)'
        df['קבוצת שטח'] = df['שטח בדונם'].apply(get_area_group)
    return df

df = load_data()

# ─── Sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.markdown("## 📐 מערכת מדידות")
st.sidebar.markdown("---")
page = st.sidebar.radio('', ['דשבורד', 'גרפים ו-EDA', 'טבלת נתונים', 'חיזוי לוח זמנים'])
st.sidebar.markdown("---")
st.sidebar.markdown(f"<p style='color:#475569;font-size:12px;text-align:right'>סה\"כ פרויקטים: <strong style='color:#38bdf8'>{len(df)}</strong></p>", unsafe_allow_html=True)

# ─── Plotly dark theme helper ──────────────────────────────────────────────────
DARK_LAYOUT = dict(
    paper_bgcolor='rgba(22,45,74,0.0)',
    plot_bgcolor='rgba(22,45,74,0.0)',
    font=dict(family='Heebo, Arial', size=14, color='#cbd5e1'),
    xaxis=dict(gridcolor='rgba(255,255,255,0.06)', zerolinecolor='rgba(255,255,255,0.1)'),
    yaxis=dict(gridcolor='rgba(255,255,255,0.06)', zerolinecolor='rgba(255,255,255,0.1)'),
    margin=dict(t=40, b=40, l=20, r=20),
)

# ══════════════════════════════════════════════════════════════════════════════
#  דשבורד
# ══════════════════════════════════════════════════════════════════════════════
if page == 'דשבורד':
    st.markdown('<div class="page-title">דשבורד <span class="accent">סטטיסטיקות</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">סיכום ביצועים ועמידה ב-SLA</div>', unsafe_allow_html=True)

    total    = len(df)
    sla_rate = df['עמידה ב-SLA'].mean() * 100
    avg_days = df['משך בפועל (ימים)'].mean()
    avg_hrs  = df['Time Spent (שעות)'].mean()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric('סה"כ פרויקטים', total)
    c2.metric('עמידה ב-SLA', f'{sla_rate:.1f}%')
    c3.metric('משך ממוצע (ימים)', f'{avg_days:.1f}')
    c4.metric('שעות עבודה ממוצעות', f'{avg_hrs:.1f}')

    st.markdown('---')
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader('עמידה ב-SLA לפי סוג פרויקט')
        sla_type = (df.groupby('Custom field (סוג פרויקט)')['עמידה ב-SLA']
                    .mean().mul(100).reset_index())
        sla_type.columns = ['סוג פרויקט', 'אחוז עמידה']
        fig = px.bar(sla_type, x='סוג פרויקט', y='אחוז עמידה',
                     color='אחוז עמידה', color_continuous_scale='Blues',
                     range_color=[0,100], text_auto='.1f')
        fig.update_layout(**DARK_LAYOUT, xaxis_tickangle=-30,
                          coloraxis_showscale=False)
        fig.update_traces(marker_line_width=0)
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        st.subheader('התפלגות עמידה ב-SLA')
        counts = df['עמידה ב-SLA'].map({True:'עמד', False:'חרג'}).value_counts().reset_index()
        counts.columns = ['סטטוס', 'כמות']
        fig = px.pie(counts, values='כמות', names='סטטוס',
                     color='סטטוס',
                     color_discrete_map={'עמד':'#0ea5e9', 'חרג':'#f43f5e'},
                     hole=0.55)
        fig.update_layout(**DARK_LAYOUT)
        fig.update_traces(textfont_size=15)
        st.plotly_chart(fig, use_container_width=True)

    st.subheader('משך ממוצע לפי מנהל פרויקט')
    mgr = (df.groupby('Custom field (מנהל פרויקט)')['משך בפועל (ימים)']
           .mean().round(1).reset_index())
    mgr.columns = ['מנהל פרויקט', 'משך ממוצע (ימים)']
    fig = px.bar(mgr, x='מנהל פרויקט', y='משך ממוצע (ימים)',
                 text_auto=True, color='משך ממוצע (ימים)',
                 color_continuous_scale='Blues')
    fig.update_layout(**DARK_LAYOUT, coloraxis_showscale=False)
    fig.update_traces(marker_line_width=0)
    st.plotly_chart(fig, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
#  EDA
# ══════════════════════════════════════════════════════════════════════════════
elif page == 'גרפים ו-EDA':
    st.markdown('<div class="page-title">ניתוח <span class="accent">נתונים</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">חקירה סטטיסטית של נתוני הפרויקטים</div>', unsafe_allow_html=True)

    st.subheader('התפלגות משך פרויקט בפועל')
    fig = px.histogram(df, x='משך בפועל (ימים)', nbins=25, marginal='box',
                       color_discrete_sequence=['#0ea5e9'])
    fig.update_layout(**DARK_LAYOUT)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader('משך פרויקט לפי סוג')
    fig = px.box(df, x='Custom field (סוג פרויקט)', y='משך בפועל (ימים)',
                 color='Custom field (סוג פרויקט)')
    fig.update_layout(**DARK_LAYOUT, showlegend=False, xaxis_tickangle=-30)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader('קורלציה: זמן עבודה מול משך בפועל')
    fig = px.scatter(df, x='Time Spent (שעות)', y='משך בפועל (ימים)',
                     color='Custom field (סוג פרויקט)', trendline='ols',
                     hover_data=['Issue key'])
    fig.update_layout(**DARK_LAYOUT)
    st.plotly_chart(fig, use_container_width=True)

    if 'שטח בדונם' in df.columns:
        st.subheader('קורלציה: שטח בדונם מול משך בפועל')
        df_area = df[df['שטח בדונם'].notna()]
        if not df_area.empty:
            fig = px.scatter(df_area, x='שטח בדונם', y='משך בפועל (ימים)',
                             color='Custom field (סוג פרויקט)', trendline='ols',
                             hover_data=['Issue key'])
            fig.update_layout(**DARK_LAYOUT)
            st.plotly_chart(fig, use_container_width=True)

            st.markdown('---')
            st.subheader('🌳 ניתוח לפי קבוצות שטח פרויקט')
            show_estimated = st.checkbox(
                '🔮 הצג הערכת שטח משוערת לכלל הפרויקטים (חיזוי Random Forest)',
                value=False
            )
            if show_estimated:
                from sklearn.ensemble import RandomForestRegressor
                df_known   = df_area.copy()
                df_missing = df[df['שטח בדונם'].isna()].copy()
                FEATURES_AREA = ['תשומות משרד','תשומות שטח','Time Spent (שעות)','משך בפועל (ימים)']
                for d in [df_known, df_missing]:
                    d['תשומות משרד'] = pd.to_numeric(d['Custom field (תשומות - משרד)'], errors='coerce').fillna(0)
                    d['תשומות שטח']  = pd.to_numeric(d['Custom field (תשומות - שטח)'],  errors='coerce').fillna(0)
                X_train = df_known[FEATURES_AREA]
                y_train = df_known['שטח בדונם']
                rf_model = RandomForestRegressor(n_estimators=100, max_depth=4, random_state=42)
                rf_model.fit(X_train, y_train)
                if not df_missing.empty:
                    X_missing = df_missing[FEATURES_AREA]
                    df_missing = df_missing.copy()
                    df_missing['שטח בדונם'] = rf_model.predict(X_missing).clip(min=0.1)
                    df_missing['קבוצת שטח'] = df_missing['שטח בדונם'].apply(
                        lambda v: 'קטן (0-5 דונם)' if v<=5 else ('בינוני (5-10 דונם)' if v<=10 else 'גדול (10+ דונם)'))
                    df_all = pd.concat([df_known, df_missing], ignore_index=True)
                else:
                    df_all = df_known
                area_group_stats = (df_all.groupby('קבוצת שטח')['משך בפועל (ימים)']
                                    .agg(['mean','median','count']).reset_index())
                area_group_stats.columns = ['קבוצת שטח','ממוצע (ימים)','חציון (ימים)','מספר פרויקטים']
                st.dataframe(area_group_stats, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
#  טבלת נתונים
# ══════════════════════════════════════════════════════════════════════════════
elif page == 'טבלת נתונים':
    st.markdown('<div class="page-title">טבלת <span class="accent">נתונים</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">עיון, חיפוש וסינון הנתונים</div>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["📊 סקירה כללית", "🔍 חיפוש וסינון"])

    with tab1:
        st.subheader("סקירה כללית של הנתונים")
        col1, col2 = st.columns(2)
        with col1:
            raw_df = pd.read_csv('data.csv')
            st.metric("מספר שורות", f"{len(raw_df):,}")
        with col2:
            st.metric("מספר עמודות", f"{len(raw_df.columns)}")
        st.subheader("סוג כל עמודה")
        dtypes_df = pd.DataFrame({
            'שם העמודה': raw_df.columns,
            'סוג נתונים': raw_df.dtypes.astype(str)
        }).reset_index(drop=True)
        st.dataframe(dtypes_df, use_container_width=True)

    with tab2:
        st.subheader("חיפוש וסינון נתונים")
        col1, col2, col3 = st.columns(3)
        with col1:
            types = ['הכל'] + sorted(df['Custom field (סוג פרויקט)'].dropna().unique().tolist())
            sel_type = st.selectbox('סוג פרויקט:', types)
        with col2:
            managers = ['הכל'] + sorted(df['Custom field (מנהל פרויקט)'].dropna().unique().tolist())
            sel_mgr = st.selectbox('מנהל פרויקט:', managers)
        with col3:
            search_key = st.text_input('חיפוש לפי מספר פרויקט:', value='')

        filtered = df.copy()
        if sel_type != 'הכל':
            filtered = filtered[filtered['Custom field (סוג פרויקט)'] == sel_type]
        if sel_mgr != 'הכל':
            filtered = filtered[filtered['Custom field (מנהל פרויקט)'] == sel_mgr]
        if search_key.strip():
            filtered = filtered[filtered['Issue key'].astype(str).str.contains(search_key, case=False, na=False)]

        st.markdown(f"<p>מוצגות <strong style='color:#38bdf8'>{len(filtered)}</strong> רשומות מתוך {len(df)}</p>", unsafe_allow_html=True)
        st.dataframe(filtered, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
#  חיזוי
# ══════════════════════════════════════════════════════════════════════════════
elif page == 'חיזוי לוח זמנים':
    st.markdown('<div class="page-title">חיזוי <span class="accent">לוח זמנים</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="page-subtitle">הערכת זמנים חכמה מבוססת מודל ML</div>', unsafe_allow_html=True)

    project_types = sorted(df['Custom field (סוג פרויקט)'].dropna().unique().tolist())

    col1, col2, col_num = st.columns(3)
    with col1:
        project_type = st.selectbox('סוג פרויקט:', project_types)
    with col2:
        start_date = st.date_input('תאריך התחלה:', datetime.date.today())
    with col_num:
        project_number = st.text_input('מספר פרויקט:', value="1001")

    type_df = df[df['Custom field (סוג פרויקט)'] == project_type]
    default_sla = 65
    if not type_df.empty and 'SLA התחייבות (ימים)' in type_df.columns:
        sla_series = type_df['SLA התחייבות (ימים)'].dropna()
        if not sla_series.empty:
            try: default_sla = int(sla_series.iloc[0])
            except: default_sla = 65

    col3, col4, col5, col6 = st.columns(4)
    with col3:
        office_work = st.number_input('תשומות משרד (שעות):', min_value=0.0, value=9.0, step=1.0)
    with col4:
        field_work  = st.number_input('תשומות שטח (שעות):', min_value=0.0, value=9.0, step=1.0)

    import math
    if field_work <= 0:   recommended_sla = 7
    elif field_work <= 9: recommended_sla = 14
    else: recommended_sla = 14 + int(math.ceil((field_work-9)/9.0)*7)

    with col5:
        sla_days = st.number_input('SLA חוזי (ימים):', min_value=1, value=int(recommended_sla), step=1,
                                   help="פרק הזמן המרבי שהובטח ללקוח בחוזה")
    with col6:
        project_area = st.number_input('שטח המדידה (דונם):', min_value=0.1, value=5.0, step=1.0)

    if   project_area <= 5:  st.markdown("🟢 **קבוצת שטח: קטן (0-5 דונם)**")
    elif project_area <= 10: st.markdown("🔵 **קבוצת שטח: בינוני (5-10 דונם)**")
    else:                    st.markdown("🔴 **קבוצת שטח: גדול (10+ דונם)**")

    if st.button('⚡ חשב וחזה לוח זמנים', type='primary'):
        predicted_days  = None
        used_ml_model   = False
        try:
            model = joblib.load('models/model.pkl')
            input_data = pd.DataFrame([{
                'Custom field (סוג פרויקט)':    project_type,
                'Custom field (תשומות - משרד)': office_work,
                'Custom field (תשומות - שטח)':  field_work,
                'SLA התחייבות (ימים)':           int(sla_days),
                'שטח בדונם':                     project_area
            }])
            predicted_days = int(round(model.predict(input_data)[0]))
            used_ml_model  = True
        except Exception:
            try:
                from main import estimate_project_duration
                predicted_days = estimate_project_duration(project_type, project_area)
            except Exception:
                predicted_days = int(sla_days)

        schedule_model = calculate_target_dates(start_date, predicted_days)
        schedule_sla   = calculate_target_dates(start_date, int(sla_days))

        st.markdown('---')
        st.markdown(f"### 📋 לוחות זמנים לפרויקט {project_number}")

        model_label = "Ridge Regression" if used_ml_model else "מודל ליניארי"
        st.info(f"🔮 **חיזוי ({model_label}):** {predicted_days} ימים בפועל  |  📋 **SLA חוזי:** {int(sla_days)} ימים")

        if predicted_days <= sla_days:
            st.success(f"✅ **בטוח לעבודה!** צפויים לסיים **{sla_days - predicted_days} ימים לפני הדדליין**.")
        else:
            st.warning(f"⚠️ **סכנת עיכוב!** צפויה חריגה של **{predicted_days - sla_days} ימים** מה-SLA.")

        res_tab1, res_tab2 = st.tabs(["🔮 לוח זמנים מבוסס חיזוי", "📋 לוח זמנים חוזי (SLA)"])

        def build_schedule_table(schedule, label_days):
            st.markdown(f"🎯 **תאריך יעד סופי:** {schedule['final_deadline'].strftime('%d/%m/%Y')}  |  **{label_days} ימים**")
            rows, prev = [], start_date
            for stage, deadline in schedule['stages'].items():
                rows.append({'שלב': stage, 'תאריך התחלה': prev.strftime('%d/%m/%Y'),
                             'תאריך יעד': deadline.strftime('%d/%m/%Y'),
                             'ימים': (deadline-prev).days})
                prev = deadline
            st.table(pd.DataFrame(rows))
            gantt = [{'שלב': r['שלב'], 'התחלה': start_date, 'סיום': deadline}
                     for r, (_, deadline) in zip(rows, schedule['stages'].items())]
            prev2 = start_date
            gantt2 = []
            for stage, deadline in schedule['stages'].items():
                gantt2.append({'שלב': stage, 'התחלה': prev2, 'סיום': deadline})
                prev2 = deadline
            fig = px.timeline(pd.DataFrame(gantt2), x_start='התחלה', x_end='סיום',
                              y='שלב', color='שלב')
            fig.update_yaxes(autorange='reversed')
            fig.update_layout(**DARK_LAYOUT)
            st.plotly_chart(fig, use_container_width=True)

        with res_tab1:
            build_schedule_table(schedule_model, predicted_days)
        with res_tab2:
            build_schedule_table(schedule_sla, int(sla_days))
