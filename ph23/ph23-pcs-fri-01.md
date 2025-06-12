# Missing Protocol PH23-PCS (Part 4)

- Jade Xie <jade@secbit.io>
- Yu Guo <yu.guo@secbit.io>

This paper presents the PH23 protocol coupled with the univariate polynomial commitment scheme FRI-PCS.

## Integrating with FRI

Let's first review the PH23 protocol. For an n-variable MLE polynomial $\tilde{f}(X_0,X_1, \ldots, X_{n - 1})$, it can be written in point-value form over the hypercube $\{0,1\}^n$:

$$
\tilde{f}(X_0, X_1, \ldots, X_{n-1}) = \sum_{i=0}^{N-1} a_i \cdot \overset{\sim}{eq}(\mathsf{bits}(i), (X_0, X_1, \ldots, X_{n-1}))
$$
where $N = 2^n$. When proving that this MLE polynomial evaluates to $v$ at a point $\vec{u} = (u_0, u_1, \ldots, u_{n-1})$, we have:

$$
\tilde{f}(u_0, u_1, \ldots, u_{n-1}) = \sum_{i=0}^{N-1} a_i \cdot \overset{\sim}{eq}(\mathsf{bits}(i), (u_0, u_1, \ldots, u_{n-1})) = v
$$

Let $c_i = \overset{\sim}{eq}(\mathsf{bits}(i), (u_0, u_1, \ldots, u_{n-1}))$, then the evaluation proof is transformed into proving an inner product:

$$
\sum_{i = 0}^{N - 1} a_i \cdot c_i = \langle \vec{a}, \vec{c} \rangle =  v
$$

Since $\vec{c}$ is provided by the Prover, to prevent cheating, we need to prove:

1. That $\vec{c}$ is well-formed.
2. That the inner product $\langle \vec{a}, \vec{c} \rangle = v$.

To prove the correctness of point 1, we need to prove that the following $n + 1$ polynomials evaluate to $0$ on a multiplicative subgroup $H = \{\omega^0, \omega^1, \ldots, \omega^{N - 1}\}$.

$$
\begin{aligned}
p_0(X) = &s_0(X)\cdot \big(c(X) - (1-u_0)(1-u_1)\cdots(1-u_{n-1})\big)      \\
p_1(X) = &s_0(X)\cdot \big(c(X)u_{n-1} - c(\omega^{2^{n-1}}\cdot X)(1-u_{n-1})\big) \\
p_2(X) = &s_1(X)\cdot \big(c(X)u_{n-2} - c(\omega^{2^{n-2}}\cdot X)(1-u_{n-2})\big)  \\
\cdots & \quad\cdots \\
p_{n}(X) = &s_{n-1}(X)\cdot \big(c(X)u_0 - c(\omega\cdot X)(1-u_0)\big) \\
\end{aligned}
$$

To prove the correctness of the inner product in point 2, we use the Grand Sum method, constructing a polynomial $z(X)$ and constraining it with the following polynomials that must evaluate to $0$ on $H$:

$$
\begin{aligned}
h_0(X) = &L_0(X)\cdot\big(z(X) - a_0\cdot c_0\big) \\
h_1(X) = &(X-1)\cdot\big(z(X)-z(\omega^{-1}\cdot X)-a(X)\cdot c(X)) \\
h_2(X) = &L_{N-1}(X)\cdot\big( z(X) - v \big) \\
\end{aligned}
$$

Using a random value $\alpha$ provided by the Verifier, we can aggregate the above $n + 4$ polynomials into a single polynomial $h(X)$:

$$
\begin{aligned}
h(X) &= p_0(X) + \alpha\cdot p_1(X) + \alpha^2\cdot p_2(X) + \cdots + \alpha^{n}\cdot p_{n}(X)\\  & + \alpha^{n+1} \cdot h_0(X) + \alpha^{n+2} \cdot h_1(X) + \alpha^{n+3} \cdot h_2(X) 
\end{aligned}
$$

Now we only need to prove that $h(X)$ evaluates to $0$ on $H$, which completes the proof that $\tilde{f}(u_0, u_1, \ldots, u_{n-1}) = v$. Let $v_H(X)$ be the vanishing polynomial on $H$, then there exists a quotient polynomial $t(X)$ such that:

$$
h(X) = t(X) \cdot v_H(X)
$$

To verify the existence of this quotient polynomial, the Verifier selects a random point $\zeta$, and the Prover sends $t(\zeta), h(\zeta)$ to the Verifier. However, the Prover is actually committing to $a(X)$, $c(X)$, $z(X)$, and $t(X)$, so the Prover sends:

