from source.tex_to_graph import TexToGraph, Graph
import typing as tp

if __name__ == "__main__":
    file_path = "extracted_information/00253/"
    graph = Graph(file_path)
    graph.get_parents('mainthm')


    file_path = "extracted_information/2101_26/"
    graph = Graph(file_path)
    graph.get_parents('f-lem3.5')
