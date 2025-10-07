from ..parser.tokenizer import Tokenizer
from ..parser.parser import Parser
from ..automata.nfa import NFA
from .nfa_builder import NFABuilder
from ..automata.nfa_visualizer import NFAVisualizer


class Regex:
    def __init__(self, pattern: str, nfa: NFA) -> None:
        self.pattern = pattern
        self.nfa = nfa

    @classmethod
    def from_pattern(cls, pattern: str) -> "Regex":
        tokenizer = Tokenizer(pattern)
        tokens = list(tokenizer.get_tokens())
        parser = Parser(tokens)
        root = parser.parse()
        print(root)
        nfa = NFABuilder(root).build()
        return cls(pattern=pattern, nfa=nfa)

    def save_png(self, output_path: str) -> None:
        NFAVisualizer(self.nfa).to_png(output_path)

    def fullmatch(self, s: str) -> bool:
        return self.nfa.accepts(s)

    def match(self, s: str) -> bool:
        raise NotImplementedError("TODO bonus I")

    def search(self, s: str) -> bool:
        raise NotImplementedError("TODO bonus II")
