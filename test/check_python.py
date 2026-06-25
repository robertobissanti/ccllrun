import importlib.util
import sys

spec = importlib.util.spec_from_file_location("solution", sys.argv[1])
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

cases = [
    ([], []),
    ([(5, 1), (2, 4), (10, 10), (11, 12)], [(1, 5), (10, 12)]),
    ([(-3, -1), (-2, 2), (8, 8)], [(-3, 2), (8, 8)]),
    ([(1, 2), (1, 2), (4, 3)], [(1, 4)]),
]
for value, expected in cases:
    original = list(value)
    got = mod.merge_intervals(value)
    assert got == expected, (value, got, expected)
    assert value == original, "input modificato"
    assert all(isinstance(x, tuple) for x in got), got
print("PASS")
