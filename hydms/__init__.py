"""HydMS — inverse design of metal-hydride compositions.

This package is the project. The earlier pipeline (``Machine_Model/``) and the report built on
it (``REPORT.md``) were removed by card #107 because their numbers could not be reproduced;
both survive at the git tag ``machine-model-archive``, and the citations below of the form
``Machine_Model/src/...`` resolve there.

Layers own knowledge, not phases. Each subpackage below owns exactly one kind of
knowledge, and nothing outside it needs to know that knowledge; see ``kanban/README.md``
for why the work is cut this way.
"""

__version__ = "0.1.0"
