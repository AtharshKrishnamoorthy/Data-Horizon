from sqlalchemy import create_engine
from langchain_community.utilities import SQLDatabase

SQLALECHEMY_DB_URL = "mysql://root:root@127.0.0.1:3306/ecommerce_rag"

db_engine = create_engine(
    SQLALECHEMY_DB_URL,
    pool_pre_ping=True,
    pool_recycle=3600
)


db = SQLDatabase(db_engine, view_support=True, schema="ecommerce_rag")

