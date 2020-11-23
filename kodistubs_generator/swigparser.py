"""
Parser for SWIG-generated XML definitions of Kodi Python API modules
"""
import os
import re
import lxml.etree as etree


SWIG_XML = {
    'Library - xbmc': 'AddonModuleXbmc.i.xml',
    'Addon': 'AddonModuleXbmcaddon.i.xml',
    'Library - xbmcgui': 'AddonModuleXbmcgui.i.xml',
    'Library - xbmcplugin': 'AddonModuleXbmcplugin.i.xml',
    'Library - xbmcvfs': 'AddonModuleXbmcvfs.i.xml',
    'CryptoSession': 'AddonModuleXbmcdrm.i.xml',
}

# For similar patterns longer patterns should precede shorter ones
DECL_TYPE_SUBS = [
    (re.compile(r'r\.q\(const\)\.XBMCAddon::xbmcgui::InfoLabelDict'), 'Dict[str, str]'),
    (re.compile(r'r\.q\(const\)\.XBMCAddon::Properties'), 'Dict[str, str]'),
    (re.compile(r'r\.q\(const\)\.std::vector<\(XBMCAddon::Properties\)>'), 'List[Dict[str, str]]'),
    (re.compile(r'r\.q\(const\)\.std::vector<\(Tuple<\(XBMCAddon::String,p\.q\(const\)\.XBMCAddon::xbmcgui::ListItem,bool\)>\)>'), 'List[Tuple[str, ListItem, bool]]'),
    (re.compile(r'r\.q\(const\)\.std::vector<\(Tuple<\(XBMCAddon::String,XBMCAddon::String\)>\)>'), 'List[Tuple[str, str]]'),
    (re.compile(r'r\.q\(const\).std::vector<\(Alternative<\(XBMCAddon::String,p\.q\(const\)\.XBMCAddon::xbmcgui::ListItem\)>\)>'), 'List[Union[str, ListItem]]'),
    (re.compile(r'r\.q\(const\)\.Alternative<\(XBMCAddon::String,p\.q\(const\)\.XBMCAddon::xbmcgui::ListItem\)>'), 'Union[str, ListItem]'),
    (re.compile(r'r\.q\(const\)\.Alternative<\(XBMCAddon::String,p\.q\(const\)\.ListItem\)>'), 'Union[str, ListItem]'),
    (re.compile(r'r\.q\(const\)\.std::vector<\(XBMCAddon::String\)>'), 'List[str]'),
    (re.compile(r'r\.q\(const\)\.std::vector<\(int\)>'), 'List[int]'),
    (re.compile(r'r\.q\(const\)\.std::map<\(XBMCAddon::String,XBMCAddon::String\)>'), 'Dict[str, str]'),
    (re.compile(r'std::vector<\(p.XBMCAddon::xbmcgui::Control\)>'), 'List[Control]'),
    (re.compile(r'p\.q\(const\)\.XBMCAddon::xbmcgui::Control'), 'Control'),
    (re.compile(r'p\.XBMCAddon::xbmcgui::Control'), 'Control'),
    (re.compile(r'r?\.?q\(const\)\.XBMCAddon::String'), 'str'),
    (re.compile(r'p\.XBMCAddon::xbmcgui::Action'), 'Action'),
    (re.compile(r'XBMCAddon::String'), 'str'),
    (re.compile(r'r?\.?q\(const\)\.String'), 'str'),
    (re.compile(r'String'), 'str'),
    (re.compile(r'std::string'), 'str'),
    (re.compile(r'p\.q\(const\)\.XBMCAddon::xbmcgui::ListItemList'), 'List[ListItem]'),
    (re.compile(r'p\.q\(const\)\.XBMCAddon::xbmcgui::ListItem'), 'ListItem'),
    (re.compile(r'p\.XBMCAddon::xbmcgui::ListItem'), 'ListItem'),
    (re.compile(r'XBMCAddon::xbmcgui::ListItem'), 'ListItem'),
    (re.compile(r'p\.q\(const\)\.ListItem'), 'ListItem'),
    (re.compile(r'r\.q\(const\)\.XBMCAddon::xbmc::PlayParameter'), 'Union[str, PlayList]'),
    (re.compile(r'p\.q\(const\)\.PlayList'), 'PlayList'),
    (re.compile(r'r\.q\(const\)\.XbmcCommons::Buffer'), 'Union[str, bytes, bytearray]'),
    (re.compile(r'r\.XbmcCommons::Buffer'), 'Union[str, bytes, bytearray]'),
    (re.compile(r'long long'), 'int'),
    (re.compile(r'long'), 'int'),
    (re.compile(r'double'), 'float'),
    (re.compile('unsigned int'), 'int'),
    (re.compile(r'p\.q\(const\)\.char'), 'str'),
    (re.compile(r'q\(const\)\.'), ''),
    (re.compile(r','), ', '),
]

