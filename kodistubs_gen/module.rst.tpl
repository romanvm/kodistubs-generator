{{ module.__name__ }}
{{ underline }}

.. automodule:: {{ module.__name__ }}

  .. rubric:: Classes

  .. autosummary::

    {% for class in module.classes %}
    {{ class.name }}
    {%- endfor %}


  .. rubric:: Functions

  .. autosummary::

    {% for func in module.functions %}
    {{ func.name }}
    {%- endfor %}
