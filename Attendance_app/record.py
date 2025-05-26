import pandas as pd
def get_record():
    try:
        
        file='attendance.xlsx'

        df=pd.read_excel(file,engine='openpyxl')
        records=df.to_dict(orient='records')
        return records
    except Exception as e:
        print(f"error{e}")
        return False