RET_TYPE_SUBS = [
    (re.compile(r'void'), 'None'),
    (re.compile(r'double'), 'float'),
    (re.compile(r'long long'), 'int'),
    (re.compile(r'long'), 'int'),
    (re.compile(r'unsigned int'), 'int'),
    (re.compile(r'xbmc::InfoTagVideo'), 'InfoTagVideo'),
    (re.compile(r'xbmc::InfoTagMusic'), 'InfoTagMusic'),
    (re.compile(r'XBMCAddon::xbmcgui::ListItem'), 'ListItem'),
    (re.compile(r'XBMCAddon::xbmcgui::Control'), 'Control'),
    (re.compile(r'std::unique_ptr<\(std::vector<\(int\)>\)>'), 'List[int]'),
    (re.compile(r'Alternative<\(XBMCAddon::String,std::vector<\(XBMCAddon::String\)>\)>'), 'Union[str, List[str]]'),
    (re.compile(r'std::vector<\(std::string\)>'), 'List[str]'),
    (re.compile(r'XBMCAddon::String'), 'str'),
    (re.compile(r'std::vector'), 'List'),
    (re.compile(r'q\(const\)\.char'), 'str'),
    (re.compile(r'XbmcCommons::Buffer'), 'bytearray'),
    (re.compile(r'<\('), '['),
    (re.compile(r'\)>'), ']'),
    (re.compile(r','), ', '),
]

VALUE_SUBS = [
    (re.compile(r'false'), 'False'),
    (re.compile(r'true'), 'True'),
    (re.compile(r'XBFONT_LEFT'), '0'),
    (re.compile(r'XBFONT_CENTER_Y'), '4'),
    (re.compile(r'lLOGDEBUG'), 'LOGDEBUG'),
    (re.compile(r'CLangCodeExpander::ENGLISH_NAME'), 'ENGLISH_NAME'),
    (re.compile(r'XBMCAddon::emptyString'), '""'),
    (re.compile(r'double'), 'float'),
    (re.compile(r'Player::defaultPlayParameter'), '""'),
    (re.compile(r'std::vector< int >\(\)'), 'None'),
    (re.compile(r'NULL'), 'None'),
    (re.compile(r'XBMCAddon::xbmcgui::INPUT_ALPHANUM'), 'INPUT_ALPHANUM'),
    (re.compile(r'SEEK_SET'), '0'),
]

RET_VALUE_SUBS = {
    'None': 'pass',
    'Tuple[List[str], List[str]]': 'return [""], [""]',
    'ListItem': 'return ListItem()',
    'List[int]': 'return [0]',
    'Control': 'return Control()',
    'Tuple[str, str]': 'return "", ""',
    'Union[str, List[str]]': 'return ""',
    'List[str]': 'return [""]',
    'str': 'return ""',
    'int': 'return 0',
    'long': 'return 0',
    'float': 'return 0.0',
    'bool': 'return True',
    'unicode': 'return ""',
    'InfoTagVideo': 'return InfoTagVideo()',
    'InfoTagMusic': 'return InfoTagMusic()',
    'InfoTagRadioRDS': 'return InfoTagRadioRDS()',
    'bytearray': 'return bytearray()',
}


BASE_CLASS_SUBS = [
    ('AddonClass', ''),
    ('AddonCallback', ''),
]


def clean_type(decl):
    """
    Convert SWIG type declarations for arguments to Python types

    :param decl: SWIG argument type
    :return: Python argument type
    """
    for sub in DECL_TYPE_SUBS:
        decl = sub[0].sub(sub[1], decl)
    return decl


def clean_value(val):
    """
    Convert C++ default arguments to Python

    :param val: C++ argument as string
    :return: Python argument
    """
    for sub in VALUE_SUBS:
        val = sub[0].sub(sub[1], val)
    return val


def clean_rtype(rtype):
    """
    Convert SWIG return types to Python

    :param rtype: SWIG return type
    :return: Python return type
    """
    for sub in RET_TYPE_SUBS:
        rtype = sub[0].sub(sub[1], rtype)
    return rtype


def clean_retvalue(retvalue):
    """
    Convert Python return types to actual Python return statements

    :param retvalue: Python type
    :return: Python return statement
    """
    if retvalue in RET_VALUE_SUBS:
        retvalue = RET_VALUE_SUBS[retvalue]
    return retvalue


def clean_base_class(base_class):
    """
    Convert SWIG base classes to Python

    :param base_class: SWIG base class
    :return: Python base class
    """
    for sub in BASE_CLASS_SUBS:
        base_class = base_class.replace(sub[0], sub[1])
    return base_class


