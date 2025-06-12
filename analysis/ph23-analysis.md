# PH23 Protocol Complexity Analysis

- Jade Xie <jade@secbit.io>
- Yu Guo <yu.guo@secbit.io>

PH23+KZG10 Protocol (Optimized Version) Protocol Description Document: [PH23+KZG10 Protocol (Optimized Version)](https://github.com/sec-bit/mle-pcs/blob/main/ph23/ph23-pcs-02.md#2-ph23kzg10-protocol-optimized-version)

For the KZG10 protocol, its Commitment has additive homomorphism.

## Precomputation

1. Precompute $s_0(X),\ldots, s_{n-1}(X)$ and $v_H(X)$

$$
v_H(X) = X^N - 1 
$$

$$
s_i(X) = \frac{v_H(X)}{v_{H_i}(X)} = \frac{X^N-1}{X^{2^i}-1}
$$

2. Precompute Bary-Centric Weights $\{\hat{w}_i\}$ on $D=(1, \omega, \omega^2, \ldots, \omega^{2^{n-1}})$. This can accelerate

$$
\hat{w}_j = \prod_{l\neq j} \frac{1}{\omega^{2^j} - \omega^{2^l}}
$$

3. Precompute KZG10 SRS for Lagrange Basis $A_0 =[L_0(\tau)]_1, A_1= [L_1(\tau)]_1, A_2=[L_2(\tau)]_1, \ldots, A_{N-1} = [L_{2^{n-1}}(\tau)]_1$

## Common inputs

1. $C_a=[\hat{f}(\tau)]_1$: the (uni-variate) commitment of $\tilde{f}(X_0, X_1, \ldots, X_{n-1})$
2. $\vec{u}=(u_0, u_1, \ldots, u_{n-1})$: evaluation point
3. $v=\tilde{f}(u_0,u_1,\ldots, u_{n-1})$: computed value of MLE polynomial $\tilde{f}$ at $\vec{X}=\vec{u}$

## Commit calculation process

1. Prover constructs a univariate polynomial $a(X)$ such that its Evaluation form equals $\vec{a}=(a_0, a_1, \ldots, a_{N-1})$, where $a_i = \tilde{f}(\mathsf{bits}(i))$, which is the value of $\tilde{f}$ on the Boolean Hypercube $\{0,1\}^n$.

$$
a(X) = a_0\cdot L_0(X) + a_1\cdot L_1(X) + a_2\cdot L_2(X) + \cdots + a_{N-1}\cdot L_{N-1}(X)
$$

> Prover: In this step, the Prover does not need to derive the coefficient form, but directly uses the evaluation form for computation, which does not involve computational complexity.

2. Prover calculates the commitment $C_a$ of $\hat{f}(X)$ and sends $C_a$

$$
C_{a} = a_0\cdot A_0 + a_1\cdot A_1 + a_2\cdot A_2 + \cdots + a_{N-1}\cdot A_{N-1} = [\hat{f}(\tau)]_1
$$

where $A_0 =[L_0(\tau)]_1, A_1= [L_1(\tau)]_1, A_2=[L_2(\tau)]_1, \ldots, A_{N-1} = [L_{2^{n-1}}(\tau)]_1$ were obtained during the precomputation process.

> Prover: The algorithm complexity is $\mathsf{msm}(N, \mathbb{G}_1)$, representing the commitment of a vector of length $N$.

> #### Commit Phase Complexity
>
> In the commit phase, the total complexity for the prover is:
>
> $$
> \mathsf{msm}(N, \mathbb{G}_1)
> $$

## Evaluation proof protocol

Recall the constraint of the polynomial operation to be proven:

$$
\tilde{f}(u_0, u_1, u_2, \ldots, u_{n-1}) = v
$$

Here $\vec{u}=(u_0, u_1, u_2, \ldots, u_{n-1})$ is a publicly known challenge point.

### Prover Memory

- KZG10 SRS: $A_0 =[L_0(\tau)]_1, A_1= [L_1(\tau)]_1, A_2=[L_2(\tau)]_1, \ldots, A_{N-1} = [L_{2^{n-1}}(\tau)]_1$
- Bary-Centric Weights: $\{\hat{w}_i\}$
- $([z_H(x)|_{x \in gH}])^{-1} = (g^N - 1)^{-1}$
- $\vec{a} = \{a_0, \ldots, a_{N-1}\} = [a(x)|_{x \in H}]$
- $C_a=[\hat{f}(\tau)]_1$
- $\vec{u}=(u_0, u_1, \ldots, u_{n-1})$
- $v=\tilde{f}(u_0,u_1,\ldots, u_{n-1})$
- $\vec{c} = \{c_0, \ldots, c_{N-1}\}$

### Round 1.

Prover:

#### Round 1-1

1. Calculate vector $\vec{c}$, where each element $c_i=\overset{\sim}{eq}(\mathsf{bits}(i), \vec{u})$

##### Prover Cost 1-1

> Prover: 
> 
> The algorithm for calculating vector $\vec{c}$ is:
> 
> ```python
> @classmethod
> def eqs_over_hypercube(cls, rs):
>     k = len(rs)
>     n = 1 << k
>     evals = [Field(1)] * n
>     half = 1
>     for i in range(k):
>         for j in range(half):
>             evals[j+half] = evals[j] * rs[i]
>             evals[j] = evals[j] - evals[j+half]
>         half *= 2
>     return evals
> ```
> For example, when $k = 2$, the calculation result should be:
> 
> $$
> \begin{aligned}
>   00 & \quad (1 - u_0) & (1- u_1)  \\
>   10 & \quad u_0 & (1- u_1) \\
>   01 & \quad (1 - u_0) & u_1 \\
>   11 & \quad u_0 & u_1
> \end{aligned}
> $$
> 
> This algorithm first calculates based on the binary position of $u_0$, and then updates all elements if an additional bit $u_1$ is added.
> 
> - Inside the `for j in range(1)` loop, `evals[1]` and `evals[0]` are calculated:
>   - `evals[1]` = $u_0$, corresponding to the bit position `1` of $u_0$
>   - `evals[0]` = $1 - u_0$, corresponding to the binary bit position `0` of $u_0$
> - Inside `for j in range(2)`, update the position where $u_1$ is located.
>   - `j = 0`, update `evals[0]` and `evals[2]`
>   - `j = 1`, update `evals[1]` and `evals[3]`
> 
> In each loop of `for j in range(half)`, there is 1 multiplication in the finite field, namely `evals[j+half] = evals[j] * rs[i]`, and `half` changes as $1, 2, 2^2, \ldots, 2^{k-1}$, so the total number of finite field multiplications is:
> 
> $$
>   1 + 2 + 2^2 + \ldots + 2^{k - 1} = \frac{1(1 - 2^k)}{1 - 2} = 2^k - 1 = N - 1
> $$
> 
> Therefore, the computational complexity here is $(N - 1) ~ \mathbb{F}_{\mathsf{mul}}$.

##### Prover Memory 1-1

- KZG10 SRS: $A_0 =[L_0(\tau)]_1, A_1= [L_1(\tau)]_1, A_2=[L_2(\tau)]_1, \ldots, A_{N-1} = [L_{2^{n-1}}(\tau)]_1$
- Bary-Centric Weights: $\{\hat{w}_i\}$
- $\vec{a} = \{a_0, \ldots, a_{N-1}\} = [a(x)|_{x \in H}]$
- $C_a=[\hat{f}(\tau)]_1$
- $\vec{u}=(u_0, u_1, \ldots, u_{n-1})$
- $v=\tilde{f}(u_0,u_1,\ldots, u_{n-1})$
- $\vec{c} = \{c_0, \ldots, c_{N-1}\}$

#### Round 1-2

Construct polynomial $c(X)$ such that its evaluation results on $H$ are exactly $\vec{c}$.

$$
c(X) = \sum_{i=0}^{N-1} c_i \cdot L_i(X)
$$

##### Prover Cost 1-2

Prover: This step does not require calculating $c(X)$, the calculation proceeds directly with $\vec{c}$.

#### Round 1-3

Calculate the commitment of $c(X)$ as $C_c= [c(\tau)]_1$, and send $C_c$

$$
C_c = \mathsf{KZG10.Commit}(\vec{c}) = [c(\tau)]_1 
$$

##### Prover Cost 1-3

The commitment calculation method for $C_c$ is:

$$
C_c = c_0 \cdot A_0 + c_1 \cdot A_1 + \ldots + c_{N - 1} \cdot A_{N - 1}
$$

The algorithm complexity here is $\mathsf{msm}(N, \mathbb{G}_1)$

#### Prover Cost Round 1

> 
> Prover complexity is:
>
> $$
> (N - 1) ~ \mathbb{F}_{\mathsf{mul}} + \mathsf{msm}(N, \mathbb{G}_1)
> $$

#### Prover Memory Round 1

- KZG10 SRS: $A_0 =[L_0(\tau)]_1, A_1= [L_1(\tau)]_1, A_2=[L_2(\tau)]_1, \ldots, A_{N-1} = [L_{2^{n-1}}(\tau)]_1$
- Bary-Centric Weights: $\{\hat{w}_i\}$
- $\vec{a} = \{a_0, \ldots, a_{N-1}\} = [a(x)|_{x \in H}]$
- $C_a=[\hat{f}(\tau)]_1$
- $\vec{u}=(u_0, u_1, \ldots, u_{n-1})$
- $v=\tilde{f}(u_0,u_1,\ldots, u_{n-1})$
- $\vec{c} = \{c_0, \ldots, c_{N-1}\}$

### Round 2.

Verifier: Send challenge number $\alpha\leftarrow_{\$}\mathbb{F}_p$

Prover:

#### Round 2-1

Construct constraint polynomials $p_0(X),\ldots, p_{n}(X)$ regarding $\vec{c}$

$$
\begin{split}
p_0(X) &= s_0(X) \cdot \Big( c(X) - (1-u_0)(1-u_1)...(1-u_{n-1}) \Big) \\
p_k(X) &= s_{k-1}(X) \cdot \Big( u_{n-k}\cdot c(X) - (1-u_{n-k})\cdot c(\omega^{2^{n-k}}\cdot X)\Big) , \quad k=1\ldots n
\end{split}
$$

##### Prover Cost 2-1

> 📝 **Note**: First, let's introduce how to quickly perform polynomial multiplication and division in finite fields. Let
> $$
> H' = \{g^0, g^1, \ldots, g^{2N - 1}\} = \langle g \rangle
> $$
>
> Take 
>   
> $$
>H = \langle g^2 \rangle = \langle \omega \rangle = \{\omega^0, \omega^1, \ldots, \omega^{N - 1} \}
> $$
>
> Then
>   
> $$
>gH = \{g\omega^0, g\omega^1, \ldots, g\omega^{N - 1} \} =\{ g^1, g^3, \ldots, g^{2N - 1} \}
> $$
>
> If we want to calculate 
>    
> $$
>a(X) = a_1 + a_2 X + \ldots + a_{N - 1}X^{N - 1}
> $$
>
> and
>   
> $$
>b(X) = b_1 + b_2 X + \ldots + b_{N - 1}X^{N - 1}
> $$
> 
> the product polynomial $c(X) = a(X)\cdot b(X)$. If what we have is the evaluation form of $a(X)$ and $b(X)$ on $H$, i.e.,
>   $$
> [a(x)|_{x \in H}], \quad [b(x)|_{x \in H}]
>$$
> 
> We want to calculate the quotient polynomial
> 
> $$
>q(X) = \frac{a(X) \cdot b(X)}{z_H(X)}
> $$
>
> Since $\deg(q) < N$, storing $q(X)$ can still use the evaluation form. Since $z_H(X)$ is 0 on $H$, we can calculate
>   
> $$
>[(a(x) \cdot b(x))|_{x \in gH}], \quad [z_H(x)|_{x \in gH}]
> $$
>
> Then divide element-wise to calculate $[q(x)|_{x \in gH}]$.
> - Calculate $[a(x))|_{x \in gH}]$: First perform IFFT on $[a(x)|_{x \in H}]$ to get the coefficients of $a(X)$, then perform FFT to calculate its values on $gH$. In actual implementation, this can be done simultaneously, but the complexity should remain unchanged, which is $N \log N ~ \mathbb{F}_{\mathsf{mul}}$, also denoted as $\mathsf{FFT}(N) + \mathsf{IFFT}(N)$.
>- Calculate $[b(x))|_{x \in gH}]$: First perform IFFT on $[b(x)|_{x \in H}]$ to get the coefficients of $b(X)$, then perform FFT to calculate its values on $gH$. The complexity of this step is $\mathsf{FFT}(N) + \mathsf{IFFT}(N)$, which is $N \log N ~ \mathbb{F}_{\mathsf{mul}}$.
> - Calculate $[(a(x) \cdot b(x))|_{x \in gH}]$: Multiply $N$ elements, with complexity $N ~ \mathbb{F}_{\mathsf{mul}}$.
> - Calculate $[z_H(x)|_{x \in gH}]$: Since $z_H(X) = X^N - 1$, we have
> $$
>   z_H(x) = z_H(g\omega^i) = (g\omega^i)^N - 1 = g^N \cdot (\omega^N)^i - 1 = g^N - 1
> $$
> The value of $z_H(X)$ on $gH$ is always a constant, so its inverse $(g^N - 1)^{-1}$ can be precalculated. This step does not involve Prover's complexity.
> - Calculate $[q(x)|_{x \in gH}]$: Multiply each value in $[(a(x) \cdot b(x))|_{x \in gH}]$ by $(g^N - 1)^{-1}$ to get $[q(x)|_{x \in gH}]$, with complexity $N ~ \mathbb{F}_{\mathsf{mul}}$.
> 
> Therefore, the overall complexity for calculating the division is
> 
> $$
> 2~ \mathsf{FFT}(N) + 2~\mathsf{IFFT}(N) + 2N ~ \mathbb{F}_{\mathsf{mul}}
> $$

