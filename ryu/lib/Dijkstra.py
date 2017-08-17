from collections import defaultdict

class Graph:
    def __init__(self):
        self.nodes = set()
        self.edges = defaultdict(list)
        self.distances = {}

    def init_edges(self):
        self.edges = defaultdict(list)
        self.distances = {}

    def set_node(self, value):
        self.nodes = set(value)

    def set_distance(self, from_node, to_node, distance, undirected=False):
        self.distances[(from_node, to_node)] = distance
        if undirected == True:
            self.distances[(to_node, from_node)] = distance

    def add_node(self, value):
        self.nodes.add(value)

    def add_edge(self, from_node, to_node, distance = 1, undirected=False):
        self.edges.setdefault(from_node, [])
        if to_node not in self.edges[from_node]:
            self.edges[from_node].append(to_node)
        if undirected == True:
            self.edges.setdefault(  to_node, [])
            if from_node not in self.edges[to_node]:
                self.edges[to_node].append(from_node)
        self.set_distance(from_node, to_node, distance, undirected)

    def del_node(self, value):
        if value in self.nodes:
            self.nodes.remove(value)
        self.edges.pop(value, None)
        for edge in self.edges:
            self.del_edge(edge, value)

    def del_edge(self, from_node, to_node, undirected=False):
        if to_node in self.edges[from_node] :
            self.edges[from_node].remove(to_node)
        if undirected == True:
            if from_node in self.edges[to_node] :
                self.edges[to_node].remove(from_node)
        self.del_distance(from_node, to_node)

    def del_distance(self, from_node, to_node, undirected=False):
        self.distances.pop((from_node, to_node), None)
        if undirected == True:
            self.distances.pop((to_node, from_node), None)

def dijsktra(graph, initial, end):
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

        # if found end then break
        if end in graph.edges[min_node]:
            weight = current_weight + graph.distances[(min_node, end)]
            visited[end] = weight
            path[end] = min_node
            break

        # if not find end then travel
        for edge in graph.edges[min_node]:
            weight = current_weight + graph.distances[(min_node, edge)]
            if edge not in visited or weight < visited[edge]:
                visited[edge] = weight
                path[edge] = min_node

    if initial not in path.values():
        return None
    else:

        way = get_way(path, initial, end)
        if way == None:
            return None
        way.insert(0,initial)
        return way

def get_way(path, initial, end):
    if end not in path: return None
    way = []
    if path[end] != initial:
        way = get_way(path, initial, path[end])
    way.append(end)
    return way
