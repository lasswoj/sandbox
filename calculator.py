import math
import itertools
import asyncio


# from https://en.wikipedia.org/wiki/Algorithms_for_calculating_variance
def parallel_variance(n_a, avg_a, M2_a, n_b, avg_b, M2_b):
    if not n_a:
        return M2_b, n_b, avg_b, M2_b
    n = n_a + n_b
    delta = avg_b - avg_a
    avg_power = (avg_a * n_a + avg_b * n_b) / n
    M2 = M2_a + M2_b + delta**2 * n_a * n_b / n
    var_ab = M2 / (n - 1)
    return var_ab, n, avg_power, M2


class BranchValues:
    def __init__(self, avg, _min, i_min, _max, i_max, amount, variance):
        self.avg = avg
        self.min = _min
        self.i_min = i_min
        self.max = _max
        self.i_max = i_max
        self.amount = amount
        self.variance = variance

    @staticmethod
    def from_chunk(slice_iter, start, end, residual=None):
        iter1, iter2 = itertools.tee(slice_iter, 2)
        amount = end - start
        if not amount:
            return None
        lmax = -math.inf
        lmin = math.inf
        l_imax = 0
        l_imin = 0
        l_avg = 0
        for cur, val in enumerate(iter1):
            if val > lmax:
                lmax = val
                l_imax = start + cur
            if val < lmin:
                lmin = val
                l_imin = start + cur
            l_avg += val
        l_avg /= amount
        vars = 0
        for i in iter2:
            var = i - l_avg
            var *= var
            vars += var
        if amount == 1:
            variance = 0
        else:
            variance = vars / (amount - 1)
        thisbranch = BranchValues(l_avg, lmin, l_imin, lmax, l_imax, amount, variance)
        if residual:
            return BranchValues.merger([thisbranch, residual])
        return thisbranch

    def subtract(self, slice_iter, start, end, residual):
        # residual = BranchValues.from_chunk(slice_iter, start, end)
        amount = self.amount - residual.amount

        if not amount:
            return
        avg = (self.avg * self.amount - residual.avg * residual.amount) / amount
        if self.i_max < start or self.i_min < start:
            self.max = -math.inf
            self.min = math.inf
            for cur, val in enumerate(slice_iter):
                if val > self.max:
                    self.max = val
                    self.i_max = start + cur
                if val < self.min:
                    self.min = val
                    self.i_min = start + cur
        delta = residual.avg - self.avg
        m2 = self.variance * (self.amount - 1)
        m2 -= (
            residual.variance * (residual.amount - 1)
            + delta**2 * (residual.amount * self.amount) / amount
        )
        self.variance = m2 / (amount - 1)

        self.avg = avg
        self.amount = amount

    @staticmethod
    def merger(branches, start):
        branches = [i for i in branches if i]
        if len(branches) == 0:
            return None
        if len(branches) == 1:
            return branches[0]
        lmax = -math.inf
        l_imax = 0
        lmin = math.inf
        l_imin = 0
        avg_a = 0
        amount = 0
        variance = 0
        # for initial paralel variance calculation
        M2_a = 0
        for i in branches:
            variance, amount, avg_a, M2_a = parallel_variance(
                amount, avg_a, M2_a, i.amount, i.avg, i.variance * (i.amount - 1)
            )
            if i.min < lmin:
                l_imin = i.i_min
                lmin = i.min
            if i.max > lmax:
                l_imax = i.i_max
                lmax = i.max

        return BranchValues(avg_a, lmin, l_imin, lmax, l_imax, amount, variance)