$$
\big(a(\zeta), c(\zeta), c(\zeta\cdot\omega), c(\zeta\cdot\omega^2), \ldots, c(\zeta\cdot\omega^{2^{n-1}}), z(\zeta), z(\zeta\cdot\omega^{-1}), t(\zeta)\big)
$$

With these values, the Verifier can calculate $h(\zeta)$ on their own. Since $H$ is public, the Verifier can also calculate $v_H(\zeta)$, and then verify:

$$
h(\zeta) \stackrel{?}{=} t(\zeta) \cdot v_H(\zeta)
$$

To convince the Verifier that these values are correct, we need to use a univariate polynomial commitment scheme (PCS). Previous articles introduced using KZG10, but this paper implements it using FRI-PCS.

Through the polynomial construction process above, we know that $a(X), c(X), z(X), t(X)$ all have degree $N - 1$. The polynomial $a(X)$ needs to be opened at point $\zeta$. FRI-PCS uses the DEEP technique, where Reed-Solomon encoding space $\mathsf{RS}_{k}[\mathbb{F},D]$ is defined as:
$$
\mathsf{RS}_{k}[\mathbb{F},D] = \{p(x)_{x \in D} : p(X) \in \mathbb{F}[X], \deg p(X) \le k - 1 \}
$$

This requires the Verifier to select a random number $\zeta \stackrel{\$}{\leftarrow} \mathbb{F} \setminus D$. To prove the correctness of $a(\zeta)$, we need to prove that the quotient polynomial:

$$
q_a(X) = \frac{a(X) - a(\zeta)}{X - \zeta}
$$
has degree less than $N - 1$.

For $c(X)$, which needs to be opened at $n + 1$ points, $H_{\zeta}' = \{\zeta, \zeta\cdot\omega, \zeta\cdot\omega^2, \ldots, \zeta\cdot\omega^{2^{n-1}} \}$, we use the method introduced in the [H22] paper's "Multi-point queries" section to open multiple points simultaneously. The quotient polynomial is:

$$
q_c(X) = \sum_{x \in H_\zeta'} \frac{c(X) - c(x)}{X - x} = \frac{c(X) - c(\zeta)}{X - \zeta} + \frac{c(X) - c(\zeta \cdot \omega)}{X - \zeta \cdot \omega} + \ldots + \frac{c(X) - c(\zeta \cdot \omega^{2^{n-1}})}{X - \zeta \cdot \omega^{2^{n-1}}}
$$

We now need to prove that $q_c(X)$ has degree less than $N - 1$.

Similarly for $z(X)$, we prove that the quotient polynomial:

$$
q_z(X) = \frac{z(X) - z(\zeta)}{X - \zeta} + \frac{z(X) - z(\zeta \cdot \omega^{-1})}{X - \zeta \cdot \omega^{-1}}
$$
has degree less than $N - 1$.

For $t(X)$, we prove that the quotient polynomial:

$$
q_t(X) = \frac{t(X) - t(\zeta)}{X - \zeta}
$$
has degree less than $N - 1$.

At this point, the Verifier provides a random number $r \stackrel{\$}{\leftarrow} \mathbb{F}$, and we can batch the four quotient polynomials together:

$$
q'(X) = q_a(X) + r \cdot q_c(X) + r^2 \cdot q_z(X) + r^3 \cdot q_t(X)
$$

This way, we only need to call FRI's low degree test once to prove that $\deg(q'(X)) < N - 1$. To interface with the FRI low degree test protocol, we need to align the degree of $q'(X)$ to a power of 2, by getting another random number $\lambda$ from the Verifier and proving:

$$
q(X) = (1 + \lambda \cdot X) q'(X)
$$
has degree less than $N$.

> 📝 **Remark:**
> When batching different polynomials above, we could also select three different random numbers $r_1, r_2, r_3$ from $\mathbb{F}$ and set:
> 
> $$
> q'(X) = q_a(X) + r_1 \cdot q_c(X) + r_2 \cdot q_z(X) + r_3 \cdot q_t(X)
> $$
> 
> This method provides slightly higher security than using powers of a single random number for batching. ([BCIKS20])

One more point to note: since we use the DEEP method to construct quotient polynomials, we require that the set of evaluation points formed by the selected random number $\zeta$ must not intersect with the Reed-Solomon encoding group:

