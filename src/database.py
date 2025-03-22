from sqlmodel import create_engine

# ref: https://sqlmodel.tiangolo.com/tutorial/create-db-and-table/#engine-echo
engine = create_engine("postgresql+psycopg2://user:password@127.0.0.1:5432/database", echo=True)