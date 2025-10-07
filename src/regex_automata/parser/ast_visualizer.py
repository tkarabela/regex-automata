import graphviz  # type: ignore[import-untyped]

from .ast import AstNode


class ASTVisualizer:
    def __init__(self, ast: AstNode) -> None:
        self.ast = ast

    def get_graph_dot(self) -> graphviz.Graph:
        g = graphviz.Graph()
        g.attr(rankdir='TB')

        for u in self.ast.iter_descendants():
            g.node(self.node_id(u), label=u.get_label(), shape="circle")
            for v in u.iter_children():
                g.edge(self.node_id(u), self.node_id(v))

        return g

    @staticmethod
    def node_id(node: AstNode) -> str:
        return f"node{id(node)}"

    def render(self, output_path: str = "ast.png") -> None:
        dot = self.get_graph_dot()
        dot.render(outfile=output_path)
