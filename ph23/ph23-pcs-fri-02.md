# The Missing Protocol PH23-PCS (Part 5)

- Jade Xie <jade@secbit.io>
- Yu Guo <yu.guo@secbit.io>

In the previous article *The Missing Protocol PH23-PCS (Four)* in the *Connecting to FRI* section, we reviewed that the PH23 protocol proof is divided into two parts:

1. Proving that $\vec{c}$ is Well-Formedness.
2. Proving that the inner product $\langle \vec{a}, \vec{c} \rangle = v$.

To prove the correctness of part 1, we need to prove that the following $n + 1$ polynomials all evaluate to $0$ on a multiplicative subgroup $H = \{\omega^0, \omega^1, \ldots, \omega^{N - 1}\}$.

$$
\begin{aligned}
p_0(X) = &s_0(X)\cdot \big(c(X) - (1-u_0)(1-u_1)\cdots(1-u_{n-1})\big)      \\
p_1(X) = &s_0(X)\cdot \big(c(X)u_{n-1} - c(\omega^{2^{n-1}}\cdot X)(1-u_{n-1})\big) \\
p_2(X) = &s_1(X)\cdot \big(c(X)u_{n-2} - c(\omega^{2^{n-2}}\cdot X)(1-u_{n-2})\big)  \\
\cdots & \quad\cdots \\
p_{n}(X) = &s_{n-1}(X)\cdot \big(c(X)u_0 - c(\omega\cdot X)(1-u_0)\big) \\
\end{aligned}
$$

In the protocol introduced in *The Missing Protocol PH23-PCS (Four)*, the Grand Sum method was used to prove the correctness of part 2. Here, we use the Univariate Sumcheck protocol to prove the inner product. We decompose $a(X) \cdot c(X)$ as follows:

$$
a(X)\cdot c(X) = q_{ac}(X)\cdot v_H(X) + X\cdot g(X) + (v/N), \quad \deg(g)<N-1
$$

If we prove that the above equation holds and $\deg (g) < N - 1$, we have effectively proven that the inner product is correct: $\langle \vec{a}, \vec{c} \rangle = v$.

Let's see how the Verifier validates that the above polynomials hold and that $\deg (g) < N - 1$.

1. Proving that $\vec{c}$ is Well-Formedness.
	
	First, using the random number $\alpha$ provided by the Verifier, we aggregate the $n + 1$ polynomials $p_i(X)$ into a single polynomial $p(X)$:
	
	$$
	p(X) = p_0(X) + \alpha\cdot p_1(X) + \alpha^2\cdot p_2(X) + \cdots + \alpha^{n}\cdot p_{n}(X)
	$$
	
	Now we need to show that $p(X)$ evaluates to $0$ on $H$. Let $v_H(X)$ be the Vanishing polynomial for $H$, then there exists a quotient polynomial $t(X)$ satisfying:
	
	$$
	p(X) = t(X) \cdot v_H(X)
	$$
	
	To verify the existence of the quotient polynomial, the Verifier selects a random point $\zeta$, and the Prover sends:
	
	$$
	\big(c(\zeta), c(\zeta\cdot\omega), c(\zeta\cdot\omega^2), \ldots, c(\zeta\cdot\omega^{2^{n-1}}), t(\zeta)\big)
	$$
	
	The Verifier can compute $p(\zeta)$, calculate $v_H(\zeta)$ independently, and verify:
	
	$$
	p(\zeta) \stackrel{?}{=} t(\zeta) \cdot v_H(\zeta)
	$$

2. Proving the inner product $\langle \vec{a}, \vec{c} \rangle = v$.
	
	To prove:
	
	$$
	a(X)\cdot c(X) = q_{ac}(X)\cdot v_H(X) + X\cdot g(X) + (v/N), \quad \deg(g)<N-1
	$$
	
	We can use the same random number $\zeta$, and the Prover sends:
	
	$$
	\big(a(\zeta), q_{ac}(\zeta), g(\zeta)\big)
	$$
	
	The Verifier checks:
	
	$$
	a(\zeta)\cdot c(\zeta) \overset{?}{=} q_{ac}(\zeta)\cdot v_H(\zeta) + \zeta\cdot g(\zeta) + (v/N)
	$$
	
	Additionally, we need to prove $\deg(g)<N-1$, which can be done using FRI's low degree test.

To demonstrate that the values sent by the Prover above are correct, we need to use FRI-PCS. To integrate with the FRI protocol, let's first analyze the degrees of these polynomials. Since $a(X)$ and $c(X)$ are obtained from $\vec{a}$ and $\vec{c}$ respectively:

$$
\deg(a(X)) = N - 1, \quad \deg(c(X)) = N - 1
$$

And:

$$
s_i(X) = \frac{v_H(X)}{v_{H_i}(X)} = \frac{X^N-1}{X^{2^i}-1}
$$

We can determine that $\deg(s_i) = N - 2^i$, therefore:

$$
\deg(p(X)) = \deg(p_0(X)) = \deg(s_0(X)) + \deg(c(X)) = N - 1+ N - 1 = 2N - 2
$$

