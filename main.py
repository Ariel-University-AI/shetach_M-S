import datetime

# --- הגדרת מבני נתונים ---
# מילון המייצג את המשקלים למודל רגרסיה לינארית פשוט (Mockup)
# המשקל מייצג את מספר הימים לדונם/יחידת גודל עבור כל סוג פרויקט
PROJECT_TYPE_WEIGHTS = {
    "מפה טופוגרפית": 0.5,  # חצי יום לכל יחידת גודל
    "מדידה להיתר": 1.2,    # 1.2 ימים לכל יחידת גודל
    "איתור תשתיות": 0.8,
    "חלוקה (פרצלציה)": 2.5
}

# חלוקת זמן משוערת בין שלבי הפרויקט (באחוזים מתוך סך הזמן)
STAGES_PERCENTAGE = {
    "עבודת שטח": 0.30,
    "עבודת חישוב": 0.15,
    "עבודת משרד": 0.40,
    "בקרה (QA)": 0.15
}

# --- פונקציות עיבוד וחישוב ---

def estimate_project_duration(project_type: str, project_size: float) -> int:
    """
    פונקציה המדמה את פעולת מודל הרגרסיה.
    מקבלת את סוג הפרויקט וגודלו, ומחזירה הערכה למספר הימים הנדרש.
    """
    if project_type not in PROJECT_TYPE_WEIGHTS:
        raise ValueError("סוג הפרויקט לא קיים במערכת")
        
    weight = PROJECT_TYPE_WEIGHTS[project_type]
    # חישוב: משקל * גודל + זמן התארגנות בסיסי (יומיים)
    estimated_days = (weight * project_size) + 2
    
    return int(round(estimated_days))

def calculate_target_dates(start_date: datetime.date, total_days: int) -> dict:
    """
    מחשבת את תאריכי היעד עבור כל אחד משלבי הפרויקט בהתאם לאחוזים.
    """
    stages_deadlines = {}
    current_date = start_date
    
    for stage, percentage in STAGES_PERCENTAGE.items():
        stage_days = int(round(total_days * percentage))
        # מינימום יום אחד לכל שלב
        stage_days = max(1, stage_days) 
        
        # חישוב תאריך סיום השלב 
        stage_deadline = current_date + datetime.timedelta(days=stage_days)
        stages_deadlines[stage] = stage_deadline
        current_date = stage_deadline
        
    # הדדליין הסופי של הפרויקט
    final_deadline = start_date + datetime.timedelta(days=total_days)
    
    return {
        "final_deadline": final_deadline,
        "stages": stages_deadlines
    }

# --- הדפסת תוצאה לדוגמה ---

def main():
    print("=== מערכת חיזוי לו\"ז פרויקטים ===")
    
    # נתוני קלט לדוגמה (מהמשתמש/מנהל הלקוח)
    sample_type = "מפה טופוגרפית"
    sample_size = 50.0  # לדוגמה, 50 דונם
    start_date = datetime.date.today()
    
    print(f"נתוני הפרויקט: סוג - '{sample_type}', גודל - {sample_size}")
    print(f"תאריך התחלה: {start_date.strftime('%d/%m/%Y')}\n")
    
    try:
        # 1. חיזוי משך הזמן הכולל
        total_days = estimate_project_duration(sample_type, sample_size)
        print(f"⌛ חיזוי המודל: הפרויקט יארך כ-{total_days} ימים.\n")
        
        # 2. בניית לוח הזמנים וחלוקה לשלבים
        schedule = calculate_target_dates(start_date, total_days)
        
        print(f"🎯 תאריך יעד סופי למסירה ללקוח: {schedule['final_deadline'].strftime('%d/%m/%Y')}\n")
        
        print("פירוט יעדים לפי שלבים למעקב והתראות:")
        for stage, deadline in schedule['stages'].items():
            print(f" - {stage}: סיום משוער עד ה- {deadline.strftime('%d/%m/%Y')}")
            
    except ValueError as e:
        print(f"שגיאה: {e}")

if __name__ == "__main__":
    main()
