from collections import defaultdict
import requests

address = "0x9f26aE5cd245bFEeb5926D61497550f79D9C6C1c"
url = "https://api.etherscan.io/api?module=account&action=txlist&address=" + address + \
          "&startblock=0&endblock=99999999&page=1&offset=1000&sort=desc&apikey=YourApiKeyToken"

response = requests.get(url)

address_content = response.json()
result = address_content.get("result")

for n,transaction in enumerate(result):
    hash = transaction.get("hash")
    tx_from = transaction.get("from")
    tx_to = transaction.get("to")
    gasPrice = transaction.get("gasPrice")
    gasUsed = transaction.get("gasUsed")
    timeStamp = transaction.get("timeStamp")
    value = transaction.get("value")
    contractAddress = transaction.get("contractAddress")
    tokenSymbol = "ETH"

    print("{ \n")
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
    print ("\n")

