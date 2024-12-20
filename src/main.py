import json
import os
import zipfile

import networkx as nx
import numpy as np
import pandas as pd
from kaggle.api.kaggle_api_extended import KaggleApi
from sklearn.metrics import adjusted_mutual_info_score, adjusted_rand_score

import algorithm.kcomm.graph_kClusterAlgorithm_functions as QCD
import algorithm.kcomm.graph_kClusterAlgorithm_functions_optimized as QCD_optimized
import algorithm.kcomm.graphFileUtility_functions as GFU


# Initialize and authenticate the Kaggle API
api = KaggleApi()
api.authenticate()

data_dir = "../data"
competition = 'cm4ai-community-detection-benchmark'
data_path = os.path.join(data_dir, competition)
os.makedirs(data_dir, exist_ok=True)

output_dir = "../output"
os.makedirs(output_dir, exist_ok=True)

# Download all files from a competition (e.g., Titanic)
competition = 'cm4ai-community-detection-benchmark'
api.competition_download_files(competition, path=data_dir, force=True)

# Extract all files from the zip to the specified directory
zip_file_path = data_path + ".zip"
with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
    zip_ref.extractall(data_path)

args_dict = {
    "benchmark_gen":"networkx",
    "output_dir" : output_dir
}

number_of_nodes_in_nx_benchmark = 1000
beta0 = 5
gamma0 = -250
threshold = 0.2
qsize = 64

run_profile="defaults"

if args_dict["benchmark_gen"] == 'karate':

    print(f"Using benchmark graph generated by: nx-karate")  
    
    run_label = "zacharys-karate-club"
    input_graph = "zacharys-karate-club"
    
    G = nx.karate_club_graph() 

    gt_arr = []
    gt_arr = [G.nodes[v]['club'] for v in G.nodes()]
    gt_arr = [0 if x == 'Mr. Hi' else 1 for x in gt_arr]        # Convert to binary labels


elif args_dict["benchmark_gen"] == 'networkx':
    
    print(f"Using benchmark graph generated by: networkx")    

    run_label = f"LFR_rs11_N{number_of_nodes_in_nx_benchmark}_ad5_mc20_mu0.1"
    input_graph = f"../data/cm4ai-community-detection-benchmark/{run_label}"

    G = nx.read_edgelist(f"{input_graph}.edgelist")

    df = pd.read_csv(f"{input_graph}_communities.csv")
    gt_dict = df.set_index('id')['solution'].to_dict()

    sorted_by_keys = dict(sorted(gt_dict.items()))
    gt_arr = []
    for k,v in sorted_by_keys.items():
        gt_arr.append(v)

elif args_dict["benchmark_gen"] == 'dynbench':

    print(f"Using benchmark graph generated by: Dynbench")    
    
    # n = Number of nodes per community
    # q = Number of communities
    run_label = "stdmerge-n32-q8-pout01.t00100"
    input_graph = f"../../data/cm4ai_community_detection/cm4ai-community-detection-benchmark/{run_label}.graph"
    ground_truth_path = f"../../data/cm4ai_community_detection/cm4ai-community-detection-benchmark/{run_label}.comms"

    edgelist = pd.read_csv(input_graph, sep=' ', names=["source","target"])
    G = nx.from_pandas_edgelist(edgelist)
    for edge in G.edges():
        G[edge[0]][edge[1]]['weight'] = 1

    gt_arr=[]
    with open(ground_truth_path) as ground_truth_file:
        for line in ground_truth_file:
            if line.startswith("#"):
                continue
            fields = line.strip().split(" ")
            gt_arr.append(fields[1])

A = nx.adjacency_matrix(G)
print ('\nAdjacency matrix:\n', A.todense())

num_parts = len(np.unique(gt_arr))
num_blocks = num_parts 
num_nodes = nx.number_of_nodes(G)
num_edges = nx.number_of_edges(G)
print (f"\nQuantum Community Detection: Up to {num_parts} communities")
print (f"Graph has {num_nodes} nodes and {num_edges} edges")

beta, gamma, GAMMA  = QCD.set_penalty_constant(num_nodes, num_blocks, beta0, gamma0)

mtotal, modularity = QCD.build_mod(A, threshold, num_edges)
print ("\nModularity matrix: \n", modularity)

print ("min value = ", modularity.min())
print ("max value = ", modularity.max())

print ("threshold = ", threshold)

Q_optimized = QCD_optimized.makeQubo(modularity, beta, gamma, GAMMA, num_nodes, num_parts, num_blocks, threshold)

print(Q_optimized)