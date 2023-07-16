import argparse
from pathlib import Path
import os
import shutil
from typing import Optional
from markdownify import MarkdownConverter, ATX, ATX_CLOSED, SETEXT, UNDERLINED, chomp, line_beginning_re, abstract_inline_conversion
import random

MARKDOWN_BQ_STYLE = "MARKDOWN_BQ_STYLE"

class MessyMarkdownConverter(MarkdownConverter):
    """
    Create a custom MarkdownConverter that adds two newlines after an image
    """
    counter = 0
    def __init__(self, **options):
        self.__class__.counter += 1
        self.seed  = options.get("seed", self.__class__.counter)
        self.random = random.Random(self.seed)

        #  options.setdefault("autolinks", self.random.choice([True, False]))
        options.setdefault("autolinks", False)
        options.setdefault("bullets", self.random.choice(['*', '+', '-', '--', '**', '++', '-*', '+*', '*-', '**-', '++-']))
        options.setdefault("default_title", self.random.choice([True, False]))
        options.setdefault("escape_asterisks", self.random.choice([True, False]))
        options.setdefault("escape_underscores", self.random.choice([True, False]))
        options.setdefault("heading_style", self.random.choice([ATX, ATX_CLOSED, 'SETEXT', 'UNDERLINED']))
        options.setdefault("strong_em_symbol", self.random.choice(['*', '_EM_', "~B~", "_B_", "<B>"]))
        options.setdefault("wrap_width", self.random.randint(40, 120))
        options.setdefault("sub_symbol", self.random.choice(['~', '_', '*SUB*', '?SUB?', '!SUB!']))
        options.setdefault("sup_symbol", self.random.choice(['^', '^_', '*SUP*', '?SUP?', '!SUP!']))
        self.capitalize_bold = self.random.choice([True, False])
        self.blockquote_style = self.random.choice(['>', '>>', '>>>', '>>>>', '>>>>>'] + [MARKDOWN_BQ_STYLE] * 5)
        self.a_style = self.random.choice([
            '%s[%s](%s%s)%s',
            '%s%s\n<%s%s>\n%s',
            'link_text: %s%s\nlink: <%s%s>\nlink_suffix: %s',
            '%s%s\n<@%s%s@>\n%s',
            '%s$%s$[%s%s]%s'
        ])
        self.code_style = self.random.choice([
            '`',
            '`%',
            '`>',
            '~+',
            '`~'
        ])
        self.pre_style = self.random.choice([
            '\n```%s\n%s\n```\n',
            '\n~~~%s\n%s\n~~~\n',
            '\n^^^%s\n%s\n^^^\n',
            '\n+++%s\n%s\n+++\n',
            '\n!?!%s\n%s\n!?!\n'
        ])
        self.img_style = self.random.choice([
            '![%s](%s%s)',
            '@[%s]!@(%s%s)',
            '<[%s]>!(%s%s)',
            '[%s]!!(%s%s)',
            '?[%s](%s%s)'
        ])
        self.p_style = self.random.choice([
            '%s\n\n\t',
            '%s\n\n\t\t',
            '%s\n\n  ',
            '%s\n\t',
            '%s\n  '
        ])
        self.h_style = self.random.choice([
            "#",
            "#@",
            "@#",
            "#!",
            "!#"
        ])
        self.h_style_under = self.random.choice([
            "=",
            '-',
            "&",
            "&=",
            "&-"
        ])
        self.li_style = self.random.choice([
            '%s.',
            '%s... ',
            '%s. ',
            '%s ',
            '%s...'
        ])
        self.table_style_f = self.random.choice([
            '\n\n',
            '\n\n\n',
            '\n\t\t',
            '\n\n\t',
            '\n\n  '
        ])
        self.table_style_r = self.random.choice([
            '\n',
            '\n\n',
            '\n\t',
        ])
        self.td_style_f = self.random.choice([
            ' ',
            '  ',
            '_ '
        ])
        self.td_style_r = self.random.choice([
            '|',
            ':',
            '|:',
            ':|'
        ])
        self.title_style = self.random.choice([
            '_TITLE_',
            '_TT_',
            '!!!',
            '<T>',
            ''
        ])
        self.var_style = self.random.choice([
            "$",
            "$$",
            "$!",
            "!$",
            "$ $"
        ])
        self.caption_style = self.random.choice([
            "%s",
            "[%s]\n",
            "%s\n",
            "\nCAPTION: %s\n",
            "\nCAPTION: [%s]\n"
        ])
        self.dd_style = self.random.choice([
            ":%s\n",
            "::%s\n",
            "\n:%s\n",
            "\n::%s\n"
        ])
        self.dt_style = self.random.choice([
            "%s\n:",
            "%s\n::",
            "\n%s\n:",
            "\n%s\n::"
        ])
        # print("Random seed set to {}".format(self.seed))
        super().__init__(**options)

    #TODO: Why are we eliminating the title node?
    # def process_tag(self, node, *args, **kwargs):
    #     if node.name == "title":
    #         return ""
    #     return super().process_tag(node, *args, **kwargs)

    def process_tag(self, node, *args, **kwargs):
        if node.name == "title":
            node.string = ""
            # print(node.text)
        return super().process_tag(node, *args, **kwargs)

    def convert_a(self, el, text, convert_as_inline):
        prefix, suffix, text = chomp(text)
        if not text:
            return ''
        href = el.get('href')
        title = el.get('title')
        # For the replacement see #29: text nodes underscores are escaped
        if (self.options['autolinks']
                and text.replace(r'\_', '_') == href
                and not title
                and not self.options['default_title']):
            # Shortcut syntax
            return '<%s>' % href
        if self.options['default_title'] and not title:
            title = href
        title_part = ' "%s"' % title.replace('"', r'\"') if title else ''
        # return '%s[%s](%s%s)%s' % (prefix, text, href, title_part, suffix) if href else text
        return self.a_style % (prefix, text, href, title_part, suffix) if href else text

    def convert_b(self, el, text, *args):
        if self.capitalize_bold:
            text = text.upper()
        return super().convert_b(el, text, *args)

    def convert_blockquote(self, el, text, *args):
        if self.blockquote_style != MARKDOWN_BQ_STYLE:
            bq_prefix = self.blockquote_style
            lines = text.split("\n")
            lines = [f"{bq_prefix} {line}" for line in lines]
            text = "\n".join(lines)
        return super().convert_blockquote(el, text, *args)

    def convert_caption(self, el, text, convert_as_inline):
      return self.caption_style % text

    convert_cite = convert_a

    def convert_code(self, el, text, convert_as_inline):
        if el.parent.name == 'pre':
            return text
        converter = abstract_inline_conversion(lambda self: self.code_style)
        return converter(self, el, text, convert_as_inline)

    def convert_dd(self, el, text, convert_as_inline):
      return self.dd_style % text

    def convert_dt(self, el, text, convert_as_inline):
      return self.dt_style % text

    def convert_hn(self, n, el, text, convert_as_inline):
        if convert_as_inline:
            return text

        style = self.options['heading_style'].lower()
        text = text.rstrip()
        if style == UNDERLINED and n <= 2:
            line = self.h_style_under
            return super().underline(text, line)
        hashes = self.h_style * n
        if style == ATX_CLOSED:
            return '%s %s %s\n\n' % (hashes, text, hashes)
        return '%s %s\n\n' % (hashes, text)

    def convert_img(self, el, text, convert_as_inline):
        alt = el.attrs.get('alt', None) or ''
        src = el.attrs.get('src', None) or ''
        title = el.attrs.get('title', None) or ''
        title_part = ' "%s"' % title.replace('"', r'\"') if title else ''
        if (convert_as_inline
                and el.parent.name not in self.options['keep_inline_images_in']):
            return alt

        return self.img_style % (alt, src, title_part)

    def convert_li(self, el, text, convert_as_inline):
        parent = el.parent
        if parent is not None and parent.name == 'ol':
            if parent.get("start"):
                start = int(parent.get("start"))
            else:
                start = 1
            bullet = self.li_style % (start + parent.index(el))
        else:
            depth = -1
            while el:
                if el.name == 'ul':
                    depth += 1
                el = el.parent
            bullets = self.options['bullets']
            bullet = bullets[depth % len(bullets)]
        return '%s %s\n' % (bullet, (text or '').strip())

    def convert_table(self, el, text, convert_as_inline):
        return self.table_style_f + text + self.table_style_r

    def convert_td(self, el, text, convert_as_inline):
        return self.td_style_f + text + self.td_style_r

    convert_th = convert_td

    def convert_p(self, el, text, convert_as_inline):
        if convert_as_inline:
            return text
        if self.options['wrap']:
            text = fill(text,
                        width=self.options['wrap_width'],
                        break_long_words=False,
                        break_on_hyphens=False)
        return self.p_style % text if text else ''

    def convert_pre(self, el, text, convert_as_inline):
        if not text:
            return ''
        code_language = self.options['code_language']

        if self.options['code_language_callback']:
            code_language = self.options['code_language_callback'](el) or code_language

        return self.pre_style % (code_language, text)

    convert_q = convert_blockquote

    convert_var = abstract_inline_conversion(lambda self: self.var_style)

