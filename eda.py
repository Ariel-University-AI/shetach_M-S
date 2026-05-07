import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# === טעינת הנתונים ===
df = pd.read_csv("data.csv")

# === המרת תאריכים ===
date_cols = ["בדיקת תאריך עדכון של לשרטוט", "סוף", "התחלה", "תאריך סיום צפוי (SLA)"]
for col in date_cols:
    df[col] = pd.to_datetime(df[col], errors="coerce")

# === חישוב משך בפועל ===
df["משך בפועל (ימים)"] = (df["סוף"] - df["התחלה"]).dt.days

# === המרת זמן עבודה משניות לשעות ===
df["Time Spent (שעות)"] = df["Σ Time Spent"] / 3600

# === בדיקת עמידה ב-SLA ===
df["חריגה SLA"] = df["משך בפועל (ימים)"] - df["SLA התחייבות (ימים)"]
df["עמידה ב-SLA"] = df["חריגה SLA"] <= 0

# === הדפסות בסיסיות ===
print("\n--- סטטיסטיקות משך בפועל ---")
print(df["משך בפועל (ימים)"].describe())

print("\n--- עמידה ב-SLA ---")
print(df["עמידה ב-SLA"].value_counts())

print("\n--- משך לפי סוג פרויקט ---")
print(df.groupby("Custom field (סוג פרויקט)")["משך בפועל (ימים)"].mean())

# === גרפים ===
plt.figure(figsize=(10,5))
sns.histplot(df["משך בפועל (ימים)"], kde=True)
plt.title("התפלגות משך פרויקט בפועל")
plt.show()

plt.figure(figsize=(10,5))
sns.boxplot(x="Custom field (סוג פרויקט)", y="משך בפועל (ימים)", data=df)
plt.xticks(rotation=45)
plt.title("משך פרויקט לפי סוג פרויקט")
plt.show()

plt.figure(figsize=(10,5))
sns.scatterplot(x="Time Spent (שעות)", y="משך בפועל (ימים)", data=df)
plt.title("קורלציה בין זמן עבודה לבין משך בפועל")
plt.show()