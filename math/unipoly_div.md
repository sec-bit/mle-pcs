# Fast Polynomial Division Based on Newton Iteration

Traditional polynomial synthetic division requires a computational complexity of $O(n^2)$. This section introduces a fast division algorithm using Newton Iteration, with a complexity consistent with polynomial multiplication, only $O(M(n))$. Here, $M(n)$ represents the complexity of polynomial multiplication.

## Reversed Polynomials

Let's consider a finite field $F$, and polynomials $f(X)$ and $g(X)$ in $F[X]$. Since $F[X]$ is a Euclidean Domain, $f(X)$ and $g(X)$ satisfy the division with remainder equation:

$$
f(X) = g(X)\cdot q(X) + r(X)
$$
where $\deg(r)<\deg(g)$. For convenience, let's denote $n=\deg(f)$ and $m=\deg(g)$.

First, let's introduce an important concept: the **reversed polynomial**. If $f(X)$ is represented in coefficient form as:

$$
f = a_0 + a_1X + \cdots + a_{n-1}X^{n-1} \in F[X] 
$$

Then its reversed polynomial is:

$$
\mathsf{rev}(f) = a_{n-1} + a_{n-2}X + \cdots + a_1X^{n-2} + a_0X^{n-1}  \in F[X] 
$$

Simply put, $\mathsf{rev}(f)$ reverses the coefficients of $f$, making the highest-degree coefficient the constant term, the second-highest the coefficient of $X$, and so on. The formal definition of the reverse transformation is: $\mathsf{rev}_k(f):F[X]\to F[X]$:

$$
\mathsf{rev}_k(f): f \longmapsto X^kf\left(\frac{1}{X}\right)
$$

If $k=\deg(f)$, then $\mathsf{rev}_k(f)$ represents the reversed polynomial of $f$, and we can omit the subscript $k$, writing it as $\mathsf{rev}(f)$. Let's expand the definition of $\mathsf{rev}_k(f)$:

$$
\begin{aligned}
\mathsf{rev}_k(f) & = X^kf\left(\frac{1}{X}\right) \\
& = X^k\left(a_0 + \frac{a_{1}}{X} + \cdots + \frac{a_{n-2}}{X^{n-2}} + \frac{a_{n-1}}{X^{n-1}}\right) \\
& = a_0X^k + a_1X^{k-1} + \cdots + a_{n-1}X^{k-n+1}  \\
& = X^{k-n+1}\big( a_{n-1} + a_{n-2}X + \cdots + a_1X^{n-2} + a_0X^{n-1} \big)
\end{aligned}
$$

where $k\ge (n-1)$. If $k=n-1$, then $\mathsf{rev}_k(f)$ exactly equals the reversed polynomial of $f$. It's easy to verify that $\mathsf{rev}_k$ satisfies additive homomorphism:

$$
\mathsf{rev}_k(f+g) = \mathsf{rev}_k(f) + \mathsf{rev}_k(g)
$$

And $\mathsf{rev}_k$ also satisfies the following multiplicative relationship:

$$
\mathsf{rev}_k(f\cdot g) = \mathsf{rev}_j(f)\cdot \mathsf{rev}_{k-j}(g)
$$

$$
\mathsf{rev}_k(f) = X^d \cdot \mathsf{rev}_{k-d}(f)
$$

Substituting the division decomposition of $f(X)$ into the definition of $\mathsf{rev}(f)$, we get:

$$
\begin{aligned}
\mathsf{rev}_{n-1}(f) & = \mathsf{rev}_{n-1}(p\cdot g + r) \\
& = \mathsf{rev}_{n-1}(p\cdot g) + \mathsf{rev}_{n-1}(r) \\
& = \mathsf{rev}_{n-m}(q)\cdot \mathsf{rev}_{m-1}(g) + X^{n-m+1}\mathsf{rev}_{m-2}(r)
\end{aligned}
$$

Then we can derive the following equation:

$$
\mathsf{rev}(f) \equiv \mathsf{rev}_{n-m}(q)\cdot \mathsf{rev}_{m-1}(g) \mod{X^{n-m+1}}
$$

Note that in the above equation, $r(X)$ is elevated into higher-degree terms by $X^{n-m+1}$, so we can eliminate it through polynomial modular arithmetic.

