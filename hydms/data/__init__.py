"""L1 -- source schemas, the merge key, the composition identity and the split protocol.

Four questions this layer answers once, so that nothing above it answers them again:

``load.py``
    What a valid row is. Three raw files, each with its declared schema, validated at the
    door -- a loader either returns a frame matching its schema or names the rows that do
    not. Nothing is coerced, filled or stripped.

``merge.py``
    How feature blocks are attached to the measurement table: by key, with coverage asserted
    both ways, never by position. Leak L9.

``canonical.py``
    When two rows describe the same material, and which alloy class that material belongs
    to. The key every split, every fold and every group-by uses. Leaks L8 and L13.

Splits (card #13) and screening (card #14) join them here, and both group on
:func:`hydms.data.canonical.group_keys` -- the raw formula string is not an identity.
"""
