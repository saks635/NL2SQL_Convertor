# utils/helpers.py
import re

def format_prompt(question, schema):
    """Formats the schema and question into a stricter prompt for the LLM."""
    return f"""
Given the following SQL schema:
---
{schema}
---
Based on the schema, write a single, valid SQLite query to answer the following question: "{question}"

IMPORTANT: Your response must contain ONLY the SQL query and nothing else. Do not include any explanations, greetings, or markdown formatting.

SQL Query:
"""

def clean_sql(sql_text):
    """
    More robustly cleans the raw SQL output from the LLM.
    It finds the SQL statement and extracts it.
    """
    # Find the start of the SQL query (case-insensitive)
    select_match = re.search(r'SELECT.*?;', sql_text, re.IGNORECASE | re.DOTALL)
    
    if select_match:
        # Extract the matched SQL query
        sql_query = select_match.group(0)
        # Clean up whitespace
        return " ".join(sql_query.split()).strip()
    
    # Fallback for simple cases or if regex fails
    sql_text = re.sub(r"```sql|```", "", sql_text, flags=re.IGNORECASE)
    sql_text = " ".join(sql_text.split()).strip()
    if not sql_text.endswith(';'):
        sql_text += ';'
        
    return sql_text