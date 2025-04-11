import requests
import pandas as pd

def fetch_data(symbol='AAPL', **kwargs):
    url = f'https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol={symbol}&interval=1min&apikey=YOUR_API_KEY'
    response = requests.get(url)
    data = response.json()
    df = pd.DataFrame.from_dict(data['Time Series (1min)'], orient='index')
    df.index = pd.to_datetime(df.index)
    df.columns = ['open', 'high', 'low', 'close', 'volume']
    df = df.astype(float)
    # Store result in XCom
    #kwargs['ti'].xcom_push(key='fetched_df', value=df.to_json())
    return df
    
def transform_data(**kwargs):
    df_json = kwargs['ti'].xcom_pull(key='fetched_df')
    df = pd.read_json(df_json)
    df = df.sort_index()
    df['moving_avg'] = df['close'].rolling(window=5).mean()
    df['anomaly'] = abs(df['close'] - df['moving_avg']) > 2 * df['close'].std()
    print(df.tail())  # For testing/logging purpose

print(fetch_data())