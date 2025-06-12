# Zeromorph-PCS (Part II)

## 1. Optimization Ideas

## 2. Protocol Description

### Evaluation Proof Protocol

#### Common Inputs
- Commitment $\mathsf{cm}(f)$ of the MLE polynomial $\tilde{f}$ mapped to the univariate polynomial $f(X)=[[\tilde{f}]]_n$
- Evaluation point $\mathbf{u}=(u_0, u_1, \ldots, u_{n-1})$
- Evaluation result $v = \tilde{f}(\mathbf{u})$

#### Witness
- Evaluation vector $\mathbf{a} = (a_0, a_1, \ldots, a_{2^n-1})$ of the MLE polynomial $\tilde{f}$

#### Round 1
- Prover computes $n$ remainder MLE polynomials $\{\tilde{q}_i\}_{i=0}^{n-1}$
- Prover constructs univariate polynomials $q_i=[[\tilde{q}_i]]_i, \quad 0 \leq i < n$ mapped from remainder MLE polynomials

$$
\tilde{f}(X_0,X_1,\ldots, X_{n-1}) - v = \sum_{i=0}^{n-1} (X_i-u_i) \cdot \tilde{q}_i(X_0,X_1,\ldots, X_{i-1})
$$

- Prover computes and sends their commitments: $\mathsf{cm}(q_0), \mathsf{cm}(q_1), \ldots, \mathsf{cm}(q_{n-1})$

#### Round 2
1. Verifier sends a random number $\beta\in \mathbb{F}_q^*$
2. Prover constructs $g(X)$ as an aggregation polynomial of $\{q_i(X)\}$, satisfying

$$
g(X^{-1}) = \sum_{i=0}^{n-1} \beta^i \cdot X^{-2^i+1}\cdot q_i(X)
$$

3. Prover computes and sends the commitment $\mathsf{cm}(g)$ of $g(X)$

#### Round 3
1. Verifier sends a random number $\zeta\in \mathbb{F}_p^*$ to challenge the polynomial evaluation at $X=\zeta$

2. Prover computes $g(\zeta^{-1})$ and calculates the quotient polynomial $q_g(X)$

$$
q_g(X) = \frac{g(X) - g(\zeta^{-1})}{X-\zeta^{-1}}
$$

3. Prover constructs linearization polynomials $r_\zeta(X)$ and $s_\zeta(X)$

- Computes $r_\zeta(X)$:

$$
r_\zeta(X) = f(X) - v\cdot \Phi_{n}(\zeta) - \sum_{i=0}^{n-1} \Big(\zeta^{2^i}\cdot \Phi_{n-i-1}(\zeta^{2^{i+1}}) - u_i\cdot \Phi_{n-i}(\zeta^{2^{i}})\Big)\cdot q_i(X)
$$

- Computes $s_\zeta(X)$, which equals zero at $X=\zeta$:

$$
s_\zeta(X) = g(\zeta^{-1}) - \sum_i\beta^i\zeta^{2^i-1}\cdot q_i(X)
$$

- Computes quotient polynomials $w_r(X)$ and $w_s(X)$:

$$
w_r(X) = \frac{r_\zeta(X)}{X-\zeta}, \qquad w_s(X) = \frac{s_\zeta(X)}{X-\zeta}
$$

4. Computes and sends commitment $\mathsf{cm}(q_g)$

#### Round 4
1. Verifier sends a random number $\alpha\in \mathbb{F}_p^*$ to aggregate $w_r(X)$ and $w_s(X)$

2. Prover computes $w(X)$ and sends its commitment $\mathsf{cm}(w)$:

$$
w(X) = w_r(X) + \alpha\cdot w_s(X)
$$

#### Proof
Total of $n+3$ elements in $\mathbb{G}_1$ and $1$ element in $\mathbb{F}_q$:

$$
\pi= \Big( \mathsf{cm}(q_0), \mathsf{cm}(q_1), \ldots, \mathsf{cm}(q_{n-1}), \mathsf{cm}(g), \mathsf{cm}(q_g), \mathsf{cm}(w), g(\zeta^{-1})\Big)
$$

#### Verification
The Verifier:

1. Constructs commitment $\mathsf{cm}(r_\zeta)$:

$$
\mathsf{cm}(r_\zeta) = \mathsf{cm}(f) - \mathsf{cm}(v\cdot \Phi_{n}(\zeta)) - \sum_{i=0}^{n-1} \Big(\zeta^{2^i}\cdot \Phi_{n-i-1}(\zeta^{2^{i+1}}) - u_i\cdot \Phi_{n-i}(\zeta^{2^{i}})\Big)\cdot \mathsf{cm}(q_i)
$$

2. Constructs commitment $\mathsf{cm}(s_\zeta)$:

$$
\mathsf{cm}(s_\zeta) = g(\zeta^{-1})\cdot[1]_1 - \sum_{i=0}^{n-1} \beta^i \cdot \zeta^{-2^i+1}\cdot \mathsf{cm}(q_i)
$$

3. Verifies that $r_\zeta(\zeta) = 0$ and $s_\zeta(\zeta) = 0$:

$$
e(\mathsf{cm}(r_\zeta) + \alpha\cdot \mathsf{cm}(s_\zeta), \ [1]_2) = e(\mathsf{cm}(w),\ [\tau]_2 - \zeta\cdot [1]_2)
$$

Which can be transformed into the following pairing equation:

$$
e(\mathsf{cm}(r_\zeta) + \alpha\cdot \mathsf{cm}(s_\zeta) + \zeta\cdot\mathsf{cm}(w), \ [1]_2) = e(\mathsf{cm}(w),\ [\tau]_2)
$$

4. Verifies the correctness of $g(\zeta^{-1})$:

$$
e(\mathsf{cm}(g) - g(\zeta^{-1})\cdot [1]_1 + \zeta^{-1}\cdot\mathsf{cm}(q_g),\  [1]_2) = e(\mathsf{cm}(q_g), \ [\tau]_2)
$$

## 3. Performance Analysis