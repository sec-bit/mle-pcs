# Computation of Inverse in Extension Fields

For an extension field $\mathbb{F}_{p^n}$ over a base field $\mathbb{F}_p$, if we directly apply the Extended Euclidean Algorithm or Fermat's Little Theorem to compute inverses, it requires multiple multiplication operations in $\mathbb{F}_{p^n}$, which is computationally expensive. An optimization approach is to convert the inverse computation in the extension field to inverse computation in the base field or a subfield. This conversion introduces a small number of additional multiplication operations, but reduces the overall computational complexity.

## Quadratic Extension

Let's consider a simple case where the base field is $\mathbb{F}_p$ and the extension field is $\mathbb{F}_{p^2}$.

We specify an irreducible polynomial $f(X)\in\mathbb{F}_p[X]$, and construct the extension field $\mathbb{F}_{p^2}$ as $\mathbb{F}_p[X]/(f(X))$.

$$
f(X) = X^2 - c_0
$$

Then 

$$
\mathbb{F}_{p^2} = \mathbb{F}_{p}[X]/(X^2 - c_0)
$$

Let's assume $\alpha$ is a root of $X^2-c_0$ in $\mathbb{F}_{p^2}$. Then $\mathbb{F}_{p^2}$ can be written as $\mathbb{F}_{p}[\alpha]$.

According to finite field theory, elements in $\mathbb{F}_{p^2}$ can be represented as $a_0 + a_1 \alpha$, where $a_0, a_1 \in \mathbb{F}_{p}$.

$$
\mathbb{F}_{p^2} = \{a_0 + a_1 \alpha \mid a_0, a_1 \in \mathbb{F}_{p}\}
$$

To find the inverse of $a = a_0 + a_1 \alpha$, denoted as $a^{-1}$, we can convert it to elements in $\mathbb{F}_{p}$.
Let $a^{-1} = b_0 + b_1 \alpha$, then we have

$$
(a_0 + a_1 \alpha)(b_0 + b_1 \alpha) = 1
$$

Simplifying the left side of the equation and using $\alpha^2 = c_0$, we get:

$$
(a_0b_0 + c_0\cdot a_1b_1) + (a_0b_1 + a_1b_0)\alpha = 1
$$

Since there is no $\alpha$ term on the right side, we have $a_0b_1 + a_1b_0 = 0$ and $a_0b_0 + c_0\cdot a_1b_1 = 1$. This can also be represented in matrix form:

$$
\begin{bmatrix}
a_0 & c_0\cdot a_1 \\
a_1 & a_0
\end{bmatrix}
\begin{bmatrix}
b_0 \\
b_1 \\
\end{bmatrix}
= \begin{bmatrix}
1 \\ 0
\end{bmatrix}
$$

By inverting the matrix on the left, we can obtain the computation matrix for $b_0$ and $b_1$:

$$
\begin{bmatrix}
b_0 \\
b_1 \\
\end{bmatrix}
=
\begin{bmatrix}
a_0 & c_0\cdot a_1 \\
a_1 & a_0
\end{bmatrix}^{-1}
\begin{bmatrix}
1 \\
0 \\
\end{bmatrix}
=
(a_0^2 - c_0\cdot a_1^2)^{-1}
\begin{bmatrix}
a_0 & - c_0\cdot a_1 \\
-a_1 & a_0
\end{bmatrix}
\begin{bmatrix}
1 \\
0 \\
\end{bmatrix}
$$

The term $(a_0^2 - c_0\cdot a_1^2)^{-1}$ is an element in $\mathbb{F}_{p}$. Thus, computing $a^{-1}$ is converted to an inverse operation in $\mathbb{F}_{p}$, with a constant number (five in this case) of additional multiplication operations in $\mathbb{F}_{p}$.

```python
def quadratic_inv(t: K, c0: F):
    if t == K(0):
        raise ValueError("t=0")
    g = K.gen()   # root of f(X)=(X^2 - c0)
    [a0, a1] = t.list()
    a0_sq = a0 * a0
    a1_sq = a1 * a1
    
    scalar = a0_sq - c0 * a1_sq
    scalar_inv = scalar.inverse()

    b0 = scalar_inv * a0
    b1 = scalar_inv * (-a1)
    
    return b0 + b1 * g
```

