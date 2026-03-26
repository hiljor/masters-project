import itertools as it


def allKCombinations(n, k):
    """Yield all combinations of k or less elements from numbers between 0 and n-1.

    Args:
        n (int): The upper limit of the numbers to choose from (exclusive).
        k (int): The number of elements in each combination.

    Yields:
        tuple: A combination of k or less elements from the range 0 to n-1.
    """
    
    numbers = range(n)
    for i in range(k + 1):
        for comb in it.combinations(numbers, i):
            yield comb