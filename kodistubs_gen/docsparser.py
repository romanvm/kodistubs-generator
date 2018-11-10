"""
Parser for Doxygen XML docs for Kodi Python API functions and classes
"""
import os
import re
from xml.sax import parseString, ContentHandler
from lxml import etree
from .swigparser import parse_swig_xml

MODULES = [
    'group__python__xbmc.xml',
    'group__python__xbmcaddon.xml',
    'group__python__xbmcgui.xml',
    'group__python__xbmcplugin.xml',
    'group__python__xbmcvfs.xml',
    'group__python__xbmcdrm.xml',
]

CLEAN_DOCS_SUBS = [
    (re.compile(r'````'), ''),
    (re.compile(r'\s+?\.\.\.?'), '\n'),
    (re.compile(r'\*\*Example:\*\*'), 'Example::'),
    (re.compile(r'^\*\*(.+?)\*\*'), r'\1'),
    (re.compile(r'(\S)(Example::)'), r'\1\n\n\2'),
    (re.compile(r'^\s\s(\w)', re.M), r'\1'),
    (re.compile(r'^\n\n'), ''),
    (re.compile(r'(:[\w\s]+?:.+?\n)(\w)'), r'\1\n\2'),
    (re.compile(r'(:[\w\s]+?:.+?\n\n)(:)'), r'\1\n\2'),
    (re.compile(r'^{.+}$', re.M), ''),
    (re.compile(r'\n\n\n+?'), '\n\n'),
]


class DocsHandler(ContentHandler):
    READING_TEXT = 0
    READING_HEADER = 1
    READING_PARAM_NAME = 2
    READING_PARAM_DESCR = 3
    READING_RETURN_DESCR = 4
    READING_TABLE = 5

    def __init__(self):
        super().__init__()
        self._string = ''
        self._buffer = ''
        self._state = self.READING_TEXT
        self._cols = None
        self._rows = None
        self._reading_exception = False

    def as_string(self):
        return self._string

    def as_list(self):
        return self._string.split('\n')

    def startElement(self, name, attrs):
        if name == 'heading':
            self._state = self.READING_HEADER
        elif name == 'bold':
            self._string += '**'
        elif name == 'parameterlist' and attrs.get('kind') == 'exception':
            self._state = self._reading_exception = True
        elif name == 'parametername':
            self._state = self.READING_PARAM_NAME
        elif name == 'parameterdescription':
            self._state = self.READING_PARAM_DESCR
        elif name == 'simplesect' and attrs.get('kind') == 'return':
            self._state = self.READING_RETURN_DESCR
        elif name == 'programlisting':
            self._string += '\n\n'
        elif name == 'codeline':
            self._string += '    '
        elif name == 'sp':
            self._string += ' '
        elif name == 'table':
            self._state = self.READING_TABLE
            self._cols = int(attrs.get('cols'))
            self._rows = []
        elif name == 'row':
            self._rows.append([])
        elif name == 'computeroutput':
            self._string += ' ``'

    def endElement(self, name):
        if name == 'heading':
            self._buffer = self._buffer.strip()
            if not(self._buffer.startswith('{') and self._buffer.endswith('}')):
                self._string += self._buffer
            self._buffer = ''
            self._state = self.READING_TEXT
        elif name == 'bold':
            self._string += '**'
        elif name == 'parametername':
            self._string += ' '
        elif name == 'parameterdescription':
            self._string += '\n'
        elif name == 'parameterlist' and self._reading_exception:
            self._reading_exception = False
        elif name == 'simplesect' and self._state == self.READING_RETURN_DESCR:
            self._state = self.READING_TEXT
        elif name == 'codeline':
            self._string += '\n'
        elif name == 'row':
            row_length = len(self._rows[-1])
            if row_length < self._cols:
                self._rows[-1] += ['' for _ in range(self._cols - row_length)]
        elif name == 'table':
            col_widths = []
            for i in range(self._cols):
                column = [row[i] for row in self._rows]
                width = len(max(column, key=lambda item: len(item)))
                col_widths.append(width)
                for row in self._rows:
                    row[i] = row[i].ljust(width)
            t_border = ['=' * w for w in col_widths]
            self._buffer += ' '.join(t_border) + '\n'
            if not self._rows[0][0].isspace():
                self._buffer += ' '.join(self._rows[0]) + '\n'
                self._buffer += ' '.join(t_border) + '\n'
            for row in self._rows[1:]:
                self._buffer += ' '.join(row) + '\n'
            self._buffer += ' '.join(t_border) + '\n'
            self._string += '\n' + self._buffer
            self._cols = self._rows = None
            self._buffer = ''
            self._state = self.READING_TEXT
        elif name == 'computeroutput':
            self._string += '``'
        elif name == 'para' and self._state == self.READING_TEXT and self._string[-1:] != '\n':
            self._string += '\n\n'

    def characters(self, content):
        content = content.replace('&apos;', '\'')
        if content.isspace():
            content = content.strip()
        if self._state == self.READING_HEADER:
            self._buffer += content
        elif self._state == self.READING_PARAM_NAME and not self._reading_exception:
            self._string += ':param ' + content + ':'
        elif self._state == self.READING_PARAM_NAME and self._reading_exception:
            self._string += ':raises ' + content + ':'
        elif self._state == self.READING_RETURN_DESCR:
            self._string += ':return: ' + content
            self._state = self.READING_TEXT
        elif self._state == self.READING_TABLE:
            self._rows[-1].append(content)
        else:
            self._string += content


