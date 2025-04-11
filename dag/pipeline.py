from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import requests
import pandas as pd

# === Your original functions ===
def fetch_data(symbol='AAPL', **kwargs):
    url = f'https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol={symbol}&interval=1min&apikey=YOUR_API_KEY'
    response = requests.get(url)
    data = response.json()
    df = pd.DataFrame.from_dict(data['Time Series (1min)'], orient='index')
    df.index = pd.to_datetime(df.index)
    df.columns = ['open', 'high', 'low', 'close', 'volume']
    df = df.astype(float)
    # Store result in XCom
    kwargs['ti'].xcom_push(key='fetched_df', value=df.to_json())
    
def transform_data(**kwargs):
    df_json = kwargs['ti'].xcom_pull(key='fetched_df')
    df = pd.read_json(df_json)
    df = df.sort_index()
    df['moving_avg'] = df['close'].rolling(window=5).mean()
    df['anomaly'] = abs(df['close'] - df['moving_avg']) > 2 * df['close'].std()
    print(df.tail())  # For testing/logging purpose

# === Airflow DAG setup ===
default_args = {
    'owner': 'ray',
    'retries': 1,
    'retry_delay': timedelta(minutes=2),
}

with DAG(
    dag_id='fetch_transform_stock_data',
    default_args=default_args,
    description='Fetch stock data and process anomalies',
    start_date=datetime(2025, 4, 10),
    schedule_interval='*/5 * * * *',  # every 5 minutes
    catchup=False
) as dag:

    task_fetch = PythonOperator(
        task_id='fetch_data',
        python_callable=fetch_data,
        provide_context=True
    )

    task_transform = PythonOperator(
        task_id='transform_data',
        python_callable=transform_data,
        provide_context=True
    )

    task_fetch >> task_transform