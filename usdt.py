import pymongo
import requests
from mongo import Document
from pymongo import MongoClient
import dns

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

address = "0x9f26aE5cd245bFEeb5926D61497550f79D9C6C1c"

url = "https://api.etherscan.io/api?module=account&action=tokentx&" \
      "contractaddress=" + address + "&page=1&offset=100&sort=asc&apikey=YourApiKeyToken"

response = requests.get(url)
address_content = response.json()
result = address_content.get("result")

for token in result:
    hash = token.get("hash")
    tx_from = token.get("from")
    tx_to = token.get("to")
    gasPrice = token.get("gasPrice")
    gasUsed = token.get("gasUsed")
    timeStamp = token.get("timeStamp")
    value = token.get("value")
    contractAddress = token.get("contractAddress")
    tokenSymbol = "USDT"

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
