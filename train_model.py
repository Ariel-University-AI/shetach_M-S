import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib
import os

# ── טעינה וניקוי ────────────────────────────────────────────────
df = pd.read_csv('data/dataset.csv')

# סינון סוגי פרויקטים שלא מעוניינים להכליל במודל
exclude_types = [
    'מחלקת תצר - עבודות נוספות',
    'עבודת משרד',
    'סקר',
    'פיקוח',
    'ליווי הפקעות'
]
df = df[~df['Custom field (סוג פרויקט)'].isin(exclude_types)]

df['סוף']    = pd.to_datetime(df['סוף'],    errors='coerce')
df['התחלה']  = pd.to_datetime(df['התחלה'],  errors='coerce')
df['משך בפועל (ימים)'] = (df['סוף'] - df['התחלה']).dt.days

# המרת עמודת השטח למספר והשלמת חסרים לפי חציון
df['שטח בדונם'] = pd.to_numeric(df['שטח בדונם'], errors='coerce')
median_area = df['שטח בדונם'].median()
df['שטח בדונם'] = df['שטח בדונם'].fillna(median_area)

FEATURES = [
    'Custom field (סוג פרויקט)',
    'Custom field (תשומות - משרד)',
    'Custom field (תשומות - שטח)',
    'SLA התחייבות (ימים)',
    'שטח בדונם'
]
TARGET = 'משך בפועל (ימים)'

df_model = df[FEATURES + [TARGET]].copy()
df_model['Custom field (תשומות - משרד)'] = pd.to_numeric(
    df_model['Custom field (תשומות - משרד)'], errors='coerce').fillna(0)
df_model['Custom field (תשומות - שטח)'] = pd.to_numeric(
    df_model['Custom field (תשומות - שטח)'], errors='coerce').fillna(0)

df_model = df_model.dropna(subset=['Custom field (סוג פרויקט)', TARGET])
df_model = df_model[df_model[TARGET] > 0]

# הסרת חריגים קיצוניים (מעל 365 ימים)
df_model = df_model[df_model[TARGET] <= 365]

print(f"שורות לאימון לאחר ניקוי: {len(df_model)}")
print(f"סוגי פרויקטים: {df_model['Custom field (סוג פרויקט)'].nunique()}")

# ── חלוקה לסטים ─────────────────────────────────────────────────
X = df_model[FEATURES]
y = df_model[TARGET]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

print(f"Train: {len(X_train)} | Test: {len(X_test)}")

# ── בניית Pipeline ───────────────────────────────────────────────
CAT_COLS = ['Custom field (סוג פרויקט)']
NUM_COLS = [
    'Custom field (תשומות - משרד)',
    'Custom field (תשומות - שטח)',
    'SLA התחייבות (ימים)',
    'שטח בדונם'
]

preprocessor = ColumnTransformer([
    ('cat', OneHotEncoder(handle_unknown='ignore'), CAT_COLS),
    ('num', StandardScaler(),                       NUM_COLS),
])

candidates = {
    'RandomForest':       RandomForestRegressor(n_estimators=200, max_depth=10, random_state=42),
    'GradientBoosting':   GradientBoostingRegressor(n_estimators=200, max_depth=4, random_state=42),
    'Ridge':              Ridge(alpha=1.0),
}

# ── השוואת אלגוריתמים ────────────────────────────────────────────
print(f"\n{'אלגוריתם':<22} {'MAE':>8} {'RMSE':>8} {'R²':>8}")
print("-" * 50)

results = {}
for name, regressor in candidates.items():
    pipe = Pipeline([('preprocessor', preprocessor), ('model', regressor)])
    pipe.fit(X_train, y_train)
    y_pred = pipe.predict(X_test)
    mae  = mean_absolute_error(y_test, y_pred)
    rmse = mean_squared_error(y_test, y_pred) ** 0.5
    r2   = r2_score(y_test, y_pred)
    results[name] = {'pipe': pipe, 'mae': mae, 'rmse': rmse, 'r2': r2}
    print(f"{name:<22} {mae:>8.1f} {rmse:>8.1f} {r2:>8.3f}")

# ── בחירת הטוב ביותר (לפי MAE) ───────────────────────────────────
best_name = min(results, key=lambda n: results[n]['mae'])
best      = results[best_name]
print(f"\nהמודל הטוב ביותר: {best_name}")
print(f"  MAE : {best['mae']:.1f} ימים")
print(f"  RMSE: {best['rmse']:.1f} ימים")
print(f"  R²  : {best['r2']:.3f}")

# ── שמירה ────────────────────────────────────────────────────────
os.makedirs('models', exist_ok=True)
joblib.dump(best['pipe'], 'models/model.pkl')
print(f"\nהמודל נשמר: models/model.pkl")
