# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project does

Generates [Kodistubs](https://github.com/romanvm/Kodistubs) — Python stub modules for the Kodi Python API — from
Kodi's C++ source files. The pipeline is: Kodi C++ sources → Doxygen XML docs + SWIG XML type definitions →
parsed data structures → Jinja2-rendered Python stubs with reStructuredText docstrings.

## Prerequisites

- Kodi sources cloned, CMake configured (`cmake .`), and SWIG bindings built (`make python_binding`)
- Doxygen installed on the system
- Python 3 virtual environment with `pip install -r requirements.txt` (`lxml`, `Jinja2`)

## Running the generator

```bash
# First run or to regenerate Doxygen docs
python generator.py -o <path-to-kodi-sources>

# Subsequent runs (reuses existing Doxygen output in build/kodi-docs/xml/)
python generator.py <path-to-kodi-sources>
```

Output lands in `build/Kodistubs/*.py` (stub modules) and `build/json/*.json` (structured data).
The `build/` directory is not tracked by git.

## Architecture

### Pipeline stages

1. **`generator.py`** — entry point; creates `build/kodi.doxy` from `kodi.doxy.tpl`, runs `doxygen`, calls
   `parse()`, renders each module via `module.py.tpl`, writes `.py` and `.json` output.

2. **`kodistubs_generator/docsparser.py`** — drives the overall parse. Calls `parse_xml_docs()` for each of the
   6 Kodi modules (`xbmc`, `xbmcaddon`, `xbmcgui`, `xbmcplugin`, `xbmcvfs`, `xbmcdrm`), merges in SWIG type info,
   flattens class hierarchies, applies docstring cleanup regexes, and handles special-case renames
   (e.g. `atime` → `st_atime`, `deleteFile` → `delete`).

3. **`kodistubs_generator/swigparser.py`** — parses SWIG-generated XML to extract function signatures and
   C++-to-Python type mappings. Four ordered regex substitution lists (`DECL_TYPE_SUBS`, `RET_TYPE_SUBS`,
   `VALUE_SUBS`, `RET_VALUE_SUBS`) convert C++ type strings like `r.q(const).std::vector<(XBMCAddon::String)>`
   into Python types (`List[str]`, `Optional[...]`, etc.).

4. **`kodistubs_generator/docstrings_parser/`** — SAX-based XML parser that converts Doxygen XML description
   nodes into reStructuredText. `parser.py` is a `ContentHandler`; `elements.py` defines output element classes
   with line-wrapping at 90 characters.

5. **`kodistubs_generator/module.py.tpl`** — Jinja2 template that renders the final `.py` stub file: imports,
   constants, classes with base classes, methods with docstrings and return stubs.

### Data structure flowing between stages

```python
{
  'name': str,           # display name
  '__name__': str,       # module filename (e.g. 'xbmc')
  'docstring': str,
  'constants': [...],
  'functions': [{'name', 'docstring', 'params', 'rtype', 'return', 'indent'}, ...],
  'classes': [{'name', 'docstring', 'base_class', 'functions': [...]}, ...]
}
```

## Post-editing generated stubs

See @post-editing-prompt.md
