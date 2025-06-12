# Complexity Analysis of Gemini-PCS Algorithm

- Jade Xie <jade@secbit.io>
- Yu Guo <yu.guo@secbit.io>

## Optimized Version 1

- Protocol document: [Gemini-PCS (Part III)](https://github.com/sec-bit/mle-pcs/blob/main/gemini/Gemini-PCS-3.md)
- Corresponding Python code: [bcho_pcs.py](https://github.com/sec-bit/mle-pcs/blob/main/src/bcho_pcs.py)

The following protocol proves that a multilinear extension (MLE) polynomial $\tilde{f}(X_0, X_1, \ldots, X_{n-1})$ evaluates to $v = \tilde{f}(u_0, u_1, \ldots, u_{n-1})$ at point $\vec{u}=(u_0, u_1, \ldots, u_{n-1})$. Here $\tilde{f}(X_0, X_1, \ldots, X_{n-1})$ is expressed in coefficient form as:

$$
\tilde{f}(X_0, X_1, \ldots, X_{n-1}) = \sum_{i=0}^{n-1} f_i\cdot X_0^{i_0}X_1^{i_1}\cdots X_{n-1}^{i_{n-1}}
$$

### Common Input

1. Commitment to the vector $\vec{f}=(f_0, f_1, \ldots, f_{n-1})$ as $C_f$

$$
C_f = \mathsf{KZG10.Commit}(\vec{f})
$$

2. Evaluation point $\vec{u}=(u_0, u_1, \ldots, u_{n-1})$

3. $v = \tilde{f}(u_0, u_1, \ldots, u_{n-1})$

### Witness

1. Coefficients of polynomial $f(X)$: $f_0, f_1, \ldots, f_{n-1}$

### Round 1

1. Prover computes $h_1(X), h_2(X), \ldots, h_{n-1}(X)$ such that:

$$
h_{i+1}(X^2) = \frac{h_i(X) + h_i(-X)}{2} + u_i\cdot \frac{h_i(X) - h_i(-X)}{2X}
$$

where $h_0(X) = f(X)$

2. Prover computes commitments $(H_1, H_2, \ldots, H_{n-1})$ such that:

$$
H_{i+1} = \mathsf{KZG10.Commit}(h_{i+1}(X))
$$

3. Prover sends $(H_1, H_2, \ldots, H_{n-1})$

> Prover:
>
> - For $i = 1, \ldots, n-1$, compute polynomial $h_i$ using the formula:
>
> $$
> h_{i}(X) = h_e^{(i-1)}(X) + u_{i-1} \cdot h_o^{(i-1)}(X)
> $$
>
> > 💡 The prover doesn't need to compute and send $h_n(X)$ because the final polynomial is a constant polynomial equal to the evaluation result $v$, which the Verifier can verify by querying $h_{n-1}(X)$.
>
> To compute $h_i(X)$, we use the above formula. The coefficients of $h_{i-1}(X)$ are known, and $h_e^{(i-1)}(X)$ and $h_o^{(i-1)}(X)$ are the even and odd coefficients of $h_{i-1}(X)$ respectively. The main complexity lies in computing $u_{i-1} \cdot h_o^{(i-1)}(X)$, which involves multiplication in the finite field. $h_{i-1}(X)$ has $2^{n-(i-1)}$ coefficients, so $h_o^{(i-1)}(X)$ has $2^{n-i}$ coefficients. Thus, the complexity for multiplying $u_{i-1}$ with these coefficients is $2^{n-i} ~ \mathbb{F}_{\mathsf{mul}}$.
>
> Therefore, the complexity for computing $h_1(X), \ldots, h_{n-1}(X)$ is:
>
> $$
> \sum_{i=1}^{n-1} 2^{n-i} ~ \mathbb{F}_{\mathsf{mul}} = (2^n - 2) ~ \mathbb{F}_{\mathsf{mul}}
> $$
>
> - The complexity for computing $H_1 = [h_{1}(\tau)]_1, \ldots, H_{n-1} = [h_{n-1}(\tau)]_1$ is:
>
> $$
> \sum_{i=1}^{n-1} \mathsf{msm}(2^{n-i}, \mathbb{G}_1) = \sum_{i=1}^{n-1} \mathsf{msm}(2^i, \mathbb{G}_1)
> $$
>
> Thus, the total computational complexity for this round is:
>
> $$
> (2^n - 2) ~ \mathbb{F}_{\mathsf{mul}} + \sum_{i=1}^{n-1} \mathsf{msm}(2^i, \mathbb{G}_1)
> $$

### Round 2

1. Verifier sends random point $\beta \in \mathbb{F}_p$

2. Prover computes $h_0(\beta), h_1(\beta), \ldots, h_{n-1}(\beta)$

3. Prover computes $h_0(-\beta), h_1(-\beta), \ldots, h_{n-1}(-\beta)$

4. Prover computes $h_0(\beta^2)$

5. Prover sends $\{h_i(\beta), h_i(-\beta)\}_{i=0}^{n-1}$ and $h_0(\beta^2)$

Prover:

- Computing $\beta^2$ has a complexity of $\mathbb{F}_{\mathsf{mul}}$, while computing $-\beta$ only involves addition/subtraction in the finite field, which we don't count.
- Using Horner's method to evaluate a polynomial at a point requires as many field multiplications as there are coefficients. Thus, computing $\{h_i(\beta), h_i(-\beta)\}_{i=0}^{n-1}$ has a complexity of:

$$
2 \sum_{i=0}^{n-1} 2^{n-i} ~ \mathbb{F}_{\mathsf{mul}} = (2^{n+1} - 4) ~ \mathbb{F}_{\mathsf{mul}}
$$

- Computing $h_0(\beta^2)$ has a complexity of $2^n ~ \mathbb{F}_{\mathsf{mul}}$

Therefore, the total complexity for this round is:

$$
\mathbb{F}_{\mathsf{mul}} + (2^{n+1} - 4) ~ \mathbb{F}_{\mathsf{mul}} + 2^n ~ \mathbb{F}_{\mathsf{mul}} = (3 \cdot 2^n - 3) ~ \mathbb{F}_{\mathsf{mul}}
$$


> 🎈 In the code, the Prover also computes $\{h_i(\beta^2)\}_{i=1}^{n-1}$, which isn't necessary and could save computation. In that case, the Verifier would need to compute these values during verification, increasing its computational load.
>
> ```python
> # Compute evaluations of h_i(X) at beta, -beta, beta^2
> evals_pos = []
> evals_neg = []    
> evals_sq = []
> for i in range(k):
>     poly = h_poly_vec[i]
>     poly_at_beta = UniPolynomial.evaluate_at_point(poly, beta)
>     poly_at_neg_beta = UniPolynomial.evaluate_at_point(poly, -beta)
>     poly_at_beta_sq = UniPolynomial.evaluate_at_point(poly, beta * beta)
>     evals_pos.append(poly_at_beta)
>     evals_neg.append(poly_at_neg_beta)
>     evals_sq.append(poly_at_beta_sq)
> ```

### Round 3


1. Verifier sends random value $\gamma \in \mathbb{F}_p$ to aggregate multiple polynomials

2. Prover computes $h(X)$:

$$
h(X) = h_0(X) + \gamma \cdot h_1(X) + \gamma^2 \cdot h_2(X) + \cdots + \gamma^{n-1} \cdot h_{n-1}(X)
$$

3. Define a new Domain $D$ containing 3 elements:

$$
D = \{\beta, -\beta, \beta^2\}
$$

4. Prover computes a quadratic polynomial $h^*(X)$ that interpolates $h(X)$ at the points in $D$:

$$
h^*(X) = h(\beta) \cdot \frac{(X+\beta)(X-\beta^2)}{2\beta(\beta-\beta^2)} + h(-\beta) \cdot \frac{(X-\beta)(X-\beta^2)}{2\beta(\beta^2+\beta)} + h(\beta^2) \cdot \frac{X^2-\beta^2}{\beta^4-\beta^2}
$$

5. Prover computes quotient polynomial $q(X)$:

$$
q(X) = \frac{h(X) - h^*(X)}{(X^2-\beta^2)(X-\beta^2)}
$$

6. Prover computes commitment to $q(X)$:

$$
C_q = \mathsf{KZG10.Commit}(q(X))
$$

7. Prover sends $C_q$

Prover:

- First, compute $\gamma^2, \ldots, \gamma^{n-1}$, with complexity $(n-2) ~ \mathbb{F}_{\mathsf{mul}}$.
- Computing $h(X)$ mainly involves multiplying $\gamma^i$ with the coefficients of $h_i(X)$, with complexity:

$$
\sum_{i=1}^{n-1} 2^{n-i} ~ \mathbb{F}_{\mathsf{mul}} = (2^n - 2) ~ \mathbb{F}_{\mathsf{mul}}
$$

- Computing $h^*(X)$:

    $$
    h^*(X) = h(\beta) \cdot \frac{(X+\beta)(X-\beta^2)}{2\beta(\beta-\beta^2)} + h(-\beta) \cdot \frac{(X-\beta)(X-\beta^2)}{2\beta(\beta^2+\beta)} + h(\beta^2) \cdot \frac{X^2-\beta^2}{\beta^4-\beta^2}
    $$

    If computed as per the above expression:
    
    - Computing $\beta^4$ has complexity $\mathbb{F}_{\mathsf{mul}}$
    - Computing denominators $2\beta(\beta-\beta^2)$, $2\beta(\beta^2+\beta)$, and $\beta^4-\beta^2$ has complexity $2 ~ \mathbb{F}_{\mathsf{mul}}$
    - Computing inverses of these denominators has complexity $3 ~ \mathbb{F}_{\mathsf{inv}}$
    - Multiplying these inverses with $h(\beta)$, $h(-\beta)$, and $h(\beta^2)$ has complexity $3 ~ \mathbb{F}_{\mathsf{mul}}$
    - The three numerator polynomials can be directly expanded:

    $$
    \begin{aligned}
        & X^2 + (\beta - \beta^2) X - \beta^3 \\
        & X^2 - (\beta + \beta^2) X + \beta^3 \\
        & X^2 - \beta^2
    \end{aligned}
    $$
    
    Computing $\beta^3$ has complexity $\mathbb{F}_{\mathsf{mul}}$.
    
    - Multiplying these polynomials with the previously calculated coefficients has complexity 
    
    $$
    2 ~ \mathbb{F}_{\mathsf{mul}} + 2 ~\mathbb{F}_{\mathsf{mul}} + \mathbb{F}_{\mathsf{mul}} = 5 ~ \mathbb{F}_{\mathsf{mul}}
    $$

    Thus, the total complexity for computing $h^*(X)$ is:
    
    $$
    (1 + 2 + 3 + 1 + 5) ~ \mathbb{F}_{\mathsf{mul}} + 3 ~ \mathbb{F}_{\mathsf{inv}} = 12 ~ \mathbb{F}_{\mathsf{mul}} + 3 ~ \mathbb{F}_{\mathsf{inv}}
    $$

    > 🎈 The code uses Barycentric interpolation for the three points $(\beta, h(\beta))$, $(-\beta, h(-\beta))$, and $(\beta^2, h(\beta^2))$.
    >
    > - [ ] Analyze the complexity of this interpolation, which involves polynomial multiplication and division.


- Computing quotient polynomial $q(X)$ involves multiplying three linear polynomials for the denominator, and dividing $h(X) - h^*(X)$ by this result. The complexity is:

$$
\mathsf{polymul}(1, 1) + \mathsf{polymul}(2, 1) + \mathsf{polydiv}(2^n - 1, 3)
$$

- Computing $C_q$: The degree of $q(X)$ is $\deg(q) = 2^n - 1 - 3 = 2^n - 4$, so the complexity for computing $C_q$ is:

$$
\mathsf{msm}(2^n - 3, \mathbb{G}_1)
$$

Therefore, the total complexity for this round is:

$$
\begin{aligned}
    & (n - 2) ~ \mathbb{F}_{\mathsf{mul}} + (2^n - 2) ~ \mathbb{F}_{\mathsf{mul}} + 12 ~ \mathbb{F}_{\mathsf{mul}} + 3 ~ \mathbb{F}_{\mathsf{inv}}\\
    &  + \mathsf{polymul}(1, 1) + \mathsf{polymul}(2, 1) +  \mathsf{polydiv}(2^n - 1, 3) + \mathsf{msm}(2^n - 3, \mathbb{G}_1) \\
    = & (2^{n} + n + 8) ~ \mathbb{F}_{\mathsf{mul}} + 3 ~ \mathbb{F}_{\mathsf{inv}} \\
    &  + \mathsf{polymul}(1, 1) + \mathsf{polymul}(2, 1) +  \mathsf{polydiv}(2^n - 1, 3) + \mathsf{msm}(2^n - 3, \mathbb{G}_1) \\
\end{aligned}
$$

### Round 4

1. Verifier sends random point $\zeta \in \mathbb{F}_p$

2. Prover computes linearization polynomial $r(X)$ such that $r(\zeta) = 0$:

$$
r(X) = h(X) - h^*(\zeta) - (\zeta^2-\beta^2)(\zeta-\beta^2) \cdot q(X)
$$

3. Prover computes quotient polynomial $w(X)$:

$$
w(X) = \frac{r(X)}{(X-\zeta)}
$$

4. Prover computes commitment to $w(X)$:

$$
C_w = \mathsf{KZG10.Commit}(w(X))
$$

5. Prover sends $C_w$

Prover:

- Computing $\zeta^2$ has complexity $\mathbb{F}_{\mathsf{mul}}$
- Computing $r(X)$:
  - Computing $h^*(\zeta)$: Since $\deg(h^*) = 2$, evaluating at a point has complexity $3 ~ \mathbb{F}_{\mathsf{mul}}$
  - Computing $(\zeta^2-\beta^2)(\zeta-\beta^2)$ has complexity $\mathbb{F}_{\mathsf{mul}}$
  - Computing $(\zeta^2-\beta^2)(\zeta-\beta^2) \cdot q(X)$: With $\deg(q) = 2^n - 4$, this has complexity $\mathsf{polymul}(0, 2^n - 4)$
  
  Thus, the total complexity for computing $r(X)$ is:
  
  $$
  4 ~ \mathbb{F}_{\mathsf{mul}} + \mathsf{polymul}(0, 2^n - 4)
  $$

- Computing quotient polynomial $w(X)$ using linear division: Since $\deg(r) = 2^n - 1$, this has complexity $(2^n - 1) ~ \mathbb{F}_{\mathsf{mul}}$.
- Computing $C_w$ has complexity $\mathsf{msm}(2^n - 1, \mathbb{G}_1)$.

The total complexity for this round is:

$$
\begin{aligned}
    & \mathbb{F}_{\mathsf{mul}} + 4 ~ \mathbb{F}_{\mathsf{mul}} + \mathsf{polymul}(0, 2^n - 4) + (2^n - 1) ~ \mathbb{F}_{\mathsf{mul}} + \mathsf{msm}(2^n - 1, \mathbb{G}_1) \\
    = & (2^n + 4) ~ \mathbb{F}_{\mathsf{mul}} + \mathsf{polymul}(0, 2^n - 4) + \mathsf{msm}(2^n - 1, \mathbb{G}_1) 
\end{aligned}
$$

### Total Prover Complexity

Combining all the rounds:

$$
\begin{aligned}
    & (2^n - 2) ~ \mathbb{F}_{\mathsf{mul}} + \sum_{i = 1}^{n - 1} \mathsf{msm}(2^{i}, \mathbb{G}_1) \\
    & + (3 \cdot 2^{n} - 3) ~ \mathbb{F}_{\mathsf{mul}} \\
    & + (2^{n} + n + 8) ~ \mathbb{F}_{\mathsf{mul}} + 3 ~ \mathbb{F}_{\mathsf{inv}} \\
    &  + \mathsf{polymul}(1, 1) + \mathsf{polymul}(2, 1) +  \mathsf{polydiv}(2^n - 1, 3) + \mathsf{msm}(2^n - 3, \mathbb{G}_1) \\
    & + (2^n + 4) ~ \mathbb{F}_{\mathsf{mul}} + \mathsf{polymul}(0, 2^n - 4) + \mathsf{msm}(2^n - 1, \mathbb{G}_1) \\
    = & (6 \cdot 2^{n} + n + 7) ~ \mathbb{F}_{\mathsf{mul}} + 3 ~ \mathbb{F}_{\mathsf{inv}} \\
    & +  \mathsf{polymul}(1, 1) + \mathsf{polymul}(2, 1) + \mathsf{polymul}(0, 2^n - 4) +  \mathsf{polydiv}(2^n - 1, 3) \\
    & + \sum_{i = 1}^{n - 1} \mathsf{msm}(2^{i}, \mathbb{G}_1) + \mathsf{msm}(2^n - 3, \mathbb{G}_1) + \mathsf{msm}(2^n - 1, \mathbb{G}_1)\\
\end{aligned}
$$

Using polynomial long division:

$$
\mathsf{polydiv}(N, k) = (N - k + 1) ~ \mathbb{F}_{\mathsf{inv}} + (kN - k^2 + k) ~ \mathbb{F}_{\mathsf{mul}} 
$$

We get:

$$
\begin{align}
\mathsf{polydiv}(2^n - 1, 3)  & = (N - 1 - 3 + 1) ~ \mathbb{F}_{\mathsf{inv}} + (3(N - 1) - 3^2 + 3) ~ \mathbb{F}_{\mathsf{mul}}  \\
 & = (N - 3) ~ \mathbb{F}_{\mathsf{inv}} + (3N - 9) ~ \mathbb{F}_{\mathsf{mul}} 
\end{align}
$$

> [!important] 
> - [ ] There should be a more efficient implementation for division.

Therefore, the complexity is:

$$
\begin{align}
& (6 \cdot 2^{n} + n + 7) ~ \mathbb{F}_{\mathsf{mul}} + 3 ~ \mathbb{F}_{\mathsf{inv}} \\
    & +  \mathsf{polymul}(1, 1) + \mathsf{polymul}(2, 1) + \mathsf{polymul}(0, 2^n - 4) +  \mathsf{polydiv}(2^n - 1, 3) \\
    & + \sum_{i = 1}^{n - 1} \mathsf{msm}(2^{i}, \mathbb{G}_1) + \mathsf{msm}(2^n - 3, \mathbb{G}_1) + \mathsf{msm}(2^n - 1, \mathbb{G}_1) \\
= & (6 N + n + 7) ~ \mathbb{F}_{\mathsf{mul}} + 3 ~ \mathbb{F}_{\mathsf{inv}} \\
    & +  4 ~ \mathbb{F}_{\mathsf{mul}} + 6 ~ \mathbb{F}_{\mathsf{mul}} + (N - 3) ~ \mathbb{F}_{\mathsf{mul}}+  (N - 3) ~ \mathbb{F}_{\mathsf{inv}} + (3N - 9) ~ \mathbb{F}_{\mathsf{mul}}  \\
    & + \sum_{i = 1}^{n - 1} \mathsf{msm}(2^{i}, \mathbb{G}_1) + \mathsf{msm}(2^n - 3, \mathbb{G}_1) + \mathsf{msm}(2^n - 1, \mathbb{G}_1) \\
=  & (10 N + n + 5) ~ \mathbb{F}_{\mathsf{mul}} + N ~ \mathbb{F}_{\mathsf{inv}} \\
& + \sum_{i = 1}^{n - 1} \mathsf{msm}(2^{i}, \mathbb{G}_1) + \mathsf{msm}(N - 3, \mathbb{G}_1) + \mathsf{msm}(N - 1, \mathbb{G}_1) 
\end{align}
$$





### Proof Representation

The proof consists of $n+1$ elements in $\mathbb{G}_1$ and $2n+1$ elements in $\mathbb{F}_p$:

$$
\pi=\Big(H_1, H_2, \ldots, H_{n-1}, C_q, C_w, \{h_i(\beta), h_i(-\beta)\}_{i=0}^{n-1}, h_0(\beta^2) \Big)
$$


Proof size:

$$
(n + 1)~\mathbb{G}_1 + (2n + 1) ~ \mathbb{F}_p
$$

### Verification


1. Verifier computes $(h_1(\beta^2), h_2(\beta^2), \ldots, h_{n-1}(\beta^2))$:

$$
h_{i+1}(\beta^2) = \frac{h_i(\beta) + h_i(-\beta)}{2} + u_i\cdot \frac{h_i(\beta) - h_i(-\beta)}{2\beta}
$$

2. Verifier checks if $h_n(\beta^2)$ equals the claimed evaluation $v = \tilde{f}(\vec{u})$:

$$
h_n(\beta^2) \overset{?}{=} v
$$

3. Verifier computes commitment to $h(X)$:

$$
C_h = C_f + \gamma\cdot H_1 + \gamma^2\cdot H_2 + \cdots + \gamma^{n-1}\cdot H_{n-1}
$$

4. Verifier computes commitment to $r_\zeta(X)$:

$$
C_r = C_h - h^*(\zeta)\cdot[1]_1 - (\zeta^2-\beta^2)(\zeta-\beta^2)\cdot C_q
$$

5. Verifier checks if $C_w$ is a valid evaluation proof for $C_r$ at $X=\zeta$:

$$
\mathsf{KZG10.Verify}(C_r, \zeta, 0, C_w) \overset{?}{=} 1
$$

Or directly expanded as a Pairing check:

$$
e\Big(C_r + \zeta\cdot C_w, [1]_2\Big) \overset{?}{=} e\Big(C_w, [\tau]_2 \Big)
$$


Verifier:

1. Computing $h_1(\beta^2), \ldots, h_{n-1}(\beta^2)$:

- Computing $\beta^2$ has complexity $\mathbb{F}_{\mathsf{mul}}$
- For each $h_{i+1}(\beta^2)$, computing the inverses of $2$ and $2\beta$ and then multiplying with the numerators has complexity $2 ~ \mathbb{F}_{\mathsf{inv}} + 2 ~ \mathbb{F}_{\mathsf{mul}}$. Multiplying the second term with $u_i$ adds another $\mathbb{F}_{\mathsf{mul}}$, for a total of $2 ~ \mathbb{F}_{\mathsf{inv}} + 3 ~ \mathbb{F}_{\mathsf{mul}}$ per item, for $n-1$ items.



The total complexity for this step is:

$$
\mathbb{F}_{\mathsf{mul}} + (2n - 2) ~ \mathbb{F}_{\mathsf{inv}} + (3n - 3) ~ \mathbb{F}_{\mathsf{mul}} = (3n - 2) ~ \mathbb{F}_{\mathsf{mul}} + (2n - 2) ~ \mathbb{F}_{\mathsf{inv}}
$$

2. Computing $C_h$:

- Computing $\gamma^2, \ldots, \gamma^{n-1}$ has complexity $(n-2) ~ \mathbb{F}_{\mathsf{mul}}$
- Computing $\gamma \cdot H_1, \ldots, \gamma^{n-1} \cdot H_{n-1}$ has complexity $(n-1) ~ \mathsf{EccMul}^{\mathbb{G}_1}$
- Adding $n$ points in $\mathbb{G}_1$ to get $C_h$ has complexity $(n-1) ~ \mathsf{EccAdd}^{\mathbb{G}_1}$

The total complexity for this step is:

$$
(n - 2) ~ \mathbb{F}_{\mathsf{mul}} + (n - 1) ~ \mathsf{EccMul}^{\mathbb{G}_1} + (n - 1) ~ \mathsf{EccAdd}^{\mathbb{G}_1}
$$

# 3. Computation of $C_r$

- Computation of $h^*(\zeta)$ through bary-centric interpolation method, which the verifier calculates themselves

    The analysis approach here is consistent with the ph23 protocol. Here, $h^*(X)$ is derived by interpolation from 3 point-value pairs:

    $$
        h^*(X) = \frac{h(\beta) \cdot \frac{\hat{\omega_0}}{X- \beta} + h(-\beta) \cdot \frac{\hat{\omega_1}}{X+ \beta} + h(\beta^2) \cdot \frac{\hat{\omega_2}}{X- \beta^2}}{\frac{\hat{\omega_0}}{X- \beta} + \frac{\hat{\omega_1}}{X+ \beta} + \frac{\hat{\omega_2}}{X- \beta^2}}
    $$

    where:

    $$
    \begin{aligned}
        & \hat{\omega_0} = (\beta + \beta)(\beta - \beta^2) \\
        & \hat{\omega_1} = (-\beta - \beta)(-\beta - \beta^2) \\
        & \hat{\omega_2} = (\beta^2 - \beta)(\beta^2 - (-\beta))
    \end{aligned}
    $$

    Since $\beta$ is randomly generated, it cannot be pre-computed, resulting in a complexity of $3 ~ \mathbb{F}_{\mathsf{mul}}$.

    To calculate $h^*(\zeta)$, we substitute $\zeta$ into the expression for $h^*(X)$:

    $$
        h^*(\zeta) = \frac{h(\beta) \cdot \frac{\hat{\omega_0}}{\zeta- \beta} + h(-\beta) \cdot \frac{\hat{\omega_1}}{\zeta+ \beta} + h(\beta^2) \cdot \frac{\hat{\omega_2}}{\zeta- \beta^2}}{\frac{\hat{\omega_0}}{\zeta- \beta} + \frac{\hat{\omega_1}}{\zeta+ \beta} + \frac{\hat{\omega_2}}{\zeta- \beta^2}}
    $$

    Without detailing the method, the complexity analysis is consistent with ph23. For a set of n point-value pairs, this step has a complexity of $(2n + 1) ~ \mathbb{F}_{\mathsf{mul}} + (n + 1) ~ \mathbb{F}_{\mathsf{inv}}$. Therefore, the computation complexity here is $7 ~ \mathbb{F}_{\mathsf{mul}} + 4 ~ \mathbb{F}_{\mathsf{inv}}$.

    Thus, the total complexity for calculating $h^*(\zeta)$ is:

    $$
        10 ~ \mathbb{F}_{\mathsf{mul}} + 4 ~ \mathbb{F}_{\mathsf{inv}}
    $$

- Calculation of $[h^*(\zeta)]_1$, with a complexity of $\mathsf{EccMul}^{\mathbb{G}_1}$
   
- Computing $(\zeta^2 - \beta^2)(\zeta - \beta^2) \cdot C_q$: Computing $\zeta^2$ has complexity $\mathbb{F}_{\mathsf{mul}}$, computing $(\zeta^2 - \beta^2)(\zeta - \beta^2)$ has complexity $\mathbb{F}_{\mathsf{mul}}$, and multiplying this value with $C_q$ has complexity $\mathsf{EccMul}^{\mathbb{G}_1}$. The total complexity is 

$$
2 ~ \mathbb{F}_{\mathsf{mul}} + \mathsf{EccMul}^{\mathbb{G}_1}
$$

- Computing $C_r$ by adding/subtracting three points in $\mathbb{G}_1$ has complexity $2 ~ \mathsf{EccAdd}^{\mathbb{G}_1}$.

The total complexity for this step is:

$$
\begin{aligned}
    & 10 ~ \mathbb{F}_{\mathsf{mul}} + 4 ~ \mathbb{F}_{\mathsf{inv}}\\
    &  + \mathsf{EccMul}^{\mathbb{G}_1} \\
    & + 2 ~ \mathbb{F}_{\mathsf{mul}} + \mathsf{EccMul}^{\mathbb{G}_1} + 2 ~ \mathsf{EccAdd}^{\mathbb{G}_1} \\
    = & 12 ~ \mathbb{F}_{\mathsf{mul}} + 4 ~ \mathbb{F}_{\mathsf{inv}}  + 2 ~ \mathsf{EccMul}^{\mathbb{G}_1} + 2 ~ \mathsf{EccAdd}^{\mathbb{G}_1}
\end{aligned}
$$

4. Verification using Pairing:

$$
e(C_r + \zeta \cdot C_w, [1]_2) \overset{?}{=} e(C_w, [\tau]_2)
$$

- Computing $C_r + \zeta \cdot C_w$ has complexity $\mathsf{EccMul}^{\mathbb{G}_1} + \mathsf{EccAdd}^{\mathbb{G}_1}$
- Computing two pairings has complexity $2 ~ P$

The total complexity for this step is:

$$
\mathsf{EccMul}^{\mathbb{G}_1} + \mathsf{EccAdd}^{\mathbb{G}_1} + 2~P
$$

### Verifier Complexity

Combining all steps:

$$
\begin{aligned}
    & (3n - 2) ~ \mathbb{F}_{\mathsf{mul}} + (2n - 2) ~ \mathbb{F}_{\mathsf{inv}} \\
    & + (n - 2) ~ \mathbb{F}_{\mathsf{mul}} + (n - 1) ~ \mathsf{EccMul}^{\mathbb{G}_1} + (n - 1) ~ \mathsf{EccAdd}^{\mathbb{G}_1} \\
    & + 12 ~ \mathbb{F}_{\mathsf{mul}} + 4 ~ \mathbb{F}_{\mathsf{inv}}  + 2 ~ \mathsf{EccMul}^{\mathbb{G}_1} + 2 ~ \mathsf{EccAdd}^{\mathbb{G}_1} \\
    & + \mathsf{EccMul}^{\mathbb{G}_1} + \mathsf{EccAdd}^{\mathbb{G}_1} + 2~P \\
    = & (4n + 8) ~ \mathbb{F}_{\mathsf{mul}} + (2n + 2) ~ \mathbb{F}_{\mathsf{inv}} + (n + 1) ~ \mathsf{EccMul}^{\mathbb{G}_1} + (n + 2) ~ \mathsf{EccAdd}^{\mathbb{G}_1} + 2~P
\end{aligned}
$$

### Summary

**Prover's cost:**

$$
\begin{aligned}
    & (6 \cdot 2^{n} + n + 7) ~ \mathbb{F}_{\mathsf{mul}} + 3 ~ \mathbb{F}_{\mathsf{inv}} \\
    & +  \mathsf{polymul}(1, 1) + \mathsf{polymul}(2, 1) + \mathsf{polymul}(0, 2^n - 4) +  \mathsf{polydiv}(2^n - 1, 3) \\
    & + \sum_{i = 1}^{n - 1} \mathsf{msm}(2^{i}, \mathbb{G}_1) + \mathsf{msm}(2^n - 3, \mathbb{G}_1) + \mathsf{msm}(2^n - 1, \mathbb{G}_1)\\
\end{aligned}
$$

Simplified:

$$
(10 N + n + 5) ~ \mathbb{F}_{\mathsf{mul}} + N ~ \mathbb{F}_{\mathsf{inv}} 
+ \sum_{i = 1}^{n - 1} \mathsf{msm}(2^{i}, \mathbb{G}_1) + \mathsf{msm}(N - 3, \mathbb{G}_1) + \mathsf{msm}(N - 1, \mathbb{G}_1) 
$$



**Verifier's cost:**

$$
\begin{aligned}
    & (4n + 8) ~ \mathbb{F}_{\mathsf{mul}} + (2n + 2) ~ \mathbb{F}_{\mathsf{inv}} + (n + 1) ~ \mathsf{EccMul}^{\mathbb{G}_1} + (n + 2) ~ \mathsf{EccAdd}^{\mathbb{G}_1} + 2~P
\end{aligned}
$$


**Proof size:**

$$
(2n + 1)  \mathbb{F}_p + (n + 1) \cdot \mathbb{G}_1
$$

## Optimized Version 2

- Protocol document: [Gemini-PCS-4](https://github.com/sec-bit/mle-pcs/blob/main/gemini/Gemini-PCS-4.md)

Optimization technique:

This version uses an approach inspired by the query phase of FRI protocol. Instead of evaluating $h_0(X)$ at challenge point $X=\beta$, then evaluating the folded polynomial $h_1(X)$ at $X=\beta^2$, and so on until $h_{n-1}(\beta^{2^{n-1}})$. This allows reuse of evaluation points when verifying the folding of $h_i(X)$, saving $n$ evaluation points in total.

Proving goal: A multilinear extension polynomial $\tilde{f}(X_0, X_1, \ldots, X_{n-1})$ evaluates to $v = \tilde{f}(u_0, u_1, \ldots, u_{n-1})$ at point $\vec{u}=(u_0, u_1, \ldots, u_{n-1})$.

The MLE polynomial is expressed in coefficient form:

$$
\tilde{f}(X_0, X_1, \ldots, X_{n-1}) = \sum_{i=0}^{n-1} c_i\cdot X_0^{i_0}X_1^{i_1}\cdots X_{n-1}^{i_{n-1}}
$$

### Common Input

1. Commitment to the vector $\vec{c}=(c_0, c_1, \ldots, c_{n-1})$ as $C_f$:

$$
C_f = \mathsf{KZG10.Commit}(\vec{c})
$$

2. Evaluation point $\vec{u}=(u_0, u_1, \ldots, u_{n-1})$

3. $v = \tilde{f}(u_0, u_1, \ldots, u_{n-1})$

### Witness

- Coefficients of polynomial $f(X)$: $\vec{c}=(c_0, c_1, \ldots, c_{n-1})$

### Round 1

1. Prover defines $h_0(X) = f(X)$ and computes folded polynomials $h_1(X), h_2(X), \ldots, h_{n-1}(X)$ such that:

$$
h_{i+1}(X^2) = \frac{h_i(X) + h_i(-X)}{2} + u_i\cdot \frac{h_i(X) - h_i(-X)}{2X}
$$

2. Prover computes commitments $(C_{h_1}, C_{h_2}, \ldots, C_{h_{n-1}})$ such that:

$$
C_{h_{i+1}} = \mathsf{KZG10.Commit}(h_{i+1}(X))
$$

3. Prover sends $(C_{h_1}, C_{h_2}, \ldots, C_{h_{n-1}})$

The computation in this round is the same as in Optimized Version 1, so the complexity is:

$$
(2^n - 2) ~ \mathbb{F}_{\mathsf{mul}} + \sum_{i = 1}^{n - 1} \mathsf{msm}(2^{i}, \mathbb{G}_1)
$$

### Round 2

1. Verifier sends random point $\beta \in \mathbb{F}_p$

2. Prover computes $h_0(\beta)$

3. Prover computes $h_0(-\beta), h_1(-\beta^2), \ldots, h_{n-1}(-\beta^{2^{n-1}})$

4. Prover sends $\big(h_0(\beta), h_0(-\beta), h_1(-\beta^2), \ldots, h_{n-1}(-\beta^{2^{n-1}})\big)$

Prover:

- Computing $\beta^2, \ldots, \beta^{2^{n-1}}$ has complexity $(n-1) ~ \mathbb{F}_{\mathsf{mul}}$
- Computing $h_0(\beta), h_0(-\beta), \ldots, h_{n-1}(-\beta^{2^{n-1}})$ has complexity:

$$
2^{n} ~ \mathbb{F}_{\mathsf{mul}} + \sum_{i=0}^{n-1} 2^{n-i} ~ \mathbb{F}_{\mathsf{mul}} = (3 \cdot 2^{n} - 2) ~ \mathbb{F}_{\mathsf{mul}}
$$

Therefore, the total complexity for this round is:

$$
(n-1) ~ \mathbb{F}_{\mathsf{mul}} + (3 \cdot 2^{n} - 2) ~ \mathbb{F}_{\mathsf{mul}} = (3 \cdot 2^{n} + n - 3) ~ \mathbb{F}_{\mathsf{mul}}
$$

### Round 3

1. Verifier sends random value $\gamma \in \mathbb{F}_p$ to aggregate multiple polynomials

2. Prover computes $q(X)$ satisfying:

$$
q(X) = \frac{h_0(X)-h_0(\beta)}{X-\beta} + \sum_{i=0}^{n-1} \gamma^{i+1} \cdot \frac{h_i(X)-h_i(-\beta^{2^i})}{X+\beta^{2^i}}
$$

3. Define a new Domain $D$ containing the points:

$$
D = \{\beta, -\beta, -\beta^2, \ldots, -\beta^{2^{n-1}}\}
$$

4. Prover computes and sends commitment $C_q = \mathsf{KZG10.Commit}(q(X))$

Prover:

- Computing $\gamma^2, \ldots, \gamma^n$ has complexity $(n-1) ~ \mathbb{F}_{\mathsf{mul}}$
- Computing $\gamma^{i+1} \cdot (h_i(X) - h_i(-\beta^{2^i}))$ has complexity $\mathsf{polymul}(0, 2^{n-i})$, dividing this by $(X + \beta^{2^i})$ using linear division has complexity $2^{n-i} ~ \mathbb{F}_{\mathsf{mul}}$. The total complexity for computing $q(X)$ including the first term is:

$$
2^n ~ \mathbb{F}_{\mathsf{mul}} + \sum_{i=0}^{n-1} (\mathsf{polymul}(0, 2^{n-i}) + 2^{n-i} ~ \mathbb{F}_{\mathsf{mul}}) = (3 \cdot 2^n - 2) ~ \mathbb{F}_{\mathsf{mul}} + \sum_{i=0}^{n-1} \mathsf{polymul}(0, 2^{i+1})
$$

- Computing $C_q$ has complexity $\mathsf{msm}(2^n - 1, \mathbb{G}_1)$

Therefore, the total complexity for this round is:

$$
\begin{aligned}
    & (n-1) ~ \mathbb{F}_{\mathsf{mul}} + (3 \cdot 2^n - 2) ~ \mathbb{F}_{\mathsf{mul}} + \sum_{i=0}^{n-1} \mathsf{polymul}(0, 2^{i+1}) + \mathsf{msm}(2^n - 1, \mathbb{G}_1) \\
    & = (3 \cdot 2^n + n - 3) ~ \mathbb{F}_{\mathsf{mul}} + \sum_{i=0}^{n-1} \mathsf{polymul}(0, 2^{i+1}) + \mathsf{msm}(2^n - 1, \mathbb{G}_1)
\end{aligned}
$$

### Round 4


1. Verifier sends random point $\zeta \in \mathbb{F}_q$

2. Prover computes linearization polynomial $L_\zeta(X)$ such that $L_\zeta(\zeta) = 0$:

$$
L_\zeta(X) = v_D(\zeta) \cdot q(X) - \frac{v_D(\zeta)}{\zeta-\beta} \cdot (h_0(X)-h_0(\beta)) - \sum_{i=0}^{n-1} \gamma^{i+1} \cdot \frac{v_D(\zeta)}{\zeta+\beta^{2^i}} \cdot (h_i(X)-h_i(-\beta^{2^i}))
$$

3. Prover computes quotient polynomial $w(X)$:

$$
w(X) = \frac{L_\zeta(X)}{(X-\zeta)}
$$

4. Prover computes and sends commitment to $w(X)$:

$$
C_w = \mathsf{KZG10.Commit}(w(X))
$$

**Complexity analysis:**

1. Computing $L_\zeta(X)$:

- Computation of $\gamma^2, \ldots, \gamma^{n}$, with complexity of $(n - 1) ~ \mathbb{F}_{\mathsf{mul}}$.
- Computation of $v_D(\zeta)$,
  
    $$
    v_D(\zeta) = (\zeta - \beta)(\zeta - (-\beta)) \cdots (\zeta - (-\beta^{2^{n - 1}}))
    $$

    Since $D$ contains a total of $n + 1$ elements, this involves multiplying $n + 1$ elements, resulting in a complexity of $n ~ \mathbb{F}_{\mathsf{mul}}$.
- The total complexity for computing $L_\zeta(X)$ is:

$$
\begin{aligned}
    & \mathsf{polymul}(0, 2^n - 2) + \mathbb{F}_{\mathsf{inv}} + \mathbb{F}_{\mathsf{mul}} + \mathsf{polymul}(0, 2^n) \\
    & + \sum_{i=0}^{n-1} (\mathbb{F}_{\mathsf{inv}} + 2 ~ \mathbb{F}_{\mathsf{mul}} + \mathsf{polymul}(0, 2^{n-i})) \\
    & = (2n+1) ~ \mathbb{F}_{\mathsf{mul}} + (n+1) ~ \mathbb{F}_{\mathsf{inv}} + \sum_{i=0}^{n-1} \mathsf{polymul}(0, 2^{i+1}) + \mathsf{polymul}(0, 2^n-2) + \mathsf{polymul}(0, 2^n)
\end{aligned}
$$

2. Computing $w(X)$ using linear division: With $\deg(L_\zeta) = 2^n$, this has complexity $2^n ~ \mathbb{F}_{\mathsf{mul}}$

3. Computing $C_w$ has complexity $\mathsf{msm}(2^n-1, \mathbb{G}_1)$

The total complexity for this round is:

$$
\begin{aligned}
    & (2n+1) ~ \mathbb{F}_{\mathsf{mul}} + (n+1) ~ \mathbb{F}_{\mathsf{inv}} + \sum_{i=0}^{n-1} \mathsf{polymul}(0, 2^{i+1}) + \mathsf{polymul}(0, 2^n-2) \\
    & + \mathsf{polymul}(0, 2^n) + 2^n ~ \mathbb{F}_{\mathsf{mul}} + \mathsf{msm}(2^n-1, \mathbb{G}_1) \\
    = & (2^n+2n+1) ~ \mathbb{F}_{\mathsf{mul}} + (n+1) ~ \mathbb{F}_{\mathsf{inv}} + \sum_{i=0}^{n-1} \mathsf{polymul}(0, 2^{i+1}) + \mathsf{polymul}(0, 2^n-2) \\
    & + \mathsf{polymul}(0, 2^n) + \mathsf{msm}(2^n-1, \mathbb{G}_1)
\end{aligned}
$$


### Proof Representation

The proof consists of $n+1$ elements in $\mathbb{G}_1$ and $n+1$ elements in $\mathbb{F}_q$:

$$
\pi=\Big(C_{f_1}, C_{f_2}, \ldots, C_{f_{n-1}}, C_q, C_w, h_0(\beta), h_0(-\beta), h_1(-\beta^2), \ldots, h_{n-1}(-\beta^{2^{n-1}})\Big)
$$


Proof size:

$$
(n+1) \cdot \mathbb{G}_1 + (n+1) \cdot \mathbb{F}_p
$$

### Verification


1. Verifier computes $(h_1(\beta^2), h_2(\beta^{2^2}), \ldots, h_{n-1}(\beta^{2^{n-1}}), h_n(\beta^{2^n}))$:

$$
h_{i+1}(\beta^{2^{i+1}}) = \frac{h_i(\beta^{2^i}) + h_i(-\beta^{2^i})}{2} + u_i \cdot \frac{h_i(\beta^{2^i}) - h_i(-\beta^{2^i})}{2\beta^{2^i}}
$$

2. Verifier checks if $h_n(\beta^{2^n})$ equals the claimed evaluation $v = \tilde{f}(\vec{u})$:

$$
h_n(\beta^{2^n}) \overset{?}{=} v
$$

3. Verifier computes commitment to $L_\zeta(X)$:

$$
C_L = v_D(\zeta) \cdot C_q - e_0 \cdot (C_{h_0} - h_0(\beta) \cdot [1]_1) - \sum_{i=0}^{n-1} e_{i+1} \cdot (C_{h_i} - h_i(-\beta^{2^i}) \cdot [1]_1)
$$

where $e_0, e_1, \ldots, e_n$ are defined as:

$$
\begin{aligned}
e_0 &= \frac{v_D(\zeta)}{\zeta-\beta} \\
e_{i+1} &= \gamma^{i+1} \cdot \frac{v_D(\zeta)}{\zeta+\beta^{2^i}}, \quad i=0,1,\ldots,n-1
\end{aligned}
$$

4. Verifier checks if $C_w$ is a valid evaluation proof for $C_L$ at $X=\zeta$:

$$
\mathsf{KZG10.Verify}(C_L, \zeta, 0, C_w) \overset{?}{=} 1
$$

Or directly as a Pairing check:

$$
e\Big(C_L + \zeta \cdot C_w, [1]_2\Big) \overset{?}{=} e\Big(C_w, [\tau]_2 \Big)
$$


Verifier:

1. Computing $h_1(\beta^2), \ldots, h_n(\beta^{2^n})$:

- Computing $\beta^2, \beta^{2^2}, \ldots, \beta^{2^n}$ has complexity $n ~ \mathbb{F}_{\mathsf{mul}}$
- For each $h_{i+1}(\beta^{2^{i+1}})$, computing the inverses of $2$ and $2\beta^{2^i}$ and then multiplying with the numerators has complexity $2 ~ \mathbb{F}_{\mathsf{inv}} + 3 ~ \mathbb{F}_{\mathsf{mul}}$ per item, for $n$ items.

The total complexity for this step is:

$$
n ~ \mathbb{F}_{\mathsf{mul}} + 2n ~ \mathbb{F}_{\mathsf{inv}} + 3n ~ \mathbb{F}_{\mathsf{mul}} = 4n ~ \mathbb{F}_{\mathsf{mul}} + 2n ~ \mathbb{F}_{\mathsf{inv}}
$$

2. Computing $C_L$:

- First, calculate $v_D(\zeta)$,
  
    $$
    v_D(\zeta) = (\zeta - \beta)(\zeta - (-\beta)) \cdots (\zeta - (-\beta^{2^{n - 1}}))
    $$

    Since $D$ contains a total of $n + 1$ elements, this involves multiplying $n + 1$ elements, resulting in a complexity of $n ~ \mathbb{F}_{\mathsf{mul}}$.
    
- Computing $e_0$ has complexity $\mathbb{F}_{\mathsf{inv}} + \mathbb{F}_{\mathsf{mul}}$
- Computing $\gamma^2, \ldots, \gamma^n$ has complexity $(n-1) ~ \mathbb{F}_{\mathsf{mul}}$
- Computing each $e_{i+1}$ has complexity $\mathbb{F}_{\mathsf{inv}} + 2 ~ \mathbb{F}_{\mathsf{mul}}$, for $n$ items, giving a total of $n ~ \mathbb{F}_{\mathsf{inv}} + 2n ~ \mathbb{F}_{\mathsf{mul}}$
- Computing 

$$
\sum_{i = 0}^{n - 1} e_{i + 1} \cdot (C_{h_i} - h_i(- \beta^{2^{i}}) \cdot [1]_1)
$$

Computing $e_{i + 1} \cdot (C_{h_i} - h_i(- \beta^{2^{i}}) \cdot [1]_1)$ has a complexity of $2 ~ \mathsf{EccMul}^{\mathbb{G}_1} + \mathsf{EccAdd}^{\mathbb{G}_1}$. The total complexity is $2n ~ \mathsf{EccMul}^{\mathbb{G}_1} + n ~ \mathsf{EccAdd}^{\mathbb{G}_1} + (n - 1) ~ \mathsf{EccAdd}^{\mathbb{G}_1}$, which equals $2n ~ \mathsf{EccMul}^{\mathbb{G}_1} + (2n - 1) ~ \mathsf{EccAdd}^{\mathbb{G}_1}$.

- Computing $e_0 \cdot (C_{h_0} - h_0(\beta) \cdot [1]_1)$, with a complexity of $2 ~ \mathsf{EccMul}^{\mathbb{G}_1} + \mathsf{EccAdd}^{\mathbb{G}_1}$.
- Computing $v_D(\zeta) \cdot C_q$ has complexity $\mathsf{EccMul}^{\mathbb{G}_1}$, and adding the three terms to compute $C_L$ has complexity $2 ~ \mathsf{EccAdd}^{\mathbb{G}_1}$

The total complexity for this step is:

$$
\begin{aligned}
    & n ~ \mathbb{F}_{\mathsf{mul}} + \mathbb{F}_{\mathsf{inv}} + \mathbb{F}_{\mathsf{mul}} + (n-1) ~ \mathbb{F}_{\mathsf{mul}} + n ~ \mathbb{F}_{\mathsf{inv}} + 2n ~ \mathbb{F}_{\mathsf{mul}} \\
    & + 2n ~ \mathsf{EccMul}^{\mathbb{G}_1} + (2n-1) ~ \mathsf{EccAdd}^{\mathbb{G}_1} + 2 ~ \mathsf{EccMul}^{\mathbb{G}_1} + \mathsf{EccAdd}^{\mathbb{G}_1} + \mathsf{EccMul}^{\mathbb{G}_1} + 2 ~ \mathsf{EccAdd}^{\mathbb{G}_1} \\
    = & 4n ~ \mathbb{F}_{\mathsf{mul}} + (n+1) ~ \mathbb{F}_{\mathsf{inv}} + (2n+3) ~ \mathsf{EccMul}^{\mathbb{G}_1} + (2n+2) ~ \mathsf{EccAdd}^{\mathbb{G}_1}
\end{aligned}
$$

3. Final verification using Pairing:

$$
e(C_L + \zeta \cdot C_w, [1]_2) \overset{?}{=} e(C_w, [\tau]_2)
$$

- Computing $C_L + \zeta \cdot C_w$ has complexity $\mathsf{EccMul}^{\mathbb{G}_1} + \mathsf{EccAdd}^{\mathbb{G}_1}$
- Computing two pairings has complexity $2 ~ P$

The total complexity for this step is:

$$
\mathsf{EccMul}^{\mathbb{G}_1} + \mathsf{EccAdd}^{\mathbb{G}_1} + 2 ~ P
$$

### Verifier Complexity

Combining all steps:

$$
\begin{aligned}
    & 4n ~ \mathbb{F}_{\mathsf{mul}} + 2n ~ \mathbb{F}_{\mathsf{inv}} \\
    & + 4n ~ \mathbb{F}_{\mathsf{mul}} + (n+1) ~ \mathbb{F}_{\mathsf{inv}} + (2n+3) ~ \mathsf{EccMul}^{\mathbb{G}_1} + (2n+2) ~ \mathsf{EccAdd}^{\mathbb{G}_1} \\
    & + \mathsf{EccMul}^{\mathbb{G}_1} + \mathsf{EccAdd}^{\mathbb{G}_1} + 2 ~ P \\
    & = 8n ~ \mathbb{F}_{\mathsf{mul}} + (3n+1) ~ \mathbb{F}_{\mathsf{inv}} + (2n+4) ~ \mathsf{EccMul}^{\mathbb{G}_1} + (2n+3) ~ \mathsf{EccAdd}^{\mathbb{G}_1} + 2 ~ P
\end{aligned}
$$

### Summary

**Prover's cost:**

$$
\begin{aligned}
    & (2^n - 2) ~ \mathbb{F}_{\mathsf{mul}} + \sum_{i = 1}^{n - 1} \mathsf{msm}(2^{i}, \mathbb{G}_1) \\
    & + (3 \cdot 2^{n} + n - 3) ~ \mathbb{F}_{\mathsf{mul}} \\
    & + (3 \cdot 2^{n} + n - 3) ~ \mathbb{F}_{\mathsf{mul}} + \sum_{i = 0}^{n - 1} \mathsf{polymul}(0, 2^{i + 1}) + \mathsf{msm}(2^n - 1, \mathbb{G}_1) \\
    & + (2^n + 2n + 1) ~ \mathbb{F}_{\mathsf{mul}}  + (n + 1) ~ \mathbb{F}_{\mathsf{inv}} + \sum_{i = 0}^{n - 1} \mathsf{polymul}(0, 2^{i + 1}) + \mathsf{polymul}(0, 2^n - 2) \\
    & + \mathsf{polymul}(0, 2^n) + \mathsf{msm}(2^n - 1, \mathbb{G}_1) \\
    = & (8 \cdot 2^{n} + 4n - 7) ~ \mathbb{F}_{\mathsf{mul}} + (n + 1) ~ \mathbb{F}_{\mathsf{inv}} + 2 \cdot \sum_{i = 0}^{n - 1} \mathsf{polymul}(0, 2^{i + 1}) + \mathsf{polymul}(0, 2^n - 2) \\
    & + \mathsf{polymul}(0, 2^n) + \sum_{i = 1}^{n - 1} \mathsf{msm}(2^{i}, \mathbb{G}_1) + 2 ~ \mathsf{msm}(2^n - 1, \mathbb{G}_1)\\
\end{aligned}
$$

This simplifies to:

$$
\begin{aligned}
    & (8 N + 4n - 7) ~ \mathbb{F}_{\mathsf{mul}} + (n + 1) ~ \mathbb{F}_{\mathsf{inv}} + 2 \cdot \sum_{i = 0}^{n - 1} \mathsf{polymul}(0, 2^{i + 1}) + \mathsf{polymul}(0, 2^n - 2) \\
    & + \mathsf{polymul}(0, N) + \sum_{i = 1}^{n - 1} \mathsf{msm}(2^{i}, \mathbb{G}_1) + 2 ~ \mathsf{msm}(N - 1, \mathbb{G}_1)\\
\end{aligned}
$$

Substituting $\mathsf{polymul}(0, N) = (N+1) ~ \mathbb{F}_{\mathsf{mul}}$:

$$
\begin{aligned}
    & (8 N + 4n - 7) ~ \mathbb{F}_{\mathsf{mul}} + (n + 1) ~ \mathbb{F}_{\mathsf{inv}} + 2 \cdot \sum_{i = 0}^{n - 1} \mathsf{polymul}(0, 2^{i + 1}) + \mathsf{polymul}(0, 2^n - 2) \\
    & + \mathsf{polymul}(0, N) + \sum_{i = 1}^{n - 1} \mathsf{msm}(2^{i}, \mathbb{G}_1) + 2 ~ \mathsf{msm}(N - 1, \mathbb{G}_1)\\
	= & (8 N + 4n - 7) ~ \mathbb{F}_{\mathsf{mul}} + (n + 1) ~ \mathbb{F}_{\mathsf{inv}} + 2 \cdot \sum_{i = 0}^{n - 1} (2^{i + 1} + 1) ~ \mathbb{F}_{\mathsf{mul}} + (2^n - 1) ~ \mathbb{F}_{\mathsf{mul}} \\
    & + (N + 1) ~ \mathbb{F}_{\mathsf{mul}} + \sum_{i = 1}^{n - 1} \mathsf{msm}(2^{i}, \mathbb{G}_1) + 2 ~ \mathsf{msm}(N - 1, \mathbb{G}_1) \\
	= & (8 N + 4n - 7) ~ \mathbb{F}_{\mathsf{mul}} + (n + 1) ~ \mathbb{F}_{\mathsf{inv}} + 2 \cdot \sum_{i = 0}^{n - 1} (2^{i + 1} + 1) ~ \mathbb{F}_{\mathsf{mul}} + (2^n - 1) ~ \mathbb{F}_{\mathsf{mul}} \\
    & + (N + 1) ~ \mathbb{F}_{\mathsf{mul}} + \sum_{i = 1}^{n - 1} \mathsf{msm}(2^{i}, \mathbb{G}_1) + 2 ~ \mathsf{msm}(N - 1, \mathbb{G}_1) \\
	= & (8 N + 4n - 7) ~ \mathbb{F}_{\mathsf{mul}} + (n + 1) ~ \mathbb{F}_{\mathsf{inv}} + (4N + 2n - 4) ~ \mathbb{F}_{\mathsf{mul}} + (N - 1) ~ \mathbb{F}_{\mathsf{mul}} \\
    & + (N + 1) ~ \mathbb{F}_{\mathsf{mul}} + \sum_{i = 1}^{n - 1} \mathsf{msm}(2^{i}, \mathbb{G}_1) + 2 ~ \mathsf{msm}(N - 1, \mathbb{G}_1) \\
	= & (14 N + 6n - 11) ~ \mathbb{F}_{\mathsf{mul}} + (n + 1) ~ \mathbb{F}_{\mathsf{inv}} + \sum_{i = 1}^{n - 1} \mathsf{msm}(2^{i}, \mathbb{G}_1) + 2 ~ \mathsf{msm}(N - 1, \mathbb{G}_1)   \\
\end{aligned}
$$


**Verifier's cost:**

$$
8n ~ \mathbb{F}_{\mathsf{mul}} + (3n+1) ~ \mathbb{F}_{\mathsf{inv}} + (2n+4) ~ \mathsf{EccMul}^{\mathbb{G}_1} + (2n+3) ~ \mathsf{EccAdd}^{\mathbb{G}_1} + 2 ~ P
$$

**Proof size:**

$$
(n+1) \cdot \mathbb{F}_p + (n+1) \cdot \mathbb{G}_1
$$