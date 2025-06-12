# Gemini-PCS (Part III)

## 1. Optimization Approach

## 2. Protocol Description

The protocol below proves that a MLE polynomial $\tilde{f}(X_0, X_1, \ldots, X_{n-1})$ evaluated at point $\vec{u}=(u_0, u_1, \ldots, u_{n-1})$ has value $v = \tilde{f}(u_0, u_1, \ldots, u_{n-1})$. Here, $\tilde{f}(X_0, X_1, \ldots, X_{n-1})$ is represented in coefficient form as:

$$
\tilde{f}(X_0, X_1, \ldots, X_{n-1}) = \sum_{i=0}^{n-1} f_i\cdot X_0^{i_0}X_1^{i_1}\cdots X_{n-1}^{i_{n-1}}
$$

### Common Input

1. Commitment $C_f$ to vector $\vec{f}=(f_0, f_1, \ldots, f_{n-1})$

$$
C_f = \mathsf{KZG10.Commit}(\vec{f})
$$

2. Evaluation point $\vec{u}=(u_0, u_1, \ldots, u_{n-1})$

3. $v = \tilde{f}(u_0, u_1, \ldots, u_{n-1})$

### Witness

1. Coefficients $f_0, f_1, \ldots, f_{n-1}$ of polynomial $f(X)$

### Round 1.

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

### Round 2.

1. Verifier sends a random point $\beta\in\mathbb{F}_p$

2. Prover computes $h_0(\beta), h_1(\beta), \ldots, h_{n-1}(\beta)$

3. Prover computes $h_0(-\beta), h_1(-\beta), \ldots, h_{n-1}(-\beta)$

4. Prover computes $h_0(\beta^2)$

5. Prover sends $\{h_i(\beta), h_i(-\beta)\}_{i=0}^{n-1}$, and $h_0(\beta^2)$

### Round 3.

1. Verifier sends a random value $\gamma\in\mathbb{F}_p$ to aggregate multiple polynomials

2. Prover computes $h(X)$

$$
h(X) = h_0(X) + \gamma\cdot h_1(X) + \gamma^2\cdot h_2(X) + \cdots + \gamma^{n-1}\cdot h_{n-1}(X)
$$

3. Defines a new Domain $D$ containing $3$ elements:

$$
D = \{\beta, -\beta, \beta^2\}
$$

4. Prover computes a quadratic polynomial $h^*(X)$ such that it matches the values of $h(X)$ on $D$:

$$
h^*(X) = h(\beta)\cdot \frac{(X+\beta)(X-\beta^2)}{2\beta(\beta-\beta^2)} + h(-\beta)\cdot \frac{(X-\beta)(X-\beta^2)}{2\beta(\beta^2+\beta)} + h(\beta^2)\cdot \frac{X^2-\beta^2}{\beta^4-\beta^2}
$$

5. Prover computes the quotient polynomial $q(X)$

$$
q(X) = \frac{h(X) - h^*(X)}{(X^2-\beta^2)(X-\beta^2)}
$$

6. Prover computes the commitment $C_q$ to $q(X)$

$$
C_q = \mathsf{KZG10.Commit}(q(X))
$$

7. Prover sends $C_q$

### Round 4.

1. Verifier sends a random point $\zeta\in\mathbb{F}_p$

2. Prover computes the linearized polynomial $r(X)$ such that $r(\zeta) = 0$:

$$
r(X) = h(X) - h^*(\zeta) - (\zeta^2-\beta^2)(\zeta-\beta^2)\cdot q(X)
$$

3. Prover computes the quotient polynomial $w(X)$

$$
w(X) = \frac{r(X)}{(X-\zeta)}
$$

4. Prover computes the commitment $C_w$ to $w(X)$:

$$
C_w = \mathsf{KZG10.Commit}(w(X))
$$

5. Prover sends $C_w$

### Proof Representation

As we can see, the proof consists of $n+1$ elements in $\mathbb{G}_1$ and $2n+1$ elements in $\mathbb{F}_p$:

$$
\pi=\Big(H_1, H_2, \ldots, H_{n-1}, C_q, C_w, \{h_i(\beta), h_i(-\beta)\}_{i=0}^{n-1}, h_0(\beta^2) \Big)
$$

### Verification Process

1. Verifier computes $(h_1(\beta^2), h_2(\beta^2), \ldots, h_{n-1}(\beta^2))$

$$
h_{i+1}(\beta^2) = \frac{h_i(\beta) + h_i(-\beta)}{2} + u_i\cdot \frac{h_i(\beta) - h_i(-\beta)}{2\beta}
$$

2. Verifier checks if $h_{n}(\beta^2)$ equals the claimed polynomial evaluation $v=\tilde{f}(\vec{u})$

$$
h_n(\beta^2) \overset{?}{=} v
$$

3. Verifier computes the commitment $C_h$ to $h(X)$

$$
C_h = C_f + \gamma\cdot H_1 + \gamma^2\cdot H_2 + \cdots + \gamma^{n-1}\cdot H_{n-1}
$$

4. Verifier computes the commitment $C_r$ to $r_\zeta(X)$:

$$
C_r = C_h - h^*(\zeta)\cdot[1]_1 - (\zeta^2-\beta^2)(\zeta-\beta^2)\cdot C_q
$$

5. Verifier checks if $C_w$ is a valid evaluation proof for $C_r$ at $X=\zeta$:

$$
\mathsf{KZG10.Verify}(C_r, \zeta, 0, C_w) \overset{?}{=} 1
$$

Or directly expanded in pairing form:

$$
e\Big(C_r + \zeta\cdot C_w, [1]_2\Big) \overset{?}{=} e\Big(C_w, [\tau]_2 \Big)
$$

## 3. Performance Analysis of Optimizations

## References