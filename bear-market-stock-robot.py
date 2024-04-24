import threading
import logging
import csv
import os, sys
import time
import schedule
import random
from datetime import datetime, timedelta, date
from datetime import time as time2
import alpaca_trade_api as tradeapi
import pytz
import talib
import yfinance as yf
import sqlalchemy
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import SQLAlchemyError

# import warnings     # comment out this line to utilize warnings.filterwarnings

# warnings.filterwarnings('ignore')     # comment out this line to display more error messages.

# Load environment variables for Alpaca API
APIKEYID = os.getenv('APCA_API_KEY_ID')
APISECRETKEY = os.getenv('APCA_API_SECRET_KEY')
APIBASEURL = os.getenv('APCA_API_BASE_URL')

# Initialize the Alpaca API
api = tradeapi.REST(APIKEYID, APISECRETKEY, APIBASEURL)

global stocks_to_buy, today_date, today_datetime, csv_writer, csv_filename, fieldnames, price_changes, end_time

# the below will print the list of stocks to buy and their prices when True.
PRINT_STOCKS_TO_BUY = False  # keep this as False for the robot to work faster.

# the below will print the Robot's personal buy and sell database when True.
PRINT_ROBOT_STORED_BUY_AND_SELL_LIST_DATABASE = True  # keep this as False for the robot to work faster.

# the below will print the stocks to sell when True.
PRINT_DATABASE = True  # keep this as True to view the stocks to sell. False for a faster robot.

# the below will print the Average True Range of stock prices when True.
DEBUG = False  # this robot works faster when this is False.

# the below Permission variable will allow all owned position shares to sell today when True on the first run.
# Default value POSITION_DATES_AS_YESTERDAY_OPTION = False
POSITION_DATES_AS_YESTERDAY_OPTION = False  # keep this as False to not change the dates of owned stocks

# set the timezone to Eastern
eastern = pytz.timezone('US/Eastern')

# Dictionary to maintain previous prices and price increase and price decrease counts
stock_data = {}

# Dictionary to store previous prices for symbols
previous_prices = {}

end_time = 0  # Initialize end_time as a global variable

# Define the API datetime format
api_time_format = '%Y-%m-%dT%H:%M:%S.%f-04:00'

# the below variable was recommended by Artificial Intelligence
buy_sell_lock = threading.Lock()

logging.basicConfig(filename='trading-bot-program-logging-messages.txt', level=logging.INFO)

# Define the CSV file and fieldnames
csv_filename = 'log-file-of-buy-and-sell-signals.csv'
fieldnames = ['Date', 'Buy', 'Sell', 'Quantity', 'Symbol', 'Price Per Share']

# Open the CSV file for writing and set up a CSV writer
with open(csv_filename, mode='w', newline='') as csv_file:
    csv_writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

    # Write the header row
    csv_writer.writeheader()

# Define the Database Models
# Newer Data Base Model code below
Base = sqlalchemy.orm.declarative_base()


class TradeHistory(Base):
    __tablename__ = 'trade_history'
    id = Column(Integer, primary_key=True)
    symbol = Column(String)
    action = Column(String)  # 'buy' or 'sell'
    quantity = Column(Integer)
    price = Column(Float)
    date = Column(String)
    # the above date is string data format in the database


class Position(Base):
    __tablename__ = 'positions'
    symbol = Column(String, primary_key=True)
    quantity = Column(Integer)
    avg_price = Column(Float)
    purchase_date = Column(String)
    # the above date is string data format in the database


# Initialize SQLAlchemy
engine = create_engine('sqlite:///trading_bot.db')
Session = sessionmaker(bind=engine)
session = Session()

# Create tables if not exist
Base.metadata.create_all(engine)


def stop_if_stock_market_is_closed():
    # Check if the current time is within the stock market hours
    # Set the stock market open and close times
    market_open_time = time2(9, 30)
    market_close_time = time2(16, 0)

    while True:
        # Get the current time in Eastern Time
        eastern = pytz.timezone('US/Eastern')
        now = datetime.now(eastern)
        current_time = now.time()

        # Check if the current time is within market hours
        if now.weekday() <= 4 and market_open_time <= current_time <= market_close_time:
            break

        print("\n")
        print('''

            2023 Edition of the Bear Market Advanced Stock Trading Robot 
           _____   __                   __             ____            __            __ 
          / ___/  / /_  ____   _____   / /__          / __ \  ____    / /_   ____   / /_
          \__ \  / __/ / __ \ / ___/  / //_/         / /_/ / / __ \  / __ \ / __ \ / __/
         ___/ / / /_  / /_/ // /__   / ,<           / _, _/ / /_/ / / /_/ // /_/ // /_  
        /____/  \__/  \____/ \___/  /_/|_|         /_/ |_|  \____/ /_.___/ \____/ \__/  

                                                  https://github.com/CodeProSpecialist

                       Featuring an An Accelerated Database Engine with Python 3 SQLAlchemy  

         ''')
        print(f'Current date & time (Eastern Time): {now.strftime("%A, %B %d, %Y, %I:%M:%S %p")}')
        print("Stockbot only works Monday through Friday: 9:30 am - 4:00 pm Eastern Time.")
        print("Waiting until Stock Market Hours to begin the Stockbot Trading Program.")
        print("\n")
        print("\n")
        time.sleep(60)  # Sleep for 1 minute and check again. Keep this under the p in print.


