# Gemini-PCS-1

- Tianyu ZHENG [tian-yu.zheng@connect.polyu.hk](mailto:tian-yu.zheng@connect.polyu.hk)

Gemini [BCH+22] is an elastic SNARK, where "elastic" means that the prover can balance between his time and memory by setting parameters to meet the requirements of different use cases.

As the core algorithm of Gemini, the Tensor Product Check provides a method for proving the evaluation of a multilinear polynomial, such as $\tilde{f}(\vec{\rho}) = u$. In other words, this method achieves a transformation from multivariable polynomials to univariate polynomials, inspiring us to construct a new multilinear polynomial commitment scheme.

In its specific construction, the Tensor Product Check adopts a split-and-fold approach similar to previous works (Sumcheck, Bulletproofs, FRI), achieving efficient communication and verifier complexity, while its prover algorithm can realize the elastic property.

# MLE and Tensor Product

In the Zeromorph notes, we mentioned that a Multilinear Extension uniquely corresponds to a function mapping from Boolean vectors to a finite field, of the form $f: \{0,1\}^n \rightarrow \mathbb{F}_q$. The figure below is an example of a three-dimensional MLE polynomial $\tilde{f}(X_0,X_1,X_2)$, which can be uniquely represented by the "point-value vector" $(a_0, a_1,...,a_7)$.

<img src="image/mle.png" align=center width="40%">

Similarly, an MLE polynomial can also be represented in "coefficient form", for example, the above figure can be written as

$$
\tilde{f}(X_0,X_1,X_2) = f_0+f_1X_0+f_2X_1+f_3X_2+f_4X_0X_1+f_5X_0X_2 + f_6X_1X_2 + f_7X_0X_1X_2
$$

The ordering of monomials in this expression is based on Lexicographic Order.

Besides the "point-value form" and "coefficient form", we introduce a new form of expression based on the "tensor product".

Simply put, the tensor product is a special "multiplication" between two vectors, denoted as $\vec{a} \otimes \vec{b}$. Specifically, we can first compute $a b^T$(assuming $\vec{a}, \vec{b}$ are column vectors), then concatenate the resulting matrix into a vector, which is the result of the tensor product. For example, $\vec{a}=(a_1,a_2)$ and $\vec{b}=(b_1, b_2, b_3)$:

$$
\begin{bmatrix}a_1 \\ a_2\end{bmatrix} \cdot \begin{bmatrix}b_1, b_2,b_3\end{bmatrix} = \begin{bmatrix}a_1b_1, a_1b_2, a_1b_3 \\ a_2b_1, a_2b_2, a_2b_3\end{bmatrix}
$$

Thus, $\vec{a} \otimes \vec{b} = (a_1b_1, a_2b_1, a_1b_2, a_2b_2, a_1b_3, a_2b_3)$.

Comparing with the "coefficient form" of the MLE polynomial mentioned earlier, we find that all its monomials can be obtained from a continuous tensor product:

$$
(1,X_0)\otimes(1,X_1)\otimes(1,X_2) = (1, X_0, X_1, X_0X_1, X_2, X_0X_2, X_1X_2, X_0X_1X_2)
$$

We abbreviate the left-hand side as $\otimes_{j=0}^2 (1,X_j)$. Then an MLE polynomial can be written in inner product form:

$$
\tilde{f}(X_0,X_1,X_2) = \langle \vec{f}, \otimes_{j=0}^2 (1,X_j) \rangle
$$

where the left element is the coefficient vector $\vec{f}$, and the right element is a monomial vector$\otimes_{j=0}^2 (1,X_j)$.

# Split-and-Fold Paradigm

In Gemini, the authors present a protocol based on a univariate polynomial commitment scheme (such as KZG10) to check the correctness of the tensor product, based on which we can further construct the transformation from multivariable to univariate polynomials. We first explain the main idea of the Tensor Product Check using the mentioned three-dimensional MLE polynomial as an example.

Suppose the prover wants to prove the instance: $\vec{f} = (f_0,...,f_7)$, satisfying the relation $\langle\vec{f}, \otimes_{j=0}^{2}(1,\rho_j) \rangle = u$, where $\rho_0,\rho_1, \rho_2$ are in the finite field $F$.

For convenience, we rewrite the indices of elements in the vector $\vec{f}$ in little-endian binary representation, i.e., 

$$
f_i = f_{i_0i_1i_2}, i = \langle (2^0, 2^1, 2^2), (i_0,i_1,i_2) \rangle
$$

where $i_0,i_1,i_2 \in \{0,1\}$.

After re-indexing, the tensor product expands to the following equation:

$$
\begin{matrix} &&\langle\vec{f}, \otimes_{j=0}^{2}(1,\rho_j) \rangle & \\ & = & f_{000}\rho_0^{0}\rho_1^{0}\rho_2^{0}& + &f_{100}\rho_0^{1}\rho_1^{0}\rho_2^{0}& + &f_{010}\rho_0^{0}\rho_1^{1}\rho_2^{0}& + &f_{110}\rho_0^{1}\rho_1^{1}\rho_2^{0} \\ & + & f_{001}\rho_0^{0}\rho_1^{0}\rho_2^{1}& + &f_{101}\rho_0^{1}\rho_1^{0}\rho_2^{1}& + &f_{011}\rho_0^{0}\rho_1^{1}\rho_2^{1}& + &f_{111}\rho_0^{1}\rho_1^{1}\rho_2^{1} \end{matrix}
$$

We find that each coefficient $f_{i_0i_1i_2}$ corresponds one-to-one with the exponents of $\rho_0,\rho_1,\rho_2$, i.e.,

$$
f_{i_0i_1i_2} \cdot \rho_0^{i_0}\rho_1^{i_1} \rho_2^{i_2}, \text{ for all } i_0,i_1,i_2 \in \{ 0,1 \}
$$

Therefore, we can always divide $\vec{f}$ into two equal-length parts based on the exponent $i_j$ of $\rho_j$, and each part satisfies a tensor product subproblem. For example, after dividing $\vec{f}$ based on $\rho_0$, we obtain two tensor product relations regarding $\vec{f}_1, \vec{f}_2$:

$$
\langle\vec{f}, \otimes_{j=0}^{2}(1,\rho_j) \rangle = \langle\vec{f}_1, \otimes_{j=1}^{2}(1,\rho_j) \rangle + \rho_0 \langle\vec{f}_2, \otimes_{j=1}^{2}(1,\rho_j) \rangle
$$

Notice that in these two subproblems, the right-hand elements of the inner product are the same: both are $\otimes_{j=0}^1 (1,\rho_j)$, so they can be further combined into one $\langle\vec{f}_1 + \rho_0 \vec{f}_2, \otimes_{j=1}^{2}(1,\rho_j) \rangle$.

As can be seen, for a vector $\vec{f}$ of length $N$, we split it into two vectors of length $N/2$, then combine them into one vector. Through this round of operations, we reduce a tensor product problem of size
$N$ to one of size $N/2$.

Recursively, the problem can eventually be reduced to size 1.

**Multivariable Polynomial Split-and-Fold**

As mentioned earlier, we can view a tensor product relation as an evaluation relation of a multivariable polynomial, i.e.,

$$
\langle\vec{f}, \otimes_{j=0}^{2}(1,\rho_j) \rangle = u \quad \Leftrightarrow \quad \tilde{f}(\rho_0,\rho_1,\rho_2) = u
$$

For the multivariable polynomial $\tilde{f}^{(0)} = \tilde{f}$, its split-and-fold process in the $j\in[1,3]$ round is as follows:

- **split:** the prover divides the multivariable polynomial $\tilde{f}^{(j-1)}$ into two parts: the first part contains any monomial with degree 0 of $X_j$ (denoted as $\tilde{f}_e^{(j-1)}$), satisfying

$$
\tilde{f}^{(j-1)} = \tilde{f}_{e}^{(j-1)} + X_{j-1} \cdot \tilde{f}_{o}^{(j-1)}.
$$

- **fold:** the prover linearly combines the two separated polynomials $\tilde{f}_e^{(j-1)}, \tilde{f}_o^{(j-1)}$ using the weight $\rho_{j-1}$, obtaining a new multivariable polynomial denoted as $\tilde{f}^{(j)}(X) = \tilde{f}_e^{(j-1)}(X) + \rho_{j-1} \cdot \tilde{f}_o^{(j-1)}(X)$.

The figure below shows the calculation process for $j=1$:

<img src="image/Gemini-multipoly.png" align=center width="60%">

# **Tensor Product Check Protocol**

Through the recursive algorithm described above, we reduce the problem of checking the correctness of an $N$-length tensor product relation to checking the correctness of $n = \left \lceil \log N \right \rceil$ split-and-fold processes.

In fact, this divide-and-conquer approach (split-and-fold) has appeared in many previous protocols, such as Sumcheck, Bulletproofs, and FRI. The difference is that Gemini provides a protocol based on KZG10 to prove the split-and-fold process, which requires $n= \log(|\vec{f}|)$ interactions.

We present the PIOP protocol for proving tensor product relations as follows:

**Tensor-product Check Protocol**