$$
\{\zeta, \zeta\cdot\omega, \zeta\cdot\omega^2, \ldots, \zeta\cdot\omega^{2^{n-1}}, \zeta \cdot \omega^{-1}\} \cap D = \emptyset
$$

## PH23 + FRI Protocol

Proof objective: For an MLE polynomial $\tilde{f}(X_0, X_1, \ldots, X_{n - 1})$ with $n$ variables, represented in point-value form:

$$
\tilde{f}(X_0, X_1, \ldots, X_{n-1}) = \sum_{i=0}^{N-1} a_i \cdot \overset{\sim}{eq}(\mathsf{bits}(i), (X_0, X_1, \ldots, X_{n-1}))
$$

The goal is to prove that $\tilde{f}(X_0, X_1, \ldots, X_{n - 1})$ evaluates to $v = \tilde{f}(u_0,u_1, \ldots, u_{n - 1})$ at point $\vec{u} = (u_0,u_1, \ldots, u_{n - 1})$.

### Commit Phase

For the FRI protocol, the commitment to a polynomial is computing its Reed-Solomon encoding and committing to this encoding. In the Commit phase of PCS, we need to commit to the original MLE polynomial:

$$
\tilde{f}(X_0, X_1, \ldots, X_{n-1}) = \sum_{i=0}^{N-1} a_i \cdot \overset{\sim}{eq}(\mathsf{bits}(i), (X_0, X_1, \ldots, X_{n-1}))
$$

Vector $\vec{a}$ uniquely defines an n-variable MLE polynomial, so committing to polynomial $\tilde{f}$ is actually committing to $\vec{a}$. If using the FRI protocol, we first need to convert $\vec{a}$ into polynomial $a(X)$, then commit to its Reed-Solomon encoding on $D$.

1. The Prover constructs a univariate polynomial $a(X)$ such that its evaluation at $H$ gives $\vec{a} = (a_{0,}a_{1},\ldots, a_{N-1})$.

$$
a(X) = a_0 \cdot L_0(X) + a_1 \cdot L_1(X) + \ldots + a_{N-1} \cdot L_{N-1}(X)
$$
2. The Prover calculates the commitment $C_a$ to polynomial $a(X)$ and sends $C_a$ to the Verifier:

$$
C_a = \mathsf{cm}([a(x)|_{x \in D}]) = \mathsf{MT.commit}([a(x)|_{x \in D}]) 
$$

### Common Inputs
1. FRI protocol parameters: Reed-Solomon encoding regions $D_n \subset D_{n-1} \subset \cdots \subset D_0 = D$, rate $\rho$, number of query rounds $l$.
2. Commitment $C_a$:

$$
C_a = \mathsf{cm}([a(x)|_{x \in D}]) = \mathsf{MT.commit}([a(x)|_{x \in D}]) 
$$

3. Evaluation point $\vec{u} = (u_0,u_1, \ldots, u_{n - 1})$
4. $v = \tilde{f}(u_0,u_1, \ldots, u_{n - 1})$ 

### Witness

- The values of the multivariate polynomial $\tilde{f}(X_0, X_1, \ldots, X_{n - 1})$ on the Boolean Hypercube $\vec{a} = (a_0,a_1, \ldots, a_{N-1})$ 

### Evaluation Proof Protocol

#### Round 1

Prover:

1. Calculates vector $\vec{c}$, where each element $c_i=\overset{\sim}{eq}(\mathsf{bits}(i), \vec{u})$

2. Constructs polynomial $c(X)$ whose evaluations on $H$ match $\vec{c}$:

$$
c(X) = \sum_{i=0}^{N-1} c_i \cdot L_i(X)
$$

3. Calculates commitment $C_c$ to $c(X)$ and sends $C_c$:

$$
C_c = \mathsf{cm}([c(x)|_{x \in D}]) = \mathsf{MT.commit}([c(x)|_{x \in D}]) 
$$

#### Round 2

Verifier: Sends challenge number $\alpha \stackrel{\$}{\leftarrow} \mathbb{F}_p$ 

Prover: 

1. Constructs constraint polynomials $p_0(X),\ldots, p_{n}(X)$ for $\vec{c}$:

$$
\begin{split}
p_0(X) &= s_0(X) \cdot \Big( c(X) - (1-u_0)(1-u_1)...(1-u_{n-1}) \Big) \\
p_k(X) &= s_{k-1}(X) \cdot \Big( u_{n-k}\cdot c(X) - (1-u_{n-k})\cdot c(\omega^{2^{n-k}}\cdot X)\Big) , \quad k=1\ldots n
\end{split}
$$

