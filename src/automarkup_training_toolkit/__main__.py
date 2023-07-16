from argparse import ArgumentParser
from itertools import chain
from pathlib import Path
import re
from typing import  Optional
from .converters import HtmlToMessYEConverter, SimplifiedDitaConverter, DitaMarkdownConverter, DitaHtmlConverter, HtmlToSimplifiedHtmlConverter, HtmlToMessyConverter, PandocRstConverter, PandocTxtConverter, PandocAsciidocConverter, PandocOrgModeConverter


def parse_args():
    parser = ArgumentParser(description='Process DITA files.')
    parser.add_argument('input_dir', type=Path, help='Input directory with DITA files')
    parser.add_argument('--output_dir', type=Path, default='out', help='Output directory for processed files')
    parser.add_argument('--doctype', type=str, help='The doctype to process')
    parser.add_argument('--glob', type=str, default='*.xml,*.dita', help='The file type to process')
    return parser.parse_args()


def process_file(input_file: Path, input_dir: Path, output_dir: Path, transformations: dict, doctype: Optional[str]=None):
    with input_file.open() as f:
        if doctype and not re.search(f'<!DOCTYPE\\s+{doctype}', f.read()):
            return
        
    output_dir = output_dir / input_file.relative_to(input_dir).stem

    base_name = input_file.stem
    print(input_file)
    transformations = {'Original': input_file}

    plain_text = output_dir / "plain_text"
    markup = output_dir / "markup"
    tmp = output_dir / "tmp"

    converters = [
        SimplifiedDitaConverter(markup, base_name, transformations, 'Original'),
        DitaMarkdownConverter(plain_text, base_name, transformations, SimplifiedDitaConverter.__name__),
        DitaHtmlConverter(tmp, base_name, transformations, SimplifiedDitaConverter.__name__),
        HtmlToSimplifiedHtmlConverter(markup, base_name, transformations, 'DitaHtmlConverter'),
        HtmlToMessyConverter(plain_text, base_name, transformations, 'HtmlToSimplifiedHtmlConverter', 1),
        HtmlToMessyConverter(plain_text, base_name, transformations, 'HtmlToSimplifiedHtmlConverter', 2),
        HtmlToMessyConverter(plain_text, base_name, transformations, 'HtmlToSimplifiedHtmlConverter', 3),
        HtmlToMessyConverter(plain_text, base_name, transformations, 'HtmlToSimplifiedHtmlConverter', 4),
        HtmlToMessyConverter(plain_text, base_name, transformations, 'HtmlToSimplifiedHtmlConverter', 5),
        PandocRstConverter(plain_text, base_name, transformations, 'HtmlToSimplifiedHtmlConverter'),
        PandocTxtConverter(plain_text, base_name, transformations, 'HtmlToSimplifiedHtmlConverter'),
        PandocAsciidocConverter(plain_text, base_name, transformations, 'HtmlToSimplifiedHtmlConverter'),
        PandocOrgModeConverter(plain_text, base_name, transformations, 'HtmlToSimplifiedHtmlConverter'),
        HtmlToMessYEConverter(plain_text, base_name, transformations, 'HtmlToSimplifiedHtmlConverter'),
    ]

    for converter in converters:
        converter.convert()

def copy_files_metrics_ready(formats_dir: Path, metrics_ready_dir: Path):
    prompt = Path("prompt.txt")
    
    for filename in formats_dir.glob("*/plain_text/*"):
        new_filename = Path(str(metrics_ready_dir / filename.name.split(".")[0] / filename.name ) + ".txt")
        new_filename.parent.mkdir(parents=True, exist_ok=True)
        new_filename.write_text(filename.read_text())
        (new_filename.parent / prompt.name).write_text(prompt.read_text())
        dita = list((filename.parent.parent / "markup").glob("*.dita"))[0]
        new_filename.with_suffix(".xml").write_text(dita.read_text())
        html = list((filename.parent.parent / "markup").glob("*.html"))[0]
        new_filename.with_suffix(".html").write_text(html.read_text())

def main():
    args = parse_args()
    transformations = {}
    formats_dir = Path(args.output_dir) / "formats"
    files = (args.input_dir.rglob(pat) for pat in args.glob.split(","))
    for input_file in chain(*files):
        process_file(input_file, args.input_dir, formats_dir, transformations, args.doctype)
    metrics_ready_dir = Path(args.output_dir) / "metrics_ready"
    metrics_ready_dir.mkdir(parents=True, exist_ok=True)
    copy_files_metrics_ready(formats_dir, metrics_ready_dir)


if __name__ == '__main__':
    main()
