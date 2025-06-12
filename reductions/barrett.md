# Barrett Reduction

Barrett Reduction is an optimization algorithm used in modular arithmetic calculations (finding remainders) that avoids expensive division operations. Its basic concept is quite straightforward.

When calculating the remainder r of $a \bmod N$ (a modulo N), the conventional approach is to first compute the quotient $q = a \div N$, and then calculate the remainder $r = a - q \times N$.

However, computing q requires a division operation, which is computationally expensive for CPUs. Barrett Reduction avoids this division by introducing a pre-computed constant.

## Core Algorithm Concept

1. Choose a sufficiently large $R = 2^k$ such that $R > N$.
2. Pre-compute $\mu = \lfloor R / N \rfloor$. (where $\lfloor \rfloor$ represents the floor function)
3. When you need to compute $a \bmod N$, use the following steps instead:
   - Calculate $q = \lfloor(a \times \mu) / R\rfloor$
   - Calculate $r = a - q \times N$
   - If $r \geq N$, then $r = r - N$

The key optimization here is that since R is a power of 2, $(a \times \mu) / R$ can be implemented through a simple bit shift operation: $q = (a \times \mu) \gg k$.

For a fixed finite field, N is typically constant, so $\mu$ can also be pre-computed and stored.

## Error Analysis

This method may result in q being slightly smaller than the actual quotient because $\mu$ is a lower bound of $R/N$ (due to the floor function). This is why we need to check if r is less than N after calculating $r = a - q \times N$, and subtract N again if r is greater than or equal to N.

Regarding the number of times N needs to be subtracted in the worst case:

- The upper bound of the error can be proven to be 2. That is, the calculated r can be at most 2N larger than the actual remainder.
- Therefore, at most two subtractions of N are needed to obtain the correct remainder.

## Algorithm Advantages

1. Avoids expensive division operations, replacing them with multiplication and bit shift operations.
2. For a fixed modulus N, $\mu$ can be pre-computed, further improving efficiency.
3. Even in the worst case, only a finite number (at most two) of additional subtractions are needed.

## Error Range for Computing μ

Let's define $q'$ as the actual value of $a/N$, and q as the value obtained through Barrett Reduction:
$q' = \lfloor a / N \rfloor$, $q = \lfloor(a \times \mu) / R\rfloor$

1. $R = 2^k$, where k is an integer, and $R > N$.
2. $\mu = \lfloor R / N \rfloor$
3. Assume $a < R$ (an important assumption that usually holds in practical applications)

### Upper Bound: $q \leq q'$

We know that $\mu = \lfloor R / N \rfloor$, so $\mu \leq R / N$.

$$
\begin{aligned}
q &= \lfloor(a \times \mu) / R\rfloor \\
  &\leq \lfloor(a \times (R/N)) / R\rfloor \quad \text{(since } \mu \leq R/N\text{)} \\
  &= \lfloor a / N \rfloor \\
  &= q'
\end{aligned}
$$

Therefore, $q \leq q'$

### Lower Bound: $q > q' - 2$

First, we know that $R/N - 1 < \mu \leq R/N$ (since $\mu$ is the floor of $R/N$)
Thus:

$$
\begin{aligned}
q &= \lfloor(a \times \mu) / R\rfloor \\
  &> \lfloor(a \times (R/N - 1)) / R\rfloor \quad \text{(since } \mu > R/N - 1\text{)} \\
  &= \lfloor a/N - a/R \rfloor
\end{aligned}
$$

Next, we can write:
$q > a/N - a/R - 1$ (since for any x, $\lfloor x \rfloor > x - 1$)

Now, using our assumption that $a < R$, we have $a/R < 1$, so:

$$
\begin{aligned}
q &> a/N - 1 - 1 \\
  &= a/N - 2 
\end{aligned}
$$

But $q' = \lfloor a/N \rfloor$, so $a/N - 1 < q' \leq a/N$
Substituting this inequality into the expression above:
$q > (q' - 1) - 2 = q' - 3$

Since q is an integer, $q \geq q' - 2$

Combining with our previous result $q \leq q'$, we can conclude that $q' - 2 < q \leq q'$