Target relation: $\langle\vec{f}, \otimes_{j=0}^{n-1}(1,\rho_j) \rangle = u$

Prover's input: Public parameters, instance $x = (\rho_0,...,\rho_{n-1}, u)$, witness $w = \vec{f}$

Verifier's input: Public parameters, instance $x = (\rho_0,...,\rho_{n-1}, u)$

1. The prover constructs a univariate polynomial $f^{(0)}(X) = f(X)$.
2. For $j \in 1,...,n$, the prover computes
$$
f^{(j)}(X) = f_e^{(j-1)}(X) + \rho_{j-1} \cdot f_o^{(j-1)}(X)
$$

where $f_e^{(j-1)}, f_o^{(j-1)}$ are polynomials composed of even and odd degree terms of $f^{(j-1)}$, 

satisfying $f^{(j-1)}(X) = f_e^{(j-1)}(X^2) + X \cdot f_o^{(j-1)}(X^2)$.

1. The prover sends the Oracles of $f^{(0)},f^{(1)},...,f^{(n-1)}$ to the verifier.
2. The verifier randomly selects a challenge value $\beta \leftarrow \mathbb{F}$ and queries the Oracles as follows:

$$
e^{(j-1)}:= f^{(j-1)}(\beta), \bar{e}^{(j-1)} := f^{(j-1)}(-\beta), \hat{e}^{(j-1)} := f^{(j)}(\beta^2)
$$

where $j=1,...,n$, and when $j=n$, the query $f^{(n)}(\beta^2)$ is omitted, and $\hat{e}^{(n-1)} := u$ is directly set.

1. For $j = 0,...,n-1$, the verifier checks

$$
\hat{e}^{(j)} = \frac{e^{(j)} + \bar{e}^{(j)}}{2} + \rho_j \cdot \frac{e^{(j)}-\bar{e}^{(j)}}{2\beta}
$$

In each round, the prover generates Oracles for the polynomials obtained before and after the split-and-fold. Specifically, a split-and-fold relation can be written as:

> Given $f(X), f_e(X), f_o(X),f'(X)$, weight $\rho$, they satisfy the following relations
> 
> 
> $$
> f(X)=f_e(X^2)+X\cdot f_o(X^2) \qquad \% \ \text{split} \\ f'(X) = f_e(X)+\rho \cdot f_o(X)\qquad \% \ \text{fold}
> $$
> 

Since even and odd polynomials satisfy (1) $f_e(X^2)=(f(X)+f(-X))/2$, and (2) $f_o(X^2)=(f(X)-f(-X))/2X$, we can further write the above two equations as one:

$$
f'(X^2)=\frac{f(X)+f(-X)}{2} + \rho \cdot \frac{f(X)-f(-X)}{2X}
$$

To check the validity of this equation, the verifier only needs to randomly select a challenge value $\beta$in the finite field $F$,and check whether the values of $f,f'$ at $X=\beta$ satisfy the relation.

# **Multivariable to Univariate Transformation**

Before introducing the protocol for multivariable to univariate conversion, let's delve deeper into some principles hidden in the tensor product protocol. Although the goal of the tensor product protocol is to prove the evaluation of a multivariable polynomial, all the polynomials involved in the protocol, except for the coefficient vector of the input multivariable polynomial, are univariate.

Let's write the Split-and-fold process using univariate polynomials:

**Univariate Polynomial Split-and-fold**

In the $j$-th round:

- **split:** The prover divides the univariate polynomial $f^{(j-1)}$ into two parts: the first part contains any monomial with an even degree of $X$ (denoted as $X \cdot f_o^{(j-1)}$), satisfying

$$
f^{(j-1)}(X) = f_e^{(j-1)}(X^2) + X \cdot f_o^{(j-1)}(X^2)
$$

- **fold:** The prover linearly combines the two separated polynomials $f_e^{(j-1)}, f_o^{(j-1)}$ using the weight 
$\rho_{j-1}$, obtaining a new univariate polynomial denoted as $f^{(j)}(X) = f_e^{(j-1)}(X) + \rho_{j-1} \cdot f_o^{(j-1)}(X)$. [Remark] we need to introduce an additional mapping $X^2 \mapsto X$to obtain $f_e^{(j-1)}(X), f_o^{(j-1)}(X)$.

Therefore, the tensor product protocol can be seen as the prover synchronously executing a recursive algorithm on the univariate polynomial $f$ to simulate the computation process of $\tilde{f}$.

Taking a three-dimensional polynomial as an example, the calculation process in the $j=1$ round is described as follows: 

The split-and-fold calculation in univariate polynomials is as follows:

<img src="image/Gemini-unipoly.png" align=center width="60%">