def parse_function(func_doc, attributelist_tag, is_method=False):
    """
    Parse an etree node with a function definition

    :param func_doc: docs dict for the function
    :param attributelist_tag: etree node with function definition
    :param is_method: True if this is a method of a class
    """
    rtype_tags = attributelist_tag.xpath('./attribute[@name="type"]')
    if rtype_tags:
        rtype = clean_rtype(rtype_tags[0].attrib['value'])
    else:
        rtype = 'None'
    if rtype == 'str':
        unicode_tag = attributelist_tag.xpath('./attribute[@name="feature_python_coerceToUnicode"]')
        if unicode_tag:
            rtype = 'unicode'
    func_doc['return'] = clean_retvalue(rtype)
    param_tags = attributelist_tag.xpath('./parmlist/parm/attributelist')
    params = []
    if is_method:
        params.append('self')
    if param_tags:
        for param_tag in param_tags:
            param = param_tag.xpath('./attribute[@name="name"]')[0].attrib['value']
            param_type = param_tag.xpath('./attribute[@name="type"]')[0].attrib['value']
            param_type = clean_type(param_type).strip()
            value_tag = param_tag.xpath('./attribute[@name="value"]')
            if value_tag:
                param_value = clean_value(value_tag[0].attrib['value'])
            else:
                param_value = None
            if param_value == 'None':
                param_type = f'Optional[{param_type}]'
            param += ': ' + param_type
            if param_value is not None:
                param += ' = ' + param_value
            params.append(param)
    joined_params = ', '.join(params)
    signature_string = f'def {func_doc["name"]}({joined_params}) -> {rtype}:'
    if len(signature_string) <= 76:
        params.clear()
        params.append(joined_params)
    if is_method and len(params) > 1:
        params[0] = ', '.join(params[:2])
        params.pop(1)
    # Rename xbmcvfs.Stat.atime, mtime and ctime methods
    if func_doc['name'] in {'atime', 'mtime', 'ctime'}:
        func_doc['name'] = 'st_' + func_doc['name']
    func_doc['params'] = params
    func_doc['rtype'] = rtype
    offset = 5 if is_method else 1
    func_doc['indent'] = len('def ' + func_doc['name']) + offset


def parse_swig_xml(module_docs, swig_dir):
    """
    Parse SWIG-generated module definition

    :param module_docs: docs dictionary object
    :param swig_dir: directory where SWIG XML definitions are located
    :return:
    """
    swig_xml = os.path.join(swig_dir, SWIG_XML[module_docs['name']])
    root_tag = etree.parse(swig_xml)
    module_docs['__name__'] = root_tag.xpath(
        '/top/attributelist/attribute[@name="name"]'
    )[0].attrib['value']
    const_tags = root_tag.xpath('//constant/attributelist/attribute[@name="sym_name"]')
    constants = []
    for const_tag in const_tags:
        constants.append(const_tag.attrib['value'] + ' = 0')
    module_docs['constants'] = constants
    for func_doc in module_docs['functions'][:]:
        try:
            attributelist_tag = root_tag.xpath(f'//cdecl/attributelist/attribute[@value="{func_doc["name"]}"]/..')[0]
        except IndexError:
            print(f'{func_doc["name"]} not found in {SWIG_XML[module_docs["name"]]}')
            module_docs['functions'].remove(func_doc)
            continue
        parse_function(func_doc, attributelist_tag)
    for class_doc in module_docs['classes'][:]:
        try:
            class_attrib_list_tag = root_tag.xpath(
                f'//class/attributelist/attribute[@value="{class_doc["name"]}"]/..')[0]
        except IndexError:
            print(f'{class_doc["name"]} not found in {SWIG_XML[module_docs["name"]]}')
            module_docs['classes'].remove(class_doc)
            continue
        base_class_tag = class_attrib_list_tag.xpath('./baselist/base')[0]
        class_doc['base_class'] = clean_base_class(base_class_tag.attrib['name'])
        for meth_doc in class_doc['functions'][:]:
            attributelist_tag = root_tag.xpath(
                f'//class/attributelist/attribute[@name="sym_name" and @value="{class_doc["name"]}"]'
                f'/../../cdecl/attributelist/attribute[@value="{meth_doc["name"]}"]/..')
            try:
                parse_function(meth_doc, attributelist_tag[0], True)
            except IndexError:
                class_doc['functions'].remove(meth_doc)
                continue
        constructor_tag = root_tag.xpath(
            f'//constructor/attributelist/attribute[@value="{class_doc["name"]}"]/..'
        )
        if constructor_tag:
            init_doc = {'name': '__init__', 'docstring': ''}
            parse_function(init_doc, constructor_tag[0], True)
            class_doc['functions'].insert(0, init_doc)
