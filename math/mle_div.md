# Polynomial Division and Ruffini's Rule

### Univariate Polynomial Division and Ruffini's Rule

According to Ruffini's rule, there is a close relationship between polynomial division and polynomial evaluation.

If we use polynomial long division to calculate $f(X)/(X-d)$, we get a quotient polynomial $q(X)$ and a remainder $r$, satisfying:

$$
f(X) = (X-d)\cdot q(X) + r
$$

This is the well-known polynomial remainder theorem, stating that the remainder equals $f(d)$. So when $f(X)$ minus the remainder, it can be divided evenly by $(X-d)$. Is there also a connection between the quotient polynomial $q(X)$ and $f(d)$?
Here's a conclusion: the quotient polynomial $q(X)$ is exactly the intermediate calculation result produced during the evaluation of $f(X)$ at $X=d$.

Representing $f(X)$ in coefficient form, we have:

$$
f(X) = a_0 + a_1X + a_2X^2 + \ldots + a_nX^n
$$

Rearranging, we get:

$$
f(X) = a_0 + X(a_1 + X(a_2 + \ldots + X(a_{n-1} + Xa_n)\ldots)
$$  

To calculate the "polynomial evaluation" $f(d)$, we substitute $X=d$ from left to right into the above equation:

$$
\begin{split}
    q_{n-1} &= d\cdot 0 + a_n\\
    q_{n-2} &= d\cdot q_{n-1} + a_{n-1} \\
    \vdots & \vdots \\
    q_1     &= d\cdot q_2 + a_2 \\
    q_0     &= d\cdot q_1 + a_1 \\
    v       &= d\cdot q_0 + a_0 \\
\end{split}
$$

And $(q_0, q_1, \ldots, q_{n-1})$ are precisely the coefficients of the quotient polynomial $q(X)$. In other words, the linear division process of a polynomial is actually the polynomial evaluation process.

Let's take a simple example: $f(X) = 5 + 3X + 2X^2 + X^3$. To calculate $f(-2)$, which is equivalent to calculating $f(X)/(X+2)$, the process is:

$$
\begin{array}{lll}
    q_2 &= (-2)\cdot 0 + 1 &= 1\\
    q_1 &= (-2)\cdot 1 + 2 &= 0\\
    q_0 &= (-2)\cdot 0 + 3 &= 3\\
    v   & = (-2)\cdot 3 + 5 &= -1\\
\end{array}
$$

We thus get the result $f(-2) = -1$ and incidentally obtain the quotient polynomial $q(X) = 3 + X^2$.

We can implement this calculation process with a simple loop:

```rust
fn div_poly(f: &[Scalar], d: Scalar) -> (Vec<Scalar>, Scalar) {
    let mut rem = Scalar::zero();
    let mut quo = Vec::new();

    for c in coeffs.iter().rev() {
        rem = rem * d + c;
        quo.insert(0, rem);
    }
    (quo, rem)
}
```

Actually, Ruffini's rule applies not just to linear polynomial division but to division by polynomials of any degree. This generalized algorithm is known as Synthetic Division.

So far, we've been discussing univariate polynomial division. What about MLE (Multilinear Extension) division? Fortunately, Ruffini's rule also applies to MLE polynomial division; the calculation process of MLE polynomial division is equivalent to the MLE polynomial evaluation process.

### MLE Polynomial Division

To warm up, when we divide an MLE by a univariate linear polynomial, we can view the MLE as a univariate polynomial, with other variables seen as mutually non-calculable constants. This way, we can use univariate polynomial division to quickly obtain the quotient polynomial (an $(n-1)$-variate MLE) and remainder.

For example:

$$
\tilde{f}(X_0, X_1, X_2) = 2\cdot X_0X_2 + 3\cdot X_1 + 4\cdot X_0
$$

The division is:

$$
\frac{2\cdot X_0X_2 + 3\cdot X_1 + 4\cdot X_0}{(X_2-a)} = \frac{(2\cdot X_0)X_2 + (3\cdot X_1 + 4\cdot X_0)}{(X_2-a)} = 2\cdot X_0, 3X_1 + (4+ 2a)X_0
$$

The remainder is $3X_1 + (4+ 2a)X_0$, and the quotient polynomial is an MLE, $2\cdot X_0$. Next, we can continue to divide the remainder polynomial by $(X_1-b)$:

$$
\frac{3X_1 + (4+ 2a)X_0}{(X_1-b)} = 3, (4+ 2a)X_0 + 3b
$$

The remainder becomes $(4+ 2a)X_0 + 3b$, and the quotient is $3$. Finally, we continue division with $(X_0-c)$:

$$
\frac{(4+ 2a)X_0 + 3b}{(X_0-c)} = 4+2a, 3b + (4+2a)c 
$$

The remainder is $3b + (4+2a)c$, and the quotient is $4+2a$.

We've now performed three complete MLE polynomial divisions, dividing by $(X_2-a)$, $(X_1-b)$, and $(X_0-c)$. We've obtained three quotients and a final remainder. Looking at the final remainder, it's exactly the value of $\tilde{f}(\vec{X})$ at $(c,b,a)$, perfectly matching Ruffini's rule:

$$
r= 3b + (4+2a)c  = \tilde{f}(c, b, a)
$$

The three quotient polynomials are:

$$
\begin{split}
    q_2(X_0,X_1) &= 2\cdot X_0\\
    q_1(X_0) &= 3\\
    q_0 &= 4+2a\\
\end{split}
$$

Computing polynomial division isn't so intuitive, so next we'll use Ruffini's rule to calculate MLE evaluation and simultaneously compute the quotient polynomial, making the process clearer. The MLE calculation can be viewed as a folding process. For every variable $X_k\in\{X_{n-1},\ldots, X_0\}$, we can view the polynomial as a univariate linear polynomial:

$$
\tilde{f}(\vec{X},X_k)=A + B\cdot X_k
$$

When we substitute $X_k = \alpha$, we get:

$$
\tilde{f}(\vec{X},X_k)=A + \alpha\cdot B
$$

If we represent $\tilde{f}$ as a coefficient vector, this process can be seen as a folding based on the factor $\alpha$. For example, for $\tilde{f}(X_0, X_1, X_2) = 2\cdot X_0X_2 + 3\cdot X_1 + 4\cdot X_0$, its coefficient vector is:

$$
\begin{array}{cccccccc}
(&0, &4, &3, &0, &0, &2, &0, &0 &) \\
&1, &X_0, &X_1, &X_0X_1, &X_2, &X_0X_2, &X_1X_2, &X_0X_1X_2& \\
\end{array}
$$

Each coefficient corresponds to the monomial in the second row. Next, if we want to calculate $f(c, b, a)$, we can use a split-and-fold approach:

$$
\begin{split}
(0,4,3,0) + a\cdot {\color{blue}(0,2,0,0)} & = (0, 4+2a, 3, 0)\\    
(0, 4+2a) + b\cdot {\color{blue}(3, 0)} & = (3b, 4+2a)\\
(3b) + c\cdot {\color{blue}(4+2a)} & = 3b+ (4+2a)c\\    
\end{split}
$$

In each round, we split the vector in half, add the left half to the right half multiplied by a factor. After three recursive rounds, we finally get the result $3b+ (4+2a)c$, which matches the remainder from our earlier polynomial division. As mentioned before, according to Ruffini's rule, the quotient polynomial should be the intermediate result during the evaluation. So where do we find traces of the quotient polynomial in this folding process?

The quotient polynomials are the MLEs with the blue-marked vectors as "coefficient vectors", i.e., the right half of the vector in each round of the split-and-fold process. Let's verify: the first row's quotient polynomial is $2\cdot X_0$, which is the coefficient of monomials $(1,X_0,X_1,X_0X_1)$, so the first quotient polynomial is $2X_0$; the second row's quotient is $(3,0)$, which is a constant polynomial; the third row's quotient is $(4+2a)$, also a constant polynomial. This matches the results we obtained through manual division.

> TODO: q_k = f(... 1+u_k, ...) - f(... u_k, ...)

However, in the ZeroMorph protocol, MLEs are represented in "value form". If we want to use the above method for division, we'd need to first convert the MLE from value form to coefficient form. The generalized algorithm for this conversion (similar to FFT for univariate polynomials) has a time complexity of $O(N\log^2N)$, or $O(2^n\cdot n^2)$. And after calculating the quotient, we'd need to perform the inverse transformation on the $n-1$ quotient polynomials to go from coefficient form back to value form. This would introduce non-negligible conversion overhead.

In fact, we can use the split-and-fold approach to directly compute evaluation on the MLE's "value form" and simultaneously calculate the quotient polynomial, completely avoiding the back-and-forth conversion between "value form" and "coefficient form".

Let's see how evaluation is calculated on the MLE's value form:

$$
\tilde{f}(X_0,X_1,\ldots, X_{n-2}, X_{n-1}) = \sum_{\vec{i}\in\{0,1\}^n} f_{\vec{i}} \cdot \tilde{eq}(\vec{i}, \vec{X})
$$

Suppose the value form of $\tilde{f}$ is the vector $(f_{000}, f_{100}, \ldots, f_{111})$, corresponding to the HyperCube $\{0,1\}^3$.

We substitute values for $X_{n-1},\ldots, X_0$ from right to left. For instance, if we first substitute $X_{n-1}=u_{n-1}$, then the value form of $\tilde{f}^{(1)}(X_0,X_1,\ldots, X_{n-2})$ is:

$$
(1-u_{n-1})\cdot(f_0, f_1, \ldots, f_{2^{n-2}-1}) +  u_k\cdot(f_{2^{n-2}}, f_{2^{n-2}+1}, \ldots, f_{2^{n-1}-1})
$$

This calculation is also a split-and-fold process, which can be recursively continued until the vector is folded into one dimension.

Using our previous example MLE polynomial, $\tilde{f}(X_0, X_1, X_2) = 2\cdot X_0X_2 + 3\cdot X_1 + 4\cdot X_0$, its value form is:

$$
\begin{array}{cccccccc}
(&0, &4, &3, &7, &0, &6, &3, &9 &) \\
&f_{000}, &f_{100}, &f_{010}, &f_{110}, &f_{001}, &f_{101}, &f_{011}, &f_{111}& \\
\end{array}
$$

For instance, if we substitute $(X_0=1,X_1=0,X_2=1)$, then $\tilde{f}(1, 0, 1)=2+4=6$, which corresponds to the $f_{101}$ element in the value vector.

Now, let's substitute $(X_0=c,X_1=b,X_2=a)$ and use the split-and-fold approach to complete the evaluation:

$$
\begin{split}
(1-a)\cdot(0,4,3,7) + a\cdot (0,6,3,9) & = (0, 4+2a, 3, 7+2a)\\    
(1-b)\cdot(0, 4+2a) + b\cdot (3, 7+2a) & = (3b, (1-b)(4+2a)+b(7+2a)) = (3b, 4+2a+3b)\\
(1-c)\cdot(3b) + c\cdot (4+2a+3b) & =  3b - 3bc +4c+2ac + 3bc = 3b+ (4+2a)c\\    
\end{split}
$$

As expected, the final result is still $3b+ (4+2a)c$, though it's not as easy to find the quotient polynomial in this calculation.

The quotient polynomial for each row is the right vector minus the left vector. Let's examine each row:

$$
\begin{split}
q_2(X_0,X_1): & (0, 6, 3, 9) - (0, 4, 3, 7) = (0, 2, 0, 2)\\
q_1(X_0):     & (3, 7+2a) - (0, 4+2a) = (3, 3)\\
q_0:          & (4+2a+3b) - (3b) = 4+2a\\
\end{split}
$$

Remember, these are the value forms of the quotient polynomials. We can convert them to "coefficient form" through polynomial interpolation and compare with the earlier quotients.

Another method, as described earlier, is to map a low-dimensional HyperCube to a high-dimensional one, which is actually a repetition of the low-dimensional Cube. So, seeing that the value form of $q_2(X_0,X_1)$ is $(0, 2, 0, 2)$, which is a repetition in a 2-dimensional HyperCube, indicates that the coefficient related to the variable $X_1$ is zero. Thus, we can quickly deduce $q_2(X_0,X_1) = 2X_0$. Similarly, the value form of $q_1(X_0)$ is $(3,3)$, also a repeating pattern, indicating that the coefficients of monomials containing the $X_0$ variable are zero. Hence, $q_1(X_0) = 3$. Finally, with $q_0() = 4+2a$, these matches perfectly with the quotient polynomials calculated using the coefficient form earlier.