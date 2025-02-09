import os
from dotenv import load_dotenv
from langchain_community.utilities import SQLDatabase
from langchain.chains.sql_database.query import create_sql_query_chain
from langchain_groq import ChatGroq
from sqlalchemy import create_engine
import pandas as pd
from conn import db,db_engine


load_dotenv()

def setup_llm(api_key = os.getenv("GROQ_API_KEY")):
   llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=api_key,
    temperature=0
   )
   return llm

def clean_sql_with_llm(response: str, llm=setup_llm()):
    prompt = f"""Extract and return ONLY the SQL query from this text, without any additional text, quotes, or markdown:

Input text:
{response}

Return only the clean SQL query that can be executed directly. Do not include any explanations, markdown formatting, or additional text."""

    cleaned_response = llm.invoke(prompt).content
    return cleaned_response.strip()

def get_sql_response(input: str, llm=setup_llm(), db=db, db_engine=db_engine):
    chain = create_sql_query_chain(llm, db)
    
    response = chain.invoke({"question": input})
    print("Generated SQL Query:", response)
    
    try:

        sql_query = clean_sql_with_llm(response, llm)
        print("\nCleaned SQL Query:", sql_query)
        
 
        data = pd.read_sql(sql_query, db_engine)
        print("\nQuery Results:")
        print(data)
        
        return data, sql_query
        
    except Exception as e:
        print(f"Error processing SQL query: {e}")
        print(f"Raw response: {response}")
        return None, None