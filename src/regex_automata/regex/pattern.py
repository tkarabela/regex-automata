from .flags import PatternFlag
from .match import Match
from regex_automata.regex.nfa_evaluator import NFAEvaluator
from ..errors import ParserError, PatternError, TokenizerError
from ..parser.ast_processor import ASTProcessor
from ..parser.ast_visualizer import ASTVisualizer
from ..parser.tokenizer import Tokenizer
from ..parser.parser import Parser
from .nfa_builder import NFABuilder
from ..automata.nfa_visualizer import NFAVisualizer


class Pattern:
    def __init__(self, pattern: str, flags: PatternFlag = PatternFlag.NOFLAG, epsilon_free: bool = True) -> None:
        try:
            tokenizer = Tokenizer(pattern, flags)
            self.tokens = list(tokenizer.get_tokens())
        except TokenizerError as e:
            msg = "\n".join([
                str(e),
                "",
                pattern,
                format("^", f">{e.string_pos+1}")
            ])
            raise PatternError(msg) from e

        try:
            parser = Parser(self.tokens)
            self.raw_ast = parser.parse()
        except ParserError as e:
            msg = "\n".join([
                str(e),
                "",
                pattern,
                format("^", f">{e.string_pos+1}")
            ])
            raise PatternError(msg) from e

        try:
            self.ast = ASTProcessor(self.raw_ast).get_processed_ast()
        except Exception as e:
            raise PatternError("AST processing failed") from e

        self.nfa = NFABuilder(self.ast).build(epsilon_free=epsilon_free)
        self.pattern = pattern
        self.flags = flags

    def render_nfa(self, output_path: str = "nfa.png") -> None:
        NFAVisualizer(self.nfa).render(output_path)

    def render_ast(self, output_path: str = "ast.png", raw: bool = False) -> None:
        ast = self.ast if not raw else self.raw_ast
        ASTVisualizer(ast).render(output_path)

    def fullmatch(self, text: str, start: int = 0, end: int | None = None) -> Match | None:
        end_ = end if end is not None else len(text)
        m = self.match(text, start, end)
        if m is not None and m.span[-1] != end_:
            m = None
        return m

    def match(self, text: str, start: int = 0, end: int | None = None) -> Match | None:
        evaluator = NFAEvaluator(self.nfa, self.flags)
        return evaluator.match(text, start, end)

    def search(self, text: str, start: int = 0, end: int | None = None) -> Match | None:
        # TODO implement this properly via automaton
        end_ = end if end is not None else len(text)
        for i in range(start, end_):
            m = self.match(text, i, end)
            if m is not None:
                return m
        return None
