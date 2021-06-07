import re
import json
from glob import glob
from pathlib import Path
from pyvis.network import Network
from .algorithms import *
from statistics import median
from collections import deque


class FileInfo:
    def __init__(self, file_path: str, extracted_info_directory: str):
        """

        :param file_path: file path
        :param extracted_info_directory: directory of graph parameters files
        """
        self.line = ""
        self.current_index = 0

        self.elements: tp.Dict[str, tp.Dict[str, tp.Any]] = {}
        self.file_path = file_path

        clean_file_path = ".".join(self.file_path.split(".")[:-1])
        clean_file_path = "/".join(clean_file_path.split("/")[1:])
        self.name_dir = extracted_info_directory + clean_file_path + "/"

        if self.name_dir != "":
            Path(self.name_dir).mkdir(parents=True, exist_ok=True)

    def open_file(self):
        """
        opens file for read
        :return:
        """
        file = open(self.file_path)
        self.lines = iter(file)
        self.line = ""
        self.current_index = 0

    def get_next_line(self) -> None:
        """
        gets next line
        :return:
        """
        self.line = next(self.lines)
        self.current_index += 1

        while self.line.isspace():
            self.line = next(self.lines)
            self.current_index += 1

    def save_graph(self) -> None:
        """

        :return:
        """
        graph = get_graph(self.elements)
        in_cycle = find_cycles(graph)

        try:

            if self.elements:
                node_style = {"borderWidth": 4, "color": "blue"}

                nt = Network(height='900px', width='100%', directed=True)
                all_lemmas: tp.Dict[str, int] = {}

                for i, node in enumerate(self.elements):
                    node_style["color"] = "blue"
                    if node in in_cycle:
                        node_style["color"] = "red"

                    if self.elements[node]["is_cite"]:
                        node_style["color"] = "orange"

                    nt.add_node(i, node, **node_style)
                    all_lemmas[node] = i

                for child_node in self.elements:
                    for parent_node in self.elements[child_node]["dependent_on"]:
                        if parent_node not in self.elements and parent_node not in all_lemmas:
                            all_lemmas[parent_node] = len(all_lemmas)
                            node_style["color"] = "green"
                            nt.add_node(len(all_lemmas) - 1, parent_node, **node_style)
                        edge = (all_lemmas[parent_node], all_lemmas[child_node])
                        nt.add_edge(*edge)

                # save visualization of graph
                nt.save_graph(self.name_dir + 'visualization.html')
        except:
            print("Exception during graph visualization. Visualization wasn't saved")

        # save raw graph
        with open(self.name_dir + 'graph.json', "w") as output_file:
            json.dump(graph, output_file)

    def get_basic_graph_properties(self):
        graph_properties = {
            "vertex_with_most_in_degree": None,
            "max_in_degree": None,
            "vertex_with_most_out_degree": None,
            "max_out_degree": None,
            "mean_vertex_degree": None,
            "median_vertex_degree": None,
            "mean_vertex_degree_without_isolated": None,
            "median_vertex_degree_without_isolated": None,
        }

        max_in_degree = 0
        max_in_degree_elements = []
        for element, keys in self.elements.items():
            if len(keys["dependent_on"]) > max_in_degree:
                max_in_degree_elements = [element]
                max_in_degree = len(keys["dependent_on"])
            elif len(keys["dependent_on"]) == max_in_degree:
                max_in_degree_elements.append(element)

        graph_properties["vertex_with_most_in_degree"] = max_in_degree_elements
        graph_properties["max_in_degree"] = max_in_degree

        graph = get_graph(self.elements)

        max_out_degree = 0
        max_out_degree_elements = []
        for element, keys in graph.items():
            if len(keys) > max_out_degree:
                max_out_degree_elements = [element]
                max_out_degree = len(keys)
            elif len(keys) == max_out_degree:
                max_out_degree_elements.append(element)

        graph_properties["vertex_with_most_out_degree"] = max_out_degree_elements
        graph_properties["max_out_degree"] = max_out_degree

        degrees = [len(key) for _, key in graph.items()]

        graph_properties["mean_vertex_degree"] = sum(degrees) / len(degrees)
        graph_properties["median_vertex_degree"] = median(degrees)

        degrees_non_zero = [degree for degree in degrees if degree != 0]

        if len(degrees_non_zero) != 0:
            graph_properties["mean_vertex_degree_without_isolated"] = sum(degrees_non_zero) / len(degrees_non_zero)
            graph_properties["median_vertex_degree_without_isolated"] = median(degrees_non_zero)

        with open(self.name_dir + 'graph_properties.json', "w") as output_file:
            json.dump(graph_properties, output_file)


