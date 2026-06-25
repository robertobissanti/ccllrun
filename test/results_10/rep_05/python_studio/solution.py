def merge_intervals(intervals):
    """Merge overlapping or adjacent intervals.

    Normalises reversed pairs, merges overlaps and adjacency,
    returns a sorted list of unique tuples. Input is never mutated.
    """
    # Normalise every pair so that low <= high
    normalised = [tuple(sorted(pair)) for pair in intervals]

    # Sort by start, then by end
    normalised.sort()

    merged = []
    for start, end in normalised:
        if merged and start <= merged[-1][1] + 1:
            # Overlap or adjacency — extend the current interval
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))

    return merged
