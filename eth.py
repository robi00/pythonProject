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


account1 = "0x9f26aE5cd245bFEeb5926D61497550f79D9C6C1c"
account2 = "0xbCEaA0040764009fdCFf407e82Ad1f06465fd2C4"
account3 = "0x03B70DC31abF9cF6C1cf80bfEEB322E8D3DBB4ca"
account4 = "0xEda5066780dE29D00dfb54581A707ef6F52D8113"
account5 = "0x5a59FC20E2659f9Df6A21ccD8627eA0D2403b36B"

API_KEY = os.getenv("API_KEY")

accounts = [account1, account2, account3, account4, account5]

for address in accounts:
    url = "https://api.etherscan.io/api?module=account&action=txlist&address=" + address + \
          "&startblock=0&endblock=99999999&page=1&offset=1000&sort=desc&apikey=" + API_KEY
    response = requests.get(url)
    address_content = response.json()
    result = address_content.get("result")

    for transaction in result:
        hash = transaction.get("hash")
        tx_from = transaction.get("from")
        tx_to = transaction.get("to")
        gasPrice = transaction.get("gasPrice")
        gasUsed = transaction.get("gasUsed")
        timeStamp = transaction.get("timeStamp")
        value = transaction.get("value")
        contractAddress = transaction.get("contractAddress")
        tokenSymbol = "ETH"

        mongoDatabase.Etherscan.insert_one(
            {
                "address": address,
                "   hash": hash,
                "   from": tx_from,
                "   to": tx_to,
                "   gasPrice": gasPrice,
                "   gasUsed": gasUsed,
                "   timeStamp": timeStamp,
                "   contractAddress": contractAddress,
                "   tokenSymbol": tokenSymbol,
            }
        )
        print("Transaction entered")






