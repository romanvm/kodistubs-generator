# coding: utf-8
"""
Parse doxygen object descriptions into ReStructuredText docstrings
"""

from typing import List
from xml.sax.handler import ContentHandler
from . import elements


class DocstringParser(ContentHandler):

    def __init__(self):
        super().__init__()
        self._elements: List[elements.BaseElement] = [elements.TextElement()]
        self._reading_exception_block = False

    def as_string(self):
        return ''.join(str(elem) for elem in self._elements)

    def __str__(self):
        return self.as_string()

    def startElement(self, name: str, attrs: dict):
        if name == 'parameterlist' and attrs.get('kind') == 'exception':
            self._reading_exception_block = True
        if name == 'heading':
            self._elements.append(elements.HeadingElement())
        if name == 'para' and isinstance(self._elements[-1], elements.TextElement):
            self._elements.append(elements.ParaElement())
        elif name == 'parametername':
            self._elements.append(elements.ParameternameElement(is_exception=self._reading_exception_block))
        elif name == 'parameterdescription':
            self._elements.append(elements.ParameterdescriptionElement())
        elif name == 'itemizedlist':
            self._elements[-1].append('\n\n')
        elif name == 'table':
            columns = int(attrs['cols'])
            self._elements.append(elements.TableElement(columns))
        elif name == 'row' and isinstance(self._elements[-1], elements.TableElement):
            self._elements[-1].start_row()
        elif name == 'entry' and isinstance(self._elements[-1], elements.TableElement):
            self._elements[-1].start_cell()
            if attrs.get('thead') == 'yes':
                self._elements[-1].has_header = True
        elif name == 'bold':
            self._elements[-1].append('**')
        elif name == 'codeline':
            self._elements.append(elements.CodelineElement())
        elif name == 'sp':
            self._elements[-1].append(' ')
        elif name == 'linebreak':
            self._elements[-1].append('\n')
        # elif name == 'hruler':
        #     self._elements[-1].append('\n\n')
        elif name == 'simplesect' and attrs.get('kind') == 'return':
            self._elements.append(elements.SimplesectReturnElement())
        elif name == 'ref' and attrs.get('kindref') in {'member', 'compound'}:
            self._elements[-1].append('`')
        elif name == 'computeroutput':
            self._elements[-1].append('``')
        elif name == 'simplesect' and attrs.get('kind') == 'note':
            self._elements.append(elements.NoteElement())

    def endElement(self, name: str):
        if name == 'parameterlist' and self._reading_exception_block:
            self._reading_exception_block = False
        if (name in {
                    'heading',
                    'parameterdescription',
                    'table',
                    'codeline',
                    'simplesect',
                }
                or name == 'para' and isinstance(self._elements[-1], elements.ParaElement)):
            self._elements.append(elements.TextElement())
        elif name == 'bold':
            self._elements[-1].append('**')
        elif name == 'para' and isinstance(self._elements[-1], elements.TextElement):
            self._elements[-1].append('\n\n')
        elif name == 'ref':
            self._elements[-1].append('`')
        elif name == 'computeroutput':
            self._elements[-1].append('``')

    def characters(self, content: str):
        content = self._clean_content(content)
        if content.isspace():
            content = ' '
        self._elements[-1].append(content)

    @staticmethod
    def _clean_content(content: str) -> str:
        content = content.replace('&apos;', '\'')
        content = content.rstrip(' \n')
        return content