def print_database_tables():
    if PRINT_DATABASE:
        positions = api.list_positions()
        show_price_percentage_change = True  # set to true to view % price changes

        # Print TradeHistory table
        print("\nTrade History In This Robot's Database:")
        print("\n")
        print("Stock | Buy or Sell | Quantity | Avg. Price | Date ")
        print("\n")

        for record in session.query(TradeHistory).all():
            print(f"{record.symbol} | {record.action} | {record.quantity} | {record.price:.2f} | {record.date}")

        print("----------------------------------------------------------------")
        # Print Position table
        print("\n")
        print("Positions in the Database To Sell 1 or More Days After the Date Shown:")
        print("\n")
        print("Stock | Quantity | Avg. Price | Date or The 1st Day This Robot Began Working ")
        print("\n")
        for record in session.query(Position).all():
            symbol, quantity, avg_price, purchase_date = record.symbol, record.quantity, record.avg_price, record.purchase_date

            # Format purchase_date to show 0 digits after the decimal point
            purchase_date_str = purchase_date  # this is already correct string data format

            # Calculate percentage change if show_price_percentage_change is True
            if show_price_percentage_change:
                current_price = get_current_price(symbol)  # Replace with your actual method to get current price
                percentage_change = ((current_price - avg_price) / avg_price) * 100
                print(
                    f"{symbol} | {quantity} | {avg_price:.2f} | {purchase_date_str} | Price Change: {percentage_change:.2f}%")
            else:
                print(f"{symbol} | {quantity} | {avg_price:.2f} | {purchase_date_str}")
        print("\n")


def get_stocks_to_trade():
    try:
        with open('bear-short-ETF-funds-buy-list.txt', 'r') as file:
            stock_symbols = [line.strip() for line in file.readlines()]

        if not stock_symbols:  # keep this under the w in with
            print("\n")
            print(
                "********************************************************************************************************")
            print(
                "*   Error: The file bear-short-ETF-funds-buy-list.txt doesn't contain any stock symbols.   *")
            print(
                "*   This Robot does not work until you place stock symbols in the file named:                          *")
            print(
                "*       bear-short-ETF-funds-buy-list.txt                                                  *")
            print(
                "********************************************************************************************************")
            print("\n")

        return stock_symbols  # keep this under the i in if

    except FileNotFoundError:  # keep this under the t in try
        print("\n")
        print("****************************************************************************")
        print("*   Error: File not found: bear-short-ETF-funds-buy-list.txt   *")
        print("****************************************************************************")
        print("\n")
        return []  # keep this under the p in print


def remove_symbol_from_trade_list(symbol):
    with open('bear-short-ETF-funds-buy-list.txt', 'r') as file:
        lines = file.readlines()
    with open('bear-short-ETF-funds-buy-list.txt', 'w') as file:
        for line in lines:
            if line.strip() != symbol:
                file.write(line)  # keep this under the i in line


def get_opening_price(symbol):
    stock_data = yf.Ticker(symbol)
    # Fetch the stock data for today and get the opening price
    return round(stock_data.history(period="1d")["Open"].iloc[0], 4)


def get_current_price(symbol):
    stock_data = yf.Ticker(symbol)
    return round(stock_data.history(period='1d')['Close'].iloc[0], 4)


def get_atr_high_price(symbol):
    atr_value = get_average_true_range(symbol)
    current_price = get_current_price(symbol)
    return round(current_price + 0.40 * atr_value, 4)


def get_atr_low_price(symbol):
    atr_value = get_average_true_range(symbol)
    current_price = get_current_price(symbol)
    return round(current_price - 0.10 * atr_value, 4)


def get_average_true_range(symbol):
    ticker = yf.Ticker(symbol)
    data = ticker.history(period='30d')
    atr = talib.ATR(data['High'].values, data['Low'].values, data['Close'].values, timeperiod=22)
    return atr[-1]