Now analyzing the algorithm complexity. The Prover needs to calculate $[p_i(x)|_{x \in gH}]$ to facilitate the subsequent calculation of the quotient polynomial's evaluation form.

1. Prover calculates $[s_0(x)|_{x \in gH}], [s_1(x)|_{x \in gH}], \ldots, [s_{n - 1}(x)|_{x \in gH}]$. The values of $s_0(x), \ldots, s_{n - 1}(x)$ at any point can be obtained using an $O(n)$ algorithm, as shown in Round 3, with complexity $(n - 1) ~ \mathbb{F}_{\mathsf{mul}}$. Since $|gH| = N$, the complexity to obtain all values on $gH$ is $(n - 1)N ~ \mathbb{F}_{\mathsf{mul}}$.
2. Calculate $[c(x)|_{x \in gH}]$ by first using IFFT on $[c(x)|_{x \in H}]$ to get its coefficients, then using FFT to find its values on $gH$, with complexity $\mathsf{FFT}(N) + \mathsf{IFFT}(N)$.
3. Calculate $[(c(x) - (1 - u_0)(1 - u_1) \ldots (1 - u_{n - 1}))|_{x \in gH}]$: $(1 - u_0)(1 - u_1) \ldots (1 - u_{n - 1})$ is actually $c_0$, and we can directly subtract for calculation.
4. Calculate $[p_0(x)|_{x \in gH}]$, involving $N$ multiplications, with complexity $N ~ \mathbb{F}_{\mathsf{mul}}$.
5. For $k = 1, \ldots, n$, calculate $[( u_{n-k}\cdot c(x) - (1-u_{n-k})\cdot c(\omega^{2^{n-k}}\cdot x))|_{x \in gH}]$: For each $k$ and $x \in gH$, each calculation involves 2 finite field multiplications, so the complexity to calculate all values for all $k$ is $2nN ~ \mathbb{F}_{\mathsf{mul}}$.
6. For $k = 1, \ldots, n$, calculate $[p_k(x)|_{x \in gH}]$, for each $k$, involving $N$ multiplications, so the total complexity is $nN ~ \mathbb{F}_{\mathsf{mul}}$.

In summary, the total complexity for this step is:

$$
\begin{aligned}
  & (n - 1)N ~ \mathbb{F}_{\mathsf{mul}} + \mathsf{FFT}(N) + \mathsf{IFFT}(N) + N ~ \mathbb{F}_{\mathsf{mul}} + 3nN ~ \mathbb{F}_{\mathsf{mul}} \\
  = & \mathsf{FFT}(N) + \mathsf{IFFT}(N) + 4nN ~ \mathbb{F}_{\mathsf{mul}}
\end{aligned}
$$

##### Prover Memory 2-1

- KZG10 SRS: $A_0 =[L_0(\tau)]_1, A_1= [L_1(\tau)]_1, A_2=[L_2(\tau)]_1, \ldots, A_{N-1} = [L_{2^{n-1}}(\tau)]_1$
- Bary-Centric Weights: $\{\hat{w}_i\}$
- $\vec{a} = \{a_0, \ldots, a_{N-1}\} = [a(x)|_{x \in H}]$
- $C_a=[\hat{f}(\tau)]_1$
- $\vec{u}=(u_0, u_1, \ldots, u_{n-1})$
- $v=\tilde{f}(u_0,u_1,\ldots, u_{n-1})$
- $\vec{c} = \{c_0, \ldots, c_{N-1}\} = [c(x)|_{x \in H}]$
- Coefficients of $c(X)$
- $[c(x)|_{x \in gH}]$
- $\{[p_k(x)|_{x \in gH}]\}_{k = 0}^n$

#### Round 2-2

Aggregate $\{p_i(X)\}$ into a single polynomial $p(X)$

$$
p(X) = p_0(X) + \alpha\cdot p_1(X) + \alpha^2\cdot p_2(X) + \cdots + \alpha^{n}\cdot p_{n}(X)
$$

##### Prover Cost 2-2

This step actually calculates $[p(x)|_{x \in gH}]$ rather than the polynomial coefficients.

1. The prover calculates $\alpha^2, \alpha^3, \ldots, \alpha^n$ from $\alpha$, involving a total of $n - 1$ multiplications in the finite field, so the complexity is $(n - 1) ~ \mathbb{F}_{\mathsf{mul}}$.
2. For each $x \in gH$, directly calculate

$$
p(x) = p_0(x) + \alpha\cdot p_1(x) + \alpha^2\cdot p_2(x) + \cdots + \alpha^{n}\cdot p_{n}(x)
$$

This involves $n$ finite field multiplications, and with a total of $|gH| = N$ values of $x$, the complexity is $nN ~ \mathbb{F}_{\mathsf{mul}}$.

In summary, the complexity for this step is:

$$
(nN + n - 1) ~ \mathbb{F}_{\mathsf{mul}}
$$

##### Prover Memory 2-2

- KZG10 SRS: $A_0 =[L_0(\tau)]_1, A_1= [L_1(\tau)]_1, A_2=[L_2(\tau)]_1, \ldots, A_{N-1} = [L_{2^{n-1}}(\tau)]_1$
- Bary-Centric Weights: $\{\hat{w}_i\}$
- $\vec{a} = \{a_0, \ldots, a_{N-1}\} = [a(x)|_{x \in H}]$
- $C_a=[\hat{f}(\tau)]_1$
- $\vec{u}=(u_0, u_1, \ldots, u_{n-1})$
- $v=\tilde{f}(u_0,u_1,\ldots, u_{n-1})$
- $\vec{c} = \{c_0, \ldots, c_{N-1}\} = [c(x)|_{x \in H}]$
- $[c(x)|_{x \in gH}]$
- $[p(x)|_{x \in gH}]$

#### Round 2-3

Construct accumulator polynomial $z(X)$ that satisfies:

$$
\begin{split}
z(1) &= a_0\cdot c_0 \\
z(\omega_{i}) - z(\omega_{i-1}) &= a(\omega_{i})\cdot c(\omega_{i}), \quad i=1,\ldots, N-1 \\ 
z(\omega^{N-1}) &= v \\
\end{split}
$$

##### Prover Cost 2-3

Having already obtained $[a(x)|_{x \in H}]$ and $[c(x)|_{x \in H}]$, calculating $[z(x)|_{x \in H}]$ is straightforward.

$$
\begin{aligned}
  & z(1) = a_0 \cdot c_0 \\
  & z(\omega_1) = z(1) + a(\omega_1) \cdot c(\omega_1) \\
  & \cdots \\
  & z(\omega_{N - 1}) = z(\omega_{N - 2}) + a(\omega_{N - 1}) \cdot c(\omega_{N - 1}) \\
  & z(\omega^{N - 1}) = v
\end{aligned}
$$

The complexity involved is $N ~ \mathbb{F}_{\mathsf{mul}}$.

##### Prover Memory 2-3

- KZG10 SRS: $A_0 =[L_0(\tau)]_1, A_1= [L_1(\tau)]_1, A_2=[L_2(\tau)]_1, \ldots, A_{N-1} = [L_{2^{n-1}}(\tau)]_1$
- Bary-Centric Weights: $\{\hat{w}_i\}$
- $([z_H(x)|_{x \in gH}])^{-1} = (g^N - 1)^{-1}$
- $[L_0(x)|_{x \in gH}]$
- $[L_{N - 1}(x)|_{x \in gH}]$
- $\vec{a} = \{a_0, \ldots, a_{N-1}\} = [a(x)|_{x \in H}]$
- $C_a=[\hat{f}(\tau)]_1$
- $\vec{u}=(u_0, u_1, \ldots, u_{n-1})$
- $v=\tilde{f}(u_0,u_1,\ldots, u_{n-1})$
- $\vec{c} = \{c_0, \ldots, c_{N-1}\} = [c(x)|_{x \in H}]$
- $[c(x)|_{x \in gH}]$
- $[p(x)|_{x \in gH}]$
- $[z(x)|_{x \in H}]$

#### Round 2-4

Construct constraint polynomials $h_0(X), h_1(X), h_2(X)$ that satisfy:

$$
\begin{split}
h_0(X) &= L_0(X)\cdot\big(z(X) - c_0\cdot a(X) \big) \\
h_1(X) &= (X-1)\cdot\big(z(X)-z(\omega^{-1}\cdot X)-a(X)\cdot c(X)) \\
h_2(X) & = L_{N-1}(X)\cdot\big( z(X) - v \big) \\
\end{split}
$$

##### Prover Cost 2-4

To calculate $[h_0(x)|_{x \in gH}], [h_1(x)|_{x \in gH}], [h_2(x)|_{x \in gH}]$:
- First calculate $[z(x)|_{x \in gH}]$, with complexity $\mathsf{FFT}(N) + \mathsf{IFFT}(N)$.
- Calculate $[a(x)|_{x \in gH}]$, with complexity $\mathsf{FFT}(N) + \mathsf{IFFT}(N)$.
- Calculate $[h_0(x)|_{x \in gH}]$, with complexity $2N ~ \mathbb{F}_{\mathsf{mul}}$
- Calculate $[(a(x) \cdot c(x))|_{x \in gH}]$, with complexity $N ~ \mathbb{F}_{\mathsf{mul}}$.
- Calculate $[h_1(x)|_{x \in gH}]$, with complexity $N ~ \mathbb{F}_{\mathsf{mul}}$
- Calculate $[h_2(x)|_{x \in gH}]$, with complexity $N ~ \mathbb{F}_{\mathsf{mul}}$

The total complexity for this step is:

$$
2~ \mathsf{FFT}(N) + 2~ \mathsf{IFFT}(N) + 5N ~ \mathbb{F}_{\mathsf{mul}}
$$

##### Prover Memory 2-4

This round adds $[h_0(x)|_{x \in gH}], [h_1(x)|_{x \in gH}], [h_2(x)|_{x \in gH}]$.

