
from .ast import AstNode, AstEmpty, AstConcatenation, AstUnion, AstRepetition, AstCharacterSet, AstIteration


class ASTProcessor:
    def __init__(self, raw_ast: AstNode) -> None:
        self.raw_ast = raw_ast

    def get_processed_ast(self) -> AstNode:
        return self.convert(self.raw_ast)

    def convert(self, node: AstNode) -> AstNode:
        match node:
            case AstEmpty():
                return self.convert_AstEmpty(node)
            case AstCharacterSet():
                return self.convert_AstCharacter(node)
            case AstIteration():
                return self.convert_AstIteration(node)
            case AstRepetition():
                return self.convert_AstRepetition(node)
            case AstUnion():
                return self.convert_AstUnion(node)
            case AstConcatenation():
                return self.convert_AstConcatenation(node)
            case _:
                raise NotImplementedError(f"Cannot convert node {node!r}")

    def convert_AstEmpty(self, node: AstEmpty) -> AstNode:
        return node

    def convert_AstCharacter(self, node: AstCharacterSet) -> AstNode:
        return node

    def convert_AstIteration(self, node: AstIteration) -> AstNode:
        return AstIteration(self.convert(node.u))

    def convert_AstRepetition(self, node: AstRepetition) -> AstNode:
        # implemented via AST transform
        # a{3,}  == "aaa(a)*"
        # a{,3}  == "|a|aa|aaa" == "|a(|a(|a)))"
        # a{3,5} == "aaa(a|aa)" == "aaa(|a(|(a))"

        root: AstNode
        if node.min == 0 and node.max is None:
            root = AstIteration(node.u)
        elif node.max is None:
            root = AstConcatenation(
                self.iterated_concatenation(node.u, node.min),
                AstIteration(node.u)
            )
        else:
            root = AstConcatenation(
                self.iterated_concatenation(node.u, node.min),
                self.iterated_prefix(node.u, node.max - node.min),
            )

        return self.convert(root)

    def convert_AstUnion(self, node: AstUnion) -> AstNode:
        return AstUnion(self.convert(node.u), self.convert(node.v))

    def convert_AstConcatenation(self, node: AstConcatenation) -> AstNode:
        return AstConcatenation(self.convert(node.u), self.convert(node.v))

    @staticmethod
    def iterated_concatenation(node: AstNode, n: int) -> AstNode:
        # 0 -> AstEmpty == ""
        # 1 -> AstConcatenation(AstEmpty, u) == "u"
        # 2 -> AstConcatenation(AstConcatenation(AstEmpty, u), u) == "uu"
        output: AstNode = AstEmpty()
        for _ in range(n):
            output = AstConcatenation(output, node.copy())
        return output

    @staticmethod
    def iterated_prefix(node: AstNode, n: int) -> AstNode:
        # 0 -> AstEmpty = ""
        # 1 -> AstUnion(AstEmpty, AstConcatenation(u, AstEmpty)) == "|u"
        # 2 -> AstUnion(AstEmpty, AstConcatenation(u, AstUnion(AstEmpty, AstConcatenation(u, AstEmpty)))) == "|u(|u)"
        output: AstNode = AstEmpty()
        for _ in range(n):
            output = AstUnion(
                AstEmpty(),
                AstConcatenation(node.copy(), output)
            )
        return output
