# Gemini: Interfacing with FRI

- Jade Xie  <jade@secbit.io>

The Gemini protocol [BCH+22] provides an approach for converting a multilinear polynomial PCS into a univariate polynomial commitment scheme. To briefly review, in order to prove that the opening value of an MLE polynomial at a certain point is v, it can be transformed into an inner product proof. This inner product proof is obtained by repeatedly performing operations similar to sumcheck or split-and-fold in the FRI protocol on a univariate polynomial. This further converts the inner product proof into proving that some univariate polynomials have correct values at certain random points. In the original Gemini paper, KZG10's univariate polynomial PCS was used to implement this proof. In fact, the univariate polynomial PCS can also use the FRI PCS scheme. One advantage of FRI PCS is that for openings of polynomials of different degrees at multiple points, they can be combined into one polynomial using random numbers, requiring only one call to FRI's low degree test to complete all these proofs.

Below, drawing on the description in Appendix B of the HyperPlonk paper [BBBZ23], we provide a detailed protocol for Gemini interfacing with FRI PCS.

## Protocol Description

Proof goal: For an MLE polynomial with n variables $\tilde{f}(X_0, X_1, \ldots, X_{n - 1})$, represented in coefficient form:

$$
\tilde{f}(X_0, X_1, \ldots, X_{n - 1}) = \sum_{i = 0}^{2^n - 1}c_i \cdot X_0^{i_0} X_1^{i_1} \cdots X_{n - 1}^{i_{n-1}}
$$

where $(i_0, i_1,\ldots,i_{n - 1})$ is the binary representation of $i$, with $i_0$ being the least significant bit of the binary representation, satisfying $i = \sum_{j=0}^{n-1}i_j 2^{j}$.

The goal of the proof is to prove that the value of $\tilde{f}(X_0, X_1, \ldots, X_{n - 1})$ at the point $\vec{u} = (u_0,u_1, \ldots, u_{n - 1})$ is $v = \tilde{f}(u_0,u_1, \ldots, u_{n - 1})$.

### Public Inputs

1. FRI protocol parameters: Reed-Solomon encoding domain $D_n \subset D_{n-1} \subset \cdots \subset D_0 = D$, code rate $\rho$, number of query rounds $l$.
2. Commitment to polynomial $f(X)$:

$$
C_f = \mathsf{cm}([f(x)|_{x \in D}]) = \mathsf{MT.commit}([f(x)|_{x \in D}]) 
$$

where $f(X)$ is a polynomial of degree $2^n - 1$, with the same coefficients $\vec{c}$ as $\tilde{f}$:

$$
f(X) = \sum_{i = 0}^{2^n - 1} c_i \cdot X^i
$$

3. Evaluation point $\vec{u} = (u_0,u_1, \ldots, u_{n - 1})$
4. $v = \tilde{f}(u_0,u_1, \ldots, u_{n - 1})$ 

### Witness

- Coefficients $\vec{c} = (c_0,c_1, \ldots, c_{2^n - 1})$ of the multivariate polynomial $\tilde{f}(X_0, X_1, \ldots, X_{n - 1})$

### Round 1

1. Prover sets $h_0(X) = f(X)$, computes folded polynomials $h_1(X), h_2(X), \ldots, h_{n-1}(X)$, such that for $i = 1, \ldots, n-1$:

$$
h_{i}(X^{2}) = \frac{h_{i - 1}(X) + h_{i - 1}(-X)}{2} + u_{i - 1} \cdot \frac{h_{i - 1}(X) - h_{i - 1}(-X)}{2X}
$$

2. Prover computes commitments $(C_{h_{1}},C_{h_{2}}, \ldots, C_{h_{n-1}})$, where for $i = 1, \ldots, n-1$:

