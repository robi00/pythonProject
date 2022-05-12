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
    # print(f"Entering transaction {hash} for the account {addr}")


def store_txs(address: str):
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
        if transaction['from'] == address:
            _tx['incoming'] = "no"
        else:
            _tx['incoming'] = "yes"
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
        if transaction['from'] == address:
            _tx['incoming'] = "no"
        else:
            _tx['incoming'] = "yes"
        store_transaction(tx=_tx, addr=address)


def extract_transactions(address):
    collections = mongoDatabase.list_collection_names()
    len_list = len(collections)
    if len_list != 0:
        mongoDatabase.Etherscan.drop()
        mongoDatabase.create_collection("Etherscan")
    i = 0
    store_txs(address)
    # store_txs_erc20(address)
    i += 1
    if i % 3 == 0:
        time.sleep(10)


def load_addresses():
    addresses = list()
    with open("addresses.csv") as f:
        datafile = f.readlines()
        for address in datafile:
            address = address.split("\t")
            address = address[0]
            if "0x" in address:  # check
                addresses.append(address)
    return addresses


def edge(tx_from: str, tx_to: str, gasPrice: str, gasUsed: str, timeStamp: str, value: str, label: str, incoming: str):
    ent = "{},{},{},{},{},{},{},{}".format(tx_from, tx_to, gasPrice, gasUsed, value, timeStamp, label, incoming)
    write("edges.csv", entry=ent)


def create_edges(addresses: list):
    with open("transactions.csv") as f:
        for line in f:
            line = line.split(",")
            fromAddr = line[0]
            toAddr = line[1]
            gasPrice = line[2]
            gasUsed = line[3]
            value = line[4]
            timeStamp = line[5]
            incoming = line[6].strip("\n")
            if fromAddr in addresses:  # malicious from address
                labe = '0'
            elif fromAddr not in addresses and toAddr not in addresses:  # onest from and to
                labe = '2'
            else:  # onest from but malicious to -> phishing
                labe = '1'

            edge(
                tx_from=fromAddr,
                tx_to=toAddr,
                gasPrice=gasPrice,
                gasUsed=gasUsed,
                value=value,
                timeStamp=timeStamp,
                label=labe,
                incoming=incoming
            )


def create_nodes():
    addresses = set()
    with open("edges.csv") as f:
        datafile = f.readlines()
        for label in datafile:
            label = label.split(",")
            if label[6] == '0':
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
            elif label[6] == '1':
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


def tr(tx_from: str, tx_to: str, gasPrice: str, gasUsed: str, value: str, timeStamp: str, incoming: str):
    ent = "{},{},{},{},{},{},{}".format(tx_from, tx_to, gasPrice, gasUsed, value, timeStamp, incoming)
    write("transactions.csv", entry=ent)


def get_tr():
    res = mongoDatabase.Etherscan.find({})
    for transaction in res:
        tra = transaction['transactions']
        _tx = {}
        _tx['from'] = tra['from']
        _tx['to'] = tra['to']
        _tx['gasPrice'] = tra['gasPrice']
        _tx['gasUsed'] = tra['gasUsed']
        _tx['timeStamp'] = tra['timeStamp']
        _tx['value'] = tra['value']
        _tx['incoming'] = tra['incoming']
        tr(
            tx_from=_tx['from'],
            tx_to=_tx['to'],
            gasPrice=_tx['gasPrice'],
            gasUsed=_tx['gasUsed'],
            timeStamp=_tx['timeStamp'],
            value=_tx['value'],
            incoming=_tx['incoming'],
        )


def generate_eth_fraud():
    filenames_fraud = []
    for n in range(1, 501):
        account_number = f"account{n}.csv"
        filenames_fraud.append(account_number)

    for fname in filenames_fraud:
        with open(fname) as a:
            data = a.readlines()
            for line in data:
                line = line.split(",")
                if "0x" in line[0]:
                    value = line[9]
                    timestamp = line[2]
                    ent = "{},{}".format(timestamp, value)
                    write("val_normalized.csv", entry=ent)


def generate_eth_honest():
    filenames_honest = []
    for n in range(1, 501):
        account_number = f"acc{n}.csv"
        filenames_honest.append(account_number)

    for fname in filenames_honest:
        with open(fname) as a:
            data = a.readlines()
            for line in data:
                line = line.split(",")
                if "0x" in line[0]:
                    value = line[9]
                    timestamp = line[2]
                    ent = "{},{}".format(timestamp, value)
                    write("val_normalized.csv", entry=ent)


def numbers(address: str, nodes: int, edges: int, incoming: int, weight_in: int, weight_out: int):
    if edges == 0:
        outcoming = 0
        percincoming = 0
        percoutcoming = 0
    else:
        outcoming = edges - incoming
        percincoming = (incoming / edges) * 100
        percoutcoming = 100 - percincoming
    ent = "{},{},{},{},{},{},{},{},{}".format(address, nodes, edges, incoming, outcoming, percincoming, percoutcoming,
                                              weight_in, weight_out)
    # write("numbers_honest.csv", entry=ent)
    write("numbers_fraud.csv", entry=ent)


