# coding: utf-8
# This file is generated from Kodi source code and post-edited
# to correct code style and docstrings formatting.
# License: GPL v.3 <https://www.gnu.org/licenses/gpl-3.0.en.html>
"""
{{ module.docstring|wordwrap }}
"""
from typing import Union, List, Dict, Tuple

__kodistubs__ = True

{% for const in module.constants %}
{{ const }}
{%- endfor %}

{% for class in module.classes %}
class {{ class.name }}({{ class.base_class }}):
    """
    {{ class.docstring|indent }}
    """
    {% for method in class.functions %}
    def {{ method.signature }}:
        # {{ method.type_annot }}
        {%- if method.docstring %}
        """
        {{ method.docstring|indent(width=8) }}
        """
        {%- endif %}
        {{ method.return }}
    {% endfor %}
{% endfor %}

{% for func in module.functions %}
def {{ func.signature }}:
    # {{ func.type_annot }}
    """
    {{ func.docstring|indent }}
    """
    {{ func.return }}

{% endfor %}
