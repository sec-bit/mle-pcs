# Comparison of MLE-PCS (Final Report)

Last update: 2025-06-12
## Background

Polynomial Commitment Schemes (PCS) are important components in many zkSNARK (zero-knowledge Succinct Non-interactive ARguments of Knowledge) systems. A Prover can commit to a polynomial and later prove to a Verifier that the value of this polynomial at a publicly disclosed opening point is correct.

![zkSNARK](img/zksnark.png)
Initially, schemes like [KZG10] only supported univariate polynomials. Assuming a univariate polynomial with $N$ coefficients, the Prover's computational complexity was $O(N \log N)$. Recently, many SNARK proof systems have begun using Multilinear Polynomial Commitment Schemes (MLE-PCS), such as Hyperplonk[CBBZ22]. For a multilinear polynomial with $N$ coefficients, the Prover's computational complexity can achieve linearity, i.e., $O(N)$. MLE-PCS can not only construct more efficient proof systems, but the representation of multilinear polynomials also brings other benefits, such as efficient split-and-fold on Hypercubes, better support for high-degree constraints, and more flexible decomposition.

This project **MLE-PCS** focuses on researching and comparing different multilinear polynomial commitment schemes, including their design, security assumptions, and efficiency.

## MLE-PCS Overview

For an $n$-variate linear polynomial $\tilde{f}(X_0, X_1, \ldots, X_{n - 1})$, there are two forms of representation:

1. Coefficients form

A multilinear polynomial can be represented in terms of coefficients as follows:

$$
\tilde{f}(X_0, X_1, \ldots, X_{n - 1}) = c_0 + c_1 X_0 + c_2 X_1 + \ldots + c_{2^n - 1} X_0 X_1 \cdots X_{n - 1}
$$

where $\{c_i\}_{0  \le i \le 2^{n} - 1}$ are the coefficients of the multilinear polynomial.

2. Evaluations form

A multilinear polynomial can also be represented by its values on the Boolean Hypercube $B_n = \{0,1\}^n$, as:

$$
\tilde{f}(X_0, X_1, \ldots, X_{n - 1}) = \sum_{i = 0}^{2^n - 1} \tilde{f}(\mathsf{bits}(i)) \cdot \tilde{eq}(\mathsf{bits}(i), (X_0, X_1, \ldots, X_{n - 1}))
$$

Here, $\mathsf{bits}(i) = (i_0, i_1, \ldots, i_{n-1})$ represents the binary representation of $i$ as a vector, with the first component $i_0$ being the least significant bit in the binary representation, i.e., Little-endian. For example, when $n = 3$, the binary representation of $3$ is $011$, so the vector $\mathsf{bits}(3) = (1,1,0)$. $\tilde{eq}(\mathsf{bits}(i), (X_0, X_1, \ldots, X_{n - 1}))$ is the Lagrange polynomial on the Boolean Hypercube $B_n = \{0,1\}^n$, defined as:

$$
\tilde{eq}(\mathsf{bits}(i), (X_0, X_1, \ldots, X_{n - 1})) = \prod_{j = 0}^{n - 1} ((1 - i_j)(1 - X_j) + i_j X_j)
$$

In the MLE-PCS commitment protocol, the Prover first commits to the multilinear polynomial $\tilde{f}$ to the Verifier. Subsequently, in the Evaluation proof protocol, the Prover proves to the Verifier that the value of $\tilde{f}$ at a public point $\vec{u} = (u_0, \ldots, u_{n - 1})$ is $v$, i.e., proving that $\tilde{f}(u_0, \ldots, u_{n - 1}) = v$.