def status_printer_buy_stocks():
    print(f"\rBuy stocks function is working correctly right now. Checking stocks to buy.....", end='', flush=True)
    # After the loop, print a newline character to move to the next line with the print command below.
    print()  # keep this under the s in status_printer_buy_stocks()


def status_printer_sell_stocks():
    print(f"\rSell stocks function is working correctly right now. Checking stocks to sell.....", end='', flush=True)
    # After the loop, print a newline character to move to the next line with the print command below.
    print()  # keep this under the s in status_printer_sell_stocks()


# Function to calculate MACD, RSI, and Volume
def calculate_technical_indicators(symbol, lookback_days=90):
    stock_data = yf.Ticker(symbol)
    historical_data = stock_data.history(period=f'{lookback_days}d')

    # Calculate MACD
    short_window = 12
    long_window = 26
    signal_window = 9
    historical_data['macd'], historical_data['signal'], _ = talib.MACD(historical_data['Close'],
                                                                       fastperiod=short_window,
                                                                       slowperiod=long_window,
                                                                       signalperiod=signal_window)

    # Calculate RSI
    rsi_period = 14
    historical_data['rsi'] = talib.RSI(historical_data['Close'], timeperiod=rsi_period)

    # Calculate Volume
    historical_data['volume'] = historical_data['Volume']

    return historical_data


# Function to print technical indicators
def print_technical_indicators(symbol, historical_data):
    print("")
    print(f"\nTechnical Indicators for {symbol}:\n")
    print(historical_data[['Close', 'macd', 'signal', 'rsi', 'volume']].tail())
    print("")


def calculate_cash_on_hand():
    # Calculate the total cash on hand
    cash_available = round(float(api.get_account().cash), 2)
    return cash_available


def calculate_total_symbols(stocks_to_buy):
    # Calculate the total number of symbols in "stocks_to_buy"
    total_symbols = len(stocks_to_buy)
    return total_symbols


def allocate_cash_equally(cash_available, total_symbols):
    # Make the total quantity of stocks_to_buy as close to $400 as possible and buy no more than $400 per stock symbol
    max_allocation_per_symbol = 400  # how much cash to spend per stock purchase
    allocation_per_symbol = min(max_allocation_per_symbol, cash_available) / total_symbols
    return allocation_per_symbol


def get_previous_price(symbol):
    # Check if the symbol has a previous price
    if symbol in previous_prices:
        return previous_prices[symbol]
    else:
        # If no previous price is available, fetch the current price and use it as the previous price
        current_price = get_current_price(symbol)  # Fetch the current price
        previous_prices[symbol] = current_price  # Set it as the previous price
        print(
            f"No previous price for {symbol} was found. Using the current price as the previous price: {current_price}")
        return current_price


# Function to update previous prices
def update_previous_price(symbol, current_price):
    previous_prices[symbol] = current_price


def run_schedule():
    while not end_time_reached():
        schedule.run_pending()
        time.sleep(1)


def track_price_changes(symbol):
    current_price = get_current_price(symbol)
    previous_price = get_previous_price(symbol)

    print("")
    # Print the values of the technical indicators
    print_technical_indicators(symbol, calculate_technical_indicators(symbol))
    print("")

    if current_price > previous_price:
        price_changes[symbol]['increased'] += 1
        print(f"{symbol} price just increased | current price: {current_price}")
        time.sleep(2)
    elif current_price < previous_price:
        price_changes[symbol]['decreased'] += 1
        print(f"{symbol} price just decreased | current price: {current_price}")
        time.sleep(2)
    else:
        print(f"{symbol} price has not changed | current price: {current_price}")
        time.sleep(2)
    time.sleep(1)  # Wait 1 - 3 seconds per price check


def end_time_reached():
    return time.time() >= end_time