The purpose of doing this is that polynomial division no longer needs to consider the remainder polynomial $r(X)$; we only need to calculate the reversed polynomial of the quotient polynomial $\mathsf{rev}(q)$ using the equation above.

We can further transform the equation to get the calculation formula for $\mathsf{rev}_{n-m}(q)$:

$$
\mathsf{rev}_{n-m}(q) \equiv \mathsf{rev}_{n-1}(f)\cdot \mathsf{rev}_{m-1}(g)^{-1} \mod{X^{n-m+1}}
$$

Calculating the quotient polynomial $q(X)$ depends on finding the multiplicative inverse of a polynomial under modular arithmetic, i.e., how to compute $\mathsf{rev}_{m-1}(g)^{-1}$ such that $\mathsf{rev}_{m-1}(g)\cdot \mathsf{rev}_{m-1}(g)^{-1} \equiv 1\mod{X^{n-m+1}}$. For convenience, let's introduce a new constant variable: $l=n-m+1$. Note that since $l>n-m=\deg(q)$, we have:

$$
\mathsf{rev}_{n-m}(q) = \mathsf{rev}_{n-m}(f)\cdot \mathsf{rev}_{m-1}(g)^{-1}
$$

If we can successfully calculate $\mathsf{rev}_{n-m}(q)$, then $q(X)$ can be solved as:

$$
q = \mathsf{rev}_{n-m}(\mathsf{rev}_{n-m}(q))
$$

The next question is, in a polynomial equation with modular arithmetic, is calculating the multiplicative inverse of a polynomial easier? In other words, how do we calculate the multiplicative inverse in the quotient ring $F[X]/\langle X^l \rangle$?

## Existence of Multiplicative Inverses in Quotient Rings

We know that only unit elements have multiplicative inverses in a ring. So which polynomials have multiplicative inverses in the quotient ring $F[X]/\langle X^l \rangle$? Since $X^l$ is clearly not an irreducible polynomial, $F[X]/\langle X^l \rangle$ does not form a field.

We can consider the subring $F[X]/\langle X^l \rangle$ of $F[X]$. Does every polynomial $f(X)$ have an inverse element? The answer is yes. This is because for any Euclidean Domain $R$, if two elements $a, m\in R$ are coprime, i.e., $\gcd(a, m)=1$, then through the Extended Euclidean Algorithm, we can compute $s, t\in R$ that satisfy the Bezout equation:

$$
s a + t m = 1
$$

For any polynomial $f\in F[X]/\langle X^l \rangle$ modulo $X^l$, as long as its constant term is non-zero, $\gcd(f, X^l)=1$, satisfying the above property. So we can compute the inverse of $f\bmod{X^l}$ using the Extended Euclidean Algorithm, but this requires $O(n^2)$ complexity.

For our problem of calculating $h$ in $g\cdot h \equiv 1\mod{X^l}$, since $g$ is the reversed polynomial of some polynomial, its constant term must be non-zero. In particular, if the original polynomial is a monic polynomial (with leading coefficient 1), then its constant term is 1, i.e., $g(0)=1$.

We could use the recursive formula above to calculate an approximate solution for $h$, i.e., calculate the coefficients $(b_0, b_1, \cdots, b_{l-1})$, but this requires $O(l^2)$ complexity.

## Formal Power Series Ring and Polynomial Inversion

To calculate the inverse of a polynomial, we need to introduce an important concept, the formal power series ring (Formal Power Series Ring). If we extend the polynomial ring $F[X]$ to include polynomials with infinitely many non-zero higher-degree terms, we get the formal power series ring $F[[X]]$:

$$
p(X) = \sum_{i=0}^{\infty} a_iX^i \in F[[X]]
$$

For any $p_1, p_2\in F[[X]]$, addition and multiplication in the ring are defined as:

$$
p_1(X) + p_2(X) = \sum_{i=0}^{\infty}(a_i + b_i)X^i
$$

$$
p_1(X)\cdot p_2(X) = \sum_{i=0}^{\infty}\Big(\sum_{j=0}^{i}a_j b_{i-j}\Big)X^i
$$

Additionally, any non-zero $p(X)$ can be uniquely factored as $X^n p_0(X)$, where the constant term of $p_0(X)$ is non-zero. $F[[X]]$ is a UFD (Unique Factorization Domain). If we define the function $\delta(p) = n$, then $F[[X]]$ is a Euclidean Domain.