This method is not limited to binomial extensions but is applicable to any irreducible polynomial. For example, if we generate $\mathbb{F}_{p^2}$ using the polynomial:

$$
g(X) = X^2 + c_1X + c_0
$$

Then exploring the product of two elements in $\mathbb{F}_{p^2}$:

$$
\begin{aligned}
(a_0 + a_1 \alpha)(b_0 + b_1 \alpha) &= a_0b_0 + (a_0b_1 + a_1b_0)\alpha + a_1b_1 \alpha^2 \\
&= a_0b_0 + (a_0b_1 + a_1b_0)\alpha + a_1b_1 (c_1\alpha + c_0) \\
&= (a_0b_0 + c_0a_1b_1) + (a_0b_1 + a_1b_0 + c_1a_1b_1)\alpha
\end{aligned}
$$

In matrix form:

$$
\begin{bmatrix}
a_0 & c_0\cdot a_1 \\
a_1 & a_0+c_1a_1
\end{bmatrix}
\begin{bmatrix}
b_0 \\
b_1 \\
\end{bmatrix}
= \begin{bmatrix}
1 \\ 0
\end{bmatrix}
$$

Inverting the matrix on the left:

$$
\begin{bmatrix}
a_0 & c_0\cdot a_1 \\
a_1 & a_0+c_1a_1
\end{bmatrix}^{-1}
=
(a_0^2 -a_1^2c_0 + a_0a_1c_1)^{-1}
\begin{bmatrix}
a_0+a_1c_1 & -a_1c_0 \\
-a_1 & a_0
\end{bmatrix}
$$

## Cubic Extension

We still assume the base field is $\mathbb{F}_p$ and the cubic extension field is $\mathbb{F}_{p^3}$.

For simplicity, we continue to specify a binomial irreducible polynomial $f(X)\in\mathbb{F}_p[X]$ and construct the extension field $\mathbb{F}_{p^3}$ as $\mathbb{F}_p[X]/(f(X))$.

$$
f(X) = X^3 - c_0
$$

Let $\alpha$ be a root of $X^3-c_0$ in $\mathbb{F}_{p^3}$. Then elements in $\mathbb{F}_{p^3}$ can be represented as $a_0 + a_1 \alpha + a_2 \alpha^2$, where $a_0, a_1, a_2 \in \mathbb{F}_{p}$.

Let $a^{-1} = b_0 + b_1 \alpha + b_2 \alpha^2$, then we have

$$
(a_0 + a_1 \alpha + a_2 \alpha^2)(b_0 + b_1 \alpha + b_2 \alpha^2) = 1
$$

After expansion and substituting $\alpha^3 = c$, we get:

$$
(a_0b_0 + c_0\cdot a_2b_1 + c_0\cdot a_1b_2) + (a_0b_1 + a_1b_0 + c_0\cdot a_2b_2) \alpha + (a_0b_2 + a_1b_1 + a_2b_0) \alpha^2 = 1
$$

We can write this equation in matrix form:

$$
\begin{bmatrix}
a_0 & c_0\cdot a_2 & c_0\cdot a_1 \\
a_1 & a_0 & c_0\cdot a_2 \\
a_2 & a_1 & a_0
\end{bmatrix}
\begin{bmatrix}
b_0 \\
b_1 \\
b_2 \\
\end{bmatrix}
= \begin{bmatrix}
1 \\
0 \\
0 \\
\end{bmatrix}
$$

We invert the matrix on the left:

