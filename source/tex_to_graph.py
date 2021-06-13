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
        self.single_file = True

        if self.name_dir != "":
            Path(self.name_dir).mkdir(parents=True, exist_ok=True)

        self.has_numbering = False

        self.groups = {
            'chapter': 1,
            'section': 2,
            'subsection': 3,
            'subsubsection': 4,
        }

        self.next_group = 5

        self.dependencies_parents = {
            'chapter': [2],
            'section': [3],
            'subsection': [4]
        }

        self.current_numeration = {

        }

    def open_file(self):
        """
        Opens file for read
        :return:
        """
        file = open(self.file_path)
        self.lines = iter(file)
        self.line = ""
        self.current_index = 0

    def get_next_line(self) -> None:
        """
        Gets next line
        :return:
        """
        self.line = next(self.lines)
        self.current_index += 1

        while self.line.isspace():
            self.line = next(self.lines)
            self.current_index += 1

    def check_sections(self):
        self.open_file()
        sections1 = re.compile(r'\\begin{(chapter|section|subsection|subsubsection)}')
        sections2 = re.compile(r'\\(chapter|section|subsection|subsubsection)')
        found_sections = set()

        while True:
            try:
                self.get_next_line()

                if sections1.search(self.line):
                    x = self.line.find('{')
                    y = self.line.find('}')
                    name = self.line[x + 1:y]
                    found_sections.add(name)
                elif sections2.search(self.line):
                    x = self.line.find('\\')
                    y = self.line.find('{')
                    name = self.line[x + 1:y]
                    found_sections.add(name)
            except StopIteration:
                break

        numbering = ''
        for element in ['chapter', 'section', 'subsection', 'subsubsection']:
            if element in found_sections:
                self.current_numeration[self.groups[element]] = numbering + '0'
                numbering += '0.'
            elif element in self.dependencies_parents:
                self.dependencies_parents.pop(element)

    def get_section_numberings(self):
        self.check_sections()

        self.open_file()
        regex_newtheorem = re.compile(r'\\newtheorem{[^}]*}')

        self.namings = {

        }

        while True:
            try:
                self.get_next_line()

                if regex_newtheorem.search(self.line):
                    self.has_numbering = True
                    x = self.line.find('{')
                    y = self.line.find('}')
                    vr = self.line[x + 1:y]
                    x = self.line.rfind('{')
                    y = self.line.rfind('}')
                    name = self.line[x + 1:y]
                    if '\\' in name:
                        name = ""
                    self.namings[vr] = name

                    # \newtheorem{}[]{} pattern
                    if re.search(r'\\newtheorem{[^}]*}[ \t\n]*\[', self.line):
                        x = self.line.find('[')
                        y = self.line.find(']')
                        parent = self.line[x + 1: y]
                        if parent not in self.groups:
                            self.groups[parent] = self.next_group
                            self.current_numeration[self.groups[parent]] = '0'
                            self.next_group += 1
                        self.groups[vr] = self.groups[parent]
                    # \newtheorem{}{}[] pattern
                    elif '%[' in self.line:
                        continue
                    elif '[' in self.line:
                        x = self.line.find('[')
                        y = self.line.find(']')
                        parent = self.line[x + 1: y]
                        self.groups[vr] = self.next_group

                        self.next_group += 1

                        if parent in self.dependencies_parents:
                            self.dependencies_parents[parent].append(self.groups[vr])
                        else:
                            self.dependencies_parents[parent] = [self.groups[vr]]

                        if parent not in self.current_numeration:
                            if parent not in self.groups:
                                self.groups[parent] = self.next_group
                                self.next_group += 1
                            self.current_numeration[self.groups[parent]] = '0'
                        self.current_numeration[self.groups[vr]] = str(
                            self.current_numeration[self.groups[parent]]) + '.0'
                    else:
                        self.groups[vr] = self.next_group
                        self.next_group += 1
                        self.current_numeration[self.groups[vr]] = '0'
            except StopIteration:
                break

    def update_numbering(self, argument: str) -> str:
        if argument[-1] == '*':
            return " "
        cur = self.current_numeration[self.groups[argument]]
        last_digit = int(cur.split('.')[-1])
        if cur.find('.') == -1:
            self.current_numeration[self.groups[argument]] = str(last_digit + 1)
        else:
            self.current_numeration[self.groups[argument]] = '.'.join(cur.split('.')[:-1]) + '.' + str(
                last_digit + 1)

        if argument in self.dependencies_parents:
            to_update = deque([(child, self.groups[argument]) for child in self.dependencies_parents[argument]])
            while len(to_update):
                group, parent = to_update.popleft()
                self.current_numeration[group] = self.current_numeration[parent] + '.0'
                for key, value in self.groups.items():
                    if value == group and key in self.dependencies_parents:
                        for child in self.dependencies_parents[key]:
                            to_update.append((child, group))
        return self.current_numeration[self.groups[argument]]

    def save_graph(self) -> None:
        """
        Creates graph as Network and saves its visualization
        :return:
        """

        graph = get_adjacency_list_graph(self.elements)
        in_cycle = find_cycles(graph)
        nodes_description: tp.Dict[str, tp.Dict[str, str]] = {}

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
                    nodes_description[node] = {"color": "", "full_name": ""}
                    nodes_description[node]["color"] = node_style["color"]
                    nodes_description[node]["full_name"] = self.elements[node]["full_name"]
                    nt.add_node(i, self.elements[node]["full_name"], **node_style)
                    all_lemmas[node] = i

                for child_node in self.elements:
                    for parent_node in self.elements[child_node]["dependent_on"]:
                        if parent_node not in self.elements and parent_node not in all_lemmas:
                            all_lemmas[parent_node] = len(all_lemmas)
                            node_style["color"] = "green"
                            nodes_description[parent_node] = {"color": "", "full_name": ""}
                            nodes_description[parent_node]["color"] = "green"
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

        with open(self.name_dir + 'nodes_description.json', "w") as output_file:
            json.dump(nodes_description, output_file)

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

        graph = get_adjacency_list_graph(self.elements)

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

        self.structure_words = {'theorem', 'thm', 'theo', 'mainthm', 'myTheo', 'teorema', 'theo', 'mytheorem',
                                'lemma', 'lem', 'Lemma', 'lemm', 'sublemma', 'lm', 'lmm', 'lmma', 'mylemma',
                                'claim', 'clm', 'myclaim',
                                'corollary', 'cor',
                                'proposition', 'prop', 'pro', 'propo', 'propris', 'myproposition',
                                'criterion',
                                }
        self.unwanted_statement_words = {'definition', 'defn', 'defin', 'dfn'
                                                                        'example', 'exam',
                                         'question', 'ques',
                                         'algorithm',
                                         'figure'}

        capital_letter_words = set()
        for word in self.structure_words:
            capital_letter_words.add(word.capitalize())
        self.structure_words.update(capital_letter_words)

        capital_letter_words = set()
        for word in self.unwanted_statement_words:
            capital_letter_words.add(word.capitalize())
        self.unwanted_statement_words.update(capital_letter_words)

        if unwanted_statement_words:
            self.unwanted_statement_words.update(unwanted_statement_words)

        for word in self.unwanted_statement_words:
            if word in self.structure_words:
                self.structure_words.remove(word)

        if additional_statement_words:
            self.structure_words.update(additional_statement_words)

        self.newtheorem = "\\newtheorem{"

        self.additional_begin_statement_commands = additional_begin_statement_commands
        self.additional_end_statement_commands = additional_end_statement_commands

        self.statement_begin_regex = re.compile('')
        self.statement_end_regex = re.compile('')

        if additional_begin_proof_commands:
            self.proof_begin_regex = re.compile(
                r"\\begin{(proof|pf|IEEEproof|Proof)}|" + '|'.join(additional_begin_proof_commands))
        else:
            self.proof_begin_regex = re.compile(r"\\begin{(proof|pf|IEEEproof|Proof)}")

        if additional_end_proof_commands:
            self.proof_end_regex = re.compile(r"\\end{(proof|pf)}|" + '|'.join(additional_end_proof_commands))
        else:
            self.proof_end_regex = re.compile(r"\\end{(proof|pf)}")

        self.reference_regex = re.compile(r"\\ref{(" + '|'.join(self.structure_words) + ")[^}]*}")
        self.short_reference_regex = re.compile(r"\\ref{[^}]*}")
        self.equation_regex = re.compile(r"\\begin{(equation|eq)}")
        self.equation_reference_regex = re.compile(r"\\eqref{[^}]*}")

        self.file_path = tex_files_directory
        self.extracted_info_directory = extracted_info_directory
        self.files = glob(self.file_path + '**/*.tex', recursive=True)

    def create_graph(self):
        for file_path in self.files:
            file = FileInfo(file_path, self.extracted_info_directory)
            self.__get_labels_from_newtheorem_commands(file)
            file.get_section_numberings()

            self.__get_all_theorems(file)
            self.__delete_unlabeled_without_dependencies(file)
            file.save_graph()
            file.get_basic_graph_properties()

    def __get_labels_from_newtheorem_commands(self, file: FileInfo) -> None:
        """
        Get all naming of elements from \newtheorem{}
        :param file:
        :return:
        """

        file.open_file()

        while True:
            try:
                file.get_next_line()

                if file.line.find(self.newtheorem) != -1 and file.line.find('}'):
                    position = file.line.find(self.newtheorem)
                    naming = file.line[position + len(self.newtheorem):file.line.find('}') + position]

                    if naming not in self.unwanted_statement_words:
                        self.structure_words.add(naming)
            except StopIteration:
                break

        if self.additional_begin_statement_commands:
            self.statement_begin_regex = re.compile(
                r"\\(begin{(" + '|'.join(self.structure_words) + "[^}]*)})|" + '|'.join(
                    self.additional_begin_statement_commands))
        else:
            self.statement_begin_regex = re.compile(
                r"\\(begin{(" + '|'.join(self.structure_words) + "[^}]*)})")

        if self.additional_end_statement_commands:
            self.statement_end_regex = re.compile(
                r"\\end{(" + '|'.join(self.structure_words) + ")}|" + '|'.join(self.additional_end_statement_commands))
        else:
            self.statement_end_regex = re.compile(
                r"\\end{(" + '|'.join(self.structure_words) + ")}")

    def __get_all_theorems(self, file: FileInfo) -> None:
        """
        Extract all information about elements and dependencies
        :param file: object that keeps information about file
        :return:
        """

        file.open_file()
        all_sections = set(file.groups.keys())
        reg_line1 = re.compile(r'\\begin{(' + '|'.join(all_sections) + ')}')
        reg_line2 = re.compile(r'\\(chapter|section|subsection|subsubsection)')
        equations: tp.Dict[str, str] = {}

        file.get_next_line()
        while file.line.find('\\begin{document}') == -1:
            file.get_next_line()

        def process_proof(element_name: str) -> None:
            # iterating through lines of proof
            while not self.proof_end_regex.search(file.line):
                # trying to find \ref{}
                for element in self.short_reference_regex.finditer(file.line):
                    dependency_name = file.line[element.start() + len('\\ref{'):element.end() - 1]

                    if dependency_name != element_name and dependency_name in file.elements:
                        file.elements[element_name]["dependent_on"].add(dependency_name)

                # if new equation is proposed in proof
                if self.equation_regex.search(file.line):
                    if file.line.find("label{") != -1:
                        pos = file.line.find("label{")
                        eq_name = file.line[pos + 6:file.line[pos:].find("}") + pos]
                        equations[eq_name] = element_name

                # trying to find equations that were proposed earlier in other proofs
                for element in self.equation_reference_regex.finditer(file.line):
                    dependency_name = file.line[element.start() + 7:element.end() - 1]
                    if dependency_name in equations and equations[dependency_name] != element_name:
                        file.elements[element_name]["dependent_on"].add(equations[dependency_name])
                file.get_next_line()

        def get_one_theorem() -> None:

            # if statement found
            if self.statement_begin_regex.search(file.line):
                element_name = ""

                element_description = {
                    "start_position": 0,
                    "dependent_on": set(),
                    "is_cite": False,
                    "full_name": ""
                }

                if file.has_numbering:
                    argument = file.line[file.line.find('{') + 1:file.line.find('}')]

                    current_number = file.update_numbering(argument)

                    element_description["full_name"] = file.namings[argument] + ' ' + current_number

                # trying to find label in current line
                if file.line.find("\cite") != -1:
                    element_description["is_cite"] = True

                if re.search('label{', file.line):
                    pos = file.line.find("label{")
                    element_name = file.line[pos + 6:file.line[pos:].find("}") + pos]
                    element_description["start_position"] = file.current_index
                    file.get_next_line()

                # trying to find label in next line
                else:
                    file.get_next_line()

                    if file.line.find("\cite") != -1:
                        element_description["is_cite"] = True

                    if re.search('label{', file.line):
                        pos = file.line.find("label{")
                        element_name = file.line[pos + 6:file.line[pos:].find("}") + pos]
                        element_description["start_position"] = file.current_index

                    # if no label found, create default name
                    else:
                        element_name = 'unlabeled_' + str(file.current_index - 1)
                        element_description["start_position"] = file.current_index - 1
                file.elements[element_name] = element_description
                file.elements[element_name]["full_name"] += '(' + element_name + ')'

                # trying to find proof
                while not self.proof_begin_regex.search(file.line):

                    # if got not proof but new statement
                    if self.statement_begin_regex.search(file.line) or reg_line1.search(file.line) or reg_line2.search(
                            file.line):
                        return
                    file.get_next_line()

                # if proof was found that doesn't strictly follow the statement
                if self.proof_begin_regex.search(file.line) and self.short_reference_regex.search(file.line):
                    return

                process_proof(element_name)

            # if proof was found that doesn't strictly follow the statement
            elif self.proof_begin_regex.search(file.line) and self.short_reference_regex.search(file.line):
                element_name = ""
                for element in self.short_reference_regex.finditer(file.line):
                    element_name = file.line[element.start() + 5:element.end() - 1]
                    break

                process_proof(element_name)
            elif file.has_numbering and reg_line1.search(file.line):
                argument = file.line[file.line.find('{') + 1:file.line.find('}')]
                file.update_numbering(argument)
            elif file.has_numbering and reg_line2.search(file.line):
                argument = file.line[file.line.find('\\') + 1:file.line.find('{')]
                file.update_numbering(argument)

            file.get_next_line()

        while True:
            try:
                get_one_theorem()
            except StopIteration:
                break

    def __delete_unlabeled_without_dependencies(self, file: FileInfo) -> None:
        elements_to_delete = []
        for element in file.elements:
            if element.startswith("unlabeled") and len(file.elements[element]["dependent_on"]) == 0:
                elements_to_delete.append(element)

        for element in elements_to_delete:
            file.elements.pop(element)


class Graph:
    def __init__(self, file_path: str) -> None:
        """

        :param file_path: path to json file containing graph description
        """

        self.graph = {}
        self.nodes = {}

        try:
            with open(file_path + 'graph.json', "r") as file:
                self.graph = json.load(file)
            with open(file_path + 'nodes_description.json', "r") as file:
                self.nodes = json.load(file)
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

        node_style = {"borderWidth": 4, "color": "blue"}

        for i, node in enumerate(subgraph_elements):
            node_style["color"] = self.nodes[node]["color"]
            nt.add_node(i, self.nodes[node]["full_name"], **node_style)
            all_lemmas[node] = i

        for node in subgraph_elements:
            for parent in self.matrix_graph[node]["parents"]:
                if parent in subgraph_elements:
                    edge = (all_lemmas[parent], all_lemmas[node])
                    nt.add_edge(*edge)

        nt.save_graph(self.name_dir + element_name + '_subgraph_visualization.html')
