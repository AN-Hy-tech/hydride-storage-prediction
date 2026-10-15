"""HydMS — inverse design of metal-hydride compositions.

All work lives in this package. The archival pipeline behind the old ``REPORT.md`` was
deleted by card #107; it and the report are recoverable at git tag ``machine-model-archive``,
which is where every ``src/<file>.py:<line>`` citation in this package points.

Layers own knowledge, not phases. Each subpackage below owns exactly one kind of
knowledge, and nothing outside it needs to know that knowledge; see ``kanban/README.md``
for why the work is cut this way.
"""

__version__ = "0.1.0"
