import typing as tp
from itertools import chain, combinations


def get_graph(graph: tp.Dict[str, tp.Dict[str, tp.Any]]) -> tp.Dict[str, tp.List[str]]:
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


def find_cycles(graph: tp.Dict[str, tp.Dict[str, tp.Any]]) -> tp.Set[str]:
    new_graph = get_graph(graph)
    visited: tp.Dict[str, bool] = {key: False for key in new_graph}
    stack: tp.Dict[str, bool] = {key: False for key in new_graph}
    nodes_in_cycles: tp.Set[str] = set()

    def in_cycle(node: str) -> bool:
        visited[node] = True
        stack[node] = True
        flag = False

        for child_node in new_graph[node]:
            if not visited[child_node] and in_cycle(child_node):
                nodes_in_cycles.add(child_node)
                nodes_in_cycles.add(node)
                flag = True
            elif stack[child_node]:
                nodes_in_cycles.add(node)
                flag = True

        stack[node] = False
        return flag

    for node in new_graph:
        if not visited[node]:
            in_cycle(node)

    return nodes_in_cycles


def powerset(iterable):
    """
    Get all subsets
    :param iterable:
    :return:
    """
    s = list(iterable)
    return chain.from_iterable(combinations(s, r) for r in range(len(s) + 1))


def get_substrings(word: str) -> tp.Set[str]:
    """
    Get all possible word reductions
    :param word:
    :return:
    """
    first_letter, word = word[0], word[1:]
    result = set()
    for element in powerset(word):
        result.add(first_letter + ''.join(element))
        result.add(first_letter.upper() + ''.join(element))
    return {word for word in result if len(word) >= 3}