def buy_stocks(bought_stocks, stocks_to_buy, buy_sell_lock):
    stocks_to_remove = []
    global start_time, end_time, original_start_time, price_changes, symbol, buy_stock_green_light

    buy_stock_green_light = 0  # Initialize the global variable

    extracted_date_from_today_date = datetime.today().date()
    today_date_str = extracted_date_from_today_date.strftime("%Y-%m-%d")

    now = datetime.now(pytz.timezone('US/Eastern'))
    current_time_str = now.strftime("Eastern Time | %I:%M:%S %p | %m-%d-%Y |")

    # debugging code below to run the robot at different times
    # start_trading_time = datetime.now(pytz.timezone('US/Eastern')).replace(hour=5, minute=30, second=0, microsecond=0)

    # Define the target time as 2:57pm Eastern Time to begin looking for bear stocks to buy near the market closing time.
    start_trading_time = datetime.now(pytz.timezone('US/Eastern')).replace(hour=14, minute=57, second=0, microsecond=0)

    # print("datetime.now as compared to start_trading_time: ",datetime.now(pytz.timezone('US/Eastern')))     # uncomment this line to debug the code
    # print("start_trading_time to start buying stocks: ",start_trading_time)      # uncomment this line to debug the code

    # Check if the current time is before the start trading time
    if datetime.now(pytz.timezone('US/Eastern')) < start_trading_time:
        return  # Exit the function if the current time is before start_trading_time

    # Define the start_time variable
    start_time = time.time()

    # Store the original start_time for error handling
    original_start_time = start_time

    # below is the debugging end_time of 60 seconds to look for errors.
    #end_time = start_time + 60  # 60 seconds

    # Calculate the end_time based on the start_time
    # we need to select a time out of the 6.5 hour stock market trading day
    # to evaluate stock prices before buying stocks.
    # The most successful settings are to buy if price increases 3 times within 3 minutes
    # when using MACD, RSI, and VOLUME conditions to buy stocks at the correct times.
    # ( buying stocks after 9:30am Eastern time )
    end_time = start_time + 3 * 60  # 3 minutes multiplied by 60 seconds per minute

    # Define the target time as 15:56 Eastern Time ( to stop the buy_stocks function )
    target_time = datetime.now(pytz.timezone('US/Eastern')).replace(hour=15, minute=56, second=0, microsecond=0)

    # print("datetime.now as compared to target_time: ",datetime.now(pytz.timezone('US/Eastern')))     # uncomment this line to debug the code
    # print("target_time to stop buying stocks: ",target_time)      # uncomment this line to debug the code

    # Check if the current time is before the target time
    # Exit the buy_stocks function if the current time is after target_time
    if datetime.now(pytz.timezone('US/Eastern')) > target_time:
        print("")
        print("Returning and Exiting from the Buy Stocks function.")
        print("")
        return
    else:
        print("")
        print(" Continuing with the Buy Stocks function. ")
        print("")

    # Initialize the price_changes dictionary outside the loop
    # Define a dictionary to keep track of price changes for each symbol
    price_changes = {symbol: {'increased': 0, 'decreased': 0} for symbol in stocks_to_buy}

    try:
        while not end_time_reached():
            # Print total price increases per stock symbol
            for symbol in stocks_to_buy:
                cash_available = calculate_cash_on_hand()
                total_symbols = calculate_total_symbols(stocks_to_buy)
                allocation_per_symbol = allocate_cash_equally(cash_available, total_symbols)

                current_price = get_current_price(symbol)

                # Use the calculated allocation for all stocks
                qty_of_one_stock = int(allocation_per_symbol / current_price)

                # Schedule the task only once (right here within for symbol in stocks to buy)
                if not hasattr(buy_stocks, 'scheduled_task'):
                    buy_stocks.scheduled_task = schedule.every(1).seconds.do(track_price_changes, symbol)

                    # Start the background thread to run the schedule
                    schedule_thread = threading.Thread(target=run_schedule)
                    schedule_thread.start()

                # Update the dictionary to keep track of price changes for each symbol
                # Assuming track_price_changes returns 'increase' or 'decrease'
                change_type = track_price_changes(symbol)
                if change_type == 'increase':
                    price_changes[symbol]['increased'] += 1
                elif change_type == 'decrease':
                    price_changes[symbol]['decreased'] += 1

                print("")
                print(f"Total Price Increases for {symbol}: {price_changes[symbol]['increased']}")
                print(f"Total Price Decreases for {symbol}: {price_changes[symbol]['decreased']}")
                print("")

                # I might not need the extra sleep command below
                # keep the below time.sleep(1) below the s in "for symbol"
                time.sleep(2)   # wait 1.7 to 3 seconds to not move too fast for the stock price data rate limit.

        # Print overall total price increases and decreases after reaching end_time_reached()
        if end_time_reached():
            for symbol in stocks_to_buy:
                cash_available = calculate_cash_on_hand()
                total_symbols = calculate_total_symbols(stocks_to_buy)
                allocation_per_symbol = allocate_cash_equally(cash_available, total_symbols)

                current_price = get_current_price(symbol)

                # Use the calculated allocation for all stocks
                qty_of_one_stock = int(allocation_per_symbol / current_price)

                total_cost_for_qty = current_price * qty_of_one_stock

                # Print some debugging information
                print("")
                status_printer_buy_stocks()
                print("")
                print(f"Symbol: {symbol}")
                print(f"Current Price: {current_price}")
                print(f"Qty of One Stock: {qty_of_one_stock}")
                print(f"Total Cost for Qty: {total_cost_for_qty}")
                print("")
                print(f"Cash Available: {cash_available}")
                print("")
                print(f"Increased: {price_changes[symbol]['increased']}")
                print(f"Decreased: {price_changes[symbol]['decreased']}")
                print("")
                print(f"End Time Reached for waiting 30 seconds: {end_time_reached()}")
                print("")

                total_increases = price_changes[symbol]['increased']
                total_decreases = price_changes[symbol]['decreased']
                print("")
                print(f"Total Price Increases for {symbol}: {total_increases}")
                print(f"Total Price Decreases for {symbol}: {total_decreases}")
                print("")

                overall_total_increases = sum(price_changes[symbol]['increased'] for symbol in stocks_to_buy)
                overall_total_decreases = sum(price_changes[symbol]['decreased'] for symbol in stocks_to_buy)
                print("")
                print(f"Overall Total Price Increases: {overall_total_increases}")
                print(f"Overall Total Price Decreases: {overall_total_decreases}")
                print("")

                historical_data = calculate_technical_indicators(symbol, lookback_days=90)
                macd_value = historical_data['macd'].iloc[-1]
                rsi_value = historical_data['rsi'].iloc[-1]
                volume_value = historical_data['volume'].iloc[-1]

                print(f"MACD: {macd_value}")
                print(f"RSI: {rsi_value}")
                print(f"Volume: {volume_value}")
                print("")

                # Add conditions based on your chosen values for MACD, RSI, and Volume
                # Add conditions based on your specified values for MACD, RSI, and Volume
                favorable_macd_condition = (historical_data['signal'].iloc[-1] > 0.15)  # MACD signal is greater than 0.15
                favorable_rsi_condition = (historical_data['rsi'].iloc[-1] > 25)  # RSI is greater than 25 ( weak bear RSI )
                # Favorable volume is greater than 15% less than the mean or more volume than 85% average volume.
                favorable_volume_condition = (historical_data['volume'].iloc[-1] > 0.85 * historical_data['volume'].mean())

                # THE BELOW PYTHON CODE WILL PURCHASE STOCKS
                # AND IT WORKS CORRECTLY WHEN THE PRICE INCREASES ENOUGH TIMES.
                # The most successful settings are to buy if price increases 3 times within 3 minutes
                # when using MACD, RSI, and VOLUME conditions to buy stocks at the correct times.
                if (cash_available >= total_cost_for_qty and
                        price_changes[symbol]['increased'] >= 3 and
                        price_changes[symbol]['increased'] > price_changes[symbol]['decreased'] and
                        favorable_macd_condition and favorable_rsi_condition and favorable_volume_condition):
                    if qty_of_one_stock > 0:  # Add this condition to check if qty_of_one_stock is greater than 0
                        print("")
                        print(
                            f" ******** Buying stocks for {symbol}... "
                            f"************************************************************* ")
                        print("")
                        print_technical_indicators(symbol, calculate_technical_indicators(symbol))
                        print("")
                        # Convert symbol from BRK-B to BRK.B if necessary
                        symbol = symbol.replace('-', '.')
                        api.submit_order(symbol=symbol, qty=qty_of_one_stock, side='buy', type='market',
                                         time_in_force='day')

                        print("")
                        print(f" {current_time_str} , Bought {qty_of_one_stock} shares of {symbol} at {current_price}")
                        print("")
                        with open(csv_filename, mode='a', newline='') as csv_file:
                            csv_writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
                            csv_writer.writerow(
                                {'Date': current_time_str, 'Buy': 'Buy', 'Quantity': qty_of_one_stock, 'Symbol': symbol,
                                 'Price Per Share': current_price})
                        # keep the line below under the w in with open
                        stocks_to_remove.append((symbol, current_price, today_date_str))  # Append tuple.
                        # the database requires the datetime date format from today_date
                        # this append tuple will provide the date=date and the purchase_date = date
                        # in the correct datetime format for the database. This is the date
                        # in the below "with buy_sell_lock:" code block.
                        buy_stock_green_light = 1  # Set the variable to 1 in the buy condition

                    # the below else needs to be under the "I" in if qty_of_one_stock
                    else:
                        print("")
                        print("Price increases are favorable to buy stocks. Quantity of One Stock is 0. Not buying "
                              "stocks right now. Perhaps we need more cash before buying. ")
                        print("")
                        buy_stock_green_light = 0  # Set the variable to 0 in the not buying condition

                    # keep the below else under the "if" that is above the else
                else:
                    print("")
                    print("\nNot buying stocks based on the technical indicators: MACD, RSI, VOLUME, or based on price decreases. ")
                    print("")
                    print_technical_indicators(symbol, calculate_technical_indicators(symbol))
                    print("")

                time.sleep(2)    # keep this under the "if" in "if cash available"

            # I might not need the extra sleep command below
            # keep the below time.sleep(1) below the f in "for symbol"
            time.sleep(2)    # wait 1.7 to 3 seconds to not move too fast for the stock price data rate limit.

        time.sleep(2)    # keep this under the i in "if end_time_reached". this stops after checking each stock price

    except Exception as e:  # keep this under the t in "try:"
        # Handle the exception (e.g., log the error)
        print(f"An error occurred: {str(e)}")  # keep this under the p in except
        # Restart the schedule_thread with the original start_time to prevent progress loss
        start_time = original_start_time  # keep this under the p in print
        end_time = start_time + 102 * 60
        schedule_thread = threading.Thread(target=run_schedule)
        schedule_thread.start()

    try:  # keep this under the b in "buy_stocks"
        with buy_sell_lock:
            for symbol, price, date in stocks_to_remove:
                bought_stocks[symbol] = (round(price, 4), date)
                stocks_to_buy.remove(symbol)
                remove_symbol_from_trade_list(symbol)
                trade_history = TradeHistory(symbol=symbol, action='buy', quantity=qty_of_one_stock, price=price,
                                             date=date)  # the database requires the string date format
                session.add(trade_history)
                db_position = Position(symbol=symbol, quantity=qty_of_one_stock, avg_price=price,
                                       purchase_date=date)  # the database requires the string date format
                session.add(db_position)

            session.commit()
            refresh_after_buy()

            # Get account information
            account_info = api.get_account()  # keep this below time.sleep

            # Check day trade count
            day_trade_count = account_info.daytrade_count

            # keep the if day_trade_count below the "q" in qty_of_one_stock
            if buy_stock_green_light == 1 and day_trade_count < 3:
                print("")
                print("Waiting 2 minutes before placing a trailing stop sell order.....")
                print("")
                time.sleep(120)  # wait 120 seconds for buy order to process.

                stop_order_id = place_trailing_stop_sell_order(symbol, qty_of_one_stock, current_price)
                # keep the below "if" below the "a" in day_trade_count
                if stop_order_id:
                    print(f"Trailing stop sell order placed for {symbol} with ID: {stop_order_id}")
                    print("")
                else:
                    print(f"Failed to place trailing stop sell order for {symbol}")
                    print("")

    except SQLAlchemyError as e:  # keep this under the t in "try"
        session.rollback()  # Roll back the transaction on error
        # Handle the error or log it