class TexToGraph:
    def __init__(self, tex_files_directory: str = "source_files/",
                 extracted_info_directory: str = "extracted_information/",
                 additional_statement_words: tp.Optional[tp.Set[str]] = None,
                 unwanted_statement_words: tp.Optional[tp.Set[str]] = None,
                 additional_begin_statement_commands: tp.Optional[tp.Set[str]] = None,
                 additional_end_statement_commands: tp.Optional[tp.Set[str]] = None,
                 additional_begin_proof_commands: tp.Optional[tp.Set[str]] = None,
                 additional_end_proof_commands: tp.Optional[tp.Set[str]] = None):

        """

        :param tex_files_directory: directory of latex files
        :param visualization_directory: directory of graph visualization files
        :param extracted_graph_info_directory: directory of graph parameters files
        :param additional_statement_words: words to add to search inside brackets of commands \\begin{}, \\end{},
               while searching for statement blocks
        :param unwanted_statement_words: words to exclude from search inside brackets of commands \\begin{}, \\end{},
               while searching for statement blocks
        :param additional_begin_statement_commands: full commands like "\\begin{$word$}" to search for the beginning of
               statement block,
        :param additional_end_statement_commands: full commands like "\\end{$word$}" to search for the ending of
               statement block,
        :param additional_begin_proof_commands: full commands like "\\begin{$word$}" to search for the beginning of
               proof block
        :param additional_end_proof_commands: full commands like "\\end{$word$}" to search for the ending of
               proof block
        """

        self.structures_words = ['theorem', 'lemma', 'claim', 'corollary', 'proposition']

        self.extended_words: tp.Set[str] = set()
        for word in self.structures_words:
            self.extended_words.update(get_substrings(word))

        if additional_statement_words:
            self.extended_words.update(additional_statement_words)

        if unwanted_statement_words:
            for word in unwanted_statement_words:
                if word in self.extended_words:
                    self.extended_words.remove(word)

        self.extended_words.add('Th')

        self.newtheorem = "\\newtheorem{"

        if additional_begin_statement_commands:
            self.statement_begin_regex = re.compile(
                r"\\(begin{(" + '|'.join(self.extended_words) + "[^}]*)})|" + '|'.join(
                    additional_begin_statement_commands))
        else:
            self.statement_begin_regex = re.compile(
                r"\\(begin{(" + '|'.join(self.extended_words) + "[^}]*)})")

        if additional_end_statement_commands:
            self.statement_end_regex = re.compile(
                r"\\end{(" + '|'.join(self.extended_words) + ")}|" + '|'.join(additional_end_statement_commands))
        else:
            self.statement_end_regex = re.compile(
                r"\\end{(" + '|'.join(self.extended_words) + ")}")

        if additional_begin_proof_commands:
            self.proof_begin_regex = re.compile(r"\\begin{(proof|pf)}|" + '|'.join(additional_begin_proof_commands))
        else:
            self.proof_begin_regex = re.compile(r"\\begin{(proof|pf)}")

        if additional_end_proof_commands:
            self.proof_end_regex = re.compile(r"\\end{(proof|pf)}|" + '|'.join(additional_end_proof_commands))
        else:
            self.proof_end_regex = re.compile(r"\\end{(proof|pf)}")

        self.reference_regex = re.compile(r"\\ref{(" + '|'.join(self.extended_words) + ")[^}]*}")
        self.short_reference_regex = re.compile(r"\\ref{[^}]*}")
        self.equation_regex = re.compile(r"\\begin{(equation|eq)}")
        self.equation_reference_regex = re.compile(r"\\eqref{[^}]*}")

        self.file_path = tex_files_directory
        self.extracted_info_directory = extracted_info_directory
        self.files = glob(self.file_path + '**/*.tex', recursive=True)

    def create_graph(self):
        for file_path in self.files:
            file = FileInfo(file_path, self.extracted_info_directory)
            self.__get_labels_from_newtheorem(file)

            self.__get_all_theorems(file)
            file.save_graph()
            file.get_basic_graph_properties()

    def __get_labels_from_newtheorem(self, file: FileInfo) -> None:
        """
        Get all naming of elements from \newtheorem{}
        :param file_path:
        :return:
        """

        file.open_file()

        while True:
            try:
                file.get_next_line()

                if file.line.find(self.newtheorem) != -1 and file.line.find('}'):
                    position = file.line.find(self.newtheorem)
                    naming = file.line[position + len(self.newtheorem):file.line.find('}') + position]

                    self.extended_words.add(naming)
            except StopIteration:
                break

    # TODO: make more options: get graph of current theorem parents
    def __get_all_theorems(self, file: FileInfo) -> None:
        """
        Extract all information about elements and dependencies
        :param file: object that controls file
        :return:
        """

        file.open_file()

        equations: tp.Dict[str, str] = {}

        default_element_description = {
            "start_position": 0,
            "dependent_on": []
        }

        file.get_next_line()

        def get_one_theorem() -> None:
            # if proof was found that doesn't strictly follow the statement
            if self.proof_begin_regex.search(file.line) and self.short_reference_regex.search(file.line):
                element_name = ""
                for element in self.short_reference_regex.finditer(file.line):
                    element_name = file.line[element.start() + 5:element.end() - 1]
                    break
                while not self.proof_end_regex.search(file.line):
                    file.get_next_line()

                    for element in self.short_reference_regex.finditer(file.line):
                        dependency_name = file.line[element.start() + 5:element.end() - 1]

                        if dependency_name != element_name and dependency_name in file.elements:
                            file.elements[element_name]["dependent_on"].append(dependency_name)

                    if self.equation_regex.search(file.line):
                        if file.line.find("label{") != -1:
                            pos = file.line.find("label{")
                            eq_name = file.line[pos + 6:file.line[pos:].find("}") + pos]
                            equations[eq_name] = element_name

                    for element in self.equation_reference_regex.finditer(file.line):
                        dependency_name = file.line[element.start() + 7:element.end() - 1]
                        if dependency_name in equations and equations[dependency_name] != element_name:
                            file.elements[element_name]["dependent_on"].append(equations[dependency_name])
            # if statement found
            elif self.statement_begin_regex.search(file.line):
                element_name = ""

                element_description = {
                    "start_position": 0,
                    "dependent_on": [],
                    "is_cite": False
                }

                # trying to find label in current line
                if file.line.find("\cite") != -1:
                    element_description["is_cite"] = True

                if re.search('label{', file.line):
                    pos = file.line.find("label{")
                    element_name = file.line[pos + 6:file.line[pos:].find("}") + pos]
                    element_description["start_position"] = file.current_index

                # trying to find label in next line
                else:
                    file.get_next_line()

                    if re.search('label{', file.line):
                        pos = file.line.find("label{")
                        element_name = file.line[pos + 6:file.line[pos:].find("}") + pos]
                        element_description["start_position"] = file.current_index

                        if file.line.find("\cite") != -1:
                            element_description["is_cite"] = True

                    # if no label found, create default name
                    else:
                        element_name = 'unlabeled_' + str(file.current_index - 1)
                        element_description["start_position"] = file.current_index - 1

                # trying to find proof
                while not self.proof_begin_regex.search(file.line):
                    file.get_next_line()

                    # if got not proof but new statement
                    if self.statement_begin_regex.search(file.line):
                        file.elements[element_name] = element_description
                        return

                # if proof was found that doesn't strictly follow the statement
                if self.proof_begin_regex.search(file.line) and self.short_reference_regex.search(file.line):
                    file.elements[element_name] = element_description
                    return

                while not self.proof_end_regex.search(file.line):
                    file.get_next_line()

                    for element in self.short_reference_regex.finditer(file.line):
                        dependency_name = file.line[element.start() + 5:element.end() - 1]

                        if dependency_name != element_name and dependency_name in file.elements:
                            element_description["dependent_on"].append(dependency_name)

                    if self.equation_regex.search(file.line):
                        if file.line.find("label{") != -1:
                            pos = file.line.find("label{")
                            eq_name = file.line[pos + 6:file.line[pos:].find("}") + pos]
                            equations[eq_name] = element_name

                    for element in self.equation_reference_regex.finditer(file.line):
                        dependency_name = file.line[element.start() + 7:element.end() - 1]
                        if dependency_name in equations and equations[dependency_name] != element_name:
                            element_description["dependent_on"].append(equations[dependency_name])

                file.elements[element_name] = element_description

            file.get_next_line()

        while True:
            try:
                get_one_theorem()
            except StopIteration:
                break


