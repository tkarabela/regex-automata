[![CI - build](https://img.shields.io/github/actions/workflow/status/tkarabela/regex-automata/main.yml?branch=master)](https://github.com/tkarabela/regex-automata/actions)
[![CI - coverage](https://img.shields.io/codecov/c/github/tkarabela/regex-automata)](https://app.codecov.io/github/tkarabela/regex-automata)
[![MyPy & Ruffle checked](https://img.shields.io/badge/MyPy%20%26%20Ruffle-checked-blue?style=flat)](https://github.com/tkarabela/regex-automata/actions)

# regex-automata

A toy implementation of regular expressions using finite automata.

## Usage

```python
import regex_automata

pattern = regex_automata.compile(r"(foo)*bar|baz")  # regex_automata.Pattern

pattern.fullmatch("foofoobar")  # regex_automata.Match(span=(0, 9), match='foofoobar')
pattern.fullmatch("foo")        # None

pattern.ast  # regex_automata.parser.ast.AstNode
pattern.nfa  # regex_automata.automata.nfa.NFA

pattern.render_ast("regex_ast.svg")
pattern.render_nfa("regex_nfa.svg")
```

Abstract syntax tree of `(foo)*bar|baz`:

![tree for (foo)*bar|baz](./static/example_ast.svg)

Finite automaton accepting `(foo)*bar|baz`:

![automaton for (foo)*bar|baz](./static/example_nfa.svg)


## Features compared to standard `re` module

- Library
  - `match()`, `fullmatch()` and `search()` methods (search is currently implemented naively via match)
  - `Match` object containing span and matched text (but no groups)
  - flags `DOTALL` and `IGNORECASE`

- Syntax
  - character sets: `.`, `[...]` (special sequences such as `\w` are not supported)
  - repetition: `*`, `?`, `+`, `{n,k}`
  - basic groups: `(...)` that behave like `(?:...)` ie. non-capturing

## Implementation overview

- Input pattern is tokenized via `regex_automata.parser.tokenizer.Tokenizer`
  - Characters and sets are represented with `regex_automata.automata.rangeset.RangeSet`
- List of tokens is processed by recursive descent parser `regex_automata.parser.parser.Parser`
- Parser produces "raw" abstract syntax tree composed of `regex_automata.parser.ast.AstNode` nodes
- AST is processed with `regex_automata.parser.ast_processor.ASTProcessor` to produce the final tree
  - This is used to replace fancy repetition with primitives (union, concatenation, iteration)
- Epsilon-free NFA is recursively constructed from the AST using `regex_automata.regex.nfa_builder.NFABuilder`
- The processed pattern is stored in `regex_automata.regex.pattern.Pattern`, which is the high-level interface
- When processing input text, the text and NFA are passed to `regex_automata.regex.nfa_evaluator.NFAEvaluator`
- The evaluator produces `regex_automata.regex.match.Match` objects

## Grammar

The recursive descent parser uses the following LL(1) grammar:

```
 1.  E  → F E'
 2.  E' → | E
 3.  E' → ε
 4.  F  → G F'
 5.  F' → G F'
 6.  F' → ε
 7.  G  → H G'
 8.  G' → *
 9.  G' → ε
10.  H  → ( E )
11.  H  → a
12.  E  → ε
```

Which is derived from the following CFG:

```
E → F | E
E → F
E → ε
F → G F
F → G
G → H *
G → H
H → ( E )
H → a
```

Which is derived from the following CFG:

```
E → E | E
E → E E
E → E *
E → ( E )
E → a
E → ε
```

## License

MIT, see [LICENSE.txt](./LICENSE.txt).
