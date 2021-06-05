import re
import json
from glob import glob
from pathlib import Path
from pyvis.network import Network
from algorithms import *


class LatexToGraph:
    def __init__(self, tex_files_directory: str, additional_words: tp.Optional[tp.List[str]] = None):
        self.structures_words = ['theorem', 'lemma', 'claim', 'corollary', 'proposition']

        if additional_words:
            self.structures_words.extend(additional_words)

        self.extended_words: tp.Set[str] = set()
        for word in self.structures_words:
            self.extended_words.update(get_substrings(word))

        self.extended_words.add('Th')
        if 'proof' in self.extended_words:
            self.extended_words.remove('proof')
        if 'example' in self.extended_words:
            self.extended_words.remove('example')

        self.newtheorem = "\\newtheorem{"
        self.statement_begin_regex = re.compile(r"\\begin{(" + '|'.join(self.extended_words) + ")}")
        self.statement_end_regex = re.compile(r"\\end{(" + '|'.join(self.extended_words) + ")}")
        self.proof_begin_regex = re.compile(r"\\begin{(proof|pf)}")
        self.proof_end_regex = re.compile(r"\\end{(proof|pf)}")
        self.reference_regex = re.compile(r"\\ref{(" + '|'.join(self.extended_words) + ")[^}]*}")
        self.equation_regex = re.compile(r"\\begin{(equation|eq)}")
        self.equation_reference_regex = re.compile(r"\\eqref{[^}]*}")

        self.file_path = tex_files_directory
        self.files = glob(self.file_path + '**/*.tex', recursive=True)
        self.lines: tp.Iterable
        self.line = ""
        self.current_index = 0

        self.elements: tp.Dict[str, tp.Dict[str, tp.Any]] = {}
        self.file_name = ""

    def create_graph(self):
        for file in self.files:
            self.get_labels_from_newtheorem(file)
            self.line = ""
            self.current_index = 0

            self.get_all_theorems(file)
            self.get_graph()

    def __get_next_line(self) -> None:
        self.line = next(self.lines)
        self.current_index += 1

        while self.line.isspace():
            self.line = next(self.lines)
            self.current_index += 1

    def get_labels_from_newtheorem(self, file_path: str):
        """
        Get all naming of elements from \newtheorem{}
        :param file_path:
        :return:
        """

        file = open(file_path)
        self.lines = iter(file)

        while True:
            try:
                self.__get_next_line()

                if self.line.find(self.newtheorem) != -1 and self.line.find('}'):
                    position = self.line.find(self.newtheorem)
                    naming = self.line[position + len(self.newtheorem):self.line.find('}') + position]

                    self.extended_words.add(naming)
            except StopIteration:
                break

    # TODO: add cite processing
    # TODO: make more options: get graph of current theorem parents
    def get_all_theorems(self, file_path: str) -> None:
        """

        :param file_path: path to the file being processed
        :return:
        """

        file = open(file_path)
        self.lines = iter(file)

        self.file_name = "/".join(file_path.split("/")[1:])[:-4]
        equations: tp.Dict[str, str] = {}

        graph_description: tp.Dict[str, tp.Any] = {
            "most_important": [],
            "number_of_child": 0,
            "most_dependable": [],
            "number_of_parents": 0,
            "name": file_path.split("/")[-1]
        }

        default_element_description = {
            "start_position": 0,
            "dependent_on": []
        }

        self.__get_next_line()

        def get_one_theorem() -> None:
            # если нашли начало доказательства, которое идёт не строго за формулировкой
            if self.proof_begin_regex.search(self.line) and self.reference_regex.search(self.line):
                element_name = ""
                for element in self.reference_regex.finditer(self.line):
                    element_name = self.line[element.start() + 5:element.end() - 1]
                    break
                while not self.proof_end_regex.search(self.line):
                    self.__get_next_line()

                    for element in self.reference_regex.finditer(self.line):
                        dependency_name = self.line[element.start() + 5:element.end() - 1]
                        if dependency_name != element_name:
                            self.elements[element_name]["dependent_on"].append(dependency_name)
            # если нашли начало формулировки
            elif self.statement_begin_regex.search(self.line):
                element_name = ""

                element_description = {
                    "start_position": 0,
                    "dependent_on": [],
                    "is_cite": False
                }

                # trying to find label in current line
                if re.search('label{', self.line):
                    pos = self.line.find("label{")
                    element_name = self.line[pos + 6:self.line[pos:].find("}") + pos]
                    element_description["start_position"] = self.current_index

                    if self.line.find("\cite") != -1:
                        element_description["is_cite"] = True

                # trying to find label in next line
                else:
                    self.__get_next_line()

                    if re.search('label{', self.line):
                        pos = self.line.find("label{")
                        element_name = self.line[pos + 6:self.line[pos:].find("}") + pos]
                        element_description["start_position"] = self.current_index

                        if self.line.find("\cite") != -1:
                            element_description["is_cite"] = True

                    # if no label found, create default name
                    else:
                        element_name = 'unlabeled_' + str(self.current_index - 1)
                        element_description["start_position"] = self.current_index - 1

                # trying to find proof
                while not self.proof_begin_regex.search(self.line):
                    self.__get_next_line()

                    # if got not proof but new statement
                    if self.statement_begin_regex.search(self.line):
                        self.elements[element_name] = element_description
                        return

                while not self.proof_end_regex.search(self.line):
                    self.__get_next_line()

                    if self.equation_regex.search(self.line):
                        if self.line.find("label{") != -1:
                            pos = self.line.find("label{")
                            eq_name = self.line[pos + 6:self.line[pos:].find("}") + pos]
                            equations[eq_name] = element_name

                    for element in self.reference_regex.finditer(self.line):
                        dependency_name = self.line[element.start() + 5:element.end() - 1]
                        if dependency_name != element_name:
                            element_description["dependent_on"].append(dependency_name)

                    for element in self.equation_reference_regex.finditer(self.line):
                        x, y = element.start(), element.end()
                        dependency_name = self.line[element.start() + 7:element.end() - 1]
                        if dependency_name in equations and equations[dependency_name] != element_name:
                            element_description["dependent_on"].append(equations[dependency_name])

                self.elements[element_name] = element_description

            self.__get_next_line()

        while True:
            try:
                get_one_theorem()
            except StopIteration:
                break

    def get_graph(self):
        in_cycle = find_cycles(self.elements)

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

            name_dir = 'visualization/' + "/".join(self.file_path.split("/")[1:-1])
            if name_dir != "":
                Path(name_dir).mkdir(parents=True, exist_ok=True)
            nt.save_graph(f'visualization/{self.file_name}.html')


if __name__ == '__main__':
    tex_files_directory = 'sources_tex/small_folder'

    ltg = LatexToGraph(tex_files_directory)
    ltg.create_graph()
