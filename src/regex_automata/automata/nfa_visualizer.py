import graphviz  # type: ignore[import-untyped]

from .nfa import NFA


class NFAVisualizer:
    def __init__(self, nfa: NFA) -> None:
        self.nfa = nfa

    def get_digraph_dot(self) -> graphviz.Digraph:
        g = graphviz.Digraph()
        g.attr(rankdir='LR')
        g.node("", shape="none")
        for u in self.nfa.states:
            g.node(str(u), shape="doublecircle" if u in self.nfa.final_states else "circle")
        g.edge("", str(self.nfa.initial_state))
        for u, d in self.nfa.transitions.items():
            for c, vs in d.items():
                c = c or "ε"
                for v in vs:
                    g.edge(str(u), str(v), label=c)
        return g

    def render(self, output_path: str = "nfa.png") -> None:
        dot = self.get_digraph_dot()
        dot.render(outfile=output_path)
