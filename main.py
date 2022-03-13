import requests
from mongo import Document
from pymongo import MongoClient
import dns
try:
    credential = MongoClient(
        "mongodb+srv://MongoUser:password1234@cluster0.dka3m.mongodb.net/MyMongoDB?retryWrites=true"
        "&w=majority")
    print("Connected succesfully")
except:
    print("Could not connect to MongoDB")

mongoDatabase = credential.get_database("MyMongoDB")
collection = mongoDatabase.get_collection("Etherscan")

if collection is None:
    mongoDatabase.create_collection("Etherscan")
    print("Collection: Etherscan")
else:
    print("Existing collection")

def get_transaction_by_address(address):
    url = "https://api.etherscan.io/api?module=account&action=txlist&address=" + str(address) + \
          "&startblock=0&endblock=99999999&page=1&offset=1000&sort=desc&apikey=YourApiKeyToken"
    response = requests.get(url)
    address_content = response.json()
    result = address_content.get("result")

    for n, transaction in enumerate(result):

        hash = transaction.get("hash")
        tx_from = transaction.get("from")
        tx_to = transaction.get("to")
        gasPrice = transaction.get("gasPrice")
        gasUsed = transaction.get("gasUsed")
        timeStamp = transaction.get("timeStamp")
        value = transaction.get("value")
        contractAddress = transaction.get("contractAddress")
        tokenSymbol = "ETH"

        document = {"address": ""+address,
                    "hash": hash,
                    "from": tx_from,
                    "to": tx_to,
                    "gasPrice": gasPrice,
                    "gasUsed": gasUsed,
                    "timeStamp": timeStamp,
                    "value": value,
                    "contractAddress": contractAddress,
                    "tokenSymbol": tokenSymbol}
        result = collection.insert_one(document)

        cursor = collection.find()
        for record in cursor:
            print(record)

        print("{")
        print("'address': ", address)
        print("'transaction':{")
        print(" 'hash': ", hash)
        print(" 'from': ", tx_from)
        print(" 'to': ", tx_to)
        print(" 'gasPrice': ", gasPrice)
        print(" 'gasUsed': ", gasUsed)
        print(" 'timeStamp': ", timeStamp)
        print(" 'value': ", value)
        print(" 'contractAddress': ", contractAddress)
        print(" 'tokenSymbol': ", tokenSymbol)
        print(" }")
        print("}")
        print("\n")
    return result


account1 = get_transaction_by_address(0x9f26aE5cd245bFEeb5926D61497550f79D9C6C1c)
print(account1)

