import re
import json
from glob import glob
from pathlib import Path
import typing as tp
from pyvis.network import Network
from algorithms import *

# Getting all possible 'theorem' and 'lemma' reductions that can be used as markers
theorem_words = get_substrings('theorem')
lemma_words = get_substrings('lemma')
theorem_words.extend(lemma_words)

# Getting all needed regex
statement_begin_regex = re.compile(r"\\begin{(" + '|'.join(theorem_words) + ")}")
statement_end_regex = re.compile(r"\\end{(" + '|'.join(theorem_words) + ")}")
proof_begin_regex = re.compile(r"\\begin{proof}")
proof_end_regex = re.compile(r"\\end{proof}")
reference_regex = re.compile(r"\\ref{[^}]*}")

line = ""
index = 0


#TODO: make code more readable
#TODO: fix indexes
#TODO: match->search
#TODO: add cite processing
#TODO: make more options: get graph of current theorem parents
def get_all_theorems(file_path: str, visualize=True, save_description=True) -> None:
    """

    :param file_path: path to the file being processed
    :param visualize: True if save visualized graphs
    :param save_description: Get basic information about graph
    :return:
    """

    file = open(file_path)
    name = "/".join(file_path.split("/")[1:])[:-4]

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

        if statement_begin_regex.search(line):
            lemma_name = ""
            lemma_json = {
                "start_position": 0,
                "has_proof": False,
                "dependencies": []
            }

            if re.search('label{', line):
                pos = line.find("label{")
                lemma_name = line[pos + 6:line[pos:].find("}") + pos]
                lemma_json["start_position"] = index
            else:
                line, index = get_next_line()
                if re.match(r'label{', line):
                    lemma_name = line[line.find("{") + 1:line.find("}")]
                    lemma_json["start_position"] = index
                else:
                    lemma_name = 'unlabeled_' + str(index)
                    lemma_json["start_position"] = index

            while not proof_begin_regex.search(line):
                line, index = get_next_line()
                if statement_begin_regex.search(line):
                    lemmas[lemma_name] = lemma_json
                    return

            lemma_json["has_proof"] = True

            while not proof_end_regex.search(line):
                line, index = get_next_line()
                for element in reference_regex.finditer(line):
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
