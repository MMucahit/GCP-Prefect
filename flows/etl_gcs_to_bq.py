from pathlib import Path

import pandas as pd

from prefect import flow, task
from prefect_gcp.cloud_storage import GcsBucket
from prefect_gcp import GcpCredentials

@task(retries=3, log_prints=True)
def extract_from_gcs(color: str, year: int, month: int) -> Path:
    """Download trip data from GCS"""

    gcs_path = f'data/{color}/{color}_tripdata_{year}-{month:02}.parquet'
    gcs_block = GcsBucket.load('zoom-gcs')
    gcs_block.get_directory(from_path=gcs_path, local_path=f'./')

    return Path(gcs_path)

@task()
def transform(path: Path) -> pd.DataFrame:
    """Data cleaning example"""

    df = pd.read_parquet(path)
    
    print(f"pre: missing passenger count: {df['passenger_count'].isna().sum()}")
    
    df['passenger_count'].fillna(0, inplace=True)

    print(f"pre: missing passenger count: {df['passenger_count'].isna().sum()}")

    return df

@task()
def write_bq(df: pd.DataFrame) -> None:
    """Write DataFrame to Big Query"""

    gcp_credentials_block = GcpCredentials.load("zoom-gcp-creds")

    df.to_gbq(destination_table='dezoomcamp.nyc_taxi', 
              project_id='data-talks-club-390410', 
              credentials=gcp_credentials_block.get_credentials_from_service_account(),        
              chunksize=500_000, 
              if_exists='append')
    
    return

@flow()
def elt_gcs_to_bq(color: str, year: int, month: int):
    """Main ETL flow to load data into Big Query"""

    path = extract_from_gcs(color, year, month)
    df = transform(path)
    write_bq(df)

@flow()
def etl_parent_flow(months: list[int] = [1, 2, 3], year: int = 2021, color: str = 'yellow'):
    for month in months:
        elt_gcs_to_bq(color, year, month)   

if __name__ == '__main__':
    etl_parent_flow()