from source.tex_to_graph import TexToGraph
import typing as tp

if __name__ == "__main__":
    additional_statement_words: tp.Optional[tp.Set[str]] = {'rem'}
    unwanted_statement_words: tp.Optional[tp.Set[str]] = None
    additional_begin_statement_commands: tp.Optional[tp.Set[str]] = None
    additional_end_statement_commands: tp.Optional[tp.Set[str]] = None
    additional_begin_proof_commands: tp.Optional[tp.Set[str]] = None
    additional_end_proof_commands: tp.Optional[tp.Set[str]] = None

    ttg = TexToGraph(
        additional_statement_words=additional_statement_words,
        unwanted_statement_words=unwanted_statement_words,
        additional_begin_statement_commands=additional_begin_statement_commands,
        additional_end_statement_commands=additional_end_statement_commands,
        additional_begin_proof_commands=additional_begin_proof_commands,
        additional_end_proof_commands=additional_end_proof_commands
    )

    ttg.create_graph()
