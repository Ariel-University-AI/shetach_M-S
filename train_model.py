import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
import joblib
import os

# ── טעינה וניקוי ────────────────────────────────────────────────
df = pd.read_csv('data/dataset.csv')

df['סוף']    = pd.to_datetime(df['סוף'],    errors='coerce')
df['התחלה']  = pd.to_datetime(df['התחלה'],  errors='coerce')
df['משך בפועל (ימים)'] = (df['סוף'] - df['התחלה']).dt.days

FEATURES = [
    'Custom field (סוג פרויקט)',
    'Custom field (תשומות - משרד)',
    'Custom field (תשומות - שטח)',
    'SLA התחייבות (ימים)',
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
]

preprocessor = ColumnTransformer([
    ('cat', OneHotEncoder(handle_unknown='ignore'), CAT_COLS),
    ('num', StandardScaler(),                       NUM_COLS),
])

pipeline = Pipeline([
    ('preprocessor', preprocessor),
    ('model', RandomForestRegressor(
        n_estimators=200,
        max_depth=10,
        random_state=42,
    )),
])

# ── אימון ────────────────────────────────────────────────────────
pipeline.fit(X_train, y_train)

# ── הערכה ────────────────────────────────────────────────────────
y_pred = pipeline.predict(X_test)
mae = mean_absolute_error(y_test, y_pred)
r2  = r2_score(y_test, y_pred)

print(f"\nתוצאות הערכה (test set):")
print(f"  MAE  (שגיאה ממוצעת בימים): {mae:.1f}")
print(f"  R²   (דיוק המודל 0-1):     {r2:.3f}")

# ── שמירה ────────────────────────────────────────────────────────
os.makedirs('models', exist_ok=True)
joblib.dump(pipeline, 'models/model.pkl')
print("\nהמודל נשמר: models/model.pkl")
