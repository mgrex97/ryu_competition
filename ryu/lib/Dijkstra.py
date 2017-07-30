from collections import defaultdict

class Graph:
    def __init__(self):
        self.nodes = set()
        self.edges = defaultdict(list)
        self.distances = {}

    def set_node(self, value):
        self.nodes = set(value)

    def set_distance(self, from_node, to_node, distance):
        self.distances[(from_node, to_node)] = distance
        # self.distances[(to_node, from_node)] = distance

    def add_node(self, value):
        self.nodes.add(value)

    def add_edge(self, from_node, to_node, distance = 1):
        self.edges[from_node].append(to_node)
        # self.edges[to_node].append(from_node)
        self.set_distance(from_node, to_node, distance)

def dijsktra(graph, initial, ends):
    visited = {initial: 0}
    path = {}

    nodes = set(graph.nodes)
    
    while nodes:
        min_node = None
        for node in nodes:
            if node in visited:
                if min_node is None:
                    min_node = node
                elif visited[node] < visited[min_node]:
                    min_node = node

        if min_node is None:
            break

        nodes.remove(min_node)
        current_weight = visited[min_node]

        for edge in graph.edges[min_node]:
            weight = current_weight + graph.distances[(min_node, edge)]
            if edge not in visited or weight < visited[edge]:
                visited[edge] = weight
                path[edge] = min_node

    # print(path)
    if type(ends) is list :
        for end in ends:
            return get_way(path, initial, end)
    else:
        return get_way(path, initial, ends)
    # return path

def get_way(path, initial, end):
    if end not in path : return None
    way = []
    if path[end] != initial:
        way = get_way(path, initial, path[end])
    way.append(end)
    return way