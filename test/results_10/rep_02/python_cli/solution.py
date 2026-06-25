def merge_intervals(intervals):
    """Merge overlapping or adjacent intervals.

    Normalises reversed pairs, merges overlaps/adjacency, returns
    a sorted list of unique tuples. Uses only the standard library.
    """
    # Normalise: ensure (low, high) for every pair
    normalised = [tuple(sorted(iv)) for iv in intervals]

    # Deduplicate while preserving order
    seen = set()
    unique = []
    for iv in normalised:
        if iv not in seen:
            seen.add(iv)
            unique.append(iv)

    # Sort by start, then by end
    unique.sort()

    merged = []
    for start, end in unique:
        if merged and start <= merged[-1][1] + 1:
            # Overlapping or adjacent
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))

    return merged
