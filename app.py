import os
import streamlit as st
import pandas as pd
import plotly.express as px
import datetime
import joblib
from main import calculate_target_dates

# התאמת גופנים בגרפים לגדולים וקריאים יותר באופן גלובלי
_original_plotly_chart = st.plotly_chart
def show_large_plotly_chart(fig, *args, **kwargs):
    if hasattr(fig, 'update_layout'):
        fig.update_layout(
            font=dict(size=16, family="Arial"),
            title=dict(font=dict(size=20)),
            hoverlabel=dict(font=dict(size=15)),
            xaxis=dict(tickfont=dict(size=14), title=dict(font=dict(size=16))),
            yaxis=dict(tickfont=dict(size=14), title=dict(font=dict(size=16)))
        )
    return _original_plotly_chart(fig, *args, **kwargs)
st.plotly_chart = show_large_plotly_chart


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
    if 'שטח בדונם' in df.columns:
        df['שטח בדונם'] = pd.to_numeric(df['שטח בדונם'], errors='coerce')
        def get_area_group(val):
            if pd.isna(val):
                return 'לא מוגדר'
            if val <= 5:
                # 0-5 Dunam
                return 'קטן (0-5 דונם)'
            elif val <= 10:
                # 5-10 Dunam
                return 'בינוני (5-10 דונם)'
            else:
                # 10+ Dunam
                return 'גדול (10+ דונם)'
        df['קבוצת שטח'] = df['שטח בדונם'].apply(get_area_group)
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

    if 'שטח בדונם' in df.columns:
        st.subheader('קורלציה: שטח בדונם מול משך בפועל')
        df_area = df[df['שטח בדונם'].notna()]
        if not df_area.empty:
            fig = px.scatter(
                df_area, x='שטח בדונם', y='משך בפועל (ימים)',
                color='Custom field (סוג פרויקט)', trendline='ols',
                hover_data=['Issue key']
            )
            st.plotly_chart(fig, use_container_width=True)

            st.markdown('---')
            st.subheader('🌳 ניתוח לפי קבוצות שטח פרויקט')
            
            show_estimated = st.checkbox(
                '🔮 הצג הערכת שטח משוערת לכלל הפרויקטים (חיזוי במודל Random Forest עבור 217 פרויקטים חסרים על בסיס תשומותיהם)',
                value=False
            )
            
            if show_estimated:
                from sklearn.ensemble import RandomForestRegressor
                df_known = df_area.copy()
                df_missing = df[df['שטח בדונם'].isna()].copy()
                
                FEATURES_AREA = ['תשומות משרד', 'תשומות שטח', 'Time Spent (שעות)', 'משך בפועל (ימים)']
                
                # Prep features
                for d in [df_known, df_missing]:
                    d['תשומות משרד'] = pd.to_numeric(d['Custom field (תשומות - משרד)'], errors='coerce').fillna(0)
                    d['תשומות שטח'] = pd.to_numeric(d['Custom field (תשומות - שטח)'], errors='coerce').fillna(0)
                
                X_train = df_known[FEATURES_AREA]
                y_train = df_known['שטח בדונם']
                
                # Train model
                rf_model = RandomForestRegressor(n_estimators=100, max_depth=4, random_state=42)
                rf_model.fit(X_train, y_train)
                
                # Predict missing areas
                if not df_missing.empty:
                    X_missing = df_missing[FEATURES_AREA]
                    df_missing['שטח בדונם'] = rf_model.predict(X_missing)
                
                # Recategorize
                def get_area_group(val):
                    if pd.isna(val): return 'לא מוגדר'
                    if val <= 5: return 'קטן (0-5 דונם)'
                    elif val <= 10: return 'בינוני (5-10 דונם)'
                    else: return 'גדול (10+ דונם)'
                
                df_known['קבוצת שטח'] = df_known['שטח בדונם'].apply(get_area_group)
                df_missing['קבוצת שטח'] = df_missing['שטח בדונם'].apply(get_area_group)
                
                df_for_charts = pd.concat([df_known, df_missing])
                title_suffix = ' (בפועל + משוער לכלל 267 הפרויקטים)'
                
                st.info('💡 המערכת אימנה מודל Random Forest על גבי 50 הפרויקטים בעלי השטח הידוע, וביצעה חיזוי שטח לכל שאר 217 הפרויקטים בהתבסס על תשומות משרד, שטח, שעות עבודה ומשך הפרויקט.')
            else:
                df_for_charts = df_area[df_area['קבוצת שטח'] != 'לא מוגדר'].copy()
                title_suffix = ' (50 פרויקטים נמדדים בלבד)'
            
            c_area_1, c_area_2 = st.columns(2)
            with c_area_1:
                st.markdown(f'<p style="text-align:right; font-weight:bold; font-size:1.1rem;">התפלגות פרויקטים{title_suffix}</p>', unsafe_allow_html=True)
                area_counts = df_for_charts['קבוצת שטח'].value_counts().reset_index()
                area_counts.columns = ['קבוצת שטח', 'כמות']
                
                # סדר הצגה נכון (קטן -> בינוני -> גדול)
                order_map = {'קטן (0-5 דונם)': 0, 'בינוני (5-10 דונם)': 1, 'גדול (10+ דונם)': 2}
                area_counts['sort_idx'] = area_counts['קבוצת שטח'].map(order_map)
                area_counts = area_counts.sort_values('sort_idx')

                fig_ac = px.pie(
                    area_counts, values='כמות', names='קבוצת שטח',
                    color='קבוצת שטח',
                    color_discrete_map={
                        'קטן (0-5 דונם)': '#6c63ff',
                        'בינוני (5-10 דונם)': '#00d2ff',
                        'גדול (10+ דונם)': '#ff6b6b'
                    }
                )
                st.plotly_chart(fig_ac, use_container_width=True)
                
            with c_area_2:
                st.markdown(f'<p style="text-align:right; font-weight:bold; font-size:1.1rem;">משך פרויקט ממוצע (ימים){title_suffix}</p>', unsafe_allow_html=True)
                area_duration = df_for_charts.groupby('קבוצת שטח')['משך בפועל (ימים)'].mean().round(1).reset_index()
                area_duration.columns = ['קבוצת שטח', 'משך ממוצע (ימים)']
                
                area_duration['sort_idx'] = area_duration['קבוצת שטח'].map(order_map)
                area_duration = area_duration.sort_values('sort_idx')

                fig_ad = px.bar(
                    area_duration, x='קבוצת שטח', y='משך ממוצע (ימים)', text_auto=True,
                    color='קבוצת שטח',
                    color_discrete_map={
                        'קטן (0-5 דונם)': '#6c63ff',
                        'בינוני (5-10 דונם)': '#00d2ff',
                        'גדול (10+ דונם)': '#ff6b6b'
                    }
                )
                st.plotly_chart(fig_ad, use_container_width=True)
        else:
            st.info('אין נתוני שטח זמינים בחתך הנוכחי.')

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

    tab1, tab2 = st.tabs(["📊 ניתוח ראשוני (דרישות המטלה)", "🔍 חיפוש וסינון נתונים"])

    with tab1:
        st.header("📊 טעינת נתונים וניתוח ראשוני")
        st.markdown("עמוד זה מציג ניתוח ראשוני של קובץ הנתונים הגולמי `data.csv` כפי שנדרש במטלה.")
        
        # טעינת קובץ גולמי
        raw_df = pd.read_csv('data.csv')
        
        # 1. 5 שורות ראשונות
        st.subheader("🔍 5 השורות הראשונות של הטבלה")
        st.dataframe(raw_df.head(5), use_container_width=True)
        
        # 2. מספר שורות ועמודות
        st.subheader("📐 מימדי הטבלה")
        rows, cols = raw_df.shape
        c1, c2 = st.columns(2)
        with c1:
            st.metric(label="מספר שורות כולל", value=f"{rows:,}")
        with c2:
            st.metric(label="מספר עמודות כולל", value=f"{cols}")
            
        # 3. סוג כל עמודה
        st.subheader("🏷️ סוג כל עמודה (Data Types)")
        dtypes_df = pd.DataFrame({
            'שם העמודה': raw_df.columns,
            'סוג נתונים (Dtype)': raw_df.dtypes.astype(str)
        }).reset_index(drop=True)
        st.dataframe(dtypes_df, use_container_width=True)

    with tab2:
        st.header("🔍 חיפוש וסינון נתונים")
        col1, col2, col3 = st.columns(3)
        with col1:
            types = ['הכל'] + sorted(df['Custom field (סוג פרויקט)'].dropna().unique().tolist())
            sel_type = st.selectbox('סוג פרויקט:', types)
        with col2:
            managers = ['הכל'] + sorted(df['Custom field (מנהל פרויקט)'].dropna().unique().tolist())
            sel_mgr = st.selectbox('מנהל פרויקט:', managers)
        with col3:
            search_key = st.text_input('חיפוש לפי מספר פרויקט (Issue Key):', value='')

        filtered = df.copy()
        if sel_type != 'הכל':
            filtered = filtered[filtered['Custom field (סוג פרויקט)'] == sel_type]
        if sel_mgr != 'הכל':
            filtered = filtered[filtered['Custom field (מנהל פרויקט)'] == sel_mgr]
        if search_key.strip() != '':
            filtered = filtered[filtered['Issue key'].astype(str).str.contains(search_key, case=False, na=False)]

        st.write(f'מוצגות **{len(filtered)}** רשומות מתוך {len(df)}')
        st.dataframe(filtered, use_container_width=True)

