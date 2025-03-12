import pandas as pd

def load_data(file_path):
    return pd.read_csv(file_path)

def clean_data(data):
    data = data.drop(columns=['Buy Change', 'Sell Change'], axis=1)
    return data

def save_data(data, file_path):
    data.to_csv(file_path, index=False)

def process_data(data):
    data['Date'] = pd.to_datetime(data['Date'], format='%d/%m/%Y %H:%M')
    data['Brand'] = data['Brand'].str.strip().astype(str)
    data['Type'] = data['Type'].str.strip().astype(str)
    data['Buy'] = data['Buy'].str.split().str[0].str.replace('.', '',regex=False).astype(float)
    data['Sell'] = data['Sell'].str.split().str[0].str.replace('.', '',regex=False).astype(float)
    data['Spread'] = data['Sell'] - data['Buy']
    return data

def main():
    INPUT_FILE = '../data/gold_price.csv'
    OUTPUT_FILE = '../data/processed_gold_price.csv'
    data = load_data(INPUT_FILE)
    data = clean_data(data)
    data = process_data(data)
    save_data(data, OUTPUT_FILE)


if __name__ == '__main__':
    main()
