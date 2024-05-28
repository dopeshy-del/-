import requests
import streamlit as st
from dateutil.parser import parse
from datetime import datetime
from cachetools import TTLCache, cached

CACHE_TTL = 86400  # Установка времени жизни кэша на 24 часа
cache = TTLCache(maxsize=100, ttl=CACHE_TTL)       # Создание объекта кэша с использованием TTLCache из библиотеки cachetools

API_KEY = "1062e495e1b561b9d4b04352"                                     # Ключ API для доступа к внешнему сервису курсов валют
BASE_URL = f"https://v6.exchangerate-api.com/v6/{API_KEY}/"

@cached(cache)
def fetch_exchange_rates(src):
    url = f"{BASE_URL}latest/{src}"
    response = requests.get(url)
    
    if response.status_code != 200:
        raise ValueError("Ошибка при получении курсов валют")
    
    data = response.json()
    print("Ответ API:", data)  # Добавилен отладочный вывод
    
    if data.get("result") != "success":
        raise ValueError(f"Ошибка при получении курсов валют: {data.get('error-type', 'Unknown error')}")
    
    if "conversion_rates" not in data:
        raise ValueError(f"Некорректный ответ от API: отсутствует ключ 'conversion_rates'. Полный ответ: {data}")
    
    last_updated_datetime = parse(data["time_last_update_utc"]).replace(tzinfo=None)
    exchange_rates = data["conversion_rates"]
    return last_updated_datetime, exchange_rates

def convert_currency(src, dst, amount):
    last_updated_datetime, exchange_rates = fetch_exchange_rates(src)
    
    if dst not in exchange_rates:
        raise ValueError(f"Некорректный ответ от API: отсутствует курс для валюты {dst}")
    
    if src not in exchange_rates:
        raise ValueError(f"Некорректный ответ от API: отсутствует курс для валюты {src}")
    
    print("Проверка пройдена для исходной и целевой валюты")
    
    return last_updated_datetime, exchange_rates[dst] * amount

def get_all_currencies():
    url = f"{BASE_URL}codes"
    response = requests.get(url)
    
    if response.status_code != 200:
        raise ValueError("Ошибка при получении списка валют")
    
    data = response.json()
    
    if data.get("result") != "success":
        raise ValueError(f"Ошибка при получении списка валют: {data.get('error-type', 'Unknown error')}")
    
    currency_dict = {f"{code} - {name}": code for code, name in data.get("supported_codes", [])}
    # Добавлен перевод названий валют на русский
    russian_names = {
        "USD": "Доллар",
        "GBP": "Фунт стерлинга",
        "EUR": "Евро",
        "RUB": "Рубль",
        "AED": "Дирхам"
    }
    russian_currency_dict = {f"{russian_names.get(code, code)} - {name}": code for name, code in currency_dict.items()}
    return russian_currency_dict

def search_currencies(search_query):
    all_currencies = get_all_currencies()
    filtered_currencies = {key: value for key, value in all_currencies.items() if search_query.lower() in key.lower()}
    return filtered_currencies

def main():
    st.title("Конвертер валют")

    st.markdown("""
        <style>
        .big-font {
            font-size:30px !important;
        }
        .result-box {
            background-color: #f0f0f0;
            padding: 20px;
            border-radius: 10px;
            margin-top: 20px;
        }
        </style>
        """, unsafe_allow_html=True)

    tabs = st.sidebar.radio("Выберите вкладку", ["Популярные валюты", "Все валюты"])

    if tabs == "Популярные валюты":
        st.sidebar.subheader("Популярные валюты")
        popular_currencies = {
            "Доллар - USD": "USD",
            "Фунт стерлинга - GBP": "GBP",
            "Евро - EUR": "EUR",
            "Рубль - RUB": "RUB",
            "Дирхам - AED": "AED"
        }
        source_currency_label = st.sidebar.selectbox("Валюта из которой переводят", list(popular_currencies.keys()), index=0)
        destination_currency_label = st.sidebar.selectbox("Валюта в которую переводят", list(popular_currencies.keys()), index=1)

        source_currency = popular_currencies[source_currency_label]
        destination_currency = popular_currencies[destination_currency_label]
    else:
        st.sidebar.subheader("Поиск валют")
        search_query_source = st.sidebar.text_input("Введите название валюты для поиска (исходная валюта)")
        search_query_dest = st.sidebar.text_input("Введите название валюты для поиска (целевая валюта)")
        filtered_source_currencies = search_currencies(search_query_source)
        filtered_dest_currencies = search_currencies(search_query_dest)
        
        source_currency_label = st.sidebar.selectbox("Исходная валюта", list(filtered_source_currencies.keys()), index=0)
        destination_currency_label = st.sidebar.selectbox("Целевая валюта", list(filtered_dest_currencies.keys()), index=0)

        source_currency = filtered_source_currencies[source_currency_label]
        destination_currency = filtered_dest_currencies[destination_currency_label]

    amount = st.number_input("Количество", value=1, step=1, format="%d", min_value=1)
    convert_button = st.button("Конвертировать")

    if convert_button:
        try:
            with st.spinner('Загрузка данных...'):
                last_updated_datetime, converted_amount = convert_currency(source_currency, destination_currency, amount)
            st.markdown(f"""
                <div class="result-box">
                    <p class="big-font">{amount} {source_currency} = {converted_amount:.2f} {destination_currency}</p>
                    <p>Дата последнего обновления курсов: {last_updated_datetime}</p>
                </div>
                """, unsafe_allow_html=True)
        except ValueError as e:
            st.error(f"Ошибка: {e}")
        except Exception as e:
            st.error(f"Произошла непредвиденная ошибка: {e}")

if __name__ == "__main__":
    main()