Compared to the multivariable polynomial split-and-fold, the variable $X$ in the first round of the univariate polynomial corresponds to $X_0$ in the multivariable case, and in the second round, $X^2$ corresponds to $X_1$. In fact, these two processes are calculations on the coefficient vector $\vec{f}$ in different “bases”.

When we need to evaluate a multivariable polynomial on the basis $\{X_0,X_1,X_2\}$, we only need to perform the same operations synchronously on $\{X^1,X^2,X^4\}$ (i.e., on the univariate polynomial), and we can simulate the evaluation process of the multivariable polynomial using the univariate polynomial.

More formally, we obtain a mapping relationship from the multivariable basis vector space to the univariate basis vector space:

$$
\iota: \{ X_0,X_1,X_2 \} \rightarrow \{ X^1, X^2, X^4\}
$$

Therefore, we say that the tensor product protocol provides a method for proving from multivariable to univariate, i.e., multi-to-uni IOP. As shown in the figure below, ideally, we hope the prover can directly generate an Oracle for the multivariable polynomial and send it to the verifier. However, due to the lack of efficient multivariable polynomial commitment schemes in practice, the prover can only construct a proof protocol for the Tensor Product Check (i.e., Multi-Uni-IOP) to simulate the evaluation process of the multivariable polynomial on the univariate polynomial.

The prover needs to send $n$ univariate polynomial Oracles for the verifier to query and check. Since these checks are independent, the verifier can query all Oracles at a single point $\beta$ at once, without needing $O(n)$ points.

<img src="image/Gemini-PIOP.png" align=center width="60%">

# Implementation based on KZG10

For the IOP protocol given earlier, we can deploy a univariate polynomial commitment scheme (KZG10) to compile it into an AoK (Argument of Knowledge). KZG10 supports proving the evaluation of a polynomial at a point, with the advantage of having a constant-size proof and supporting batch proofs. The disadvantage is that it requires a trusted setup and has relatively high proof complexity (requiring FFT operations).

[Remark] Since we compile the IOP into an Argument of Knowledge, KZG10 needs to satisfy extractability, which is proven in Marlin [CHM+19].

Let's briefly review the proof principle of KZG10: Given public parameters: $\mathbb{G}_1, \mathbb{G}_2, \mathbb{G}_T, G, H, e$. In the initialization phase, randomly select $\tau \in \mathbb{}F$ and compute $\tau H \in \mathbb{G}_2$ and the vector

$$
(G,\tau G,\ldots \tau^{D-1}G,\tau^{D}G)\in \mathbb{G}_1^{D+1}
$$

We use square brackets $[a]_1$ to denote scalar multiplication on an elliptic curve group element $a \cdot G$. The KZG proof process is as follows:

1. The prover computes the commitment of a univariate polynomial $f(X)$ of degree $d$, i.e.,$[f(\tau)]_1 = \sum_{j=0}^d f_j \cdot \tau^j G$.
2. The prover publicly reveals the value of the polynomial at point $\rho$, $f(\rho)=u$, and computes the quotient polynomial below to generate the evaluation proof $[q(\tau)]_1$.
$$
q(X) = \frac{f(X)-f(\rho)}{X-\rho}
$$
3. The verifier checks the evaluation proof $e([f(\tau)]_1-[u]_1, [1]_2) = e([q(\tau)]_1, [\tau-\rho]_2)$.

Therefore, to compile the IOP protocol, it is only necessary to commit to the polynomials $f^{(1)},...,f^{(n-1)}$ in the protocol and open them at the specified points $\beta, -\beta, \beta^2$. 

However, there are two points that still need our attention: (1) The degrees of these polynomials are not the same. To prevent the prover from cheating by using polynomials that do not meet the degree requirements, methods from Marlin, Zeromorph [CHM+19, KT23] are needed to restrict the polynomial's Degree Bound. (2) Most polynomials need to be opened at the three points $\beta, -\beta, \beta^2$. If a separate evaluation proof is generated for each point, it will increase the proof size and verification complexity. Multi-point evaluation proof techniques can be used to optimize this problem.

**Degree Bound Proof:** To prove $deg(f)\leq d$

- The prover provides $[f(\tau)]_1$ and attaches $[\tau^{D-d}\cdot f(\tau)]_1$  to send to the verifier.
- The verifier checks the equation $e([f(\tau)]_1, [1]_2) = e([\tau^{D-d}\cdot f(\tau)]_1, [\tau^{D-d}]_2)$.

**Multi-point Evaluation Proof:** To prove $f(X)$ opens at $\beta_1, \beta_2, \beta_3$ as $u_1,u_2,u_3$