def refresh_after_buy():
    global stocks_to_buy, bought_stocks
    time.sleep(2)
    stocks_to_buy = get_stocks_to_trade()
    bought_stocks = update_bought_stocks_from_api()



# Function to place trailing stop sell order
def place_trailing_stop_sell_order(symbol, qty_of_one_stock, current_price):
    try:
        stop_loss_percent = 1.0  # You can adjust this percentage based on your strategy
        stop_loss_price = current_price * (1 - stop_loss_percent / 100)

        stop_order = api.submit_order(
            symbol=symbol,
            qty=qty_of_one_stock,
            side='sell',
            type='trailing_stop',
            trail_percent=stop_loss_percent,
            time_in_force='gtc'  # 'gtc' or 'day'
        )

        print(f"Placed trailing stop sell order for {qty_of_one_stock} shares of {symbol} at {stop_loss_price}")

        # Check if the symbol exists in bought_stocks before deleting
        with buy_sell_lock:
            if symbol in bought_stocks:
                del bought_stocks[symbol]

                # Delete the position from the database
                db_position = session.query(Position).filter_by(symbol=symbol).first()

                # Check if the position exists before attempting to delete
                if db_position:
                    # Delete the position
                    session.delete(db_position)

                    # Commit the changes
                    session.commit()

        return stop_order.id

    except Exception as e:
        print(f"Error placing trailing stop sell order for {symbol}: {str(e)}")
        return None