$$
\begin{bmatrix}
a_0 & c_0\cdot a_2 & c_0\cdot a_1 \\
a_1 & a_0 & c_0\cdot a_2 \\
a_2 & a_1 & a_0
\end{bmatrix}^{-1}
=
(s)^{-1}
\begin{bmatrix}
a_0^2 - c_0\cdot a_1\cdot a_2 
& c_0\cdot a_1^2 - c_0\cdot a_0\cdot a_2 
& c_0^2\cdot a_2^2 - c_0\cdot a_0\cdot a_1 
\\
c_0\cdot a_2^2 - a_0\cdot a_1 
& a_0^2 - c_0\cdot a_1\cdot a_2 
& c_0\cdot a_1^2 - c_0\cdot a_0\cdot a_2 
\\
a_1^2 - a_0\cdot a_2 
& c\cdot a_2^2 - a_0\cdot a_1 
& c\cdot a_1\cdot a_2 - a_0^2
\end{bmatrix}
$$

Where $s=a_0^3 + c_0\cdot a_1^3 + c_0^2\cdot a_2^3 - 3c_0\cdot a_0\cdot a_1\cdot a_2$.

Next, we can convert the computation of $b_0, b_1, b_2$ to an inverse operation in $\mathbb{F}_{p}$, $s^{-1}$, multiplied by elements in the base field:

$$
\begin{bmatrix}
b_0 \\
b_1 \\
b_2 \\
\end{bmatrix}
= s^{-1}
\begin{bmatrix}
a_0^2 - c_0\cdot a_1\cdot a_2  \\
c_0\cdot a_2^2 - a_0\cdot a_1  \\
a_1^2 - a_0\cdot a_2 
\end{bmatrix}
$$

```python
def cubic_inv(t: K, w: F):
    [a0, a1, a2] = t.list()
    g = K.gen()
    a0_sq = a0 * a0
    a1_sq = a1 * a1
    a2_w = w * a2
    a0_a1 = a0 * a1

    scalar = a0*a0_sq + w*a1*a1_sq + a2_w * a2_w * a2 - F(3) * a2_w * a0_a1
    scalar_inv = scalar.inverse()
    b0 = scalar_inv * (a0_sq - a1 * a2_w)
    b1 = scalar_inv * (a2_w * a2 - a0_a1)
    b2 = scalar_inv * (a1_sq - a0 * a2)
    return b0 + b1 * g + b2 * g^2
```

By combining some reusable multiplication operations in $\mathbb{F}_{p}$, we ultimately require 14 multiplication operations in $\mathbb{F}_{p}$ plus one inverse operation in $\mathbb{F}_{p}$.

## Quartic Extension

For quartic extensions, we can still use the approach above, though the complexity of matrix inversion increases rapidly.

We can, of course, convert a quartic extension into two steps of quadratic extensions.

$$
\mathbb{F}_{p^4} = \mathbb{F}_{p}(\alpha)(\beta)
$$

Then the first step of the inverse operation converts the inverse in the quartic extension field to an inverse in the quadratic extension field, and finally uses the quadratic extension inverse formula to convert it to an inverse operation in the base field.

If $\mathbb{F}_{p^4}$ is a direct quartic extension, but the irreducible polynomial used is a quartic binomial, then we have a more optimized approach (this approach comes from the implementation of RicsZero).

$$
\mathbb{F}_{p^4}\cong\mathbb{F}_{p}[X]/(X^4-c)
$$

To calculate the multiplicative inverse $\theta^{-1}$ of an element $\theta$, i.e.,

$$
\frac{1}{\theta} = \frac{1}{a_0 + a_1\alpha + a_2\alpha^2 + a_3\alpha^3}
$$

where $\alpha$ is a root of the irreducible polynomial $X^4-c=0$, satisfying $\alpha^4-c=0$. We multiply both the numerator and denominator of the above equation by an auxiliary element $\zeta$

$$
\zeta = a_0 - a_1\alpha + a_2\alpha^2 - a_3\alpha^3
$$

Thus

$$
\frac{1}{\theta} = \frac{\zeta}{\zeta\cdot\theta} 
$$

Since two coefficients in $\theta$ and $\zeta$ have opposite signs, two coefficients (related to $\alpha$ and $\alpha^3$) in the product $\zeta\cdot\theta$ will be eliminated:

