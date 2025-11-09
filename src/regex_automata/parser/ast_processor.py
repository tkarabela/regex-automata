
from .ast import AstNode, AstEmpty, AstConcatenation, AstUnion, AstRepetition, AstCharacterSet, AstIteration, \
    AstBoundaryAssertion, AstGroup


class ASTProcessor:
    def __init__(self, raw_ast: AstNode) -> None:
        self.raw_ast = raw_ast

    def get_processed_ast(self) -> AstNode:
        ast = self.convert(self.raw_ast)
        return AstGroup(0, ast)

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
            case AstBoundaryAssertion():
                return self.convert_AstBoundaryAssertion(node)
            case AstGroup():
                return self.convert_AstGroup(node)
            case _:
                return node

    @classmethod
    def get_max_group_number(cls, node: AstNode) -> int | None:
        values = []
        for u in node.iter_children():
            value = cls.get_max_group_number(u)
            if value is not None:
                values.append(value)
        if isinstance(node, AstGroup):
            values.append(node.number)

        if not values:
            return None
        else:
            return max(values)

    def convert_AstEmpty(self, node: AstEmpty) -> AstNode:
        return node

    def convert_AstCharacter(self, node: AstCharacterSet) -> AstNode:
        return node

    def convert_AstIteration(self, node: AstIteration) -> AstNode:
        u = self.convert(node.u)
        match u:
            case AstEmpty():
                return u
            case _:
                return AstIteration(u)

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
        u = self.convert(node.u)
        v = self.convert(node.v)
        match u, v:
            case AstEmpty(), AstEmpty():
                return AstEmpty()
            case _:
                return AstUnion(u, v)

    def convert_AstConcatenation(self, node: AstConcatenation) -> AstNode:
        u = self.convert(node.u)
        v = self.convert(node.v)
        match u, v:
            case AstEmpty(), w:
                return w
            case w, AstEmpty():
                return w
            case _:
                return AstConcatenation(u, v)

    def convert_AstBoundaryAssertion(self, node: AstBoundaryAssertion) -> AstNode:
        return node

    def convert_AstGroup(self, node: AstGroup) -> AstNode:
        return AstGroup(node.number, self.convert(node.u))

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
