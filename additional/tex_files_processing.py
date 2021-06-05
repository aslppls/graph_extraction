import re
import json
from glob import glob
from algorithms import *

lemmas: tp.Dict[str, int] = {}
whole_lines: tp.Dict[str, int] = {}
commands: tp.Dict[str, int] = {}

theorem_words = get_substrings('theorem')
lemma_words = get_substrings('lemma')
theorem_words.extend(lemma_words)
regex = re.compile(r'\\(begin|end){[^}]*}')
regex_be = re.compile(r"\\(begin|end){(" + '|'.join(theorem_words) + r")}")
regex_newtheorem = re.compile(r'\\newtheorem{[^}]*}')


def find_newtheorem(file_path: str):
    file = open(file_path)
    lines = iter(file)

    while True:
        try:
            line = next(lines)
            for match in regex_newtheorem.finditer(line):
                substr = line[match.start(): match.end()]
                if substr not in commands:
                    commands[substr] = 1
                else:
                    commands[substr] += 1
        except StopIteration:
            break
        except UnicodeDecodeError:
            continue


def find_begin_end(file_path: str):
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
                if line not in whole_lines:
                    whole_lines[line] = 1
                else:
                    whole_lines[line] += 1
        except StopIteration:
            break
        except UnicodeDecodeError:
            continue


if __name__ == '__main__':
    tex_files_directory = '../sources_tex/articles/'
    files = glob(tex_files_directory + '**/*.tex', recursive=True)

    for file in files:
        find_newtheorem(file)

    # lemmas = dict(sorted(lemmas.items(), key=lambda item: item[1]))
    # whole_lines = dict(sorted(lemmas.items(), key=lambda item: item[1]))
    #
    # with open("lines.json", "w") as outfile:
    #     json.dump(whole_lines, outfile)
    #
    # with open("info.json", "w") as outfile:
    #     json.dump(lemmas, outfile)

    commands = dict(sorted(commands.items(), key=lambda item: item[1]))
    with open("newtheorem.json", "w") as outfile:
        json.dump(commands, outfile)
