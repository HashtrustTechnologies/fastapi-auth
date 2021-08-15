import os

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# SQLALCHEMY_DATABASE_URL = (
#     "postgresql://{dbuser}:{dbpassword}@{dbhost}:{dbport}/{dbname}".format(
#         dbport=os.environ.get("DB_PORT", "5432"),
#         dbhost=os.environ.get("DB_HOST", "db"),
#         dbname=os.environ.get("DB_NAME", "postgres"),
#         dbuser=os.environ.get("DB_USER", "postgres"),
#         dbpassword=os.environ.get("DB_PASSWORD", "postgres"),
#     )
# )

SQLALCHEMY_DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/main_db"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
