"""HydMS — inverse design of metal-hydride compositions.

All the project's code lives in this package. The first pipeline, ``Machine_Model/``, was
removed by card #107; citations to it below resolve at commit ``4348f6ff96``.

Layers own knowledge, not phases. Each subpackage below owns exactly one kind of
knowledge, and nothing outside it needs to know that knowledge; see ``kanban/README.md``
for why the work is cut this way.
"""

__version__ = "0.1.0"