2. Aggregates $\{p_i(X)\}$ into a single polynomial $p(X)$:

$$
p(X) = p_0(X) + \alpha\cdot p_1(X) + \alpha^2\cdot p_2(X) + \cdots + \alpha^{n}\cdot p_{n}(X)
$$

3. Constructs accumulator polynomial $z(X)$ satisfying:

$$
\begin{split}
z(1) &= a_0\cdot c_0 \\
z(\omega_{i}) - z(\omega_{i-1}) &=  a(\omega_{i})\cdot c(\omega_{i}), \quad i=1,\ldots, N-1 \\ 
z(\omega^{N-1}) &= v \\
\end{split}
$$

4. Constructs constraint polynomials $h_0(X), h_1(X), h_2(X)$ satisfying:

$$
\begin{split}
h_0(X) &= L_0(X)\cdot\big(z(X) - c_0\cdot a(X) \big) \\
h_1(X) &= (X-1)\cdot\big(z(X)-z(\omega^{-1}\cdot X)-a(X)\cdot c(X)) \\
h_2(X) & = L_{N-1}(X)\cdot\big( z(X) - v \big) \\
\end{split}
$$

5. Aggregates $p(X)$ and $h_0(X), h_1(X), h_2(X)$ into polynomial $h(X)$:

$$
\begin{split}
h(X) &= p(X) + \alpha^{n+1} \cdot h_0(X) + \alpha^{n+2} \cdot h_1(X) + \alpha^{n+3} \cdot h_2(X)
\end{split}
$$

6. Calculates Quotient polynomial $t(X)$ satisfying:

$$
h(X) =t(X)\cdot v_H(X)
$$

7. Calculates commitments $C_t, C_z$ to $t(X)$ and $z(X)$ and sends them to the Verifier:

$$
\begin{split}
C_t &= \mathsf{cm}([t(x)|_{x \in D}]) = \mathsf{MT.commit}([t(x)|_{x \in D}]) \\
C_z &= \mathsf{cm}([z(x)|_{x \in D}]) = \mathsf{MT.commit}([z(x)|_{x \in D}])
\end{split}
$$

#### Round 3

Verifier: Sends random evaluation point $\zeta \stackrel{\$}{\leftarrow} \mathbb{F}_p^* \setminus D$  

Prover: 

1. Calculates $s_i(X)$ evaluations at $\zeta$:

$$
s_0(\zeta), s_1(\zeta), \ldots, s_{n-1}(\zeta)
$$

The Prover can efficiently calculate $s_i(\zeta)$ using the formula:

$$
\begin{aligned}
  s_i(\zeta) & = \frac{\zeta^N - 1}{\zeta^{2^i} - 1} \\
  & = \frac{(\zeta^N - 1)(\zeta^{2^i} +1)}{(\zeta^{2^i} - 1)(\zeta^{2^i} +1)} \\
  & = \frac{\zeta^N - 1}{\zeta^{2^{i + 1}} - 1} \cdot (\zeta^{2^i} +1) \\
  & = s_{i + 1}(\zeta) \cdot (\zeta^{2^i} +1)
\end{aligned} 
$$

This means $s_i(\zeta)$ can be calculated from $s_{i + 1}(\zeta)$, with:

$$
s_{n-1}(\zeta) = \frac{\zeta^N - 1}{\zeta^{2^{n-1}} - 1} = \zeta^{2^{n-1}} + 1
$$

This gives an O(n) algorithm to calculate $s_i(\zeta)$ without division operations. The calculation proceeds: $s_{n-1}(\zeta) \rightarrow s_{n-2}(\zeta) \rightarrow \cdots \rightarrow s_0(\zeta)$.

2. Defines evaluation Domain $H_\zeta'$ with $n+1$ elements:

$$
H_\zeta'=\zeta H = \{\zeta, \omega\zeta, \omega^2\zeta,\omega^4\zeta, \ldots, \omega^{2^{n-1}}\zeta\}
$$

3. Calculates and sends evaluations of $c(X)$ on $H_\zeta'$:

$$
c(\zeta), c(\zeta\cdot\omega), c(\zeta\cdot\omega^2), c(\zeta\cdot\omega^4), \ldots, c(\zeta\cdot\omega^{2^{n-1}})
$$

4. Calculates and sends $z(\zeta)$ and $z(\omega^{-1}\cdot\zeta)$
5. Calculates and sends $t(\zeta)$
6. Calculates and sends $a(\zeta)$

#### Round 4