def process_file(file_path: Path, out_dir: Optional[Path] = None, options: Optional[dict] = None) -> None:
    messy_file = file_path.with_suffix(".messy")
    clean_file = file_path.with_suffix(".clean")
    clean_converter = MarkdownConverter()
    input = file_path.read_text()
    clean = clean_converter.convert(input).strip()
    clean_file.write_text(clean)
    html_to_messy(file_path, messy_file, options)
    if out_dir:
        # Copy processed file to the out directory
        cp_target = out_dir / clean_file.name
        shutil.copy(clean_file, cp_target)
        # print(f"Copied to: {cp_target}")
    print(messy_file)

def html_to_messy(file_path: Path, messy_file: Path, options: Optional[dict] = None) -> None:
    input = file_path.read_text()
    options = options or {}
    options["seed"] = options.get("seed", hash(input))
    converter = MessyMarkdownConverter(**options)
    messy = converter.convert(input).strip()
    messy_file.write_text(messy)
    # print(f"Created: {messy_file, clean_file}")

def process_html_files(directory: Path, out_dir: Optional[Path] = None, options: Optional[dict] = None) -> None:
    for file_path in directory.rglob('*.html'):
        process_file(file_path, out_dir, options)
    print("Done")


def main() -> None:
    parser = argparse.ArgumentParser(description="Process HTML files in a directory.")
    parser.add_argument("directory", type=Path, help="Directory to search for HTML files.")
    parser.add_argument("-o", "--outdir", type=Path, default=None, help="Directory to output processed files. (Optional)")
    
    args = parser.parse_args()
    process_html_files(args.directory, args.outdir)

if __name__ == "__main__":
    main()

# def md(html, **options):
#     return MessyMarkdownConverter(**options).convert(html)


# print(dir(MarkdownConverter))
# print(md('<b>Yay</b> <a href="http://github.com">GitHub</a>'))  # > '**Yay** [GitHub](http://github.com)'
# print(md('<b>Yay</b> <i>foo</i> <a href="http://github.com">GitHub</a>'))  # > '**Yay** [GitHub](http://github.com)'
