import os
import json
import sqlite3
import tkinter as tk
import datetime as dt
from tkinter import ttk
# from PIL import Image, ImageTk
from tkinter import messagebox
import pandas_datareader.data as web

# GLOBAL VARIABLES
DB_NAME = 'stocks.db'
TABLE_NAME = 'prices'
ROOT_GEOMETRY_SIZE = '960x490'
MANAGER_GEOMETRY_SIZE = '180x180'
DIV_DATA = json.load(open('data/historical_div_sp500.json', 'r'))


def _get_close_price(symbol):
    startDate = (dt.date.today() - dt.timedelta(days=5)).strftime("%Y-%m-%d")
    endDate = dt.date.today().strftime("%Y-%m-%d")
    close = web.DataReader(symbol, 'yahoo', startDate,
                           endDate)['Adj Close'].iloc[-1].round(2)
    #print(close)
    return close


def _clear_input():
    symbol_input.delete(0, tk.END)
    price_input.delete(0, tk.END)


def popup():
    response = messagebox.askyesnocancel(
        "Deleting All Data...", "Are you sure you want to delete all data?")
    if response == True:
        erase()
    elif response == False:
        return
    else:
        return


def add():
    # INPUT VALIDITY CHECK
    s = symbol_input.get()
    tp = price_input.get()
    if len(s) == 0 or len(tp) == 0:
        return
    if (s == "") or (not str(tp).isnumeric()):
        _clear_input()
        return messagebox.showwarning("WARNING!", "INVALID INPUT.")
    try:
        cp = _get_close_price(s)
        last_year = dt.datetime.today().year - 1
        div_yield = round(100 * DIV_DATA[s.upper()][0][str(last_year)] / cp, 3)
    except:
        _clear_input()
        return messagebox.showwarning("WARNING!",
                                      "INCORRECT SYMBOL OR SYMBOL IS NOT IN S&P500.")

    db_connect = sqlite3.connect(DB_NAME)
    c = db_connect.cursor()

    # Create a table
    c.execute(f"""CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
        symbol text,
        target_price real,
        current_price real,
        dividend_yield real
        ) """)

    # Insert into table
    c.execute(
        f"INSERT INTO {TABLE_NAME} VALUES (:symbol, :target_price, :current_price, :dividend_yield)",
        {
            'symbol': s.upper(),
            'target_price': tp,
            'current_price': cp,
            'dividend_yield': div_yield
        })

    _clear_input()
    db_connect.commit()
    db_connect.close()
    query()


def delete():
    db_connect = sqlite3.connect(DB_NAME)
    c = db_connect.cursor()

    c.execute(f"DELETE from {TABLE_NAME} WHERE oid=" + str(uid_from_create_manager))

    db_connect.commit()
    db_connect.close()
    query()
    manager.destroy()

def remove_selected():
    if len(watchlist_tree.selection()) > 0:
        #uid_watchlist_tree = watchlist_tree.item(watchlist_tree.focus())['values'][0]
        db_connect = sqlite3.connect(DB_NAME)
        c = db_connect.cursor()
        c.execute(f"DELETE from {TABLE_NAME} WHERE oid=" + str(uid_from_create_manager))
        db_connect.commit()
        db_connect.close()
        watchlist_tree.selection_clear()
    if len(buylist_tree.selection()) > 0:
        #uid_buylist_tree = buylist_tree.item(buylist_tree.focus())['values'][0]
        db_connect = sqlite3.connect(DB_NAME)
        c = db_connect.cursor()
        c.execute(f"DELETE from {TABLE_NAME} WHERE oid=" + str(uid_from_create_manager))
        db_connect.commit()
        db_connect.close()
        buylist_tree.selection_clear()

    query()


def save_change():
    db_connect = sqlite3.connect(DB_NAME)
    c = db_connect.cursor()

    c.execute(
        f"""UPDATE {TABLE_NAME} SET
              symbol = :s,
              target_price = :tp

              WHERE oid = :oid
              """, {
            's': symbol_input_manager.get(),
            'tp': price_input_manager.get(),
            'oid': uid_from_create_manager
        })

    db_connect.commit()
    db_connect.close()
    query()
    manager.destroy()

