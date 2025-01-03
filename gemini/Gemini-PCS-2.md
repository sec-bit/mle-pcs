# Gemini-PCS-2

- Tianyu ZHENG [tian-yu.zheng@connect.polyu.hk](mailto:tian-yu.zheng@connect.polyu.hk)

In the first part, we introduced the Tensor product check protocol for multivariable polynomial evaluation proofs in Gemini [BCH+22] and briefly explained how it can be applied to practical proof systems to convert multivariable polynomials into univariate polynomials. In this part, we focus on the security of the Tensor product check protocol and propose some optimizations based on Gemini.

# Recap

For ease of reading, let's review the process of the tensor product check protocol:

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

# **Security Analysis**

**Completeness**

Given a polynomial coefficient vector satisfying $\langle\vec{f}, \otimes_{j=0}^{2}(1,\rho_j) \rangle = u$, an honest prover executing the above protocol will pass verification. According to our discussion in the “Split-and-fold Check Protocol”, when the prover correctly executes the split to obtain $f_e^{(j-1)}(X), f_o^{(j-1)}(X)$, the folded $f^{(j)}(X)$ will pass verification, and $f^{(j)}(X)$ satisfies the following expression:

$$
f^{(j)}(X) = \sum_{i_0,...,i_{n-1} \in \{ 0,1 \}} f_{i_0\cdots i_{n-1}} \cdot \rho_0^{i_0} \cdots \rho_{j-1}^{i_{j-1}} \cdot X^{\langle \vec{i}_{[j:n-1]}, \vec{2}^{n-1-j}\rangle}
$$

where $\vec{2}^{n-1-j} = (2^0,...,2^{n-1-j})$. Clearly, when $j=n$, we have $f^{(n)}(X) = \tilde{f}(\vec{\rho})= u$.

**Soundness**

Here we adopt a different but more understandable proof method than the original Gemini paper. Suppose $\langle\vec{f}, \otimes_{j=0}^{2}(1,\rho_j) \rangle \neq u$. For a malicious prover, if it can output a series of interactive data, including the Oracles of polynomials $f^{(j)}, j=0,...,n-1$ and successfully pass verification, then there must exist at least one pair of Oracles whose polynomials do not satisfy the split-and-fold relation. That is, there exists $j$ such that

$$
p_j(X) = f^{(j)}(X^2) - \frac{f^{(j-1)}(X)+f^{(j-1)}(-X)}{2} - \rho_{j-1}\frac{f^{(j-1)}(X)-f^{(j-1)}(-X)}{2X}
$$

is a non-zero polynomial. Note that the highest degree of $p_j(X)$ is $2^{n-(j-1)}-1$. Let event $E_j$ denote that $p_j(X)$ is a non-zero polynomial and $p_j(\beta) = 0$. According to the Schwartz-Zippel lemma, $Pr(E_j) \leq deg(p_j)/|F|$. Then for all $p_1(X),...,p_{n}(X)$, the probability that there exists a non-zero polynomial that is zero at point $\beta$ can be restricted using the union bound:

$$
Pr(E_1 \vee \cdots \vee E_n) \leq Pr(E_1) + \cdots + Pr(E_n) = \sum_{j=1}^n \frac{deg(p_j)}{|F|} = \frac{2N}{|F|}
$$

**Regarding degree bound**

Note that in the original Gemini paper, the verifier needs to check that the degree of each $f^{(j)}$ is strictly less than or equal to $2^{n-j}-1$. This is also reflected in the above proof: assuming the highest degree of $p_j(X)$ is $2^{n-(j-1)}-1$.

