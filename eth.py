import time
import pymongo
import requests
from mongo import Document
from pymongo import MongoClient
import dns
from dotenv import load_dotenv
import os

conn = pymongo.MongoClient("mongodb://127.0.0.1:27017")
mongoDatabase = conn.get_database("MyMongoDB")
collection = mongoDatabase.get_collection("Etherscan")

list = mongoDatabase.list_collection_names()
list_len = len(list)

if list_len == 0:
    mongoDatabase.create_collection("Etherscan")
    print("Collection: Etherscan")
else:
    print("Existing collection")

API_KEY = os.getenv("API_KEY")


def store_transaction(tx: dict, addr: str):
    trans = {'address': addr, 'transactions': tx}
    mongoDatabase.Etherscan.insert_one(trans)
    print("Transaction entered")


def store_txs(address: str):
    url = f"https://api.etherscan.io/api?module=account&action=txlist&address={address}&startblock=0&" \
          f"endblock=99999999&page=1&offset=1000&sort=desc&apikey={API_KEY}"
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


def store_txs_erc20(address: str):
    url = f"https://api.etherscan.io/api?module=account&action=tokentx&address={address}&startblock=0&endblock" \
          f"=999999999&sort=desc&apikey={API_KEY} "
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
        store_txs(address=address)
        store_txs_erc20(address=address)
        i += 1
        if i % 5 == 0:
            time.sleep(1)


"""def get_transaction(hash: str) -> dict:
    mongoDatabase.Etherscan.find({"hash": hash})
    return {
        "address": address,
        "hash": hash,
        "from": _tx['from'],
        "to": _tx['to'],
        "gasPrice": _tx['gasPrice'],
        "gasUsed": _tx['gasUsed'],
        "timeStamp": _tx['timeStamp'],
        "contractAddress": _tx['contractAddress'],
        "tokenSymbol": _tx['tokenSymbol'],
    }"""


def main():
    account1 = "0x9f26aE5cd245bFEeb5926D61497550f79D9C6C1c"
    account2 = "0xbCEaA0040764009fdCFf407e82Ad1f06465fd2C4"
    account3 = "0x03B70DC31abF9cF6C1cf80bfEEB322E8D3DBB4ca"
    account4 = "0xEda5066780dE29D00dfb54581A707ef6F52D8113"
    account5 = "0x5a59FC20E2659f9Df6A21ccD8627eA0D2403b36B"
    accounts = [account1, account2, account3, account4, account5]
    extract_transactions(accounts)
    """hash = "0x6bb7039bd0bff1083c7d651ec32065239e574c3c8034a44ec6859f87b9e01dc9"
    print(get_transaction(hash))"""


if __name__ == '__main__':
    main()