Verifier: Sends random number $r \stackrel{\$}{\leftarrow} \mathbb{F}_p$

Prover:

1. Calculates quotient polynomial $q_a(X)$:

$$
q_a(X) = \frac{a(X) - a(\zeta)}{X - \zeta}
$$
2. Calculates quotient polynomial $q_c(X)$:

$$
q_c(X) = \sum_{x \in H_\zeta'} \frac{c(X) - c(x)}{X - x} = \frac{c(X) - c(\zeta)}{X - \zeta} + \frac{c(X) - c(\zeta \cdot \omega)}{X - \zeta \cdot \omega} + \ldots + \frac{c(X) - c(\zeta \cdot \omega^{2^{n-1}})}{X - \zeta \cdot \omega^{2^{n-1}}}
$$
3. Calculates quotient polynomial $q_z(X)$:

$$
q_z(X) = \frac{z(X) - z(\zeta)}{X - \zeta} + \frac{z(X) - z(\zeta \cdot \omega^{-1})}{X - \zeta \cdot \omega^{-1}}
$$
4. Calculates quotient polynomial $q_t(X)$:

$$
q_t(X) = \frac{t(X) - t(\zeta)}{X - \zeta}
$$
5. Batches the four quotient polynomials using powers of random number $r$:

$$
q'(X) = q_a(X) + r \cdot q_c(X) + r^2 \cdot q_z(X) + r^3 \cdot q_t(X)
$$

#### Round 5

This round aligns the quotient polynomial $q'(X)$ to a power of 2 to interface with the FRI protocol:

1. Verifier sends random number $\lambda \stackrel{\$}{\leftarrow} \mathbb{F}$
2. Prover calculates:

$$
q(X) = (1 + \lambda \cdot X) q'(X)
$$
on domain $D$.

#### Round 6

Prover and Verifier interact in the FRI low degree test to prove $q(X)$ has degree less than $2^n$:

$$
\pi_{q} = \mathsf{FRI.LDT}(q(X), 2^n)
$$

This includes $n$ rounds of interaction, until the original polynomial is folded into a constant polynomial. The specific interaction process is:

- Let $q^{(0)}(x)|_{x \in D} := q(x)|_{x \in D}$
- For $i = 1,\ldots, n$:
  - Verifier sends random number $\alpha^{(i)}$
  - For any $y \in D_i$, find $x \in D_{i - 1}$ such that $x^2 = y$, Prover calculates:

  $$
    q^{(i)}(y) = \frac{q^{(i - 1)}(x) + q^{(i - 1)}(-x)}{2} + \alpha^{(i)} \cdot \frac{q^{(i - 1)}(x) - q^{(i - 1)}(-x)}{2x}
  $$
  
  - If $i < n$, Prover sends Merkle Tree commitment to $[q^{(i)}(x)|_{x \in D_{i}}]$:
  
  $$
  \mathsf{cm}(q^{(i)}(X)) = \mathsf{cm}([q^{(i)}(x)|_{x \in D_{i}}]) = \mathsf{MT.commit}([q^{(i)}(x)|_{x \in D_{i}}])
  $$

  - If $i = n$, choose any $x_0 \in D_{n}$, Prover sends the value of $q^{(i)}(x_0)$.

> 📝 **Notes**
>
> If the folding count $r < n$, then the polynomial won't fold to a constant, so the Prover will send a Merkle Tree commitment in round $r$ rather than sending a value.

#### Round 7

This round continues the FRI protocol's low degree test query phase. The Verifier repeats the query $l$ times, each time selecting a random number from $D_0$ and having the Prover send the folded values and corresponding Merkle Paths to verify the correctness of each folding round.

Repeat $l$ times:
- Verifier randomly selects $s^{(0)} \stackrel{\$}{\leftarrow} D_0$ 
- Prover opens commitments to $a(s^{(0)}), a(-s^{(0)},c(s^{(0)}),c(-s^{(0)}),z(s^{(0)}),z(-s^{(0)}),t(s^{(0)}),t(-s^{(0)})$, sending these values and their Merkle Paths:
  
$$
  (a(s^{(0)}), \pi_{a}(s^{(0)})) \leftarrow \mathsf{MT.open}([a(x)|_{x \in D_0}], s^{(0)})
$$

$$
  (a(-s^{(0)}), \pi_{a}(-s^{(0)})) \leftarrow \mathsf{MT.open}([a(x)|_{x \in D_0}], -s^{(0)})
$$

$$
  (c(s^{(0)}), \pi_{c}(s^{(0)})) \leftarrow \mathsf{MT.open}([c(x)|_{x \in D_0}], s^{(0)})
$$

$$
  (c(-s^{(0)}), \pi_{c}(-s^{(0)})) \leftarrow \mathsf{MT.open}([c(x)|_{x \in D_0}], -s^{(0)})
$$

$$
  (z(s^{(0)}), \pi_{z}(s^{(0)})) \leftarrow \mathsf{MT.open}([z(x)|_{x \in D_0}], s^{(0)})
$$

$$
  (z(-s^{(0)}), \pi_{z}(-s^{(0)})) \leftarrow \mathsf{MT.open}([z(x)|_{x \in D_0}], -s^{(0)})
$$

$$
  (t(s^{(0)}), \pi_{t}(s^{(0)})) \leftarrow \mathsf{MT.open}([t(x)|_{x \in D_0}], s^{(0)})
$$

$$
  (t(-s^{(0)}), \pi_{t}(-s^{(0)})) \leftarrow \mathsf{MT.open}([t(x)|_{x \in D_0}], -s^{(0)})
$$
- Prover computes $s^{(1)} = (s^{(0)})^2$
- For $i = 1, \ldots, n - 1$
  - Prover sends the values of $q^{(i)}(s^{(i)})$ and $q^{(i)}(-s^{(i)})$, along with their Merkle paths:
  
  $$
  \{(q^{(i)}(s^{(i)}), \pi_{q^{(i)}}(s^{(i)}))\} \leftarrow \mathsf{MT.open}([q^{(i)}(x)|_{x \in D_i}], s^{(i)})
  $$
$$
  \{(q^{(i)}(-s^{(i)}), \pi_{q}^{(i)}(-s^{(i)}))\} \leftarrow \mathsf{MT.open}([q^{(i)}(x)|_{x \in D_i}], -s^{(i)})
  $$
  - Prover computes $s^{(i + 1)} = (s^{(i)})^2$
> If the number of folding rounds $r < n$, then the final step requires sending the value of $q^{(r)}(s^{(r)})$ along with its Merkle path.

#### Proof

The proof sent by the Prover is:

$$
\pi = (C_c,C_t, C_z, c(\zeta), c(\zeta\cdot\omega), c(\zeta\cdot\omega^2), c(\zeta\cdot\omega^4), \ldots, c(\zeta\cdot\omega^{2^{n-1}}), z(\zeta), z(\omega^{-1} \cdot \zeta), t(\zeta), a(\zeta), \pi_{q})
$$

Using the notation $\{\cdot\}^l$ to denote the proof generated by repeating the query $l$ times in the FRI low degree test phase, the FRI low degree test proof is:

$$
\begin{aligned}
  \pi_{q} = &  ( \mathsf{cm}(q^{(1)}(X)), \ldots, \mathsf{cm}(q^{(n - 1)}(X)),q^{(n)}(x_0),  \\
  & \, \{a(s^{(0)}), \pi_{a}(s^{(0)}), a(- s^{(0)}), \pi_{a}(-s^{(0)}),\\
  & \quad c(s^{(0)}), \pi_{c}(s^{(0)}), c(- s^{(0)}), \pi_{c}(-s^{(0)}), \\
  & \quad z(s^{(0)}), \pi_{z}(s^{(0)}), z(- s^{(0)}), \pi_{z}(-s^{(0)}), \\
  & \quad t(s^{(0)}), \pi_{t}(s^{(0)}), t(- s^{(0)}), \pi_{t}(-s^{(0)}), \\
  & \quad q^{(1)}(s^{(1)}), \pi_{q^{(1)}}(s^{(1)}),q^{(1)}(-s^{(1)}), \pi_{q^{(1)}}(-s^{(1)}), \ldots, \\
  & \quad q^{(n - 1)}(s^{(n - 1)}), \pi_{q^{(n - 1)}}(s^{(n - 1)}),q^{(n - 1)}(-s^{(n - 1)}), \pi_{q^{(i)}}(-s^{(n - 1)})\}^l)
\end{aligned}
$$

#### Verification

1. Verifier calculates $s_0(\zeta), \ldots, s_{n-1}(\zeta)$ using the recursive method mentioned earlier.
2. Verifier calculates $p_0(\zeta), \ldots, p_n(\zeta)$

$$
\begin{split}
p_0(\zeta) &= s_0(\zeta) \cdot \Big( c(\zeta) - (1-u_0)(1-u_1)...(1-u_{n-1}) \Big) \\
p_k(\zeta) &= s_{k-1}(\zeta) \cdot \Big( u_{n-k}\cdot c(\zeta) - (1-u_{n-k})\cdot c(\omega^{2^{n-k}}\cdot \zeta)\Big) , \quad k=1\ldots n
\end{split}
$$
3. Verifier calculates $p(\zeta)$

$$
p(\zeta) = p_0(\zeta) + \alpha\cdot p_1(\zeta) + \alpha^2\cdot p_2(\zeta) + \cdots + \alpha^{n}\cdot p_{n}(\zeta)
$$
4. Verifier calculates $v_H(\zeta), L_0(\zeta), L_{N-1}(\zeta)$ 


$$
v_H(\zeta) = \zeta^N - 1
$$

$$
L_0(\zeta) = \frac{1}{N}\cdot \frac{v_{H}(\zeta)}{\zeta-1}
$$

$$
L_{N-1}(\zeta) = \frac{\omega^{N-1}}{N}\cdot \frac{v_{H}(\zeta)}{\zeta-\omega^{N-1}}
$$
5. Verifier calculates $h_0(\zeta), h_1(\zeta), h_2(\zeta)$

$$
\begin{split}
h_0(\zeta) &= L_0(\zeta)\cdot\big(z(\zeta) - c_0\cdot a(\zeta) \big) \\
h_1(\zeta) &= (\zeta-1)\cdot\big(z(\zeta)-z(\omega^{-1}\cdot \zeta)-a(\zeta)\cdot c(\zeta)) \\
h_2(\zeta) & = L_{N-1}(\zeta)\cdot\big( z(\zeta) - v \big) \\
\end{split}
$$
6. Verifier calculates $h(\zeta)$

$$
\begin{split}
h(\zeta) &= p(\zeta) + \alpha^{n+1} \cdot h_0(\zeta) + \alpha^{n+2} \cdot h_1(\zeta) + \alpha^{n+3} \cdot h_2(\zeta)
\end{split}
$$
7. Verifier verifies the correctness of the quotient polynomial:

$$
h(\zeta) \stackrel{?}{=} t(\zeta) \cdot v_H(\zeta)
$$

8. Verifier verifies the low degree test proof for $q(X)$:

$$
\mathsf{FRI.LDT.verify}(\pi_{q}, 2^n) \stackrel{?}{=} 1
$$

The verification process repeats the following steps l times:

- Verify the correctness of $a(s^{(0)}), a(-s^{(0)}), c(s^{(0)}), c(-s^{(0)}), z(s^{(0)}), z(-s^{(0)}), t(s^{(0)}), t(-s^{(0)})$ using Merkle tree verification:

$$
\mathsf{MT.verify}(\mathsf{cm}(a(X)), a(s^{(0)}), \pi_{a}(s^{(0)})) \stackrel{?}{=} 1
$$

$$
\mathsf{MT.verify}(\mathsf{cm}(a(X)), a(-s^{(0)}), \pi_{a}(-s^{(0)})) \stackrel{?}{=} 1
$$

$$
\mathsf{MT.verify}(\mathsf{cm}(c(X)), c(s^{(0)}), \pi_{c}(s^{(0)})) \stackrel{?}{=} 1
$$

$$
\mathsf{MT.verify}(\mathsf{cm}(c(X)), c(-s^{(0)}), \pi_{c}(-s^{(0)})) \stackrel{?}{=} 1
$$

$$
\mathsf{MT.verify}(\mathsf{cm}(z(X)), z(s^{(0)}), \pi_{z}(s^{(0)})) \stackrel{?}{=} 1
$$

$$
\mathsf{MT.verify}(\mathsf{cm}(z(X)), z(-s^{(0)}), \pi_{z}(-s^{(0)})) \stackrel{?}{=} 1
$$

$$
\mathsf{MT.verify}(\mathsf{cm}(t(X)), t(s^{(0)}), \pi_{t}(s^{(0)})) \stackrel{?}{=} 1
$$

$$
\mathsf{MT.verify}(\mathsf{cm}(t(X)), t(-s^{(0)}), \pi_{t}(-s^{(0)})) \stackrel{?}{=} 1
$$

Based on the verified values, the verifier calculates $q^{(0)}(s^{(0)})$ and $q^{(0)}(-s^{(0)})$. For $x \in \{s^{(0)}, -s^{(0)} \}$, compute:

$$
\begin{align}
q'(x) & = \frac{a(x) - a(\zeta)}{x - \zeta} + r \cdot \left( \frac{c(x) - c(\zeta)}{x - \zeta} + \frac{c(x) - c(\zeta \cdot \omega)}{x - \zeta \cdot \omega} + \ldots + \frac{c(x) - c(\zeta \cdot \omega^{2^{n-1}})}{x - \zeta \cdot \omega^{2^{n-1}}}\right) \\ \\
& \qquad + r^2 \cdot \left(\frac{z(x) - z(\zeta)}{x - \zeta} + \frac{z(x) - z(\zeta \cdot \omega^{-1})}{x - \zeta \cdot \omega^{-1}}\right) + r^3 \cdot \frac{t(x) - t(\zeta)}{x - \zeta}
\end{align}
$$

- Then compute:

$$
q^{(0)}(s^{(0)}) = (1 + \lambda \cdot s^{(0)}) q'(s^{(0)})
$$

$$
q^{(0)}(-s^{(0)}) = (1 - \lambda \cdot s^{(0)}) q'(-s^{(0)})
$$

- Verify the correctness of $q^{(1)}(s^{(1)})$ and $q^{(1)}(-s^{(1)})$:

$$
\mathsf{MT.verify}(\mathsf{cm}(q^{(1)}(X)), q^{(1)}(s^{(1)}), \pi_{q^{(1)}}(s^{(1)})) \stackrel{?}{=} 1
$$

$$
\mathsf{MT.verify}(\mathsf{cm}(q^{(1)}(X)), q^{(1)}(-s^{(1)}), \pi_{q^{(1)}}(-s^{(1)})) \stackrel{?}{=} 1
$$

- Verify the $1$ round of folding is correct:

$$
q^{(1)}(s^{(1)}) \stackrel{?}{=} \frac{q^{(0)}(s^{(0)}) + q^{(0)}(- s^{(0)})}{2} + \alpha^{(1)} \cdot \frac{q^{(0)}(s^{(0)}) - q^{(0)}(- s^{(0)})}{2 \cdot s^{(0)}}
$$

- For $i = 2, \ldots, n - 1$:
  - Verify the correctness of $q^{(i)}(s^{(i)})$ and $q^{(i)}(-s^{(i)})$:

  $$
  \mathsf{MT.verify}(\mathsf{cm}(q^{(i)}(X)), q^{(i)}(s^{(i)}), \pi_{q^{(i)}}(s^{(i)})) \stackrel{?}{=} 1
  $$
  
  $$
  \mathsf{MT.verify}(\mathsf{cm}(q^{(i)}(X)), q^{(i)}(-s^{(i)}), \pi_{q^{(i)}}(-s^{(i)})) \stackrel{?}{=} 1
  $$
  
  - Verify the $i$-th round of folding is correct:
  
  $$
  q^{(i)}(s^{(i)}) \stackrel{?}{=} \frac{q^{(i-1)}(s^{(i - 1)}) + q^{(i - 1)}(- s^{(i - 1)})}{2} + \alpha^{(i)} \cdot \frac{q^{(i - 1)}(s^{(i - 1)}) - q^{(i - 1)}(- s^{(i - 1)})}{2 \cdot s^{(i - 1)}}
  $$

- Verify that the polynomial has been folded down to a constant:

$$
q^{(n)}(x_0) \stackrel{?}{=} \frac{q^{(n-1)}(s^{(n - 1)}) + q^{(n - 1)}(- s^{(n - 1)})}{2} + \alpha^{(n)} \cdot \frac{q^{(n - 1)}(s^{(n - 1)}) - q^{(n - 1)}(- s^{(n - 1)})}{2 \cdot s^{(n - 1)}}
$$

## Summary

This paper implements MLE polynomial PCS by connecting the PH23 protocol with the FRI protocol. The inner product proof is implemented through Grand Sum. This protocol can also be implemented through Univariate Sumcheck, which will be specifically described in the next article, and compared with this protocol.

## References

- [PH23] Papini, Shahar, and Ulrich Haböck. "Improving logarithmic derivative lookups using GKR." Cryptology ePrint Archive (2023). https://eprint.iacr.org/2023/1284
- [H22] Haböck, Ulrich. "A summary on the FRI low degree test." _Cryptology ePrint Archive_ (2022).
- [BCIKS20] Eli Ben-Sasson, Dan Carmon, Yuval Ishai, Swastik Kopparty, and Shubhangi Saraf. Proximity Gaps for Reed–Solomon Codes. In *Proceedings of the 61st Annual IEEE Symposium on Foundations of Computer Science*, pages 900–909, 2020.