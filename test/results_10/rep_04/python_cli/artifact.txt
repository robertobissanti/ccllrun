def merge_intervals(intervals):
    """Merge overlapping or adjacent intervals.

    Accepts a list of (start, end) pairs. Each pair is normalised so that
    start <= end.  Overlapping or touching intervals are merged.  The result
    is a sorted list of unique tuples.
    """
    # Normalise every pair so (lo, hi) with lo <= hi.
    normalised = [tuple(sorted(pair)) for pair in intervals]

    # Sort by start, then by end.
    normalised.sort()

    merged: list[tuple[int, int]] = []
    for start, end in normalised:
        if merged and start <= merged[-1][1] + 1:
            # Overlapping or adjacent → extend.
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))

    return merged