For any polynomial $f(X)\in F[X]$, we can view it as a power series with zero coefficients for higher-degree terms:

$$
f(X) = \sum_{i=0}^{d}a_iX^i + \sum_{i=d+1}^{\infty}0X^i
$$

We can also map any power series $p(X)$ to a polynomial in $F[X]$ using modular arithmetic:

$$
p(X) = \sum_{i=0}^{d}a_iX^i + O(X^{d+1}) \equiv f(X) \mod{X^d}
$$

Here, $O(X^{d+1})$ represents all terms of degree $X^{d+1}$ and higher. By marking terms higher than $X^d$ as tail terms we don't care about, we get an approximate representation of the power series $p(X)$, where $d$ represents the precision of the approximation.

So we can conclude that $F[X]$ is a subring of $F[[X]]$, and we can embed elements of $F[X]$ into $F[[X]]$ via a monomorphism:

$$
\begin{aligned}
\iota: & F[X] \to F[[X]] \\
& f(X) \mapsto \sum_{i=0}^{d}a_iX^i + \sum_{i=d+1}^{\infty}0X^i
\end{aligned}
$$

Why introduce the power series ring? Because the power series ring has another very useful **property**:

- Any power series $p(X)$ with a non-zero constant term has a multiplicative inverse $\tilde{p}(X)$ such that $p(X)\cdot \tilde{p}(X) = 1$

This conclusion seems a bit magical. Let's look at a simple example:

$$
p_1(X)\in \mathbb{F}_7[X] = 1 + 2X + 3X^2 + 2X^3
$$

Its multiplicative inverse is a potentially infinitely long power series. For convenience, we'll take only its first ten terms, i.e., with precision 10:

$$
\tilde{p}_1(X) = 1 + 5X + X^2 + 2X^3 + 4X^4 + 5X^5 + 2X^6 + X^7 + 3X^8 + X^9 + O(X^{10})
$$

And its tail term $O(X^{10})$ represents the sum of all terms after $X^{10}$.

We can try treating $\tilde{p}_1(X)$ without the tail term as a polynomial and multiplying it by $p_1(X)$ to see the result:

$$
\begin{aligned}
& p_1(X)\cdot (1 + 5X + X^2 + 2X^3 + 4X^4 + 5X^5 + 2X^6 + X^7 + 3X^8 + X^9)) \\
= & 1 + 6X^{10} + 2X^{11} + 2X^{12}
\end{aligned}
$$

We get a polynomial approximately equal to 1. The product has only terms of degree 10 or higher in its tail. In other words, if we consider a precision of 10, this product is indeed approximately equal to 1.

How do we calculate this possibly infinitely long $\tilde{p}(X)$? Let's derive the calculation formula.

Assume 
 
$$
\tilde{p}(X)=\sum_{i=0}^{\infty}b_iX^i
$$ 

Then clearly the following formula holds:

$$
\Big(\sum_{i=0}^{\infty}b_iX^i\Big)\Big(\sum_{i=0}^{\infty}a_iX^i\Big) = 1
$$

Since $a_0\neq 0$, we have $b_0 = \frac{1}{a_0}$ because $a_0b_0 = 1$. Then considering the coefficient of the first-degree term in the product, since the coefficient of $X$ is zero, we have:

$$
a_1b_0 + a_0b_1 = 0
$$

So we get: 

$$
b_1 = -\frac{a_1b_0}{a_0}
$$

Through similar derivation, we can get the expression for $b_2$:

$$
b_2 = -\frac{a_1b_1 + a_2b_0}{a_0}
$$

This pattern can be generalized to any $b_k$, giving a recursive calculation formula:

$$
b_k = -\frac{a_1b_{k-1} + a_2b_{k-2} + \cdots a_kb_0 }{a_0} = -\frac{1}{a_0}\Big(\sum_{j=1}^{k}a_{j}b_{k-j}\Big)
$$

This recursive formula can continue, calculating the coefficients of $\tilde{p}(X)$ from low-degree to high-degree until the required computational precision is reached.

