"""The one-command path from raw data to a promoted artifact.

Reproducibility is the point: same seed, same metrics, and a manifest recording the
git SHA, seeds and package versions behind every run.

``smoke.py``
    The cheap end of that: every stage of the chain, in order, over a small committed fixture,
    in about twelve seconds -- ``python -m hydms.pipeline.smoke``. It answers *does the chain
    still connect?* and nothing else. No number it prints is quotable: the fit is a handful of
    features at a sentinel budget over two hundred sampled rows. The expensive end is
    :mod:`hydms.surrogate.train` and :mod:`hydms.surrogate.calibrate`, which is where a real
    run and a real artifact version come from. Card #73.
"""
