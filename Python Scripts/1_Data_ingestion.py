import pandas as pd
from sqlalchemy import create_engine
import os
import logging
import time

os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    filename='logs/data_ingestion.log',
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filemode="a"
)

engine = create_engine('sqlite:///inventory.db')

def ingest_data_in_chunks(file_path, table_name, engine, chunksize=100000):
    """Load large CSV into SQLite in chunks to prevent memory crash"""
    logging.info(f"Starting ingestion for {file_path} in chunks of {chunksize}")
    
    i = 0
    for chunk in pd.read_csv(file_path, chunksize=chunksize):
        if_exists_option = 'replace' if i == 0 else 'append'  # first chunk replaces, others append
        chunk.to_sql(table_name, con=engine, if_exists=if_exists_option, index=False)
        i += 1
        logging.info(f"Loaded chunk {i} for {file_path}")
    
    logging.info(f"Completed ingestion for {file_path}")

def load_raw_data():
    """Ingest every CSV file one by one into the database using chunks"""
    start = time.time()
    for file in os.listdir('data'):
        if file.endswith('.csv'):
            file_path = os.path.join('data', file)
            table_name = file[:-4]  # remove .csv
            ingest_data_in_chunks(file_path, table_name, engine)
    end_time = time.time()
    total_time = (end_time - start)/60
    logging.info("Ingestion Complete Successfully")
    logging.info(f"Total ingestion time: {total_time:.2f} minutes")

if __name__ == '__main__':
    load_raw_data()
