import requests
import pandas as pd

def fetch_data(symbol='AAPL'):
    url = f'https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol={symbol}&interval=1min&apikey=YOUR_API_KEY'
    response = requests.get(url)
    data = response.json()
    df = pd.DataFrame.from_dict(data['Time Series (1min)'], orient='index')
    df.index = pd.to_datetime(df.index)
    df.columns = ['open', 'high', 'low', 'close', 'volume']
    return df

def transform_data(df):
    df = df.sort_index()
    df = df.astype(float)
    df['moving_avg'] = df['close'].rolling(window=5).mean()
    df['anomaly'] = abs(df['close'] - df['moving_avg']) > 2 * df['close'].std()
    return df

dff = fetch_data()
print(dff)

print(transform_data(dff))