$$
\deg(t(X)) = \deg(p(X)) - \deg(v_H(X)) = 2N - 2 - N = N - 2
$$

From the decomposition of $a(X) \cdot c(X)$, we can deduce:

$$
\deg(q_{ac}(X)) = \deg(a(X) \cdot c(X)) - \deg(v_H(X)) = 2N - 2 - N = N - 2 
$$

$$
\deg(g(X)) = N - 1 - 1 = N - 2
$$

To call FRI's low degree test only once, we first perform degree correction. We ask the Verifier for a random number $r \stackrel{\$}{\leftarrow} \mathbb{F}$:

$$
t'(X) = t(X) + r \cdot X \cdot t(X)
$$

$$
q'_{ac}(X) = q_{ac}(X) + r \cdot X \cdot q_{ac}(X)
$$

$$
g'(X) = g(X) + r \cdot X \cdot g(X)
$$

Now the polynomials $a(X), c(X), t'(X), q'_{ac}(X), g'(X)$ all have degree $N - 1$. The values sent by the Prover are:

$$
\big(c(\zeta), c(\zeta\cdot\omega), c(\zeta\cdot\omega^2), \ldots, c(\zeta\cdot\omega^{2^{n-1}}), t(\zeta),a(\zeta), q_{ac}(\zeta), g(\zeta)\big)
$$

To prove that the values sent above are correct, a function may need to be opened at multiple points simultaneously. We adopt the same method of constructing quotient polynomials as introduced in the **Connecting to FRI** section of this article.

- For $a(X)$, prove that the quotient polynomial
	
	$$
	q_a(X) = \frac{a(X) - a(\zeta)}{X - \zeta}
	$$
	
	has a degree less than $N - 1$.

