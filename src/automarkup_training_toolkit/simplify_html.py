import difflib
import re
from typing import Optional, Set
from bs4 import BeautifulSoup
from pathlib import Path
import argparse
import markdownify

# TODO: what to do about colspan, rowspan, scope: table attributes, 

ATTRS_TO_DELETE = ["title", "alt", "nav"]  # these change the Markdown, but not in ways that normal humans would
ATTRS_TO_IGNORE = ["class", "id", "lang", "style", "dir", "border", "compact", "shape", "name", "usemap", "target", "data", "rel", "role", "headers",  "height", "width" ]
ATTRS_TO_KEEP = set(["charset", # meta charset="utf-8", without this the output will be type-confused
                     "href", "src", 
                     "type" # for different types of ordered lists
                     ])

ELEMENTS_TO_DELETE = ["object", "samp", "nav", "meta", "figure", "colgroup", "col"]
ELEMENTS_TO_SKIP = ["area", "link", "br", "map"]
ELEMENTS_TO_UNWRAP = ["abbr", "article", "div", "main", "map", "nav", "object", "section", "span", "sub", "sup", "u"]

def process_element(element, unknown_attrs, all_elements) -> None:
    if not element.name: # already deleted
        return
    
    if element.name in ELEMENTS_TO_SKIP:
        element.decompose()
        return
    elif element.name == "meta" and "charset" not in element.attrs:
        element.decompose()
        return
    elif element.name in ELEMENTS_TO_UNWRAP:
        element.unwrap()
        return
    
    for attr in tuple(element.attrs.keys()):
        if attr in ATTRS_TO_IGNORE:
            del element[attr]
    if unknown_attrs is not None:
        extra_attrs = set(element.attrs.keys()) - ATTRS_TO_KEEP
        for attr in extra_attrs:
            attr_str = f"{element.name}.{attr}"
            if attr_str not in unknown_attrs:
                unknown_attrs.add(attr_str)
                print(f"Unknown attribute: {attr_str}")
    if all_elements is not None:
        all_elements.add(element.name)


def simplify_html(
    file_path: Path,
    out_path: Path,
    unknown_attrs: Optional[Set] = None,
    all_elements: Optional[Set] = None,
) -> None:
    soup = BeautifulSoup(Path(file_path).read_text(), "html.parser")

    # Remove elements and attrs that are part of Markdown but are not
    # practical in Messy Markdown for auto-markup engines
    for element in soup():
        if element.name in ELEMENTS_TO_DELETE:
            element.decompose()
        else:
            for attr in tuple(element.attrs or ()):
                if attr in ATTRS_TO_DELETE:
                    del element[attr]

    orig = markdownify.MarkdownConverter().convert_soup(soup)

    # Remove all class and id attributes
    for element in soup():
        process_element(element, unknown_attrs, all_elements)

    out_path.write_text(str(soup))

    new = markdownify.MarkdownConverter().convert_soup(soup)

    if re.sub(r"\s", "", orig) != re.sub(r"\s", "", new):
        diff = difflib.context_diff(orig.splitlines(), new.splitlines())
        diff = "\n".join(diff)
        Path("/tmp/orig.md").write_text(orig)
        Path("/tmp/new.md").write_text(new)
        assert (
            orig == new
        ), f"File {file_path} has changed after simplification. Please check the output: {out_path} : {diff}"


def process_html_files(
    directory: Path, out_dir: Path = None, unknown_attrs: Set = None, all_elements: Set = None
) -> None:
    for file_path in directory.rglob("*.html"):
        if not str(file_path).endswith(".simplified.html"):
            if out_dir:
                out_path = out_dir / file_path.name
            else:
                out_path = Path(file_path).with_suffix(".simplified.html")
            simplify_html(file_path, out_path, unknown_attrs, all_elements)


def main() -> None:
    parser = argparse.ArgumentParser(description="Process HTML files in a directory.")
    parser.add_argument(
        "directory", type=Path, help="Directory to search for HTML files."
    )
    parser.add_argument(
        "-o",
        "--outdir",
        type=Path,
        default=None,
        help="Directory to output processed files. (Optional)",
    )

    args = parser.parse_args()
    unknown_attrs = set()
    all_elements = set()
    process_html_files(args.directory, args.outdir, unknown_attrs, all_elements)
    if unknown_attrs:
        print("Unknown attributes", unknown_attrs)
    print("Elements", sorted(all_elements))


if __name__ == "__main__":
    main()
