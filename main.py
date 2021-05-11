import re
import json
from glob import glob
from pathlib import Path
import typing as tp
from pyvis.network import Network

lemmas_without_proof = {}
line = ""
index = 0


def get_graph(graph: tp.Dict[str, tp.Dict[str, tp.Any]]) -> tp.Dict[str, tp.List[str]]:
    new_graph: tp.Dict[str, tp.List[str]] = {}

    for node in graph:
        for parent_node in graph[node]["dependencies"]:
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


def get_all_theorems(file_path: str, visualize=True, save_description=True) -> None:
    file = open(file_path)
    name = "/".join(file_path.split("/")[1:])[:-4]
    ref = re.compile(r'\\ref{\b(lemma|theorem|lem|thm|pro)(?:(?!\bref\b).)*?\b}')
    lines = iter(file)
    global line
    line = next(lines)
    global index

    global lemmas_without_proof
    lemmas: tp.Dict[str, tp.Dict[str, tp.Any]] = {}

    description: tp.Dict[str, tp.Any] = {
        "most_important": [],
        "number_of_child": 0,
        "most_dependable": [],
        "number_of_parents": 0,
        "name": file_path.split("/")[-1]
    }

    def get_next_line() -> tp.Tuple[tp.Any, int]:
        global index
        index += 1
        return next(lines), index

    def get_one_theorem() -> None:
        global line
        global index

        if re.match(r'\\begin{(lemma|theorem|proposition|pro)}', line):
            lemma_name = ""
            lemma_json = {
                "start_position": 0,
                "has_proof": False,
                "dependencies": []
            }

            if re.search(r'\\label', line):
                pos = line.find("\label{")
                lemma_name = line[pos + 7:line[pos:].find("}") + pos]
                lemma_json["start_position"] = index
            else:
                line, index = get_next_line()
                if re.match(r'\\label', line):
                    lemma_name = line[line.find("{") + 1:line.find("}")]
                    lemma_json["start_position"] = index
                else:
                    lemma_name = 'unlabeled_' + str(index)
                    lemma_json["start_position"] = index

            while not re.match(r'\\begin{proof}', line):
                line, index = get_next_line()
                if re.match(r'\\begin{(lemma|theorem|proposition|pro)}', line):
                    lemmas_without_proof[lemma_name] = lemma_json
                    lemmas[lemma_name] = lemma_json
                    return

            lemma_json["has_proof"] = True

            while not re.match(r'\\end{proof}', line):
                line, index = get_next_line()
                for element in ref.finditer(line):
                    dep_name = line[element.start() + 5:element.end() - 1]
                    if dep_name != lemma_name:
                        lemma_json["dependencies"].append(dep_name)
            lemmas[lemma_name] = lemma_json

        line, index = get_next_line()

    while True:
        try:
            get_one_theorem()
        except StopIteration:
            break

    if save_description:
        for lemma in lemmas:
            if description["number_of_child"] < len(lemmas[lemma]["dependencies"]):
                description["number_of_child"] = len(lemmas[lemma]["dependencies"])
                description["most_important"] = [lemma]
            elif description["number_of_child"] == len(lemmas[lemma]["dependencies"]):
                description["most_important"].append(lemma)
            elif description["number_of_parents"] < len(lemmas[lemma]["dependencies"]):
                description["number_of_parents"] = len(lemmas[lemma]["dependencies"])
                description["most_dependable"] = [lemma]
            elif description["number_of_parents"] == len(lemmas[lemma]["dependencies"]):
                description["most_dependable"].append(lemma)

        with open("extracted_json_information/files_description.json", "a") as outfile:
            json.dump(description, outfile)
        with open("extracted_json_information/files_description.json", "a") as outfile:
            outfile.write(",\n")

    in_cycle = find_cycles(lemmas)

    if lemmas:
        node_style = {"borderWidth": 4, "color": "blue"}

        nt = Network(height='900px', width='100%', directed=True)
        all_lemmas: tp.Dict[str, int] = {}

        for i, node in enumerate(lemmas):
            node_style["color"] = "blue"
            if node in in_cycle:
                node_style["color"] = "red"
            nt.add_node(i, node, **node_style)
            all_lemmas[node] = i

        for child_node in lemmas:
            for parent_node in lemmas[child_node]["dependencies"]:
                if parent_node not in lemmas and parent_node not in all_lemmas:
                    all_lemmas[parent_node] = len(all_lemmas)
                    node_style["color"] = "green"
                    nt.add_node(len(all_lemmas) - 1, parent_node, **node_style)
                edge = (all_lemmas[parent_node], all_lemmas[child_node])
                nt.add_edge(*edge)

        if visualize:
            name_dir = 'visualization/' + "/".join(file_path.split("/")[1:-1])
            if name_dir != "":
                Path(name_dir).mkdir(parents=True, exist_ok=True)
            nt.save_graph(f'visualization/{name}.html')


if __name__ == '__main__':
    save_descr = False
    get_graphs = True
    tex_files_directory = 'sources_tex/'
    files = glob(tex_files_directory + '**/*.tex', recursive=True)

    if save_descr:
        with open("extracted_json_information/files_description.json", "w") as outfile:
            outfile.write("[\n")

        for i, file_path in enumerate(files):
            get_all_theorems(file_path, get_graphs, True)

        with open("extracted_json_information/files_description.json", "a") as outfile:
            outfile.write("]\n")

        # with open("extracted_json_information/lemmas.json", "w") as outfile:
        #     json.dump(lemmas, outfile)
    else:
        for i, file_path in enumerate(files):
            get_all_theorems(file_path, get_graphs, False)