- For $c(X)$, prove that the quotient polynomial
	
	$$
	q_c(X) = \sum_{x \in H_\zeta'} \frac{c(X) - c(x)}{X - x} = \frac{c(X) - c(\zeta)}{X - \zeta} + \frac{c(X) - c(\zeta \cdot \omega)}{X - \zeta \cdot \omega} + \ldots + \frac{c(X) - c(\zeta \cdot \omega^{2^{n-1}})}{X - \zeta \cdot \omega^{2^{n-1}}}
	$$
	
	has a degree less than $N - 1$.

- For $t(X)$, use the quotient polynomial of $t'(X)$ to prove that
	
	$$
	q_{t'}(X) = \frac{t'(X) - t'(\zeta)}{X - \zeta}
	$$
	
	has a degree less than $N - 1$.

- For $q_{ac}(X)$, use the quotient polynomial of $q_{ac}'(X)$ to prove that
	
	$$
	q_{q_{ac}'}(X) = \frac{q_{ac}'(X) - q_{ac}'(\zeta)}{X - \zeta}
	$$
	
	has a degree less than $N - 1$.

- For $g(X)$, use the quotient polynomial of $g'(X)$ to prove that
	
	$$
	q_{g'}(X) = \frac{g'(X) - g'(\zeta)}{X - \zeta}
	$$
	
	has a degree less than $N - 1$. This naturally proves that $\deg(g(X)) < N - 1$.

Next, we batch these 5 low degree tests into a single low degree test proof using powers of the random number $r$:

$$
q'(X) = q_a(X) + r \cdot q_c(X) + r^2 \cdot q_{t'}(X) + r^4 \cdot q_{q_{ac}'}(X) + r^6 \cdot q_{g'}(X)
$$

Note that since $t'(X), q_{ac}'(X), g'(X)$ polynomials have already used the random number $r$ for degree correction, to achieve the effect of multiple random numbers with powers of a single random number, the batch powers are not increasing naturally as $(1, r, r^2, r^3, r^4)$ but rather as $(1, r, r^2, r^4, r^6)$.

Now we just need to use FRI's low degree test to prove that $\deg(q'(X)) < N - 1$. Finally, to interface with the FRI low degree test protocol, we need to align the degree of $q'(X)$ to a power of 2 by asking the Verifier for a random number $\lambda$ and proving that:

$$
q(X) = (1 + \lambda \cdot X) q'(X)
$$

has a degree less than $N$.

## PH23 + FRI Protocol

### Commit Phase

For the FRI protocol, the commitment to a polynomial is the commitment to its Reed-Solomon encoding. In the PCS Commit phase, we need to commit to the original MLE polynomial:

$$
\tilde{f}(X_0, X_1, \ldots, X_{n-1}) = \sum_{i=0}^{N-1} a_i \cdot \overset{\sim}{eq}(\mathsf{bits}(i), (X_0, X_1, \ldots, X_{n-1}))
$$

Vector $\vec{a}$ uniquely defines an $n$-variable MLE polynomial. To commit to the MLE polynomial $\tilde{f}$, we essentially commit to $\vec{a}$. If using the FRI protocol, we first convert $\vec{a}$ into a polynomial $a(X)$, then commit to its Reed-Solomon encoding on $D$.

1. The Prover constructs a univariate polynomial $a(X)$ such that its evaluations on $H$ are $\vec{a} = (a_{0,}a_{1},\ldots, a_{N-1})$.

	$$
	a(X) = a_0 \cdot L_0(X) + a_1 \cdot L_1(X) + \ldots + a_{N-1} \cdot L_{N-1}(X)
	$$
	
2. The Prover computes the commitment $C_a$ to polynomial $a(X)$ and sends $C_a$ to the Verifier:

	$$
	C_a = \mathsf{cm}([a(x)|_{x \in D}]) = \mathsf{MT.commit}([a(x)|_{x \in D}]) 
	$$

### Public Input

1. FRI protocol parameters: Reed-Solomon encoding domains $D_n \subset D_{n-1} \subset \cdots \subset D_0 = D$, code rate $\rho$, number of query rounds $l$.
2. Commitment $C_a$:

	$$
	C_a = \mathsf{cm}([a(x)|_{x \in D}]) = \mathsf{MT.commit}([a(x)|_{x \in D}]) 
	$$
	
3. Evaluation point $\vec{u} = (u_0,u_1, \ldots, u_{n - 1})$
4. $v = \tilde{f}(u_0,u_1, \ldots, u_{n - 1})$ 

### Witness

- Values of the multivariate polynomial $\tilde{f}(X_0, X_1, \ldots, X_{n - 1})$ on the Boolean Hypercube: $\vec{a} = (a_0,a_1, \ldots, a_{N-1})$ 

### Evaluation Proof Protocol

#### Round 1

Prover:

1. Computes vector $\vec{c}$, where each element $c_i=\overset{\sim}{eq}(\mathsf{bits}(i), \vec{u})$

2. Constructs polynomial $c(X)$ such that its evaluations on $H$ are exactly $\vec{c}$.

	$$
	c(X) = \sum_{i=0}^{N-1} c_i \cdot L_i(X)
	$$
3. Computes the commitment $C_c$ to $c(X)$ and sends $C_c$:
	
	$$
	C_c = \mathsf{cm}([c(x)|_{x \in D}]) = \mathsf{MT.commit}([c(x)|_{x \in D}]) 
	$$

4. Decomposes $a(X) \cdot c(X)$ to compute $q_{ac}(X)$ and $g(X)$ satisfying:

	$$
	a(X)\cdot c(X) = q_{ac}(X)\cdot v_H(X) + X\cdot g(X) + (v/N)
	$$
	
5. Computes the commitment $C_{q_{ac}}$ to $q_{ac}(X)$ and sends $C_{q_{ac}}$:

	$$
	C_{q_{ac}} = \mathsf{cm}([q_{ac}(x)|_{x \in D}]) = \mathsf{MT.commit}([q_{ac}(x)|_{x \in D}]) 
	$$
	
6. Computes the commitment $C_g$ to $g(X)$ and sends $C_{g}$:

	$$
	C_{g} = \mathsf{cm}([g(x)|_{x \in D}]) = \mathsf{MT.commit}([g(x)|_{x \in D}]) 
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
	
3. Computes the Quotient polynomial $t(X)$ satisfying:
	
	$$
	p(X) =t(X)\cdot v_H(X)
	$$
	
4. Computes the commitment $C_t$ to $t(X)$ and sends it to the Verifier:

	$$
	\begin{split}
	C_t &= \mathsf{cm}([t(x)|_{x \in D}]) = \mathsf{MT.commit}([t(x)|_{x \in D}])
	\end{split}
	$$

#### Round 3

Verifier: Sends random evaluation point $\zeta \stackrel{\$}{\leftarrow} \mathbb{F}_p^* \setminus D$  

Prover: 

1. Computes the evaluations of $s_i(X)$ at $\zeta$:
	
	$$
	s_0(\zeta), s_1(\zeta), \ldots, s_{n-1}(\zeta)
	$$
	
	The Prover can efficiently compute $s_i(\zeta)$ using the formula for $s_i(X)$:
	
	$$
	\begin{aligned}
	  s_i(\zeta) & = \frac{\zeta^N - 1}{\zeta^{2^i} - 1} \\
	  & = \frac{(\zeta^N - 1)(\zeta^{2^i} +1)}{(\zeta^{2^i} - 1)(\zeta^{2^i} +1)} \\
	  & = \frac{\zeta^N - 1}{\zeta^{2^{i + 1}} - 1} \cdot (\zeta^{2^i} +1) \\
	  & = s_{i + 1}(\zeta) \cdot (\zeta^{2^i} +1)
	\end{aligned} 
	$$
	
	Thus, $s_i(\zeta)$ can be computed from $s_{i + 1}(\zeta)$, and:
	
	$$
	s_{n-1}(\zeta) = \frac{\zeta^N - 1}{\zeta^{2^{n-1}} - 1} = \zeta^{2^{n-1}} + 1
	$$
	
	This gives us an $O(n)$ algorithm to compute $s_i(\zeta)$ without division operations. The computation sequence is: $s_{n-1}(\zeta) \rightarrow s_{n-2}(\zeta) \rightarrow \cdots \rightarrow s_0(\zeta)$.
	
2. Defines the evaluation Domain $H_\zeta'$ containing $n+1$ elements:
	
	$$
	H_\zeta'=\zeta H = \{\zeta, \omega\zeta, \omega^2\zeta,\omega^4\zeta, \ldots, \omega^{2^{n-1}}\zeta\}
	$$
	
3. Computes and sends the evaluations of $c(X)$ on $H_\zeta'$:
	
	$$
	c(\zeta), c(\zeta\cdot\omega), c(\zeta\cdot\omega^2), c(\zeta\cdot\omega^4), \ldots, c(\zeta\cdot\omega^{2^{n-1}})
	$$
4. Computes and sends $t(\zeta)$
5. Computes and sends $a(\zeta)$
6. Computes and sends $q_{ac}(\zeta)$ 
7. Computes and sends $g(\zeta)$ 

#### Round 4

Verifier: Sends random number $r \stackrel{\$}{\leftarrow} \mathbb{F}_p$

Prover:

1. Performs degree correction, computing polynomials $t'(X), q'_{ac}(X), g'(X)$:
	
	$$
	t'(X) = t(X) + r \cdot X \cdot t(X)
	$$
	
	$$
	q'_{ac}(X) = q_{ac}(X) + r \cdot X \cdot q_{ac}(X)
	$$
	
	$$
	g'(X) = g(X) + r \cdot X \cdot g(X)
	$$

2. Computes quotient polynomial $q_a(X)$:
	
	$$
	q_a(X) = \frac{a(X) - a(\zeta)}{X - \zeta}
	$$
	
3. Computes quotient polynomial $q_c(X)$:
	
	$$
	q_c(X) = \sum_{x \in H_\zeta'} \frac{c(X) - c(x)}{X - x} = \frac{c(X) - c(\zeta)}{X - \zeta} + \frac{c(X) - c(\zeta \cdot \omega)}{X - \zeta \cdot \omega} + \ldots + \frac{c(X) - c(\zeta \cdot \omega^{2^{n-1}})}{X - \zeta \cdot \omega^{2^{n-1}}}
	$$
	
4. Computes quotient polynomial $q_{t'}(X)$:

	$$
	q_{t'}(X) = \frac{t'(X) - t'(\zeta)}{X - \zeta}
	$$
	
5. Computes quotient polynomial $q_{q_{ac}'}(X)$:

	$$
	q_{q_{ac}'}(X) = \frac{q_{ac}'(X) - q_{ac}'(\zeta)}{X - \zeta}
	$$

6. Computes quotient polynomial $q_{g'}(X)$:
	
	$$
	q_{g'}(X) = \frac{g'(X) - g'(\zeta)}{X - \zeta}
	$$
7. Batches the 5 quotient polynomials using powers of $r$:
	
	$$
	q'(X) = q_a(X) + r \cdot q_c(X) + r^2 \cdot q_{t'}(X) + r^4 \cdot q_{q_{ac}'}(X) + r^6 \cdot q_{g'}(X)
	$$
#### Round 5

This round aligns the quotient polynomial $q'(X)$ to a power of 2 to interface with the FRI protocol.

1. Verifier sends random number $\lambda \stackrel{\$}{\leftarrow} \mathbb{F}$
2. Prover computes 

$$
q(X) = (1 + \lambda \cdot X) q'(X)
$$
on $D$.

#### Round 6

The Prover and Verifier interact for FRI's low degree test to prove that $q(X)$ has degree less than $2^n$.

$$
\pi_{q} = \mathsf{FRI.LDT}(q(X), 2^n)
$$

This involves $n$ rounds of interaction, ultimately folding the original polynomial into a constant polynomial. Using $i$ to denote the $i$-th round, the interaction process is:

- Define $q^{(0)}(x)|_{x \in D} := q(x)|_{x \in D}$
- For $i = 1,\ldots, n$:
  - Verifier sends random number $\alpha^{(i)}$
  - For any $y \in D_i$, find $x \in D_{i-1}$ such that $y^2 = x$, Prover computes:

  $$
    q^{(i)}(y) = \frac{q^{(i - 1)}(x) + q^{(i - 1)}(-x)}{2} + \alpha^{(i)} \cdot \frac{q^{(i - 1)}(x) + q^{(i - 1)}(-x)}{2x}
  $$

  
  - If $i < n$, Prover sends the Merkle Tree commitment of $[q^{(i)}(x)|_{x \in D_{i}}]$,
  
  $$
  \mathsf{cm}(q^{(i)}(X)) = \mathsf{cm}([q^{(i)}(x)|_{x \in D_{i}}]) = \mathsf{MT.commit}([q^{(i)}(x)|_{x \in D_{i}}])
  $$

  - If $i = n$, choose any $x_0 \in D_{n}$, Prover sends the value of $q^{(i)}(x_0)$.

> 📝 **Notes**
>
> If the folding count $r < n$, the final result won't be a constant polynomial. In that case, the Prover sends a Merkle Tree commitment in round $r$ instead of sending a value.

#### Round 7

This round continues the FRI protocol's low degree test query phase. The Verifier repeats queries $l$ times, each time selecting a random number from $D_0$ and asking the Prover to send the folding values from each round and corresponding Merkle Paths to verify each folding's correctness.

Repeat $l$ times:
- Verifier randomly selects $s^{(0)} \stackrel{\$}{\leftarrow} D_0$ 
- Prover opens commitments to $a(s^{(0)}), a(-s^{(0)},c(s^{(0)}),c(-s^{(0)}),t(s^{(0)}),t(-s^{(0)}),q_{ac}(s^{(0)}),q_{ac}(-s^{(0)}),g(s^{(0)}),g(-s^{(0)})$, providing these values and their Merkle Paths:
  
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
  (t(s^{(0)}), \pi_{t}(s^{(0)})) \leftarrow \mathsf{MT.open}([t(x)|_{x \in D_0}], s^{(0)})
$$

$$
  (t(-s^{(0)}), \pi_{t}(-s^{(0)})) \leftarrow \mathsf{MT.open}([t(x)|_{x \in D_0}], -s^{(0)})
$$

$$
  (q_{ac}(s^{(0)}), \pi_{q_{ac}}(s^{(0)})) \leftarrow \mathsf{MT.open}([q_{ac}(x)|_{x \in D_0}], s^{(0)})
$$

$$
  (q_{ac}(-s^{(0)}), \pi_{q_{ac}}(-s^{(0)})) \leftarrow \mathsf{MT.open}([q_{ac}(x)|_{x \in D_0}], -s^{(0)})
$$

$$
  (g(s^{(0)}), \pi_{g}(s^{(0)})) \leftarrow \mathsf{MT.open}([g(x)|_{x \in D_0}], s^{(0)})
$$

$$
  (g(-s^{(0)}), \pi_{g}(-s^{(0)})) \leftarrow \mathsf{MT.open}([g(x)|_{x \in D_0}], -s^{(0)})
$$

- Prover computes $s^{(1)} = (s^{(0)})^2$ 
- For $i = 1, \ldots, n - 1$:
  - Prover sends values $q^{(i)}(s^{(i)}), q^{(i)}(-s^{(i)})$ with their Merkle Paths:
  
  $$
  \{(q^{(i)}(s^{(i)}), \pi_{q^{(i)}}(s^{(i)}))\} \leftarrow \mathsf{MT.open}([q^{(i)}(x)|_{x \in D_i}], s^{(i)})
  $$
  $$
  \{(q^{(i)}(-s^{(i)}), \pi_{q}^{(i)}(-s^{(i)}))\} \leftarrow \mathsf{MT.open}([q^{(i)}(x)|_{x \in D_i}], -s^{(i)})
  $$
  - Prover computes $s^{(i + 1)} = (s^{(i)})^2$

> If the folding count $r < n$, then the last step requires sending the value $q^{(r)}(s^{(r)})$ with its Merkle Path.

#### Proof

The proof sent by the Prover is:

$$
\pi = (C_c,C_{q_{ac}}, C_g, C_t, c(\zeta), c(\zeta\cdot\omega), c(\zeta\cdot\omega^2), c(\zeta\cdot\omega^4), \ldots, c(\zeta\cdot\omega^{2^{n-1}}), t(\zeta), a(\zeta), q_{ac}(\zeta), g(\zeta), \pi_{q})
$$

Using the notation $\{\cdot\}^l$ to represent the proofs generated during the $l$ query repetitions in FRI's low degree test, which are randomly selected, the FRI low degree test proof is:

$$
\begin{aligned}
  \pi_{q} = &  ( \mathsf{cm}(q^{(1)}(X)), \ldots, \mathsf{cm}(q^{(n - 1)}(X)),q^{(n)}(x_0),  \\
  & \, \{a(s^{(0)}), \pi_{a}(s^{(0)}), a(- s^{(0)}), \pi_{a}(-s^{(0)}),\\
  & \quad c(s^{(0)}), \pi_{c}(s^{(0)}), c(- s^{(0)}), \pi_{c}(-s^{(0)}), \\
  & \quad t(s^{(0)}), \pi_{t}(s^{(0)}), t(- s^{(0)}), \pi_{t}(-s^{(0)}), \\
  & \quad q_{ac}(s^{(0)}), \pi_{q_{ac}}(s^{(0)}), q_{ac}(- s^{(0)}), \pi_{q_{ac}}(-s^{(0)}), \\
  & \quad g(s^{(0)}), \pi_{g}(s^{(0)}), g(- s^{(0)}), \pi_{g}(-s^{(0)}), \\
  & \quad q^{(1)}(s^{(1)}), \pi_{q^{(1)}}(s^{(1)}),q^{(1)}(-s^{(1)}), \pi_{q^{(1)}}(-s^{(1)}), \ldots, \\
  & \quad q^{(n - 1)}(s^{(n - 1)}), \pi_{q^{(n - 1)}}(s^{(n - 1)}),q^{(n - 1)}(-s^{(n - 1)}), \pi_{q^{(i)}}(-s^{(n - 1)})\}^l)
\end{aligned}
$$

#### Verification

1. Verifier computes $s_0(\zeta), \ldots, s_{n-1}(\zeta)$ using the recursive method mentioned earlier.
2. Verifier computes $p_0(\zeta), \ldots, p_n(\zeta)$:
	
	$$
	\begin{split}
	p_0(\zeta) &= s_0(\zeta) \cdot \Big( c(\zeta) - (1-u_0)(1-u_1)...(1-u_{n-1}) \Big) \\
	p_k(\zeta) &= s_{k-1}(\zeta) \cdot \Big( u_{n-k}\cdot c(\zeta) - (1-u_{n-k})\cdot c(\omega^{2^{n-k}}\cdot \zeta)\Big) , \quad k=1\ldots n
	\end{split}
	$$
3. Verifier computes $p(\zeta)$:
	
	$$
	p(\zeta) = p_0(\zeta) + \alpha\cdot p_1(\zeta) + \alpha^2\cdot p_2(\zeta) + \cdots + \alpha^{n}\cdot p_{n}(\zeta)
	$$
	
4. Verifier computes $v_H(\zeta)$:

	$$
	v_H(\zeta) = \zeta^N - 1
	$$
	
5. Verifier checks the correctness of the quotient polynomial:

	$$
	p(\zeta) \stackrel{?}{=} t(\zeta) \cdot v_H(\zeta)
	$$
6. Verifier checks the correctness of the inner product:

	$$
	a(\zeta)\cdot c(\zeta) \overset{?}{=} q_{ac}(\zeta)\cdot v_H(\zeta) + \zeta\cdot g(\zeta) + (v/N)
	$$
	
7. Verifier verifies the low degree test proof for $q(X)$:

$$
\mathsf{FRI.LDT.verify}(\pi_{q}, 2^n) \stackrel{?}{=} 1
$$

The specific verification process repeats $l$ times:
- Verify the correctness of $a(s^{(0)}), a(-s^{(0)},c(s^{(0)}),c(-s^{(0)}),t(s^{(0)}),t(-s^{(0)}),q_{ac}(s^{(0)}),q_{ac}(-s^{(0)}),g(s^{(0)}),g(-s^{(0)})$ by checking:

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
\mathsf{MT.verify}(\mathsf{cm}(t(X)), t(s^{(0)}), \pi_{t}(s^{(0)})) \stackrel{?}{=} 1
$$

$$
\mathsf{MT.verify}(\mathsf{cm}(t(X)), t(-s^{(0)}), \pi_{t}(-s^{(0)})) \stackrel{?}{=} 1
$$

$$
\mathsf{MT.verify}(\mathsf{cm}(q_{ac}(X)), q_{ac}(s^{(0)}), \pi_{q_{ac}}(s^{(0)})) \stackrel{?}{=} 1
$$

$$
\mathsf{MT.verify}(\mathsf{cm}(q_{ac}(X)), q_{ac}(-s^{(0)}), \pi_{q_{ac}}(-s^{(0)})) \stackrel{?}{=} 1
$$

$$
\mathsf{MT.verify}(\mathsf{cm}(g(X)), g(s^{(0)}), \pi_{g}(s^{(0)})) \stackrel{?}{=} 1
$$

$$
\mathsf{MT.verify}(\mathsf{cm}(g(X)), g(-s^{(0)}), \pi_{g}(-s^{(0)})) \stackrel{?}{=} 1
$$
- Verifier computes $t'(s^{(0)}), t'(-s^{(0)}), q'_{ac}(s^{(0)}), q'_{ac}(-s^{(0)}), g'(s^{(0)}), g'(-s^{(0)})$ and $t'(\zeta), q'_{ac}(\zeta), g'(\zeta)$


$$
t'(s^{(0)}) = t(s^{(0)}) + r \cdot s^{(0)} \cdot t(s^{(0)}), \qquad t'(-s^{(0)}) = t(-s^{(0)}) + r \cdot (-s^{(0)}) \cdot t(-s^{(0)}) 
$$

$$
q_{ac}'(s^{(0)}) = q_{ac}(s^{(0)}) + r \cdot s^{(0)} \cdot q_{ac}(s^{(0)}), \qquad q_{ac}'(-s^{(0)}) = q_{ac}(-s^{(0)}) + r \cdot (-s^{(0)}) \cdot q_{ac}(-s^{(0)}) 
$$

$$
g'(s^{(0)}) = g(s^{(0)}) + r \cdot s^{(0)} \cdot g(s^{(0)}), \qquad g'(-s^{(0)}) = g(-s^{(0)}) + r \cdot (-s^{(0)}) \cdot g(-s^{(0)}) 
$$

$$
t'(\zeta) = t(\zeta) + r \cdot \zeta \cdot t(\zeta)
$$

$$
q_{ac}'(\zeta) = q_{ac}(\zeta) + r \cdot \zeta \cdot q_{ac}(\zeta)
$$

$$
g'(\zeta) = g(\zeta) + r \cdot \zeta \cdot g(\zeta)
$$

- Verifier calculates $q'(s^{(0)})$ and $q'(-s^{(0)})$ using the provided values: $a(s^{(0)}), a(-s^{(0)},c(s^{(0)}),c(-s^{(0)}),t(s^{(0)}),t(-s^{(0)}),q_{ac}(s^{(0)}),q_{ac}(-s^{(0)}),g(s^{(0)}),g(-s^{(0)})$

$$
\begin{align}
q'(s^{(0)}) & = \frac{a(s^{(0)}) - a(\zeta)}{s^{(0)} - \zeta} + r \cdot \left( \frac{c(s^{(0)}) - c(\zeta)}{s^{(0)} - \zeta} + \frac{c(s^{(0)}) - c(\zeta \cdot \omega)}{s^{(0)} - \zeta \cdot \omega} + \ldots + \frac{c(s^{(0)}) - c(\zeta \cdot \omega^{2^{n-1}})}{s^{(0)} - \zeta \cdot \omega^{2^{n-1}}}\right) \\ \\
& \qquad + r^2 \cdot \frac{t'(s^{(0)}) - t'(\zeta)}{s^{(0)} - \zeta} + r^4 \cdot \frac{q_{ac}'(s^{(0)}) - q_{ac}'(\zeta)}{s^{(0)} - \zeta} + r^6 \cdot \frac{g'(s^{(0)}) - g'(\zeta)}{s^{(0)} - \zeta}
\end{align}
$$

$$
\begin{align}
q'(-s^{(0)}) & = \frac{a(-s^{(0)}) - a(\zeta)}{-s^{(0)} - \zeta} + r \cdot \left( \frac{c(-s^{(0)}) - c(\zeta)}{-s^{(0)} - \zeta} + \frac{c(-s^{(0)}) - c(\zeta \cdot \omega)}{-s^{(0)} - \zeta \cdot \omega} + \ldots + \frac{c(-s^{(0)}) - c(\zeta \cdot \omega^{2^{n-1}})}{-s^{(0)} - \zeta \cdot \omega^{2^{n-1}}}\right) \\ \\
& \qquad + r^2 \cdot \frac{t'(-s^{(0)}) - t'(\zeta)}{-s^{(0)} - \zeta} + r^4 \cdot \frac{q_{ac}'(-s^{(0)}) - q_{ac}'(\zeta)}{-s^{(0)} - \zeta} + r^6 \cdot \frac{g'(-s^{(0)}) - g'(\zeta)}{-s^{(0)} - \zeta}
\end{align}
$$

- Verifier computes:

$$
q^{(0)}(s^{(0)}) = (1 + \lambda \cdot s^{(0)}) q'(s^{(0)})
$$

$$
q^{(0)}(-s^{(0)}) = (1 - \lambda \cdot s^{(0)}) q'(-s^{(0)})
$$

- Verifier checks the correctness of $q^{(1)}(s^{(1)}), q^{(1)}(-s^{(1)})$

$$
\mathsf{MT.verify}(\mathsf{cm}(q^{(1)}(X)), q^{(1)}(s^{(1)}), \pi_{q^{(1)}}(s^{(1)})) \stackrel{?}{=} 1
$$


$$
\mathsf{MT.verify}(\mathsf{cm}(q^{(1)}(X)), q^{(1)}(-s^{(1)}), \pi_{q^{(1)}}(-s^{(1)})) \stackrel{?}{=} 1
$$

- Verifier checks if the first round folding is correct:

$$
q^{(1)}(s^{(1)}) \stackrel{?}{=} \frac{q^{(0)}(s^{(0)}) + q^{(0)}(- s^{(0)})}{2} + \alpha^{(1)} \cdot \frac{q^{(0)}(s^{(0)}) - q^{(0)}(- s^{(0)})}{2 \cdot s^{(0)}}
$$
- For $i = 2, \ldots, n - 1$:
  - Verify the correctness of $q^{(i)}(s^{(i)}), q^{(i)}(-s^{(i)})$
  $$
  \mathsf{MT.verify}(\mathsf{cm}(q^{(i)}(X)), q^{(i)}(s^{(i)}), \pi_{q^{(i)}}(s^{(i)})) \stackrel{?}{=} 1
  $$

  $$
  \mathsf{MT.verify}(\mathsf{cm}(q^{(i)}(X)), q^{(i)}(-s^{(i)}), \pi_{q^{(i)}}(-s^{(i)})) \stackrel{?}{=} 1
  $$
  - Check if the $i$-th round folding is correct:
  
  $$
  q^{(i)}(s^{(i)}) \stackrel{?}{=} \frac{q^{(i-1)}(s^{(i - 1)}) + q^{(i - 1)}(- s^{(i - 1)})}{2} + \alpha^{(i)} \cdot \frac{q^{(i - 1)}(s^{(i - 1)}) - q^{(i - 1)}(- s^{(i - 1)})}{2 \cdot s^{(i - 1)}}
  $$
- Check if the final polynomial is constant:
  $$
  q^{(n)}(x_0) \stackrel{?}{=} \frac{q^{(n-1)}(s^{(n - 1)}) + q^{(n - 1)}(- s^{(n - 1)})}{2} + \alpha^{(n)} \cdot \frac{q^{(n - 1)}(s^{(n - 1)}) - q^{(n - 1)}(- s^{(n - 1)})}{2 \cdot s^{(n - 1)}}
  $$

## Comparison of Two FRI Integration Approaches

Comparing the protocols in *The Missing Protocol PH23-PCS (Four)* and this article, the main difference is in the method used to prove the inner product. We'll refer to the protocol from *The Missing Protocol PH23-PCS (Four)* as Protocol 1, which uses the Grand Sum method for proving inner products and requires computing the class sum polynomial $z(X)$, constrained by three polynomials that must evaluate to 0 on $H$:

$$
\begin{aligned}
h_0(X) = &L_0(X)\cdot\big(z(X) - a_0\cdot c_0\big) \\
h_1(X) = &(X-1)\cdot\big(z(X)-z(\omega^{-1}\cdot X)-a(X)\cdot c(X)) \\
h_2(X) = &L_{N-1}(X)\cdot\big( z(X) - v \big) \\
\end{aligned}
$$

Protocol 2 (this article's protocol) uses the Univariate Sumcheck method, decomposing $a(X) \cdot c(X)$ to obtain $q_{ac}(X)$ and $g(X)$:

$$
a(X)\cdot c(X) = q_{ac}(X)\cdot v_H(X) + X\cdot g(X) + (v/N), \quad \deg(g)<N-1
$$

Let's compare their computational complexities:

Prover Computation:
- Protocol 1 additionally requires:
	- Computing $z(X), h_0(X), h_1(X), h_2(X)$
	- Computing commitment $C_z$
	- Computing $z(\zeta), z(\omega^{-1} \cdot \zeta)$
	- Computing $q_z(X)$

- Protocol 2 additionally requires:
	- Decomposing $a(X) \cdot c(X)$ to get $q_{ac}(X)$ and $g(X)$
	- Computing commitments $C_{q_{ac}}, C_{g}$
	- Computing $q_{ac}(\zeta), g(\zeta)$
	- Performing degree correction, computing $t'(X), q'_{ac}(X), g'(X)$
	- Computing $q_{q'_{ac}}(X), q_{g'}(X)$

By comparison, the difference in Prover computational complexity is not particularly significant.

Proof Size:
- Protocol 2 additionally sends:
	- One more polynomial commitment, $C_g$
	- In the FRI query phase, repeated $l$ times, it sends values and Merkle Paths for two more points
	
Protocol 2 has a larger proof size, requiring additional hash values and field elements, with the quantity related to the repetition count $l$.

Verifier Computation:
- Protocol 1 additionally requires:
	- Computing $L_0(\zeta), L_{N-1}(\zeta)$
	- Computing $h_0(\zeta), h_1(\zeta), h_2(\zeta)$
	Protocol 1's additional computation complexity is $2 ~ \mathbb{F}_{\mathsf{inv}} + 9 ~\mathbb{F}_{\mathsf{mul}}$.
- Protocol 2 additionally requires:
	- Verifying $a(\zeta)\cdot c(\zeta) \overset{?}{=} q_{ac}(\zeta)\cdot v_H(\zeta) + \zeta\cdot g(\zeta) + (v/N)$
	- Repeating $l$ times: verifying 2 more opening points, requiring hash calculations
	- Repeating $l$ times: computing degree-corrected polynomial values at corresponding points. For $x \in \{s^{(0)}, -s^{(0)}, \zeta\}$, computing $t'(x), g'(x), q_{ac}'(x)$ from $t(x), g(x), q_{ac}(x)$. Computing one value costs $2 ~ \mathbb{F}_{\mathsf{mul}}$, so the total complexity is $18l ~ \mathbb{F}_{\mathsf{mul}}$.
	
Protocol 1's Verifier computation is more efficient than Protocol 2's.

In summary, Protocol 2 requires handling 5 polynomials when interfacing with FRI: $a(X),c(X),t(X),q_{ac}(X),g(X)$, which is one more than Protocol 1. Additionally, these polynomials have inconsistent degrees, requiring degree correction for $t(X),q_{ac}(X),g(X)$ to reach degree $N-1$. Since the protocol initially commits to the original polynomials and requires additional operations for degree correction, this increases complexity during the FRI low degree test.

In the query phase, Protocol 2 needs to send proofs for one more polynomial at query points, repeated $l$ times, increasing the proof size. For the verifier, this means verifying more query point proofs and computing degree-corrected function values at query points, both related to $l$, increasing verification computational complexity.

Our analysis shows that the complexity of interfacing with the FRI protocol depends on the number of polynomials to handle and the number of opening points. Protocol 2 deals with more polynomials, resulting in larger proof sizes and higher verifier computational complexity compared to Protocol 1.

## References

- [PH23] Papini, Shahar, and Ulrich Haböck. "Improving logarithmic derivative lookups using GKR." Cryptology ePrint Archive (2023). https://eprint.iacr.org/2023/1284
- [H22] Haböck, Ulrich. "A summary on the FRI low degree test." _Cryptology ePrint Archive_ (2022).
- [BCIKS20] Eli Ben-Sasson, Dan Carmon, Yuval Ishai, Swastik Kopparty, and Shubhangi Saraf. Proximity Gaps for Reed–Solomon Codes. In *Proceedings of the 61st Annual IEEE Symposium on Foundations of Computer Science*, pages 900–909, 2020.