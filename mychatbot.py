from gradio.components import Chatbot
from markdown_it import MarkdownIt
from markdown_it import MarkdownIt
from mdit_py_plugins.dollarmath.index import dollarmath_plugin
from mdit_py_plugins.footnote.index import footnote_plugin
from gradio.utils import tex2svg
from typing import List, Tuple
import re
import pygments
from pygments.lexers import get_lexer_by_name, guess_lexer
from pygments.formatters import HtmlFormatter

def my_get_markdown_parser() -> MarkdownIt:
    md = (
        MarkdownIt(
            "js-default",
            {
                "linkify": True,
                "typographer": True,
                "html": True,
                "breaks": True,
            },
        )
        .use(dollarmath_plugin, renderer=tex2svg, allow_digits=False)
        .use(footnote_plugin)
        .enable("table")
    )

    # Add target="_blank" to all links. Taken from MarkdownIt docs: https://github.com/executablebooks/markdown-it-py/blob/master/docs/architecture.md
    def render_blank_link(self, tokens, idx, options, env):
        tokens[idx].attrSet("target", "_blank")
        return self.renderToken(tokens, idx, options, env)

    md.add_render_rule("link_open", render_blank_link)

    return md

def parse_fencecode(raw):
    regex = r"```(.*?)\n(.*?\n*)```"
    matches = re.findall(regex, raw, re.DOTALL)
    # print(matches)
    for language, code in matches:
        try:
            lexer = get_lexer_by_name(language)
        except pygments.util.ClassNotFound:
            lexer = guess_lexer(code)
        formatter = HtmlFormatter()
        parsed_code = pygments.highlight(code.rstrip(), lexer, formatter).strip()
        raw = raw.replace(f"```{language}\n{code}```\n", parsed_code)
    # print(raw)
    return raw


class MyChatbot(Chatbot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.md = my_get_markdown_parser()

    def postprocess(
        self, y: List[Tuple[str | None, str | None]]
    ) -> List[Tuple[str | None, str | None]]:
        """
        Parameters:
            y: List of tuples representing the message and response pairs. Each message and response should be a string, which may be in Markdown format.
        Returns:
            List of tuples representing the message and response. Each message and response will be a string of HTML.
        """
        if y is None:
            return []
        for i, (message, response) in enumerate(y):
            y[i] = (
                None if message is None else self.md.renderInline(parse_fencecode(message)),
                None if response is None else self.md.renderInline(parse_fencecode(response)),
            )
        return y
    
    def get_block_name(self) -> str:
        return "chatbot"