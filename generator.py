# (c) 2018, Roman Miroshnychenko <roman1972@gmail.com>
# License: GPL v.3
"""
Script for semi-automated generation of
`Kodistubs <https://github.com/romanvm/Kodistubs>`_ from Kodi source files.
"""

import argparse
import json
from pathlib import Path
from subprocess import run

from jinja2 import Environment, FileSystemLoader

from kodistubs_generator.docsparser import parse

base_dir = Path(__file__).resolve().parent
template_dir = base_dir / 'kodistubs_generator'
build_dir = base_dir / 'build'
kodistubs_dir = build_dir / 'Kodistubs'
json_dir = build_dir / 'json'
docs_dir = build_dir / 'kodi-docs'
doxy_path = build_dir / 'kodi.doxy'
jinja_env = Environment(loader=FileSystemLoader(template_dir))


def parse_arguments():
    parser = argparse.ArgumentParser(description='Kodistubs generator')
    parser.add_argument('kodi_src', nargs='?', help='Kodi sources dir')
    parser.add_argument('-o', '--overwrite', action='store_true',
                        help='Overwrite Doxygen docs')
    return parser.parse_args()


def create_doxyfile(src_dir):
    kodi_doxy = jinja_env.get_template('kodi.doxy.tpl')
    with doxy_path.open('w', encoding='utf-8') as fo:
        fo.write(kodi_doxy.render(src_dir=src_dir, out_dir=docs_dir))


def generate_doxy_docs():
    run(['doxygen', str(doxy_path)])


def main():
    print('Generating Kodistubs...')
    if not build_dir.exists():
        build_dir.mkdir()
        kodistubs_dir.mkdir()
        json_dir.mkdir()
    args = parse_arguments()
    kodi_src = Path(args.kodi_src)
    src_dir = kodi_src / 'xbmc' / 'interfaces' / 'legacy'
    swig_dir = kodi_src / 'build' / 'swig'
    if not swig_dir.exists():
        swig_dir = kodi_src / 'build' / 'build' / 'swig'
    if args.overwrite or not (docs_dir / 'xml').exists():
        create_doxyfile(src_dir)
        generate_doxy_docs()
    template_py = jinja_env.get_template('module.py.tpl')
    module_docs = parse(docs_dir, swig_dir)
    for mod in module_docs:
        print(f'Writing {mod["__name__"]}...')
        with (json_dir / (mod['__name__'] + '.json')).open('w') as fo:
            json.dump(mod, fo, indent=2)
        module_py = template_py.render(module=mod)
        with (kodistubs_dir / (mod['__name__'] + '.py')).open('w',
                  encoding='utf-8') as fo:
            fo.write(module_py)
    print('Done')


if __name__ == '__main__':
    main()
