"""HydMS — inverse design of metal-hydride compositions.

All new work lives in this package. ``Machine_Model/src/`` is the frozen archival record
behind ``REPORT.md`` and is never modified — rewriting it would orphan every published
number (PRD §7.2).

Layers own knowledge, not phases. Each subpackage below owns exactly one kind of
knowledge, and nothing outside it needs to know that knowledge; see ``kanban/README.md``
for why the work is cut this way.
"""

__version__ = "0.1.0"
