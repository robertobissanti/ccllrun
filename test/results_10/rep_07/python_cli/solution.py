def merge_intervals(intervals):
    """Merge overlapping or adjacent intervals.

    Normalises reversed pairs, merges overlaps/adjacency, returns
    a sorted list of unique tuples. Input is never mutated.
    """
    if not intervals:
        return []

    # Normalise: ensure (low, high) for every pair
    normalised = [tuple(sorted(iv)) for iv in intervals]

    # Sort by start, then by end
    normalised.sort()

    merged = [normalised[0]]
    for start, end in normalised[1:]:
        prev_start, prev_end = merged[-1]
        # Overlap or adjacency: merge
        if start <= prev_end + 1:
            merged[-1] = (prev_start, max(prev_end, end))
        else:
            merged.append((start, end))

    return merged