# Modify the update_bought_stocks_from_api function to use the correct purchase date
def update_bought_stocks_from_api():
    positions = api.list_positions()
    bought_stocks = {}

    yesterday = datetime.today() - timedelta(days=1)

    run_counter_file = "trading_bot_run_counter.txt"

    if not os.path.exists(run_counter_file):
        with open(run_counter_file, "w") as f:
            f.write("0")
        run_counter = 0
    else:
        with open(run_counter_file, "r") as f:
            run_counter = int(f.read())
        run_counter += 1

    for position in positions:
        symbol = position.symbol
        avg_entry_price = float(position.avg_entry_price)

        try:
            db_position = session.query(Position).filter_by(symbol=symbol).one()
            db_position.quantity = position.qty
            db_position.avg_price = avg_entry_price

            if POSITION_DATES_AS_YESTERDAY_OPTION and run_counter < 1:
                db_position.purchase_date = yesterday.strftime("%Y-%m-%d")  # Use the provided date format
        except NoResultFound:
            purchase_date = yesterday if POSITION_DATES_AS_YESTERDAY_OPTION and run_counter < 1 else datetime.today()
            purchase_date_str = purchase_date.strftime("%Y-%m-%d")  # Convert datetime to string
            db_position = Position(symbol=symbol, quantity=position.qty, avg_price=avg_entry_price,
                                   purchase_date=purchase_date_str)  # Use the provided date format
            session.add(db_position)

        bought_stocks[symbol] = (avg_entry_price, db_position.purchase_date)

    with open(run_counter_file, "w") as f:
        f.write(str(run_counter))

    session.commit()
    return bought_stocks


