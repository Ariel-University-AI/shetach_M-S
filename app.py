import os
import streamlit as st
import pandas as pd
import plotly.express as px
import datetime
import joblib
from main import calculate_target_dates

st.set_page_config(
    page_title='מערכת ניהול פרויקטי מדידה',
    page_icon='📐',
    layout='wide',
    initial_sidebar_state='expanded'
)

st.markdown("""
<style>
    body, .main, .block-container, p, h1, h2, h3, label, div {
        direction: rtl;
        text-align: right;
    }
    .stMetric { direction: rtl; }
    .stSelectbox label, .stNumberInput label, .stDateInput label { float: right; }
</style>
""", unsafe_allow_html=True)


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
    return df


df = load_data()

st.sidebar.title('📐 מערכת מדידות')
page = st.sidebar.radio('בחרי עמוד:', ['דשבורד', 'גרפים ו-EDA', 'טבלת נתונים', 'חיזוי לוח זמנים'])

# ───────────────────────────── דשבורד ─────────────────────────────
if page == 'דשבורד':
    st.title('דשבורד סטטיסטיקות')

    total = len(df)
    sla_rate = df['עמידה ב-SLA'].mean() * 100
    avg_days = df['משך בפועל (ימים)'].mean()
    avg_hours = df['Time Spent (שעות)'].mean()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric('סה"כ פרויקטים', total)
    c2.metric('עמידה ב-SLA', f'{sla_rate:.1f}%')
    c3.metric('משך ממוצע (ימים)', f'{avg_days:.1f}')
    c4.metric('שעות עבודה ממוצעות', f'{avg_hours:.1f}')

    st.markdown('---')

    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader('עמידה ב-SLA לפי סוג פרויקט')
        sla_type = (
            df.groupby('Custom field (סוג פרויקט)')['עמידה ב-SLA']
            .mean()
            .mul(100)
            .reset_index()
        )
        sla_type.columns = ['סוג פרויקט', 'אחוז עמידה']
        fig = px.bar(
            sla_type, x='סוג פרויקט', y='אחוז עמידה',
            color='אחוז עמידה', color_continuous_scale='RdYlGn',
            range_color=[0, 100], text_auto='.1f'
        )
        fig.update_layout(xaxis_tickangle=-30)
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        st.subheader('התפלגות עמידה ב-SLA')
        counts = df['עמידה ב-SLA'].map({True: 'עמד', False: 'חרג'}).value_counts().reset_index()
        counts.columns = ['סטטוס', 'כמות']
        fig = px.pie(
            counts, values='כמות', names='סטטוס',
            color='סטטוס', color_discrete_map={'עמד': '#2ecc71', 'חרג': '#e74c3c'}
        )
        st.plotly_chart(fig, use_container_width=True)

    st.subheader('משך ממוצע לפי מנהל פרויקט')
    mgr = (
        df.groupby('Custom field (מנהל פרויקט)')['משך בפועל (ימים)']
        .mean()
        .round(1)
        .reset_index()
    )
    mgr.columns = ['מנהל פרויקט', 'משך ממוצע (ימים)']
    fig = px.bar(mgr, x='מנהל פרויקט', y='משך ממוצע (ימים)', text_auto=True)
    st.plotly_chart(fig, use_container_width=True)

# ───────────────────────────── EDA ─────────────────────────────
elif page == 'גרפים ו-EDA':
    st.title('ניתוח נתונים (EDA)')

    st.subheader('התפלגות משך פרויקט בפועל')
    fig = px.histogram(df, x='משך בפועל (ימים)', nbins=25, marginal='box')
    st.plotly_chart(fig, use_container_width=True)

    st.subheader('משך פרויקט לפי סוג')
    fig = px.box(
        df, x='Custom field (סוג פרויקט)', y='משך בפועל (ימים)',
        color='Custom field (סוג פרויקט)'
    )
    fig.update_layout(showlegend=False, xaxis_tickangle=-30)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader('קורלציה: זמן עבודה מול משך בפועל')
    fig = px.scatter(
        df, x='Time Spent (שעות)', y='משך בפועל (ימים)',
        color='Custom field (סוג פרויקט)', trendline='ols',
        hover_data=['Issue key']
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader('חריגה מ-SLA לפי פרויקט')
    fig = px.bar(
        df.sort_values('חריגה SLA', ascending=False).head(30),
        x='Issue key', y='חריגה SLA',
        color='עמידה ב-SLA',
        color_discrete_map={True: '#2ecc71', False: '#e74c3c'}
    )
    fig.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)