Some MLE-PCS protocols are described in Evaluations Form, while others are described in Coefficients Form. This naturally creates a form conversion problem. For example, if a multilinear polynomial is given in coefficient form, it would need to be converted to Evaluation form using an algorithm similar to FFT to adapt to protocols described in Evaluation form. However, many authors have noted that this FFT conversion is not necessary to adapt to such protocols. Taking the Basefold [ZCF23] protocol as an example, in the original paper [ZCF23], the protocol is described in coefficients, but Ulrich Haböck in paper [H24] described the Basefold protocol in Evaluations form. Based on the original Basefold protocol, only the folding form in the FRI protocol needs to be changed. For more on this conversion, see the note [An Alternative Folding Method](https://github.com/sec-bit/mle-pcs/blob/main/basefold/basefold-03.md#an-alternative-folding-method).

This project describes the basic principles of many MLE-PCS, and for some protocols, we have also supplemented protocol descriptions in alternative forms of multilinear polynomial representation. The table below lists the MLE-PCS covered in this project.

| Scheme        | Paper      | Notes                                                                                                                                                                                                                                                                                                                                                                            |
| ------------- | ---------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| PST13         | [XZZPS19]  | [Notes on Libra-PCS](https://github.com/sec-bit/mle-pcs/blob/main/libra-pcs/libra-pcs.md)                                                                                                                                                                                                                                                                                        |
| zeromorph     | [KT23]     | [Notes on Zeromorph](https://github.com/sec-bit/mle-pcs/blob/main/zeromorph/zeromorph.md), [Zeromorph-PCS (Part II)](https://github.com/sec-bit/mle-pcs/blob/main/zeromorph/zeromorph-02.md)                                                                                                                                                                                     |
| zeromorph-fri | ⭐          | [Zeromorph-PCS: Integration with FRI](https://github.com/sec-bit/mle-pcs/blob/main/zeromorph/zeromorph-fri.md)                                                                                                                                                                                                                                                                   |
| gemini        | [BCH+22]   | [Gemini-PCS (Part I)](https://github.com/sec-bit/mle-pcs/blob/main/gemini/Gemini-PCS-1.md),[Gemini-PCS (Part II)](https://github.com/sec-bit/mle-pcs/blob/main/gemini/Gemini-PCS-2.md),[Gemini-PCS (Part III)](https://github.com/sec-bit/mle-pcs/blob/main/gemini/Gemini-PCS-3.md), [Gemini-PCS (Part IV)](https://github.com/sec-bit/mle-pcs/blob/main/gemini/Gemini-PCS-4.md) |
| gemini-fri    | ⭐          | [Gemini: Interfacing with FRI](https://github.com/sec-bit/mle-pcs/blob/main/gemini/gemini-fri.md)                                                                                                                                                                                                                                                                                |
| hyperKZG      | N/A        | [Notes on HyperKZG](https://github.com/sec-bit/mle-pcs/blob/main/gemini/hyperkzg-pcs-01.md)                                                                                                                                                                                                                                                                                      |
| PH23-KZG      | [PH23]     | [The Missing Protocol PH23-PCS (Part 1)](https://github.com/sec-bit/mle-pcs/blob/main/ph23/ph23-pcs-01.md), [Missing Protocol PH23-PCS (Part 2)](https://github.com/sec-bit/mle-pcs/blob/main/ph23/ph23-pcs-02.md)                                                                                                                                                               |
| PH23-fri      | ⭐          | [The Missing Protocol PH23-PCS (Part 4)](https://github.com/sec-bit/mle-pcs/blob/main/ph23/ph23-pcs-fri-01.md),[The Missing Protocol PH23-PCS (Part 5)](https://github.com/sec-bit/mle-pcs/blob/main/ph23/ph23-pcs-fri-02.md)                                                                                                                                                    |
| Mercury       | [EG25]     | [Mercury Notes: Implementing Constant Proof Size](https://github.com/sec-bit/mle-pcs/blob/main/mercury/mercury-01.md), [Mercury Notes: Integration with KZG](https://github.com/sec-bit/mle-pcs/blob/main/mercury/mercury-02.md)                                                                                                                                                 |
| Samaritan     | [GPS25]    |                                                                                                                                                                                                                                                                                                                                                                                  |
| Virgo         | [ZXZS19]   | [Notes on Virgo-PCS](https://github.com/sec-bit/mle-pcs/blob/main/virgo-pcs/virgo-pcs-01.md)                                                                                                                                                                                                                                                                                     |
| Hyrax         | [WTSTW18]  | [Notes on Hyrax-PCS](https://github.com/sec-bit/mle-pcs/blob/main/hyrax-pcs/hyrax-01.md)                                                                                                                                                                                                                                                                                         |
| Basefold      | [ZCF23]    | [Notes on Basefold (Part I): Foldable Linear Codes](https://github.com/sec-bit/mle-pcs/blob/main/basefold/basefold-01.md), [Notes on Basefold (Part II): IOPP](https://github.com/sec-bit/mle-pcs/blob/main/basefold/basefold-02.md), [Notes on Basefold (Part III): MLE Evaluation Argument](https://github.com/sec-bit/mle-pcs/blob/main/basefold/basefold-03.md)              |
| Basefold      | ⭐          | [An Alternative Folding Method](https://github.com/sec-bit/mle-pcs/blob/main/basefold/basefold-03.md#an-alternative-folding-method)                                                                                                                                                                                                                                              |
| Deepfold      | [GLHQTZ24] | [Note on DeepFold: Protocol Overview](https://github.com/sec-bit/mle-pcs/blob/main/fri/deepfold.md)                                                                                                                                                                                                                                                                              |
| Ligerito      | [NA25]     | [Ligerito-PCS Notes](https://github.com/sec-bit/mle-pcs/blob/main/ligerito-pcs/ligerito-01.md)                                                                                                                                                                                                                                                                                   |
| WHIR          | [ACFY24b]  | [Note on WHIR: Reed-Solomon Proximity Testing with Super-Fast Verification](https://github.com/sec-bit/mle-pcs/blob/main/fri/whir.md)                                                                                                                                                                                                                                            |
| FRI-Binius    | [DP24]     | [Notes on FRI-Binius (Part I): Binary Towers](https://github.com/sec-bit/mle-pcs/blob/main/fri-binius/binius-01.md), [Notes on Binius (Part II): Subspace Polynomial](https://github.com/sec-bit/mle-pcs/blob/main/fri-binius/binius-02.md)                                                                                                                                      |
| Greyhound     | [NS24]     | [Greyhound Commitment](https://github.com/sec-bit/mle-pcs/blob/main/grey-hound/greyhound_pcs.md)                                                                                                                                                                                                                                                                                 |
| Σ-Check       | [GQZGX24]  | https://eprint.iacr.org/2024/1654.pdf                                                                                                                                                                                                                                                                                                                                            |
| Hyperwolf     | [ZGX25]    | https://eprint.iacr.org/2025/922                                                                                                                                                                                                                                                                                                                                                 |

NOTE: Items marked with "⭐️" in the Remarks column represent new protocol descriptions added in this project.

### Classification by Commitment Protocols

All MLE-PCS protocols are extended from Univariate PCS or built directly on them.

For a univariate polynomial $f(X)$,

$$
f(X) = a_0 + a_1 X + a_2 X^2 + \ldots + a_{N-1}X^{N-1}
$$

Different ways of committing to $f(X)$ correspond to different Univariate PCS.

| Commitments         | Algebra                   | Schemes                                                                                            |
| ------------------- | ------------------------- | -------------------------------------------------------------------------------------------------- |
| KZG10               | Paring Friendly ECC based | PST13(mKZG or Liba-PCS), Zeromorph, Gemini, HyperKZG, PH23-KZG, Mercury, Samaritan                 |
| Merkle Tree         | Linear code based         | Ligero, Virgo, Basefold, Deepfold, WHIR, PH23-fri, Zeromorph-fri, Gemini-fri, Ligerito, FRI-Binius |
| Pedersen Commitment | ECC based                 | Hyrax, Σ-Check                                                                                     |
| Ajtai Commitment    | Lattice based             | Greyhound, Hyperwolf                                                                               |

#### KZG10

KZG10 polynomial commitment requires a Trusted Setup to produce a set of vectors with internal algebraic structure,

$$
(G_0, G_1, \ldots, G_{N-1}, H_0, H_1) = (G, \gamma G, \gamma^2 G, \ldots, \gamma^{N- 1} G, H, \gamma H)
$$

Here, $\gamma$ is a random number generated through Trusted Setup, which must not be leaked after generation. $G, H$ are generators on elliptic curve groups $\mathbb{G}_1, \mathbb{G}_2$ respectively, and there exists a bilinear mapping between them: $e: \mathbb{G}_1\times \mathbb{G}_2 \rightarrow \mathbb{G}_T$.

The commitment to polynomial $f(X)$ is:

$$
\begin{align}
C_{f(X)}  & = a_0 G_0 + a_1 G_1 + \ldots + a_{N - 1}G_{N - 1} \\
 & = a_0 G + a_1 \gamma G + \ldots + a_{N-1} \gamma^{N - 1} G \\
 & = f(\gamma) G
\end{align}
$$

The commitment $C_{f(X)}$ is exactly $f(\gamma)G$. To construct a PCS using KZG10, such as creating an opening proof for $f(\zeta) = y$, one needs to prove that there exists a quotient polynomial $q(X)$ satisfying:

$$
f(X) = q(X) \cdot (X - \zeta) + y
$$

The Prover can provide the commitment $C_{q(X)}$ to $q(X)$ as the opening proof for $f(\zeta) = y$. Using the additive homomorphic property of commitments and bilinear mapping, the Verifier can verify the divisibility relationship on $\mathbb{G}_T$:

$$
e(C_{f(X)} - y \cdot G, H) \overset{?}{=} e(C_{q(X)} , \gamma H - \zeta H)
$$

From the above description, it can be seen that the KZG10 commitment scheme has the following characteristics:
- Requires a trusted setup to generate public parameters with a specific algebraic structure.
- Uses bilinear mapping on elliptic curves to verify opening proofs.
- The opening proof verification requires only one group element, which often makes the proof size constant.

#### Merkle Tree

Merkle Tree-based commitments do not require a Trusted Setup and are based on the properties of Linear Codes. Taking the FRI protocol as an example, to commit to $f(X)$, the Prover sends the Reed-Solomon Code of $f(X)$ to the Verifier in the form of a Merkle Tree. Specifically, let $H \subset \mathbb{F}_q$ be a multiplicative group of order $2^k (k \in \mathbb{N})$, and the rate of the Reed-Solomon Code be $\rho$. The Reed-Solomon Code of $f(X)$ is the values of $f(X)$ on $H$, forming a vector:

$$
[f(x)|_{x \in H}]
$$

The elements of this vector, or their hash values, serve as the leaf nodes of the Merkle Tree, and the root of this Merkle Tree is the commitment to $f(X)$.

To prove $f(\zeta) = y$ (for $\zeta \notin H$), taking the FRI protocol to construct a PCS as an example [H22], one proves:

$$
f^{(0)}(X) =\frac{f(X) - y}{X - \zeta} + \lambda \cdot X \cdot \frac{f(X) - y}{X - \zeta}
$$

with degree less than $N$, where $\lambda \leftarrow \mathbb{F}_q$ is a random number sent by the Verifier. The Prover first encodes $f^{(0)}(X)$ on $H$ using Reed-Solomon, commits to the encoded vector using a Merkle Tree, and then the Prover and Verifier proceed with the FRI protocol. In the Query phase of the protocol, if leaf nodes on the Merkle Tree need to be opened, the Prover must send the corresponding Merkle Paths as proof.

Protocols using Merkle Trees as commitment schemes have the following characteristics:
- Do not require trusted setup.
- Commitment computation mainly relies on hash, which has less computational overhead compared to KZG10 since KZG10 requires operations on elliptic curves.
- Prover needs to send Merkle Paths during the proof process, making the proof size larger than KZG10 in most cases.

#### Pedersen Commitment

Pedersen Commitment is another commitment scheme based on elliptic curves. Unlike KZG10, Pedersen Commitment doesn't require a Trusted Setup to generate vectors with specific algebraic structures. Instead, it uses a Hash-to-point algorithm to generate a set of random elliptic curve group elements:

$$
G_0, G_1, \ldots, G_{M-1}, H_0 \leftarrow \mathbb{G}
$$

With these elements, we can commit to a vector $\vec{a}$ of length $N<M$:

$$
\mathsf{cm}(\vec{a}) = a_0 G_0 + a_1 G_1 + \ldots + a_{N-1} G_{N-1}
$$

If the Prover can also generate a random factor $\rho\leftarrow \mathbb{F}$, then the Pedersen commitment is Perfectly Hiding:

$$
\mathsf{cm}(\vec{a}) = a_0 G_0 + a_1 G_1 + \ldots + a_{N-1} G_{N-1} + \rho H_0
$$

Although these random group points have no internal structure, we can still prove that the vector behind the commitment satisfies certain properties. One of the most typical is the inner product proof:

$$
\langle \vec{a}, \vec{b} \rangle = v
$$

We can typically use either the Bulletproof approach or the ∑-Check approach to prove the inner product. Based on inner product proofs, we can also prove Hadamard products of vectors, or even more complex matrix multiplications. The biggest issue with this commitment scheme is that the Verifier's computational complexity is $O(N)$, but we can still use amortization or recursive proof techniques to mitigate the Verifier's computational burden.

Protocols that use Pedersen Commitment as their commitment scheme have the following characteristics:

- No Trusted Setup required.
- Commitment computation primarily relies on elliptic curve multiplication.
- Using Bulletproof-based inner product proofs, the proof size is $O(\log(N))$, but the Verifier's computational complexity is $O(N)$.

#### Ajtai Commitment

Ajtai commitment is a lattice-based commitment method with post-quantum security. Assuming the vector to be committed is $\vec{a}$, Ajtai commitment first selects an $n \times m$-size matrix $G$ (similar to the group element in Pedersen commitment), and computes 
$$
\mathsf{cm}(\vec{a}) = G \vec{a}
$$ 
to get the commitment result $\vec{t}$. 

The key differences between Ajtai commitments and Pedersen commitments are:

1. Ajtai commitment requires that the committed content $\vec{a}$ must be "small enough", meaning there is an upper bound $B$ such that for all $a_i$, $|a_i| < B$. This is due to the hardness requirements of the SIS/LWE problem, and only under this condition can the binding/hiding properties of Ajtai commitment be reduced to the SIS/LWE problem. To commit to polynomials with arbitrary coefficients, a common method is to split each coefficient into smaller but longer arrays (such as binary representation), and then commit to the split result. This satisfies the $< B$ requirement. Similarly, during opening, an additional step is needed to recover the original coefficients by computing the inner product of the binary vector with $(1, 2, 2^2, \cdots)$.
2. Since the result of Ajtai commitment is itself a vector, implementing "commitment-of-commitment" becomes very easy. That is, after splitting, multiple commitments can again undergo Ajtai commitment. This technique is widely used in lattice designs to further reduce proof volume.

To improve efficiency, many implementations use polynomial rings to implement Ajtai commitment (note that the polynomial ring here is unrelated to the polynomials in polynomial commitments), where the elements of vectors/matrices are ring elements. This more general case allows the security of Ajtai commitment to be reduced to the M-SIS/M-LWE problem.

Protocols that use Ajtai Commitment as their commitment scheme have the following characteristics:

- No Trusted Setup required.
- Commitment computation primarily relies on matrix multiplication.
- An additional norm check for the opening is required.
- Using LaBRADOR-based inner product proofs, the proof size is $O(\log(N))$, but the Verifier's computational complexity is $O(N)$.

### Classification by Evaluation Proof Principles

Based on different implementation methods, MLE-PCS can be categorized as follows:

| Principle         | Schemes                        |
|-------------------|--------------------------------|
| Quotienting       | PST13(Libra-PCS), Zeromorph, Zeromorph-FRI    |    
| Sumcheck          | Basefold, Deepfold, WHIR, Ligerito, FRI-Binius |  
| Split-and-fold    | Gemini, HyperKZG, Gemini-fri, Hyperwolf |
| Inner-product     | Ligero, Hyrax, Σ-Check, PH23-kzg, Virgo-PCS, Mercury, Samaritan,  GreyHound | 

#### Quotienting

MLE-PCS aims to prove that a multilinear polynomial $\tilde{f}(X_0, \ldots, X_{n - 1})$ at a public point $(u_0, \ldots, u_{n - 1})$ has a value of $v$, i.e., proving that $\tilde{f}(u_0, \ldots, u_{n - 1}) = v$.

According to the division decomposition theorem for MLE polynomials given in paper [PST13], we have:

$$
\begin{split}
\tilde{f}(X_0, X_1, \ldots, X_{n-1}) -  {\color{red}\tilde{f}(u_0, u_1, \ldots, u_{n-1})} & = \tilde{q}_{n-1}(X_0, X_1, \ldots, X_{n-2}) \cdot (X_{n-1} - u_{n-1}) \\
& + \tilde{q}_{n-2}(X_0, X_1, \ldots, X_{n-3}) \cdot (X_{n-2} - u_{n-2}) \\
& + \cdots \\
& + \tilde{q}_{1}(X_0) \cdot (X_{1} - u_{1}) \\
& + \tilde{q}_{0} \cdot (X_{0} - u_{0}) \\
\end{split}
$$

If $\tilde{f}(u_0, \ldots, u_{n - 1}) = v$, then we have:

$$
\begin{split}
\tilde{f}(X_0, X_1, \ldots, X_{n-1}) - {\color{red}v} & = \tilde{q}_{n-1}(X_0, X_1, \ldots, X_{n-2}) \cdot (X_{n-1} - u_{n-1}) \\
& + \tilde{q}_{n-2}(X_0, X_1, \ldots, X_{n-3}) \cdot (X_{n-2} - u_{n-2}) \\
& + \cdots \\
& + \tilde{q}_{1}(X_0) \cdot (X_{1} - u_{1}) \\
& + \tilde{q}_{0} \cdot (X_{0} - u_{0}) \\
\end{split}
$$

At this point, proving $\tilde{f}(u_0, \ldots, u_{n - 1}) = v$ can be converted into proving the existence of $\{\tilde{q}_i\}_{0\leq i<n}$ that satisfy the above division equation.

PST13 [PST13, XZZPS19] introduces structured SRS to commit to quotient polynomials $\tilde{q}_0, \tilde{q}_1, \ldots, \tilde{q}_{n-1}$, and the Verifier verifies the correctness of the above division decomposition through ECC-Pairing operations.

The core of the Zeromorph [KT23] protocol is to provide a mapping from multilinear polynomials to univariate polynomials, where the Evaluations of the MLE polynomial on the Boolean Hypercube directly serve as coefficients of the univariate polynomial. By transforming the multilinear polynomials in the above division decomposition into univariate polynomials through this mapping method, we can derive a key equation that the Zeromorph protocol aims to prove:

$$
\begin{split}
[[\tilde{f}(X_0, X_1, \ldots, X_{n-1})]]_n - v\cdot\Phi_n(X) &=\sum_{k=0}^{n-1}\Big(X^{2^k}\cdot \Phi_{n-k-1}(X^{2^{k+1}}) - u_k\cdot\Phi_{n-k}(X^{2^k})\Big)\cdot [[\tilde{q}_k(X_0, X_1, \ldots, X_{k-1})]]_k
\end{split}
$$

Here $[[\tilde{f}(X_0, X_1, \ldots, X_{n-1})]]_n$ represents the direct correspondence of the values of $\tilde{f}(X_0, \ldots, X_{n - 1})$ on the boolean hypercube $B_n = \{0,1\}^n$ to the coefficients of a univariate polynomial, i.e.,

$$
[[\tilde{f}(X_0, X_1, \ldots, X_{n-1})]]_n = \sum_{i = 0}^{2^n - 1} \tilde{f}(\mathsf{bits}(i)) \cdot X^{i}
$$
$[[\tilde{q}_k(X_0, X_1, \ldots, X_{k-1})]]_k$ follows the same mapping method, transforming a multilinear polynomial into a univariate polynomial, i.e.,

$$
[[\tilde{q}_k(X_0, X_1, \ldots, X_{k-1})]]_k = \sum_{i = 0}^{2^k - 1} \tilde{q}_{k}(\mathsf{bits}(i)) \cdot X^i
$$

$\Phi_n(X)$ and $\Phi_{n-k}(X^{2^k})$ are also univariate polynomials. Generally, $\Phi_k(X^h)$ denotes the following polynomial:

$$
\Phi_k(X^h) = 1 + X^h + X^{2h} + \ldots + X^{(2^{k}-1)h}
$$

Therefore, both sides of the key equation in the Zeromorph protocol are univariate polynomials. The Verifier can randomly select a point, and the Prover only needs to prove that these univariate polynomials satisfy the above equation at that random point, which can be done using univariate-PCS. Thus, the Zeromorph protocol can choose to interface with different univariate-PCS, such as KZG10 or FRI-PCS.

#### Inner-product 

The proof of $\tilde{f}(u_0, \ldots, u_{n - 1}) = v$ for Multilinear Polynomials can be transformed into the following Inner-product form:

$$
\langle \vec{f}, \otimes_{j=0}^{n - 1}(1, u_i)\rangle = v
$$

That is, proving that the inner product of vector $\vec{f}$ and vector $\otimes_{j=0}^{n - 1}(1, u_i)$ is $v$. There are many protocols that construct MLE-PCS through this inner product proof method, including Virgo[ZXZS19], Hyrax[WTSTW16], PH23-PCS[PH23], Mercury[EG25], and Samaritan[GPS25].

Virgo-PCS[ZXZS19] is described in the Coefficients Form of MLE polynomials, where proving $\tilde{f}(u_0, \ldots, u_{n - 1}) = v$ is equivalent to the inner product relation:

$$
\langle \vec{f}, \otimes_{j=0}^{n - 1}(1, u_i)\rangle = v
$$

Virgo-PCS uses Univariate Sumcheck to prove this inner product. In Univariate Sumcheck, besides proving that a univariate polynomial constraint holds, it's also necessary to prove that a univariate polynomial's degree is less than a certain value, which is accomplished using the FRI protocol.

In Univariate Sumcheck, for the Verifier to verify that a constraint on a univariate polynomial holds, they need to calculate the value of a polynomial $u(X)$ constructed from the vector $\otimes_{j=0}^{n - 1}(1, u_i)$ at a point, but this requires $O(N)$ computation. Virgo uses the GKR protocol to delegate this computation to the Prover, allowing the Verifier to complete verification with only $O(\log^2(N))$ computation.

The PH23-PCS[PH23] protocol describes the Evaluations Form of multilinear polynomials, where proving $\tilde{f}(u_0, \ldots, u_{n - 1}) = v$ means proving:

$$
\sum_{i = 0}^{2^n - 1} \tilde{f}(\mathsf{bits}(i)) \cdot \tilde{eq}(\mathsf{bits}(i), (u_0,\ldots,u_{n-1})) = v
$$

Let vector $\vec{a} = (\tilde{f}(\mathsf{bits}(0)), \ldots, \tilde{f}(\mathsf{bits}(2^n - 1)))$, and the i-th component of vector $\vec{c}$ be $\tilde{eq}(\mathsf{bits}(i), (u_0,\ldots,u_{n-1}))$. Then the above summation can be viewed from an inner product perspective:

$$
\langle \vec{a}, \vec{c} \rangle  = v
$$

The PH23-PCS proof protocol is divided into two parts:

(1) Proving that the components of vector $\vec{c}$ are indeed $\tilde{eq}(\mathsf{bits}(i), (u_0,\ldots,u_{n-1}))$

(2) Proving that the inner product $\langle \vec{a}, \vec{c} \rangle  = v$

For part (1), using the structure of $\tilde{eq}(\mathsf{bits}(i), (u_0,\ldots,u_{n-1}))$, a univariate polynomial $c(X)$ is constructed, and proof is done using constraints of $n + 1$ univariate polynomials.

For part (2), this is an inner product proof, which can be done using methods like Grand Sum or Univariate Sumcheck. The article [The Missing Protocol PH23-PCS (Part 1)](https://github.com/sec-bit/mle-pcs/blob/main/ph23/ph23-pcs-01.md) provides a complete protocol for PH23-PCS using Grand Sum for inner product proofs. Using the Grand Sum method, proving an inner product can be converted to proving that $3$ univariate polynomial constraints hold.

Thus, both parts of the PH23-PCS proof can be transformed into proving that $n + 4$ univariate polynomial constraints hold, which can then be proven using univariate polynomial PCS, so PH23-PCS can interface with KZG10 and FRI-PCS.

The Hyrax [WTSTW16] protocol directly views the MLE polynomial $\tilde{f}(u_0, u_1, u_2, u_3)$ as a vector-matrix multiplication equation:

$$
\tilde{f}(u_0, u_1, u_2, u_3) = 
\begin{bmatrix}
1 & u_2 & u_3 & u_2u_3 \\
\end{bmatrix}
\begin{bmatrix}
c_0 & c_1 & c_2 & c_3 \\
c_4 & c_5 & c_6 & c_7 \\
c_8 & c_9 & c_{10} & c_{11} \\
c_{12} & c_{13} & c_{14} & c_{15}
\end{bmatrix}
\begin{bmatrix}
1 \\
u_0 \\
u_1 \\
u_0u_1 \\
\end{bmatrix}
$$

Then the matrix is committed row by row. Hyrax uses Pedersen Commitment, which has additive homomorphism, so the commitment vectors can first be inner-producted with $(1, u_2, u_3, u_2u_3)$ to get a single commitment, and then prove that the inner product of the vector corresponding to this commitment and $(1, u_0, u_1, u_0u_1)$ equals $v$. This final inner product proof uses the Bulletproofs-IPA protocol, with the Verifier's computational complexity at $O(\sqrt{N})$ and the Proof size at $O(\log(N))$.

The Mercury [EG25] and Samaritan [GPS25] protocols have very similar approaches, both improving on the matrix multiplication equation described in Hyrax. Unlike Hyrax, Mercury and Samaritan only need to compute commitments for the vector as a whole, rather than row by row, generating $\sqrt{N}$ commitments. Then they transform the overall Evaluation proof into two inner product proofs. Additionally, Mercury batches the two inner product proofs into one, further optimizing the protocol.

#### Sumcheck Method

Substituting $\tilde{f}(u_0, \ldots, u_{n - 1}) = v$ into the point-value form of the multilinear polynomial, we can transform it into proving the summation on $B_n = \{0,1\}^n$:

$$
\sum_{\vec{b} = \{0,1\}^n}\tilde{f}(\vec{b}) \cdot \tilde{eq}(\vec{b}, \vec{u}) = v
$$

So we can prove that the above summation holds, thereby proving the correctness of the Multilinear Polynomial Evaluation. The challenge with using Sumcheck is that in the last step of the Sumcheck protocol, the Verifier needs to obtain the value of $\tilde{f}$ at a random point for final verification, completing the entire Sumcheck protocol. The significant contribution of the Basefold [ZCF23] protocol is discovering that if we synchronously use the FRI protocol on the univariate polynomial corresponding to $\tilde{f}$, and use the same random number as the Sumcheck protocol in each round of folding, then when folded to the last step, the resulting constant is exactly the value of $\tilde{f}$ at the random point that the Sumcheck protocol wants in the last step.

$$
h(r_{n-1}) \overset{?}{=} \tilde{f}(r_0, r_1, \ldots, r_{n-1})\cdot \tilde{eq}((r_0, r_1, \ldots, r_{n-1}), \vec{u})
$$

The Deepfold protocol and WHIR protocol also continue with the Sumcheck approach, with the difference being that Deepfold adopts the idea from DEEP-FRI, where the Prover predetermined the evaluation of a polynomial at some Out-of-domain random point as a form of Commitment, ensuring that the Prover always commits to the same polynomial even in the List-decoding Regime. This random Evaluation can also be proven using the Sumcheck protocol. Specifically, in each round of the Basefold protocol interaction, the Verifier additionally randomly selects a $z_i\leftarrow \mathbb{F}$, and then the Prover sends $y_i$ and proves that it is the value of $\hat{f}^{(i)}(z_i)$. Since $\hat{f}^{(i)}$ and $\tilde{f}^{(i)}$ have an isomorphic mapping, $y_i$ is also the evaluation value of the following MLE polynomial:

$$
y_i = \tilde{f}^{(i)}(z_i, z_i^2, \cdots, z_i^{2^{n-i-1}})
$$

Therefore, in subsequent protocol interactions, the Prover similarly uses a new Sumcheck protocol to prove the correctness of $\tilde{f}^{(i)}(z_i, z_i^2, \cdots, z_i^{2^{n-i-1}})$.

WHIR improves on the Deepfold protocol by merging both Out-of-domain and In-domain random queries into Sumcheck, leading to an optimized protocol state. Similarly, Ligerito, based on Basefold, also utilizes the Sumcheck protocol. In each Round, the Verifier samples some points from the Oracle, and the correctness of the encoding of these points should be calculated by the Verifier. Since this calculation is an inner product, the Verifier can use the Sumcheck protocol to delegate it to the Prover, and this Sumcheck can be merged with the Sumcheck protocol part of the current round of the Basefold protocol, greatly optimizing the subsequent flow of the protocol.

#### Split-and-fold (Recursive)

This proof approach is very similar to the FRI protocol, repeatedly splitting and folding a larger polynomial until a constant is reached.
Both the Gemini [BCH+22] protocol and HyperKZG use the split-and-fold idea for proof, with the difference being that the multilinear polynomial in Gemini is in Coefficients Form, while in hyperKZG it uses Evaluations Form. In the protocol, only the folding method needs to be changed, without requiring FFT conversion from point-value form to coefficient form.

Taking the Gemini protocol as an example, view the coefficient form of the MLE polynomial:

$$
\tilde{f}(X_0, X_1, \ldots, X_{n-1}) = \sum_{i=0}^{2^n-1} f_i \cdot X_0^{i_0}X_1^{i_1} \cdots X_{n - 1}^{i_{n - 1}} 
$$

as an inner product between a vector and a tensor product structure:

$$
\tilde{f}(X_0, X_1, \ldots, X_{n-1}) = \langle \vec{f}, \otimes_{i=0}^{n - 1}(1, X_i)\rangle
$$

For example, with $n = 3$, the coefficient vector:

$$
\vec{f} = (f_0,f_1, f_2, \ldots, f_7)
$$

The tensor product structure can also be viewed as a vector:

$$
\otimes_{i=0}^{2}(1, X_i) = (1, X_0, X_1, X_0X_1, X_2, X_0X_2, X_1X_2, X_0X_1X_2)
$$

Therefore, to prove $\tilde{f}(u_0, \ldots, u_{n - 1}) = v$, we prove:

$$
\langle \vec{f}, \otimes_{j=0}^{n - 1}(1, u_i)\rangle = v
$$

This inner product form can be split-and-folded:

$$
\langle \vec{f}, \otimes_{j=0}^{n - 1}(1, u_i)\rangle = \langle \vec{f}_{even}, \otimes_{j=1}^{n - 1}(1, u_i)\rangle  + u_0 \langle \vec{f}_{odd}, \otimes_{j=1}^{n - 1}(1, u_i)\rangle 
$$

where $\vec{f}_{even}$ represents the vector composed of even-indexed terms from coefficient vector $\vec{f}$, and $\vec{f}_{odd}$ represents the vector of odd-indexed terms from $\vec{f}$. Using $n = 3$ as an example again:

$$
\begin{align}
\langle \vec{f}, \otimes_{j=0}^{n - 1}(1, u_i)\rangle  & =  f_0 + f_1 u_0 + f_2 u_1 + f_3 u_0 u_1 + f_4 u_2 + f_5 u_0 u_2 + f_6 u_1 u_2 + f_7 u_0u_1u_2 \\
 & = (f_0 + f_2 u_1 + f_4 u_2 + f_6 u_1u_2) + u_0 \cdot (f_1 + f_3 u_1 + f_5 u_2 + f_7 u_1u_2) \\
 & =  \langle \vec{f}_{even}, \otimes_{j=1}^{n - 1}(1, u_i)\rangle  + u_0 \langle \vec{f}_{odd}, \otimes_{j=1}^{n - 1}(1, u_i)\rangle 
\end{align}
$$

Here, split-and-fold means first splitting the 8-term sum into two parts—even terms $f_0 + f_2 u_1 + f_4 u_2 + f_6 u_1u_2$ and odd terms $f_1 + f_3 u_1 + f_5 u_2 + f_7 u_1u_2$—then folding these two parts into one using $u_0$. This folded part can continue the split-and-fold process. The split-and-fold idea here is the same as in FRI and sumcheck.

We can directly convert the coefficient form of the MLE polynomial into the coefficients of a univariate polynomial. For instance, the univariate polynomial corresponding to $\tilde{f}(X_0, \ldots, X_{n - 1})$ is:

$$
f(X) = \sum_{i=0}^{2^n-1} f_i \cdot X^i
$$

So the split-and-fold technique can be applied directly to $f(X)$, with a process identical to the FRI protocol, except that the folding coefficient is not a random number but $u_i$. This eventually transforms into a constant polynomial, and the result should equal the value of $\tilde{f}$ at point $(u_0, \ldots, u_{n - 1})$, i.e., equal to $v$. In this process, the verifier needs to verify the correctness of each fold, which can be done by randomly challenging some points. This can be implemented through univariate-PCS, which can interface with KZG10 or FRI.

### Classification by MLE Representation Form

MLE-PCS protocols sit above Multilinear PIOP protocols. These common PIOPs are usually Sumcheck or GKR protocols. In typical implementations, Multilinear Polynomials are represented in Evaluations Form. Not all MLE-PCS protocols directly prove the Evaluations Form. If an MLE-PCS protocol can only prove or commit to the Coefficients Form of Multilinear Polynomial protocols, then the Prover needs to additionally calculate the Coefficients Form of the Multilinear Polynomial using the Algebraic FFT (NTT) algorithm, which requires $O(N\log{N})$ computational time complexity. This might prevent the Prover from achieving linear-time workload.

Although some MLE-PCS papers only describe one form, such as the Coefficients Form, the protocol itself can also support the Evaluations Form. In engineering practice, one can choose the appropriate protocol variant based on more detailed performance analysis. Below we list the support for the two representation forms of Multilinear Polynomials by the MLE-PCS covered in this project:


| Scheme     | Coefficients | Evaluations  |
| ---------- | ------------ | ------------ |
| PST13      | [PST13] ✅    | ✅  [XZZPS19] |
| Zeromorph  | ❓            | ✅ [KT23]     |
| Gemini     | [BCH+22]     |              |
| hyperKZG   |              | ✅ HyperKZG   |
| PH23-KZG   |              | ✅ [PH23]     |
| Mercury    | ✔️           | ✅ [EG25]     |
| Samaritan  | ✔️           | ✅ [GPS25]    |
| Virgo      | ✅ [ZXZS19]   | ❓            |
| Hyrax      | ✅            | ✅ [WTSTW16]  |
| Basefold   | ✅ [ZCF23]    | ✅ [H24]      |
| Deepfold   | ✅ [GLHQTZ24] | ❓            |
| Ligerito   | ✅            | ✅ [NA25]     |
| WHIR       | ✅ [ACFY24b]  | ❓            |
| FRI-Binius | ✔️           | ✅ [DP24]     |
| Σ-Check    | ✅ [GQZGX24]  | ✅            |
| Greyhound  | ✅ [NS24]     | ✅            |
| Hyperwolf  | ✅ [ZGX25]    | ✅            |

- ✅: Supported
- ✔️: Supported, but needs further analysis
- ❓: May not be supported, but not further proven

## Security Analysis of MLE-PCS

For an MLE-PCS protocol, we're not only concerned with how the protocol is constructed, but also with its security proofs, including properties like Completeness, Soundness, Knowledge soundness, and Zero-knowledge. There are significant differences in security assumptions between KZG10-based and FRI-based MLE-PCS.

| Assumption    | Algebra            | Schemes                                                                          |
| ------------- | ------------------ | -------------------------------------------------------------------------------- |
| KZG10(BSDH, AGM, )          | ECC based          | PST13, Zeromorph, Gemini, HyperKZG, PH23-KZG, Mercury, Samaritan      |
| Random Oracle (Hash) | Linear code based | Virgo, PH23-fri, zeromorph-fri, Gemini-fri, Basefold, Deepfold, WHIR, FRI-Binius |
| EC Discrete Log | ECC based          |  Hyrax，∑-check      |
| M-SIS | Lattice based | Greyhound, Hyperwolf      |

### Security Based on KZG10

For MLE-PCS based on [KZG10], we focus on their Knowledge Soundness proof (also called Extractability).

In the [KZG10] paper, the authors required the protocol to satisfy the Evaluation Binding property, which only guarantees that the prover cannot forge a proof making the polynomial $f(X)$ open to two different values $v_1 \neq v_2$ at the same point $a$.

However, when [KZG10] is used in SNARK design, satisfying only the Evaluation Binding property is insufficient for the security requirements of Knowledge Soundness in the proof system.

Therefore, researchers have proposed stronger security requirements for [KZG10], namely **"Extractability"**: For any algebraic adversary $\mathcal{A}_{alg}$, if it can output a valid polynomial evaluation proof, then there must exist another efficient algorithm $\mathcal{B}_{alg}$ that can extract the secret value $f(X)$ of the polynomial commitment $C$, satisfying $f(z) = v$.

For the extractability proof of [KZG10], we typically care about two points:

- Security model: Using standard model or idealized model, such as Random Oracle model, or Algebraic Group model
- Difficulty assumption: Mainly considering whether the type of assumption used is Falsifiable or Non-falsifiable

Several works based on [KZG10], including [MBKM19], [GWC19], and [CHM+20], have discussed the extractability proof problem. We summarize as follows:

| paper | security model | assumption separation | assumption |
| --- | --- | --- | --- |
| [MBKM19], [GWC19] | AGM+ROM | Falsifiable | q-DLOG |
| [CHM+20] | ROM | Non-Falsifiable | PKE |
| [HPS23] | AGMOS+ROM | Falsifiable | FPR+TOFR |
| [LPS24] | ROM | Falsifiable | ARSDH |

This project deeply studied the security proofs of the KZG protocol in blog post format, including:

- [KZG-soundness-1](https://github.com/sec-bit/mle-pcs/blob/main/kzg10/kzg%20notes/kzg-soundness-1.md): Introduces the concept of KZG extractability and analyzes the KZG security proof method in the AGM+ROM model from the [MBKM19] paper

- [KZG-soundness-2](https://github.com/sec-bit/mle-pcs/blob/main/kzg10/kzg%20notes/kzg-soundness-2.md): Introduces and analyzes in detail the KZG security proof method in the ROM model from the [LPS24] paper

In addition, [HPS23] proposed an improved security model called AGMOS (Algebraic Group Model with Oblivious Sampling). As a more realistic variant of AGM, AGMOS gives an adversary the additional ability to blindly sample group elements without knowing the discrete logarithm.

Furthermore, [HPS23] points out that there are two different KZG extractability definitions in actual protocol design:

- The extractor algorithm extracts the polynomial after the Commit and Open phases, as in [MBKM19], [CHM+20]
- The extractor algorithm extracts the polynomial only after the Commit phase, as in [GWC19]

Among them, although the latter can be proven secure in the AGM model, it would reduce to a spurious knowledge assumption that is insecure in the standard model.

In addition to extractability, we usually also require [KZG10] to satisfy the hiding property, as an important component for constructing zkSNARK or other secure protocols with the Zero-knowledge property.
This project also discusses this aspect, including:

[Understanding Hiding KZG10](https://github.com/sec-bit/mle-pcs/blob/main/kzg10/kzg_hiding.md): This article details two methods for implementing the Hiding property for KZG10. One scheme is from [KT23], with the main technique being a simplified version of multivariate polynomial commitment from [PST13]. The second scheme is from [CHM+20], with the main technique being an improvement on the original KZG protocol paper [KZG10].

### Security Based on Linear Code

For MLE-PCS based on Linear Code, we focus on their Soundness proof. The FRI protocol [BBHR18] itself is an IOPP (Interactive Oracle Proof of Proximity) protocol for Reed-Solomon (RS) encoding, and its security is closely related to the properties of RS encoding and some coding theory. We conducted an in-depth study of the soundness proof for the FRI series of protocols.

For a set of evaluations $S$ in a finite field $\mathbb{F}$, assuming the number of elements in $S$ is $N$, given a rate parameter $\rho \in (0,1]$, the encoding $\text{RS}[\mathbb{F},S,\rho]$ represents the set of all functions $f: S \rightarrow \mathbb{F}$, where $f$ is the evaluations of a polynomial of degree $d < \rho N$, i.e., there exists a polynomial $\hat{f}$ of degree $d < \rho N$ such that $f$ and $\hat{f}$ have consistent values on $S$.

The FRI protocol solves the *RS proximity problem*: Assuming we can obtain an oracle about the function $f: S \rightarrow \mathbb{F}$, the Verifier needs to use fewer query complexities and have a high probability of distinguishing whether $f$ belongs to one of the following cases:

1.  $f \in \text{RS}[\mathbb{F},S,\rho]$
2. $\Delta(f, \text{RS}[\mathbb{F},S,\rho]) > \delta$

That is, either $f$ is a codeword in the RS encoding $\text{RS}[\mathbb{F},S,\rho]$, or the relative Hamming distance from $f$ to all codewords in $\text{RS}[\mathbb{F},S,\rho]$ is greater than the proximity parameter $\delta$.

The [BBHR18] paper provides the soundness proof for the FRI protocol. For $\delta < \delta_0$, where $\delta_0 \approx \frac{1 - 3 \rho}{4}$, for any malicious Prover $P^*$, the probability that the Verifier rejects $P^*$ is approximately $\delta - \frac{O(1)}{|\mathbb{F}|}$.

Through analysis, we know that under the same security parameter, the larger the value of $\delta_0$ can be, the fewer queries the Verifier needs to make in the Query phase, thus reducing the proof size and computational complexity of the FRI protocol. After the [BBHR18] paper, many theoretical research works have appeared to increase $\delta_0$ in the FRI protocol.

| paper                   | $\delta_0$                                           |
| ----------------------- | ---------------------------------------------------- |
| [BBHR18]FRI             | $\delta_0 \approx \frac{1 - 3\rho}{4}$               |
| [BKS18]Worst-case ...   | $\delta_0 \approx 1 - \rho^{\frac{1}{4}}$            |
| [BGKS20]DEEP-FRI        | $\delta_0 \approx 1 - \rho^{\frac{1}{3}}$ , tight(!) |
| [BCIKS20]Proximity Gaps | $\delta_0 \approx 1 - \rho^{\frac{1}{2}}$            |

This project studied the security proofs of the FRI protocol in blog post format, including:

- [Dive into BBHR18-FRI Soundness](https://github.com/sec-bit/mle-pcs/blob/main/fri/BBHR18-FRI.md): Detailed analysis of the security proof in the FRI paper [BBHR18]
- [Dive into BCIKS20-FRI Soundness](https://github.com/sec-bit/mle-pcs/blob/main/fri/BCIKS20-proximity-gaps.md): Introduction to how the Proximity Gaps theorem can improve the security parameters in the FRI protocol
- [Proximity Gaps and Correlated Agreement: The Core of FRI Security Proof](https://github.com/sec-bit/mle-pcs/blob/main/fri/fri-proximity-gap.md): In-depth exploration of core concepts in FRI security proof

The [ACFY24a] STIR paper proposed an improvement to the FRI protocol, with the idea of reducing the code rate in each k-fold of the FRI protocol to achieve smaller query complexity. In the blog post [STIR: Improving Rate to Reduce Query Complexity](https://github.com/sec-bit/mle-pcs/blob/main/fri/stir.en.md), we detail the differences between the FRI and STIR protocols, introduce the protocol flow for one iteration, and analyze the soundness of one iteration.

Although the Basefold protocol [ZCF23] is applicable to the Random Foldable Code mentioned in the paper, it still applies to Reed Solomon encoding, so it can be understood that the Basefold protocol combines sumcheck and the FRI protocol. In the original Basefold paper [ZCF23], its soundness is only proven to have $\delta_0$ at most $(1 - \rho)/2$. Subsequently, Ulrich Haböck proved in [H24] that the Basefold protocol for Reed Solomon can reach the Johnson bound $1 - \sqrt{\rho}$, and Hadas Zeilberger proved in the Khatam [Z24] paper that the Basefold protocol for general linear codes can reach $1 - \rho^{\frac{1}{3}}$.

Related note articles on the Basefold protocol include:

- Basefold protocol introduction:
	- [Notes on Basefold (Part I): Foldable Linear Codes](https://github.com/sec-bit/mle-pcs/blob/main/basefold/basefold-01.md) 
	- [Notes on Basefold (Part II): IOPP](https://github.com/sec-bit/mle-pcs/blob/main/basefold/basefold-02.md)
	- [Notes on Basefold (Part III): MLE Evaluation Argument](https://github.com/sec-bit/mle-pcs/blob/main/basefold/basefold-03.md)
- Soundness proof from the original Basefold paper [ZCF23]:
	- [Notes on BaseFold (Part IV): Random Foldable Codes](https://github.com/sec-bit/mle-pcs/blob/main/basefold/basefold-04.md)
	- [Notes on Basefold (Part V): IOPP Soundness](https://github.com/sec-bit/mle-pcs/blob/main/basefold/basefold-05.md)
- Soundness proof of the Basefold protocol given in [H24]:
	- [Note on Basefold's Soundness Proof under List Decoding](https://github.com/sec-bit/mle-pcs/blob/main/basefold/basefold-habock-overview.md)
	- [Note on Soundness Proof of Basefold under List Decoding](https://github.com/sec-bit/mle-pcs/blob/main/basefold/basefold-habock-soundness.md)

The Deepfold protocol and WHIR protocol adopt the same idea as the Basefold protocol, combining the sumcheck protocol to construct MLE-PCS. The Deepfold protocol combines the sumcheck protocol with DEEP-FRI. For a detailed introduction to this protocol, see the blog post [Note on DeepFold: Protocol Overview](https://github.com/sec-bit/mle-pcs/blob/main/fri/deepfold.md). The WHIR protocol combines the sumcheck protocol and STIR protocol, and the blog post [Note on WHIR: Reed-Solomon Proximity Testing with Super-Fast Verification](https://github.com/sec-bit/mle-pcs/blob/main/fri/whir.md) introduces the WHIR protocol in detail.

The Basefold protocol, Deepfold protocol, and WHIR protocol have similar approaches. In the blog post [BaseFold vs DeepFold vs WHIR](https://github.com/sec-bit/mle-pcs/blob/main/analysis/basefold-deepfold-whir.md), we compare the construction of these three protocols and, through analysis of their soundness proofs, compare the number of queries by the Verifier in these three protocols.

### Security Based on M-SIS

For lattice-based polynomial commitment schemes, we focus on the proof of knowledge soundness.

Unlike discrete logarithm-based schemes, relations in lattice-based cryptography typically include additional norm constraints to meet the security requirements of lattice assumptions. Therefore, in the proof of knowledge soundness, we not only need to prove that the extracted witness satisfies conventional constraints such as IPA, but also must further prove that the norm of this witness is small enough, ensuring it can be bound to the Ajtai commitment.

The security of the Greyhound protocol is built on the M-SIS problem variant of infinite norm. In the proof of knowledge soundness, Greyhound proves that the extracted witness pair $(\bar{c}, \bar{w})$ satisfies a relaxed relation. This relaxed relation is the same as the original relation in other conventional constraints, differing only in the norm constraint and binding constraint.

For the binding constraint, the relaxed relation requires $\bar{c} A \bar{w} = \bar{c} \mathsf{cm}$, where $\mathsf{cm}$ is the commitment to the witness and a public parameter. For the norm constraint, the relaxed relation requires $| \bar{c} \bar{w} | \le 2\bar{\beta}$, while the original relation requires $| w | \le \beta$.

By constraining that the M-SIS problem remains hard at the norm $\min\{2\bar{\beta},\ 8T\bar{\beta}\}$, the proof can guarantee that the extracted witness is both bound to the original commitment $\mathsf{cm}$ and satisfies all other conventional constraints. Here, $T$ represents the operation norm of $\bar{c}$.

The security of Hyperwolf is built on the $\ell_2$-norm version of the M-SIS problem. In proving the norm constraint, the protocol adopts a technical approach similar to Labrador: by proving that the norm of the witness under a certain random projection is small, it can be inferred with high probability that the norm of the original vector is also within an acceptable range.

To prove that the $\ell_2$ norm of a vector $\vec{a} \in \mathbb{Z}^n$ is small, while avoiding leaking its complete information, we can use the Johnson–Lindenstrauss (JL) lemma. The core idea of this lemma is that the $\ell_2$ norm of a high-dimensional vector can be approximately preserved with high probability after random linear projection.

The specific method is as follows: The Verifier randomly generates a projection matrix $\Pi \in \mathbb{Z}^{256 \times n}$, where each element is independently sampled from the set ${-1, 0, 1}$ with probabilities $\Pr[-1] = \Pr[1] = 1/4$, $\Pr[0] = 1/2$. The Prover calculates and sends the projected vector $\vec{p} = \Pi \vec{a}$. The Verifier then checks the norm of $\vec{p}$ to estimate whether the norm of the original vector $\vec{a}$ satisfies the constraint. The specific content of the JL Lemma is as follows:

**Modular Johnson–Lindenstrauss Variant:**
Let $q \in \mathbb{N}$, and let $\mathcal{D}$ be a distribution defined on ${0, \pm 1}$, satisfying $\mathcal{D}(1) = \mathcal{D}(-1) = 1/4$, $\mathcal{D}(0) = 1/2$. For any $\vec{a} \in \mathbb{Z}_q^n$, if it satisfies $|\vec{a}| \le b$ and $b \le q/125$, then:

$$
\begin{equation}
\begin{split}
\Pr_{\Pi \leftarrow \mathcal{D}^{256\times n}}[\|\Pi\vec{a}\mod q\|^2< 30b^2] \lessapprox  2^{-128}.
\nonumber
\end{split}
\end{equation}
$$

According to this theorem, proving the short norm problem can be reduced to proving that a projected vector $\vec{p}$ is well-formed (i.e., satisfies the IPA relation). This method can guarantee with high probability that the extracted witness satisfies the norm constraint, while only introducing a constant-level slack, achieving a good balance between efficiency and security.

## Discoveries

In the process of deeply studying the underlying principles of these MLE-PCS, we found that some protocols still have room for optimization, and we proposed some new implementation methods. Below are our main innovations.

### ∑-Check Protocol

The compressed Σ-protocol theory [AC20](https://eprint.iacr.org/2020/152), [ACF21](https://eprint.iacr.org/2020/753) offers a general approach for efficiently proving polynomial relations. In the context of PCS, it can be either (1) used directly to prove PCS evaluations by expressing them as a relation $\{(\vec{f}; F, \vec{z}, v): \mathsf{Com}(\vec{f}) = F, f(\vec{z}) = v\}$, where $\vec{f}$​ represents the coefficients of the polynomial $f$; or (2) applied as a drop-in replacement for IPA in Bulletproofs-based PCS systems like [Hyrax](https://eprint.iacr.org/2017/1132.pdf). [AC20](https://eprint.iacr.org/2020/152) and [ACF21](https://eprint.iacr.org/2020/753) demonstrate that this can be achieved through linearization based on arithmetic circuits, followed by the application of [Bulletproofs compression](https://eprint.iacr.org/2017/1066), resulting in a Bulletproofs-based PCS with a transparent setup.

Our recent contribution, [Σ-Check](https://eprint.iacr.org/2024/1654), advances this research field by introducing an efficient sumcheck-based method for proving $k$ distinct polynomial evaluations, each with $n$ variables, at a cost of $O(n+\log k)$-size proofs. This approach eliminates the need for circuit-based linearization and proves to be more efficient when handling $k$ polynomials, which previously required $O(n+k)$ cost in [AC20](https://eprint.iacr.org/2020/152) and [ACF21](https://eprint.iacr.org/2020/753). A prototype implementation is available at [GitHub](https://github.com/QMorning/Compressed-Sigma-Protocol-from-Sumcheck).

### Hyperwolf Protocol

In the [Greyhound](https://eprint.iacr.org/2024/1293.pdf) protocol, the polynomial evaluation process can be expressed as the inner product of a coefficient vector $\vec{f}$ of length $N$ with the tensor product of two vectors $\vec{a}$ and $\vec{b}$ of length $n = \sqrt{N}$, i.e., $v = \langle \vec{f}, \vec{a} \otimes \vec{b} \rangle$. Alternatively, this process can be understood as reconstructing $\vec{f}$ into a matrix $F$ of size $n \times n$, and then performing matrix multiplication successively with $\vec{a}$ and $\vec{b}$. Specifically, $\vec{f}$ can be seen as concatenated from each row of $F$ in row-major order.

By rewriting the polynomial evaluation process into the above structure, the Greyhound protocol achieves a reduction in proof size and verification time to sublinear levels, while maintaining the prover's computational cost as linear. This structural optimization allows the protocol to balance security with efficiency and practicality.

The [Hyperwolf](https://eprint.iacr.org/2025/922.pdf) protocol is an optimization of the [Greyhound](https://eprint.iacr.org/2024/1293.pdf) protocol, with the core idea being to generalize the original two-dimensional structure to $k$ dimensions ($k \ge 2$).

Specifically, it interprets the one-dimensional coefficient vector $\vec{f}$ as a $k$-dimensional hypercube $[F]^{(k)}$ with dimensions $b \times b \times \cdots \times b$ (a total of $k$ dimensions), satisfying $b^k = N$. The polynomial evaluation process can be viewed as successive tensor-directional matrix multiplication of this hypercube with $k$ auxiliary vectors. Based on this structure, we designed a proof system with $k$ rounds of interaction, where the proof size and verification time for each round is $O(b)$, resulting in an overall proof size and verification time of $O(kb) = O(kN^{1/k})$. When $k = \log N$, the system's total complexity can be optimized to $O(\log N)$, significantly enhancing performance.

### Optimizing the Zeromorph Protocol

In the zeromorph protocol, we need to prove that $n$ quotient polynomials $q_i(X) = [[\tilde{q}_i]]_i (0 \le i < n)$ have degrees less than $2^i$. Section 6 of the zeromorph paper [KT23] aggregates multiple Degree Bound proofs together, as detailed in [Optimized Protocol](https://github.com/sec-bit/mle-pcs/blob/main/zeromorph/zeromorph.md#optimized-protocol). However, in this protocol, the Verifier needs to perform two operations on the elliptic curve $\mathbb{G}_2$, which is very expensive.

We used another method to prove Degree Bound, avoiding operations by the Verifier on the elliptic curve $\mathbb{G}_2$. The cost is a slight increase in the Verifier's calculations on the elliptic curve $\mathbb{G}_1$ and adding a point on the elliptic curve $\mathbb{G}_1$ and a value on the finite field to the proof, which is acceptable in scenarios with high requirements on Verifier Cost. The detailed description of this protocol is in [Zeromorph-PCS (Part II)](https://github.com/sec-bit/mle-pcs/blob/main/zeromorph/zeromorph-02.md).

### Optimizing the Gemini Protocol

In the gemini protocol, the Prover needs to calculate the values of $n$ polynomials $h_0(X), \ldots, h_{n - 1}(X)$ at random points $\beta, -\beta, \beta^2$ and send them to the Verifier, letting the Verifier verify that there is a folding relationship between $h_{i + 1}(X^2)$ and $h_{i}(X)$ and $h_i(-X)$. For this part of the protocol description, see [Gemini-PCS (Part I)](https://github.com/sec-bit/mle-pcs/blob/main/gemini/Gemini-PCS-1.md#implementation-based-on-kzg).

We discovered two ways to optimize the gemini protocol.

Optimization Method 1: The Prover only needs to send $h_0(\beta^2)$ and the values of $h_0(X), \ldots, h_{n - 1}(X)$ at random points $\beta, -\beta$, using random numbers to aggregate $h_0(X)$ and $h_1(X), \ldots, h_{n - 1}(X)$ into one polynomial, proving at once that these polynomials are correct at $\beta, -\beta, \beta^2$. This can reduce the proof size, eliminating $n - 1$ values on the finite field. For the specific protocol description, see [Gemini-PCS (Part III)](https://github.com/sec-bit/mle-pcs/blob/main/gemini/Gemini-PCS-3.md).

Optimization Method 2: Another optimization method adopts the idea of selecting points in the Query phase of the FRI protocol. It challenges $h_0(X)$ at $X = \beta$, then challenges the folded polynomial $h_1(X)$ at $X = \beta^2$, and so on, until $h_{n - 1}(\beta^{2^{n-1}})$. The benefit is that each opening point of $h_{i}(X)$ can be reused when verifying the folding of $h_{i+1}(X)$, saving $n$ more opening points beyond Optimization Method 1. Compared to Optimization Method 1, the cost of this approach is an increase in computation for both Prover and Verifier, but it reduces proof size. For the specific protocol description, see [Gemini-PCS (Part IV)](https://github.com/sec-bit/mle-pcs/blob/main/gemini/Gemini-PCS-4.md).

### Optimizing the PH23 Protocol

In the original paper [PH23], the authors provided an inner product-based MLE-PCS protocol. Following the ideas provided in the original paper, the protocol we designed has a proof size of $O(\log{N})$. The core idea of the PH23 protocol is to prove the following inner product:

$$
\tilde{f}(X_0,X_1,\ldots,X_{n-1}) = \sum_{\vec{b}\in\{0,1\}^n} a(\vec{b}) \cdot \tilde{eq}(\vec{b}, \vec{u}) 
$$

If we denote $\tilde{eq}(\vec{b}, \vec{u})$ as $\vec{c}$, then the Evaluation proof can be transformed into an inner product proof, i.e., proving

$$
\langle \vec{a}, \vec{c} \rangle \overset{?}{=} \tilde{f}(X_0,X_1,\ldots,X_{n-1})
$$

Proving the inner product alone is not enough; the Prover also needs to commit to $\vec{c}$ and prove the correctness of $\vec{c}$ to the Verifier. Paper [PH23] provided a scheme that uses $\log{N}$ polynomial constraints to prove the correctness of $\vec{c}$. This can optimize the Proof size to $O(\log{N})$ Field elements plus $O(1)$ Group Elements. However, this is not the most optimized scheme for Proof size.

We can define three column vectors, namely $\vec{c}$, $\vec{c}'$, and $\vec{u}'$, where $\vec{c}'$ is the Lookup vector in $\vec{c}$, meaning that for any $c_i\in\vec{c'}$, we have $c_i\in\vec{c}$. Note that this is not an Unindexed Lookup relation, but an Indexed Lookup relation. Then we define that each element in $\vec{u}'$ also comes from $\vec{u}$. In this way, we can use a polynomial constraint relation to prove the correctness of $\vec{c}$.

$$
(1-u'_i) \cdot c_i - u'_i \cdot c'_i = 0, \quad \forall i \in [N]
$$

We can prove the Indexed Lookup relation using a Copy Constraint Argument, or we can use an Indexed Logup Argument protocol, thus achieving $O(1)$ Proof size.

### Adding FRI Interface Protocols for PH23 and Gemini

For PH23-PCS, zeromorph, and gemini protocols, they all transform MLE-PCS into univariate-PCS. In the original protocols, the interfacing univariate-PCS is KZG10. We tried to interface these protocols with FRI-PCS protocols and provided complete protocol descriptions.

1. **PH23-FRI** 

	We provided two different protocols for interfacing PH23 with FRI.

	- Protocol 1 description is in [The Missing Protocol PH23-PCS (Part 4)](https://github.com/sec-bit/mle-pcs/blob/main/ph23/ph23-pcs-fri-01.md), where the inner product proof is implemented through Grand Sum.
	- Protocol 2 description is in [The Missing Protocol PH23-PCS (Part 5)](https://github.com/sec-bit/mle-pcs/blob/main/ph23/ph23-pcs-fri-02.md), where the inner product proof is implemented through the Univariate Sumcheck method.
	
	By comparing these two different implementation methods, we found that Protocol 2 deals with more polynomials, resulting in higher overall proof size and Verifier computational complexity compared to Protocol 1.
	
2. **Gemini-FRI**
	
	Protocol description is in [Gemini: Interfacing with FRI](https://github.com/sec-bit/mle-pcs/blob/main/gemini/gemini-fri.md). One advantage of FRI-PCS is that for opening polynomials of different degrees at multiple points, random numbers can be used to merge them into one polynomial, requiring only one call to FRI's low degree test to complete all these proofs. Therefore, when combining the Gemini protocol with FRI-PCS, only one call to the FRI protocol is needed to prove the correct opening of multiple polynomials at different points in the Gemini protocol.
	
### Optimizing the Basefold Protocol 

In the Sumcheck sub-protocol of Basefold, the $h^{(i)}(X)$ sent by the Prover in each step is a univariate quadratic polynomial, but after Sumcheck optimization [Gru24], the Prover can send just a linear polynomial, reducing the communication in the Sumcheck sub-protocol. This point is mentioned in paper [H24]. Further research into the Deepfold protocol revealed that it uses a different Sumcheck protocol from [H24], as detailed in [The Connection between Deepfold and sumcheck](https://github.com/sec-bit/mle-pcs/blob/main/fri/deepfold.md#deepfold-%E4%B8%8E-sumcheck-%E7%9A%84%E8%81%94%E7%B3%BB).

Briefly, according to the definition of $\tilde{eq}(\vec{X}, \vec{Y})$, it can be decomposed as:

$$
\tilde{eq}(\vec{X}_0\parallel\vec{X}_1, \vec{Y}_0\parallel\vec{Y}_1) = eq(\vec{X}_0, \vec{Y}_0) \cdot eq(\vec{X}_1, \vec{Y}_1)
$$

First, observe the definition of $h^{(0)}(X)$:

$$
h^{(0)}(X) = \sum_{b_1,b_2\in\{0,1\}^{2}} \tilde{f}(X, b_1, b_2) \cdot \tilde{eq}((u_0, u_1, u_2), (X, b_1, b_2))
$$

The right side of the equation can be rewritten as:

$$
\begin{aligned}
h^{(0)}(X) &= \sum_{b_1,b_2\in\{0,1\}^{2}} \tilde{f}(X, b_1, b_2) \cdot \tilde{eq}((u_0, u_1, u_2), (X, b_1, b_2)) \\
&= \sum_{b_1,b_2\in\{0,1\}^{2}} \tilde{f}(X, b_1, b_2) \cdot eq(u_0, X) \cdot eq((u_1, u_2), (b_1, b_2)) \\
&= eq(u_0, X) \cdot \sum_{(b_1,b_2)\in\{0,1\}^2}  \Big( \tilde{f}(X, b_1, b_2) \cdot eq((u_1,u_2), (b_1, b_2)) \Big) \\
\end{aligned}
$$

This way, the Prover only needs to send $g(X)=\sum_{(b_1,b_2)\in\{0,1\}^2}  \Big( \tilde{f}(X, b_1, b_2) \cdot eq((u_1,u_2), (b_1, b_2)) \Big)$ to the Verifier, who can compute $eq(u_0, X)$ and multiply it. This calculation is just a Linear Combination involving only one multiplication.

Another article [Basefold Optimization](https://github.com/sec-bit/mle-pcs/blob/main/basefold/basefold-opt.md) applies Deepfold's optimization techniques to Basefold, effectively reducing the computation for both Prover and Verifier, while also reducing proof length. After rough estimation, the Sumcheck Prover's operations are reduced by half, while the Sumcheck Verifier's operations are reduced to one-sixth of [H24]. For Basefold, the main component of the Verifier's overall operations is still the FRI-Query operations, so this optimization may not be that significant, but from a protocol design perspective, the optimized protocol is more concise. Whether this technique can be applied to other protocols is worth further study. Interested readers can refer to the optimized code prototype implementation [basefold_rs_opt_pcs.py](https://github.com/sec-bit/mle-pcs/blob/main/src/basefold_rs_opt_pcs.py).

## Code Implementation (Python)

This project has implemented many MLE-PCS protocols in Python code, with Jupyter Notebook versions also available for some protocols, helping users understand the protocols through interactive code.

| Scheme           | Python Code                                                                                                                                                                                                                                                              | Jupyter Notebook                                                                                                                                                                                                 |
| ---------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Gemini           | [bcho_pcs.py](https://github.com/sec-bit/mle-pcs/blob/main/src/bcho_pcs.py)                                                                                                                                                                                              | [bcho_pcs.ipynb](https://github.com/sec-bit/mle-pcs/blob/main/src/bcho_pcs.ipynb)                                                                                                                                |
| HyperKZG         | [hyperkzg_pcs.py](https://github.com/sec-bit/mle-pcs/blob/main/src/hyperkzg_pcs.py)                                                                                                                                                                                      |                                                                                                                                                                                                                  |
| Zeromorph        | [zeromorph.py](https://github.com/sec-bit/mle-pcs/blob/main/src/zeromorph.py), [zeromorph_zk.py](https://github.com/sec-bit/mle-pcs/blob/main/src/zeromorph_zk.py), [zerofri.py](https://github.com/sec-bit/mle-pcs/blob/zeromorph_fri/src/zerofri.py)                   | [zeromorph.ipynb](https://github.com/sec-bit/mle-pcs/blob/main/src/zeromorph.ipynb), [zeromorph_mapping_tutorial.ipynb](https://github.com/sec-bit/mle-pcs/blob/main/zeromorph/zeromorph_mapping_tutorial.ipynb) |
| PH23             | [ph23_pcs.py](https://github.com/sec-bit/mle-pcs/blob/main/src/ph23_pcs.py)                                                                                                                                                                                              |                                                                                                                                                                                                                  |
| Mercury          | [mercury_pcs.py](https://github.com/sec-bit/mle-pcs/blob/main/src/mercury_pcs.py)                                                                                                                                                                                        |                                                                                                                                                                                                                  |
| Samaritan        | [samaritan_pcs.py](https://github.com/sec-bit/mle-pcs/blob/main/src/samaritan_pcs.py)                                                                                                                                                                                    |                                                                                                                                                                                                                  |
| Basefold         | [Basefold.py](https://github.com/sec-bit/mle-pcs/blob/main/src/Basefold.py),[basefold_rs_opt_pcs.py](https://github.com/sec-bit/mle-pcs/blob/main/src/basefold_rs_opt_pcs.py), [basefold_rs_pcs.py](https://github.com/sec-bit/mle-pcs/blob/main/src/basefold_rs_pcs.py) | [Basefold.ipynb](https://github.com/sec-bit/mle-pcs/blob/main/src/Basefold.ipynb)                                                                                                                                |
| Deepfold         | [deepfold_pcs.py](https://github.com/sec-bit/mle-pcs/blob/main/src/deepfold_pcs.py)                                                                                                                                                                                      | [deepfold.ipynb](https://github.com/sec-bit/mle-pcs/blob/main/src/deepfold.ipynb)                                                                                                                                |
| WHIR             | [whir_pcs.py](https://github.com/sec-bit/mle-pcs/blob/main/src/whir_pcs.py)                                                                                                                                                                                              |                                                                                                                                                                                                                  |
| Hyrax            | [hyrax_pcs.py](https://github.com/sec-bit/mle-pcs/blob/main/src/hyrax_pcs.py)                                                                                                                                                                                            |                                                                                                                                                                                                                  |
| PST13(Libra-PCS) | [libra_pcs.py](https://github.com/sec-bit/mle-pcs/blob/main/src/libra_pcs.py)                                                                                                                                                                                            |                                                                                                                                                                                                                  |

In addition to implementing these protocols, some subprotocols used by MLE-PCS protocols have also been implemented.

| Subprotocol            | Python Code | Jupyter Notebook                                                            |
| ---------------------- | --- | -------- |
| FRI                    | [fri.py](https://github.com/sec-bit/mle-pcs/blob/main/src/fri.py) |   |
| STIR                   | | [stir.ipynb](https://github.com/sec-bit/mle-pcs/blob/main/src/stir.ipynb)   |
| KZG10                  | [kzg10.py](https://github.com/sec-bit/mle-pcs/blob/main/src/kzg10.py),[kzg10_hiding_m.py](https://github.com/sec-bit/mle-pcs/blob/main/src/kzg10_hiding_m.py), [kzg10_hiding_z.py](https://github.com/sec-bit/mle-pcs/blob/main/src/kzg10_hiding_z.py), [kzg10_non_hiding.py](https://github.com/sec-bit/mle-pcs/blob/main/src/kzg10_non_hiding.py),[kzg_hiding.py](https://github.com/sec-bit/mle-pcs/blob/main/src/kzg_hiding.py) | [kzg10.ipynb](https://github.com/sec-bit/mle-pcs/blob/main/src/kzg10.ipynb) |
| IPA                    | [ipa.py](https://github.com/sec-bit/mle-pcs/blob/main/src/ipa.py) |   |
| univariate polynomial  | [unipolynomial.py](https://github.com/sec-bit/mle-pcs/blob/main/src/unipolynomial.py), [unipoly.py](https://github.com/sec-bit/mle-pcs/blob/main/src/unipoly.py), [unipoly2.py](https://github.com/sec-bit/mle-pcs/blob/main/src/unipoly2.py) |    |
| multilinear polynomial | [mle2.py](https://github.com/sec-bit/mle-pcs/blob/main/src/mle2.py) |


### Algebraic Operation Optimization

When implementing MLE-PCS, polynomial operations are ubiquitous, and different implementation methods have different impacts on the complexity of polynomial operations. In this project, we have researched some optimization methods for polynomial operations, including polynomial division optimization.

- Optimization of polynomial division

Assume a finite field $\mathbb{F}$. For polynomials $f(X)$ and $g(X)$ in $\mathbb{F}[X]$, they satisfy the division with remainder equation:

$$
f(X) = g(X) \cdot q(X) + r(X)
$$

and $\deg(r) < \deg(g)$. Let $n = \deg(f), m = \deg(g)$. Traditional division requires $O(n^2)$ computational complexity to calculate the quotient polynomial $q(X)$ and remainder polynomial $r(X)$ after dividing $f(X)$ by $g(X)$. This project introduces a fast division algorithm using Newton Iteration, with algorithmic complexity consistent with polynomial multiplication, i.e., $O(M(n))$, where $M(n)$ represents the complexity of polynomial multiplication. For a detailed description of this algorithm, see the blog post [Fast Polynomial Division Based on Newton Iteration](https://github.com/sec-bit/mle-pcs/blob/main/math/unipoly_div.md), with the corresponding Python code implementation in [unipolynomial.py](https://github.com/sec-bit/mle-pcs/blob/main/math/unipolynomial.py).

## Comparison of KZG10-based MLE-PCS

KZG-based MLE-PCS include Libra-PCS, PH23-PCS, zeromorph, gemini, mercury, and samaritan.

This project theoretically detailed the complexity of PH23-PCS, zeromorph, and gemini protocols, including finite field multiplication, finite field division, addition and multiplication on elliptic curves, etc. All three protocols transform MLE polynomial commitments into univariate polynomial commitments, which can be interfaced with KZG10 or FRI, but their transformation methods differ, resulting in differences in efficiency.

First, let's briefly summarize the approaches of these three protocols. PH23 and zeromorph both consider the point-value form of MLE polynomials on the Hypercube, while gemini considers the coefficient form of MLE polynomials.

|           | MLE                     | Approach                                                                                           |
| --------- | ----------------------- | -------------------------------------------------------------------------------------------- |
| ph23      | evaluation on hypercube | Transformed into proving inner product, needing to prove correct construction of $\vec{c}$ and inner product proof (sum product scheme), transforming into proving $n + 4$ univariate polynomials are $0$ on $\mathbb{H}$. |
| zeromorph | evaluation on hypercube | Using remainder theorem to decompose multivariate polynomials, then directly mapping the values of decomposed polynomials on hypercube to univariate polynomials, proving equations about univariate polynomials hold and degree bounds of quotient polynomials.      |
| gemini    | coefficients form                     | Directly corresponding to coefficients of univariate polynomials, using split-and-fold to fold univariate polynomials until finally folded into a constant polynomial.                                   |

For zeromorph and gemini protocols, we provide some optimization ideas, resulting in multiple versions of these two protocols. The links to the protocol description documents and complexity analysis documents are shown in the table below.

| Protocol   | Version                       | Protocol Description Document | Protocol Analysis Document                                                  |
| --------- | ------------------- |  --- | ------------------------------------------------------------ |
| ph23      |                          | [PH23+KZG10 Protocol (Optimized Version)](https://github.com/sec-bit/mle-pcs/blob/main/ph23/ph23-pcs-02.md#2-ph23kzg10-protocol-optimized-version) | [ph23-analysis](https://github.com/sec-bit/mle-pcs/blob/main/analysis/ph23-analysis.md)            |
| gemini    | Optimization 1                    | [gemini-pcs-02](https://github.com/sec-bit/mle-pcs/blob/main/gemini/Gemini-PCS-2.md)                                                           | [gemini-analysis](https://github.com/sec-bit/mle-pcs/blob/main/analysis/gemini-analysis.md)        |
| gemini    | Optimization 2: Similar to FRI query optimization   | [gemini-pcs-03](https://github.com/sec-bit/mle-pcs/blob/main//gemini/Gemini-PCS-3.md)                                                          | [gemini-analysis](https://github.com/sec-bit/mle-pcs/blob/main/analysis/gemini-analysis.md)        |
| zeromorph | v1: batched degree bound | [Optimized Protocol](https://github.com/sec-bit/mle-pcs/blob/main/zeromorph/zeromorph.md#optimized-protocol)                                       | [zeromorph-anlysis](https://github.com/sec-bit/mle-pcs/blob/main/analysis/zeromorph-anlysis.md) |
| zeromorph | v2: optimized degree bound proof   | [Zeromorph-PCS (Part II)](https://github.com/sec-bit/mle-pcs/blob/main/zeromorph/zeromorph-02.md)                                                  | [zeromorph-anlysis](https://github.com/sec-bit/mle-pcs/blob/main/analysis/zeromorph-anlysis.md) |

Below is the complexity analysis result for these three protocols interfacing with KZG10, where the notation is as follows:

- $n$: Number of variables in the MLE polynomial.
- $N$: $N = 2^n$.
- $\mathbb{F}_{\mathsf{mul}}$: Multiplication operation on finite field $\mathbb{F}$. Addition operations on the finite field are not counted in complexity analysis.
- $\mathbb{F}_{\mathsf{inv}}$: Division operation on finite field $\mathbb{F}$.
- $\mathsf{msm}(m, \mathbb{G})$: Complexity of multi-scalar multiplication, where $m$ represents the number of scalars, and $\mathbb{G}$ represents the elliptic curve group.
- $\mathsf{EccMul}^{\mathbb{G}}$: Multiplication operation on elliptic curve group $\mathbb{G}$.
- $\mathsf{EccAdd}^{\mathbb{G}}$: Addition operation on elliptic curve group $\mathbb{G}$.
- $P$: Complexity of pairing operation between two elliptic curves.
- $D_{max}$: Maximum power of system parameters $[\tau^{D_{max}}]_1$ and $[\tau^{D_{max}}]_2$ generated in the setup phase of the KZG protocol.
- $\mathbb{G}_1$: First elliptic curve group.
- $\mathbb{G}_2$: Second elliptic curve group.

### PH23

In step 10 of [Round 3](https://github.com/sec-bit/mle-pcs/blob/main/ph23/ph23-pcs-02.md#round-3) of the PH23 protocol, the Prover needs to construct the Quotient polynomial $q_{\omega\zeta}(X)$:

$$
q_{\omega\zeta}(X) = \frac{z(X) - z(\omega^{-1}\cdot\zeta)}{X - \omega^{-1}\cdot\zeta}
$$

We considered two implementation methods for this calculation.

Method 1: The numerator and denominator polynomials are represented in coefficient form. When calculating the quotient polynomial, since the denominator is a linear polynomial, linear polynomial division can be used, with complexity $(N - 1) ~ \mathbb{F}_{\mathsf{mul}}$. This method yields the quotient polynomial in coefficient form. In subsequent steps of the protocol, the quotient polynomial needs to be committed and sent to the Verifier. Since $q_{\omega\zeta}(X)$ has degree $N - 2$, assuming the calculated coefficient form is $q_{\omega\zeta}^{(0)}, q_{\omega\zeta}^{(1)}, \ldots, q_{\omega\zeta}^{(N - 2)}$, the commitment to the quotient polynomial is:

$$
Q_{\omega\zeta} = q_{\omega\zeta}^{(0)} \cdot G + q_{\omega\zeta}^{(1)} \cdot (\tau \cdot G) + \cdots + q_{\omega\zeta}^{(N - 2)} \cdot (\tau^{N - 2} \cdot G)
$$

where $G$ is the generator of elliptic curve $\mathbb{G}_1$, and $(G, \tau G, \ldots, \tau^{N - 2}G)$ is the SRS of KZG10. This requires storing these SRS in memory.

Method 2: Calculate using point-value form. Calculate $[q_{\omega\zeta}(x)|_{x \in H}]$,
- First calculate $[(x - \omega^{-1} \cdot \zeta)^{-1}|_{x \in H}]$ using an efficient inversion algorithm, with complexity $\mathbb{F}_{\mathsf{inv}} + (3N - 3) ~ \mathbb{F}_{\mathsf{mul}}$.
- Calculate $[q_{\omega\zeta}(x)|_{x \in H}]$ with complexity $N ~ \mathbb{F}_{\mathsf{mul}}$.

The total complexity of this method for calculating the quotient polynomial is:

$$
\mathbb{F}_{\mathsf{inv}} + (4N - 3) ~ \mathbb{F}_{\mathsf{mul}}
$$

We can see that since the denominator is only a linear polynomial, method 1 is more efficient, at the cost of needing to store more SRS $(G, \tau G, \ldots, \tau^{N - 2}G)$ in memory.

Considering these two different implementation methods, the complexity of the PH23 protocol is:

**Prover's cost:**

1. Using coefficient form in Round 3-10, complexity is:

$$
\begin{align}
 (17nN + 36N + 9n - 2) ~ \mathbb{F}_{\mathsf{mul}} + {(n + 1) \log^2(n + 1)  ~ \mathbb{F}_{\mathsf{mul}} } + 2~ \mathbb{F}_{\mathsf{inv}} + 5 ~ \mathsf{msm}(N, \mathbb{G}_1) + 2 ~ \mathsf{msm}(N - 1, \mathbb{G}_1)
\end{align}
$$

This method requires storing SRS $(G, \tau G, \ldots, \tau^{N - 2}G)$ in memory for polynomial commitment in coefficient form.

2. Using method 2, point-value form, in Round 3-10, complexity is:

$$
\begin{align}
  (17nN + 39N + 9n - 4) ~ \mathbb{F}_{\mathsf{mul}} + { (n + 1) \log^2(n + 1)  ~ \mathbb{F}_{\mathsf{mul}} } + 3~ \mathbb{F}_{\mathsf{inv}} + 6 ~ \mathsf{msm}(N, \mathbb{G}_1) + \mathsf{msm}(N - 1, \mathbb{G}_1)
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


### gemini

#### gemini Optimization 1

**Prover's cost:**

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

#### gemini Optimization 2

**Prover's cost:**

$$
\begin{aligned}
     & (14 N + 6n - 11) ~ \mathbb{F}_{\mathsf{mul}} + (n + 1) ~ \mathbb{F}_{\mathsf{inv}} + \sum_{i = 1}^{n - 1} \mathsf{msm}(2^{i}, \mathbb{G}_1) + 2 ~ \mathsf{msm}(N - 1, \mathbb{G}_1)   \\
\end{aligned}
$$


**Verifier's cost:**

$$
8n ~ \mathbb{F}_{\mathsf{mul}} + (3n + 1) ~ \mathbb{F}_{\mathsf{inv}} + (2n + 4) ~ \mathsf{EccMul}^{\mathbb{G}_1} + (2n + 3) ~ \mathsf{EccAdd}^{\mathbb{G}_1} + 2~P
$$

**Proof size:**

$$
(n + 1) \cdot \mathbb{F}_p + (n + 1) \cdot \mathbb{G}_1
$$

Comparing these two protocols, we can see that the gemini Optimization 2 protocol reduces proof size by $n ~ \mathbb{F}_p$ at the cost of increasing the workload of both Prover and Verifier.

### Zeromorph

We performed detailed complexity analysis on three versions of the zeromorph protocol.

#### zeromorph-v1

We performed a detailed complexity analysis of two optimized versions of the Zeromorph protocol.

**Prover's cost:**

$$
\begin{align}
& (7N + 5n - 9) ~ \mathbb{F}_{\mathsf{mul}} + \sum_{k=0}^{n} \mathsf{msm}(2^k,\mathbb{G}_1) + \mathsf{msm}(D_{max} + 1, {\mathbb{G}_1})  \\
\end{align}
$$


**Verifier's cost:**

$$
(5n - 1) ~ \mathbb{F}_{\mathsf{mul}} + (2n + 2) ~ \mathsf{EccMul}^{\mathbb{G}_1} + (2n + 2) ~ \mathsf{EccAdd}^{\mathbb{G}_1} + \mathsf{EccMul}^{\mathbb{G}_2} + \mathsf{EccAdd}^{\mathbb{G}_2} + 2~P
$$

**Proof size:**

$$
(n + 2) ~ \mathbb{G}_1
$$



#### zeromorph-v2

**Prover's cost:**

$$
\begin{aligned}
    & (7N + 5n - 10) ~ \mathbb{F}_{\mathsf{mul}} + \mathbb{F}_{\mathsf{inv}} \\
    & + \sum_{k=0}^{n} \mathsf{msm}(2^k,\mathbb{G}_1) + \mathsf{msm}(2^{n - 1} , \mathbb{G}_1) + \mathsf{msm}(2^{n - 1} - 1, \mathbb{G}_1) + \mathsf{msm}(2^n - 1, \mathbb{G}_1)
\end{aligned}
$$

**Verifier's cost:**

$$
\begin{aligned}
    (5n - 1) ~ \mathbb{F}_{\mathsf{mul}} + \mathbb{F}_{\mathsf{inv}} + (2n + 6) ~ \mathsf{EccMul}^{\mathbb{G}_1} + (2n + 7) ~ \mathsf{EccAdd}^{\mathbb{G}_1}  + 2~P
\end{aligned}
$$

**Proof size:**

$$
\begin{aligned}
    (n + 3) \cdot \mathbb{G}_1 + \mathbb{F}_q
\end{aligned}
$$


#### Summary

Comparing the complexity analysis results of these protocols, we can see that the unoptimized zeromorph protocol has the largest msm operation length, $n ~ \mathsf{msm}(D_{max} + 1,\mathbb{G}_1)$, and the largest proof size, $(2n + 1) \mathbb{G}_1$. The detailed complexity analysis can be found in [zeromorph-anlysis](https://github.com/sec-bit/mle-pcs/blob/main/analysis/zeromorph-anlysis.md). Both zeromorph-v1 and zeromorph-v2 adopt different methods to optimize the degree bound proof, reducing the Prover's msm operations and decreasing the proof size by about $n ~ \mathbb{G}_1$. The main difference between zeromorph-v1 and zeromorph-v2 is that zeromorph-v2 avoids Verifier operations on the elliptic curve $\mathbb{G}_2$, at the cost of increasing constant-level computation for the Verifier on the elliptic curve $\mathbb{G}_1$ and a proof size of $\mathbb{G}_1 + \mathbb{F}_q$.

### Comparison

Referring to the theoretical analysis in the mercury paper [EG25], and combining the above analysis results, we compare the complexity of KZG10-based protocols.

| Protocol          | Prover's cost                                    | Verifier's cost                                  | Proof size                                      |
| ----------------- | ------------------------------------------------ | ------------------------------------------------ | ----------------------------------------------- |
| Libra-PCS         | $O(N) ~ \mathbb{F}, O(N) \mathbb{G}$             | $O(\log N) ~ \mathbb{G}, O(\log N) ~ \mathbb{P}$ | $O(\log N)~ \mathbb{F}, O(1) ~ \mathbb{G}$      |
| PH23-KZG          | $O(N\log N) ~ \mathbb{F}, O(N) \mathbb{G}$       | $O(\log N) ~ \mathbb{F}, O(1) ~ \mathbb{G}$      | $O(\log N)~ \mathbb{F}, O(1) ~ \mathbb{G}$      |
| gemini            | $O(N) ~ \mathbb{F}, O(N) \mathbb{G}$             | $O(\log N) ~ \mathbb{F}, O(n) ~ \mathbb{G}$      | $O(\log N)~ \mathbb{F}, O(\log N) ~ \mathbb{G}$ |
| hyperKZG          | $O(N) ~ \mathbb{F}, O(N) \mathbb{G}$             | $O(\log N) ~ \mathbb{F}, O(n) ~ \mathbb{G}$      | $O(\log N)~ \mathbb{F}, O(\log N) ~ \mathbb{G}$ |
| zeromorph-v0      | $O(N) ~ \mathbb{F}, O(N) \mathbb{G}$             | $O(\log N) ~ \mathbb{F}, O(\log N) ~ \mathbb{G}$ | $(2\log N + 1) ~ \mathbb{G}$                    |
| zeromorph-v1      | $O(N) ~ \mathbb{F}, O(N) \mathbb{G}$             | $O(\log N) ~ \mathbb{F}, O(\log N) ~ \mathbb{G}$ | $(\log N + 2) ~ \mathbb{G}$                     |
| zeromorph-v2      | $O(N) ~ \mathbb{F}, O(N) \mathbb{G}$             | $O(\log N) ~ \mathbb{F}, O(\log N) ~ \mathbb{G}$ | $\mathbb{F}, (\log N + 3) ~ \mathbb{G}$         |
| mercury [EG25]    | $O(N) ~ \mathbb{F}, 2N + O(\sqrt{N}) \mathbb{G}$ | $O(\log N) ~ \mathbb{F}, O(1) ~ \mathbb{G}$      | $O(1)~ \mathbb{F}, O(1) ~ \mathbb{G}$           |
| samaritan [GPS25] | $O(N) ~ \mathbb{F}, O(N) \mathbb{G}$             | $O(\log N) ~ \mathbb{F}, O(1) ~ \mathbb{G}$      | $O(1)~ \mathbb{F}, O(1) ~ \mathbb{G}$           |

Through comparison, we find:
1. In terms of Prover computational complexity, PH23 has the highest complexity, requiring $O(N\log N)$ level finite field calculations, while other protocols only need $O(N) ~ \mathbb{F}$ calculations.
2. In terms of Verifier computational complexity, all protocols require $O(\log N)$ finite field operations. PH23, mercury, and samaritan protocols only need constant-level calculations on elliptic curves, while other protocols require $O(\log N)$ level calculations on elliptic curves.
3. In terms of Proof size, mercury and samaritan protocols can achieve constant-level proof sizes. We found that the PH23 protocol, when using schemes similar to Plonk, can also achieve constant-size proofs, which we plan to describe in detail in future work.
Currently, it appears that mercury and SamaritanPCS are the most efficient protocols, achieving constant proof sizes without sacrificing the Prover's linear $O(N)$ finite field operations, rather than logarithmic level $O(\log N)$.

## Comparison of FRI-based MLE-PCS

We have detailed the protocol descriptions for PH23, gemini, and zeromorph interfacing with FRI. For the zeromorph-fri protocol using [mmcs](https://github.com/Plonky3/Plonky3/blob/main/merkle-tree/src/mmcs.rs) structure and optimized with rolling batch [ZLGSCLD24] techniques, we have analyzed its complexity in detail. Comparing with the Basefold protocol, we found that the Basefold protocol is superior to the zeromorph-fri protocol. Additionally, we compared the Basefold, Deepfold, and WHIR protocols from the perspective of Verifier query complexity.

| Protocol         | Version | Protocol Description Document | Protocol Analysis Document  |
| ------------- | ----- | ----- | ------- |
| basefold      |  | basefold paper [ZCF23] | [basefold-analysis](https://github.com/sec-bit/mle-pcs/blob/main/analysis/basefold-analysis.md)  |
| ph23-fri      | inner product using grand sum  | [Missing Protocol PH23-PCS (Part 4)](https://github.com/sec-bit/mle-pcs/blob/main/ph23/ph23-pcs-fri-01.md)  |  |
| ph23-fri      | inner product using univariate sumcheck  | [Missing Protocol PH23-PCS (Part 5)](https://github.com/sec-bit/mle-pcs/blob/main/ph23/ph23-pcs-fri-02.md)  | |
| gemini-fri    |  | [Gemini: Interfacing with FRI](https://github.com/sec-bit/mle-pcs/blob/main/gemini/gemini-fri)          |  |
| zeromorph-fri | directly interfacing with fri protocol | [Zeromorph-PCS: Integration with FRI](https://github.com/sec-bit/mle-pcs/blob/main/zeromorph/zeromorph-fri) |  |
| zeromorph-fri | optimized: using [mmcs](https://github.com/Plonky3/Plonky3/blob/main/merkle-tree/src/mmcs.rs) structure to commit quotient polynomials and rolling batch [ZLGSCLD24] technique | [Zeromorph-PCS: Integration with FRI](zeromorph/zeromorph-fri.md) | [zeromorph-fri-analysis](https://github.com/sec-bit/mle-pcs/blob/main/analysis/zeromorph-fri-analysis.md) |

### Basefold v.s. Zeromorph-fri

Below are the complexity analysis results for the basefold protocol and zeromorph-fri (optimized version), where the notation is as follows:

- $n$: Number of variables in the MLE polynomial.
- $N$: $N = 2^n$.
- $\mathcal{R}$: Blowup factor parameter in the FRI protocol, with the relationship to code rate being $\mathcal{R} = \rho^{-1}$.
- $l$: Number of queries made by the Verifier in the Query phase of FRI.
- $\mathbb{F}_{\mathsf{mul}}$: Multiplication operation on finite field $\mathbb{F}$.
- $\mathbb{F}_{\mathsf{inv}}$: Division operation on finite field $\mathbb{F}$.
- $\mathsf{MT.commit}(k)$: Computational cost for committing to a vector of length $k$ using a Merkle Tree.
- $H$: Hash computation.
- $\mathsf{MMCS.commit}(k_{n-1}, k_{n-2}, \ldots, k_{1})$: Computational cost for committing to $n - 1$ vectors of lengths $k_{n-1}, \ldots, k_1$ using the MMCS structure, which requires that $k_{i + 1}/k_i = 2$, i.e., the length of adjacent vectors differs by exactly a factor of $2$.
- $C$: Compression calculation in the MMCS structure.

#### Basefold

After analysis, the complexity of the basefold protocol is:

**Prover's cost:**

$$
\begin{aligned}
\left((\frac{5}{2} \mathcal{R} + 9) \cdot N + 3n - \frac{5}{2} \mathcal{R} - 13 \right) ~ \mathbb{F}_{\mathsf{mul}} + (\mathcal{R} \cdot N - \mathcal{R}) ~ \mathbb{F}_{\mathsf{inv}} + \sum_{i = 1}^{n - 1} \mathsf{MT.commit}(2^{i} \cdot \mathcal{R}) 
\end{aligned}
$$

Adding the algorithmic complexity for the Prover to compute encoding $\pi_n$, the total complexity is:

$$
\left(\frac{\mathcal{R}}{2} \cdot nN + (\frac{5}{2} \mathcal{R} + 9) \cdot N + 3n - \frac{5}{2} \mathcal{R} - 13 \right) ~ \mathbb{F}_{\mathsf{mul}} + (\mathcal{R} \cdot N - \mathcal{R}) ~ \mathbb{F}_{\mathsf{inv}} + \sum_{i = 1}^{n - 1} \mathsf{MT.commit}(2^{i} \cdot \mathcal{R}) 
$$

**Proof size:**

$$
\begin{align}
((2l + 3)n + \mathcal{R}) ~ \mathbb{F} + \left( \frac{l}{2} \cdot n^2 + \left(\log \mathcal{R} \cdot l +\frac{1}{2} \cdot l + 1\right) \cdot n \right) ~ H 
\end{align}
$$

**Verifier's cost:**

$$
\begin{align}
\left( \frac{l}{2} \cdot n^2 + (l\log \mathcal{R} + \frac{l}{2})n \right)  ~ H + (5l + 12)n ~ \mathbb{F}_{\mathsf{mul}} + ((2l + 5)n + 1) ~ \mathbb{F}_{\mathsf{inv}}
\end{align}
$$

#### Zeromorph-fri

The complexity of the Zeromorph-fri protocol is:

**Prover's Cost:**
$$
\begin{align}
& (2\mathcal{R}\cdot nN + (2\mathcal{R} \log \mathcal{R} + 7 \mathcal{R} + 3) \cdot  N + n -  \mathcal{R}\log \mathcal{R} - 4 \mathcal{R} - 3) ~\mathbb{F}_{\mathsf{mul}} + (3 \mathcal{R} \cdot N - 2 \mathcal{R} + 1) ~\mathbb{F}_{\mathsf{inv}} \\
& + \mathsf{MMCS.commit}(2^{n-1} \cdot \mathcal{R}, \ldots, \mathcal{R}) + \sum_{i = 1}^{n - 1}\mathsf{MT.commit}(2^{i} \cdot \mathcal{R})
\end{align}
$$

**Proof size:**
$$
\begin{align}
((2l + 1) \cdot n + 3l) ~ \mathbb{F} + (\frac{3}{2} l \cdot n^2  + (3\log \mathcal{R}l  - \frac{1}{2}l + 1) n  - l + 1)  ~ H
\end{align}
$$

**Verifier's Cost:**

$$
\begin{aligned}
  & (ln^2 + (2 \log \mathcal{R}l - l) n + l - 2 \log \mathcal{R}l) ~C + (\frac{l}{2} n^2 + (\frac{3l}{2} + \log \mathcal{R}l)n - l) ~H  \\
 & + ((7l + 5)n + 5l + 1) ~ \mathbb{F}_{\mathsf{mul}} + ((3l + 1)n + 2l) ~ \mathbb{F}_{\mathsf{inv}}
\end{aligned}
$$

#### Comparison Results

Below is a comparison of the complexity of the Basefold protocol and the zeromorph-fri protocol.

**Prover's cost**

Subtracting the Prover cost of basefold (including encoding complexity) from zeromorph-fri's Prover cost:

$$
\begin{align}
& (2\mathcal{R}\cdot nN + (2\mathcal{R} \log \mathcal{R} + 7 \mathcal{R} + 3) \cdot  N + n -  \mathcal{R}\log \mathcal{R} - 4 \mathcal{R} - 3) ~\mathbb{F}_{\mathsf{mul}} + (3 \mathcal{R} \cdot N - 2 \mathcal{R} + 1) ~\mathbb{F}_{\mathsf{inv}} \\
& + \mathsf{MMCS.commit}(2^{n-1} \cdot \mathcal{R}, \ldots, \mathcal{R}) + \sum_{i = 1}^{n - 1}\mathsf{MT.commit}(2^{i} \cdot \mathcal{R}) \\
 & - \left(\left(\frac{\mathcal{R}}{2} \cdot nN + (\frac{5}{2} \mathcal{R} + 9) \cdot N + 3n - \frac{5}{2} \mathcal{R} - 13 \right) ~ \mathbb{F}_{\mathsf{mul}} + (\mathcal{R} \cdot N - \mathcal{R}) ~ \mathbb{F}_{\mathsf{inv}} + \sum_{i = 1}^{n - 1} \mathsf{MT.commit}(2^{i} \cdot \mathcal{R})  \right) \\
=  & ( \frac{3}{2}\mathcal{R}\cdot nN + (2\mathcal{R} \log \mathcal{R} + \frac{9}{2} \mathcal{R} - 6) \cdot  N - 2 \cdot n -  \mathcal{R}\log \mathcal{R} - \frac{3}{2}\mathcal{R} + 10) ~\mathbb{F}_{\mathsf{mul}} + (2 \mathcal{R} \cdot N - \mathcal{R} + 1) ~\mathbb{F}_{\mathsf{inv}} \\
& + \mathsf{MMCS.commit}(2^{n-1} \cdot \mathcal{R}, \ldots, \mathcal{R}) \\
\end{align}
$$

It can be seen that basefold has much less computational cost than zeromorph-fri, manifested in finite field multiplication calculations, inversion operations, and hash calculations for Merkle Tree commitments.

- Finite field multiplication: zeromorph-fri produces $2 \mathcal{R} \cdot nN$ finite field multiplications, mainly from calculating $\{[\hat{q}_k(x)|_{x \in D^{(k)}}]\}_{k = 0}^{n - 1}$ and $[f(x)|_{x \in D}]$, involving FFT operations, while basefold only has $\frac{\mathcal{R}}{2} \cdot nN ~ \mathbb{F}_{\mathsf{mul}}$ computational complexity during the encoding process.
- Hash calculation: zeromorph-fri not only needs to commit to the original polynomial $f(X)$, but also to $n$ quotient polynomials, using the MMCS structure for commitment, naturally incurring more hash calculations than the Basefold protocol.

**Proof size**

Subtracting basefold's proof size from zeromorph-fri's proof size:

$$
\begin{align}
 & ((2l + 1) \cdot n + 3l) ~ \mathbb{F} + (\frac{3}{2} l \cdot n^2  + (3\log \mathcal{R}l  - \frac{1}{2}l + 1) n  - l + 1)  ~ H \\
 & - \left(((2l + 3)n + \mathcal{R}) ~ \mathbb{F} + \left( \frac{l}{2} \cdot n^2 + \left(\log \mathcal{R} \cdot l +\frac{1}{2} \cdot l + 1\right) \cdot n \right) ~ H \right) \\
=  & (-2n + 3l - \mathcal{R}) ~ \mathbb{F} + \left(l \cdot n^2 + (2\log \mathcal{R} \cdot l - l) n - l + 1\right) ~H
\end{align}
$$

It can be seen that basefold has a smaller proof size than zeromorph-fri, sending about $ln^2$ fewer hash values.

**Verifier's Cost**

Subtracting basefold's verifier cost from zeromorph-fri's verifier cost:

$$
\begin{align} \\
  & (ln^2 + (2 \log \mathcal{R}l - l) n + l - 2 \log \mathcal{R}l) ~C + (\frac{l}{2} n^2 + (\frac{3l}{2} + \log \mathcal{R}l)n - l) ~H  \\
 & + ((7l + 5)n + 5l + 1) ~ \mathbb{F}_{\mathsf{mul}} + ((3l + 1)n + 2l) ~ \mathbb{F}_{\mathsf{inv}} \\
 & - \left(\left( \frac{l}{2} \cdot n^2 + (l\log \mathcal{R} + \frac{l}{2})n \right)  ~ H + (5l + 12)n ~ \mathbb{F}_{\mathsf{mul}} + ((2l + 5)n + 1) ~ \mathbb{F}_{\mathsf{inv}}\right) \\
=  & (ln^2 + (2 \log \mathcal{R}l - l) n + l - 2 \log \mathcal{R}l) ~C + \left(ln - l \right) ~ H\\
  & + ((2l - 7)n + 5l + 1) ~ \mathbb{F}_{\mathsf{mul}} + ((l - 4)n + 2l - 1) ~ \mathbb{F}_{\mathsf{inv}} \\
\end{align}
$$

It can be seen that basefold has a smaller verifier cost than zeromorph-fri.

Considering the computational amount in these three aspects, we can conclude that the Basefold protocol is superior to the Zeromorph-fri protocol.

### Comparing Basefold, Deepfold, and WHIR

The comparison between Basefold, Deepfold, and WHIR protocols is detailed in the blog post [BaseFold vs DeepFold vs WHIR]([mle-pcs/basefold-deepfold-whir/basefold-deepfold-whir.md at main · sec-bit/mle-pcs · GitHub](https://github.com/sec-bit/mle-pcs/blob/main/analysis/basefold-deepfold-whir.md)), which mainly describes the efficiency comparison results of these three protocols.

Basefold, Deepfold, and WHIR protocols are very similar in protocol framework, all following the BaseFold protocol framework, synchronously performing the sumcheck protocol and FRI/DEEP-FRI/STIR protocol with the same random numbers. The main differences between them come from the differences between the FRI protocol, DEEP-FRI protocol, and STIR protocol.

Comparing the efficiency of these three protocols, the Prover's computational amount doesn't differ significantly, mainly depending on the number of Verifier queries. More queries lead to larger Verifier computational cost and proof size. Since the STIR protocol theoretically has better query complexity than the FRI and DEEP-FRI protocols, the WHIR protocol has fewer queries compared to the BaseFold and DeepFold protocols.

On the other hand, the number of Verifier queries is related to the bound that can be achieved in the soundness proof of the protocol:

1. The DeepFold protocol based on the DEEP-FRI protocol can achieve the optimal bound $1 - \rho$ based on a simple conjecture. For the FRI protocol to reach the $1 - \rho$ bound, it would require a stronger conjecture (see [BCIKS20] Conjecture 8.4).
2. The BaseFold protocol can reach the Johnson bound $1 - \sqrt{\rho}$ for Reed Solomon encoding.
3. The WHIR protocol is only proven in the original paper to reach $(1 - \rho)/2$, but based on the method in [H24], it is promising to prove it reaches the Johnson bound $1 - \sqrt{\rho}$.

## Bulletproofs-based MLE-PCS 

Bulletproofs-based MLE-PCS include [Hyrax](https://eprint.iacr.org/2017/1132.pdf) and [Σ-Check](https://eprint.iacr.org/2024/1654).

### Hyrax

Multilinear polynomial evaluations can be viewed as inner-product relations and thus can be proven directly using inner-product arguments (IPAs), such as Bulletproofs. However, a major drawback of Bulletproofs is their linear verification time: for an $n$-variate multilinear polynomial, verification requires $O(2^n)$ time.

To address this inefficiency, the [Hyrax](https://eprint.iacr.org/2017/1132.pdf) PCS observes that polynomial evaluation can be reformulated as a matrix product. For example, consider $f(z_0, z_1, z_2, z_3) = v$. We can write:
$$
\tilde{f}(z_0, z_1, z_2, z_3) = 
\begin{bmatrix}
1 & z_2 & z_3 & z_2z_3 \\
\end{bmatrix}
\begin{bmatrix}
f_0 & f_1 & f_2 & f_3 \\
f_4 & f_5 & f_6 & f_7 \\
f_8 & f_9 & f_{10} & f_{11} \\
f_{12} & f_{13} & f_{14} & f_{15}
\end{bmatrix}
\begin{bmatrix}
1 \\
z_0 \\
z_1 \\
z_0z_1 \\
\end{bmatrix}.
$$
Let $F$ denote the inner matrix, $\vec{z}_1 := (1, z_2, z_3, z_2z_3)$, and $\vec{z}_0 := (1, z_0, z_1, z_0z_1)$. In the Hyrax protocol, the prover first sends $\vec{w} = \vec{z}_1 \cdot F$, enabling the verifier to check that $\vec{w} \cdot \vec{z}_0^\top = v$. To ensure that $\vec{w}$ is computed correctly, the verifier issues a random challenge vector $\vec{r}$, and the prover responds with $\vec{t}^\top := F \cdot \vec{r}^\top$. This leads to the relation $\vec{z}_1 \cdot \vec{t}^\top = \vec{z}_1 \cdot F \cdot \vec{r}^\top = \vec{w} \cdot \vec{r}^\top$, which holds if and only if $\vec{w}$ is correctly computed. 

As a result, the verifier only needs to compute two inner products of length $\sqrt{N}$ ($N = 2^n$), achieving sublinear verification cost. Furthermore, the prover can use an IPA to prove these inner-product relations, reducing the proof size to $O(\log n)$.

### Σ-Check

To prove a single evaluation relation $f(\vec{z}) = v$, Σ-Check employs an improved sumcheck protocol. In each round, the prover sends a linear polynomial $f_i(X) := f(r_1, \cdots, r_{i-1}, X, z_{i+1}, \cdots, z_n)$, while the verifier checks the following condition: 
$$
f_i(0) \cdot \mathsf{eq}(0, z_i) + f_i(1) \cdot \mathsf{eq}(1, z_i) \overset{?}{=} f_{i-1}(r_{i-1}).
$$ 
This approach reduces the proof size by $n$ compared to directly applying sumcheck, as in BaseFold.

When proving $k$ evaluation relations $(f_i(\vec{z}_i) = v_i)_{i = 1}^k$,  Σ-Check interpolates all $f_i(\vec{X})$ as a single function $f(\vec{y}, \vec{X})$ over a hypercube $\vec{y} \in \{0, 1\}^{\log k}$. Similarly, $\vec{z}(\vec{y})$ and $v(\vec{y})$ are defined. Given a challenge $\vec{\alpha} \in \mathbb{F}^{\log k}$, the prover can then use the improved sumcheck protocol to prove the following relation:
$$
\sum_{\vec{y} \in \{0, 1\}^{\log k}} \mathsf{eq}(\vec{\alpha}, \vec{y}) \cdot \big( f(\vec{y}, \vec{z}(\vec{y})) - v(\vec{y}) \big).
$$
After the sumcheck, this reduces to the relation $f(\vec{r}, \vec{z}(\vec{r})) - v(\vec{r}) = s$.

Since $\vec{z}(\vec{Y})$ and $v(\vec{Y})$ are public, the verifier can compute them directly. Let $f_r(\vec{X}) := f(\vec{r}, \vec{X})$, $\vec{z}_r := \vec{z}(\vec{r})$, and $v_r := v(\vec{r})$. The output relation then becomes $f_r(\vec{z}_r) = s + v_r$, which is itself an evaluation proof and can be handled by another sumcheck protocol.

It is worth noting that Σ-Check can also serve as an inner product argument (IPA), as described in Section 4.1 of [GZQ+24](https://eprint.iacr.org/2024/1654)). This enables sublinear verification when combined with the Hyrax IOP. We summarize the performance as follows.

| Scheme                  | Prover Time                                              | Verifier Time                                              | Proof Size                        |
| ----------------------- | -------------------------------------------------------- | ---------------------------------------------------------- | --------------------------------- |
| $\Sigma$-Check (as PCS) | $O(k+N)$ $\mathbb{F}$, $O(N)$ $\mathbb{G}$               | $O(k+N)$ $\mathbb{F}$, $O(k+N)$ $\mathbb{G}$               | $2(\log k + \log N)$ $\mathbb{G}$ |
| $\Sigma$-Check (as IPA) | $O(k+\sqrt{N})$ $\mathbb{F}$, $O(\sqrt{N})$ $\mathbb{G}$ | $O(k+\sqrt{N})$ $\mathbb{F}$, $O(k+\sqrt{N})$ $\mathbb{G}$ | $2(\log k + \log N)$ $\mathbb{G}$ |

## Lattice-based PCS

### Greyhound

Greyhound is a lattice-based PCS that relies on Labrador—a lattice-based interactive proof for proving inner product relations.

Structurally similar to Brakedown, Greyhound first abstracts the polynomial evaluation process as the inner product of two long vectors:

$$
v = \langle \vec{f}, \vec{u} \rangle
$$

where $\vec{f}$ is the coefficient vector of polynomial $f(X) = \sum_{i=0}^{N-1} f_i X^i$, and $\vec{u} = (1, u, u^2, \dots, u^{N-1})$ is a power vector. Then, it parses the coefficient vector $\vec{f}$ as an $n \times n$ matrix $F$, where $n = \sqrt{N}$, and writes $\vec{u}$ as the tensor product of two vectors:

$$
\vec{a} = (1, u, u^2, \dots, u^{n-1}), \quad \vec{b} = (1, u^n, u^{2n}, \dots, u^{(n-1)n}), \quad \vec{b} \otimes \vec{a} = \vec{u}.
$$

In the proof process, the Prover first calculates $F\cdot \vec{a}$ to obtain an intermediate result vector $\vec{w}$, which is sent to the Verifier. The Verifier checks if the inner product of $\vec{w}$ and $\vec{b}$ equals v, verifying:

$$
v ?= \langle \vec{w}, \vec{b} \rangle.
$$

Next, the Verifier generates a random challenge vector $\vec{c}$ of length n, the Prover calculates $\vec{z} = \vec{c}^TF$ and sends it to the Verifier. The Verifier verifies the correctness of \vec{w} through the following relation:

$$
\langle \vec{a}, \vec{z} \rangle ?= \langle \vec{w}, \vec{c} \rangle.
$$

Obviously, by expanding the one-dimensional coefficient vector into a two-dimensional matrix, the protocol's proof size and verification time are significantly optimized, reduced to sublinear levels.

The security of Greyhound is based on the MSIS (Modular Short Integer Solution) problem on lattices. By decomposing each column of the coefficient matrix with $\delta$ as the base, n short vectors of length nl can be obtained, where $l = \log_\delta q$. Subsequently, Ajtai Commit is performed on each short vector to generate corresponding commitment values.

### Hyperwolf

Inspired by Greyhound, our latest research achievement Hyperwolf further optimizes the structure, generalizing it to k dimensions, with overall efficiency reaching $O(kN^{1/k})$. By setting $k = \log N$, the scheme successfully achieves log-level proof size and verification time, significantly enhancing performance.

Specifically, we interpret the one-dimensional coefficient vector of length $N$ as a $k$-dimensional hypercube $[F]^{(k)}$ with dimensions $b \times b \times \cdots \times b$ (a total of $k$ dimensions), satisfying $b^k = N$, and construct $k$ auxiliary vectors $(\vec{a}_i)_{i \in [k]}$, where:

$$
\vec{a}_i = (1, u^{b^{i}}, u^{2b^{i}}, \cdots, u^{(b-1)b^{i}})
$$

satisfying:

$$
\vec{a}_{k-1} \otimes \vec{a}_{k-2} \otimes \cdots \otimes \vec{a}_0 = \vec{u}.
$$

Based on this, the PCS evaluation process can be described as:

$$
v = \left( \mathcal{F}\left( \cdots \left( \mathcal{F}\left( \mathcal{F}([F]^{(k)}) \cdot \vec{a}_0 \right) \cdot \vec{a}_1 \right) \cdot \vec{a}_2 \right) \cdots \right) \cdot \vec{a}_{k-1}.
$$

where function $\mathcal{F}$ maps a $(k-i)$-dimensional hypercube of size $b_{k-1} \times b_{k-2} \times \cdots \times b_i$ to a $(k-i-1)$-dimensional hypercube matrix of size $(b_{k-1} \cdots b_{i+1}) \times b_i$, where $i \in [k]$.

When $k=2$, this evaluation process is identical to that of Greyhound.

The figure below illustrates the evaluation process for $k=3$:

![lattice.png](img/lattice.png)

Our proof protocol consists of $k$ rounds of interaction, each round can be viewed as reducing a higher-dimensional relation by one dimension.

In the 0th round, the Prover first sends the intermediate result to the Verifier:

$$
\mathsf{fold}^{(k)} = \mathcal{F}(\cdots(\mathcal{F}(\mathcal{F}([F]^{(k)}) \cdot \vec{a}_0) \cdot \vec{a}_1) \cdots \vec{a}_{k-2}),
$$

The Verifier then verifies if it satisfies the inner product relation $\langle \mathsf{fold}^{(k)}, \vec{a}_{k-1} \rangle = v$. To further verify the correctness of $\mathsf{fold}^{(k)}$, the Verifier randomly generates a challenge vector $\vec{c}^{(k)}$ of length $b$. The Prover uses $\vec{c}^{(k)}$ to fold the $k$-dimensional hypercube $[F]^{(k)}$, reducing its dimension to a $(k-1)$-dimensional hypercube $[F]^{(k-1)}$, i.e.:

$$
[F]^{(k-1)} =(\vec{c}^{(k)})^T\cdot([F]^{(k)}) .
$$

This is equivalent to a $1 \times b$ vector multiplying a $b \times (b\times b\times … \times b)$ matrix.

Simultaneously, the Verifier updates the verification value:

$$
y = \langle \mathsf{fold}^{(k)}, \vec{c}^{(k)} \rangle.
$$

In each subsequent round, the Prover and Verifier repeat similar interactions:

For any round $i$, the Prover sends the intermediate result $\mathsf{fold}^{(k-i)}$ to the Verifier, the Verifier checks if $\langle \mathsf{fold}^{(k-i)}, \vec{a}_{k-i-1} \rangle = y$ holds, and generates a new challenge vector $\vec{c}^{(k-i)}$. The Prover uses this challenge to fold the witness, reducing its dimension, while the Verifier simultaneously updates the verification value $y$. After each round, the witness's dimension is reduced from $k-i$ to $k-i-1$.

After $k-2$ rounds, the witness is compressed into a one-dimensional vector $\vec{f}^{(1)}$. At this point, the Prover sends this one-dimensional vector $\vec{f}^{(1)}$ directly to the Verifier, who finally verifies if it satisfies the following relation:

$$
\langle \vec{f}^{(1)}, \vec{a}_0 \rangle = \langle \mathsf{fold}^{(2)}, \vec{c}^{(2)} \rangle.
$$

In the above interaction process, the proof size sent in each round is $O(b) = O(N^{1/k})$, and the cost for the Verifier to perform checks and update parameters is also $O(N^{1/k})$. Therefore, the total proof size and verification cost for $k$ rounds are both $O(kN^{1/k})$. When $k = \log N$, this value can be optimized to the $O(\log N)$ level.

## Future work

This project has not yet deeply compared PCS using Small Fields, which would significantly enhance Prover performance. This will be our next area of focus. Additionally, besides RS Code, linear codes with better encoding performance, such as Spelman Code, are often used to construct PCS, like brakedown and orion. Furthermore, there are some new Binary Field-based PCS protocols, and some of the protocols analyzed above can also be used for Binary Fields, like FRI and Ligerito.

## References

- [ACFY24a] Gal Arnon, Alessandro Chiesa, Giacomo Fenzi, and Eylon Yogev. "STIR: Reed-Solomon proximity testing with fewer queries." In _Annual International Cryptology Conference_, pp. 380-413. Cham: Springer Nature Switzerland, 2024.
- [ACFY24b] Gal Arnon, Alessandro Chiesa, Giacomo Fenzi, and Eylon Yogev. "WHIR: Reed–Solomon Proximity Testing with Super-Fast Verification." _Cryptology ePrint Archive_ (2024).
- [AHIV17] Scott Ames, Carmit Hazay, Yuval Ishai, and Muthuramakrishnan Venkitasubramaniam. Ligero: lightweight sublinear arguments without a trusted setup”. 2022. https://eprint.iacr.org/2022/1608.pdf
- [BBB+18] Bünz, Benedikt, Jonathan Bootle, Dan Boneh, Andrew Poelstra, Pieter Wuille, and Greg Maxwell. "Bulletproofs: Short proofs for confidential transactions and more." In 2018 IEEE symposium on security and privacy (SP), pp. 315-334. IEEE, 2018. https://eprint.iacr.org/2017/1066 
- [BBHR18] Eli Ben-Sasson, Iddo Bentov, Yinon Horesh, and Michael Riabzev. “Fast Reed–Solomon Interactive Oracle Proofs of Proximity”. In: *Proceedings of the 45th International Colloquium on Automata, Languages and Programming (ICALP)*, 2018.
- [BCC+16] Jonathan Bootle, Andrea Cerulli, Pyrros Chaidos, Jens Groth, and Christophe Petit. "Efficient Zero-Knowledge Arguments for Arithmetic Circuits in the Discrete Log Setting."  In Advances in Cryptology–EUROCRYPT 2016: 35th Annual International Conference on the Theory and Applications of Cryptographic Techniques, Vienna, Austria, May 8-12, 2016, Proceedings, Part II 35, pp. 327-357. Springer Berlin Heidelberg, 2016.  https://eprint.iacr.org/2016/263 
- [BCH+22] Bootle, Jonathan, Alessandro Chiesa, Yuncong Hu, et al. "Gemini: Elastic SNARKs for Diverse Environments." *Cryptology ePrint Archive* (2022). [https://eprint.iacr.org/2022/420](https://eprint.iacr.org/2022/420)
- [BCIKS20] Eli Ben-Sasson, Dan Carmon, Yuval Ishai, Swastik Kopparty, and Shubhangi Saraf. Proximity Gaps for Reed–Solomon Codes. In *Proceedings of the 61st Annual IEEE Symposium on Foundations of Computer Science*, pages 900–909, 2020.
- [BGKS20] Eli Ben-Sasson, Lior Goldberg, Swastik Kopparty, and Shubhangi Saraf. DEEP-FRI: sampling outside the box improves soundness. In *Thomas Vidick, editor, 11th Innovations in Theoretical Computer Science Conference, ITCS 2020, January 12-14, 2020, Seattle, Washington, USA, volume 151 of LIPIcs*, pages 5:1–5:32. Schloss Dagstuhl - Leibniz-Zentrum für Informatik, 2020.
- [BSK18] Eli Ben-Sasson, Swastik Kopparty, and Shubhangi Saraf. Worst-case to average case reductions for the distance to a code. In *33rd Computational Complexity Conference, CCC 2018, June 22-24, 2018, San Diego, CA, USA*, pages 24:1–24:23, 2018.
- [CBBZ22] Chen, Binyi, Benedikt Bünz, Dan Boneh, and Zhenfei Zhang. "Hyperplonk: Plonk with linear-time prover and high-degree custom gates." In _Annual International Conference on the Theory and Applications of Cryptographic Techniques_, pp. 499-530. Cham: Springer Nature Switzerland, 2023.
- [CHM+20] Alessandro Chiesa, Yuncong Hu, Mary Maller, Pratyush Mishra, Psi Vesely, and Nicholas Ward. "Marlin: Preprocessing zkSNARKs with universal and updatable SRS." Advances in Cryptology–EUROCRYPT 2020: 39th Annual International Conference on the Theory and Applications of Cryptographic Techniques, Zagreb, Croatia, May 10–14, 2020.
- [DP23a] Benjamin Diamond and Jim Posen. Proximity Testing with Logarithmic Randomness. 2023. https://eprint.iacr.org/2023/630.pdf
- [DP23b] Diamond, Benjamin E., and Jim Posen. "Succinct arguments over towers of binary fields." Cryptology ePrint Archive (2023).
- [DP24] Diamond, Benjamin E., and Jim Posen. "Polylogarithmic Proofs for Multilinears over Binary Towers." Cryptology ePrint Archive (2024).
- [EG25] Eagen, Liam, and Ariel Gabizon. "MERCURY: A multilinear Polynomial Commitment Scheme with constant proof size and no prover FFTs." Cryptology ePrint Archive (2025). [https://eprint.iacr.org/2025/385](https://eprint.iacr.org/2025/385)
- [GLHQTZ24] Yanpei Guo, Xuanming Liu, Kexi Huang, Wenjie Qu, Tianyang Tao, and Jiaheng Zhang. "DeepFold: Efficient Multilinear Polynomial Commitment from Reed-Solomon Code and Its Application to Zero-knowledge Proofs." _Cryptology ePrint Archive_ (2024).
- [GPS25] Ganesh, Chaya, Sikhar Patranabis, and Nitin Singh. "Samaritan: Linear-time Prover SNARK from New Multilinear Polynomial Commitments." _Cryptology ePrint Archive_ (2025). https://eprint.iacr.org/2025/419
- [GQZGX24] Shang Gao, Chen Qian, Tianyu Zheng, Yu Guo, and Bin Xiao. "$\Sigma$-Check: Compressed $\Sigma$-protocol Theory from Sum-check." (2024). https://eprint.iacr.org/2024/1654
- [Gru24] Angus Gruen. "Some Improvements for the PIOP for ZeroCheck". (2024). https://eprint.iacr.org/2024/108.
- [GWC19] Ariel Gabizon, Zachary J. Williamson, and Oana Ciobotaru. "Plonk: Permutations over lagrange-bases for oecumenical noninteractive arguments of knowledge." *Cryptology ePrint Archive* (2019).
- [H22] Ulrich Haböck. "A summary on the FRI low degree test." _Cryptology ePrint Archive_ (2022).
- [H24] Ulrich Haböck. "Basefold in the List Decoding Regime." _Cryptology ePrint Archive_(2024).
- [HPS23] Lipmaa, Helger, Roberto Parisella, and Janno Siim. "Algebraic group model with oblivious sampling." *Theory of Cryptography Conference*. Cham: Springer Nature Switzerland, 2023.
- [KT23] Kohrita, Tohru, and Patrick Towa. "Zeromorph: Zero-knowledge multilinear-evaluation proofs from homomorphic univariate commitments." Cryptology ePrint Archive (2023). https://eprint.iacr.org/2023/917 
- [KZG10] Kate, Aniket, Gregory M. Zaverucha, and Ian Goldberg. "Constant-size commitments to polynomials and their applications." In _International conference on the theory and application of cryptology and information security_, pp. 177-194. Berlin, Heidelberg: Springer Berlin Heidelberg, 2010.
- [LPS24] Lipmaa, Helger, Roberto Parisella, and Janno Siim. "Constant-size zk-SNARKs in ROM from falsifiable assumptions." Annual International Conference on the Theory and Applications of Cryptographic Techniques. Cham: Springer Nature Switzerland, 2024.
- [MBKM19] Mary Maller, Sean Bowe, Markulf Kohlweiss, and Sarah Meiklejohn, et al. "Sonic: Zero-knowledge SNARKs from linear-size universal and updatable structured reference strings". Proceedings of the 2019 ACM SIGSAC conference on computer and communications security, 2019.
- [NA25] Andrija Novakovic and Guillermo Angeris. Ligerito: A Small and Concretely Fast Polynomial Commitment Scheme. 2025. https://angeris.github.io/papers/ligerito.pdf.
- [NS24] Ngoc Khanh Nguyen and Gregor Seiler. Greyhound: Fast Polynomial Commitments from Lattices. 2024.  Cryptology ePrint Archive (2024).https://eprint.iacr.org/2024/1293
- [PH23] Papini, Shahar, and Ulrich Haböck. "Improving logarithmic derivative lookups using GKR." Cryptology ePrint Archive (2023). [https://eprint.iacr.org/2023/1284](https://eprint.iacr.org/2023/1284)
- Plonky3. https://github.com/Plonky3/Plonky3

- [PST13] Papamanthou, Charalampos, Elaine Shi, and Roberto Tamassia. "Signatures of correct computation." Theory of Cryptography Conference. Berlin, Heidelberg: Springer Berlin Heidelberg, 2013. https://eprint.iacr.org/2011/587
- [WTSTW16] Riad S. Wahby, Ioanna Tzialla, abhi shelat, Justin Thaler, and Michael Walfish. "Doubly-efficient zkSNARKs without trusted setup."  In 2018 IEEE Symposium on Security and Privacy (SP), pp. 926-943. IEEE, 2018.  https://eprint.iacr.org/2016/263 
- [XZZPS19] Tiancheng Xie, Jiaheng Zhang, Yupeng Zhang, Charalampos Papamanthou, and Dawn Song. "Libra: Succinct Zero-Knowledge Proofs with Optimal Prover Computation." Cryptology ePrint Archive (2019). https://eprint.iacr.org/2019/317
- [ZCF23] Hadas Zeilberger, Binyi Chen, and Ben Fisch. "BaseFold: efficient field-agnostic polynomial commitment schemes from foldable codes." Annual International Cryptology Conference. Cham: Springer Nature Switzerland, 2024.
- [ZLGSCLD24] Zhang, Zongyang, Weihan Li, Yanpei Guo, Kexin Shi, Sherman SM Chow, Ximeng Liu, and Jin Dong. "Fast {RS-IOP} Multivariate Polynomial Commitments and Verifiable Secret Sharing." In _33rd USENIX Security Symposium (USENIX Security 24)_, pp. 3187-3204. 2024.
- [ZGX25] Lizhen Zhang, Shang Gao, and Bin Xiao.  HyperWolf: Efficient Polynomial Commitment Schemes from Lattices. Cryptology ePrint Archive (2025).https://eprint.iacr.org/2025/922 .
- [ZSCZ24] Zhao, Jiaxing, Srinath Setty, Weidong Cui, and Greg Zaverucha. "MicroNova: Folding-based arguments with efficient (on-chain) verification." _Cryptology ePrint Archive_ (2024).
- [ZXZS19] Jiaheng Zhang, Tiancheng Xie, Yupeng Zhang, and Dawn Song. "Transparent Polynomial Delegation and Its Applications to Zero Knowledge Proof". In 2020 IEEE Symposium on Security and Privacy (SP), pp. 859-876. IEEE, 2020. https://eprint.iacr.org/2019/1482.