- KZG10 SRS: $A_0 =[L_0(\tau)]_1, A_1= [L_1(\tau)]_1, A_2=[L_2(\tau)]_1, \ldots, A_{N-1} = [L_{2^{n-1}}(\tau)]_1$
- Bary-Centric Weights: $\{\hat{w}_i\}$
- $([z_H(x)|_{x \in gH}])^{-1} = (g^N - 1)^{-1}$
- $[L_0(x)|_{x \in gH}]$
- $[L_{N - 1}(x)|_{x \in gH}]$
- $\vec{a} = \{a_0, \ldots, a_{N-1}\} = [a(x)|_{x \in H}]$
- $C_a=[\hat{f}(\tau)]_1$
- $\vec{u}=(u_0, u_1, \ldots, u_{n-1})$
- $v=\tilde{f}(u_0,u_1,\ldots, u_{n-1})$
- $\vec{c} = \{c_0, \ldots, c_{N-1}\} = [c(x)|_{x \in H}]$
- $[c(x)|_{x \in gH}]$
- $[p(x)|_{x \in gH}]$
- $[z(x)|_{x \in H}]$
- Coefficients of $z(X)$ (Round 2-4)
- $[h_0(x)|_{x \in gH}], [h_1(x)|_{x \in gH}], [h_2(x)|_{x \in gH}]$

#### Round 2-5

Aggregate $p(X)$ and $h_0(X), h_1(X), h_2(X)$ into a single polynomial $h(X)$ such that:

$$
\begin{split}
h(X) &= p(X) + \alpha^{n+1} \cdot h_0(X) + \alpha^{n+2} \cdot h_1(X) + \alpha^{n+3} \cdot h_2(X)
\end{split}
$$

##### Prover Cost 2-5

This round calculates $[h(x)_{x \in gH}]$.
- In the previous steps of this round, $\alpha^2, \ldots, \alpha^n$ have already been calculated. Now to calculate $\alpha^{n + 1}, \alpha^{n + 2}, \alpha^{n + 3}$, this involves 3 multiplications in the finite field, so the complexity is $3 ~ \mathbb{F}_{\mathsf{mul}}$.
- Calculate $[h(x)|_{gH}]$, with complexity $3N ~ \mathbb{F}_{\mathsf{mul}}$
The total complexity for this round is:
$$
(3N + 3) ~ \mathbb{F}_{\mathsf{mul}}
$$

##### Prover Memory 2-5

- KZG10 SRS: $A_0 =[L_0(\tau)]_1, A_1= [L_1(\tau)]_1, A_2=[L_2(\tau)]_1, \ldots, A_{N-1} = [L_{2^{n-1}}(\tau)]_1$
- Bary-Centric Weights: $\{\hat{w}_i\}$
- $([v_H(x)|_{x \in gH}])^{-1} = (g^N - 1)^{-1}$
- $[L_0(x)|_{x \in gH}]$
- $[L_{N - 1}(x)|_{x \in gH}]$
- $\vec{a} = \{a_0, \ldots, a_{N-1}\} = [a(x)|_{x \in H}]$
- $C_a=[\hat{f}(\tau)]_1$
- $\vec{u}=(u_0, u_1, \ldots, u_{n-1})$
- $v=\tilde{f}(u_0,u_1,\ldots, u_{n-1})$
- $\vec{c} = \{c_0, \ldots, c_{N-1}\} = [c(x)|_{x \in H}]$
- $[c(x)|_{x \in gH}]$
- $[p(x)|_{x \in gH}]$
- $[z(x)|_{x \in H}]$
- $[h_0(x)|_{x \in gH}], [h_1(x)|_{x \in gH}], [h_2(x)|_{x \in gH}]$
- $[h(x)|_{x \in gH}]$

#### Round 2-6

Calculate the Quotient polynomial $t(X)$ such that:

$$
h(X) =t(X)\cdot v_H(X)
$$

##### Prover Cost 2-6

Calculate $[t(x)|_{x \in gH}]$ for all $x \in gH$:

$$
t(x) = h(x) \cdot (v_H(x))^{-1} = h(x) \cdot (g^N - 1)^{-1}
$$

The complexity is $N ~ \mathbb{F}_{\mathsf{mul}}$.

##### Prover Memory 2-6

- KZG10 SRS: $A_0 =[L_0(\tau)]_1, A_1= [L_1(\tau)]_1, A_2=[L_2(\tau)]_1, \ldots, A_{N-1} = [L_{2^{n-1}}(\tau)]_1$
- Bary-Centric Weights: $\{\hat{w}_i\}$
- $([v_H(x)|_{x \in gH}])^{-1} = (g^N - 1)^{-1}$
- $[L_0(x)|_{x \in gH}]$
- $[L_{N - 1}(x)|_{x \in gH}]$
- $\vec{a} = \{a_0, \ldots, a_{N-1}\} = [a(x)|_{x \in H}]$
- $C_a=[\hat{f}(\tau)]_1$
- $\vec{u}=(u_0, u_1, \ldots, u_{n-1})$
- $v=\tilde{f}(u_0,u_1,\ldots, u_{n-1})$
- $\vec{c} = \{c_0, \ldots, c_{N-1}\} = [c(x)|_{x \in H}]$
- $[c(x)|_{x \in gH}]$
- $[p(x)|_{x \in gH}]$
- $[z(x)|_{x \in H}]$
- $[t(x)|_{x \in gH}]$

#### Round 2-7

Calculate $C_t=[t(\tau)]_1$, $C_z=[z(\tau)]_1$, and send $C_t$ and $C_z$

$$
\begin{split}
C_t &= \mathsf{KZG10.Commit}(t(X)) = [t(\tau)]_1 \\
C_z &= \mathsf{KZG10.Commit}(z(X)) = [z(\tau)]_1
\end{split}
$$

##### Prover Cost 2-7

Calculate $C_t$:

- From $[t(x)|_{x \in gH}]$ calculate $[t(x)|_{x \in H}]$, with complexity $\mathsf{FFT}(N) + \mathsf{IFFT}(N)$,
- Calculate

$$
C_t = t_0 A_0 + \ldots + t_{N - 1}A_{N - 1}
$$

with complexity $\mathsf{msm}(N, \mathbb{G}_1)$

Calculate $C_z$: $\mathsf{msm}(N, \mathbb{G}_1)$

Therefore, the total complexity for this step is:
$$
\mathsf{FFT}(N) + \mathsf{IFFT}(N) + 2 ~ \mathsf{msm}(N, \mathbb{G}_1)
$$

> 💡 **Option**
>
> If memory constraints are not a concern, another set of KZG10 SRS can be stored in memory in advance: $B_0 =[L'_0(\tau)]_1, B_1= [L'_1(\tau)]_1, B_2=[L'_2(\tau)]_1, \ldots, B_{N-1} = [L'_{2^{n} - 1}(\tau)]_1$, where $L_0', \ldots, L_{N - 1}'$ are the Lagrange interpolation polynomials on $gH$.
>
> - Calculate $C_t$:
>   $$
>   C_t = t_0 B_0 + \ldots + t_{N - 1}B_{N - 1}
>   $$
>   where $[t_0, \ldots, t_{N-1}]$ is $[t(x)|_{x \in gH}]$. The complexity for this step would be $\mathsf{msm}(N, \mathbb{G}_1)$.
>
> - Calculate $C_z$: $\mathsf{msm}(N, \mathbb{G}_1)$
>
> Total complexity would be:
> $$
> 2 ~ \mathsf{msm}(N, \mathbb{G}_1)
> $$
> This approach would save one FFT and one IFFT, reducing the computation by $N \log N ~ \mathbb{F}_{\mathsf{mul}}$.

### Prover Cost Round 2

Summarizing the Prover computational complexity for all steps above:

$$
\begin{aligned}
& \mathsf{FFT}(N) + \mathsf{IFFT}(N) + 4nN ~ \mathbb{F}_{\mathsf{mul}} + (nN + n - 1) ~ \mathbb{F}_{\mathsf{mul}} + N ~ \mathbb{F}_{\mathsf{mul}} + 2~ \mathsf{FFT}(N) + 2~ \mathsf{IFFT}(N) + 5N ~ \mathbb{F}_{\mathsf{mul}} \\
& + (3N + 3) ~ \mathbb{F}_{\mathsf{mul}} + N ~ \mathbb{F}_{\mathsf{mul}} + \mathsf{FFT}(N) + \mathsf{IFFT}(N) + 2 ~ \mathsf{msm}(N, \mathbb{G}_1) \\
= & 4 ~ \mathsf{FFT}(N) + 4 ~ \mathsf{IFFT}(N) + (5nN + 10N + n + 2) ~ \mathbb{F}_{\mathsf{mul}} + 2 ~ \mathsf{msm}(N, \mathbb{G}_1)
\end{aligned}
$$

### Round 3.

Verifier: Send random evaluation point $\zeta\leftarrow_{\$}\mathbb{F}_p$

Prover:

#### Round 3-1

1. Calculate the values of $s_i(X)$ at point $\zeta$:

$$
s_0(\zeta), s_1(\zeta), \ldots, s_{n-1}(\zeta)
$$

##### Prover Cost 3-1

Here the Prover can efficiently calculate $s_i(\zeta)$. From the formula for $s_i(X)$ we get:
$$
\begin{aligned}
  s_i(\zeta) & = \frac{\zeta^N - 1}{\zeta^{2^i} - 1} \\
  & = \frac{(\zeta^N - 1)(\zeta^{2^i} +1)}{(\zeta^{2^i} - 1)(\zeta^{2^i} +1)} \\
  & = \frac{\zeta^N - 1}{\zeta^{2^{i + 1}} - 1} \cdot (\zeta^{2^i} +1) \\
  & = s_{i + 1}(\zeta) \cdot (\zeta^{2^i} +1)
\end{aligned} 
$$

Thus the value of $s_i(\zeta)$ can be calculated from $s_{i + 1}(\zeta)$, and

$$
s_{n-1}(\zeta) = \frac{\zeta^N - 1}{\zeta^{2^{n-1}} - 1} = \zeta^{2^{n-1}} + 1
$$

This gives us an $O(n)$ algorithm to calculate $s_i(\zeta)$, which does not involve division operations. The calculation process is: $s_{n-1}(\zeta) \rightarrow s_{n-2}(\zeta) \rightarrow \cdots \rightarrow s_0(\zeta)$.

> - First calculate $\zeta^2, \zeta^4, \ldots, \zeta^{2^{n - 1}}$ from the random number $\zeta$. This requires one finite field multiplication for $\zeta^2 = \zeta \times \zeta$, then one more for $\zeta^4 = \zeta^2 \times \zeta^2$, and so on, each requiring one finite field multiplication. In total, this involves $n - 1$ finite field multiplications, with complexity $(n - 1) ~ \mathbb{F}_{\mathsf{mul}}$.
> - Calculate $s_{n-1}(\zeta) = \zeta^{2^{n-1}} + 1$, which only involves addition in the finite field and is not counted in the complexity.
> - Calculate $s_{i}(\zeta)$ (for $i = 0, \ldots, n - 2$), where $s_{i}(\zeta) = s_{i + 1}(\zeta) \cdot (\zeta^{2^i} +1)$ requires one finite field multiplication, so the operation needed is $\mathbb{F}_{\mathsf{mul}}$. For all $i = 0, \ldots, n - 2$, the total complexity is $(n - 1) ~ \mathbb{F}_{\mathsf{mul}}$.
> 
> Therefore, the total complexity is:
> 
> $$
>   (n - 1) ~ \mathbb{F}_{\mathsf{mul}} + (n - 1) ~ \mathbb{F}_{\mathsf{mul}} = 2(n - 1) ~ \mathbb{F}_{\mathsf{mul}}
> $$

#### Round 3-2

Define the evaluation Domain $D'$ containing $n+1$ elements:

$$
D'=D\zeta = \{\zeta, \omega\zeta, \omega^2\zeta,\omega^4\zeta, \ldots, \omega^{2^{n-1}}\zeta\}
$$

#### Round 3-3

Calculate and send the values of $c(X)$ on $D'$:

$$
c(\zeta), c(\zeta\cdot\omega), c(\zeta\cdot\omega^2), c(\zeta\cdot\omega^4), \ldots, c(\zeta\cdot\omega^{2^{n-1}})
$$

##### Prover Cost 3-3

