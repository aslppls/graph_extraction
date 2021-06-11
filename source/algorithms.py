import typing as tp


def get_adjacency_list_graph(graph: tp.Dict[str, tp.Dict[str, tp.Any]]) -> tp.Dict[str, tp.List[str]]:
    """
    From adjacency list where each node is given a list of its parents makes
    adjacency list where each node is given a list of its children
    :param graph: inverse adjacency list
    :return: adjacency list
    """
    new_graph: tp.Dict[str, tp.List[str]] = {}

    for node in graph:
        for parent_node in graph[node]["dependent_on"]:
            if parent_node in new_graph:
                new_graph[parent_node].append(node)
            else:
                new_graph[parent_node] = [node]
        if node not in new_graph:
            new_graph[node] = []

    return new_graph


def get_matrix_graph(graph: tp.Dict[str, tp.List[str]]) -> tp.Dict[str, tp.Dict[str, tp.List[str]]]:
    """
    From adjacency list makes matrix representation of graph.
    :param graph: adjacency list
    :return: Output graph structure:
    {node_name: {
            children: [],
            parents: []
    }}
    """

    new_graph: tp.Dict[str, tp.Dict[str, tp.List[str]]] = {}

    for element, values in graph.items():
        new_graph[element] = {}
        new_graph[element]["children"] = values
        new_graph[element]["parents"] = []

    for element, values in graph.items():
        for child in values:
            new_graph[child]["parents"].append(element)

    return new_graph


def find_cycles(graph: tp.Dict[str, tp.List[str]]) -> tp.Set[str]:
    """

    :param graph: adjacency list
    :return: set of nodes that are part of cycles
    """
    visited: tp.Dict[str, bool] = {key: False for key in graph}
    stack: tp.Dict[str, bool] = {key: False for key in graph}
    nodes_in_cycles: tp.Set[str] = set()

    def in_cycle(node: str) -> bool:
        visited[node] = True
        stack[node] = True
        flag = False

        for child_node in graph[node]:
            if not visited[child_node] and in_cycle(child_node):
                nodes_in_cycles.add(child_node)
                nodes_in_cycles.add(node)
                flag = True
            elif stack[child_node]:
                nodes_in_cycles.add(node)
                flag = True

        stack[node] = False
        return flag

    for node in graph:
        if not visited[node]:
            in_cycle(node)

    return nodes_in_cycles
