from os import listdir, remove

def check_for_and_del_io_files():

    if "currency_pair.txt" in listdir():
        remove("currency_pair.txt")
    if "currency_pair_history.csv" in listdir():
        remove("currency_pair_history.csv")
    if "trade_order.p" in listdir():
        remove("trade_order.p")
    
    pass