def create_manager(uid):
    global uid_from_create_manager
    uid_from_create_manager = uid
    global manager
    global price_input_manager
    global symbol_input_manager

    manager = tk.Tk()
    manager.title("MODIFY AN ALERT")
    manager.geometry(MANAGER_GEOMETRY_SIZE)

    db_connect = sqlite3.connect(DB_NAME)
    c = db_connect.cursor()

    c.execute(f"SELECT *, oid FROM {TABLE_NAME} WHERE oid=" + str(uid))
    records = c.fetchall()  # fetches all records

    # Create Labels
    symbol_manager = tk.Label(manager, text="SYMBOL", width=15)
    symbol_manager.grid(row=0, column=0)
    target_price_manager = tk.Label(manager, text="ALERT PRICE", width=15)
    target_price_manager.grid(row=1, column=0)

    # Create Entry
    symbol_input_manager = tk.Entry(manager, width=10)
    symbol_input_manager.grid(row=0, column=1, pady=10)
    price_input_manager = tk.Entry(manager, width=10)
    price_input_manager.grid(row=1, column=1, pady=10)

    # Loop through results
    for record in records:
        symbol_input_manager.insert(0, record[0])
        price_input_manager.insert(0, record[1])

    # Save Change Button in Manager
    save_change_btn = tk.Button(manager,
                                text="SAVE CHANGES",
                                command=save_change,
                                width=20)
    save_change_btn.grid(row=3, column=0, pady=10, columnspan=2)

    delete_btn = tk.Button(manager,
                                text="DELETE THIS ALERT",
                                command=delete,
                                width=20)
    delete_btn.grid(row=4, column=0, pady=10, columnspan=2)

    _clear_input()

def manage_watchlist():

    if len(watchlist_tree.selection()) > 0:
        uid = watchlist_tree.item(watchlist_tree.focus())['values'][0]
        create_manager(uid)
        unselect_watchlist()

def manage_buylist():

    if len(buylist_tree.selection()) > 0:
        uid = buylist_tree.item(buylist_tree.focus())['values'][0]
        create_manager(uid)
        unselect_buylist()

def unselect_watchlist():
    if len(watchlist_tree.selection()) > 0:
        for item in watchlist_tree.selection():
            watchlist_tree.selection_remove(item)

def unselect_buylist():
    if len(buylist_tree.selection()) > 0:
        for item in buylist_tree.selection():
            buylist_tree.selection_remove(item)