class Graph:
    def __init__(self, file_path: str) -> None:
        """

        :param file_path: path to json file containing graph description
        """

        self.graph = {}

        try:
            with open(file_path, "r") as file:
                self.graph = json.load(file)
        except:
            print("Something wrong with file path or file itself")

        self.name_dir = "/".join(file_path.split("/")[:-1]) + '/'
        self.matrix_graph = get_matrix_graph(self.graph)

    def get_parents(self, element_name: str):
        subgraph_elements = {element_name}
        to_visit = deque()
        to_visit.append(element_name)

        while len(to_visit) != 0:
            next_parent = to_visit.popleft()
            for parent in self.matrix_graph[next_parent]["parents"]:
                if parent not in subgraph_elements:
                    to_visit.append(parent)
                    subgraph_elements.add(parent)

        nt = Network(height='900px', width='100%', directed=True)
        all_lemmas: tp.Dict[str, int] = {}

        for i, node in enumerate(subgraph_elements):
            nt.add_node(i, node)
            all_lemmas[node] = i

        for node in subgraph_elements:
            for parent in self.matrix_graph[node]["parents"]:
                if parent in subgraph_elements:
                    edge = (all_lemmas[parent], all_lemmas[node])
                    nt.add_edge(*edge)

        nt.save_graph(self.name_dir + element_name + '_subgraph_visualization.html')
