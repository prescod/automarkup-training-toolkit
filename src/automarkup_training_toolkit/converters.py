

from pathlib import Path
import shutil
import subprocess
from typing import Dict, List, Optional, Union
from xml.dom import minidom
from automarkup_training_toolkit.html2markdown import HTMLToMarkdownConverter

from automarkup_training_toolkit.simplify_html import simplify_html
from automarkup_training_toolkit.html_to_messy import html_to_messy


class Converter:
    def __init__(self, output_dir: Path, base_name: str, transformations: Dict[str, Path], dependent_key: Optional[str]=None):
        self.output_dir = output_dir
        self.base_name = base_name
        self.transformations = transformations
        self.dependent_key = dependent_key
        self.output_file = self.output_dir / self.get_output_filename()

    def convert(self):
        print(self.__class__.__name__)
        print(self.transformations)
        if self.dependent_key:
            self.input_file = Path(self.transformations[self.dependent_key])
        else:
            self.input_file = None
        if self.dependent_key and isinstance(self.transformations.get(self.dependent_key), Converter):
            self.input_file = Path(self.transformations[self.dependent_key])
            assert self.input_file.exists(), f'File {self.input_file} does not exist'
        if not self.output_file.exists():
            self._convert()
        self.transformations[self.get_key()] = self.output_file

    def get_output_filename(self):
        raise NotImplementedError

    def _convert(self):
        raise NotImplementedError

    @classmethod
    def get_key(cls):
        return cls.__name__

class DitaConverter(Converter):
    def __init__(self, output_dir: Path, base_name: str, format: str, globs: Union[str, List[str]], transformations: dict, dependent_key: Optional[str]=None):
        super().__init__(output_dir, base_name, transformations, dependent_key)
        self.format = format
        self.globs = globs if isinstance(globs, list) else [globs]

    def _convert(self):
        self.input_file = self.input_file.resolve()
        output_dir = self.output_file.with_suffix(".tmp")
        command = f'dita --input={self.input_file} --output={output_dir} --format={self.format}'
        print(command)
        subprocess.run(command, shell=True, check=True)
        self.globs += [f'*/{glob}' for glob in self.globs]
        for glob in self.globs:
            matching = list(output_dir.glob(glob))
            if matching:
                matching[0].rename(self.output_file)
                shutil.rmtree(output_dir)
                return
        raise Exception(f'No matching file found for {self.input_file} in {output_dir} using {self.globs}')


class SimplifiedDitaConverter(DitaConverter):
    def __init__(self, output_dir: Path, base_name: str, transformations: dict, dependent_key: str="Original"):
        super().__init__(output_dir, base_name, 'dita', ["*.xml", "tasks/*.xml", "*.dita", "tasks/*.dita"], transformations, dependent_key)

    def _convert(self):
        res = super()._convert()
        self._remove_elements(["related-links", "prolog"])
        return res
    
    def _remove_elements(self, elements_to_delete: List[str]):
        """Load a DITA document and remove the related-links element."""
        with self.output_file.open() as f:
            tree = minidom.parse(f)
        # TODO: speed this up by removing all elements at once
        for element_to_delete in elements_to_delete:
            self._remove_element_type(element_to_delete, tree)
        with open(self.output_file, "w") as f:
            tree.writexml(f)

    def _remove_element_type(self, tagName: str, dom: minidom.Document):
        for element in dom.getElementsByTagName(tagName):
            element.parentNode.removeChild(element)

    def get_output_filename(self):
        return f'{self.base_name}.dita'


class DitaMarkdownConverter(DitaConverter):
    def __init__(self, output_dir: Path, base_name: str, transformations: dict, dependent_key: Optional[str]=None):
        super().__init__(output_dir, base_name, 'markdown', ["*.md", "tasks/*.md", "*/*.md"], transformations, dependent_key)

    def get_output_filename(self):
        return f'{self.base_name}.md'


class DitaHtmlConverter(DitaConverter):
    def __init__(self, output_dir: Path, base_name: str, transformations: dict, dependent_key: Optional[str]=None):
        super().__init__(output_dir, base_name, 'html5', ["*.html", "tasks/*.html"], transformations, dependent_key)

    def get_output_filename(self):
        return f'{self.base_name}.raw.html'


class HtmlToSimplifiedHtmlConverter(Converter):
    def __init__(self, output_dir: Path, base_name: str, transformations: dict, dependent_key: Optional[str]=None):
        super().__init__(output_dir, base_name, transformations, dependent_key)

    def _convert(self):
        assert self.input_file
        print("QQQ", self.input_file, self.input_file.exists(), self.output_file, self.output_file.exists())
        simplify_html(self.input_file, self.output_file)

    def get_output_filename(self):
        return f'{self.base_name}.html'


class HtmlToMessyConverter(Converter):
    def __init__(self, output_dir: Path, base_name: str, transformations: dict, dependent_key: Optional[str]=None, seed: Optional[int]=None):
        self.seed=seed
        super().__init__(output_dir, base_name, transformations, dependent_key)

    def _convert(self):
        assert self.input_file
        seed = hash(f"{self.input_file}_{self.seed}")
        html_to_messy(self.input_file, self.output_file, {"seed": seed})

    def get_output_filename(self):
        return f'{self.base_name}.{self.seed}.messy'
    
class HtmlToMessYEConverter(HtmlToMessyConverter):
    def _convert(self):
        assert self.input_file
        content = self.input_file.read_text()
    
        #  To do: pass through a Conversion Profile
        converter = HTMLToMarkdownConverter()
        text = converter.convert_to_messy(content)
        self.output_file.write_text(text)

    def get_output_filename(self):
        return f'{self.base_name}.messYE'



class PandocConverter(Converter):
    def __init__(self, output_dir: Path, base_name: str, format: str, transformations: dict, dependent_key: Optional[str]=None):
        self.format = format
        super().__init__(output_dir, base_name, transformations, dependent_key)

    def _convert(self):
        command = f'pandoc {self.input_file} -o {self.output_file} -t {self.format}'
        subprocess.run(command, shell=True, check=True)

    def get_output_filename(self):
        return f'{self.base_name}.{self.format}'

    def get_key(self):
        return self.format

class PandocRstConverter(PandocConverter):
    def __init__(self, output_dir: Path, base_name: str, transformations: dict, dependent_key: Optional[str]=None):
        super().__init__(output_dir, base_name, 'rst', transformations, dependent_key)


class PandocTxtConverter(PandocConverter):
    def __init__(self, output_dir: Path, base_name: str, transformations: dict, dependent_key: Optional[str]=None):
        super().__init__(output_dir, base_name, 'plain', transformations,dependent_key)


class PandocAsciidocConverter(PandocConverter):
    def __init__(self, output_dir: Path, base_name: str, transformations: dict, dependent_key: Optional[str]=None):
        super().__init__(output_dir, base_name, 'asciidoc', transformations,dependent_key)


class PandocOrgModeConverter(PandocConverter):
    def __init__(self, output_dir: Path, base_name: str, transformations: dict, dependent_key: Optional[str]=None):
        super().__init__(output_dir, base_name, 'org', transformations,dependent_key)