def query():
    db_connect = sqlite3.connect(DB_NAME)
    c = db_connect.cursor()

    c.execute(f"SELECT *, oid FROM {TABLE_NAME}")
    records = c.fetchall()  # fetches all records

    #print(records)
    # Display Treeview

    global watchlist_tree
    watchlist_tree = ttk.Treeview(root)

    # Define Columns
    watchlist_tree['columns'] = ("UID", "SYMBOL", "ALERT PRICE",
                                 "CURRENT PRICE", "DIVIDEND YIELD")

    # Format Columns
    watchlist_tree.column("#0", width=0, stretch=tk.NO)
    watchlist_tree.column("UID", anchor=tk.CENTER, width=55)
    watchlist_tree.column("SYMBOL", anchor=tk.CENTER, width=100)
    watchlist_tree.column("ALERT PRICE", anchor=tk.CENTER, width=100)
    watchlist_tree.column("CURRENT PRICE", anchor=tk.CENTER, width=100)
    watchlist_tree.column("DIVIDEND YIELD", anchor=tk.CENTER, width=100)

    # Create Headings
    watchlist_tree.heading("#0", text="", anchor=tk.CENTER)
    watchlist_tree.heading("UID", text="UID", anchor=tk.CENTER)
    watchlist_tree.heading("SYMBOL", text="SYMBOL", anchor=tk.CENTER)
    watchlist_tree.heading("ALERT PRICE", text="ALERT PRICE", anchor=tk.CENTER)
    watchlist_tree.heading("CURRENT PRICE",
                           text="CURRENT PRICE",
                           anchor=tk.CENTER)
    watchlist_tree.heading("DIVIDEND YIELD",
                        text="DIVIDEND YIELD",
                        anchor=tk.CENTER)

    global buylist_tree
    buylist_tree = ttk.Treeview(root)

    # Define Columns
    buylist_tree['columns'] = ("UID", "SYMBOL", "ALERT PRICE", "CURRENT PRICE", "DIVIDEND YIELD")

    # Format Columns
    buylist_tree.column("#0", width=0, stretch=tk.NO)
    buylist_tree.column("UID", anchor=tk.CENTER, width=55)
    buylist_tree.column("SYMBOL", anchor=tk.CENTER, width=100)
    buylist_tree.column("ALERT PRICE", anchor=tk.CENTER, width=100)
    buylist_tree.column("CURRENT PRICE", anchor=tk.CENTER, width=100)
    buylist_tree.column("DIVIDEND YIELD", anchor=tk.CENTER, width=100)

    # Create Headings
    buylist_tree.heading("#0", text="", anchor=tk.CENTER)
    buylist_tree.heading("UID", text="UID", anchor=tk.CENTER)
    buylist_tree.heading("SYMBOL", text="SYMBOL", anchor=tk.CENTER)
    buylist_tree.heading("ALERT PRICE", text="ALERT PRICE", anchor=tk.CENTER)
    buylist_tree.heading("CURRENT PRICE",
                         text="CURRENT PRICE",
                         anchor=tk.CENTER)
    buylist_tree.heading("DIVIDEND YIELD",
                         text="DIVIDEND YIELD",
                         anchor=tk.CENTER)

    # Add Data
    for i in range(len(records)):
        symbol_name = records[i][0]
        tPrice = records[i][1]
        currPrice = records[i][2]
        div_yield = records[i][3]
        uid = records[i][4]

        #print(symbol_name, tPrice, currPrice)
        if currPrice <= tPrice:
            buylist_tree.insert(parent='',
                                index='end',
                                iid=i,
                                text="",
                                values=(uid, symbol_name, "$ " + str(tPrice), "$ " + str(currPrice), str(div_yield) + " %"))
        else:
            watchlist_tree.insert(parent='',
                                  index='end',
                                  iid=i,
                                  text="",
                                  values=(uid, symbol_name, "$ " + str(tPrice), "$ " + str(currPrice), str(div_yield) + " %"))

    watchlist_tree.grid(row=4, column=0, columnspan=2, padx=10)
    buylist_tree.grid(row=4, column=3, columnspan=2, padx=10)
    db_connect.close()


def export():
    db_connect = sqlite3.connect(DB_NAME)
    c = db_connect.cursor()

    c.execute(f"SELECT * FROM {TABLE_NAME}")
    data = c.fetchall()
    return data


def refresh():
    db_connect = sqlite3.connect(DB_NAME)
    c = db_connect.cursor()
    c.execute(f"SELECT *, oid FROM {TABLE_NAME}")
    records = c.fetchall()

    for i in range(len(records)):
        symbol = records[i][0]
        currPrice = _get_close_price(symbol)
        uid = records[i][3]
        #print(f"symbol: {symbol} | currPrice: {currPrice} | oid: {records[i][3]}")
        c.execute(
            f"""UPDATE {TABLE_NAME} SET
                current_price = :cp
                WHERE oid = :oid
                """, {
                'cp': currPrice,
                'oid': uid
            })

    db_connect.commit()
    db_connect.close()
    query()
    refresh_status = tk.Label(root, text="Data Refreshed Manually at " + dt.datetime.now().strftime("%Y/%m/%d %H:%M:%S"), anchor=tk.E)
    refresh_status.grid(row=10, column=0, columnspan=6, sticky=tk.W + tk.E, padx=10)

