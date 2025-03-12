import pandas as pd

def load_data(file_path):
    return pd.read_csv(file_path, thousands=',')

def clean_data(data):
    data = data.drop(['Buy Change', 'Sell Change'],axis=1)
    return data

def process_data(data):
    
    data['Buy'] = data['Buy'].str.split(' ').str[0].str.replace('.', '',regex=False).astype(float)
    data['Sell'] = data['Sell'].str.split(' ').str[0].str.replace('.', '',regex=False).astype(float)
    data['Spread'] = data['Sell'] - data['Buy']

    data['Brand'] = data['Brand'].str.strip().astype(str)
    data['Type'] = data['Type'].str.strip().astype(str)
    data['Date'] = pd.to_datetime(data['Date'], format='%d/%m/%Y %H:%M')
    return data

def save_data(data, file_path):
    data.to_csv(file_path, index=False)

def main():
    INPUT_PATH = "../data/gold_price.csv"
    OUTPUT_PATH = "../data/processed_gold_price.csv"
    data = load_data(INPUT_PATH)
    data = clean_data(data)


    data = process_data(data)
    save_data(data, OUTPUT_PATH)

if __name__ == '__main__':
    main()