$$
C_{h_{i}} = \mathsf{cm}([h_{i}(x)|_{x \in D}]) = \mathsf{MT.commit}([h_{i}(x)|_{x \in D})
$$

### Round 2

1. Verifier sends random number $\beta \stackrel{\$}{\leftarrow} \mathbb{F}^* \setminus D$
2. Prover computes $\{h_i(\beta), h_{i}(- \beta), h_i(\beta^2)\}_{i = 0}^{n-1}$ and sends to Verifier.

### Round 3

1. Verifier sends random number $r \stackrel{\$}{\leftarrow} \mathbb{F}$
2. First perform degree correction on each polynomial $h_{i}(X)(i = 1, \ldots, n)$ to align degrees to $2^{n}- 1$. The degree of each polynomial is $\deg(h_i)=2^{n-i}-1$. For $i = 1, \ldots, n - 1$, compute $h'_i(X)$:

Method 1:

$$
h'_i(X)=h_i(X)+r\cdot X^{2^{n} - 2^{n-i}} \cdot h_i(X)
$$

Method 2: If using the degree correction method from the STIR paper [ACFY24]:

$$
h'_i(X)=\sum_{j = 0}^{2^{n}- 2^{n - i}} r^{j} \cdot X^{j} \cdot h_i(X)=h_i(X)+r\cdot X \cdot h_i(X)+r^{2} \cdot X^2 \cdot h_i(X) + \ldots + r^{2^n - 2^{n-i}} \cdot X^{2^n - 2^{n-i}} \cdot h_i(X)
$$

> 📝 **Notes**
>
> Method 2 provides higher security compared to Method 1. ([ACFY24, 2.3])

3. Batch $h_0(X)$ with $h_1'(X), \ldots, h_{n-1}'(X)$ using powers of the random number $r$:

Method 1: Compute

$$
\begin{align*}
h^*(X) & = h_0(X) + r^{1 + (0)} \cdot h_1'(X) + r^{2 + (0 + 1)} \cdot h_2'(X) + r^{3 + (0 + 1 + 1)} \cdot h_3'(X)+ \ldots + r^{n - 1 + (0 + 1 \cdot (n - 2))} \cdot h_{n-1}'(X) \\
& = h_0(X) + r \cdot h_1'(X) + r^{3} \cdot h_2'(X) + r^{5} \cdot h_3'(X)+ \ldots + r^{2n-3} \cdot h_{n-1}'(X) 
\end{align*} \tag{1}
$$

Method 2: If using the degree correction method from the STIR paper, compute the batched polynomial as:

$$
\begin{align*}
h^*(X) & = h_0(X) + r^{1 + (0)} \cdot h_1'(X) + r^{2 + (0 + e_1)} \cdot h_2'(X) + r^{3 + (0 + e_1 + e_2)} \cdot h_3'(X)\\
& \quad + \ldots + r^{n - 1 + (0 + e_1 + e_2 + \ldots + e_{n-2})} \cdot h_{n-1}'(X) \\
& = h_0(X) + r \cdot h_1'(X) + r^{2 + 2^n - 2^{n -1}} \cdot h_2'(X) + r^{2 + \sum_{i=1}^{2}(2^n-2^i)} \cdot h_3'(X) \\
& \quad + \ldots + r^{n - 1+\sum_{i=1}^{n-2}(2^n-2^i)} \cdot h_{n-1}'(X) 
\end{align*} \tag{2}
$$

4. Compute quotient polynomial $q'(X)$ to verify if $h^*(X)$ opens correctly at points $(\beta,-\beta,\beta^2)$:

$$
q'(X) = \frac{h^*(X)-h^*(\beta)}{X-\beta} + \frac{h^*(X)-h^*(-\beta)}{X+\beta} + \frac{h^*(X)-h^*(\beta^2)}{X-\beta^2}
$$

The construction of this quotient polynomial refers to the Multi-point queries section in paper [H22].

### Round 4

This round aligns the quotient polynomial $q'(X)$ to a power of 2 to interface with the FRI protocol.

1. Verifier sends random number $\lambda \stackrel{\$}{\leftarrow} \mathbb{F}$
2. Prover computes 

$$
q(X) = (1 + \lambda \cdot X) q'(X)
$$

on domain $D$.

### Round 5

Prover and Verifier engage in FRI's low degree test proof interaction to prove that the degree of $q(X)$ is less than $2^n$:

$$
\pi_{q} = \mathsf{FRI.LDT}(q(X), 2^n)
$$

This includes $n$ rounds of interaction, until the original polynomial is folded into a constant polynomial. Using $i$ to represent the $i$-th round, the specific interaction process is as follows:

- Let $q^{(0)}(x)|_{x \in D} := q(x)|_{x \in D}$
- For $i = 1,\ldots, n$:
  - Verifier sends random number $\alpha^{(i)}$
  - For any $y \in D_i$, find $x$ in $D_{i - 1}$ satisfying $x^2 = y$, Prover computes

  $$
    q^{(i)}(y) = \frac{q^{(i - 1)}(x) + q^{(i - 1)}(-x)}{2} + \alpha^{(i)} \cdot \frac{q^{(i - 1)}(x) - q^{(i - 1)}(-x)}{2x}
  $$

  
  - If $i < n$, Prover sends Merkle Tree commitment of $[q^{(i)}(x)|_{x \in D_{i}}]$:
  
  $$
  \mathsf{cm}(q^{(i)}(X)) = \mathsf{cm}([q^{(i)}(x)|_{x \in D_{i}}]) = \mathsf{MT.commit}([q^{(i)}(x)|_{x \in D_{i}}])
  $$

  - If $i = n$, choose any $x_0 \in D_{n}$, Prover sends the value of $q^{(i)}(x_0)$.

> 📝 **Notes**
>
> If the number of folds $r < n$, then it will not fold to a constant polynomial at the end. Therefore, Prover will send a Merkle Tree commitment in the $r$-th round, instead of sending a value.

### Round 6

This round continues the FRI protocol's low degree test interaction between Prover and Verifier in the query phase. Verifier repeats the query $l$ times. Each time, Verifier selects a random number from $D_0$ and asks Prover to send the folded value in the $i$-th round and the corresponding Merkle Path, allowing Verifier to verify the correctness of each round of folding.

Repeat $l$ times:
- Verifier randomly selects a number $s^{(0)} \stackrel{\$}{\leftarrow} D_0$ from $D_0$
- Prover opens the commitments of $\{h_i(s^{(0)})\}_{i = 0}^{n-1}$ and $\{h_i(-s^{(0)})\}_{i = 0}^{n-1}$, i.e., the values at these points and their corresponding Merkle Paths, and sends them to Verifier
  
  $$
  \{(h_i(s^{(0)}), \pi_{h_i}(s^{(0)}))\}_{i = 0}^{n-1} \leftarrow \{\mathsf{MT.open}([h_i(x)|_{x \in D_0}], s^{(0)})\}_{i = 0}^{n-1}
  $$

$$
  \{(h_i(-s^{(0)}), \pi_{h_i}(-s^{(0)}))\}_{i = 0}^{n-1} \leftarrow \{\mathsf{MT.open}([h_i(x)|_{x \in D_0}], -s^{(0)})\}_{i = 0}^{n-1}
$$

- Prover computes $s^{(1)} = (s^{(0)})^2$ 
- For $i = 1, \ldots, n - 1$
  - Prover sends the values of $q^{(i)}(s^{(i)}), q^{(i)}(-s^{(i)})$, along with their Merkle Paths.
  
  $$
  \{(q^{(i)}(s^{(i)}), \pi_{q^{(i)}}(s^{(i)}))\} \leftarrow \mathsf{MT.open}([q^{(i)}(x)|_{x \in D_i}], s^{(i)})
  $$
$$
  \{(q^{(i)}(-s^{(i)}), \pi_{q}^{(i)}(-s^{(i)}))\} \leftarrow \mathsf{MT.open}([q^{(i)}(x)|_{x \in D_i}], -s^{(i)})
  $$
  - Prover computes $s^{(i + 1)} = (s^{(i)})^2$

> If the number of folds $r < n$, then in the last step, the value of $q^{(r)}(s^{(r)})$ should be sent along with its Merkle Path.

### Proof

The proof sent by Prover is:

$$
\pi = (C_{h_{1}},C_{h_{2}}, \ldots, C_{h_{n-1}}, \{h_i(\beta), h_{i}(- \beta), h_i(\beta^2)\}_{i = 0}^{n-1}, \pi_{q})
$$

Using the symbol $\{\cdot\}^l$ to represent the proof generated by repeating the query $l$ times in the FRI low degree test query phase. Since each query is randomly selected, the proof in braces is also random. Then the proof of FRI's low degree test is:

$$
\begin{aligned}
  \pi_{q} = &  ( \mathsf{cm}(q^{(1)}(X)), \ldots, \mathsf{cm}(q^{(n - 1)}(X)),q^{(n)}(x_0),  \\
  & \, \{h_0(s^{(0)}), \pi_{h_0}(s^{(0)}), h_0(- s^{(0)}), \pi_{h_0}(-s^{(0)}), \cdots ,\\
  & \quad h_{n-1}(s^{(0)}), \pi_{h_{n-1}}(s^{(0)}), h_{n-1}(- s^{(0)}), \pi_{h_{n-1}}(-s^{(0)}), \\
  & \quad q^{(1)}(s^{(1)}), \pi_{q^{(1)}}(s^{(1)}),q^{(1)}(-s^{(1)}), \pi_{q^{(1)}}(-s^{(1)}), \ldots, \\
  & \quad q^{(n - 1)}(s^{(n - 1)}), \pi_{q^{(n - 1)}}(s^{(n - 1)}),q^{(n - 1)}(-s^{(n - 1)}), \pi_{q^{(i)}}(-s^{(n - 1)})\}^l)
\end{aligned}
$$

### Verification

1. Verifier verifies if the folding process is correct. For $i = 1, \ldots, n - 1$, calculate and verify based on the values sent by Prover:

$$
h_{i}(\beta^{2}) \stackrel{?}{=} \frac{h_{i - 1}(\beta) + h_{i - 1}(-\beta)}{2} + u_{i - 1} \cdot \frac{h_{i - 1}(\beta) - h_{i - 1}(-\beta)}{2\beta}
$$

2. Verifier verifies if it finally folds to the constant $v$, verify:

$$
\frac{h_{n - 1}(\beta) + h_{n - 1}(-\beta)}{2} + u_{n - 1} \cdot \frac{h_{n - 1}(\beta) - h_{n - 1}(-\beta)}{2\beta} \stackrel{?}{=} v
$$

3. Verify the low degree test proof of $q(X)$:

$$
\mathsf{FRI.LDT.verify}(\pi_{q}, 2^n) \stackrel{?}{=} 1
$$

The specific verification process is, repeat $l$ times:
- Verify the correctness of $\{h_i(s^{(0)})\}_{i = 0}^{n-1}$ and $\{h_i(-s^{(0)})\}_{i = 0}^{n-1}$. For $i = 0, \ldots, n - 1$, verify:

$$
\mathsf{MT.verify}(\mathsf{cm}(h_i(X)), h_i(s^{(0)}), \pi_{h_i}(s^{(0)})) \stackrel{?}{=} 1
$$

$$
\mathsf{MT.verify}(\mathsf{cm}(h_i(X)), h_i(-s^{(0)}), \pi_{h_i}(-s^{(0)})) \stackrel{?}{=} 1
$$

- Verifier calculates the values of $h^*(s^{(0)})$ and $h^*(-s^{(0)})$ based on $\{h_i(s^{(0)})\}_{i = 0}^{n-1}$ and $\{h_i(-s^{(0)})\}_{i = 0}^{n-1}$, calculates $h^*(\beta), h^*(-\beta), h^*(\beta^2)$ based on $\{h_i(\beta)\}_{i = 0}^{n-1}, \{h_i(-\beta)\}_{i = 0}^{n-1}, \{h_i(\beta^2)\}_{i = 0}^{n-1}$. For $x \in \{s^{(0)}, -s^{(0)}, \beta, -\beta, \beta^2\}$, Verifier calculates $h^*(x)$ as follows:

Method 1: For $i = 1, \ldots, n - 1$, calculate:

$$
h'_i(x)=h_i(x)+r\cdot (x)^{2^{n} - 2^{n-i}} \cdot h_i(x)
$$

Then calculate:

$$
\begin{align*}
h^*(x) & = h_0(x) + r \cdot h_1'(x) + r^{3} \cdot h_2'(x) + r^{5} \cdot h_3'(x)+ \ldots + r^{2n-3} \cdot h_{n-1}'(x) 
\end{align*} 
$$

Method 2: If using the degree correction method from the STIR paper [ACFY24], for $i = 1, \ldots, n - 1$, calculate:

$$
h'_i(x)=\sum_{j = 0}^{2^{n}- 2^{n - i}} r^{j} \cdot (x)^{j} \cdot h_i(x) = \begin{cases}
 h_i(x) \cdot \frac{1 - (r \cdot x)^{2^n - 2^{n-i} + 1}}{1 - r \cdot x} & \text{if } r \cdot x \neq 0\\
h_i(x) \cdot (2^n - 2^{n-i} + 1) & \text{if } r \cdot x = 0
\end{cases}
$$

Then calculate:

$$
\begin{align*}
h^*(x) & = h_0(x) + r \cdot h_1'(x) + r^{2 + 2^n - 2^{n -1}} \cdot h_2'(x) + r^{2 + \sum_{i=1}^{2}(2^n-2^i)} \cdot h_3'(x) \\
& \quad + \ldots + r^{n - 1+\sum_{i=1}^{n-2}(2^n-2^i)} \cdot h_{n-1}'(x) 
\end{align*} 
$$

- Verifier calculates:
  $$
  q'(s^{(0)}) = \frac{h^*(s^{(0)})-h^*(\beta)}{s^{(0)}-\beta} + \frac{h^*(s^{(0)})-h^*(-\beta)}{s^{(0)}+\beta} + \frac{h^*(s^{(0)})-h^*(\beta^2)}{s^{(0)}-\beta^2}
  $$

$$
  q'(-s^{(0)}) = \frac{h^*(-s^{(0)})-h^*(\beta)}{-s^{(0)}-\beta} + \frac{h^*(-s^{(0)})-h^*(-\beta)}{-s^{(0)}+\beta} + \frac{h^*(-s^{(0)})-h^*(\beta^2)}{-s^{(0)}-\beta^2}
$$

- Verifier calculates:

$$
q^{(0)}(s^{(0)}) = (1 + \lambda \cdot s^{(0)}) q'(s^{(0)})
$$

$$
q^{(0)}(-s^{(0)}) = (1 - \lambda \cdot s^{(0)}) q'(-s^{(0)})
$$

- Verify the correctness of $q^{(1)}(s^{(1)}), q^{(1)}(-s^{(1)})$:

$$
\mathsf{MT.verify}(\mathsf{cm}(q^{(1)}(X)), q^{(1)}(s^{(1)}), \pi_{q^{(1)}}(s^{(1)})) \stackrel{?}{=} 1
$$

$$
\mathsf{MT.verify}(\mathsf{cm}(q^{(1)}(X)), q^{(1)}(-s^{(1)}), \pi_{q^{(1)}}(-s^{(1)})) \stackrel{?}{=} 1
$$

- Verify if the folding in the 1st round is correct:

$$
q^{(1)}(s^{(1)}) \stackrel{?}{=} \frac{q^{(0)}(s^{(0)}) + q^{(0)}(- s^{(0)})}{2} + \alpha^{(1)} \cdot \frac{q^{(0)}(s^{(0)}) - q^{(0)}(- s^{(0)})}{2 \cdot s^{(0)}}
$$

- For $i = 2, \ldots, n - 1$
  - Verify the correctness of $q^{(i)}(s^{(i)}), q^{(i)}(-s^{(i)})$:

  $$
  \mathsf{MT.verify}(\mathsf{cm}(q^{(i)}(X)), q^{(i)}(s^{(i)}), \pi_{q^{(i)}}(s^{(i)})) \stackrel{?}{=} 1
  $$

  $$
  \mathsf{MT.verify}(\mathsf{cm}(q^{(i)}(X)), q^{(i)}(-s^{(i)}), \pi_{q^{(i)}}(-s^{(i)})) \stackrel{?}{=} 1
  $$
  
  - Verify if the folding in the $i$-th round is correct:
  
  $$
  q^{(i)}(s^{(i)}) \stackrel{?}{=} \frac{q^{(i-1)}(s^{(i - 1)}) + q^{(i - 1)}(- s^{(i - 1)})}{2} + \alpha^{(i)} \cdot \frac{q^{(i - 1)}(s^{(i - 1)}) - q^{(i - 1)}(- s^{(i - 1)})}{2 \cdot s^{(i - 1)}}
  $$
  
- Verify if it finally folds to a constant polynomial:

  $$
  q^{(n)}(x_0) \stackrel{?}{=} \frac{q^{(n-1)}(s^{(n - 1)}) + q^{(n - 1)}(- s^{(n - 1)})}{2} + \alpha^{(n)} \cdot \frac{q^{(n - 1)}(s^{(n - 1)}) - q^{(n - 1)}(- s^{(n - 1)})}{2 \cdot s^{(n - 1)}}
  $$

## Reference

- [BCH+22] Bootle, Jonathan, Alessandro Chiesa, Yuncong Hu, *_et al. "Gemini: Elastic SNARKs for Diverse Environments."_ Cryptology ePrint Archive* (2022). [https://eprint.iacr.org/2022/420](https://eprint.iacr.org/2022/420) 
- [BBBZ23] Chen, Binyi, Benedikt Bünz, Dan Boneh, and Zhenfei Zhang. "Hyperplonk: Plonk with linear-time prover and high-degree custom gates." In _Annual International Conference on the Theory and Applications of Cryptographic Techniques_, pp. 499-530. Cham: Springer Nature Switzerland, 2023.
- [H22] Haböck, Ulrich. "A summary on the FRI low degree test." _Cryptology ePrint Archive_ (2022).
- [ACFY24] Arnon, Gal, Alessandro Chiesa, Giacomo Fenzi, and Eylon Yogev. "STIR: Reed-Solomon proximity testing with fewer queries." In _Annual International Cryptology Conference_, pp. 380-413. Cham: Springer Nature Switzerland, 2024.