
import pandas as pd
import sqlite3

csv_file='amazon_review.csv'
sqlite_db='output.db'
table_name='output'

df=pd.read_csv(csv_file)
conn=sqlite3.connect(sqlite_db)
df.to_sql(table_name,conn,if_exists='replace',index=False)
conn.commit()
conn.close()