The formal power series ring $F[[X]]$ is actually a local ring (Local Ring), meaning it has only one maximal ideal $\langle X \rangle$. All power series outside this maximal ideal (elements with non-zero constant terms) are unit elements, i.e., they have multiplicative inverses.

Back to our problem, given a polynomial $g\in F[X]$, we need to solve for its multiplicative inverse $h\in F[X]$ such that $g\cdot h \equiv 1 \mod{X^l}$. Since this polynomial $g$ is the reversed polynomial of some polynomial, we can be sure its constant term is non-zero. So, according to the algorithm above, we can find a $\tilde{g}\in F[[X]]$ such that $\tilde{g}\cdot g = 1$. Of course, we don't need to compute the exact result of $\tilde{g}$ since $\tilde{g}$ is an infinitely long power series; we only need to compute its approximate solution, stopping the recursive calculation once the precision exceeds $X^l$.

$$
h(X) = b_0 + b_1X + b_2X^2 + \cdots + b_{l-1}X^{l-1}
$$

At this point, we have an algorithm for polynomial division, but its complexity is $O(l^2)$.

Next, we'll introduce how to use Newton's method (Newton Iteration) to calculate the multiplicative inverse of a polynomial, with a complexity of $O(M(l))$, where $M(l)$ represents the computational cost of polynomial multiplication. If the finite field $F$ is FFT-friendly, then the complexity $O(M(l))$ is $O(l\log l)$.

## Newton's Method

Newton's method is an iterative algorithm in mathematical analysis for approximating the roots of polynomials. For example, for a differentiable function $\phi: \mathbb{R}\to \mathbb{R}$ on the real number field, to solve for $\alpha$ such that $\phi(\alpha)=0$. First, we guess an initial value $x=\alpha_0$, then iteratively solve for $\alpha_1, \alpha_2, \cdots, \alpha_k$ until $\alpha_k\cong\alpha$. As shown in the figure,

![Newton Iteration](image-1.png)

Suppose the slope of the tangent line of $\phi(x)$ at $x=\alpha_i$ is $\phi'(\alpha_i)$. Denote the intersection of the tangent line with the $x$-axis as $\alpha_{i+1}$. Then they satisfy the following equation:

$$
\frac{\phi(\alpha_i)}{
\alpha_i - \alpha_{i+1}
} = \phi'(\alpha_{i})
$$

After a simple formula transformation, we get the recursive expression for $\alpha_{i+1}$:

