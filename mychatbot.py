from gradio.components import Chatbot
from markdown_it import MarkdownIt
from markdown_it import MarkdownIt
from mdit_py_plugins.dollarmath.index import dollarmath_plugin
from mdit_py_plugins.footnote.index import footnote_plugin
from typing import List, Tuple
import re
import pygments
from pygments.lexers import get_lexer_by_name, guess_lexer
from pygments.formatters import HtmlFormatter
import matplotlib.pyplot as plt
import matplotlib
from io import BytesIO

def tex2svg(formula, *args):
    # fix \pmod \bmod
    formula = re.sub(r"\\pmod", r"\ mod\ ", formula)
    formula = re.sub(r"\\bmod", r"\ mod\ ", formula)
    # use agg backend
    matplotlib.use('agg')
    FONTSIZE = 20
    DPI = 300
    plt.rc("mathtext", fontset="cm")
    fig = plt.figure(figsize=(0.01, 0.01))
    fig.text(0, 0, r"${}$".format(formula), fontsize=FONTSIZE)
    output = BytesIO()
    fig.savefig(
        output,
        dpi=DPI,
        transparent=True,
        format="svg",
        bbox_inches="tight",
        pad_inches=0.0,
    )
    plt.close(fig)
    output.seek(0)
    xml_code = output.read().decode("utf-8")
    svg_start = xml_code.index("<svg ")
    svg_code = xml_code[svg_start:]
    svg_code = re.sub(r"<metadata>.*<\/metadata>", "", svg_code, flags=re.DOTALL)
    svg_code = re.sub(r' width="[^"]+"', "", svg_code)
    height_match = re.search(r'height="([\d.]+)pt"', svg_code)
    if height_match:
        height = float(height_match.group(1))
        new_height = height / FONTSIZE  # conversion from pt to em
        svg_code = re.sub(r'height="[\d.]+pt"', f'height="{new_height}em"', svg_code)
    copy_code = f"<span style='font-size: 0px'>{formula}</span>"
    return f"{copy_code}{svg_code}"

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

    def parse_fencecode(self, tokens, idx, options, env):
        token = tokens[idx]
        # print(token)
        try:
            # print(token.attrs)
            lexer = get_lexer_by_name(token.info)
        except pygments.util.ClassNotFound:
            lexer = guess_lexer(token.content)
        formatter = HtmlFormatter()
        parsed_code = pygments.highlight(token.content, lexer, formatter)
        return "<pre>" + parsed_code + "</pre>"
        
    md.add_render_rule("link_open", render_blank_link)
    md.add_render_rule("fence", parse_fencecode)

    return md


class MyChatbot(Chatbot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.md = my_get_markdown_parser()

    def postprocess(
        self, y: List[Tuple[str, str]]
    ) -> List[Tuple[str, str]]:
        """
        Parameters:
            y: List of tuples representing the message and response pairs. Each message and response should be a string, which may be in Markdown format.
        Returns:
            List of tuples representing the message and response. Each message and response will be a string of HTML.
        """
        if y is None:
            return []
        for i, (message, response) in enumerate(y):
            try:
                a = None if message is None else self.md.render(message)
            except:
                a = message
            try:
                b = None if response is None else self.md.render(response)
            except:
                b = response
            y[i] = (a, b)
        return y
    
    def get_block_name(self) -> str:
        return "chatbot"

if __name__ == "__main__":
    print(tex2svg("x^2 \\pmod\{3\}"))