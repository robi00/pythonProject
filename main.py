import time
import pymongo
import requests
import csv
from pymongo import MongoClient
import dns
import os
from decouple import config
import networkx as nx
import matplotlib.pyplot as plt

# label.strip
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
    file.write(entry + "\n")
    file.close()


def store_transaction(tx: dict, addr: str):
    trans = {'address': addr, 'transactions': tx}
    mongoDatabase.Etherscan.insert_one(trans)
    hash = tx['hash']
    print(f"Entering transaction {hash} for the account {addr}")


def store_txs(address: str):
    print("IN STORE TXS:" + address)
    url = f"https://api.etherscan.io/api?module=account&action=txlist&address={address}&startblock=0&" \
          f"endblock=99999999&page=1&offset=10000&sort=desc&apikey={API_KEY}"
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
        print(f"VALUE: {_tx['value']}")

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
        _tx['tokenSymbol'] = "USDT"
        store_transaction(tx=_tx, addr=address)


def extract_transactions(addresses: list):
    i = 0
    for address in addresses:
        print("EXTRACT TRANS: " + address)
        store_txs(address)
        store_txs_erc20(address)
        i += 1
        if i % 3 == 0:
            time.sleep(1)


def load_addresses():
    addresses = set()
    with open("addresses.csv") as f:
        datafile = f.readlines()
        for address in datafile:
            address = address.split("\t")
            address = address[0]
            if "0x" in address:  # check
                addresses.add(address)
    return addresses


def edge(tx_from: str, tx_to: str, gasPrice: str, gasUsed: str, timeStamp: str, value: str, label: str):
    ent = "{},{},{},{},{},{}".format(tx_from, tx_to, gasPrice, gasUsed, timeStamp, value, label)
    write("edges.csv", entry=ent)


def create_edges(addresses: set):
    with open("transactions.csv") as f:
        for line in f:
            line = line.split(",")
            fromAddr = line[0]
            toAddr = line[1]
            gasPrice = line[2]
            gasUsed = line[3]
            timeStamp = line[4]
            value = line[5]
            if fromAddr in addresses:  # malicious from address
                label = '0'
            elif fromAddr not in addresses and toAddr not in addresses:  # onest from and to
                label = '2'
            else:  # onest from but malicious to -> phishing
                label = '1'

            edge(
                tx_from=fromAddr,
                tx_to=toAddr,
                gasPrice=gasPrice,
                gasUsed=gasUsed,
                timeStamp=timeStamp,
                value=value,
                label=label
            )


def create_nodes():
    addresses = set()
    with open("edges.csv") as f:
        datafile = f.readlines()
        for label in datafile:
            label = label.split(",")
            if label[6] == '0\n':
                addr_from = label[0]
                if "0x" in addr_from and addr_from not in addresses:
                    addresses.add(addr_from)
                    entry = "{},{}".format(addr_from, "0")
                    write("nodes.csv", entry)
                addr_to = label[1]
                if "0x" in addr_to and addr_to not in addresses:
                    addresses.add(addr_to)
                    entry = "{},{}".format(addr_to, "0")
                    write("nodes.csv", entry)
            elif label[6] == '1\n':
                addr_from = label[0]
                if "0x" in addr_from and addr_from not in addresses:
                    addresses.add(addr_from)
                    entry = "{},{}".format(addr_from, "1")
                    write("nodes.csv", entry)
                addr_to = label[1]
                if "0x" in addr_to and addr_to not in addresses:
                    addresses.add(addr_to)
                    entry = "{},{}".format(addr_to, "0")
                    write("nodes.csv", entry)
            else:
                addr_from = label[0]
                if "0x" in addr_from and addr_from not in addresses:
                    addresses.add(addr_from)
                    entry = "{},{}".format(addr_from, "2")
                    write("nodes.csv", entry)
                addr_to = label[1]
                if "0x" in addr_to and addr_to not in addresses:
                    addresses.add(addr_to)
                    entry = "{},{}".format(addr_to, "2")
                    write("nodes.csv", entry)


def get_transaction(hash: str) -> dict:
    response = mongoDatabase.Etherscan.find({"transactions.hash": hash})
    for record in response:
        print(f"RECORD: {record}")


def tr(tx_from: str, tx_to: str, gasPrice: str, gasUsed: str, value: str, timeStamp: str):
    ent = "{},{},{},{},{},{}".format(tx_from, tx_to, gasPrice, gasUsed, value, timeStamp)
    write("transactions.csv", entry=ent)


def get_tr():
    res = mongoDatabase.Etherscan.find({})
    for transaction in res:
        tra = transaction['transactions']
        _tx = {}
        print(f"DENTRO: {tra['from']}")
        _tx['from'] = tra['from']
        _tx['to'] = tra['to']
        _tx['gasPrice'] = tra['gasPrice']
        _tx['gasUsed'] = tra['gasUsed']
        _tx['timeStamp'] = tra['timeStamp']
        _tx['value'] = tra['value']
        tr(
            tx_from=_tx['from'],
            tx_to=_tx['to'],
            gasPrice=_tx['gasPrice'],
            gasUsed=_tx['gasUsed'],
            timeStamp=_tx['timeStamp'],
            value=_tx['value'],
        )


def create_graph():
    g = nx.DiGraph()
    addresses = list()
    color_map = []

    with open("nodes.csv") as f:
        datafile = f.readlines()
        for node in datafile:
            node = node.split(",")
            address = node[0]
            if "0x" in address:
                addresses.append(address)
            g.add_nodes_from(addresses)

            if '0\n' in node[1] or '1\n' in node[1] or '2\n' in node[1]:
                if node[1] == '0\n':
                    color_map.append('red')
                elif node[1] == '1\n':
                    color_map.append('green')
                else:
                    color_map.append('blue')

    with open("edges.csv") as f:
        f_addr = []
        t_addr = []
        data = f.readlines()
        for edge in data:
            edge = edge.split(",")
            from_addr = edge[0]
            if "0x" in from_addr:
                f_addr.append(from_addr)
            to_addr = edge[1]
            if "0x" in to_addr:
                t_addr.append(to_addr)
        for i in range(len(f_addr) - 1):
            if f_addr[i] not in t_addr[i]:
                g.add_edge(f_addr[i], t_addr[i], weight=1.0, alpha=0.5)  # weight=value

    plt.figure(1)
    pos = nx.planar_layout(g)
    nx.draw_networkx(g, pos, node_size=20, node_color=color_map, with_labels=False)
    plt.show()


def main():
    account1 = "0xa7f72Bf63EDeCa25636F0B13Ec5135296ca2eBb2"
    account2 = "0xEda5066780dE29D00dfb54581A707ef6F52D8113"
    account3 = "0x079667f4f7a0B440Ad35ebd780eFd216751f0758"
    accounts = [account1, account2, account3]
    extract_transactions(accounts)
    get_tr()

    """hash = "0x6bb7039bd0bff1083c7d651ec32065239e574c3c8034a44ec6859f87b9e01dc9"
    get_transaction(hash)

    write(file="edges.csv", entry="from,to,gasPrice,gasUsed,timeStamp,value,label")
    write(file="nodes.csv", entry="address,label")

    fraudulent = load_addresses()
    create_edges(fraudulent)
    create_nodes()

    create_graph()"""


if __name__ == '__main__':
    main()
