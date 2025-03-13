# Algorithm overview
### Calculations:
- I am using the power tree (with a power of 10) to store and recalculate aggregates. 
- Average is being deduced from the sum and count of the data points, or by merging (/subtracting) aggregate averages.
- For variance I am using the (slightly modified) formula:
```python
def parallel_variance(n_a, avg_a, M2_a, n_b, avg_b, M2_b):
    n = n_a + n_b
    delta = avg_b - avg_a
    M2 = M2_a + M2_b + delta**2 * n_a * n_b / n
    var_ab = M2 / (n - 1)
    return var_ab
```
(https://en.wikipedia.org/wiki/Algorithms_for_calculating_variance) and for subtraction its inversed form

### Pushing data:
When new data comes I only need to recalculate the new data aggregate(/s) and the spill in each tree node.
1. there is new data batch that  needs to squeeze in -> this causes spill on other aggregates
2. the spilling aggregate gets trimmed to the previous size and the cut spill is prepended to the next aggregate
3. the new agregate gets trimmed to previous size creating new spill for the next aggregate and so the cycle goes on

### Pulling data :
- When user wants to pull data i merge aggregates to the proper length and cache the result for next users.
- If the data is being processed (by recent push) i lock the mutex and wait for the data to be processed -> user needs to wait for processing to end

### Transactionality:
When user wants push, or fetch data for certain symbol async mutex for that symbol is locked to block other users from pushing, or getting unprocessed data.

Mutex on one symbol does not affect other symbols.

### What could be improved:
This project was estimated for 3 hours but it took around 10 (i had too much fun optimising it especially the variance), so there are some things that could be improved, but ~~they are boring~~ i dont think they are in so scope for the time being I will leave them as a **TODO!**: 
- I could separate recalculate into multiple chunks (this function is quite big) and the readability suffers a bit (tradeoff for performance)
- I could run profiler to search for any additional bottlenecks
- I could add more exception handling in case of issues, but that would require more back and forth conversation.
- I could add pre-commit hook with linters and test runners
- I could add E2E tests

# Complexity:
### Space 
The project has space complexity of O(log(n))
- there is no overhead but there is additional aggregates of the power tree.
- I am using iterators to avoid shallow copying of the data

### Time 
The time complexity is O(log(n)), but:
- every spill needs to be recalculated
- if min or max value of aggregate is being pushed out of its bounds, recalculation triggers

# How to run it:
### Within context of wenv:
```bash
pip install poetry 
poetry install --no-root
python main.py 
```

### Api documentation is avalible at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc UI: `http://localhost:8000/redoc`