$$
\zeta\cdot\theta = (a_0^2 + a_2^2\cdot c - 2a_1a_3\cdot c) + (2a_0a_2 - a_1^2 + a_3^2\cdot c)\cdot \alpha^2
$$

We let $\zeta\cdot\theta = b_0 + b_1\alpha^2$, where $b_0, b_1\in\mathbb{F}_{p}$, defined as:

$$
\begin{aligned}
b_0 &= a_0^2 + a_2^2\cdot c - 2a_1a_3\cdot c \\
b_1 &= 2a_0a_2 - a_1^2 + a_3^2\cdot c
\end{aligned}
$$

We introduce another auxiliary element $\xi=b_0 - b_1\alpha^2$, and again multiply both the numerator and denominator of $\theta^{-1}$ by $\xi$:

$$
\frac{1}{\theta} = \frac{\zeta}{\zeta\cdot\theta} 
= \frac{\zeta\cdot\xi}{\zeta\cdot\xi\cdot\theta}
$$

So the denominator $\zeta\cdot\xi\cdot\theta$ will be an element in $\mathbb{F}_{p}$, derived as follows:

$$
\zeta\cdot\xi\cdot\theta = (b_0 + b_1\alpha^2)(b_0-b_1\alpha^2) = b_0^2 - b_1^2\alpha^4 = b_0^2 - b_1^2\cdot c
$$

Note that since this approach requires the irreducible polynomial to be a binomial, i.e., $X^4-c$, the $\alpha^4$ term in the above equation can be completely replaced by $c$, ensuring that $\zeta\cdot\xi\cdot\theta$ is an element in $\mathbb{F}_{p}$. If the irreducible polynomial were of the form $X^4-c'\cdot X+ c$, the right side of the equation would introduce an extra $\alpha$ term, which would be difficult to handle.

Finally, we can derive the computation formula for $\theta^{-1}$:

$$
\frac{1}{\theta} 
= \frac{\zeta\cdot\xi}{\zeta\cdot\xi\cdot\theta}
= \frac{(a_0 - a_1\alpha + a_2\alpha^2 - a_3\alpha^3)
\cdot (b_0 - b_1\alpha^2)}{b_0^2 - b_1^2\cdot c}
$$

Clearly, the denominator of the above equation is an element in $\mathbb{F}_{p}$. And the coefficients of $\alpha$ in the numerator are products of several elements in $\mathbb{F}_{p}$.

## Inverse Algorithm Based on Frobenius Map

The core idea of the algorithms above is to convert the inverse operation in the extension field to an inverse operation in the base field.

Based on the Frobenius Map, we can also convert the inverse operation in the extension field to an inverse operation in the base field.

For an n-degree extension field $\mathbb{F}_{p^n}$, its Frobenius Map is $Frob_n: \mathbb{F}_{p^n} \to \mathbb{F}_{p^n}$, defined as $Frob_n(\alpha) = \alpha^{p}$.

For any element $\alpha$ in $\mathbb{F}_{p^n}$, we can obtain all its conjugate elements through the Frobeinus Map:

$$
\alpha, \alpha^p, \alpha^{p^2}, \cdots, \alpha^{p^{n-1}}
$$

The product of these conjugate elements (called the Norm of $\alpha$) is precisely an element in $\mathbb{F}_{p}$:

$$
\alpha \cdot \alpha^p \cdot \alpha^{p^2} \cdots \alpha^{p^{n-1}} = c
$$

Why? Here's a simple proof.

Suppose the characteristic polynomial of $\alpha$ is $f(X)$, then

$$
f(X) = (X-\alpha)(X-\alpha^p)(X-\alpha^{p^2})\cdots(X-\alpha^{p^{n-1}})
$$

where the constant term of $f(X)$ is exactly $c=\alpha \cdot \alpha^p \cdot \alpha^{p^2} \cdots \alpha^{p^{n-1}}$, and since $f(X)\in\mathbb{F}_{p}[X]$, we have $c\in\mathbb{F}_{p}$. Besides, the Norm Map is also a commonly used homomorphism from $\mathbb{F}_{p^n}$ to $\mathbb{F}_{p}$.