# ───────────────────────────── טבלה ─────────────────────────────
elif page == 'טבלת נתונים':
    st.title('טבלת נתונים')

    col1, col2 = st.columns(2)
    with col1:
        types = ['הכל'] + sorted(df['Custom field (סוג פרויקט)'].dropna().unique().tolist())
        sel_type = st.selectbox('סוג פרויקט:', types)
    with col2:
        managers = ['הכל'] + sorted(df['Custom field (מנהל פרויקט)'].dropna().unique().tolist())
        sel_mgr = st.selectbox('מנהל פרויקט:', managers)

    filtered = df.copy()
    if sel_type != 'הכל':
        filtered = filtered[filtered['Custom field (סוג פרויקט)'] == sel_type]
    if sel_mgr != 'הכל':
        filtered = filtered[filtered['Custom field (מנהל פרויקט)'] == sel_mgr]

    st.write(f'מוצגות **{len(filtered)}** רשומות מתוך {len(df)}')
    st.dataframe(filtered, use_container_width=True)

# ───────────────────────────── חיזוי ─────────────────────────────
elif page == 'חיזוי לוח זמנים':
    st.title('חיזוי לוח זמנים לפרויקט')

    MODEL_PATH = 'models/model.pkl'
    model_exists = os.path.exists(MODEL_PATH)

    if not model_exists:
        st.warning('המודל טרם אומן. הרץ את `train_model.py` תחילה.')
        st.code('python train_model.py')
    else:
        ml_model = joblib.load(MODEL_PATH)
        project_types = sorted(df['Custom field (סוג פרויקט)'].dropna().unique().tolist())

        col1, col2 = st.columns(2)
        with col1:
            project_type = st.selectbox('סוג פרויקט:', project_types)
        with col2:
            start_date = st.date_input('תאריך התחלה:', datetime.date.today())

        col3, col4, col5 = st.columns(3)
        with col3:
            office_work = st.number_input('תשומות משרד (ימים):', min_value=0.0, value=9.0, step=1.0)
        with col4:
            field_work = st.number_input('תשומות שטח (ימים):', min_value=0.0, value=9.0, step=1.0)
        with col5:
            sla_days = st.number_input('SLA התחייבות (ימים):', min_value=1, value=65, step=1)

        if st.button('חשב לוח זמנים', type='primary'):
            input_df = pd.DataFrame([{
                'Custom field (סוג פרויקט)': project_type,
                'Custom field (תשומות - משרד)': office_work,
                'Custom field (תשומות - שטח)': field_work,
                'SLA התחייבות (ימים)': sla_days,
            }])

            total_days = max(1, int(round(ml_model.predict(input_df)[0])))
            schedule = calculate_target_dates(start_date, total_days)

            st.success(f'חיזוי המודל: **{total_days} ימים**')
            st.info(f'תאריך יעד סופי למסירה: **{schedule["final_deadline"].strftime("%d/%m/%Y")}**')

            st.subheader('פירוט שלבים')
            stages_rows = []
            prev = start_date
            for stage, deadline in schedule['stages'].items():
                days = (deadline - prev).days
                stages_rows.append({
                    'שלב': stage,
                    'תאריך התחלה': prev.strftime('%d/%m/%Y'),
                    'תאריך יעד': deadline.strftime('%d/%m/%Y'),
                    'ימים': days,
                })
                prev = deadline

            st.table(pd.DataFrame(stages_rows))

            st.subheader('גנט - לוח זמנים')
            gantt_data = []
            prev = start_date
            for stage, deadline in schedule['stages'].items():
                gantt_data.append({'שלב': stage, 'התחלה': prev, 'סיום': deadline})
                prev = deadline

            fig = px.timeline(
                pd.DataFrame(gantt_data),
                x_start='התחלה', x_end='סיום', y='שלב', color='שלב'
            )
            fig.update_yaxes(autorange='reversed')
            st.plotly_chart(fig, use_container_width=True)