def sell_stocks(bought_stocks, buy_sell_lock):
    stocks_to_remove = []

    # below time and date are only used in the logging file
    now = datetime.now(pytz.timezone('US/Eastern'))
    current_time_str = now.strftime("Eastern Time | %I:%M:%S %p | %m-%d-%Y |")

    # below date is used in the database and to sell stocks
    extracted_date_from_today_date = datetime.today().date()

    for symbol, (bought_price, purchase_date) in bought_stocks.items():

        status_printer_sell_stocks()  # keep this under the "s" in "for symbol"

        # Convert today_date and bought_date to text strings
        today_date_str = extracted_date_from_today_date.strftime("%Y-%m-%d")
        bought_date_str = purchase_date  # already string data format

        # the rest of the code goes by purchase_date instead of bought_date

        # print("today_date_str = ", symbol, today_date_str)  # uncomment to print variable date to debug as same date

        # print("bought_date_str = ", symbol, bought_date_str)  # uncomment to print variable date to debug as same date

        # Check if the stock was purchased at least one day before today
        # if bought_date_str < today_date_str:

        if bought_date_str < today_date_str:  # keep under the "s" in "for symbol"
            current_price = get_current_price(symbol)  # keep this under the "o" in "bought"
            position = api.get_position(symbol)  # keep this under the "o" in "bought"
            bought_price = float(position.avg_entry_price)  # keep this under the "o" in "bought"

            # Check if there is an open sell order for the symbol
            open_orders = api.list_orders(status='open', symbol=symbol)
            if open_orders:
                print(f"There is an open sell order for {symbol}. Skipping sell order.")
                continue  # Skip to the next iteration if there's an open sell order

            # Never calculate ATR for a buy price or sell price because it is too slow. 1 second per stock.
            # Sell stocks if the current price is more than 0.1% higher than the purchase price.
            if current_price >= bought_price * 1.001:  # keep this under the "o" in "bought"
                qty = api.get_position(symbol).qty
                api.submit_order(symbol=symbol, qty=qty, side='sell', type='market', time_in_force='day')
                print(
                    f" {current_time_str}, Sold {qty} shares of {symbol} at {current_price} based on a higher selling price. ")
                with open(csv_filename, mode='a', newline='') as csv_file:
                    csv_writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
                    csv_writer.writerow(
                        {'Date': current_time_str, 'Sell': 'Sell', 'Quantity': qty, 'Symbol': symbol,
                         'Price Per Share': current_price})

                stocks_to_remove.append(symbol)  # Append symbols to remove. keep this under the w in with open

                time.sleep(2)  # keep this under the s in stocks

            time.sleep(2)  # keep this under the i in if current_price. this stops after checking each stock price

    # I might not need the extra sleep command below
    # keep the below time.sleep(1) below the f in "for symbol"
    time.sleep(2)  # wait 1 - 3 seconds to not move too fast for the stock price data rate limit.

    try:  # keep this under the s in "sell stocks"
        with buy_sell_lock:
            for symbol in stocks_to_remove:
                del bought_stocks[symbol]
                trade_history = TradeHistory(symbol=symbol, action='sell', quantity=qty, price=current_price,
                                             date=today_date_str)  # Use the provided "string data" date format
                session.add(trade_history)
                session.query(Position).filter_by(symbol=symbol).delete()
            session.commit()
            refresh_after_sell()
    except SQLAlchemyError as e:  # keep this under the t in "try"
        session.rollback()
        # Handle the error or log it


def refresh_after_sell():
    global bought_stocks
    time.sleep(2)
    bought_stocks = update_bought_stocks_from_api()