class Calculator:
    def __init__(self):
        self.arrays = {}
        self.calculations = {}
        self.locks = {}

    async def push_data(self, data, symbol):
        lock = self._get_lock(symbol)
        async with lock:  # Wait until lock is free
            self.kcalc = {}
            self.recalculate(data, symbol)

    def _get_lock(self, symbol):
        """Ensure each source has its own lock."""
        if symbol not in self.locks:
            self.locks[symbol] = asyncio.Lock()
        return self.locks[symbol]

    async def get_kcalc(self, k, symbol):
        k -= 1
        lock = self._get_lock(symbol)
        async with lock:  # Wait until lock is free
            if k not in self.kcalc:
                calculations = self.calculations.get(symbol, [])
                k_pow = 10**k
                togo = calculations[: min(len(calculations), k + 1)]
                kvalue = BranchValues.merger(togo, k_pow)
                kcalc = {
                    "avg": kvalue.avg,
                    "min": kvalue.min,
                    "max": kvalue.max,
                    "variance": kvalue.variance,
                    "last": self.arrays[symbol][-1],
                }

                self.kcalc[k] = kcalc
            return self.kcalc[k]

    def recalculate(self, data, symbol):
        bigarray = self.arrays.get(symbol, [])
        bigarray.extend(data)
        if not self.arrays.get(symbol):
            self.arrays[symbol] = bigarray
        calculations = self.calculations.get(symbol, [])

        arr_len = len(bigarray)
        i = 0
        j = 10
        newcalcs = []
        absolute_start = len(bigarray) - len(data)
        while j <= len(data):
            slice_iter = itertools.islice(data, len(data) - j, len(data) - i)
            newcalcs.append(
                BranchValues.from_chunk(
                    slice_iter, absolute_start + i, absolute_start + j
                )
            )
            if i == 0:
                i = 1
            i *= 10
            j *= 10
        residual = BranchValues.from_chunk(
            itertools.islice(data, 0, max(0, len(data) - i)),
            absolute_start + 0,
            absolute_start + max(0, len(data) - i),
        )
        tempsum = 0
        reprocess = []
        if residual:
            reprocess.append(residual)
            tempsum += residual.amount
        old_iter = 0
        while tempsum < j and old_iter < len(calculations):
            tempsum += calculations[old_iter].amount
            reprocess.append(calculations[old_iter])
            old_iter += 1

        while i <= arr_len and j <= 100000000:
            start = arr_len - i
            merged = BranchValues.merger(reprocess, start)
            if not merged:
                break
            reprocess = []
            max_amount = j - i
            if merged.amount > max_amount:
                residual = BranchValues.from_chunk(
                    itertools.islice(
                        bigarray, max(0, arr_len - (i + merged.amount)), arr_len - j
                    ),
                    arr_len - (i + merged.amount),
                    arr_len - j,
                )
                merged.subtract(
                    itertools.islice(bigarray, arr_len - j, arr_len - i),
                    arr_len - j,
                    arr_len - i,
                    residual,
                )
                reprocess.append(residual)
            newcalcs.append(merged)
            if old_iter < len(calculations):
                reprocess.append(calculations[old_iter])
                old_iter += 1
            if i == 0:
                i = 1
            i *= 10
            j *= 10
        self.calculations[symbol] = newcalcs


if __name__ == "__main__":
    go = Calculator()
    lo = [i for i in range(5)]
    go.push_data(lo, "test")
    lo = [i for i in range(5, 11)]
    go.push_data(lo, "test")
    lo = [i for i in range(11, 15)]
    go.push_data(lo, "test")
    lo = [i for i in range(15, 20)]
    go.push_data(lo, "test")
    lo = [i for i in range(20, 25)]
    go.push_data(lo, "test")
    print(go.get_kcalc(1, "test"))
    go.get_kcalc(2, "test")
    lo2 = [i for i in range(25, 40)]
    go.push_data(lo2, "test")
    lo3 = [i for i in range(40, 200)]
    go.push_data(lo3, "test")
    lo3 = [i for i in range(200, 90000)]
    go.push_data(lo3, "test")
    lo3 = [i for i in range(90000, 90010)]
    go.push_data(lo3, "test")
    lo3 = [i for i in range(90010, 90020)]
    # go.push_data(lo3)
    # print(go.get_kcalc(4))
    # print(go)

    # [8333333.25, 8.25, 833.25, 83333.25, 0.0]
