import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score

# Load data
df = pd.read_csv('data/dataset.csv')
df['סוף']    = pd.to_datetime(df['סוף'],    errors='coerce')
df['התחלה']  = pd.to_datetime(df['התחלה'],  errors='coerce')
df['משך בפועל (ימים)'] = (df['סוף'] - df['התחלה']).dt.days
df['Time Spent (שעות)'] = df['Σ Time Spent'] / 3600
df['תשומות משרד'] = pd.to_numeric(df['Custom field (תשומות - משרד)'], errors='coerce').fillna(0)
df['תשומות שטח'] = pd.to_numeric(df['Custom field (תשומות - שטח)'], errors='coerce').fillna(0)
df['SLA התחייבות (ימים)'] = pd.to_numeric(df['SLA התחייבות (ימים)'], errors='coerce').fillna(65)
df['שטח בדונם'] = pd.to_numeric(df['שטח בדונם'], errors='coerce')

# Filter valid target
df = df.dropna(subset=['Custom field (סוג פרויקט)', 'משך בפועל (ימים)'])
df = df[(df['משך בפועל (ימים)'] > 0) & (df['משך בפועל (ימים)'] <= 365)]

# Step 1: Impute Area using Random Forest
df_known = df[df['שטח בדונם'].notna()].copy()
df_missing = df[df['שטח בדונם'].isna()].copy()

FEATURES_AREA = ['תשומות משרד', 'תשומות שטח', 'Time Spent (שעות)', 'SLA התחייבות (ימים)']
X_train_area = df_known[FEATURES_AREA]
y_train_area = df_known['שטח בדונם']

rf_area = RandomForestRegressor(n_estimators=100, max_depth=4, random_state=42)
rf_area.fit(X_train_area, y_train_area)

if not df_missing.empty:
    X_missing_area = df_missing[FEATURES_AREA]
    df_missing['שטח בדונם'] = rf_area.predict(X_missing_area)

df_imputed = pd.concat([df_known, df_missing])

# Add area group feature
def get_area_group(val):
    if val <= 5: return 'Small'
    elif val <= 10: return 'Medium'
    else: return 'Large'
df_imputed['קבוצת שטח'] = df_imputed['שטח בדונם'].apply(get_area_group)

# Step 2: Evaluate Duration prediction models with Area included
# Scenario A: Numeric Area included
FEATURES_A = [
    'Custom field (סוג פרויקט)',
    'Custom field (תשומות - משרד)',
    'Custom field (תשומות - שטח)',
    'SLA התחייבות (ימים)',
    'שטח בדונם'
]
X_A = df_imputed[FEATURES_A]
y = df_imputed['משך בפועל (ימים)']

X_train, X_test, y_train, y_test = train_test_split(X_A, y, test_size=0.2, random_state=42)

preprocessor_A = ColumnTransformer([
    ('cat', OneHotEncoder(handle_unknown='ignore'), ['Custom field (סוג פרויקט)']),
    ('num', StandardScaler(), ['Custom field (תשומות - משרד)', 'Custom field (תשומות - שטח)', 'SLA התחייבות (ימים)', 'שטח בדונם']),
])

model_A = Pipeline([('preprocessor', preprocessor_A), ('model', Ridge(alpha=1.0))])
model_A.fit(X_train, y_train)
y_pred_A = model_A.predict(X_test)
print("Scenario A (Exact Area Numeric Feature):")
print(f"  R^2: {r2_score(y_test, y_pred_A):.3f}")
print(f"  MAE: {mean_absolute_error(y_test, y_pred_A):.1f} ימים")

# Scenario B: Categorical Area Group included
FEATURES_B = [
    'Custom field (סוג פרויקט)',
    'Custom field (תשומות - משרד)',
    'Custom field (תשומות - שטח)',
    'SLA התחייבות (ימים)',
    'קבוצת שטח'
]
X_B = df_imputed[FEATURES_B]

X_train_B, X_test_B, y_train_B, y_test_B = train_test_split(X_B, y, test_size=0.2, random_state=42)

preprocessor_B = ColumnTransformer([
    ('cat', OneHotEncoder(handle_unknown='ignore'), ['Custom field (סוג פרויקט)', 'קבוצת שטח']),
    ('num', StandardScaler(), ['Custom field (תשומות - משרד)', 'Custom field (תשומות - שטח)', 'SLA התחייבות (ימים)']),
])

model_B = Pipeline([('preprocessor', preprocessor_B), ('model', Ridge(alpha=1.0))])
model_B.fit(X_train_B, y_train_B)
y_pred_B = model_B.predict(X_test_B)
print("\nScenario B (Area Group Category Feature):")
print(f"  R^2: {r2_score(y_test_B, y_pred_B):.3f}")
print(f"  MAE: {mean_absolute_error(y_test_B, y_pred_B):.1f} ימים")
