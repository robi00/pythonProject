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
                if "0x4639cd8cd52ec1cf2e496a606ce28d8afb1c792f" not in address[0] \
                        and "0x64f0d720ce8b97ba44cd002005d2dfa3186c0580" not in address[0]\
                        and "0x0c8b740e3377f2be7a108aeba6a2f660588c728d" not in address[0]\
                        and "0x9e19462787be36e5e3676ad2428b26599bf9866c" not in address[0]\
                        and "0x44525c8dd44b9d470937cc9e7a0275eb14c7b01d" not in address[0]\
                        and "0xbfa82fbe0e66d8e2b7dcc16328db9ecd70533d13" not in address[0]\
                        and "0x8e1701e9509250d808eeca648feb1b8d7eed0704" not in address[0]\
                        and "0xb547027a4ccd46ec98199fa88aaedf5aa981db26" not in address[0]\
                        and "0xe0787aabbd6ee01e55f98647673552885d54eb06" not in address[0]\
                        and "0x54ff8a2d0a94d4652cfa0f91e1af092e718ffb1b" not in address[0]\
                        and "0x219b9040eb7d8d8c2e8e84b87ce9ac1c83071980" not in address[0]\
                        and "0x1bd913bbade46bf5ad8b1e5d117701fbeb078228" not in address[0]\
                        and "0x65440e4ce8a9a596a20ec8f910dfc8b1a20c5f7a" not in address[0]\
                        and "0x9477f48a278909a94d8cd9480dfa85d07103f004" not in address[0]\
                        and "0x4a008b542165fec7ec3343a35ceed6bc4f6b2280" not in address[0]\
                        and "0xf2effc1cd320ff062bae8649d150dbea3cb6b189" not in address[0]\
                        and "0x4711c198e6f04c02413794568990b6a835e8ead9" not in address[0]\
                        and "0xb507ebc4c6b65a11502fe5f20f8ceebc7e155fb4" not in address[0]\
                        and "0xb15882a04e840946cb12b41bd070dfe7b1486f93" not in address[0]\
                        and "0xb197af2df029e3367316adbea2f871fdb011ccca" not in address[0]\
                        and "0xa77db707916adeff81042ca57656931ccd8f428e" not in address[0]\
                        and "0x964432e4cfdf1463167d21815bcf9463cf19ea49" not in address[0]\
                        and "0xeb17037df15f171163d82c586c5b65ef112924ca" not in address[0]\
                        and "0x388cf3c02c034e7fe8ef164a2b414534fc212119" not in address[0]\
                        and "0x02fd82cba3bae39484d5eb7f75b5f3d5f418c691" not in address[0]\
                        and "0x514efa2ecc1be6228e46f45999dee7f1e9ed7b9a" not in address[0]\
                        and "0x1ea3ecc937bae79353d198db2cdab1e5cbe625dd" not in address[0]\
                        and "0x2306934ca884caa042dc595371003093092b2bbf" not in address[0]\
                        and "0x69bbf9a44b46083dad05d070422aaeafaca3204c" not in address[0]\
                        and "0x0913e0169f5129185c3934920d3cf6e5f56bd3be" not in address[0]\
                        and "0x27f97bc09a4e28d5935a08e2810b3e3c94f04220" not in address[0]\
                        and "0xff7c3b7f4e4260097a33c9dcc291b9d1baf2edb5" not in address[0]\
                        and "0x9c51699b4cd43ba4f6bc81d70b21291b63e6d130" not in address[0]\
                        and "0x5f5729010c873232f0ef6a68dca7455cc11de0e2" not in address[0]\
                        and "0xa2065164a26ecd3775dcf22510ad1d2daef8bd2a" not in address[0]\
                        and "0x113acf282eeb4d71bec61ad83e934bf75bf8253f" not in address[0]\
                        and "0x8f9a8dc65a423c7dec9261aa6010db738407c879" not in address[0]\
                        and "0x093fad33c3ff3534428fd18126235e1e44fa0d19" not in address[0]\
                        and "0x4c334f280f9e440788b66c4e5260c03e4477267a" not in address[0]\
                        and "0x3c0470b476aa3bf615bc828a6b2006aabab440da" not in address[0]\
                        and "0xb101f0eb0a8938769d4c3fd4f933b11627ca3768" not in address[0]\
                        and "0x02745ad75e786f0b2efbd99504e22c3cace354c1" not in address[0]\
                        and "0x52e8ebf98ef95d373d29041182830bf13c52588f" not in address[0]\
                        and "0x0aabebdabc7640410af5d901d4e460f174a4c946" not in address[0]\
                        and "0x34278f6f40079eae344cbac61a764bcf85afc949" not in address[0]\
                        and "0x2ceee24f8d03fc25648c68c8e6569aa0512f6ac3" not in address[0]\
                        and "0x6a7c5cc282a0a437eb6d7dc5beb304f961ac6411" not in address[0]\
                        and "0x003eb9c77b5b896fcc27adead606d23def34510e" not in address[0]\
                        and "0x1c3e61c8825bf58303b1ac3350843faa01de22bd" not in address[0]\
                        and "0x96036e9b51f03cabb6fe30daad1544a73f795efc" not in address[0]\
                        and "0x1412eca9dc7daef60451e3155bb8dbf9da349933" not in address[0]\
                        and "0xf9d25eb4c75ed744596392cf89074afaa43614a8" not in address[0]\
                        and "0x16b3dd2970ad3f19c6068c65777530830d33773e" not in address[0]\
                        and "0xf97bd29b8ee6e246eb57eecf5d0e8486366113fb" not in address[0]\
                        and "0xe44c8ee0622647d2563a8b2732941772328a751b" not in address[0]\
                        and "0x402db7bc77c259ce3fe639b1d5c6cd94eb35547c" not in address[0]\
                        and "0x4a96e9b57a229d94c0c28950355a72fa9e70aae3" not in address[0]\
                        and "0xefef14c36c1f2de2ca3772ba9539b6a58cfd562c" not in address[0]\
                        and "0x50228d83eeb60f31f6e58a0bd608228e9a17fe03" not in address[0]\
                        and "0xf2bad87c0d0ea8bda69c722368df4f79d92ee6c9" not in address[0]\
                        and "0x6642cec9d02e4e669103a3ed4f3505f437b8fe73" not in address[0]\
                        and "0x903bb9cd3a276d8f18fa6efed49b9bc52ccf06e5" not in address[0]\
                        and "0x70305B080eFc49eB5DFb9bdA78Aea516c398f804" not in address[0]\
                        and "0xe8868e87aaa4a0d0751691f9f33b0e5da7127039" not in address[0]\
                        and "0x6Ef982f9E7F09d4bF4a70398707c82970a6Dc31E" not in address[0]\
                        and "0x0d4f74c538613ed6e6c8c1bc8896ecfd45f5ef23" not in address[0]\
                        and "0x2bca419e570b1620b5e922fc005e806453affc83" not in address[0]\
                        and "0xe4ffd96b5e6d2b6cdb91030c48cc932756c951b5" not in address[0]\
                        and "0x34959919244b18128d084834dba11f0c91732ede" not in address[0]:
                    if int(address[3].strip("\n")) >= 50:
                        addresses.append(address[0])
    for n in range(396, 500):  # 500 fraudulent accounts
        print(f"Account{n + 1}: {addresses[n]}")
        """with open(f"account{n+1}.csv") as f:
            data = f.readlines()
            for line in data:
                line = line.split(",")
                if "0x" in line[0]:
                    tx_from = line[4]
                    tx_to = line[5]
                    value = line[9]
                    write(f"{n+1}-{addresses[n]}.csv", entry="{},{},{}".format(tx_from,tx_to,value))
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
        for _ in addresses:
            with open(f"export-{addresses[n]}.csv") as a:
                data = a.readlines()
                for line in data:
                    line = line.split(",")
                    if "0x" in line[0]:
                        value = line[9]
                        timestamp = line[2]
                        ent = "{},{}".format(timestamp, value)
                        write("val_normalized.csv", entry=ent)

        fraudulent = load_addresses()
        create_edges(fraudulent)
        create_nodes()

        print(f"Account{n + 1}: {addresses[n]}")
        create_graph(addresses[n])"""


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
                if int(address[4].strip("\n")) >= 50:
                    if "0x2faf487a4414fe77e2327f0bf4ae2a264a776ad2" not in address[1] \
                            and "0x267be1c1d684f78cb4f6a176c4911b741e4ffdc0" not in address[1] \
                            and "0x0d0707963952f2fba59dd06f2b425ace40b492fe" not in address[1] \
                            and "0x876eabf441b2ee5b5b0554fd502a8e0600950cfa" not in address[1] \
                            and "0x0a98fb70939162725ae66e626fe4b52cff62c2e5" not in address[1] \
                            and "0x2a0c0dbecc7e4d658f48e01e3fa353f44050c208" not in address[1] \
                            and "0xa910f92acdaf488fa6ef02174fb86208ad7722ba" not in address[1] \
                            and "0x0577a79cfc63bbc0df38833ff4c4a3bf2095b404" not in address[1] \
                            and "0x73f8fc2e74302eb2efda125a326655acf0dc2d1b" not in address[1] \
                            and "0xfbb1b73c4f0bda4f67dca266ce6ef42f520fbb98" not in address[1] \
                            and "0x4f6742badb049791cd9a37ea913f2bac38d01279" not in address[1] \
                            and "0xddfabcdc4d8ffc6d5beaf154f18b778f892a0740" not in address[1] \
                            and "0x0000000000000000000000000000000000000000" not in address[1] \
                            and "0x416299aade6443e6f6e8ab67126e65a7f606eef5" not in address[1] \
                            and "0xf5bec430576ff1b82e44ddb5a1c93f6f9d0884f3" not in address[1] \
                            and "0x00192fb10df37c9fb26829eb2cc623cd1bf599e8" not in address[1] \
                            and "0x829bd824b016326a401d083b33d092293333a830" not in address[1]:
                        addresses.append(address[1])
    for n in range(500):
        print(f"Account{n + 1}: {addresses[n]}")
        """with open(f"acc{n + 1}.csv") as f:
            data = f.readlines()
            for line in data:
                line = line.split(",")
                if "0x" in line[0]:
                    tx_from = line[4]
                    tx_to = line[5]
                    value = line[9]
                    write(f"honest_{n + 1}-{addresses[n]}.csv", entry="{},{},{}".format(tx_from, tx_to, value))
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
        for _ in addresses:
            with open(f"export-{addresses[n]}.csv") as a:
                data = a.readlines()
                for line in data:
                    line = line.split(",")
                    if "0x" in line[0]:
                        value = line[9]
                        timestamp = line[2]
                        ent = "{},{}".format(timestamp, value)
                        write("val_normalized.csv", entry=ent)

        fraudolent = load_addresses()
        create_edges(fraudolent)
        create_nodes()

        print(f"Account{n + 1}: {addresses[n]}")
        create_graph(addresses[n])"""


def main():
    fraudulent_graph()

    # honest_graph()


if __name__ == '__main__':
    main()