def auto_refresh():
    if (dt.datetime.today().weekday() >= 0) and (dt.datetime.today().weekday() < 5): # market open days
        now = dt.datetime.now()
        market_open = now.replace(hour=8, minute=30)
        market_close = now.replace(hour=16, minute=30)

        #print(now, market_open, market_close)

        if market_open <= now <= market_close:
            refresh()
            refresh_status = tk.Label(root, text="Data Auto-Refreshed at " + dt.datetime.now().strftime("%Y/%m/%d %H:%M:%S"), anchor=tk.E)
            refresh_status.grid(row=10, column=0, columnspan=6, sticky=tk.W + tk.E, padx=10)
            root.after(10000, auto_refresh)
        else:
            return



def erase():
    db_connect = sqlite3.connect(DB_NAME)
    c = db_connect.cursor()

    c.execute(f"DELETE FROM {TABLE_NAME}")

    db_connect.commit()
    db_connect.close()
    query()


if __name__ == '__main__':

    root = tk.Tk()
    root.title("PY STOCK MANAGER")
    root.geometry(ROOT_GEOMETRY_SIZE)
    # ico = Image.open("img/icon.png")
    # photo = ImageTk.PhotoImage(ico)
    # root.iconphoto(False, photo)

    # Create Labels
    symbol = tk.Label(root, text="STOCK SYMBOL", width=15)
    symbol.grid(row=0, column=0, pady=10)
    target_price = tk.Label(root, text="ALERT PRICE", width=15)
    target_price.grid(row=1, column=0, pady=10)

    watchlist = tk.Label(root, text=":::::::::::::::::::::::::::::::: WATCH-LIST ::::::::::::::::::::::::::::::::", width=40, font=('Courier', 10, 'bold'))
    watchlist.grid(row=3, column=0, pady=10, columnspan=2)

    alert_reached = tk.Label(root, text=":::::::::::::::::::::::::::::::: BUY-LIST ::::::::::::::::::::::::::::::::", width=40, font=('Courier', 10, 'bold'))
    alert_reached.grid(row=3, column=3, pady=10, columnspan=2)

    # Create Entry
    symbol_input = tk.Entry(root, width=20)
    symbol_input.grid(row=0, column=1)
    price_input = tk.Entry(root, width=20)
    price_input.grid(row=1, column=1)


    # Create Buttons
    addButton = tk.Button(root,
                          text="ADD SYMBOL & PRICE",
                          command=add,
                          width=50,
                          bg='#696969',
                          fg='white')
    addButton.grid(row=2, column=0, columnspan=2, pady=5)
    modify_watchlist_btn = tk.Button(root,
                           text="MODIFY A SELECTED ALERT IN WATCH-LIST",
                           command=manage_watchlist,
                           width=50,
                           bg='#4169E1',
                           fg='white')
    modify_watchlist_btn.grid(row=5, column=0, columnspan=2, pady=5)

    modify_buylist_btn = tk.Button(root,
                            text="MODIFY A SELECTED ALERT IN BUY-LIST",
                            command=manage_buylist,
                            width=50,
                            bg='#4169E1',
                            fg='white')
    modify_buylist_btn.grid(row=5, column=3, columnspan=2, pady=5)

    unselect_watchlist_btn = tk.Button(root,
                           text="UNSELECT ALL IN WATCH-LIST",
                           command=unselect_watchlist,
                           width=50,
                           bg='#4169E1',
                           fg='white')
    unselect_watchlist_btn.grid(row=6, column=0, columnspan=2, pady=5)

    unselect_buylist_btn = tk.Button(root,
                            text="UNSELECT ALL IN BUY-LIST",
                            command=unselect_buylist,
                            width=50,
                            bg='#4169E1',
                            fg='white')
    unselect_buylist_btn.grid(row=6, column=3, columnspan=2, pady=5)

    refresh_btn = tk.Button(root,
                            text="REFRESH DATA",
                            command=refresh,
                            bg="#1CA757",
                            fg='white',
                            width=50)
    refresh_btn.grid(row=0, column=2, columnspan=2, rowspan=2, pady=5)

    reset_btn = tk.Button(root,
                          text="ERASE ALL DATA",
                          command=popup,
                          width=50,
                          bg='red',
                          fg='white')
    reset_btn.grid(row=1, column=2, columnspan=2, rowspan=2, pady=5)



    if (os.path.exists(f'./{DB_NAME}')):
        query()

    auto_refresh()
    root.mainloop()