$$
\alpha_{i+1} = \alpha_i - \frac{\phi(\alpha_i)}{\phi'(\alpha_i)}
$$

By repeatedly iterating $k$ times, we can get a fast-converging approximate solution $\alpha_k\cong\alpha$.

Similarly, to solve $g\cdot h \equiv 1 \mod{X^l}$, we can construct a function $\Phi: F[[X]] \to F[[X]]$ on the formal power series ring, imitating the real-valued function $\phi(x)$:

$$
\Phi(Y) = \frac{1}{Y} - g
$$

Its derivative function is denoted as $\Phi'(Y)$:

$$
\Phi'(Y) = (\frac{1}{Y} - g)' = -\frac{1}{Y^2}
$$

The root $Y = \tilde{g}\in F[[X]]$ of this function will satisfy $\tilde{g}\cdot g = 1$:

$$
\Phi(\tilde{g}) = \frac{1}{\tilde{g}} - g = g - g = 0
$$

Please note again that since $\tilde{g}$ is a power series with infinitely many terms, we only need to get an approximate solution $h\approx \tilde{g}$, i.e.,

$$
\Phi(h) = \frac{1}{h} - g \approx 0
$$

This exact solution $\tilde{g}$ has non-zero coefficients for terms of degree $X^l$ or higher, but the approximate solution $h$ only needs to have the same coefficients as $\tilde{g}$ for lower-degree terms:

$$
\tilde{g} = h + O(X^l)
$$

Then obviously $h$ only needs to include all terms lower than $X^l$, making $h$ an element of the polynomial ring $F[X]/\langle X^l \rangle$:

$$
h = \sum_{i=0}^{l-1}b_iX^i \quad \in F[X]/\langle X^l \rangle
$$

And it satisfies:

$$
 g\cdot h = g \cdot (\tilde{g} - O(X^l)) = 1 - g\cdot O(X^l) \equiv 1 \mod{X^l}
$$

Now let's try to solve for $h$ using Newton's method, with the recursive formula:

$$
h_{i+1} = h_i - \frac{\Phi(h_i)}{\Phi'(h_i)} = h_i - \frac{\frac{1}{h_i} - g}{-\frac{1}{h_i^2}} = 2h_i - g\cdot h_i^2
$$

First, let's assume the constant term of $g$ is 1, so $g=1+O(X)$. Then let's guess an initial value for iteration: $h_0 = 1$. When we substitute $Y=h_0$ into $\Phi(Y)$:

$$
\Phi(h_0) = \frac{1}{h_0} - g = 1 - g = O(X)
$$

We can use $\bmod{X}$ modular arithmetic to **remove** the tail term $O(X)$ on the right side of the equation, getting:

$$
\Phi(h_0) = O(X) \equiv 0 \mod{X}
$$

This equation can be interpreted as: $h_0$ is an approximate root of the function $\Phi(Y)$ with **precision** $X$.

Then we use Newton's iteration formula to perform the first step of iteration, getting $h_1$:

$$
h_1 = h_0 - \frac{\Phi(h_0)}{\Phi'(h_0)} = 2h_0 - g\cdot h_0^2 = 2 - g
$$

Let's test how far $g\cdot h_1$ is from 1:

$$
1 - g\cdot h_1 = 1- g(2-g) = (1 - g)^2 = (O(X))^2 = O(X^2) \equiv 0 \mod{X^2}
$$

Now we can consider $h_1$ as an approximate root of the function $\Phi(Y)$ with **precision** $X^2$.

Continuing to iterate for $h_2$:

$$
h_2 = h_1 - \frac{\Phi(h_1)}{\Phi'(h_1)} = 2h_1 - g\cdot h_1^2 = 4 - 2g - g(2-g)^2 = 4 - 2g - 4g + 4g^2 - g^3
$$

Continue testing how far $g\cdot h_2$ is from 1. Assume $g = 1 + e_0X + e_1X^2 + e_2X^3 + O(X^4)$, then:

$$
\begin{aligned}
1 - g\cdot h_2 &= 1- g(4-6g+4g^2-g^3) \\
& = 1 - 4g + 6g^2 - 4g^3 + g^4 \\
\end{aligned}
$$

Substituting $g = 1 + e_0X + e_1X^2 + e_2X^3 + O(X^4)$ into the right side of the equation, skipping the tedious intermediate calculation steps, we can find that all coefficients for terms $X, X^2, X^3$ are eliminated to zero, finally getting:

$$
1 - g\cdot h_2 = \cdots = O(X^4) \equiv 0 \mod{X^4}
$$

So, $h_2$ is an approximate root of the function $\Phi(X)$ with precision $X^4$.

It's not hard to observe that each time we apply Newton's method, the calculation result gradually approaches the root of $\Phi(Y)$, and $(1-g\cdot h_i)$ only has terms of degree $X^{2^i}$ and higher in its tail. We can conjecture the following conclusion:

$$
g\cdot h_i \equiv 1 \mod{X^{2^i}}
$$

Here, $h_i$ is calculated through:

$$
h_{i} = h_{i-1} - \frac{\Phi(h_{i-1})}{\Phi'(h_{i-1})} \equiv 2\cdot h_{i-1} - g\cdot h_{i-1}^2 \mod{X^{2^{i}}}
$$

We can use mathematical induction to prove the theorem above:

- If $i = 0$, then $h_0 = 1$, clearly $g\cdot h_0 = 1 + O(X) \equiv 1 \mod{X}$, so the theorem holds for $i=0$.
- Assume $g\cdot h_i \equiv 1 \mod{X^{2^i}}$ holds, then considering $h_{i+1}$, expand $1-gh_{i+1}$ to similarly prove that $h_{i+1}$ satisfies the theorem equation:

$$
\begin{aligned}
1 - g\cdot h_{i+1} & = 1 - g\cdot \Big(2\cdot h_{i} - g\cdot h_{i}^2\Big) \\
& = 1 - 2g\cdot h_{i} + g^2\cdot h_{i}^2 \\
& = (1 - g\cdot h_{i})^2 \\
& \equiv 0 \mod{(X^{2^{i}})^2}
\end{aligned}
$$

Now we can understand why we initially used the $\mathsf{rev}(g)$ function to get the reversed polynomial of $g$. This is because when the reversed polynomial is treated as a power series, its constant term is stable. Although there are many cross terms in the higher-degree terms, they can be eliminated through modular arithmetic for precision.

## Polynomial Inversion Algorithm

Let's detail the calculation process for $h_k$:

$$
\begin{aligned}
h_{k+1}(X) & \equiv 2\cdot h_k(X) - f(X)\cdot h_{k}(X) \mod X^{2^k} \\
h_{k}(X) & \equiv 2\cdot h_{k-1}(X) - f(X)\cdot h_{k-1}(X) \mod X^{2^{k-1}}\\
\vdots \quad & \equiv \qquad \vdots \\
h_{2}(X) & \equiv 2\cdot h_{1}(X) - f(X)\cdot h_{1}(X) \mod X^{2}\\
h_{1}(X) & \equiv 2\cdot h_{0}(X) - f(X)\cdot h_{0}(X) \mod X\\
\end{aligned}
$$

If we assume that $l$ is a power of 2, i.e., $l=2^k$, then we can develop the following polynomial inversion algorithm (Python code). The parameter is a known polynomial $g(X)\in F[X]$, and the algorithm returns a polynomial $h\in F[X]/\langle X^l \rangle$ satisfying $gh\equiv 1 \mod{X^l}$:

```python
def poly_inverse(g: list[F], l: int):
    assert (g[0] == F.one())
    r = log_2_floor(l)
    h = [F(1)]
    for i in range(1, k+1):
        h_sq = poly_mul(h, h)
        f_h_sq = poly_mul(h_sq, f)
        h = poly_sub(poly_smul(h, F(2)), f_h_sq[:2**i])
    return h

def poly_sub(f, g):
    return [f[i] - g[i] for i in range(len(f))]

def poly_smul(f, c):
    return [f[i] * c for i in range(len(f))]

def poly_mul(f, g):
    ''' skip the implementation '''
    ...
```

How should we handle it if $l$ is not a power of 2?

We have two methods to address this. Let's first introduce the first method, from paper [CC11]. This method is very direct. Let $k$ be the integer power of 2 such that $l\leq k$. Then we have the following conclusion:
$$
X^k\mid (1 - gh) \Rightarrow  X^l\mid (1 - gh)
$$

This conclusion is very easy to prove, so we'll skip it here. We just need to think intuitively why it holds. If a power series calculates to zero with precision $X^k$, then it must be zero at lower precisions as well, just like how $1 + O(X^k)$ can definitely be represented as $1 + O(X^l)$. Therefore, we only need to calculate the polynomial $h^*$ satisfying $X^k\mid 1 - gh^*$, and then get $h = h^*\mod{X^l}$, which will definitely satisfy:

$$
X^l\mid 1 - gh
$$

So we can calculate the polynomial $h$ satisfying $X^k\mid 1 - gh$, and then get the polynomial $h$ satisfying $X^l\mid 1 - gh$ through modular arithmetic.

Another detail that needs to be handled is considering that the constant term of $g(0)$ might not be 1. This situation is very common because the reversed polynomial of $g$ is likely not a monic polynomial. Although we have a simple way to convert a non-monic polynomial to a monic one, this conversion process requires an additional $O(l)$ finite field multiplications. However, we can directly remove this constraint by setting the initial guess $h_0$ to $g(0)^{-1}$ and then continuing with the subsequent Newton's method calculations.

A third improvement is that in each polynomial multiplication operation, we can first truncate the polynomial according to precision, reducing the length of the polynomial and thus reducing computational cost. For example, when calculating $g\cdot h_{i-1}^2$, we only need to calculate $(g\bmod{X^{2^i}})\cdot h_{i-1}^2$, i.e., first truncate the polynomial $g$ according to precision, then perform the multiplication operation.

Here is the modified Python code:

```python
def poly_inverse_rev1(g: list[F], l: int):
    k = log_2_floor(l)
    h = [g[0].inverse()]
    for i in range(1, k+1):
        h_sq = poly_mul(h[:2**(i-1)], h[:2**(i-1)])
        g_h_sq = poly_mul(h_sq, g[:2**i])
        h = poly_sub(poly_smul(h, 2), g_h_sq[:2**i])
    
    h_sq = poly_mul(h, h)
    g_h_sq = poly_mul(h_sq[:l+1], g[:l+1])
    h = poly_sub(poly_smul(h[:l+1], 2), g_h_sq[:l+1])
    return h
```

### Complexity Analysis

The time complexity of this polynomial inversion algorithm is $3M(l) + 2l$.

First, in each round, there are two polynomial multiplications: one is $h_i^2$ with time complexity $M(2^{i-1})$, and one is $h_i^2\cdot g$ with time complexity $M(2^i)$. The time complexity for calculating $2h_i - g\cdot h_i^2$ is $2^i$.

The total cost of one iteration is as follows:
$$
M(2^i) + M(2^{i-1}) + 2^i \leq = \frac{3}{2}M(2^{i}) + 2^i
$$

The total cost for $r$ iterations is:

$$
\sum_{1\leq i \leq r} \Big(\frac{3}{2}M(2^i) + 2^i\Big) \lt 3M(2^r) + 2^{r+1}
$$

## Polynomial Division Algorithm

Now that we've mastered how to calculate the multiplicative inverse of a polynomial, let's outline the steps of the polynomial division algorithm. Suppose we have two polynomials $f, g\in F[X]$, where $f$ is of degree $n$, $g$ is of degree $m$, and $n\geq m$. The algorithm returns the quotient polynomial $q$ of degree $n-m$ and the remainder polynomial $r$ of degree strictly less than $m-1$, satisfying:

$$
f(X) = q(X)\cdot g(X) + r(X)
$$

The first step of the algorithm checks that the highest-degree coefficients of parameters $f$ and $g$ are non-zero, then calculates the difference in their degrees, denoted as $d=\deg{f}-\deg{g}$. Here we assume $\deg{f}\geq \deg{g}$.

The second step calculates the reversed polynomials of $f$ and $g$, denoted as $\mathsf{rev}_n(f)$ and $\mathsf{rev}_m(g)$, where $n=\deg{f}$ and $m=\deg{g}$.

The third step calculates the Inverse Element of $\mathsf{rev}_m(g)$ in the power series ring $F[[X]]$ with precision $X^{d+1}$, with the result denoted as $\tilde{g}_{d}=\mathsf{rev}_m(g)^{-1}$.

The fourth step calculates $q^* \equiv \mathsf{rev}_m(f)\cdot \tilde{g}_d \mod X^{d+1}$, denoted as $\mathsf{rev}_m(q)$.

The fifth step calculates $\mathsf{rev}_{n-m}(q^*)=\mathsf{rev}_{n-m}(\mathsf{rev}_{n-m}(q))=q$.

The sixth step calculates the remainder polynomial $r = f - q\cdot g$.

Here's the Python code for division, and then we'll analyze its complexity:

```python
def poly_div_rem(f: list[F], g: list[F]):
    assert(f[-1] != Fp(0))
    assert(g[-1] != Fp(0))
    f_deg = len(f) - 1
    g_deg = len(g) - 1
    if f_deg < g_deg:
        return [Fp(0)], f
    
    d = f_deg - g_deg
    
    rev_g = g[::-1]
    rev_f = f[::-1]

    rev_g_inv_prec_d_plus_1 = poly_inverse_rev1(rev_g, d+1)

    q = poly_mul(rev_f[:d+1], rev_g_inv_prec_d_plus_1)
    q = q[:d+1]

    q.reverse()

    r = poly_sub(f, poly_mul(q,g))
    remove_leading_zeros(r)
    return q, r
```

### Complexity Analysis

The third step of the algorithm requires $3M(l) + 2l$ polynomial multiplications; the fourth step requires one polynomial multiplication with time complexity $M(l)$; the sixth step requires one polynomial multiplication with time complexity $M(l)$, and one polynomial subtraction with time complexity $n$. So the total time complexity is:

$$
5M(l) + 2l + n
$$

## References

- [CC11] Zhengjun Cao, Hanyue Cao. Note on fast division algorithm for polynomials using Newton iteration. 2011. https://arxiv.org/pdf/1112.4014
- https://cs.uwaterloo.ca/~r5olivei/courses/2021-winter-cs487/lec5-ref.pdf
- https://math.stackexchange.com/questions/710252/multiplicative-inverse-of-a-power-series