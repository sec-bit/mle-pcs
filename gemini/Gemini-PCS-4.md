# Gemini-PCS (Part IV)

This article introduces a different optimized protocol that adopts the approach of selecting points from the Query-phase of the FRI protocol, challenging $h_0(X)$ at $X=\beta$, then challenging the folded polynomial $h_1(X)$ at $X=\beta^2$, and so on until $h_{n-1}(\beta^{2^{n-1}})$. The advantage of this approach is that each opening point of $h_i(X)$ can be reused when verifying the folding of $h_{i+1}(X)$, thereby saving a total of $n$ opening points.

## 1. Optimization Approach

## 2. Protocol Description

Proof objective: To prove that a multilinear extension (MLE) polynomial $\tilde{f}(X_0, X_1, \ldots, X_{n-1})$ with $n$ variables has the value $v = \tilde{f}(u_0, u_1, \ldots, u_{n-1})$ at point $\vec{u}=(u_0, u_1, \ldots, u_{n-1})$.

The MLE polynomial $\tilde{f}(X_0, X_1, \ldots, X_{n-1})$ is represented in coefficient form as:

$$
\tilde{f}(X_0, X_1, \ldots, X_{n-1}) = \sum_{i=0}^{n-1} c_i\cdot X_0^{i_0}X_1^{i_1}\cdots X_{n-1}^{i_{n-1}}
$$

### Public Inputs

1. Commitment $C_f$ to the vector $\vec{c}=(c_0, c_1, \ldots, c_{n-1})$

$$
C_f = \mathsf{KZG10.Commit}(\vec{c})
$$

2. Evaluation point $\vec{u}=(u_0, u_1, \ldots, u_{n-1})$

3. $v = \tilde{f}(u_0, u_1, \ldots, u_{n-1})$

### Witness 

- Coefficients $\vec{c}=(c_0, c_1, \ldots, c_{n-1})$ of the polynomial $f(X)$

### Round 1.

1. Prover denotes $h_0(X) = f(X)$, then computes the folded polynomials $h_1(X), h_2(X), \ldots, h_{n-1}(X)$, such that:

$$
h_{i+1}(X^2) = \frac{h_i(X) + h_i(-X)}{2} + u_i\cdot \frac{h_i(X) - h_i(-X)}{2X}
$$

2. Prover computes commitments $(C_{h_1}, C_{h_2}, \ldots, C_{h_{n-1}})$, such that:

$$
C_{h_{i+1}} = \mathsf{KZG10.Commit}(h_{i+1}(X))
$$

3. Prover sends $(C_{h_1}, C_{h_2}, \ldots, C_{h_{n-1}})$

### Round 2.

1. Verifier sends a random point $\beta\in\mathbb{F}_p$

2. Prover computes $h_0(\beta)$

3. Prover computes $h_0(-\beta), h_1(-\beta^2), \ldots, h_{n-1}(-\beta^{2^{n-1}})$

4. Prover sends $\big(h_0(\beta), h_0(-\beta), h_1(-\beta^2), \ldots, h_{n-1}(-\beta^{2^{n-1}})\big)$

### Round 3.

1. Verifier sends a random value $\gamma\in\mathbb{F}_p$ for polynomial aggregation

2. Prover computes $q(X)$ satisfying the equation:

$$
q(X) = \frac{h_0(X)-h_0(\beta)}{X-\beta}+ \sum_{i=0}^{n-1} \gamma^{i+1}\cdot \frac{h_i(X)-h_i(-\beta^{2^i})}{X+\beta^{2^i}}
$$

3. A new Domain $D$ is defined with $3$ elements:

$$
D = \{\beta, -\beta, -\beta^2, \ldots, -\beta^{2^{n-1}}\}
$$

4. Prover computes and sends commitment $C_q=\mathsf{KZG10.Commit}(q(X))$

### Round 4.

1. Verifier sends a random point $\zeta\in\mathbb{F}_q$

2. Prover computes the linearized polynomial $L_\zeta(X)$ which takes value $0$ at $X=\zeta$, i.e., $L_\zeta(\zeta) = 0$:

$$
L_\zeta(X) = v_D(\zeta)\cdot q(X) - \frac{v_D(\zeta)}{\zeta-\beta}\cdot(h_0(X)-h_0(\beta)) - \sum_{i=0}^{n-1} \gamma^{i+1}\cdot \frac{v_D(\zeta)}{\zeta+\beta^{2^i}}\cdot(h_i(X)-h_i(-\beta^{2^i}))
$$

3. Prover computes the quotient polynomial $w(X)$

$$
w(X) = \frac{L_\zeta(X)}{(X-\zeta)}
$$

4. Prover computes and sends the commitment $C_w$ for $w(X)$:

$$
C_w = \mathsf{KZG10.Commit}(w(X))
$$

### Proof Representation

It can be seen that a single proof consists of $n+1$ elements in $\mathbb{G}_1$ and $n+1$ elements in $\mathbb{F}_q$.

$$
\pi=\Big(C_{f_1}, C_{f_2}, \ldots, C_{f_{n-1}}, C_{q}, C_w, h_0(\beta), h_0(-\beta), h_1(-\beta^2), \ldots, h_{n-1}(-\beta^{2^{n-1}})\Big)
$$

### Verification Process

1. Verifier computes $(h_1(\beta^2), h_2(\beta^{2^2}), \ldots, h_{n-1}(\beta^{2^{n-1}}), h_n(\beta^{2^n}))$

$$
h_{i+1}(\beta^{2^{i+1}}) = \frac{h_i(\beta^{2^i}) + h_i(-\beta^{2^i})}{2} + u_i\cdot \frac{h_i(\beta^{2^i}) - h_i(-\beta^{2^i})}{2\beta^{2^i}}
$$

2. Verifier checks if $h_{n}(\beta^{2^n})$ equals the polynomial evaluation $v=\tilde{f}(\vec{u})$ to be proven

$$
h_n(\beta^{2^n}) \overset{?}{=} v
$$

3. Verifier computes the commitment $C_L$ for $L_\zeta(X)$:

$$
C_L = v_D(\zeta)\cdot C_q - e_0\cdot(C_{h_0} - h_0(\beta)\cdot[1]_1) - \sum_{i=0}^{n-1} e_{i+1}\cdot(C_{h_i} - h_i(-\beta^{2^i})\cdot[1]_1)
$$

where $e_0, e_1, \ldots, e_n$ are defined as:

$$
\begin{aligned}
e_0 &= \frac{v_D(\zeta)}{\zeta - \beta} \\
e_{i+1} &= \gamma^{i+1}\cdot \frac{v_D(\zeta)}{\zeta+\beta^{2^i}}, \quad i=0,1,\ldots,n-1
\end{aligned}
$$

4. Verifier checks if $C_w$ is the evaluation proof of $C_L$ at $X=\zeta$:

$$
\mathsf{KZG10.Verify}(C_L, \zeta, 0, C_w) \overset{?}{=} 1
$$

Or expanded directly into Pairing form:

$$
e\Big(C_L + \zeta\cdot C_w, [1]_2\Big) \overset{?}{=} e\Big(C_w, [\tau]_2 \Big)
$$

## 3. Performance Analysis of the Optimization

## References