import re
from abc import ABC, abstractmethod
from textwrap import fill
from typing import List, Iterator


class BaseElement(ABC):

    @abstractmethod
    def append(self, content: str):
        pass

    @abstractmethod
    def as_string(self) -> str:
        return ''

    def __str__(self):
        return self.as_string()

    def __repr__(self):
        return f'[{self.__class__.__name__}]<"{str(self)}>"'


class BaseTextElement(BaseElement):
    STRIP_REGEXPS = [
        re.compile(r'^({[^}]+}])'),
        re.compile(r'^(\\python_[^{]+{[^}]+})'),
    ]

    def __init__(self):
        self._string: str = ''

    def append(self, content: str):
        self._string += content

    def as_string(self) -> str:
        string = self._string.strip()
        for regexp in self.STRIP_REGEXPS:
            string = regexp.sub('', string).strip()
        return string


class TextElement(BaseTextElement):

    def as_string(self) -> str:
        string = super().as_string()
        if string:
            return fill(string)
        return ''


class HeadingElement(BaseTextElement):

    def as_string(self) -> str:
        string = super().as_string()
        if string:
            return fill(string) + '\n\n'
        return ''


class ParaElement(BaseTextElement):

    def as_string(self) -> str:
        string = super().as_string()
        if string:
            return fill(string, 80) + '\n\n'
        return ''


class ParameternameElement(BaseTextElement):

    def __init__(self, is_exception: bool = False):
        super().__init__()
        self._prefix = 'raises' if is_exception else 'param'

    def as_string(self) -> str:
        string = super().as_string()
        return f':{self._prefix} {string}: '


class ParameterdescriptionElement(BaseTextElement):

    def as_string(self) -> str:
        string = super().as_string()
        if string:
            return fill(string, subsequent_indent='    ') + '\n'
        return ''


class TableElement(BaseElement):

    def __init__(self, columns: int):
        self._columns: int = columns
        self._table: List[List[str]] = []
        self._column_max_widths: List[int] = []
        self.has_header = False

    def start_row(self):
        self._table.append([])

    def start_cell(self):
        self._table[-1].append('')

    def append(self, content: str):
        if self._table and self._table[-1]:
            self._table[-1][-1] += content

    def __iter__(self) -> Iterator[str]:
        for row in self._table:
            for cell in row:
                yield cell + ' '
            yield '\n'

    def _iter_columns(self, column):
        for row in self._table:
            yield row[column]

    def _normalize_table(self):
        for row in self._table:
            diff = self._columns - len(row)
            row += [''] * diff

    def _calculate_max_widths(self):
        for c in range(self._columns):
            self._column_max_widths.append(max(len(col) for col in self._iter_columns(c)))

    def _fill_columns(self):
        for x in range(self._columns):
            max_width = self._column_max_widths[x]
            for y in range(len(self._table)):
                self._table[y][x] = self._table[y][x].ljust(max_width)

    def _create_border_row(self) -> List[str]:
        border_row = []
        for c in range(self._columns):
            border_row.append('=' * self._column_max_widths[c])
        return border_row

    def _insert_borders(self):
        border_row = self._create_border_row()
        self._table.insert(0, border_row)
        self._table.insert(2, border_row)
        self._table.append(border_row)

    def as_string(self) -> str:
        self._normalize_table()
        self._calculate_max_widths()
        self._fill_columns()
        if self.has_header:
            self._insert_borders()
        return '\n\n' + ''.join(self) + '\n'


class CodelineElement(BaseTextElement):

    def as_string(self) -> str:
        string = super().as_string()
        if string:
            return '    ' + string + '\n'
        return '    \n'


class SimplesectReturnElement(BaseTextElement):

    def as_string(self) -> str:
        string = super().as_string()
        return f':return: {string}\n\n'


class NoteElement(BaseTextElement):

    def as_string(self) -> str:
        string = super().as_string()
        text = fill(string, initial_indent='    ', subsequent_indent='    ')
        return f'\n\n.. note::\n{text}\n\n'
