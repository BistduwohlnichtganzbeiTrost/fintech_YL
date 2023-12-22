from os import listdir, remove
from time import sleep
import pickle
from helper import *
import pandas as pd
from ib_insync import *

sampling_rate = 1 # how often (in seconds) to check for inputs from Dash
# for TWS paper account, default port is 7497; for IBG paper account, default port is 4002.
port = 7497
# choose the master id; set it in API settings within TWS/IBG
master_client_id = 54321
# choose the dedicated id just for orders
orders_client_id = 12345
# account number 
acc_number = 'text'

# create an IB app--an instance of the class 
ib = IB()
# connect the app to a running instance of IBG/TWS
# ib.disconnect()
ib.connect(host="127.0.0.1", port=port, clientId=master_client_id)

# make sure the connection--stay in this loop until ib.isConnected() == True
while not ib.isConnected():
    sleep(0.01)

print("connection successful!")

# request a current time
current_time = ib.reqCurrentTime()
print("Current time is: {}".format(current_time))

# prepare a dataframe of 'currency_pair_history.csv' when there are some errors
df_error = pd.DataFrame(columns=["date", "open", "high", "low", "close", "volume", "average", "barCount"])

# main while loop of the app: stay in this loop until the app is stopped by the user
while True:
    # if the app finds a file named 'currency_pair.txt' in the current directory, enter the code block
    if "currency_pair.txt" in listdir():
        with open("currency_pair.txt", "r") as f:
            currency_pair = f.read()
        # remove("currency_pair.txt")
        try:
            if currency_pair == "":
                df_error.to_csv("currency_pair_history.csv")
            else:
                contract = Forex(currency=currency_pair, exchange="IDEALPRO")
                bars = ib.reqHistoricalData(contract=contract,
                                            endDateTime="",
                                            durationStr="30 D",
                                            barSizeSetting="1 hour",
                                            whatToShow="MIDPOINT",
                                            useRTH=True)
                df = util.df(bars)
                df.to_csv("currency_pair_history.csv")
        except AssertionError:
            df_error.to_csv("currency_pair_history.csv")
            # side effects: doesn't return a value
        pass

    # if there's a file named trader_order.p in listdir(), then enter the loop below
    if "trader_order.p" in listdir():
        with open("trader_order.p", "rb") as f:
            trader_order = pickle.load(f)

        trade_currency = trader_order["trade_currency"]
        action = trader_order["action"]
        total_quantity = trader_order["trade_amt"]
        contract = Forex(trade_currency)
        contract_details = ContractDetails(contract)
        trade_hours = contract_details.tradingHours
        order = MarketOrder(action=action, totalQuantity=total_quantity)
        order.account = acc_number

        # create a special instance of IB() just for entering orders
        # the reason for this is because the way that Interactive Brokers automatically provides valid orders IDs 
        # to ib_insync is not trustworthy enough to rely on; it's best to set aside a dedicated clientID to only 
        # used for submitting orders, and close the connection when the order is successfully submitted.
        ib_order = IB()
        ib_order.connect(host="127.0.0.1", port=port, clientId=orders_client_id)
        new_order = ib_order.placeOrder(contract=contract, order=order)

        # in this while loop, we confirm that new_order filled
        while not new_order.orderStatus.status == "Filled":
            ib_order.sleep(0)

        remove("trader_order.p")
        ib_order.disconnect()

        pass

    # sleep for the while loop
    ib.sleep(sampling_rate)