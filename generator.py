# (c) 2018, Roman Miroshnychenko <roman1972@gmail.com>
# License: GPL v.3
"""
Script for semi-autoamated generation of
`Kodistubs <https://github.com/romanvm/Kodistubs>`_ from Kodi source files.
"""

import argparse
import json
import os
from subprocess import run
from jinja2 import Environment, FileSystemLoader
from kodistubs_generator.docsparser import parse

base_dir = os.path.dirname(os.path.abspath(__file__))
template_dir = os.path.join(base_dir, 'kodistubs_generator')
build_dir = os.path.join(base_dir, 'build')
docs_dir = os.path.join(build_dir, 'kodi-docs')
doxy_path = os.path.join(build_dir, 'kodi.doxy')
jinja_env = Environment(loader=FileSystemLoader(template_dir))


def parse_arguments():
    parser = argparse.ArgumentParser(description='Kodistubs generator')
    parser.add_argument('kodi_src', nargs='?', help='Kodi sources dir')
    parser.add_argument('-o', '--overwrite', action='store_true',
                        help='Overwrite Doxygen docs')
    return parser.parse_args()


def create_doxyfile(src_dir):
    kodi_doxy = jinja_env.get_template('kodi.doxy.tpl')
    with open(doxy_path, 'w', encoding='utf-8') as fo:
        fo.write(kodi_doxy.render(src_dir=src_dir, out_dir=docs_dir))


def generate_doxy_docs():
    run(['doxygen', doxy_path])


def main():
    print('Generating Kodistubs...')
    if not os.path.exists(build_dir):
        os.mkdir(build_dir)
    args = parse_arguments()
    src_dir = os.path.join(args.kodi_src, 'xbmc', 'interfaces', 'legacy')
    swig_dir = os.path.join(args.kodi_src, 'build', 'swig')
    if args.overwrite or not os.path.exists(os.path.join(docs_dir, 'xml')):
        create_doxyfile(src_dir)
        generate_doxy_docs()
    template_py = jinja_env.get_template('module.py.tpl')
    module_docs = parse(docs_dir, swig_dir)
    for mod in module_docs:
        print(f'Writing {mod["__name__"]}...')
        with open(os.path.join(build_dir, mod['__name__'] + '.json'), 'w') as fo:
            json.dump(mod, fo, indent=2)
        module_py = template_py.render(module=mod)
        with open(os.path.join(build_dir, mod['__name__'] + '.py'), 'w',
                  encoding='utf-8') as fo:
            fo.write(module_py)
    print('Done')


if __name__ == '__main__':
    main()
