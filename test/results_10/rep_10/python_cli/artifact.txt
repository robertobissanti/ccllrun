def merge_intervals(intervals):
    """Merge overlapping or adjacent intervals.

    Normalises each pair so that the first element is the minimum,
    merges any overlapping or touching intervals, and returns a
    sorted list of unique tuples.  The original list is never mutated.
    """
    if not intervals:
        return []

    # Normalise without mutating the caller's list
    normalised = sorted((min(a, b), max(a, b)) for a, b in intervals)

    merged = [normalised[0]]
    for start, end in normalised[1:]:
        last_start, last_end = merged[-1]
        # Overlap or adjacency → extend
        if start <= last_end + 1:
            merged[-1] = (last_start, max(last_end, end))
        else:
            merged.append((start, end))

    return merged
