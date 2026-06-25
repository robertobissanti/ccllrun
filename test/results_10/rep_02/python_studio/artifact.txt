def merge_intervals(intervals):
    """Merge overlapping or adjacent intervals.

    Normalises reversed pairs, merges overlaps/adjacency, returns
    a sorted list of unique tuples. Uses only the standard library.
    """
    # Normalise: ensure each pair is (min, max)
    normalised = [tuple(sorted(iv)) for iv in intervals]

    # Sort by start, then by end
    normalised.sort()

    merged = []
    for start, end in normalised:
        if merged and start <= merged[-1][1] + 1:
            # Overlapping or adjacent
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))

    return merged