- The values $(1, \omega, \omega^2, \ldots, \omega^{2^{n - 1}})$ can be precomputed, so calculating the points $(\zeta, \zeta \cdot \omega, \zeta \cdot \omega^2, \ldots, \zeta \cdot \omega^{2^{n - 1}})$ involves $n$ finite field multiplications, with complexity $n ~\mathbb{F}_{\mathsf{mul}}$.
- To calculate $[c(x)|_{x \in D'}]$, in Round 2-1 we obtained the coefficients of $c(X)$. Using the FFT method, we can find $[c(x)|_{x \in D^{(2)}}]$ in a subgroup $D' \subset D^{(2)}$ of size $N$, where $|D'| = n, |D^{(2)}| = N$. This naturally gives us $[c(x)|_{x \in D'}]$, with complexity $\mathsf{FFT}(N)$.

> 💡 Since we've calculated many more values than needed (only values on $D'$ are required, but we calculated values on $D^{(2)}$), there's room for optimization:
> - [ ] Calculating on the D' sub-tree has complexity $n\log^2n$
> - [ ] Is there an optimized algorithm?

The complexity for this step is:

$$
n ~\mathbb{F}_{\mathsf{mul}} + \mathsf{FFT}(N)
$$

#### Round 3-4

Calculate and send $z(\omega^{-1}\cdot\zeta)$

##### Prover Cost 3-4

In Round 2-4, the coefficients of $z(X)$ were already calculated, so we can directly use these to find the value of $z(X)$ at a specific point.

> Prover:
>
> Computing $\omega^{-1}\cdot\zeta$ has complexity $\mathbb{F}_{\mathsf{mul}}$, and computing $z(\omega^{-1}\cdot\zeta)$ has complexity $N ~\mathbb{F}_{\mathsf{mul}}$, giving a total complexity of:
>
> $$
>   (N + 1) ~ \mathbb{F}_{\mathsf{mul}}
> $$

##### Prover Memory 3-4

- KZG10 SRS: $A_0 =[L_0(\tau)]_1, A_1= [L_1(\tau)]_1, A_2=[L_2(\tau)]_1, \ldots, A_{N-1} = [L_{2^{n-1}}(\tau)]_1$
- Bary-Centric Weights: $\{\hat{w}_i\}$
- $([v_H(x)|_{x \in gH}])^{-1} = (g^N - 1)^{-1}$
- $[L_0(x)|_{x \in gH}]$
- $[L_{N - 1}(x)|_{x \in gH}]$
- Coefficients of $L_0(X)$ and $L_{N - 1}(X)$
- $\omega^{-1}$ (Precomputed)
- $\vec{a} = \{a_0, \ldots, a_{N-1}\} = [a(x)|_{x \in H}]$
- $C_a=[\hat{f}(\tau)]_1$
- $\vec{u}=(u_0, u_1, \ldots, u_{n-1})$
- $v=\tilde{f}(u_0,u_1,\ldots, u_{n-1})$
- $\vec{c} = \{c_0, \ldots, c_{N-1}\} = [c(x)|_{x \in H}]$
- $[c(x)|_{x \in gH}]$
- $[p(x)|_{x \in gH}]$
- $[z(x)|_{x \in H}]$
- $[z(x)|_{x \in gH}]$
- $[t(x)|_{x \in gH}]$
- Coefficients of $c(X)$
- Coefficients of $z(X)$
- $c(\zeta), c(\zeta\cdot\omega), c(\zeta\cdot\omega^2), c(\zeta\cdot\omega^4), \ldots, c(\zeta\cdot\omega^{2^{n-1}})$
- $s_0(\zeta), s_1(\zeta), \ldots, s_{n-1}(\zeta)$
- $z(\omega^{-1}\cdot\zeta)$
- $\alpha, \alpha^2, \ldots, \alpha^{n + 3}$ (Round 2-5)

#### Round 3-5

Calculate the Linearized Polynomial $l_\zeta(X)$:

