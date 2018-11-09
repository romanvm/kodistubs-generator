# (c) 2018, Roman Miroshnychenko <roman1972@gmail.com>
# License: 

import argparse
import os
from subprocess import run
from jinja2 import Environment, FileSystemLoader
from kodistubs_gen.docsparser import parse

base_dir = os.path.dirname(os.path.abspath(__file__))
template_dir = os.path.join(base_dir, 'kodistubs_gen')
build_dir = os.path.join(base_dir, 'build')
docs_dir = os.path.join(build_dir, 'kodi-docs')
doxy_path = os.path.join(build_dir, 'kodi.doxy')
jinja_env = Environment(loader=FileSystemLoader(template_dir))


def parse_arguments():
    parser = argparse.ArgumentParser(description='Kodistubs generator')
    parser.add_argument('kodi_src', nargs='?', help='Kodi sources dir')
    return parser.parse_args()


def create_doxyfile(src_dir):
    kodi_doxy = jinja_env.get_template('kodi.doxy.tpl')
    with open(doxy_path, 'w', encoding='utf-8') as fo:
        fo.write(kodi_doxy.render(src_dir=src_dir, out_dir=docs_dir))


def generate_doxy_docs():
    run(['doxygen', doxy_path])


def main():
    args = parse_arguments()
    if not os.path.exists(build_dir):
        os.mkdir(build_dir)
    src_dir = os.path.join(args.kodi_src, 'xbmc', 'interfaces', 'legacy')
    create_doxyfile(src_dir)
    generate_doxy_docs()
    swig_dir = os.path.join(args.kodi_src, 'build', 'swig')
    template_py = jinja_env.get_template('module.py.tpl')
    template_rst = jinja_env.get_template('module.rst.tpl')
    module_docs = parse(docs_dir, swig_dir)
    for mod in module_docs:
        module_py = template_py.render(module=mod)
        with open(os.path.join(build_dir, mod['__name__'] + '.py'), 'w',
                  encoding='utf-8') as fo:
            fo.write(module_py)
        module_rst = template_rst.render(
            module=mod,
            underline='=' * len(mod['__name__'])
        )
        with open(os.path.join(build_dir, mod['__name__'] + '.rst'), 'w',
                  encoding='utf-8') as fo:
            fo.write(module_rst)


if __name__ == '__main__':
    main()