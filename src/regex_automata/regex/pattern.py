from .match import Match
from ..errors import ParserError, PatternError, TokenizerError
from ..parser.tokenizer import Tokenizer
from ..parser.parser import Parser
from .nfa_builder import NFABuilder
from ..automata.nfa_visualizer import NFAVisualizer


class Pattern:
    def __init__(self, pattern: str) -> None:
        try:
            tokenizer = Tokenizer(pattern)
            tokens = list(tokenizer.get_tokens())
        except TokenizerError as e:
            msg = "\n".join([
                str(e),
                "",
                pattern,
                format("^", f">{e.string_pos+1}")
            ])
            raise PatternError(msg) from e

        try:
            parser = Parser(tokens)
            self.ast = parser.parse()
        except ParserError as e:
            msg = "\n".join([
                str(e),
                "",
                pattern,
                format("^", f">{e.string_pos+1}")
            ])
            raise PatternError(msg) from e

        self.nfa = NFABuilder(self.ast).build()
        self.pattern = pattern

    def save_png(self, output_path: str) -> None:
        NFAVisualizer(self.nfa).to_png(output_path)

    def fullmatch(self, s: str) -> Match | None:
        if self.nfa.accepts(s):
            return Match()
        else:
            return None

    def match(self, s: str) -> Match | None:
        raise NotImplementedError  # TODO

    def search(self, s: str) -> Match | None:
        raise NotImplementedError  # TODO