def create_graph(addr):
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
        f_addr = list()
        t_addr = list()
        timestamp = list()
        num_incoming = list()
        number = list()
        weight_in = 0
        weight_out = 0
        data = f.readlines()
        for edge in data:
            edge = edge.split(",")
            from_addr = edge[0]
            to_addr = edge[1]
            num = edge[7].strip("\n")
            number.append(num)
            if "0x" in to_addr:
                f_addr.append(from_addr)
                t_addr.append(to_addr)
                timestamp.append(edge[5])
                if "yes" in num:
                    num_incoming.append(num)

        for i in range(len(f_addr)):
            if f_addr[i] not in t_addr[i]:  # not cyclic transactions
                with open("val_normalized.csv") as f:
                    data = f.readlines()
                    for eth in data:
                        eth = eth.split(",")
                        if timestamp[i] in eth[0]:
                            g.add_edge(f_addr[i], t_addr[i], weight=eth[1].strip("\n"),
                                       alpha=0.5)  # weight=value normalized
                            if "yes" in number[i]:
                                weight_in += float(eth[1].strip('"\n'))
                            elif "no" in number[i]:
                                weight_out += float(eth[1].strip('"\n'))

    plt.figure(1)
    pos = nx.planar_layout(g)
    nx.draw_networkx(g, pos, node_size=20, node_color=color_map, with_labels=False)
    print(f"Number of nodes = {len(addresses)}")
    print(f"Number of edges = {len(f_addr)}")
    numbers(
        address=addr,
        nodes=len(addresses),
        edges=len(f_addr),
        incoming=len(num_incoming),
        weight_in=weight_in,
        weight_out=weight_out
    )
    plt.show()


def fraudulent_graph():
    """if os.path.exists("numbers_fraud.csv"):
        os.remove("numbers_fraud.csv")
        write("numbers_fraud.csv", entry="address,nodes,edges,n_edges_incoming,n_edges_outcoming,percentage_incoming,"
                                         "percentage_outcoming,total_weight_in,total_weight_out")"""
    # fraudulent accounts
    addresses = list()
    with open("addresses.csv") as f:
        datafile = f.readlines()
        for address in datafile:
            address = address.split("\t")
            if "0x" in address[0]:
                if "0" not in address[3]:
                    addresses.append(address[0])
    for n in range(500):  # 500 fraudulent accounts
        """with open(f"account{n+1}.csv") as f:
            data = f.readlines()
            for line in data:
                line = line.split(",")
                if "0x" in line[0]:
                    tx_from = line[4]
                    tx_to = line[5]
                    value = line[9]
                    write(f"{n+1}-{addresses[n]}.csv", entry="{},{},{}".format(tx_from,tx_to,value))"""
        if os.path.exists("edges.csv"):
            os.remove("edges.csv")
        if os.path.exists("nodes.csv"):
            os.remove("nodes.csv")
        if os.path.exists("transactions.csv"):
            os.remove("transactions.csv")
        if os.path.exists("val_normalized.csv"):
            os.remove("val_normalized.csv")

        extract_transactions(addresses[n])
        get_tr()
        generate_eth_fraud()

        fraudulent = load_addresses()
        create_edges(fraudulent)
        create_nodes()

        print(f"Account{n + 1}: {addresses[n]}")
        create_graph(addresses[n])


def honest_graph():
    """if os.path.exists("numbers_honest.csv"):
        os.remove("numbers_honest.csv")
        write("numbers_honest.csv", entry="address,nodes,edges,n_edges_incoming,n_edges_outcoming,percentage_incoming,"
                                         "percentage_outcoming,total_weight_in,total_weight_out")"""
    addresses = list()
    with open("honests.csv") as f:
        datafile = f.readlines()
        for address in datafile:
            address = address.split("\t")
            if "0x" in address[1]:
                addresses.append(address[1])
    for n in range(500):
        """with open(f"acc{n + 1}.csv") as f:
            data = f.readlines()
            for line in data:
                line = line.split(",")
                if "0x" in line[0]:
                    tx_from = line[4]
                    tx_to = line[5]
                    value = line[9]
                    write(f"honest_{n + 1}-{addresses[n]}.csv", entry="{},{},{}".format(tx_from, tx_to, value))"""
        if os.path.exists("edges.csv"):
            os.remove("edges.csv")
        if os.path.exists("nodes.csv"):
            os.remove("nodes.csv")
        if os.path.exists("transactions.csv"):
            os.remove("transactions.csv")
        if os.path.exists("val_normalized.csv"):
            os.remove("val_normalized.csv")

        extract_transactions(addresses[n])
        get_tr()
        generate_eth_honest()

        fraudolent = load_addresses()
        create_edges(fraudolent)
        create_nodes()

        print(f"Account{n + 1}: {addresses[n]}")
        create_graph(addresses[n])


def main():

    # fraudulent_graph()

    honest_graph()


if __name__ == '__main__':
    main()