def clean_docstring(docs):
    for sub in CLEAN_DOCS_SUBS:
        docs = sub[0].sub(sub[1], docs)
    return docs


def parse_description(description_tag):
    """
    Parse an etree node with function/class description

    :param description_tag: etree node with function/class description
    :return: function/class description as a string
    """
    handler = DocsHandler()
    parseString(etree.tostring(description_tag).decode('utf-8').replace('\n', ''), handler)
    return handler.as_string()


def parse_function_docs(memberdef_tag):
    """
    Parse an etree node with function docs

    :param memberdef_tag: etree node with function docs
    :return: function docstring
    """
    briefdescription = memberdef_tag.find('briefdescription')
    docstring = parse_description(briefdescription)
    detaileddescription = memberdef_tag.find('detaileddescription')
    docstring += parse_description(detaileddescription)
    return clean_docstring(docstring).rstrip('\n')


def parse_xml_docs(xml_docs, docs_dir):
    """
    Parse and XML Doxygen docs file

    :param xml_docs: path to a XML docs file
    :param docs_dir: directory where Doxygen docs are located
    :return: docs dict object with module info extracted from an XML docs file
    """
    root_tag = etree.parse(xml_docs)
    compounddef_tag = root_tag.find('compounddef')
    innerclass_tag = compounddef_tag.find('innerclass')
    if innerclass_tag is not None:
        name = innerclass_tag.text.split('::')[-1]
    else:
        name = compounddef_tag.find('title').text
    briefdescription_tag = compounddef_tag.find('briefdescription')
    docstring = parse_description(briefdescription_tag)
    detaileddescription_tag = compounddef_tag.find('detaileddescription')
    docstring += parse_description(detaileddescription_tag)
    docstring = clean_docstring(docstring).rstrip('\n')
    functions = []
    for memberdef in compounddef_tag.xpath('.//sectiondef[@kind="func"]/memberdef'):
        func_name = memberdef.find('name').text
        if memberdef.attrib['prot'] == 'private' or name == func_name:
            continue
        if func_name == 'deleteFile':
            func_name = 'delete'
        functions.append({
            'name': func_name,
            'docstring': parse_function_docs(memberdef)
        })
    classes = []
    for innergroup_tag in compounddef_tag.findall('innergroup'):
        classes.append(parse_xml_docs(
            os.path.join(docs_dir, 'xml', innergroup_tag.attrib['refid'] + '.xml'),
            docs_dir)
        )
    return {
        'name': name,
        'docstring': docstring,
        'classes': classes,
        'functions': functions
    }


def flatten_classes(docs):
    """
    Flatten classes hierarchy in docs dictionary

    :param docs: docs dict object
    :return: docs dict with flattened classes
    """
    for class_ in docs['classes']:
        yield class_
        if class_['classes']:
            for child_class in flatten_classes(class_):
                yield child_class


def parse(docs_dir, swig_dir):
    """
    High-level parser function

    :param docs_dir: directory where Doxygen docs are located
    :param swig_dir: directory where SWIG XML definitions are located
    :return: docs dictionary containing all necessary info for generating
        a Python stub and a Sphinx automodule definition
    """
    docs = []
    for module in MODULES:
        module_xml = os.path.join(docs_dir, 'xml', module)
        module_docs = parse_xml_docs(module_xml, docs_dir)
        if module_docs['name'] in ('Addon', 'CryptoSession'):
            module_docs['classes'] = [module_docs.copy()]
            module_docs['functions'] = []
        else:
            module_docs['classes'] = list(flatten_classes(module_docs))
        parse_swig_xml(module_docs, swig_dir)
        docs.append(module_docs)
    return docs