- The prover randomly generates a polynomial $g(X)$ of the same degree as $f(X)$, which needs to pass through the points $(\beta, u_1),(-\beta, u_2),(\beta^2, u_3)$
- The prover provides $[f(\tau)]_1$ and the evaluation proof $[q(\tau)]_1 = \frac{f(\tau)-g(\tau)}{(\tau-\beta_1)(\tau-\beta_2)(\tau-\beta_3)}$.
- The verifier checks the equation $e([f(\tau)]_1 - [g(\tau)]_1, [1]_2) = e([q(\tau)]_1, [(\tau-\beta_1)(\tau-\beta_2)(\tau-\beta_3)]_2)$.

[Remark] Both of the above techniques require additional generation of $(H,\tau H,\ldots \tau^{D-1}H,\tau^{D}H)\in \mathbb{G}_2^{D+1}$ during the Setup phase.

**Protocol Description**

Below we present the Multi-to-Uni AoK scheme compiled based on KZG:

**Instance**

- Univariate polynomial commitment $[f(\tau)]_1$ of vector $\vec{f}$ with length of $N$.
- Evaluation point vector $\vec{\rho}$.
- Evaluation result $\tilde{f}(\rho) = u$.

**Witness**

- Coefficient vector $\vec{f}$ of the multivariable polynomial.

**Interactions**

1. The prover generates polynomials $f^{(1)},...,f^{(n-1)}$ and computes and sends their commitments $[f^{(1)}(\tau)]_1,\ldots,[f^{(n-1)}(\tau)]_1$.
2. The prover computes and sends the degree bound proofs of polynomials $f^{(0)},...,f^{(n-1)}$ as $[\tau^{D-N\cdot 2^{-j} + 1}\cdot f^{(j)}(\tau)]_1, j = 0,\ldots n-1$.
3. The verifier randomly selects a point $\beta$ and sends it to the prover.
4. The prover computes the evaluation proofs for each polynomial, where
    - $[q^{(0)}(\tau)]_1 = \frac{f^{(0)}(\tau)-g^{(0)}(\tau)}{(\tau-\beta)(\tau+\beta)}$ $\quad \% \ f^{(0)}(\beta), f^{(0)}(-\beta)$
    - $[q^{(j)}(\tau)]_1 = \frac{f^{(j)}(\tau)-g^{(j)}(\tau)}{(\tau-\beta)(\tau+\beta)(\tau-\beta^2)}$ $\quad \% \ f^{(j)}(\beta), f^{(j)}(-\beta), f^{(j)}(\beta^2), j=1,...,n-1$
5. The verifier checks:
    - The correctness of the degree bound proofs $[\tau^{D-N\cdot 2^{-j} + 1}\cdot f^{(j)}(\tau)]_1, j = 0,\ldots n-1$ for $f^{(0)},...,f^{(n-1)}$.
    - The correctness of the multi-point evaluation proofs $[q^{(0)}(\tau)]_1,\ldots [q^{(n-1)}(\tau)]_1$ for $f^{(0)},...,f^{(n-1)}$.
    - The correctness of the split-and-fold relation, i.e., for $j = 0,...,n-1$, whether the following equation holds:
$$
\hat{e}^{(j)} = \frac{e^{(j)} + \bar{e}^{(j)}}{2} + \rho_j \cdot \frac{e^{(j)}-\bar{e}^{(j)}}{2\beta}
$$

**Performance Analysis**

- Proof size: $3\log N \ \mathbb{G}_1$ elements
- Verification complexity: $4 \log N \ \mathsf{Pairing},\ O(\log N) \ \mathsf{EccMul}^{\mathbb{G}_1 \text{ or } \mathbb{G}_2}$

# References

[BCH+22] Bootle, Jonathan, Alessandro Chiesa, Yuncong Hu, **et al. "Gemini: Elastic SNARKs for Diverse Environments." *Cryptology ePrint Archive* (2022). [https://eprint.iacr.org/2022/420](https://eprint.iacr.org/2022/420)

[KT23] Kohrita, Tohru, and Patrick Towa. "Zeromorph: Zero-knowledge multilinear-evaluation proofs from homomorphic univariate commitments." Cryptology ePrint Archive (2023). [https://eprint.iacr.org/2023/917](https://eprint.iacr.org/2023/917)

[CHM+19] Chiesa, Alessandro, Yuncong Hu, Mary Maller, et al. "Marlin: Preprocessing zkSNARKs with Universal and Updatable SRS." *Cryptology ePrint Archive* (2019). [https://eprint.iacr.org/2019/1047](https://eprint.iacr.org/2019/1047)