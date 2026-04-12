# Save as fix_csv.py
import pandas as pd
import os

if os.path.exists('health_log.csv'):
    try:
        df = pd.read_csv('health_log.csv')
        if df.empty:
            os.remove('health_log.csv')
            print("🗑️ Deleted empty CSV")
    except:
        os.remove('health_log.csv')
        print("🗑️ Deleted broken CSV")

print("✅ Ready - run streamlit now")