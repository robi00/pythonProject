import time
import pymongo
import requests
import csv
from pymongo import MongoClient
import dns
import os
from decouple import config

conn = pymongo.MongoClient("mongodb://127.0.0.1:27017")
mongoDatabase = conn.get_database("MyMongoDB")
collection = mongoDatabase.get_collection("Etherscan")

list_coll = mongoDatabase.list_collection_names()
list_len = len(list_coll)

if list_len == 0:
    mongoDatabase.create_collection("Etherscan")
    print("Collection: Etherscan")
else:
    print("Existing collection")
    mongoDatabase.Etherscan.drop()
    print("Existing collection deleted")
    mongoDatabase.create_collection("Etherscan")
    print("Collection: Etherscan")

API_KEY = config('API_KEY')


def write(file: str, entry: str):
    file = open(file, "a")
    file.write(entry + " \n")
    file.close()


def store_transaction(tx: dict, addr: str):
    trans = {'address': addr, 'transactions': tx}
    mongoDatabase.Etherscan.insert_one(trans)
    hash = tx['hash']
    print(f"Entering transaction {hash} for the account {addr}")


def store_txs(address: str):
    print("IN STORE TXS:" + address)
    url = f"https://api.etherscan.io/api?module=account&action=txlist&address={address}&startblock=0&" \
          f"endblock=99999999&page=1&offset=1000&sort=desc&apikey={API_KEY}"
    response = requests.get(url)
    address_content = response.json()
    print(address_content)
    result = address_content.get("result")

    for transaction in result:
        _tx = {}
        _tx['hash'] = transaction['hash']
        _tx['from'] = transaction['from']
        _tx['to'] = transaction['to']
        _tx['gasPrice'] = transaction['gasPrice']
        _tx['gasUsed'] = transaction['gasUsed']
        _tx['timeStamp'] = transaction['timeStamp']
        _tx['value'] = transaction['value']
        _tx['contractAddress'] = ""
        _tx['tokenSymbol'] = "ETH"
        store_transaction(tx=_tx, addr=address)


def store_txs_erc20(address: str):
    url = f"https://api.etherscan.io/api?module=account&action=tokentx&address={address}&startblock=0&endblock" \
          f"=999999999&sort=desc&apikey={API_KEY}"
    response = requests.get(url)
    address_content = response.json()
    result = address_content.get("result")

    for transaction in result:
        _tx = {}
        _tx['hash'] = transaction['hash']
        _tx['from'] = transaction['from']
        _tx['to'] = transaction['to']
        _tx['gasPrice'] = transaction['gasPrice']
        _tx['gasUsed'] = transaction['gasUsed']
        _tx['timeStamp'] = transaction['timeStamp']
        _tx['value'] = transaction['value']
        _tx['contractAddress'] = ""
        _tx['tokenSymbol'] = "ETH"
        store_transaction(tx=_tx, addr=address)


def extract_transactions(accounts: list):
    i = 0
    for address in accounts:
        print("EXTRACT TRANS: " + address)
        store_txs(address)
        store_txs_erc20(address)
        i += 1
        if i % 3 == 0:
            time.sleep(1)


def edge(tx_from: str, tx_to: str, gasPrice: str, gasUsed: str, value: str, label: str):
    ent = "{}, {}, {}, {}, {}, {}, ".format(tx_from, tx_to, gasPrice, gasUsed, value, label)
    write("edges.csv", entry=ent)


def create_edges():
    response = mongoDatabase.Etherscan.find({})
    for transaction in response:
        print(f"CREATE EDGES: {transaction}")
        _tx = {}
        _tx['tx_from'] = transaction['from']
        _tx['tx_to'] = transaction['to']
        _tx['gasPrice'] = transaction['gasPrice']
        _tx['gasUsed'] = transaction['gasUsed']
        _tx['value'] = transaction['value']

        with open("addresses.csv") as f:
            datafile = f.readlines()
        for line in datafile:
            if _tx['tx_from'] in line:  # malicious from address
                label = '0'
            elif not _tx['tx_from'] in line and _tx['tx_to'] in line:  # onest from and to
                label = '2'
            else:  # onest from but malicious to -> phishing
                label = '1'

        edge(
            tx_from=_tx['tx_from'],
            tx_to=_tx['tx_to'],
            gasPrice=_tx['gasPrice'],
            gasUsed=_tx['gasUsed'],
            value=_tx['value'],
            label=label
        )


def create_nodes(accounts: list):
    for account in accounts:
        with open("edges.csv") as f:
            datafile = f.readlines()
            for label in datafile:
                if label == '0':
                    id_label = '0'
                elif label == '1':
                    id_label = '1'
                elif label == '2':
                    id_label = '2'
        entry = "{},{}".format(account, id_label)
        write("nodes.csv", entry=entry)


def get_transaction(hash: str) -> dict:
    response = mongoDatabase.Etherscan.find({"transactions.hash": hash})
    for record in response:
        print(f"RECORD: {record}")


def main():
    account1 = "0x9f26aE5cd245bFEeb5926D61497550f79D9C6C1c"
    account2 = "0xbCEaA0040764009fdCFf407e82Ad1f06465fd2C4"
    account3 = "0x03B70DC31abF9cF6C1cf80bfEEB322E8D3DBB4ca"
    accounts = [account1, account2, account3]
    print(accounts)
    extract_transactions(accounts)
    hash = "0x6bb7039bd0bff1083c7d651ec32065239e574c3c8034a44ec6859f87b9e01dc9"
    get_transaction(hash)

    write(file="edges.csv", entry="from,to,gasPrice,gasUsed,value,label")
    write(file="nodes.csv", entry="address,label")

    create_edges()
    create_nodes(accounts)


if __name__ == '__main__':
    main()