def load_positions_from_database():
    positions = session.query(Position).all()
    bought_stocks = {}
    for position in positions:
        symbol = position.symbol
        avg_price = position.avg_price
        initial_api_returned_purchase_date = position.purchase_date
        # the purchase date below is changed to string data format
        purchase_date = initial_api_returned_purchase_date.strftime("%Y-%m-%d")
        bought_stocks[symbol] = (avg_price, purchase_date)
    return bought_stocks


def main():
    global stocks_to_buy

    stocks_to_buy = get_stocks_to_trade()
    bought_stocks = load_positions_from_database()
    buy_sell_lock = threading.Lock()

    while True:  # keep this under the m in main
        try:
            stop_if_stock_market_is_closed()  # comment this line to debug the Python code
            now = datetime.now(pytz.timezone('US/Eastern'))
            current_time_str = now.strftime("Eastern Time | %I:%M:%S %p | %m-%d-%Y |")

            cash_balance = round(float(api.get_account().cash), 2)
            print("------------------------------------------------------------------------------------")
            print("2023 Edition of the Bear Market Advanced Stock Trading Robot ")
            print("by https://github.com/CodeProSpecialist")
            print("------------------------------------------------------------------------------------")
            print(f"  {current_time_str} Cash Balance: ${cash_balance}")
            day_trade_count = api.get_account().daytrade_count
            print("\n")
            print(f"Current day trade number: {day_trade_count} out of 3 in 5 business days")
            print("\n")
            print("\n")
            print("------------------------------------------------------------------------------------")
            print("\n")

            stocks_to_buy = get_stocks_to_trade()

            if not bought_stocks:
                bought_stocks = update_bought_stocks_from_api()

            # the below threads will run the buy_stocks and the sell_stocks functions at the same time
            # in parallel to buy and sell more without taking more time than necessary.
            # keep the below python code below the i in if not bought stocks
            # Create threads for buy_stocks and sell_stocks
            sell_thread = threading.Thread(target=sell_stocks, args=(bought_stocks, buy_sell_lock))
            buy_thread = threading.Thread(target=buy_stocks, args=(bought_stocks, stocks_to_buy, buy_sell_lock))

            # Start both threads
            sell_thread.start()
            buy_thread.start()

            # Wait for both threads to finish
            sell_thread.join()
            buy_thread.join()

            if PRINT_STOCKS_TO_BUY:
                print("\n")
                print("------------------------------------------------------------------------------------")
                print("\n")
                print("Stocks to Purchase:")
                print("\n")
                for symbol in stocks_to_buy:
                    current_price = get_current_price(symbol)

                    print(f"Symbol: {symbol} | Current Price: {current_price} ")
                    time.sleep(1)  # wait 1 second to not move too fast for the stock data rate limit.
                print("\n")
                print("------------------------------------------------------------------------------------")
                print("\n")

            if PRINT_ROBOT_STORED_BUY_AND_SELL_LIST_DATABASE:
                print_database_tables()

            # account = api.get_account()
            # print(account)   # uncomment to print Alpaca Account details to debug the software

            if DEBUG:
                print("\n")
                print("------------------------------------------------------------------------------------")
                print("\n")
                print("Stocks to Purchase:")
                print("\n")
                for symbol in stocks_to_buy:
                    current_price = get_current_price(symbol)
                    atr_low_price = get_atr_low_price(symbol)
                    print(
                        f"Symbol: {symbol} | Current Price: {current_price} | ATR low buy signal price: {atr_low_price}")

                print("\n")
                print("------------------------------------------------------------------------------------")
                print("\n")
                print("\nStocks to Sell:")
                print("\n")
                for symbol, _ in bought_stocks.items():
                    current_price = get_current_price(symbol)
                    atr_high_price = get_atr_high_price(symbol)
                    print(
                        f"Symbol: {symbol} | Current Price: {current_price} | ATR high sell signal profit price: {atr_high_price}")

                print("\n")

            # keep the below time.sleep(60) to 60 seconds because yfinance api
            # will stop the stock data feed for the reason of exceeding the rate limit or from this program being too fast.
            print("Do Not Stop this Robot or you will need to ")
            print("delete the trading_bot.db database file and start over again with an empty database. ")
            print("Placing trades without this Robot will also require ")
            print("deleting the trading_bot.db database file and starting over again with an empty database. ")
            print("")
            print("Waiting 30 seconds before checking price data again........")
            print("")
            time.sleep(30)  # keep this under the i in if

        except Exception as e:
            logging.error(f"Error encountered: {e}")
            time.sleep(120)  # keep this under the l in logging


if __name__ == '__main__':  # keep this to the far left side.
    try:
        main()  # keep this under the e in name

    except Exception as e:  # keep this under the t in try
        logging.error(f"Error encountered: {e}")  # keep this under the p in except
        session.close()  # keep this under the l in logging