# ───────────────────────────── חיזוי ─────────────────────────────
elif page == 'חיזוי לוח זמנים':
    st.title('תכנון לוח זמנים לפרויקט (לפי SLA)')

    project_types = sorted(df['Custom field (סוג פרויקט)'].dropna().unique().tolist())

    col1, col2, col_num = st.columns(3)
    with col1:
        project_type = st.selectbox('סוג פרויקט:', project_types)
    with col2:
        start_date = st.date_input('תאריך התחלה:', datetime.date.today())
    with col_num:
        project_number = st.text_input('מספר פרויקט:', value="1001")

    # מציאת ה-SLA המוגדר כברירת מחדל עבור סוג הפרויקט שנבחר מהנתונים
    type_df = df[df['Custom field (סוג פרויקט)'] == project_type]
    if not type_df.empty and 'SLA התחייבות (ימים)' in type_df.columns:
        default_sla = int(type_df['SLA התחייבות (ימים)'].dropna().iloc[0])
    else:
        default_sla = 65

    col3, col4, col5, col6 = st.columns(4)
    with col3:
        office_work = st.number_input('תשומות משרד (שעות):', min_value=0.0, value=9.0, step=1.0)
    with col4:
        field_work = st.number_input('תשומות שטח (שעות):', min_value=0.0, value=9.0, step=1.0)
    with col5:
        sla_days = st.number_input('SLA התחייבות (ימים):', min_value=1, value=default_sla, step=1)
    with col6:
        project_area = st.number_input('שטח המדידה (דונם):', min_value=0.1, value=5.0, step=1.0)

    if project_area <= 5:
        area_group_desc = "🟢 קבוצת שטח: קטן (0-5 דונם)"
    elif project_area <= 10:
        area_group_desc = "🔵 קבוצת שטח: בינוני (5-10 דונם)"
    else:
        area_group_desc = "🔴 קבוצת שטח: גדול (10+ דונם)"
    st.markdown(f"**{area_group_desc}**")

    if st.button('חשב לוח זמנים', type='primary'):
        # חישוב לוח זמנים מתוכנן לפי SLA
        schedule_sla = calculate_target_dates(start_date, int(sla_days))

        st.markdown("---")
        st.markdown(f"### 📋 לוח זמנים מתוכנן לפרויקט מספר {project_number} (לפי SLA)")
        st.info(f"פרויקט: **{project_number}** | סוג: **{project_type}** | משך כולל: **{int(sla_days)} ימים** | 🎯 תאריך יעד סופי למסירה: **{schedule_sla['final_deadline'].strftime('%d/%m/%Y')}**")
        
        stages_rows_sla = []
        prev = start_date
        for stage, deadline in schedule_sla['stages'].items():
            days = (deadline - prev).days
            stages_rows_sla.append({
                'שלב': stage,
                'תאריך התחלה': prev.strftime('%d/%m/%Y'),
                'תאריך יעד': deadline.strftime('%d/%m/%Y'),
                'ימים': days,
            })
            prev = deadline
        st.table(pd.DataFrame(stages_rows_sla))

        # גאנט ללקוח
        gantt_sla = []
        prev = start_date
        for stage, deadline in schedule_sla['stages'].items():
            gantt_sla.append({'שלב': stage, 'התחלה': prev, 'סיום': deadline})
            prev = deadline
        fig_sla = px.timeline(
            pd.DataFrame(gantt_sla),
            x_start='התחלה', x_end='סיום', y='שלב', color='שלב'
        )
        fig_sla.update_yaxes(autorange='reversed')
        st.plotly_chart(fig_sla, use_container_width=True)

