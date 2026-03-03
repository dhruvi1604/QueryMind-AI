import sys
sys.path.append('.')
from backend.llm import generate_sql

sql, safe, reason = generate_sql('What is the total revenue?')
print('SQL:', sql)
print('Safe:', safe)
print('Reason:', reason)