from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import requests
import pandas as pd

default_args = {
    'owner': 'airflow',
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

def fetch_data(symbol='AAPL', **context):
    url = f'https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol={symbol}&interval=1min&apikey=YOUR_API_KEY'
    response = requests.get(url)
    data = response.json()
    df = pd.DataFrame.from_dict(data['Time Series (1min)'], orient='index')
    df.index = pd.to_datetime(df.index)
    df.columns = ['open', 'high', 'low', 'close', 'volume']
    df.to_csv('/tmp/raw_data.csv')  # save it for next step
    return 'data fetched'

def transform_data(**context):
    df = pd.read_csv('/tmp/raw_data.csv', index_col=0, parse_dates=True)
    df = df.sort_index()
    df = df.astype(float)
    df['moving_avg'] = df['close'].rolling(window=5).mean()
    df['anomaly'] = abs(df['close'] - df['moving_avg']) > 2 * df['close'].std()
    df.to_csv('/tmp/transformed_data.csv')
    return 'data transformed'

with DAG(
    dag_id='fetch_transform_dag',
    default_args=default_args,
    description='Fetch and transform stock data every 10 minutes',
    schedule_interval='*/10 * * * *',  # every 10 minutes
    start_date=datetime(2025, 1, 1),
    catchup=False,
) as dag:

    fetch = PythonOperator(
        task_id='fetch_data',
        python_callable=fetch_data
    )

    transform = PythonOperator(
        task_id='transform_data',
        python_callable=transform_data
    )

    fetch >> transform  # set task order