So we can leverage the properties of the Norm Map to calculate the multiplicative inverse $\theta^{-1}$ of any element $\theta\in\mathbb{F}_{p^n}$.

$$
\theta^{-1} = \theta^{-r} \cdot \theta^{r-1} 
$$

Here $r$ is calculated as:

$$
r = \frac{p^n-1}{p-1} = 1 + p + p^2 + \cdots + p^{n-1}
$$

Then according to the definition, $\theta^{r}$ is exactly the Norm of $\theta$:

$$
\theta^{r} = \theta\cdot\theta^p\cdot\theta^{p^2}\cdots\theta^{p^{n-1}} = c
$$

To calculate $\theta^{-1}$, we also need to calculate $\theta^{r-1}$, which is an element in $\mathbb{F}_{p^n}$. However, after analysis, we can use the following formula to calculate $\theta^{-1}$ "recursively":

$$
\begin{aligned}
\theta^{r-1} &= \prod_{i=1}^{n-1} \theta^{p^i} \\
        &= (((1\cdot \theta)^p \cdot \theta)^p \cdot \cdots \cdot \theta)^p
\end{aligned}
$$

The Python code is as follows:

```python
def frobenius_map(a: K):
    return a^(K.characteristic())

def frobenius_inv(a: F, degree: int):
    # compute a^{r-1}
    s = F(1)
    for i in range(1, degree):
        s = frobenius_map(s * a)
    t = s * a
    t_inv = t.inverse()

    return s * t_inv
```

As you can see, this algorithm is a general algorithm, and there are no assumptions about the structure of the extension field or the irreducible polynomial.

### Optimization of Frobenius Map for Binomial Extension Fields

If we only consider binomial extension fields, we can further optimize the computation of the Frobenius Map.

Assume the extension field is defined as:

$$
\mathbb{F}_{p^n} = \mathbb{F}_{p}[X]/(X^n - e)
$$

where $e$ is an element in $\mathbb{F}_{p}$. Let $\beta^n-e=0$, then $\beta$ is an element in $\mathbb{F}_{p^n}$ and satisfies:

$$
\beta^n = c
$$

Any element $\alpha$ can be represented as a coefficient vector in the power basis of $\beta$:

$$
\alpha = a_0 + a_1\beta + a_2 \beta^2 + \cdots + a_{n-1} \beta^{n-1}
$$

Then the Frobenius Map of $\alpha$ is $\alpha^p$, which can be derived as follows:

$$
\begin{aligned}
\alpha^p &= (a_0 + a_1\beta + a_2 \beta^2 + \cdots + a_{n-1} \beta^{n-1})^p \\
    &= a_0^p + a_1^p\beta^p + a_2^p\beta^{2p} + \cdots +  a_{n-1}^p\beta^{p(n-1)} \\
    &= a_0 + a_1\beta^p + a_2\beta^{2p} + \cdots +  a_{n-1}\beta^{p(n-1)} \\
    &= a_0 + a_1\cdot (\beta^{p-1})\cdot \beta  + a_2\cdot (\beta^{p-1})^{2}\cdot \beta^2 + \cdots +  a_{n-1}\cdot (\beta^{p-1})^{(n-1)} \cdot \beta^{n-1}
\end{aligned}
$$

So $\alpha^p$ can be represented as the dot product of the following vector and $(1,\beta,\beta^2,\cdots,\beta^{n-1})$:

$$
(a_0, a_1\cdot (\beta^{p-1}), a_2\cdot (\beta^{p-1})^{2}, \cdots, a_{n-1}\cdot (\beta^{p-1})^{(n-1)})
$$

Let $z = \beta^{p-1}$, and if $n\mid (p-1)$, then $z\in\mathbb{F}_{p}$, so its computation only involves calculations in the base field.

$$
z = \beta^{p-1} = c^{\frac{p-1}{n}}
$$

Thus, the coefficient representation of $\alpha^p$ is as follows:

$$
(a_0, a_1\cdot z, a_2\cdot z^2, \cdots, a_{n-1}\cdot z^{n-1})
$$