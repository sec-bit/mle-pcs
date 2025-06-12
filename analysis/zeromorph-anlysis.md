# Complexity Analysis of the Zeromorph Protocol Series

- Jade Xie <jade@secbit.io>
- Yu Guo <yu.guo@secbit.io>

## Complexity Analysis of the Evaluation Proof Protocol (Naive Version)

Protocol description doc: [Evaluation Proof Protocol (Naive Version)](https://github.com/sec-bit/mle-pcs/blob/main/zeromorph/zeromorph.md#protocol-description)

Below we present a simple naive implementation of the protocol for ease of understanding.

### Common Inputs

- Commitment to the MLE polynomial $\tilde{f}$: $\mathsf{cm}([[\tilde{f}]]_n)$
- Evaluation point $\mathbf{u}=(u_0, u_1, \ldots, u_{n-1})$
- Evaluation result $v = \tilde{f}(\mathbf{u})$

### Witness

- Point value vector of the MLE polynomial $\tilde{f}$ on the $n$-dimensional HyperCube: $\mathbf{a} = (a_0, a_1, \ldots, a_{2^n-1})$

### Round 1

Prover sends the commitments to the remainder polynomials:

- Computes $n$ remainder MLE polynomials: $\{\tilde{q}_k\}_{k=0}^{n-1}$ 
- Constructs univariate polynomials mapped from the remainder MLE polynomials: $\hat{q}_k=[[\tilde{q}_k]]_k, \quad 0 \leq k < n$
- Computes and sends their commitments: $\mathsf{cm}(\hat{q}_0), \mathsf{cm}(\hat{q}_1), \ldots, \mathsf{cm}(\hat{q}_{n-1})$

$$
\tilde{f}(X_0,X_1,\ldots, X_{n-1}) - v = \sum_{k=0}^{n-1} (X_k-u_k) \cdot \tilde{q}_k(X_0,X_1,\ldots, X_{k-1})
$$

Prover computes $\pi_k=\mathsf{cm}(X^{D_{max}-2^k+1}\cdot \hat{q}_k), \quad 0\leq k<n$, as a degree bound proof for $\deg(\hat{q}_k)<2^k$, and sends them to the Verifier.

> Prover:
>
> - Using the algorithm from [Zeromorph](https://eprint.iacr.org/2023/917) paper Appendix A.2, the values of $\tilde{q}_k$ on the Hypercube can be computed to obtain the coefficients of $Q_k$. According to the paper, the overall algorithm complexity is $(2^{n+1} - 3) ~ \mathbb{F}_{\mathsf{add}}$ and $(2^{n} - 2) ~ \mathbb{F}_{\mathsf{mul}}$. Ignoring the addition complexity, the complexity of computing $\hat{q}_k=[[\tilde{q}_k]]_k, \quad 0 \leq k < n$ is $(2^{n} - 2) ~ \mathbb{F}_{\mathsf{mul}}$.
> - Computing $\mathsf{cm}(\hat{q}_0), \mathsf{cm}(\hat{q}_1), \ldots, \mathsf{cm}(\hat{q}_{n-1})$ involves the MSM algorithm. For each $\mathsf{cm}(\hat{q}_{k})$, polynomial $q_{k}$ has $2^k$ coefficients, with complexity $\mathsf{msm}(2^k,\mathbb{G}_1)$. Therefore, the total complexity for this step is:
> $$
>   \sum_{k=0}^{n-1} \mathsf{msm}(2^k,\mathbb{G}_1)
> $$
> - Computing $\pi_k=\mathsf{cm}(X^{D_{max}-2^k+1}\cdot \hat{q}_k), \quad 0\leq k<n$:
>   - Computing $X^{D_{max}-2^k+1}\cdot \hat{q}_k$ involves polynomial multiplication. Since $\deg(\hat{q}_k) = 2^k - 1$, the complexity is $\mathsf{polymul}(D_{max} - 2^k + 1, 2^k - 1)$, giving a total complexity of:
>       $$
>           \sum_{k=0}^{n-1} \mathsf{polymul}(D_{max} - 2^k + 1, 2^k - 1)
>       $$
>   - Computing the commitments $\pi_k=\mathsf{cm}(X^{D_{max}-2^k+1}\cdot \hat{q}_k), \quad 0\leq k<n$ has complexity:
>       $$
>           \sum_{k=0}^{n-1} \mathsf{msm}(D_{max} + 1,\mathbb{G}_1) = n ~ \mathsf{msm}(D_{max} + 1,\mathbb{G}_1)
>       $$
>   Therefore, the total complexity for this step is:
>  $$
>   \sum_{k=0}^{n-1} \mathsf{polymul}(D_{max} - 2^k + 1, 2^k - 1) + n ~ \mathsf{msm}(D_{max} + 1,\mathbb{G}_1)
>  $$
>
> Thus, the total complexity for this round is:
> 
> $$
>   (2^{n} - 2) ~ \mathbb{F}_{\mathsf{mul}} + \sum_{k=0}^{n-1} \mathsf{msm}(2^k,\mathbb{G}_1) + \sum_{k=0}^{n-1} \mathsf{polymul}(D_{max} - 2^k + 1, 2^k - 1) + n ~ \mathsf{msm}(D_{max} + 1,\mathbb{G}_1)
> $$


> 💡 Note: The polynomial multiplication calculation $X^{D_{max}-2^k+1}\cdot \hat{q}_k$ could be optimized by simply shifting the coefficients of $\hat{q}_k$.

### Round 2

1. Verifier sends a random number $\zeta\in \mathbb{F}_p^*$

2. Prover computes the auxiliary polynomial $r(X)$ and quotient polynomial $h(X)$, and sends $\mathsf{cm}(h)$:
- Computes $r(X)$:

$$
r(X) = [[\tilde{f}]]_{n} - v\cdot \Phi_{n}(\zeta) - \sum_{k=0}^{n-1} \Big(\zeta^{2^k}\cdot \Phi_{n-k-1}(\zeta^{2^{k+1}}) - u_k\cdot \Phi_{n-k}(\zeta^{2^{k}})\Big)\cdot \hat{q}_k(X)
$$

- Computes $h(X)$ and its commitment $\mathsf{cm}(h)$ as a proof that $r(X)$ evaluates to zero at $X=\zeta$:

$$
h(X) = \frac{r(X)}{X-\zeta}
$$



> Prover:
>
> - First calculates the powers of $\zeta$: $\zeta^2, \ldots, \zeta^{2^{n}}$, involving $n$ finite field multiplications with complexity $n ~ \mathbb{F}_{\mathsf{mul}}$.
> - Computing $r(X)$:
>   - Calculates $\Phi_n(\zeta)$:
>        $$
>         \Phi_n(\zeta) = \sum_{i=0}^{n-1} \zeta^{2^i}
>        $$
>
>     This can be directly computed using the previously calculated powers of $\zeta$, involving finite field additions which we don't count in our complexity analysis.
>   - Calculates $v \cdot \Phi_n(\zeta)$, involving one finite field multiplication, with complexity $\mathbb{F}_{\mathsf{mul}}$.
>   - Calculates $\Phi_{n-k-1}(\zeta^{2^{k+1}})$. Since:
>       $$
>       \Phi_{n-k-1}(X^{2^{k+1}}) = 1 + X^{2^{k + 1}} + X^{2 \cdot 2^{k + 1}} + \ldots + X^{(2^{n - k - 1} - 1) \cdot 2^{k + 1}}
>       $$
>     Therefore:
>       $$
>       \Phi_{n-k-1}(\zeta^{2^{k+1}}) = 1 + \zeta^{2^{k + 1}} + \zeta^{2 \cdot 2^{k + 1}} + \ldots + \zeta^{(2^{n - k - 1} - 1) \cdot 2^{k + 1}}
>       $$ 
>     This can also be calculated directly through finite field additions. Similarly, $\Phi_{n-k}(\zeta^{2^{k}})$ can be calculated the same way.
>   - Calculating $\zeta^{2^k}\cdot \Phi_{n-k-1}(\zeta^{2^{k+1}}) - u_k\cdot \Phi_{n-k}(\zeta^{2^{k}})$ involves two finite field multiplications with complexity $2 ~ \mathbb{F}_{\mathsf{mul}}$. For all $k$, this gives $2n ~ \mathbb{F}_{\mathsf{mul}}$.
>   - Calculating $\Big(\zeta^{2^k}\cdot \Phi_{n-k-1}(\zeta^{2^{k+1}}) - u_k\cdot \Phi_{n-k}(\zeta^{2^{k}})\Big)\cdot \hat{q}_k(X)$ involves polynomial multiplication with complexity $\mathsf{polymul}(0, 2^k - 1)$. The total complexity after summing over all $k$ is:
>       $$
>           \sum_{k = 0}^{n - 1} \mathsf{polymul}(0, 2^k - 1)
>       $$
>   Therefore, the total complexity for computing $r(X)$ is:
>
>   $$
>       \mathbb{F}_{\mathsf{mul}} + 2n ~ \mathbb{F}_{\mathsf{mul}} +  \sum_{k = 0}^{n - 1} \mathsf{polymul}(0, 2^k - 1) = (2n + 1) ~ \mathbb{F}_{\mathsf{mul}} + \sum_{k = 0}^{n - 1} \mathsf{polymul}(0, 2^k - 1)
>   $$
>
> - Computing $\mathsf{cm}(h)$: First calculate $h(X)$ using polynomial division, with complexity related to the degree of $r(X)$. Since $\deg(r) = 2^{n - 1} - 1$, the complexity of polynomial division is $(2^{n - 1} - 1) ~ \mathbb{F}_{\mathsf{mul}}$. Then compute the commitment with complexity $\mathsf{msm}(2^{n - 1} - 1, \mathbb{G}_1)$. The total complexity for this step is:
>   $$
>       (2^{n - 1} - 1) ~ \mathbb{F}_{\mathsf{mul}} + \mathsf{msm}(2^{n - 1} - 1, \mathbb{G}_1)
>   $$
>
> The total complexity for this round is:
> $$
>   (3n + 2^{n - 1}) ~ \mathbb{F}_{\mathsf{mul}} + \sum_{k = 0}^{n - 1} \mathsf{polymul}(0, 2^k - 1) + \mathsf{msm}(2^{n - 1} - 1, \mathbb{G}_1)
> $$


### Verification 

Verifier verifies the following equations:

- Constructs the commitment to $\mathsf{cm}(r)$:

$$
\mathsf{cm}(r) = \mathsf{cm}([[\tilde{f}]]_{n}) - \mathsf{cm}(v\cdot \Phi_{n}(\zeta)) - \sum_{i=0}^{n-1} \Big(\zeta^{2^i}\cdot \Phi_{n-i-1}(\zeta^{2^{i+1}}) - u_i\cdot \Phi_{n-i}(\zeta^{2^{i}})\Big)\cdot \mathsf{cm}(\hat{q}_i)
$$

- Verifies that $r(\zeta) = 0$:

$$
e(\mathsf{cm}(r), \ [1]_2) = e(\mathsf{cm}(h), [\tau]_2 - \zeta\cdot [1]_2)
$$

- Verifies that $(\pi_0, \pi_1, \ldots, \pi_{n-1})$ are correct, i.e., verifies the degree bounds $\deg(\hat{q}_i)<2^i$ for all $0\leq i<n$:

$$
e(\mathsf{cm}(\hat{q}_i), [\tau^{D_{max}-2^i+1}]_2) = e(\pi_i, [1]_2), \quad 0\leq i<n
$$


> Verifier:
>
> - Constructing $\mathsf{cm}(r)$:
>   - Calculates the powers of $\zeta$: $\zeta^2, \ldots, \zeta^{2^{n}}$ with complexity $n ~ \mathbb{F}_{\mathsf{mul}}$.
>   - Computes $\mathsf{cm}(v\cdot \Phi_{n}(\zeta))$ with complexity $\mathbb{F}_{\mathsf{mul}} + \mathsf{EccMul}^{\mathbb{G}_1}$
>   - Computes $\sum_{i=0}^{n-1} \Big(\zeta^{2^i}\cdot \Phi_{n-i-1}(\zeta^{2^{i+1}}) - u_i\cdot \Phi_{n-i}(\zeta^{2^{i}})\Big)\cdot \mathsf{cm}(\hat{q}_i)$ with complexity:
>     $$
>        n( 2 ~ \mathbb{F}_{\mathsf{mul}}  + \mathsf{EccMul}^{\mathbb{G}_1}) + (n - 1) ~ \mathsf{EccAdd}^{\mathbb{G}_1} = 2n ~ \mathbb{F}_{\mathsf{mul}} + n ~ \mathsf{EccMul}^{\mathbb{G}_1} + (n - 1) ~ \mathsf{EccAdd}^{\mathbb{G}_1}
>     $$
>   - Computes $\mathsf{cm}([[\tilde{f}]]_{n}) - \mathsf{cm}(v\cdot \Phi_{n}(\zeta)) - \sum_{i=0}^{n-1} \Big(\zeta^{2^i}\cdot \Phi_{n-i-1}(\zeta^{2^{i+1}}) - u_i\cdot \Phi_{n-i}(\zeta^{2^{i}})\Big)\cdot \mathsf{cm}(\hat{q}_i)$ by adding three points on the elliptic curve, with complexity $2 ~ \mathsf{EccAdd}^{\mathbb{G}_1}$.
>   
>   The total complexity for constructing $\mathsf{cm}(r)$ is:
>   $$
>     (3n + 1)~ \mathbb{F}_{\mathsf{mul}} + (n + 1) ~ \mathsf{EccMul}^{\mathbb{G}_1} + (n + 1) ~ \mathsf{EccAdd}^{\mathbb{G}_1}
>   $$
> - Verifying $r(\zeta) = 0$:
>   - Computes $[\tau]_2 - \zeta\cdot [1]_2$ with complexity $\mathsf{EccMul}^{\mathbb{G}_2} + \mathsf{EccAdd}^{\mathbb{G}_2}$
>   - Computes $e(\mathsf{cm}(r), \ [1]_2)$ and $e(\mathsf{cm}(h), [\tau]_2 - \zeta\cdot [1]_2)$, involving two pairing operations, denoted as $2~P$.
>   
>   The total complexity for this step is:
>   $$
>     \mathsf{EccMul}^{\mathbb{G}_2} + \mathsf{EccAdd}^{\mathbb{G}_2} + 2~P
>   $$
> - Verifying $(\pi_0, \pi_1, \ldots, \pi_{n-1})$:
>     $$
>         e(\mathsf{cm}(\hat{q}_i), [\tau^{D_{max}-2^i+1}]_2) = e(\pi_i, [1]_2), \quad 0\leq i<n
>     $$
>     Each verification involves $2 ~ P$, so the total complexity is $2n ~ P$.
>
> The total complexity for this round is:
>
> $$
> (3n + 1)~ \mathbb{F}_{\mathsf{mul}} + (n + 1) ~ \mathsf{EccMul}^{\mathbb{G}_1} + (n + 1) ~ \mathsf{EccAdd}^{\mathbb{G}_1} + \mathsf{EccMul}^{\mathbb{G}_2} + \mathsf{EccAdd}^{\mathbb{G}_2} +  (2n + 2)~P
> $$

### Summary

> **Prover Computational Complexity:**
> 
> $$
> \begin{aligned}
>     & (2^{n} - 2) ~ \mathbb{F}_{\mathsf{mul}} + \sum_{k=0}^{n-1} \mathsf{msm}(2^k,\mathbb{G}_1) + \sum_{k=0}^{n-1} \mathsf{polymul}(D_{max} - 2^k + 1, 2^k - 1) + n ~ \mathsf{msm}(D_{max} + 1,\mathbb{G}_1) \\
>     & + (3n + 2^{n - 1}) ~ \mathbb{F}_{\mathsf{mul}} + \sum_{k = 0}^{n - 1} \mathsf{polymul}(0, 2^k - 1) + \mathsf{msm}(2^{n - 1} - 1, \mathbb{G}_1) \\
>     = & ( 3 \cdot 2^{n - 1} + 3n - 2) ~ \mathbb{F}_{\mathsf{mul}} + \sum_{k=0}^{n-1} \mathsf{polymul}(D_{max} - 2^k + 1, 2^k - 1) + \sum_{k = 0}^{n - 1} \mathsf{polymul}(0, 2^k - 1) \\
>     & + \sum_{k=0}^{n-1} \mathsf{msm}(2^k,\mathbb{G}_1) +  n ~ \mathsf{msm}(D_{max} + 1,\mathbb{G}_1) + \mathsf{msm}(2^{n - 1} - 1, \mathbb{G}_1)
> \end{aligned}
> $$
> 
> **Verifier Computational Complexity:**
> 
> $$
> (3n + 1)~ \mathbb{F}_{\mathsf{mul}} + (n + 1) ~ \mathsf{EccMul}^{\mathbb{G}_1} + (n + 1) ~ \mathsf{EccAdd}^{\mathbb{G}_1} + \mathsf{EccMul}^{\mathbb{G}_2} + \mathsf{EccAdd}^{\mathbb{G}_2} +  (2n + 2)~P
> $$
> 
> **Proof Size:**
> 
> The proof sent by the Prover consists of: 
> 
> $$
> (\mathsf{cm}(\hat{q}_0), \mathsf{cm}(\hat{q}_1), \ldots, \mathsf{cm}(\hat{q}_{n-1}), \pi_0, \ldots, \pi_{n - 1}, \mathsf{cm}(h))
> $$
> 
> For a total of $(2n + 1) \mathbb{G}_1$ elements.


Substituting the polynomial multiplication complexity $\mathsf{polymul}(a, b) = (a + 1) (b + 1) ~ \mathbb{F}_{\mathsf{mul}} = (ab + a + b + 1) ~ \mathbb{F}_{\mathsf{mul}}$, we get:

Prover complexity:

$$
\begin{align}
& ( 3 \cdot 2^{n - 1} + 3n - 2) ~ \mathbb{F}_{\mathsf{mul}} + \sum_{k=0}^{n-1} \mathsf{polymul}(D_{max} - 2^k + 1, 2^k - 1) + \sum_{k = 0}^{n - 1} \mathsf{polymul}(0, 2^k - 1) \\
& + \sum_{k=0}^{n-1} \mathsf{msm}(2^k,\mathbb{G}_1) +  n ~ \mathsf{msm}(D_{max} + 1,\mathbb{G}_1) + \mathsf{msm}(2^{n - 1} - 1, \mathbb{G}_1) \\
=  & ( \frac{3}{2}  N + 3n - 2) ~ \mathbb{F}_{\mathsf{mul}} + ((D_{max} + 2)(N - 1) - \frac{1}{3}(N^2 - 1))~ \mathbb{F}_{\mathsf{mul}} + (N - 1) ~ \mathbb{F}_{\mathsf{mul}}\\
& + \sum_{k=0}^{n-1} \mathsf{msm}(2^k,\mathbb{G}_1) +  n ~ \mathsf{msm}(D_{max} + 1,\mathbb{G}_1) + \mathsf{msm}(2^{n - 1} - 1, \mathbb{G}_1) \\
= & ((D_{max} + \frac{9}{2}) N - \frac{1}{3} N^2 + 3n - D_{max} - \frac{14}{3}) ~ \mathbb{F}_{\mathsf{mul}} \\
& + \sum_{k=0}^{n-1} \mathsf{msm}(2^k,\mathbb{G}_1) +  n ~ \mathsf{msm}(D_{max} + 1,\mathbb{G}_1) + \mathsf{msm}(2^{n - 1} - 1, \mathbb{G}_1) \\
\end{align}
$$

Verifier complexity:

$$
(3n + 1)~ \mathbb{F}_{\mathsf{mul}} + (n + 1) ~ \mathsf{EccMul}^{\mathbb{G}_1} + (n + 1) ~ \mathsf{EccAdd}^{\mathbb{G}_1} + \mathsf{EccMul}^{\mathbb{G}_2} + \mathsf{EccAdd}^{\mathbb{G}_2} +  (2n + 2)~P
$$

Proof size:

$$
(2n + 1) \mathbb{G}_1
$$

## Evaluation Proof Protocol (Optimized Version - Degree Bound Aggregation)

Protocol description doc: [Evaluation Proof Protocol (Optimized Version)](https://github.com/sec-bit/mle-pcs/blob/main/zeromorph/zeromorph.md#optimized-protocol)

### Common Inputs

- Commitment to the MLE polynomial $\tilde{f}$ mapped to univariate polynomial $f(X)=[[\tilde{f}]]_n$: $\mathsf{cm}([[\tilde{f}]]_n)$
- Evaluation point $\mathbf{u}=(u_0, u_1, \ldots, u_{n-1})$
- Evaluation result $v = \tilde{f}(\mathbf{u})$

### Witness

- Point value vector of the MLE polynomial $\tilde{f}$: $\mathbf{a} = (a_0, a_1, \ldots, a_{2^n-1})$

### Round 1

First round: Prover sends the commitments to the remainder polynomials

- Computes $n$ remainder MLE polynomials: $\{q_i\}_{i=0}^{n-1}$ 
- Constructs univariate polynomials mapped from the remainder MLE polynomials: $\hat{q}_i=[[q_i]]_i, \quad 0 \leq i < n$
- Computes and sends their commitments: $\mathsf{cm}(\hat{q}_0), \mathsf{cm}(\hat{q}_1), \ldots, \mathsf{cm}(\hat{q}_{n-1})$

$$
\tilde{f}(X_0,X_1,\ldots, X_{n-1}) - v = \sum_{i=0}^{n-1} (X_k-u_k) \cdot q_i(X_0,X_1,\ldots, X_{k-1})
$$

> Prover:
> 
> - Using the [Zeromorph](https://eprint.iacr.org/2023/917) paper's algorithm from Appendix A.2, values of $q_i$ on the Hypercube can be computed to obtain $Q_i$ coefficients. This has complexity $(2^{n} - 2) ~ \mathbb{F}_{\mathsf{mul}}$.
> - Computing $\mathsf{cm}(q_0), \mathsf{cm}(q_1), \ldots, \mathsf{cm}(q_{n-1})$ with total complexity:
> 
> $$
>   \sum_{k=0}^{n-1} \mathsf{msm}(2^k,\mathbb{G}_1)
> $$
>
> Therefore, the total complexity for this round is:
> 
> $$
>   (2^{n} - 2) ~ \mathbb{F}_{\mathsf{mul}} + \sum_{k=0}^{n-1} \mathsf{msm}(2^k,\mathbb{G}_1)
> $$
>



### Round 2

1. Verifier sends a random number $\beta\in \mathbb{F}_p^*$ to aggregate multiple degree bound proofs

2. Prover constructs $\bar{q}(X)$ as an aggregation polynomial for $\{\hat{q}_i(X)\}$, and sends its commitment $\mathsf{cm}(\bar{q})$:

$$
\bar{q}(X) = \sum_{i=0}^{n-1} \beta^i \cdot X^{2^n-2^i}\hat{q}_i(X)
$$
> Prover:
> 
> - First calculates powers of $\beta$: $\beta^2, \ldots, \beta^{n - 1}$, with complexity $(n - 2) ~ \mathbb{F}_{\mathsf{mul}}$
> - Computing $\beta^i \cdot X^{2^n-2^i}\hat{q}_i(X)$ is polynomial multiplication with complexity $\mathsf{polymul}(2^n - 2^i, 2^i - 1) + \mathsf{polymul}(0, 2^n - 1)$. The total complexity for the sum is:
>     $$
>     \begin{aligned}
>         & \sum_{i = 0}^{n - 1} \big( \mathsf{polymul}(2^n - 2^i, 2^i - 1) + \mathsf{polymul}(0, 2^n - 1) \big) \\
>         = & n ~ \mathsf{polymul}(0, 2^n - 1) + \sum_{i = 0}^{n - 1} \mathsf{polymul}(2^n - 2^i, 2^i - 1)
>     \end{aligned}
>     $$
> - Computing $\mathsf{cm}(\bar{q})$ has complexity $\mathsf{msm}(2^n , \mathbb{G}_1)$
> 
> The total complexity for this round is:
> 
> $$
> (n - 2) ~ \mathbb{F}_{\mathsf{mul}} + n ~ \mathsf{polymul}(0, 2^n - 1) + \sum_{i = 0}^{n - 1} \mathsf{polymul}(2^n - 2^i, 2^i - 1) + \mathsf{msm}(2^n , \mathbb{G}_1)
> $$

### Round 3

1. Verifier sends a random number $\zeta\in \mathbb{F}_p^*$ to challenge polynomial evaluation at $X=\zeta$

2. Prover computes $h_0(X)$ and $h_1(X)$:

- Computes $r(X)$:

$$
r(X) = \hat{f}(X) - v\cdot \Phi_{n}(\zeta) - \sum_{i=0}^{n-1} \Big(\zeta^{2^i}\cdot \Phi_{n-i-1}(\zeta^{2^{i+1}}) - u_i\cdot \Phi_{n-i}(\zeta^{2^{i}})\Big)\cdot\hat{q}_i(X)
$$
- Computes $s(X)$:

$$
s(X) = \bar{q}(X) - \sum_{k=0}^{n-1} \beta^k \cdot \zeta^{2^n-2^k}\cdot \hat{q}_k(X)
$$

- Computes quotient polynomials $h_0(X)$ and $h_1(X)$:

$$
h_0(X) = \frac{r(X)}{X-\zeta}, \qquad h_1(X) = \frac{s(X)}{X-\zeta}
$$

> Prover:
> 
> - First calculates powers of $\zeta$: $\zeta^2, \ldots, \zeta^{2^{n}}$, with complexity $n ~ \mathbb{F}_{\mathsf{mul}}$.
> - Computing $r(X)$ has complexity:
> 
>     $$
>     (2n + 1) ~ \mathbb{F}_{\mathsf{mul}} + \sum_{k = 0}^{n - 1} \mathsf{polymul}(0, 2^k - 1)
>     $$
> 
> - Computing $s(X)$:
>   - $\beta^k \cdot \zeta^{2^n-2^k}$ has complexity $\mathbb{F}_{\mathsf{mul}}$
>   - $\beta^k \cdot \zeta^{2^n-2^k}\cdot \hat{q}_k(X)$ has complexity $\mathsf{polymul}(0, 2^k - 1)$
>   
>   Thus computing $s(X) = \bar{q}(X) - \sum_{k=0}^{n-1} \beta^k \cdot \zeta^{2^n-2^k}\cdot \hat{q}_k(X)$ has complexity:
> 
>   $$
>     n ~ \mathbb{F}_{\mathsf{mul}} + \sum_{k = 0}^{n - 1} \mathsf{polymul}(0, 2^k - 1)
>   $$
> 
> - Computing the quotient polynomials $h_0(X)$ and $h_1(X)$ can be done using polynomial long division. Since $\deg(r) = 2^n - 1$ and $\deg(s(X)) = 2^n - 1$, the complexity for this step is:
> 
>     $$
>         (2^{n + 1} - 2) ~ \mathbb{F}_{\mathsf{mul}}
>     $$
> 
> The total complexity for this round is:
> 
> $$
> \begin{aligned}
>     & n ~ \mathbb{F}_{\mathsf{mul}} + (2n + 1) ~ \mathbb{F}_{\mathsf{mul}} \\
>     & + \sum_{k = 0}^{n - 1} \mathsf{polymul}(0, 2^k - 1) +  n ~ \mathbb{F}_{\mathsf{mul}} + \sum_{k = 0}^{n - 1} \mathsf{polymul}(0, 2^k - 1) +  (2^{n + 1} - 2) ~ \mathbb{F}_{\mathsf{mul}} \\
>      = & (4n + 2^{n + 1} - 1) ~ \mathbb{F}_{\mathsf{mul}} + 2 \sum_{k = 0}^{n - 1} \mathsf{polymul}(0, 2^k - 1)
> \end{aligned}
> $$

### Round 4

1. Verifier sends a random number $\alpha\in \mathbb{F}_p^*$ to aggregate $h_0(X)$ and $h_1(X)$

2. Prover computes $h(X)$ and sends its commitment $\mathsf{cm}(h)$:

$$
h(X)=(h_0(X) + \alpha\cdot h_1(X))\cdot X^{D_{max}-2^n+2}
$$ 

> Prover:
> 
> - Computing $h_0(X) + \alpha\cdot h_1(X)$ has complexity $\mathsf{polymul}(0, 2^n - 2)$.
> - Computing $(h_0(X) + \alpha\cdot h_1(X))\cdot X^{D_{max}-2^n+1}$ has complexity $\mathsf{polymul}(2^n - 2, D_{max}-2^n+1)$.
> - Computing $\mathsf{cm}(h)$ has complexity $\mathsf{msm}(D_{max} + 1, {\mathbb{G}_1})$
> 
> The total complexity for this round is:
> 
> $$
> \mathsf{polymul}(0, 2^n - 2) + \mathsf{polymul}(2^n - 2, D_{max}-2^n+1) + \mathsf{msm}(D_{max} + 1, {\mathbb{G}_1})
> $$

### Verification 

Verifier:

- Constructs the commitment to $\mathsf{cm}(r)$:

$$
\mathsf{cm}(r) = \mathsf{cm}(f) - \mathsf{cm}(v\cdot \Phi_{n}(\zeta)) - \sum_{i=0}^{n-1} \Big(\zeta^{2^i}\cdot \Phi_{n-i-1}(\zeta^{2^{i+1}}) - u_i\cdot \Phi_{n-i}(\zeta^{2^{i}})\Big)\cdot \mathsf{cm}(\hat{q}_i)
$$

- Constructs the commitment to $\mathsf{cm}(s)$:

$$
\mathsf{cm}(s) = \mathsf{cm}(\bar{q}) - \sum_{i=0}^{n-1} \beta^i \cdot \zeta^{2^n-2^i}\cdot \mathsf{cm}(\hat{q}_i)
$$
- Verifies that $r(\zeta) = 0$ and $s(\zeta) = 0$:

$$
e(\mathsf{cm}(r) + \alpha\cdot \mathsf{cm}(s), \ [\tau^{D-2^n+2}]_2) = e(\mathsf{cm}(h),\ [\tau]_2 - \zeta\cdot [1]_2)
$$


> Proof size:
> 
> Before verification, the Verifier has received the following proof:
> 
> $$
> \pi = (\mathsf{cm}(\hat{q}_0), \mathsf{cm}(\hat{q}_1), \ldots, \mathsf{cm}(\hat{q}_{n-1}), \mathsf{cm}(\bar{q}), \mathsf{cm}(h))
> $$
> 
> Thus, the proof size is $(n + 2) ~ \mathbb{G}_1$.


> Verifier:
> 
> - Constructing $\mathsf{cm}(r)$:
>   - Computes powers of $\zeta$: $\zeta^2, \zeta^4, \ldots, \zeta^{2^n}$, with complexity $n ~ \mathbb{F}_{\mathsf{mul}}$.
>   - Computes $\mathsf{cm}(v\cdot \Phi_{n}(\zeta))$ with complexity $\mathbb{F}_{\mathsf{mul}} + \mathsf{EccMul}^{\mathbb{G}_1}$
>   - Computes $\sum_{i=0}^{n-1} \Big(\zeta^{2^i}\cdot \Phi_{n-i-1}(\zeta^{2^{i+1}}) - u_i\cdot \Phi_{n-i}(\zeta^{2^{i}})\Big)\cdot \mathsf{cm}(\hat{q}_i)$:
>     - Each term has complexity $2 ~ \mathbb{F}_{\mathsf{mul}} + \mathsf{EccMul}^{\mathbb{G}_1}$
>     
>     The total complexity is $2n ~ \mathbb{F}_{\mathsf{mul}} + n ~\mathsf{EccMul}^{\mathbb{G}_1} + (n - 1) ~\mathsf{EccAdd}^{\mathbb{G}_1}$
> 
>   - Adding the three $\mathbb{G}_1$ points has complexity $2~\mathsf{EccAdd}^{\mathbb{G}_1}$.
>   
>   The total complexity for computing $\mathsf{cm}(r)$ is:
> 
>   $$
>     \begin{aligned}
>         & n ~ \mathbb{F}_{\mathsf{mul}} + \mathbb{F}_{\mathsf{mul}} + \mathsf{EccMul}^{\mathbb{G}_1} + 2n ~ \mathbb{F}_{\mathsf{mul}} + n ~\mathsf{EccMul}^{\mathbb{G}_1} + (n - 1) ~\mathsf{EccAdd}^{\mathbb{G}_1} + 2~\mathsf{EccAdd}^{\mathbb{G}_1} \\
>         = & (3n + 1) ~ \mathbb{F}_{\mathsf{mul}} + (n + 1) ~ \mathsf{EccMul}^{\mathbb{G}_1} + (n + 1) ~ \mathsf{EccAdd}^{\mathbb{G}_1}
>     \end{aligned}
>   $$
> 
> - Computation of the commitment $\mathsf{cm}(s)$
>   - Calculate $\beta^2, \ldots, \beta^{n-1}$ with complexity of $(n-2)~\mathbb{F}_{\mathsf{mul}}$
>   - Calculate $\beta^i \cdot \zeta^{2^n-2^i}\cdot \mathsf{cm}(\hat{q}_i)$ with complexity of $\mathbb{F}_{\mathsf{mul}} + \mathsf{EccMul}^{\mathbb{G}_1}$ for each term. Computing the sum $\sum_{i=0}^{n-1} \beta^i \cdot \zeta^{2^n-2^i}\cdot \mathsf{cm}(\hat{q}_i)$ requires not only calculating each term, but also adding $n$ points on the elliptic curve. Therefore, the total complexity is:
>   
>     $$
>     n ~ \mathbb{F}_{\mathsf{mul}} + n ~ \mathsf{EccMul}^{\mathbb{G}_1} + (n - 1) ~ \mathsf{EccAdd}^{\mathbb{G}_1}
>     $$
> 
>   - Calculate $\mathsf{cm}(\bar{q}) - \sum_{i=0}^{n-1} \beta^i \cdot \zeta^{2^n-2^i}\cdot \mathsf{cm}(\hat{q}_i)$ with complexity of $\mathsf{EccAdd}^{\mathbb{G}_1}$ for adding two points on the elliptic curve $\mathbb{G}_1$.
>   
>   Therefore, the total complexity for computing $\mathsf{cm}(s)$ is:
> 
>   $$
>   (2n-2)~\mathbb{F}_{\mathsf{mul}} + n~\mathsf{EccMul}^{\mathbb{G}_1} + n~\mathsf{EccAdd}^{\mathbb{G}_1}
>   $$
> 
> - Verification that $r(\zeta) = 0$ and $s(\zeta) = 0$
>   - Calculate $\mathsf{cm}(r) + \alpha\cdot \mathsf{cm}(s)$ and $[\tau]_2 - \zeta\cdot [1]_2$ with complexity of $\mathsf{EccMul}^{\mathbb{G}_1} + \mathsf{EccAdd}^{\mathbb{G}_1} + \mathsf{EccMul}^{\mathbb{G}_2} + \mathsf{EccAdd}^{\mathbb{G}_2}$
>   - Calculate the pairings $e(\mathsf{cm}(r) + \alpha\cdot \mathsf{cm}(s), [\tau^{D-2^n+2}]_2)$ and $e(\mathsf{cm}(h), [\tau]_2 - \zeta\cdot [1]_2)$, involving two pairing operations on elliptic curves, denoted as $2~P$
>   
>   The total complexity for this step is:
> 
>   $$
>   \mathsf{EccMul}^{\mathbb{G}_1} + \mathsf{EccAdd}^{\mathbb{G}_1} + \mathsf{EccMul}^{\mathbb{G}_2} + \mathsf{EccAdd}^{\mathbb{G}_2} + 2~P
>   $$
> 
> The total complexity for the Verification phase is:
> 
> $$
> \begin{aligned}
>   & (3n + 1) ~ \mathbb{F}_{\mathsf{mul}} + (n + 1) ~ \mathsf{EccMul}^{\mathbb{G}_1} + (n + 1) ~ \mathsf{EccAdd}^{\mathbb{G}_1} \\
>   & + (2n - 2) ~ \mathbb{F}_{\mathsf{mul}}  + n ~ \mathsf{EccMul}^{\mathbb{G}_1} + n ~ \mathsf{EccAdd}^{\mathbb{G}_1} \\
>   & +   \mathsf{EccMul}^{\mathbb{G}_1} + \mathsf{EccAdd}^{\mathbb{G}_1} + \mathsf{EccMul}^{\mathbb{G}_2} + \mathsf{EccAdd}^{\mathbb{G}_2} + 2~P \\
>   = & (5n - 1) ~ \mathbb{F}_{\mathsf{mul}} + (2n + 2) ~ \mathsf{EccMul}^{\mathbb{G}_1} + (2n + 2) ~ \mathsf{EccAdd}^{\mathbb{G}_1} + \mathsf{EccMul}^{\mathbb{G}_2} + \mathsf{EccAdd}^{\mathbb{G}_2} + 2~P
> \end{aligned}
> $$

### Summary

> **Prover Computational Complexity:**
> 
> $$
> \begin{aligned}
>   & (2^{n} - 2) ~ \mathbb{F}_{\mathsf{mul}} + \sum_{k=0}^{n-1} \mathsf{msm}(2^k,\mathbb{G}_1) \\
>   & + (n - 2) ~ \mathbb{F}_{\mathsf{mul}} + n ~ \mathsf{polymul}(0, 2^n - 1) + \sum_{i = 0}^{n - 1} \mathsf{polymul}(2^n - 2^i, 2^i - 1) + \mathsf{msm}(2^n , \mathbb{G}_1) \\
>   & + (4n + 2^{n + 1} - 1) ~ \mathbb{F}_{\mathsf{mul}} + 2 \sum_{k = 0}^{n - 1} \mathsf{polymul}(0, 2^k - 1) \\
>   & + \mathsf{polymul}(0, 2^n - 2) + \mathsf{polymul}(2^n - 2, D_{max}-2^n+1) + \mathsf{msm}(D_{max} + 1, {\mathbb{G}_1})\\
>   = & (3 \cdot 2^n + 5n - 5) ~ \mathbb{F}_{\mathsf{mul}} +  n ~ \mathsf{polymul}(0, 2^n - 1) + \sum_{i = 0}^{n - 1} \mathsf{polymul}(2^n - 2^i, 2^i - 1) \\
>   & + 2 \sum_{k = 0}^{n - 1} \mathsf{polymul}(0, 2^k - 1) + \mathsf{polymul}(0, 2^n - 2) + \mathsf{polymul}(2^n - 2, D_{max}-2^n+1)\\
>   & + \sum_{k=0}^{n} \mathsf{msm}(2^k,\mathbb{G}_1) + \mathsf{msm}(D_{max} + 1, {\mathbb{G}_1})
> \end{aligned}
> $$
> 
> **Verifier Computational Complexity:**
> 
> $$
> (5n - 1) ~ \mathbb{F}_{\mathsf{mul}} + (2n + 2) ~ \mathsf{EccMul}^{\mathbb{G}_1} + (2n + 2) ~ \mathsf{EccAdd}^{\mathbb{G}_1} + \mathsf{EccMul}^{\mathbb{G}_2} + \mathsf{EccAdd}^{\mathbb{G}_2} + 2~P
> $$
> 
> **Proof Size:**
> 
> $$
> (n + 2) ~ \mathbb{G}_1
> $$

Substituting the polynomial multiplication complexity $\mathsf{polymul}(a, b) = (a + 1) (b + 1) ~ \mathbb{F}_{\mathsf{mul}} = (ab + a + b + 1) ~ \mathbb{F}_{\mathsf{mul}}$, we get:

Prover complexity:

$$
\begin{align}
& (3 \cdot 2^n + 5n - 5) ~ \mathbb{F}_{\mathsf{mul}} +  n ~ \mathsf{polymul}(0, 2^n - 1) + \sum_{i = 0}^{n - 1} \mathsf{polymul}(2^n - 2^i, 2^i - 1) \\
& + 2 \sum_{k = 0}^{n - 1} \mathsf{polymul}(0, 2^k - 1) + \mathsf{polymul}(0, 2^n - 2) + \mathsf{polymul}(2^n - 2, D_{max}-2^n+1)\\
& + \sum_{k=0}^{n} \mathsf{msm}(2^k,\mathbb{G}_1) + \mathsf{msm}(D_{max} + 1, {\mathbb{G}_1}) \\
=  & (3 N + 5n - 5) ~ \mathbb{F}_{\mathsf{mul}} +  nN ~ \mathbb{F}_{\mathsf{mul}} + (\frac{2}{3}N^2 - \frac{2}{3}) ~ \mathbb{F}_{\mathsf{mul}} \\
& + (2N - 2) ~ \mathbb{F}_{\mathsf{mul}} + (N - 1) ~ \mathbb{F}_{\mathsf{mul}} + ((D_{max} + 3)N - N^2 - D_{max} - 2) ~ \mathbb{F}_{\mathsf{mul}} \\
& + \sum_{k=0}^{n} \mathsf{msm}(2^k,\mathbb{G}_1) + \mathsf{msm}(D_{max} + 1, {\mathbb{G}_1})  \\
=  & (-\frac{1}{3}N^2 +nN +(D_{max} +9)N + 5n - \frac{32}{3} - D_{max}) ~ \mathbb{F}_{\mathsf{mul}}  \\
& + \sum_{k=0}^{n} \mathsf{msm}(2^k,\mathbb{G}_1) + \mathsf{msm}(D_{max} + 1, {\mathbb{G}_1})  \\
\end{align}
$$
> 
> **Verifier complexity: **
> 
> $$
> (5n - 1) ~ \mathbb{F}_{\mathsf{mul}} + (2n + 2) ~ \mathsf{EccMul}^{\mathbb{G}_1} + (2n + 2) ~ \mathsf{EccAdd}^{\mathbb{G}_1} + \mathsf{EccMul}^{\mathbb{G}_2} + \mathsf{EccAdd}^{\mathbb{G}_2} + 2~P
> $$
> 
> Proof size:
> 
> $$
> (n + 2) ~ \mathbb{G}_1
> $$
## Zeromorph-PCS (Degree Bound Optimized)

Protocol description doc: [Zeromorph-PCS (Part II)](https://github.com/sec-bit/mle-pcs/blob/main/zeromorph/zeromorph-02.md)

### Common Inputs

- Commitment to the MLE polynomial $\tilde{f}$ mapped to univariate polynomial $f(X)=[[\tilde{f}]]_n$: $\mathsf{cm}(f)$
- Evaluation point $\mathbf{u}=(u_0, u_1, \ldots, u_{n-1})$
- Evaluation result $v = \tilde{f}(\mathbf{u})$

### Witness

- Point value vector of the MLE polynomial $\tilde{f}$: $\mathbf{a} = (a_0, a_1, \ldots, a_{2^n-1})$

### Round 1

- Prover computes $n$ remainder MLE polynomials: $\{\tilde{q}_i\}_{i=0}^{n-1}$ 
- Prover constructs univariate polynomials mapped from the remainder MLE polynomials: $q_i=[[\tilde{q}_i]]_i, \quad 0 \leq i < n$

$$
\tilde{f}(X_0,X_1,\ldots, X_{n-1}) - v = \sum_{i=0}^{n-1} (X_i-u_i) \cdot \tilde{q}_i(X_0,X_1,\ldots, X_{i-1})
$$

- Prover computes and sends their commitments: $\mathsf{cm}(q_0), \mathsf{cm}(q_1), \ldots, \mathsf{cm}(q_{n-1})$

**Prover Cost:**

This round has the same complexity as the previous batched degree bound protocol:

$$
(2^{n} - 2) ~ \mathbb{F}_{\mathsf{mul}} + \sum_{k=0}^{n-1} \mathsf{msm}(2^k,\mathbb{G}_1)
$$

### Round 2

1. Verifier sends a random number $\beta\in \mathbb{F}_q^*$ 
2. Prover constructs $g(X)$ as an aggregated polynomial for $\{q_i(X)\}$, satisfying:

$$
g(X^{-1}) = \sum_{i=0}^{n-1} \beta^i \cdot X^{-2^i+1}\cdot q_i(X)
$$

3. Prover computes and sends the commitment to $g(X)$: $\mathsf{cm}(g)$ 


**Prover Cost:** 
 
- First calculates powers of $\beta$: $\beta^2, \ldots, \beta^{n - 1}$, with complexity $(n - 2) ~ \mathbb{F}_{\mathsf{mul}}$
- Computes $g(X)$ using:

$$
g(X) = \sum_{i = 0}^{n - 1} \beta^i \cdot X^{2^i-1}{q}_i(X^{-1})
$$

Computing $X^{2^i-1}{q}_i(X^{-1})$ involves reversing the coefficients of $q_i(X)$ and then multiplying by $\beta^i$, with complexity $\mathsf{polymul}(0, 2^i - 1)$. The total complexity for the sum is:

$$
\sum_{i = 0}^{n - 1} \mathsf{polymul}(0, 2^i - 1)
$$

- Computing $\mathsf{cm}(g)$ has complexity $\mathsf{msm}(2^{n - 1} , \mathbb{G}_1)$ since $\deg(g) = 2^{n - 1} - 1$.

The total complexity for this round is:

$$
(n - 2) ~ \mathbb{F}_{\mathsf{mul}} + \sum_{i = 0}^{n - 1} \mathsf{polymul}(0, 2^i - 1) + \mathsf{msm}(2^{n - 1} , \mathbb{G}_1)
$$

### Round 3

1. Verifier sends a random number $\zeta\in \mathbb{F}_p^*$ to challenge polynomial evaluation at $X=\zeta$

2. Prover computes $g(\zeta^{-1})$, and computes quotient polynomial $q_g(X)$:

$$
q_g(X) = \frac{g(X) - g(\zeta^{-1})}{X-\zeta^{-1}}
$$

3. Prover constructs linearization polynomials $r_\zeta(X)$ and $s_\zeta(X)$:

- Computes $r_\zeta(X)$:

$$
r_\zeta(X) = f(X) - v\cdot \Phi_{n}(\zeta) - \sum_{i=0}^{n-1} \Big(\zeta^{2^i}\cdot \Phi_{n-i-1}(\zeta^{2^{i+1}}) - u_i\cdot \Phi_{n-i}(\zeta^{2^{i}})\Big)\cdot q_i(X)
$$
- Computes $s_\zeta(X)$ which evaluates to zero at $X=\zeta$:

$$
s_\zeta(X) = g(\zeta^{-1}) - \sum_i\beta^i\zeta^{2^i-1}\cdot q_i(X)
$$

- Computes quotient polynomials $w_r(X)$ and $w_s(X)$:

$$
w_r(X) = \frac{r_\zeta(X)}{X-\zeta}, \qquad w_s(X) = \frac{s_\zeta(X)}{X-\zeta}
$$

4. Computes and sends the commitment $\mathsf{cm}(q_g)$

**Prover Cost:**

- First calculates powers of $\zeta$: $\zeta^2, \ldots, \zeta^{2^{n}}$, with complexity $n ~ \mathbb{F}_{\mathsf{mul}}$.
- Computing $\zeta^{-1}$ has complexity $\mathbb{F}_{\mathsf{inv}}$.
- Computing $g(\zeta^{-1})$ using Horner's method has complexity $2^{n - 1} ~ \mathbb{F}_{\mathsf{mul}}$ since $\deg(g) = 2^{n - 1} - 1$.
- Computing $q_g(X)$ using polynomial division has complexity $(2^{n - 1} - 1) ~ \mathbb{F}_{\mathsf{mul}}$.
- Computing $r_{\zeta}(X)$ has the same complexity as in the optimized protocol:

$$
 (2n + 1) ~ \mathbb{F}_{\mathsf{mul}} + \sum_{k = 0}^{n - 1} \mathsf{polymul}(0, 2^k - 1)
$$
- Computing $s_{\zeta}(X)$: Each $\beta^i \cdot \zeta^{2^i - 1} \cdot q_i(X)$ has complexity $\mathbb{F}_{\mathsf{mul}} + \mathsf{polymul}(0, 2^i - 1)$, so the total complexity is:

$$
n ~ \mathbb{F}_{\mathsf{mul}} + \sum_{i = 0}^{n - 1}\mathsf{polymul}(0, 2^i - 1)
$$

- Computing $w_r(X)$ and $w_s(X)$ using polynomial division has complexity $(3 \cdot 2^{n - 1} - 2) ~ \mathbb{F}_{\mathsf{mul}}$ since $\deg(r_{\zeta}) = 2^n - 1$ and $\deg(s_{\zeta}) = 2^{n - 1} - 1$.

- Computing $\mathsf{cm}(q_g)$ has complexity $\mathsf{msm}(2^{n - 1} - 1, \mathbb{G}_1)$.

The total complexity for this round is:

$$
\begin{aligned}
    & n ~ \mathbb{F}_{\mathsf{mul}} + \mathbb{F}_{\mathsf{inv}} + 2^{n - 1} ~ \mathbb{F}_{\mathsf{mul}} + (2^{n - 1} - 1) ~ \mathbb{F}_{\mathsf{mul}} \\
    & + (2n + 1) ~ \mathbb{F}_{\mathsf{mul}} + \sum_{k = 0}^{n - 1} \mathsf{polymul}(0, 2^k - 1) \\
    & + n ~ \mathbb{F}_{\mathsf{mul}} + \sum_{i = 0}^{n - 1}\mathsf{polymul}(0, 2^i - 1) + (3 \cdot 2^{n - 1} - 2) ~ \mathbb{F}_{\mathsf{mul}} \\
    & + \mathsf{msm}(2^{n - 1} - 1, \mathbb{G}_1) \\
    = & (5 \cdot 2^{n - 1} + 4n - 2) ~ \mathbb{F}_{\mathsf{mul}} + \mathbb{F}_{\mathsf{inv}} + 2 \sum_{k = 0}^{n - 1} \mathsf{polymul}(0, 2^k - 1) + \mathsf{msm}(2^{n - 1} - 1, \mathbb{G}_1)
\end{aligned}
$$

### Round 4

1. Verifier sends a random number $\alpha\in \mathbb{F}_p^*$ to aggregate $w_r(X)$ and $w_s(X)$

2. Prover computes $w(X)$ and sends its commitment $\mathsf{cm}(w)$:

$$
w(X) = w_r(X) + \alpha\cdot w_s(X)
$$

**Prover Cost:**

- Computing $w_r(X) + \alpha \cdot w_s(X)$ has complexity $\mathsf{polymul}(0, 2^{n - 1} - 2)$.
- Computing $\mathsf{cm}(w)$ has complexity $\mathsf{msm}(2^n - 1, \mathbb{G}_1)$ since $\deg(w(X)) = 2^n - 2$.

The total complexity for this round is:

$$
\mathsf{polymul}(0, 2^{n - 1} - 2) + \mathsf{msm}(2^n - 1, \mathbb{G}_1)
$$

### Proof

The complete proof consists of $n+3$ elements in $\mathbb{G}_1$ and $1$ element in $\mathbb{F}_q$:

$$
\pi= \Big( \mathsf{cm}(q_0), \mathsf{cm}(q_1), \ldots, \mathsf{cm}(q_{n-1}), \mathsf{cm}(g), \mathsf{cm}(q_g), \mathsf{cm}(w), g(\zeta^{-1})\Big)
$$

**Proof size:**

$$
\begin{aligned}
    (n + 3) \cdot \mathbb{G}_1 + \mathbb{F}_q
\end{aligned}
$$


### Verification

Verifier:

1. Constructs the commitment to $\mathsf{cm}(r_\zeta)$:

$$
\mathsf{cm}(r_\zeta) = \mathsf{cm}(f) - \mathsf{cm}(v\cdot \Phi_{n}(\zeta)) - \sum_{i=0}^{n-1} \Big(\zeta^{2^i}\cdot \Phi_{n-i-1}(\zeta^{2^{i+1}}) - u_i\cdot \Phi_{n-i}(\zeta^{2^{i}})\Big)\cdot \mathsf{cm}(q_i)
$$

2. Constructs the commitment to $\mathsf{cm}(s_\zeta)$:

$$
\mathsf{cm}(s_\zeta) = g(\zeta^{-1})\cdot[1]_1 - \sum_{i=0}^{n-1} \beta^i \cdot \zeta^{-2^i+1}\cdot \mathsf{cm}(q_i)
$$

3. Verifies that $r_\zeta(\zeta) = 0$ and $s_\zeta(\zeta) = 0$:

$$
e(\mathsf{cm}(r_\zeta) + \alpha\cdot \mathsf{cm}(s_\zeta), \ [1]_2) = e(\mathsf{cm}(w),\ [\tau]_2 - \zeta\cdot [1]_2)
$$

This can be rewritten as:

$$
e(\mathsf{cm}(r_\zeta) + \alpha\cdot \mathsf{cm}(s_\zeta) + \zeta\cdot\mathsf{cm}(w), \ [1]_2) = e(\mathsf{cm}(w),\ [\tau]_2)
$$

4. Verifies the correctness of $g(\zeta^{-1})$:

$$
e(\mathsf{cm}(g) - g(\zeta^{-1})\cdot [1]_1 + \zeta^{-1}\cdot\mathsf{cm}(q_g),\  [1]_2) = e(\mathsf{cm}(q_g), \ [\tau]_2)
$$

**Verifier Cost:**

- Constructing $\mathsf{cm}(r_{\zeta})$ has the same complexity as in the optimized protocol:

$$
(3n + 1) ~ \mathbb{F}_{\mathsf{mul}} + (n + 1) ~ \mathsf{EccMul}^{\mathbb{G}_1} + (n + 1) ~ \mathsf{EccAdd}^{\mathbb{G}_1}
$$

- Constructing $\mathsf{cm}(s_{\zeta})$:
  - Computing $\zeta^{-1}$ has complexity $\mathbb{F}_{\mathsf{inv}}$.
  - Computing $g(\zeta^{-1}) \cdot [1]_1$ has complexity $\mathsf{EccMul}^{\mathbb{G}_1}$.
  - Computing $(\zeta^{-1})^{2^2 - 1}, \ldots, (\zeta^{-1})^{2^{n -1} - 1}$ has complexity $(n - 2) ~ \mathbb{F}_{\mathsf{mul}}$.
  - The computation of $\sum_{i=0}^{n-1} \beta^i \cdot (\zeta^{-1})^{2^i - 1} \cdot \mathsf{cm}(\hat{q}_i)$ has total complexity:
  
  $$
    n ~ \mathbb{F}_{\mathsf{mul}} + n ~ \mathsf{EccMul}^{\mathbb{G}_1} + (n - 1) ~ \mathsf{EccAdd}^{\mathbb{G}_1}
  $$
  - Adding the two $\mathbb{G}_1$ points has complexity $\mathsf{EccAdd}^{\mathbb{G}_1}$.
  
  The total complexity for constructing $\mathsf{cm}(s_{\zeta})$ is:

$$
\begin{aligned}
    & \mathbb{F}_{\mathsf{inv}} + \mathsf{EccMul}^{\mathbb{G}_1} + (n - 2) ~ \mathbb{F}_{\mathsf{mul}} \\
    & + n ~ \mathbb{F}_{\mathsf{mul}} + n ~ \mathsf{EccMul}^{\mathbb{G}_1} + (n - 1) ~ \mathsf{EccAdd}^{\mathbb{G}_1} + \mathsf{EccAdd}^{\mathbb{G}_1} \\
    = & (2n - 2) ~ \mathbb{F}_{\mathsf{mul}} + \mathbb{F}_{\mathsf{inv}} + (n + 1) ~ \mathsf{EccMul}^{\mathbb{G}_1} + n ~ \mathsf{EccAdd}^{\mathbb{G}_1}
\end{aligned}
$$

> - Verification that $r_{\zeta}(\zeta) = 0$ and $s_{\zeta}(\zeta) = 0$
>   - Calculate $\mathsf{cm}(r_{\zeta}) + \alpha \cdot \mathsf{cm}(s_{\zeta}) + \zeta \cdot \mathsf{cm}(w)$ with complexity of $2 ~ \mathsf{EccMul}^{\mathbb{G}_1} + 2 ~\mathsf{EccAdd}^{\mathbb{G}_1}$
>  - Calculate the pairings $e(\mathsf{cm}(r_{\zeta}) + \alpha \cdot \mathsf{cm}(s_{\zeta}) + \zeta \cdot \mathsf{cm}(w), [1]_2)$ and $e(\mathsf{cm}(w), [\tau]_2)$ with complexity of $2~P$
>   
>   Therefore, the total complexity for this step is $2 ~ \mathsf{EccMul}^{\mathbb{G}_1} + 2 ~\mathsf{EccAdd}^{\mathbb{G}_1} + 2~P$

> - Verification of the correctness of $g(\zeta^{-1})$
>   - Calculate $\mathsf{cm}(g) - g(\zeta^{-1}) \cdot [1]_1 + \zeta^{-1} \cdot \mathsf{cm}(q_g)$ with complexity of $2 ~ \mathsf{EccMul}^{\mathbb{G}_1} + 2 ~ \mathsf{EccAdd}^{\mathbb{G}_1}$
>   - Calculate the pairings $e(\mathsf{cm}(g) - g(\zeta^{-1}) \cdot [1]_1 + \zeta^{-1} \cdot \mathsf{cm}(q_g), [1]_2)$ and $e(\mathsf{cm}(q_g), [\tau]_2)$ with complexity of $2~P$
>  
>   Therefore, the total complexity for this step is $2 ~ \mathsf{EccMul}^{\mathbb{G}_1} + 2 ~ \mathsf{EccAdd}^{\mathbb{G}_1} + 2~P$

The pairing checks in steps 3 and 4 can be combined into a single check:

$$
e(\mathsf{cm}(r_{\zeta}) + \alpha \cdot \mathsf{cm}(s_{\zeta}) + \zeta \cdot \mathsf{cm}(w) + \mathsf{cm}(g) - g(\zeta^{-1}) \cdot [1]_1 + \zeta^{-1} \cdot \mathsf{cm}(q_g), [1]_2) \overset{?}{=} e(\mathsf{cm}(w) + \mathsf{cm}(q_g), [\tau]_2)
$$

This has complexity $4 ~ \mathsf{EccMul}^{\mathbb{G}_1} + 6 ~ \mathsf{EccAdd}^{\mathbb{G}_1} + 2~P$

Therefore, the total complexity for the Verification phase is:

$$
\begin{aligned}
    & (3n + 1) ~ \mathbb{F}_{\mathsf{mul}} + (n + 1) ~ \mathsf{EccMul}^{\mathbb{G}_1} + (n + 1) ~ \mathsf{EccAdd}^{\mathbb{G}_1} \\
    & + (2n - 2) ~ \mathbb{F}_{\mathsf{mul}} + \mathbb{F}_{\mathsf{inv}} + (n + 1) ~ \mathsf{EccMul}^{\mathbb{G}_1} + n ~ \mathsf{EccAdd}^{\mathbb{G}_1} \\
    & + 4 ~ \mathsf{EccMul}^{\mathbb{G}_1} + 6 ~\mathsf{EccAdd}^{\mathbb{G}_1} + 2~P  \\
    = & (5n - 1) ~ \mathbb{F}_{\mathsf{mul}} + \mathbb{F}_{\mathsf{inv}} + (2n + 6) ~ \mathsf{EccMul}^{\mathbb{G}_1} + (2n + 7) ~ \mathsf{EccAdd}^{\mathbb{G}_1}  + 2~P
\end{aligned}
$$

### Summary

**Prover Computational Complexity:**

$$
\begin{aligned}
    & (2^{n} - 2) ~ \mathbb{F}_{\mathsf{mul}} + \sum_{k=0}^{n-1} \mathsf{msm}(2^k,\mathbb{G}_1) \\
    & + (n - 2) ~ \mathbb{F}_{\mathsf{mul}} + \sum_{i = 0}^{n - 1} \mathsf{polymul}(0, 2^i - 1) + \mathsf{msm}(2^{n - 1} , \mathbb{G}_1)\\
    & + (5 \cdot 2^{n - 1} + 4n - 2) ~ \mathbb{F}_{\mathsf{mul}} + \mathbb{F}_{\mathsf{inv}} + 2 \sum_{k = 0}^{n - 1} \mathsf{polymul}(0, 2^k - 1) + \mathsf{msm}(2^{n - 1} - 1, \mathbb{G}_1) \\
    & + \mathsf{polymul}(0, 2^{n - 1} - 2) + \mathsf{msm}(2^n - 1, \mathbb{G}_1) \\
    = & (\frac{7}{2} \cdot 2^n + 5n - 6) ~ \mathbb{F}_{\mathsf{mul}} + \mathbb{F}_{\mathsf{inv}} \\
    & + 3 \sum_{k = 0}^{n - 1} \mathsf{polymul}(0, 2^k - 1) + \mathsf{polymul}(0, 2^{n - 1} - 2) \\
    & + \sum_{k=0}^{n} \mathsf{msm}(2^k,\mathbb{G}_1) + \mathsf{msm}(2^{n - 1} , \mathbb{G}_1) + \mathsf{msm}(2^{n - 1} - 1, \mathbb{G}_1) + \mathsf{msm}(2^n - 1, \mathbb{G}_1)
\end{aligned}
$$

Or simply:

$$
\begin{aligned}
    & (\frac{7}{2} \cdot 2^n + 5n - 6) ~ \mathbb{F}_{\mathsf{mul}} + \mathbb{F}_{\mathsf{inv}} \\
    & + 3 \sum_{k = 0}^{n - 1} \mathsf{polymul}(0, 2^k - 1) + \mathsf{polymul}(0, 2^{n - 1} - 2) \\
    & + \sum_{k=0}^{n} \mathsf{msm}(2^k,\mathbb{G}_1) + \mathsf{msm}(2^{n - 1} , \mathbb{G}_1) + \mathsf{msm}(2^{n - 1} - 1, \mathbb{G}_1) + \mathsf{msm}(2^n - 1, \mathbb{G}_1)
\end{aligned}
$$

**Verifier Computational Complexity:**

$$
\begin{aligned}
    (5n - 1) ~ \mathbb{F}_{\mathsf{mul}} + \mathbb{F}_{\mathsf{inv}} + (2n + 6) ~ \mathsf{EccMul}^{\mathbb{G}_1} + (2n + 7) ~ \mathsf{EccAdd}^{\mathbb{G}_1}  + 2~P
\end{aligned}
$$

**Proof Size:**

$$
\begin{aligned}
    (n + 3) \cdot \mathbb{G}_1 + \mathbb{F}_q
\end{aligned}
$$