import networkx as nx

tsp = nx.approximation.traveling_salesman_problem

# 1471
G = nx.complete_graph(1471)
print(G)
p = tsp(G)
print(p)