However, upon further research, we find that the degree check is not necessary: even if a malicious prover is allowed to construct an illegal $f^{(j')}$ in each round, whose degree is greater than the legal $f^{(j)}$ but less than or equal to $N$, we can still achieve a negligible soundness error (albeit slightly larger than the original). Specifically, for any $E_j$, we have $Pr(E_j) \leq N/|F|$, yielding $Pr(E_1 \vee \cdots \vee E_n) \leq N \log N/|F|$ (when $N < D$, the RHS is $D \log N / |F|$).

Therefore, the degree bound check in the Tensor-product check protocol based on KZG10 in the first part can be ignored to reduce the proof by $\log N$ elements in $\mathbb{G}_1$.

# Adding Zero-Knowledge

Gemini does not discuss how to achieve the ZK property of the tensor product check. Here, we provide two feasible schemes.

**Attempt 1**

Using a similar idea to the zk sumcheck implementation in [CFS17], we can directly add a blinding polynomial $g(X)$ of the same size to the original polynomial $f(X)$. For each non-zero term in $f(X), g(X)$ contains a corresponding term with a random coefficient. Let $\langle\vec{g}, \otimes_{j=0}^{n-1}(1,\rho_j) \rangle = v$.

Next, the prover only needs to additionally commit to $g(X)$ and send the commitment $cm(g(X))$ and $v$ to the verifier. The verifier then randomly selects a challenge value $c$ to combine the tensor product relations of $f, g$ into

$$
u+c\cdot v = \langle\vec{f}+c\cdot \vec{g}, \otimes_{j=0}^{n-1}(1,\rho_j) \rangle
$$

The prover and verifier then complete the Tensor product check protocol for the above relation. We will not elaborate on the specific construction of this scheme.

**Attempt 2**

The above method is straightforward, but the drawback is that the prover needs to add an additional random polynomial of the same size as $f(X)$ (length $N$). Referring to the optimization scheme for zk sumcheck in Libra [XZZPS19], we can propose an optimized scheme for the zk tensor product protocol, significantly reducing the size of the blinding polynomial.

The idea of this optimization scheme is: since the prover only sends $3n$ point values in the tensor product check, the blinding polynomial needs to contain at least $3n$ random coefficients to ensure the zero-knowledge property of the protocol.

Specifically, let the blinding polynomial be:

$$
g(X) = a_{0,1}X + a_{0,2}X^2 + \sum_{i=1}^{n-1} \left( a_{i,1} X^{3i} + a_{i,2} X^{3i+1} + a_{i,3} X^{3i+2} \right) + a_n
$$

**Zero-Knowledge Tensor Product Check Protocol**

To prove $\langle\vec{f}, \otimes_{j=0}^{n-1}(1,\rho_j) \rangle = u$

1. The prover constructs the blinding polynomial $g(X)$ and pads its coefficient vector with zeros to length $N$.
2. The prover computes and sends the following data to the verifier:

$$
v = \langle\vec{g}, \otimes_{j=0}^{n-1}(1,\rho_j) \rangle \\ C_g = cm(g(X))
$$

1. The verifier randomly selects $c \in F^*$ and sends it to the prover, then computes $u + c\cdot v, C_f + c\cdot C_g$.
2. The prover and verifier run the tensor product check protocol to prove the following relation:

$$
u+c\cdot v = \langle\vec{f}+c\cdot \vec{g}, \otimes_{j=0}^{n-1}(1,\rho_j) \rangle
$$

For convenience, let $h(X) = f(X) + c\cdot g(X)$. The above construction satisfies zero-knowledge as follows:

**Proof Sketch**

First, the simulator $S$ can be constructed as follows:

1. $S$ first inputs a random challenge value $c \neq 0$.
2. $S$ uniformly randomly generates vector $\vec{h}$ uniformly randomly generates vector $h(X)$, as well as $C_h = \mathsf{Commit}(h(X)), w = \langle\vec{h}, \otimes_{j=0}^{n-1}(1,\rho_j) \rangle$.
3. $S$ computes $v = (w-u)/c$ and the commitment $C_g = (C_h/C_f)^{1/c}$. 
4. $S$ and $V^*$ run a tensor product check protocol, proving the relation $w = \langle\vec{h}, \otimes_{j=0}^{n-1}(1,\rho_j) \rangle$.

Clearly, the messages in steps 1 and 3 are indistinguishable from those sent by an honest prover $P$.

Next, we only need to show that the execution of the tensor product check protocol in step 4 with $S$ and $V^*$ also satisfies this property. Specifically, because the protocol satisfies soundness, for each oracle $h^{(j)}, j=0,...,n-1$, it satisfies 

$$
h^{(j)}(X^2)=\frac{h^{(j-1)}(X)+f^{(j-1)}(-X)}{2} + \rho \cdot \frac{h^{(j-1)}(X)-h^{(j-1)}(-X)}{2X}
$$

Note that for the right side of the equation involving $h^{(j-1)}(X)$, its corresponding oracle also satisfies an equation related to $h^{(j-2)}(X)$. Therefore, we can always expand the right side of any $h^{(j)}(X^2)$ into a form that only contains $h^{(0)}(X), h^{(0)}(-X), h^{(0)}(X^2)$. Therefore, the responses to any queries by $V^*$ on the oracle $h^{(j)}$ at any point $\beta$ are certainly linearly independent constraints on $\vec{h}$.

Overall, after executing the tensor product check protocol, $V^*$ will obtain $3\cdot (n-1)$,$2$ values on $h^{(0)}(X)$, and one value of $h^{(n)}(X)$, i.e., $u+c\cdot v$. Since $h$ contains a blinding polynomial of size $3n$, the verifier cannot interpolate to find all coefficients of the blinding polynomial, so this protocol is indistinguishable from the one executed by an honest verifier.

# **References**

[BCH+22] Bootle, Jonathan, Alessandro Chiesa, Yuncong Hu, **et al. "Gemini: Elastic SNARKs for Diverse Environments." *Cryptology ePrint Archive* (2022). [https://eprint.iacr.org/2022/420](https://eprint.iacr.org/2022/420)

[CFS17**]** Chiesa, Alessandro, Michael A. Forbes, and Nicholas Spooner. "A zero knowledge sumcheck and its applications." [*arXiv preprint arXiv:1704.02086* (2017)](https://eprint.iacr.org/2017/305).

[XZZPS19] Xie, T., Zhang, J., Zhang, Y., Papamanthou, C., & Song, D. “Libra: Succinct zero-knowledge proofs with optimal prover computation.” [https://eprint.iacr.org/2019/317](https://eprint.iacr.org/2019/317)