$$
\begin{split}
l_\zeta(X) =& \Big(s_0(\zeta) \cdot (c(\zeta) - c_0) \\
& + \alpha\cdot s_0(\zeta) \cdot (u_{n-1}\cdot c(\zeta) - (1-u_{n-1})\cdot c(\omega^{2^{n-1}}\cdot\zeta))\\
  & + \alpha^2\cdot s_1(\zeta) \cdot (u_{n-2}\cdot c(\zeta) - (1-u_{n-2})\cdot c(\omega^{2^{n-2}}\cdot\zeta)) \\
  & + \cdots \\
  & + \alpha^{n-1}\cdot s_{n-2}(\zeta)\cdot (u_{1}\cdot c(\zeta) - (1-u_{1})\cdot c(\omega^2\cdot\zeta))\\
  & + \alpha^n\cdot s_{n-1}(\zeta)\cdot (u_{0}\cdot c(\zeta) - (1-u_{0})\cdot c(\omega\cdot\zeta)) \\
  & + \alpha^{n+1}\cdot (L_0(\zeta)\cdot\big(z(X) - c_0\cdot a(X))\\
  & + \alpha^{n+2}\cdot (\zeta - 1)\cdot\big(z(X)-z(\omega^{-1}\cdot\zeta)-c(\zeta)\cdot a(X) ) \\
  & + \alpha^{n+3}\cdot L_{N-1}(\zeta)\cdot(z(X) - v) \\
  & - v_H(\zeta)\cdot t(X)\ \Big)
\end{split}
$$

Clearly, $l_\zeta(\zeta)= 0$, so this evaluation value does not need to be sent to the Verifier, and $[l_\zeta(\tau)]_1$ can be constructed by the Verifier themselves.

##### Prover Cost 3-5

Calculate $[l_{\zeta}(x)|_{x \in H}]$.

- $L_0(\zeta)$ and $L_{N - 1}(\zeta)$: The coefficients of $L_0(X)$ and $L_{N - 1}(X)$ can be precomputed, so calculating $L_0(\zeta)$ and $L_{N - 1}(\zeta)$ has complexity $2N ~\mathbb{F}_{\mathsf{mul}}$.
- $s_0(\zeta) \cdot (c(\zeta) - c_0)$ involves one finite field multiplication, with complexity $\mathbb{F}_{\mathsf{mul}}$
- $\alpha \cdot s_0(\zeta) \cdot (u_{n-1}\cdot c(\zeta) - (1-u_{n-1})\cdot c(\omega^{2^{n-1}}\cdot\zeta))$ has complexity $4 ~ \mathbb{F}_{\mathsf{mul}}$. This is similar for terms 2 through $n+1$, so the complexity is $4n ~ \mathbb{F}_{\mathsf{mul}}$
- For $x \in H$, calculate $[\alpha^{n+1}\cdot L_0(\zeta)\cdot\big(z(x) - c_0\cdot a(x))\big)]$. Each term involves 3 finite field multiplications, so the total complexity is $3N ~ \mathbb{F}_{\mathsf{mul}}$.
- For $x \in H$, calculate $[\alpha^{n+2}\cdot (\zeta - 1)\cdot\big(z(x)-z(\omega^{-1}\cdot\zeta)-c(\zeta)\cdot a(x)]$. Computing $\omega^{-1}\cdot\zeta$ involves one finite field multiplication, and for each $x$ involves 3 finite field multiplications, so the total complexity is $(3N + 1) ~ \mathbb{F}_{\mathsf{mul}}$.
- For $x \in H$, calculate $[\alpha^{n+3}\cdot L_{N-1}(\zeta)\cdot(z(x) - v)]$. Each calculation involves 2 finite field multiplications, with complexity $2N ~ \mathbb{F}_{\mathsf{mul}}$.
- Calculate $v_H(\zeta)$, with complexity $N ~ \mathbb{F}_{\mathsf{mul}}$.
- For $x \in H$, calculate $[v_H(\zeta)\cdot t(x)]$, with complexity $N ~ \mathbb{F}_{\mathsf{mul}}$.

The total complexity for this step is:

$$
(12N + 4n + 2) ~ \mathbb{F}_{\mathsf{mul}}
$$

#### Round 3-6

Construct polynomial $c^*(X)$, which is the interpolation polynomial of the following vector on $D\zeta$:

$$
\vec{c^*} = \Big(c(\omega\cdot\zeta), c(\omega^2\cdot\zeta), c(\omega^4\cdot\zeta), \ldots, c(\omega^{2^{n-1}}\cdot\zeta), c(\zeta)\Big)
$$

Prover can use the precomputed Bary-Centric Weights $\{\hat{w}_i\}$ on $D$ to quickly calculate $c^*(X)$:

$$
c^*(X) = \frac{c^*_0 \cdot \frac{\hat{w}_0}{X-\omega\zeta} + c^*_1 \cdot \frac{\hat{w}_1}{X-\omega^{2}\zeta} + \cdots + c^*_n \cdot \frac{\hat{w}_n}{X-\omega^{2^n}\zeta}}{
   \frac{\hat{w}_0}{X-\omega\zeta} + \frac{\hat{w}_1}{X-\omega^2\zeta} + \cdots + \frac{\hat{w}_n}{X-\omega^{2^n}\zeta}
  }
$$

Here $\hat{w}_j$ are precomputed values:

$$
\hat{w}_j = \prod_{l\neq j} \frac{1}{\omega^{2^j} - \omega^{2^l}}
$$

##### Prover Cost 3-6

> 📝 Notes
> - The coefficients of $c(X)$ have already been calculated
> - [ ] Here $c(X)$ is calculated to get the coefficient form, then $\vec{c^*}$ is obtained
> - [ ] Here we obtain the coefficient form of $c^*(X)$
> - [ ] product fast interpolation
> - [ ] Computing $c^*(X)$ has complexity $(n + 1) \log^2(n + 1)$

> 📝 Previous analysis process:
>
>   Prover:
> 
> - $\vec{c^*}$ and the values of $\omega^{2^i}\zeta$ have already been calculated in step 3 of this round.
> - Calculate $\frac{\hat{w}_i}{X-\omega^{2^i}\zeta}$. The numerator is a constant, the denominator is a first-degree polynomial, so the complexity is denoted as $\mathsf{polydiv}(0, 1)$, and the result is a fraction.
> - Calculate $c_i^* \cdot \frac{\hat{w}_i}{X-\omega^{2^i}\zeta}$, where the complexity is denoted as $\mathsf{polymul}(0, -1)$.
> - Finally, calculate $c^*(X)$. After bringing to a common denominator, both the numerator and denominator are polynomials of degree $n$, so the complexity of their division is denoted as $\mathsf{polydiv}(n, n)$, and the resulting $c^*(X)$ is also of degree $n$.
> 
> Polynomial addition only involves addition in the finite field, which is not counted, so the complexity for this step $c^*(X)$ is: 
>  
> $$
>  n ~ \mathsf{polymul}(0, -1) + n ~\mathsf{polydiv}(0, 1) + \mathsf{polydiv}(n, n) 
> $$

Complexity is:

$$
(n + 1) \log^2(n + 1) ~ \mathbb{F}_{\mathsf{mul}}
$$

#### Round 3-7

Since $l_\zeta(\zeta)= 0$, there exists a Quotient polynomial $q_\zeta(X)$ such that:

$$
q_\zeta(X) = \frac{1}{X-\zeta}\cdot l_\zeta(X)
$$

##### Prover Cost 3-7

> This step's calculation uses the algorithm below, with code:
> 
> ```python
> def division_by_linear_divisor(self, d):
>     """
>     Divide a polynomial by a linear divisor (X - d) using Ruffini's rule.
> 
>     Args:
>         coeffs (list): Coefficients of the polynomial, from lowest to highest degree.
>         d (Scalar): The constant term of the linear divisor.
> 
>     Returns:
>         tuple: (quotient coefficients, remainder)
>     """
>     assert len(self.coeffs) > 0, "Polynomial degree must be at least 1"
> 
>     n = len(self.coeffs)
>     quotient = [0] * (n - 1)
>     
>     # Start with the highest degree coefficient
>     current = self.coeffs[-1]
>     
>     # Iterate through coefficients from second-highest to lowest degree
>     for i in range(n - 2, -1, -1):
>         # Store the current value in the quotient
>         quotient[i] = current
>         
>         # Compute the next value
>         current = current * d + self.coeffs[i]
>     
>     # The final current value is the remainder
>     remainder = current
> 
>     return UniPolynomial(quotient), remainder
> ```
> 
> For an $n$-degree polynomial 
> 
> $$
> f(X) = f_0 + f_1 X + f_2 X^2 + \cdots + f_{n-1} X^{n-1} + f_n X^n
> $$
> 
> divided by a linear polynomial $X - d$, to find its quotient polynomial and remainder, i.e., satisfying $f(X) = q(X)(X - d) + r(X)$, we can decompose as follows:
> 
> $$
> \begin{aligned}
>   & f_0 + f_1 X + f_2 X^2 + \cdots + f_{n-1} X^{n-1} + f_n X^n  \\
>   = & (X -  d)(f_n \cdot X^{n - 1}) + d \cdot f_n \cdot X^{n - 1} + f_{n - 1} X^{n - 1} + \cdots + f_1 X + f_0 \\
>   = & (X -  d)(f_n \cdot X^{n - 1}) + (X - d)((df_n + f_{n - 1}) \cdot X^{n - 2}) \\
>   & + d \cdot (df_n + f_{n - 1}) + f_{n - 2} X^{n - 2} + \cdots + f_1 X + f_0 \\
> \end{aligned}
> $$
> 
> From the above equation, we find:
> 
> $$
> \begin{aligned}
>   & q_{n - 1} = f_n \\
>   & q_i = d \cdot q_{i + 1} + f_{i + 1} , \quad i = n - 2, \ldots, 0 \\
> \end{aligned}
> $$
> 
> So the final remainder is:
> 
> $$
> r(X) = d \cdot q_0 + f_0
> $$
> 
> Here $i$ runs from $n - 2, \ldots, 0$, each involving one finite field multiplication, and calculating $r(X)$ also involves one multiplication, so the complexity is $n ~ \mathbb{F}_{\mathsf{mul}}$.
> 
> Coming back to analyzing the complexity of calculating $q_\zeta(X)$, we need to analyze the degree of $l_\zeta(X)$.
> 
> $$
> \begin{split}
> l_\zeta(X) =& \Big(s_0(\zeta) \cdot (c(\zeta) - c_0) \\
> & + \alpha\cdot s_0(\zeta) \cdot (u_{n-1}\cdot c(\zeta) - (1-u_{n-1})\cdot c(\omega^{2^{n-1}}\cdot\zeta))\\
>   & + \alpha^2\cdot s_1(\zeta) \cdot (u_{n-2}\cdot c(\zeta) - (1-u_{n-2})\cdot c(\omega^{2^{n-2}}\cdot\zeta)) \\
>   & + \cdots \\
>   & + \alpha^{n-1}\cdot s_{n-2}(\zeta)\cdot (u_{1}\cdot c(\zeta) - (1-u_{1})\cdot c(\omega^2\cdot\zeta))\\
>   & + \alpha^n\cdot s_{n-1}(\zeta)\cdot (u_{0}\cdot c(\zeta) - (1-u_{0})\cdot c(\omega\cdot\zeta)) \\
>   & + \alpha^{n+1}\cdot (L_0(\zeta)\cdot\big(z(X) - c_0\cdot a(X))\\
>   & + \alpha^{n+2}\cdot (\zeta - 1)\cdot\big(z(X)-z(\omega^{-1}\cdot\zeta)-c(\zeta)\cdot a(X) \big) \\
>   & + \alpha^{n+3}\cdot L_{N-1}(\zeta)\cdot(z(X) - v) \\
>   & - v_H(\zeta)\cdot t(X)\ \Big)
> \end{split}
> $$
> 
> The first few terms are constants.
> - $\alpha^{n+1}\cdot (L_0(\zeta)\cdot\big(z(X) - c_0\cdot a(X))$ has degree $N - 1 + N - 1 = 2N - 2$.
> - $\alpha^{n+2}\cdot (\zeta - 1)\cdot\big(z(X)-z(\omega^{-1}\cdot\zeta)-c(\zeta)\cdot a(X) \big)$ has degree $N - 1$.
> - $\alpha^{n+3}\cdot L_{N-1}(\zeta)\cdot(z(X) - v)$ has degree $N - 1 + N - 1 = 2N - 2$. $v_H(\zeta)\cdot t(X)$ has degree $2N - 1$.
> 
> So $l_\zeta(X)$ has degree $2N - 1$. Therefore, calculating $q_\zeta(X)$ has complexity $(2N - 1) ~ \mathbb{F}_{\mathsf{mul}}$.

📝 **Efficient Inversion Algorithm**

In general, for $N$ arbitrary points $a_0, \ldots, a_{N - 1}$, to find their inverses $a_0^{-1}, \ldots, a_{N-1}^{-1}$, direct inversion is computationally expensive. We want to convert inversion operations to multiplications in the finite field. The specific algorithm is:

1. First calculate the $N$ products:
   
$$
\begin{aligned}
& b_0 = a_0 \\
& b_1 = b_0 \cdot a_1 = a_0 \cdot a_1 \\
& b_2 = b_1 \cdot a_2 = a_0 \cdot a_1 \cdot a_2 \\
& \ldots \\
& b_{N - 2} = b_{N - 3} \cdot a_{N - 2} = a_0 \cdot a_1 \cdots a_{N - 2} \\
& b_{N - 1} = b_{N - 2} \cdot a_{N - 1} = a_0 \cdot a_1 \cdots a_{N - 2} \cdot a_{N - 1}\\
\end{aligned}
$$

Calculate $b_1, \ldots, b_{N - 1}$, each involving one finite field multiplication, with complexity $(N - 1) ~ \mathbb{F}_{\mathsf{mul}}$.

2. Calculate $b_{N-1}^{-1}$, with complexity $\mathbb{F}_{\mathsf{inv}}$.
3. Calculate:

$$
\begin{aligned}
  & b_{N-2}^{-1} = (a_0 \cdot a_1 \cdots a_{N - 2} )^{-1} = a_{N - 1} \cdot b_{N-1}^{-1} \\
  & b_{N-3}^{-1} = (a_0 \cdot a_1 \cdots a_{N - 3} )^{-1} = a_{N - 2} \cdot b_{N-2}^{-1} \\
  & \ldots \\
  & b_{1}^{-1} = (a_0 \cdot a_1 )^{-1} = a_{2} \cdot b_{2}^{-1} \\
\end{aligned}
$$

The complexity for this step is $(N - 2) ~ \mathbb{F}_{\mathsf{mul}}$.

4. Now calculate $a_0^{-1}, \ldots, a_{N-1}^{-1}$ from the beginning by multiplication:

$$
\begin{aligned}
  & a_0^{-1} = \frac{1}{a_0 \cdot a_1} \cdot a_1 = b_1^{-1} \cdot a_1 \\
  & a_1^{-1} = \frac{1}{a_0 \cdot a_1} \cdot a_0 = b_1^{-1} \cdot b_0\\
  & a_2^{-1} = \frac{1}{a_0 \cdot a_1 \cdot a_2} \cdot (a_0 \cdot a_1) = b_2^{-1} \cdot b_1\\
  & \ldots \\
  & a_{N - 2}^{-1} = \frac{1}{a_0 \cdot a_1 \cdot a_2 \cdots a_{N - 3} \cdot a_{N - 2}} \cdot (a_0 \cdot a_1 \cdot a_2 \cdots a_{N - 3} ) = b_{N - 2}^{-1} \cdot b_{N - 3} \\
  & a_{N - 1}^{-1} = \frac{1}{a_0 \cdot a_1 \cdot a_2 \cdots a_{N - 2} \cdot a_{N - 1}} \cdot (a_0 \cdot a_1 \cdot a_2 \cdots a_{N - 2} ) = b_{N - 1}^{-1} \cdot b_{N - 2} 
\end{aligned}
$$

The complexity is $N ~ \mathbb{F}_{\mathsf{mul}}$.

Therefore, the total complexity to calculate the inverses $a_0^{-1}, \ldots, a_{N-1}^{-1}$ is $\mathbb{F}_{\mathsf{inv}} + (3N - 3) ~ \mathbb{F}_{\mathsf{mul}}$.

**Analyzing Prover Cost**

In Round 3-5, we already calculated $[l_{\zeta}(x)|_{x \in H}]$. Now we'll calculate $[q_{\zeta}(x)|_{x \in H}]$.

- First calculate $N$ inverses, $[(x - \zeta)^{-1}|_{x \in H}]$, using the efficient inversion algorithm described above, with complexity $\mathbb{F}_{\mathsf{inv}} + (3N - 3) ~ \mathbb{F}_{\mathsf{mul}}$.
- Calculate $[q_{\zeta}(x)|_{x \in H}]$, with complexity $N ~ \mathbb{F}_{\mathsf{mul}}$

So the total complexity for this step is:

$$
\mathbb{F}_{\mathsf{inv}} + (4N - 3) ~ \mathbb{F}_{\mathsf{mul}}
$$

#### Round 3-8
Step 8. Construct the vanishing polynomial $z_{D_{\zeta}}(X)$ on $D\zeta$:

$$
z_{D_{\zeta}}(X) = (X-\zeta\omega)\cdots (X-\zeta\omega^{2^{n-1}})(X-\zeta)
$$

##### Prover Cost 3-8

In Round 3-6, the coefficient form of the vanishing polynomial $z_{D_{\zeta}}(X)$ has already been calculated.

#### Round 3-9
Step v,. Construct the Quotient polynomial $q_c(X)$:

$$
q_c(X) = \frac{(c(X) - c^*(X))}{(X-\zeta)(X-\omega\zeta)(X-\omega^2\zeta)\cdots(X-\omega^{2^{n-1}}\zeta)}
$$

##### Prover Cost 3-9

Since the degree of the polynomial in the denominator is relatively high, it's more efficient to perform the calculation using point-value form.

We already have the coefficient forms of $c^*(X)$ and $z_{D_{\zeta}}(X)$, calculated in Round 3-6.

- Calculate $[c^*(x)|_{x \in H}]$ using one FFT to evaluate $c^*(X)$ on $H$, with complexity $\mathsf{FFT}(N)$.
- Calculate $[z_{D_{\zeta}}(x)|_{x \in H}]$ using one FFT to evaluate $z_{D_{\zeta}}(X)$ on $H$, with complexity $\mathsf{FFT}(N)$.
- Calculate the inverse $[(z_{D_{\zeta}}(x))^{-1}|_{x \in H}]$ using the efficient inversion algorithm described earlier, with complexity $\mathbb{F}_{\mathsf{inv}} + (3N - 3) ~ \mathbb{F}_{\mathsf{mul}}$.
- Calculate $[q_c(x)|_{x \in H}]$, with complexity $N ~ \mathbb{F}_{\mathsf{mul}}$.

Therefore, the total complexity for this step is:

$$
2 ~ \mathsf{FFT}(N) + \mathbb{F}_{\mathsf{inv}} + (4N - 3) ~ \mathbb{F}_{\mathsf{mul}}
$$

#### Round 3-10

Step 10. Construct the Quotient polynomial $q_{\omega\zeta}(X)$:

$$
q_{\omega\zeta}(X) = \frac{z(X) - z(\omega^{-1}\cdot\zeta)}{X - \omega^{-1}\cdot\zeta}
$$

##### Prover Cost 3-10

Method 1: Division using coefficient form.

In Round 2-4, we already calculated the coefficient form of $z(X)$, so the coefficients of the polynomial $z(X) - z(\omega^{-1}\cdot\zeta)$ are easy to obtain - just change the constant term. The denominator polynomial is a linear polynomial, so its coefficient form can also be directly obtained. This involves division of a univariate polynomial by a linear polynomial, with complexity $(N - 1) ~ \mathbb{F}_{\mathsf{mul}}$.

Method 2: Calculation using point-value form.

Calculate $[q_{\omega\zeta}(x)|_{x \in H}]$,
- First calculate $[(x - \omega^{-1} \cdot \zeta)^{-1}|_{x \in H}]$ using the efficient inversion algorithm, with complexity $\mathbb{F}_{\mathsf{inv}} + (3N - 3) ~ \mathbb{F}_{\mathsf{mul}}$.
- Calculate $[q_{\omega\zeta}(x)|_{x \in H}]$, with complexity $N ~ \mathbb{F}_{\mathsf{mul}}$.

The total complexity for this method is:

$$
\mathbb{F}_{\mathsf{inv}} + (4N - 3) ~ \mathbb{F}_{\mathsf{mul}}
$$

We can see that since the denominator is only a linear polynomial, Method 1 would be more efficient.

#### Round 3-11

Step 11. Send $\big(Q_c = [q_c(\tau)]_1, Q_\zeta=[q_\zeta(\tau)]_1, Q_{\omega\zeta}=[q_{\omega\zeta}(\tau)]_1, \big)$

##### Prover Cost 3-11

1. Using $[q_c(x)|_{x \in H}]$ obtained in Round 3-9:

$$
Q_c = q_c(\omega^0) \cdot A_0 + \ldots q_c(\omega^{N - 1}) \cdot A_{N - 1}
$$
with complexity $\mathsf{msm}(N, \mathbb{G}_1)$.

2. Using $[q_{\zeta}(x)|_{x \in H}]$ obtained in Round 3-7:

$$
Q_\zeta = q_\zeta(\omega^0) \cdot A_0 + \ldots q_\zeta(\omega^{N - 1}) \cdot A_{N - 1}
$$
with complexity $\mathsf{msm}(N, \mathbb{G}_1)$.

3. From Round 3-10:
- If using Method 1, we get the coefficient form of $q_{\omega\zeta}(X)$: $q_{\omega\zeta}^{(0)}, q_{\omega\zeta}^{(1)}, \ldots, q_{\omega\zeta}^{(N - 2)}$, then:

$$
Q_{\omega\zeta} = q_{\omega\zeta}^{(0)} \cdot G + q_{\omega\zeta}^{(1)} \cdot (\tau \cdot G) + \cdots + q_{\omega\zeta}^{(N - 2)} \cdot (\tau^{N - 2} \cdot G)
$$
where $G$ is the generator of the elliptic curve $\mathbb{G}_1$, and $(G, \tau G, \ldots, \tau^{N - 2}G)$ is the KZG10 SRS. The complexity for this method is $\mathsf{msm}(N - 1, \mathbb{G}_1)$.

- If using Method 2, we get $[q_{\omega\zeta}(x)|_{x \in H}]$, then:

$$
Q_\zeta = q_{\omega\zeta}(\omega^0) \cdot A_0 + \ldots q_{\omega \zeta}(\omega^{N - 1}) \cdot A_{N - 1}
$$
with complexity $\mathsf{msm}(N, \mathbb{G}_1)$.

Summarizing the complexities above:

1. Using Method 1 for Round 3-10 (coefficient form), the complexity is:

$$
2 ~ \mathsf{msm}(N, \mathbb{G}_1) + \mathsf{msm}(N - 1, \mathbb{G}_1)
$$
2. Using Method 2 for Round 3-10 (point-value form), the complexity is:

$$
3 ~ \mathsf{msm}(N, \mathbb{G}_1)
$$

#### Prover Cost Round 3

Adding up all the computational complexities for this round:

1. Using Method 1 for Round 3-10 (coefficient form), the complexity is:

$$
\begin{aligned}
& 2(n - 1) ~ \mathbb{F}_{\mathsf{mul}} + n ~\mathbb{F}_{\mathsf{mul}} + \mathsf{FFT}(N) + (N + 1) ~ \mathbb{F}_{\mathsf{mul}} + (12N + 4n + 2) ~ \mathbb{F}_{\mathsf{mul}} \\
& + {\color{orange} (n + 1) \log^2(n + 1) ~ \mathbb{F}_{\mathsf{mul}} } + \mathbb{F}_{\mathsf{inv}} + (4N - 3) ~ \mathbb{F}_{\mathsf{mul}} + 2 ~ \mathsf{FFT}(N) + \mathbb{F}_{\mathsf{inv}} + (4N - 3) ~ \mathbb{F}_{\mathsf{mul}} \\
& + {\color{red} (N - 1) ~ \mathbb{F}_{\mathsf{mul}}} + {\color{red} 2 ~ \mathsf{msm}(N, \mathbb{G}_1) + \mathsf{msm}(N - 1, \mathbb{G}_1)} \\
= & 3 ~ \mathsf{FFT}(N) + (21N + 7n - 3) ~ \mathbb{F}_{\mathsf{mul}} + 2~ \mathbb{F}_{\mathsf{inv}} + {\color{orange} (n + 1) \log^2(n + 1) ~ \mathbb{F}_{\mathsf{mul}} } \\
& + {\color{red} (N - 1) ~ \mathbb{F}_{\mathsf{mul}}} + {\color{red} 2 ~ \mathsf{msm}(N, \mathbb{G}_1) + \mathsf{msm}(N - 1, \mathbb{G}_1)} \\
= & 3 ~ \mathsf{FFT}(N) + (22N + 7n - 4) ~ \mathbb{F}_{\mathsf{mul}} + 2~ \mathbb{F}_{\mathsf{inv}} + {\color{} 2 ~ \mathsf{msm}(N, \mathbb{G}_1) + \mathsf{msm}(N - 1, \mathbb{G}_1)} + {\color{orange} (n + 1) \log^2(n + 1) ~ \mathbb{F}_{\mathsf{mul}} }
\end{aligned}
$$

This method requires storing the SRS $(G, \tau G, \ldots, \tau^{N - 2}G)$ in memory to facilitate polynomial commitment in coefficient form.

2. Using Method 2 for Round 3-10 (point-value form), the complexity is:

$$
\begin{aligned}
& 2(n - 1) ~ \mathbb{F}_{\mathsf{mul}} + n ~\mathbb{F}_{\mathsf{mul}} + \mathsf{FFT}(N) + (N + 1) ~ \mathbb{F}_{\mathsf{mul}} + (12N + 4n + 2) ~ \mathbb{F}_{\mathsf{mul}} \\
& + {\color{orange} (n + 1) \log^2(n + 1) ~ \mathbb{F}_{\mathsf{mul}} } + \mathbb{F}_{\mathsf{inv}} + (4N - 3) ~ \mathbb{F}_{\mathsf{mul}} + 2 ~ \mathsf{FFT}(N) + \mathbb{F}_{\mathsf{inv}} + (4N - 3) ~ \mathbb{F}_{\mathsf{mul}} \\
& + {\color{red} \mathbb{F}_{\mathsf{inv}} + (4N - 3) ~ \mathbb{F}_{\mathsf{mul}}} + {\color{red} 3 ~ \mathsf{msm}(N, \mathbb{G}_1)} \\
= & 3 ~ \mathsf{FFT}(N) + (21N + 7n - 3) ~ \mathbb{F}_{\mathsf{mul}} + 2~ \mathbb{F}_{\mathsf{inv}} + {\color{orange} (n + 1) \log^2(n + 1) ~ \mathbb{F}_{\mathsf{mul}} } \\
& + {\color{red} \mathbb{F}_{\mathsf{inv}} + (4N - 3) ~ \mathbb{F}_{\mathsf{mul}}} + {\color{red} 3 ~ \mathsf{msm}(N, \mathbb{G}_1)} \\
= & 3 ~ \mathsf{FFT}(N) + (25N + 7n - 6) ~ \mathbb{F}_{\mathsf{mul}} + 3~ \mathbb{F}_{\mathsf{inv}} + 3 ~ \mathsf{msm}(N, \mathbb{G}_1) + {\color{orange} (n + 1) \log^2(n + 1) ~ \mathbb{F}_{\mathsf{mul}} } \\
\end{aligned}
$$

### Round 4.

#### Round 4-1

The Verifier sends a second random challenge $\xi\leftarrow_{\$}\mathbb{F}_p$

#### Round 4-2

Prover constructs the third Quotient polynomial $q_\xi(X)$:

$$
q_\xi(X) = \frac{c(X) - c^*(\xi) - z_{D_\zeta}(\xi)\cdot q_c(X)}{X-\xi}
$$

##### Prover Cost 4-2

- $c^*(X)$ has degree $N - 1$, so calculating $c^*(\xi)$ has complexity $N ~ \mathbb{F}_{\mathsf{mul}}$.
- $z_{D_\zeta}(X)$ has degree $n + 1$, so calculating $z_{D_\zeta}(\xi)$ has complexity $(n + 2) ~ \mathbb{F}_{\mathsf{mul}}$
- In Round 3-9, we already obtained $[q_c(x)|_{x \in H}]$. First calculate $[(z_{D_\zeta}(\xi)\cdot q_c(x))|_{x \in H}]$, with complexity $N ~ \mathbb{F}_{\mathsf{mul}}$.
- Calculate the coefficient form of $z_{D_\zeta}(\xi)\cdot q_c(X)$ using one IFFT, with complexity $\mathsf{IFFT}(N)$.
- Calculate $\frac{c(X) - c^*(\xi) - z_{D_\zeta}(\xi)\cdot q_c(X)}{X-\xi}$ using linear division. The numerator polynomial has degree $N - 1$, so the complexity is $(N - 1) ~ \mathbb{F}_{\mathsf{mul}}$

Therefore, the total complexity for this step is:

$$
\mathsf{IFFT}(N) + (3N + n + 1) ~ \mathbb{F}_{\mathsf{mul}} 
$$

#### Round 4-3

Prover calculates and sends $Q_\xi$:

$$
Q_\xi = \mathsf{KZG10.Commit}(q_\xi(X)) = [q_\xi(\tau)]_1
$$

##### Prover Cost 4-3

The previous step calculated the coefficient form of $q_\xi(X)$, so the complexity of the commitment mainly depends on the polynomial's degree. $\deg(q_\xi) = N - 2$, so the complexity is $\mathsf{msm}(N - 1, \mathbb{G}_1)$.

This method requires storing the SRS $(G, \tau G, \ldots, \tau^{N - 2}G)$ in memory.

#### Prover Cost Round 4

Summarizing the complexity for this round:

$$
\mathsf{IFFT}(N) + (3N + n + 1) ~ \mathbb{F}_{\mathsf{mul}} + \mathsf{msm}(N - 1, \mathbb{G}_1)
$$

### Prover Cost

Summarizing the Prover Cost for all rounds:

1. Using Method 1 for Round 3-10 (coefficient form), the complexity is:

$$
\begin{align}
 & {\color{blue} (N - 1) ~ \mathbb{F}_{\mathsf{mul}} + \mathsf{msm}(N, \mathbb{G}_1)} \\
& + {\color{red} 4 ~ \mathsf{FFT}(N) + 4 ~ \mathsf{IFFT}(N) + (5nN + 10N + n + 2) ~ \mathbb{F}_{\mathsf{mul}} + 2 ~ \mathsf{msm}(N, \mathbb{G}_1)} \\
 & + 3 ~ \mathsf{FFT}(N) + (22N + 7n - 4) ~ \mathbb{F}_{\mathsf{mul}} + 2~ \mathbb{F}_{\mathsf{inv}} + {\color{} 2 ~ \mathsf{msm}(N, \mathbb{G}_1) + \mathsf{msm}(N - 1, \mathbb{G}_1)} + {\color{orange} (n + 1) \log^2(n + 1) ~ \mathbb{F}_{\mathsf{mul}} } \\
 & + {\color{purple}\mathsf{IFFT}(N) + (3N + n + 1) ~ \mathbb{F}_{\mathsf{mul}} + \mathsf{msm}(N - 1, \mathbb{G}_1)} \\
= & (17nN + 36N + 9n - 2) ~ \mathbb{F}_{\mathsf{mul}} + {\color{orange} (n + 1) \log^2(n + 1) ~ \mathbb{F}_{\mathsf{mul}} } + 2~ \mathbb{F}_{\mathsf{inv}} + 5 ~ \mathsf{msm}(N, \mathbb{G}_1) + 2 ~ \mathsf{msm}(N - 1, \mathbb{G}_1)
\end{align}
$$

This method requires storing the SRS $(G, \tau G, \ldots, \tau^{N - 2}G)$ in memory for polynomial commitment in coefficient form.

2. Using Method 2 for Round 3-10 (point-value form), the complexity is:

$$
\begin{align}
 & {\color{blue} (N - 1) ~ \mathbb{F}_{\mathsf{mul}} + \mathsf{msm}(N, \mathbb{G}_1)} \\
& + {\color{red} 4 ~ \mathsf{FFT}(N) + 4 ~ \mathsf{IFFT}(N) + (5nN + 10N + n + 2) ~ \mathbb{F}_{\mathsf{mul}} + 2 ~ \mathsf{msm}(N, \mathbb{G}_1)} \\
 & + 3 ~ \mathsf{FFT}(N) + (25N + 7n - 6) ~ \mathbb{F}_{\mathsf{mul}} + 3~ \mathbb{F}_{\mathsf{inv}} + 3 ~ \mathsf{msm}(N, \mathbb{G}_1) + {\color{orange} (n + 1) \log^2(n + 1) ~ \mathbb{F}_{\mathsf{mul}} } \\
& + {\color{purple}\mathsf{IFFT}(N) + (3N + n + 1) ~ \mathbb{F}_{\mathsf{mul}} + \mathsf{msm}(N - 1, \mathbb{G}_1)} \\
= & (17nN + 39N + 9n - 4) ~ \mathbb{F}_{\mathsf{mul}} + {\color{orange} (n + 1) \log^2(n + 1) ~ \mathbb{F}_{\mathsf{mul}} } + 3~ \mathbb{F}_{\mathsf{inv}} + 6 ~ \mathsf{msm}(N, \mathbb{G}_1) + \mathsf{msm}(N - 1, \mathbb{G}_1)
\end{align}
$$

## Proof Representation

$7\cdot\mathbb{G}_1$, $(n+1)\cdot\mathbb{F}_{p}$

$$
\begin{aligned}
\pi_{eval} &= \big(z(\omega^{-1}\cdot\zeta), c(\zeta)，c(\omega\cdot\zeta), c(\omega^2\cdot\zeta), c(\omega^4\cdot\zeta), \ldots, c(\omega^{2^{n-1}}\cdot\zeta), \\
& \qquad C_{c}, C_{t}, C_{z}, Q_c, Q_\zeta, Q_\xi, Q_{\omega\zeta}\big)
\end{aligned}
$$

## Verification Process

### Step 1

1. Verifier calculates $c^*(\xi)$ using the precomputed Barycentric Weights $\{\hat{w}_i\}$:

$$
c^*(\xi)=\frac{\sum_i c_i^*\frac{\hat{w}_i}{\xi-x_i}}{\sum_i \frac{\hat{w}_i}{\xi-x_i}}
$$

Then calculates the corresponding commitment $C^*(\xi)=[c^*(\xi)]_1$.

#### Verifier Cost 1

> Verifier:
> 
> - First analyzing the complexity of each calculation: To calculate $\frac{\hat{w}_i}{\xi-x_i}$, the numerator $\hat{w}_i$ can be obtained from precomputation, and after calculating the denominator $\xi-x_i$, we need to compute its inverse, then multiply with $\hat{w}_i$. The complexity is therefore $\mathbb{F}_{\mathsf{mul}} + \mathbb{F}_{\mathsf{inv}}$.
> - Calculate $c_i^*\frac{\hat{w}_i}{\xi-x_i}$, with complexity $\mathbb{F}_{\mathsf{mul}}$.
> - Finally, dividing the numerator by the denominator is equivalent to inverting the denominator and multiplying with the numerator, with complexity $\mathbb{F}_{\mathsf{mul}} + \mathbb{F}_{\mathsf{inv}}$.
> - After obtaining $c^*(\xi)$, calculate its commitment $C^*(\xi)$, with complexity $\mathsf{EccMul}^{\mathbb{G}_1}$
> 
> So the total complexity for this step is: 
>
> $$
> \begin{aligned}
>   & (n + 1) ~ (\mathbb{F}_{\mathsf{mul}} + \mathbb{F}_{\mathsf{inv}}) + (n + 1) ~ \mathbb{F}_{\mathsf{mul}} + \mathbb{F}_{\mathsf{mul}} + \mathbb{F}_{\mathsf{inv}} + \mathsf{EccMul}^{\mathbb{G}_1} \\
>  = & \color{orange}{(2n + 3) ~ \mathbb{F}_{\mathsf{mul}} + (n + 2) ~ \mathbb{F}_{\mathsf{inv}} + \mathsf{EccMul}^{\mathbb{G}_1}}
> \end{aligned}
> $$

### Step 2

Verifier calculates $v_H(\zeta), L_0(\zeta), L_{N-1}(\zeta)$:

$$
v_H(\zeta) = \zeta^N - 1
$$

$$
L_0(\zeta) = \frac{1}{N}\cdot \frac{v_{H}(\zeta)}{\zeta-1}
$$

$$
L_{N-1}(\zeta) = \frac{\omega^{N-1}}{N}\cdot \frac{v_{H}(\zeta)}{\zeta-\omega^{N-1}}
$$

#### Verifier Cost 2

> Verifier:
> - $v_H(\zeta)$: $\zeta^N$ can be calculated using $\log N$ finite field multiplications, with complexity $\log N ~ \mathbb{F}_{\mathsf{mul}}$
> - $L_0(\zeta)$: $1/N$ can be provided in precomputation. Calculating the inverse of $\zeta-1$ involves one inversion operation in the finite field, with complexity $\mathbb{F}_{\mathsf{inv}}$. Multiplying the inverse of $\zeta-1$ with $v_{H}(\zeta)$ involves one multiplication in the finite field, with complexity $\mathbb{F}_{\mathsf{mul}}$. The result is then multiplied with $1/N$, with complexity $\mathbb{F}_{\mathsf{mul}}$. So the total complexity for this step is $\mathbb{F}_{\mathsf{inv}} + 2 ~ \mathbb{F}_{\mathsf{mul}}$.
> - $L_{N-1}(\zeta)$: $\omega^{N-1}/N$ can be provided in precomputation. Calculating the inverse of $\zeta-\omega^{N-1}$ involves one inversion operation in the finite field, with complexity $\mathbb{F}_{\mathsf{inv}}$. Multiplying the inverse of $\zeta-\omega^{N-1}$ with $v_{H}(\zeta)$ involves one multiplication in the finite field, with complexity $\mathbb{F}_{\mathsf{mul}}$. The result is then multiplied with $\omega^{N-1}/N$, with complexity $\mathbb{F}_{\mathsf{mul}}$. So the total complexity for this step is $\mathbb{F}_{\mathsf{inv}} + 2 ~ \mathbb{F}_{\mathsf{mul}}$.
>
> Therefore, the total complexity for this step is $2 ~ \mathbb{F}_{\mathsf{inv}} + (\log N + 4) ~ \mathbb{F}_{\mathsf{mul}}$.

### Step 3

Verifier calculates $s_0(\zeta), \ldots, s_{n-1}(\zeta)$ using the recursive method mentioned earlier.

#### Verifier Cost 3

- $\zeta^2, \zeta^4, \ldots, \zeta^{2^{n - 1}}$ can be obtained while calculating $\zeta^N$ in Step 2.
- The remaining calculation is consistent with the analysis in Round 3-1, with complexity $(n - 1) ~ \mathbb{F}_{\mathsf{mul}}$.

### Step 4

Verifier calculates $z_{D_\zeta}(\xi)$:
   
$$
z_{D_{\zeta}}(\xi) = (\xi-\zeta\omega)\cdots (\xi-\zeta\omega^{2^{n-1}})(\xi-\zeta)
$$

#### Verifier Cost 4

> Verifier:
> 
> The calculation of $\xi-\zeta\omega^i$ was already done in the previous steps, so the complexity here mainly involves multiplying $n$ numbers in the finite field, with complexity $(n - 1) ~ \mathbb{F}_{\mathsf{mul}}$.

### Step 5

Verifier calculates the commitment to the linearized polynomial $C_l$:

$$
\begin{split}
C_l & = 
\Big( \Big((c(\zeta) - c_0)s_0(\zeta) \\
& + \alpha \cdot (u_{n-1}\cdot c(\zeta) - (1-u_{n-1})\cdot c(\omega^{2^{n-1}}\cdot\zeta))\cdot s_0(\zeta)\\
  & + \alpha^2\cdot (u_{n-2}\cdot c(\zeta) - (1-u_{n-2})\cdot c(\omega^{2^{n-2}}\cdot\zeta))\cdot s_1(\zeta)  \\
  & + \cdots \\
  & + \alpha^{n-1}\cdot (u_{1}\cdot c(\zeta) - (1-u_{1})\cdot c(\omega^2\cdot\zeta))\cdot s_{n-2}(\zeta)\\
  & + \alpha^n\cdot (u_{0}\cdot c(\zeta) - (1-u_{0})\cdot c(\omega\cdot\zeta))\cdot s_{n-1}(\zeta) \Big) \cdot [1]_1 \\
  & + \alpha^{n+1}\cdot L_0(\zeta)\cdot(C_z - c_0\cdot C_a)\\
  & + \alpha^{n+2}\cdot (\zeta-1)\cdot\big(C_z - z(\omega^{-1}\cdot \zeta)\cdot [1]_1-c(\zeta)\cdot C_{a} ) \\
  & + \alpha^{n+3}\cdot L_{N-1}(\zeta)\cdot(C_z - v \cdot [1]_1) \\
  & - v_H(\zeta)\cdot C_t \Big)
\end{split}
$$

#### Verifier Cost 5

> Verifier: 
>
> - First calculate $\alpha^2, \ldots, \alpha^{n+3}$, involving $n + 2$ finite field multiplications, with complexity $(n + 2) ~ \mathbb{F}_{\mathsf{mul}}$.
> - $s_0(\zeta) \cdot (c(\zeta) - c_0)$ involves one finite field multiplication, with complexity $\mathbb{F}_{\mathsf{mul}}$
> - $\alpha \cdot s_0(\zeta) \cdot (u_{n-1}\cdot c(\zeta) - (1-u_{n-1})\cdot c(\omega^{2^{n-1}}\cdot\zeta))$ has complexity $4 ~ \mathbb{F}_{\mathsf{mul}}$. This applies to terms 2 through $n+1$, so the total complexity is $4n ~ \mathbb{F}_{\mathsf{mul}}$
> - The results above are summed to get a finite field value, which is then multiplied with $[1]_1$, with complexity $\mathsf{EccMul}^{\mathbb{G}_1}$
> - $\alpha^{n+1}\cdot L_0(\zeta)\cdot(C_z - c_0\cdot C_a)$:  
>   - $c_0\cdot C_a$ has complexity $\mathsf{EccMul}^{\mathbb{G}_1}$
>   - $C_z - c_0\cdot C_a$ involves elliptic curve subtraction, which is calculated as addition with the negative point. Since subtraction on elliptic curves is essentially addition with the negative point, and if $P_2 = (x_2, y_2)$, then $-P_2 = (x_2, -y_2)$, the complexity is essentially the same as addition. So the complexity is $\mathsf{EccAdd}^{\mathbb{G}_1}$
> 
>     > 📝 For the Python implementation of addition or subtraction on elliptic curves, refer to [py_ecc](https://github.com/ethereum/py_ecc/blob/main/py_ecc/bn128/bn128_curve.py).
>
>   - $\alpha^{n+1}\cdot L_0(\zeta)$ has complexity $\mathbb{F}_{\mathsf{mul}}$
>   - $\alpha^{n+1}\cdot L_0(\zeta)\cdot(C_z - c_0\cdot C_a)$ involves multiplying the results from above, with complexity $\mathsf{EccMul}^{\mathbb{G}_1}$
>   - So the total complexity for this calculation is $\mathbb{F}_{\mathsf{mul}} + 2 ~ \mathsf{EccMul}^{\mathbb{G}_1} + \mathsf{EccAdd}^{\mathbb{G}_1}$
> - $\alpha^{n+2}\cdot (\zeta-1)\cdot\big(C_z - z(\omega^{-1}\cdot \zeta)\cdot [1]_1-c(\zeta)\cdot C_{a} \big)$:
>   - $c(\zeta)\cdot C_{a}$: $\mathsf{EccMul}^{\mathbb{G}_1}$
>   - $z(\omega^{-1}\cdot \zeta)\cdot [1]_1$: $\mathsf{EccMul}^{\mathbb{G}_1}$
>   - $C_z - z(\omega^{-1}\cdot \zeta)\cdot [1]_1-c(\zeta)\cdot C_{a}$: $2 ~\mathsf{EccAdd}^{\mathbb{G}_1}$
>   - $\alpha^{n+2}\cdot (\zeta-1)$: $\mathbb{F}_{\mathsf{mul}}$
>   - $\alpha^{n+2}\cdot (\zeta-1)\cdot\big(C_z - z(\omega^{-1}\cdot \zeta)\cdot [1]_1-c(\zeta)\cdot C_{a} \big)$: $\mathsf{EccMul}^{\mathbb{G}_1}$
>   - Total: $\mathbb{F}_{\mathsf{mul}} + 3~\mathsf{EccMul}^{\mathbb{G}_1} + 2 ~\mathsf{EccAdd}^{\mathbb{G}_1}$
> - $\alpha^{n+3}\cdot L_{N-1}(\zeta)\cdot(C_z - v \cdot [1]_1)$:
>   - $v \cdot [1]_1$: $\mathsf{EccMul}^{\mathbb{G}_1}$
>   - $C_z - v \cdot [1]_1$: $\mathsf{EccAdd}^{\mathbb{G}_1}$
>   - $\alpha^{n+3}\cdot L_{N-1}(\zeta)\cdot(C_z - v \cdot [1]_1)$: $\mathbb{F}_{\mathsf{mul}} + \mathsf{EccMul}^{\mathbb{G}_1}$
>   - Total: $\mathbb{F}_{\mathsf{mul}} + 2~\mathsf{EccMul}^{\mathbb{G}_1} + \mathsf{EccAdd}^{\mathbb{G}_1}$
> - $v_H(\zeta)\cdot C_t$: $\mathsf{EccMul}^{\mathbb{G}_1}$
> - Sum all the results above, involving 4 additions on the elliptic curve, with complexity $4 ~ \mathsf{EccAdd}^{\mathbb{G}_1}$
> 
> Therefore, the total complexity for calculating $l_{\zeta}(X)$ in this step is:
> 
> $$
> \begin{aligned}
>   & (n + 2 + 1 + 4n) ~ \mathbb{F}_{\mathsf{mul}} + \mathsf{EccMul}^{\mathbb{G}_1} \\
>   & + \mathbb{F}_{\mathsf{mul}} + 2~\mathsf{EccMul}^{\mathbb{G}_1} + \mathsf{EccAdd}^{\mathbb{G}_1} \\
>   & + \mathbb{F}_{\mathsf{mul}} + 3~\mathsf{EccMul}^{\mathbb{G}_1} + 2 ~\mathsf{EccAdd}^{\mathbb{G}_1} \\
>   & + \mathbb{F}_{\mathsf{mul}} + 2~\mathsf{EccMul}^{\mathbb{G}_1} + \mathsf{EccAdd}^{\mathbb{G}_1} \\
>   & + \mathsf{EccMul}^{\mathbb{G}_1} + 4 ~ \mathsf{EccAdd}^{\mathbb{G}_1} \\
>   = & (5n + 6) ~ \mathbb{F}_{\mathsf{mul}} + 9 ~ \mathsf{EccMul}^{\mathbb{G}_1} + 8 ~ \mathsf{EccAdd}^{\mathbb{G}_1}
> \end{aligned}
> $$

### Step 6

Verifier generates a random number $\eta$ to merge the following Pairing verifications:

$$
\begin{split}
e(C_l + \zeta\cdot Q_\zeta, [1]_2)\overset{?}{=}e(Q_\zeta, [\tau]_2)\\
e(C_c - C^*(\xi) - z_{D_\zeta}(\xi)\cdot Q_c + \xi\cdot Q_\xi, [1]_2) \overset{?}{=} e(Q_\xi, [\tau]_2)\\
e(C_z + \zeta\cdot Q_{\omega\zeta} - z(\omega^{-1}\cdot\zeta)\cdot[1]_1, [1]_2) \overset{?}{=} e(Q_{\omega\zeta}, [\tau]_2)\\
\end{split}
$$

The merged verification only requires two Pairing operations:

$$
\begin{split}

P &= \Big(C_l + \zeta\cdot Q_\zeta\Big) \\

& + \eta\cdot \Big(C_c - C^*(\xi) - z_{D_\zeta}(\xi)\cdot Q_c + \xi\cdot Q_\xi\Big) \\

& + \eta^2\cdot\Big(C_z + \zeta\cdot Q_{\omega\zeta} - z(\omega^{-1}\cdot\zeta)\cdot[1]_1\Big)

\end{split}
$$

$$
e\Big(P, [1]_2\Big) \overset{?}{=} e\Big(Q_\zeta + \eta\cdot Q_\xi + \eta^2\cdot Q_{\omega\zeta}, [\tau]_2\Big)
$$

#### Verifier Cost 6

> Verifier:
> 
> - First calculate $\eta^2$, with complexity $\mathbb{F}_{\mathsf{mul}}$
> - $\Big(C_l + \zeta\cdot Q_\zeta\Big)$: $\mathsf{EccMul}^{\mathbb{G}_1} + \mathsf{EccAdd}^{\mathbb{G}_1}$
> - $\eta\cdot \Big(C_c - C^*(\xi) - z_{D_\zeta}(\xi)\cdot Q_c + \xi\cdot Q_\xi\Big)$:
> 
>   $$
>   2 ~ \mathsf{EccMul}^{\mathbb{G}_1} + 3 ~ \mathsf{EccAdd}^{\mathbb{G}_1} + \mathsf{EccMul}^{\mathbb{G}_1} = 3 ~ \mathsf{EccMul}^{\mathbb{G}_1} + 3 ~ \mathsf{EccAdd}^{\mathbb{G}_1}
>   $$
> - $\eta^2\cdot\Big(C_z + \zeta\cdot Q_{\omega\zeta} - z(\omega^{-1}\cdot\zeta)\cdot[1]_1\Big)$: $3 ~\mathsf{EccMul}^{\mathbb{G}_1} + 2~\mathsf{EccAdd}^{\mathbb{G}_1}$
> - Calculate $P$ by adding the results above, with complexity $2 ~ \mathsf{EccAdd}^{\mathbb{G}_1}$
> - $e\Big(P, [1]_2\Big)$ involves one pairing operation on the elliptic curve, denoted as $P$
> - $Q_\zeta + \eta\cdot Q_\xi + \eta^2\cdot Q_{\omega\zeta}$: $2 ~\mathsf{EccMul}^{\mathbb{G}_1} + 2 ~ \mathsf{EccAdd}^{\mathbb{G}_1}$
> - $e\Big(Q_\zeta + \eta\cdot Q_\xi + \eta^2\cdot Q_{\omega\zeta}, [\tau]_2\Big)$ involves one pairing operation on the elliptic curve, with complexity $P$
> 
> Adding up all the results above, the total complexity for this step is:
> 
> $$
> \begin{aligned}
>   & \mathbb{F}_{\mathsf{mul}} + \mathsf{EccMul}^{\mathbb{G}_1} + \mathsf{EccAdd}^{\mathbb{G}_1} \\
>   & + 3 ~ \mathsf{EccMul}^{\mathbb{G}_1} + 3 ~ \mathsf{EccAdd}^{\mathbb{G}_1} \\
>   & + 3 ~\mathsf{EccMul}^{\mathbb{G}_1} + 2~\mathsf{EccAdd}^{\mathbb{G}_1} \\
>   & + 2 ~ \mathsf{EccAdd}^{\mathbb{G}_1} + P + 2 ~\mathsf{EccMul}^{\mathbb{G}_1} + P \\
>   = & \mathbb{F}_{\mathsf{mul}} + 9 ~ \mathsf{EccMul}^{\mathbb{G}_1} + 8 ~ \mathsf{EccAdd}^{\mathbb{G}_1} + 2 ~ P
> \end{aligned}
> $$

### Verifier Cost

$$
\begin{aligned}
  & {\color{orange} (2n + 3) ~ \mathbb{F}_{\mathsf{mul}} + (n + 2) ~ \mathbb{F}_{\mathsf{inv}} + \mathsf{EccMul}^{\mathbb{G}_1}} \\
  & + 2 ~ \mathbb{F}_{\mathsf{inv}} + (\log N + 4) ~ \mathbb{F}_{\mathsf{mul}} \\
  & + 2(n - 1) ~ \mathbb{F}_{\mathsf{mul}} \\
  & + (n - 1) ~ \mathbb{F}_{\mathsf{mul}} \\
  & + (5n + 6) ~ \mathbb{F}_{\mathsf{mul}} + 9 ~ \mathsf{EccMul}^{\mathbb{G}_1} + 8 ~ \mathsf{EccAdd}^{\mathbb{G}_1} \\
  & + \mathbb{F}_{\mathsf{mul}} + 9 ~ \mathsf{EccMul}^{\mathbb{G}_1} + 8 ~ \mathsf{EccAdd}^{\mathbb{G}_1} + 2 ~ P \\
  = & (9n + 8) ~ \mathbb{F}_{\mathsf{mul}} + 2 ~ \mathbb{F}_{\mathsf{inv}} + 18 ~ \mathsf{EccMul}^{\mathbb{G}_1} + 16 ~ \mathsf{EccAdd}^{\mathbb{G}_1} + 2 ~ P \\
  & + {\color{orange} (2n + 3) ~ \mathbb{F}_{\mathsf{mul}} + (n + 2) ~ \mathbb{F}_{\mathsf{inv}} + \mathsf{EccMul}^{\mathbb{G}_1}} \\
  = & (11n + 11) ~ \mathbb{F}_{\mathsf{mul}} + (n + 4) ~ \mathbb{F}_{\mathsf{inv}} + 19 ~ \mathsf{EccMul}^{\mathbb{G}_1} + 16 ~ \mathsf{EccAdd}^{\mathbb{G}_1} + 2 ~ P
\end{aligned}
$$

## Protocol Complexity Summary

### Commit Phase

**Prover's cost:**

$$
N\log N ~\mathbb{F}_{\mathsf{mul}} + \mathsf{msm}(N, \mathbb{G}_1)
$$

### Evaluation Protocol

**Prover's cost:**

1. Using Method 1 for Round 3-10 (coefficient form), the complexity is:

$$
\begin{align}
 (17nN + 36N + 9n - 2) ~ \mathbb{F}_{\mathsf{mul}} + {\color{orange} (n + 1) \log^2(n + 1) ~ \mathbb{F}_{\mathsf{mul}} } + 2~ \mathbb{F}_{\mathsf{inv}} + 5 ~ \mathsf{msm}(N, \mathbb{G}_1) + 2 ~ \mathsf{msm}(N - 1, \mathbb{G}_1)
\end{align}
$$

This method requires storing the SRS $(G, \tau G, \ldots, \tau^{N - 2}G)$ in memory for polynomial commitment in coefficient form.

2. Using Method 2 for Round 3-10 (point-value form), the complexity is:

$$
\begin{align}
  (17nN + 39N + 9n - 4) ~ \mathbb{F}_{\mathsf{mul}} + {\color{orange} (n + 1) \log^2(n + 1) ~ \mathbb{F}_{\mathsf{mul}} } + 3~ \mathbb{F}_{\mathsf{inv}} + 6 ~ \mathsf{msm}(N, \mathbb{G}_1) + \mathsf{msm}(N - 1, \mathbb{G}_1)
\end{align}
$$

**Verifier's cost:**

$$
(11n + 11) ~ \mathbb{F}_{\mathsf{mul}} + (n + 4) ~ \mathbb{F}_{\mathsf{inv}} + 19 ~ \mathsf{EccMul}^{\mathbb{G}_1} + 16 ~ \mathsf{EccAdd}^{\mathbb{G}_1} + 2 ~ P
$$

**Proof size:**

$$
(n + 1) \cdot \mathbb{F}_p + 7 ~ \mathbb{G}_1
$$