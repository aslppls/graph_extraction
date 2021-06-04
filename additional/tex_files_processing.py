import re
import json
from glob import glob
import typing as tp
from itertools import chain, combinations

lemmas: tp.Dict[str, int] = {}
whole_line: tp.Dict[str, int] = {}

regex = re.compile(r'\\(begin|end){[^}]*}')


def find_lemmas_encounters(file_path: str):
    file = open(file_path)
    lines = iter(file)
    this_file_lemmas = set()

    while True:
        try:
            line = next(lines)
            for match in regex.finditer(line):
                substr = line[match.start(): match.end()]
                if substr not in this_file_lemmas:
                    if substr not in lemmas:
                        lemmas[substr] = 1
                    else:
                        lemmas[substr] += 1
                    this_file_lemmas.add(substr)
        except StopIteration:
            break


def powerset(iterable):
    s = list(iterable)
    return chain.from_iterable(combinations(s, r) for r in range(len(s) + 1))


def get_substrings(word: str) -> list:
    first_letter, word = word[0], word[1:]
    result = []
    for element in powerset(word):
        result.append(first_letter + ''.join(element))
        result.append(first_letter.upper() + ''.join(element))
    return result


def find_begin_end(file_path: str):
    theorem_words = get_substrings('theorem')
    lemma_words = get_substrings('lemma')
    theorem_words.extend(lemma_words)
    # regex_be = re.compile(r"\\(begin|end){(" + '|'.join(theorem_words) + r")}")
    regex_be = re.compile(r"\\ref{[^}]*}")

    file = open(file_path)
    lines = iter(file)
    this_file_lemmas = set()

    while True:
        try:
            line = next(lines)
            for match in regex_be.finditer(line):
                substr = line[match.start(): match.end()]
                if substr not in this_file_lemmas:
                    if substr not in lemmas:
                        lemmas[substr] = 1
                    else:
                        lemmas[substr] += 1
                    this_file_lemmas.add(substr)
        except StopIteration:
            break


if __name__ == '__main__':
    tex_files_directory = '../sources_tex/articles/'
    files = glob(tex_files_directory + '**/*.tex', recursive=True)

    for file in files:
        find_begin_end(file)

    lemmas = dict(sorted(lemmas.items(), key=lambda item: item[1]))
    with open("ref_info.json", "w") as outfile:
        json.dump(lemmas, outfile)
