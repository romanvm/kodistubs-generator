"""
Parser for Doxygen XML docs for Kodi Python API functions and classes
"""
import os
import re
from xml.sax import parseString
import lxml.etree as etree
from .swigparser import parse_swig_xml
from .docstrings_parser.parser import DocstringParser

MODULES = [
    # 'group__python__xbmc.xml',
    # 'group__python__xbmcaddon.xml',
    'group__python__xbmcgui.xml',
    # 'group__python__xbmcplugin.xml',
    # 'group__python__xbmcvfs.xml',
    # 'group__python__xbmcdrm.xml',
]

CLEAN_DOCS_SUBS = [
    # (re.compile(r'````'), ''),
    # (re.compile(r'\s+?\.\.\.?'), '\n'),
    # (re.compile(r'^\*\*(.+?)\*\*'), r'\1'),
    # (re.compile(r'(\S)(Example::)'), r'\1\n\n\2'),
    # (re.compile(r'^\s\s(\w)', re.M), r'\1'),
    # (re.compile(r'^\n\n'), ''),
    # (re.compile(r'(:[\w\s]+?:.+?\n)(\w)'), r'\1\n\2'),
    # (re.compile(r'(:[\w\s]+?:.+?\n\n)(:)'), r'\1\n\2'),
    (re.compile(r'\*\*Example:\*\*'), 'Example::'),
    (re.compile(r'(\n:(?:param|return|raises).+?)\n(\w)'), '\\1\n\n\\2'),
    (re.compile(r'^\s\sAdded'), 'Added'),
    (re.compile(r'([\w,])(\*\*[^*]+?\*\*)'), r'\1 \2'),
    (re.compile(r'``\*\*|\*\*``'), '``'),
    (re.compile(r'\*\*"|"\*\*'), '``'),
    (re.compile(r'^{\s.+?\s}$', re.M), ''),
    (re.compile(r'(\w)(`?`\w+?`?)'), r'\1 \2'),
    (re.compile(r'(.)\n\n\n+?(.)'), '\\1\n\n\\2'),
]


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
    handler = DocstringParser()
    parseString(etree.tostring(description_tag).decode('utf-8').replace('\n', ''), handler)
    return str(handler)


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
    return clean_docstring(docstring).strip(' \n')


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
        class_xml_name = innergroup_tag.attrib['refid']
        innergroup_xml_docs = parse_xml_docs(
            os.path.join(docs_dir, 'xml', class_xml_name + '.xml'),
            docs_dir
        )
        if (name in (
                'Player',
                'Window'
                ) and
                class_xml_name in (
                        'group__python__PlayerCB',
                        'group__python__xbmcgui__window__cb'
                    )
                ):
            functions += innergroup_xml_docs['functions']
        else:
            classes.append(innergroup_xml_docs)
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
        del class_['classes']


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
        if module_docs['name'] in {'Addon', 'CryptoSession'}:
            module_docs['classes'] = [module_docs.copy()]
            module_docs['functions'] = []
        else:
            module_docs['classes'] = list(flatten_classes(module_docs))
        parse_swig_xml(module_docs, swig_dir)
        docs.append(module_docs)
    return docs
