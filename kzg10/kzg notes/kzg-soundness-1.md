# KZG-Soundness-zh-1

- Tianyu ZHENG <tian-yu.zheng@connect.polyu.hk>

The KZG polynomial commitment scheme is widely used in zk-SNARKs systems, blockchain scaling solutions (such as Verkle trees), and data availability solutions due to its concise proof length, efficient verification algorithm, and updatable structured reference string (SRS). However, different application scenarios have different security requirements for KZG. Since the KZG10 paper, researchers have conducted in-depth studies on the security of KZG. The following are the main studies related to zk-SNARKs:

- **KZG10:** The first paper on the KZG polynomial commitment scheme, which only proved that the scheme satisfies the evaluation binding property.
- **Sonic:** Used KZG to construct zk-SNARKs and provided the first proof of KZG extractability in the Algebraic Group Model (AGM).
- **Plonk:** Also provided a proof of KZG extractability in AGM, but its definition has some flaws.
- **Marlin:** Provided a formal definition and gave extractability proofs in both the standard model and AGM.
- **AGMOS:** Proposed the AGMOS assumption and proved KZG extractability based on a falsifiable assumption.
- **LPS24:** Proved KZG extractability based on a falsifiable assumption only in the Random Oracle Model (ROM).

In this article, we first review the discussion of the evaluation binding property in the KZG10 paper. Next, we introduce the necessity of the KZG extractability property and provide its proof in AGM. Finally, we briefly mention some conclusions from AGMOS.

# Soundness in KZG10

**[KZG10 Protocol]**

- **Setup:** Given $\mathbb{G}_1, \mathbb{G}_2, \mathbb{G}_T, e:\mathbb{G}_1\times \mathbb{G}_2 \mapsto \mathbb{G}_T$, randomly select $\tau \in \mathbb{F}$ and compute
  $$
  SRS = ([1]_1,[\tau]_1,[\tau^2]_1,\ldots,[\tau^{D}]_1, [1]_2, [\tau]_2)
  $$

- **Commit:** The prover computes a degree $d$ univariate polynomial $f(X) \in \mathbb{F}[X]$ to generate a commitment $C_f = [f(\tau)]$
  $$
  C_f = \mathsf{Commit}(f(X)) = f_0\cdot[1]_1+f_1\cdot[\tau]_1+ \cdots + f_d\cdot[\tau^d]_1
  $$

- **Open:** The prover reveals the value of the polynomial at point $z$ as $f(z)=v$, and generates the quotient polynomial
  $$
  q(X) = \frac{f(X)-f(z)}{X-z}
  $$

- Generate the proof $\pi = [q(\tau)]_1$
  $$
  \pi = q_0\cdot[1]_1 + q_1\cdot[\tau]_1+\cdots+q_d\cdot[\tau^d]_1
  $$

- **Check:** The verifier checks the evaluation proof
  $$
  e([f(\tau)]_1-f(z)\cdot[1]_1, [1]_2) = e([q(\tau)]_1, [\tau -z]_2)
  $$

**[Evaluation Binding]**

Given an $SRS$, if for any adversary $\mathcal{A}$, the probability of finding a polynomial commitment value $C_f$ and point $z$, and generating two valid proofs $\pi, \pi'$ for $f(z) = v, f(z) = v'$ respectively, is negligible, then we consider the above polynomial commitment algorithm to satisfy the evaluation binding property.

Proving this conclusion requires the **t-Strong Diffie-Hellman Assumption**:

Let $\alpha \in \mathbb{F}$ be a random value. Given the input $([1]_1, [\alpha]_1, [\alpha^2]_1, \ldots, [\alpha^t]_1, [\alpha]_2)$, it is difficult for any adversary $\mathcal{A}$ to find an element $[\frac{1}{\alpha+c}]_1$ in $\mathbb{G}_1$, where $c$ can be any value in $\mathbb{F}/\{-\alpha\}$.

**[Security Proof]**

Assume there exists an adversary $\mathcal{A}$ that can break the evaluation binding property of the KZG10 polynomial commitment scheme: that is, given the input $SRS$, $\mathcal{A}$ computes a commitment value $C_f$ and two tuples $(z, v, \pi), (z, v', \pi')$ that can both pass the verifier's **Check** algorithm. Then we can construct an efficient algorithm $\mathcal{B}$ based on $\mathcal{A}$, which can break the t-SDH assumption.

In simple terms, we prove that if $\mathcal{A}$ exists, then we can construct $\mathcal{B}$. The contrapositive is also true: if we cannot construct $\mathcal{B}$, then $\mathcal{A}$ does not exist. In fact, since algorithm $\mathcal{B}$ (i.e., the algorithm that breaks the t-SDH assumption) is considered difficult to construct, we can conclude that the adversary $\mathcal{A}$ attacking KZG10 also does not exist.

Next, we only need to provide the construction algorithm for $\mathcal{B}$:

1. $\mathcal{B}$ sends a t-SDH instance $(\mathbb{G}_1, [1]_1, [\alpha]_1, [\alpha^2]_1, \ldots, [\alpha^t]_1, [\alpha]_2)$ as $SRS$ to $\mathcal{A}$.
2. According to the assumption, $\mathcal{A}$ can output $C_f, (z, v, \pi), (z, v', \pi')$ with non-negligible probability in polynomial time, satisfying
   $$
   e([C_f-v\cdot[1]_1, [1]_2) = e(\pi, [\alpha-z]_2)\\ e([C_f-v'\cdot[1]_1, [1]_2) = e(\pi', [\alpha-z]_2)
   $$
3. Without loss of generality, assume $\pi = [q(\alpha)]_1, \pi' = [q'(\alpha)]_1$, they satisfy
   $$
   q(\alpha) \cdot (\alpha-z) + v= f(\alpha) = q'(\alpha) \cdot (\alpha-z) + v' \\ \frac{q(\alpha)/q'(\alpha)}{v'-v} = \frac{1}{\alpha-z}
   $$
   Notice that the right-hand side is our target relation, so $\mathcal{B}$ only needs to compute the following to break the t-SDH assumption
   $$
   \frac{(\pi-\pi')}{v'-v} = [\frac{1}{\alpha-z}]_1
   $$

# Extractable KZG

**[Why is Extractability Needed?]**

The above evaluation binding property only ensures that the prover cannot open two different values at the same point, which indeed satisfies the requirements of some application scenarios, such as membership proofs. However, with the development of SNARKs, polynomial commitment proofs like KZG10 are used to construct SNARKs, instantiating polynomial Oracle in an Interactive Oracle Proof (IOP). The security properties required by IOPs impose new requirements on KZG.

For an ideal IOP protocol, its Knowledge Soundness is very easy to guarantee. According to the conclusion in HypePlonk, when an IOP satisfies the soundness property, it also satisfies the Knowledge Soundness property: there exists an extractor that only needs to query a polynomial oracle $d+1$ times to compute the entire polynomial itself.

However, when we consider instantiating polynomial Oracles in IOPs with PCS, ensuring that the instantiated SNARK satisfies the Knowledge Soundness property is not so easy.

Compared to the prover sending an oracle containing the entire polynomial in IOP (in the IOP model, the length of the oracle is the same as the polynomial, but the verifier does not fully read it), in SNARK, the prover only sends the commitment of the polynomial, which contains very little information: only the values of the polynomial at a few points.

Therefore, we can only ensure that the polynomial commitment itself is **"Extractable"** to guarantee the Knowledge Soundness of SNARK. (For detailed arguments, refer to Interactive Oracle Proofs by Eli Ben-Sasson et al. and DARK)

Sonic, Plonk, Marlin, and other SNARKs based on polynomial commitments have successively discussed this issue. Below we mainly refer to the description in Sonic to introduce the proof of KZG10 Extractability based on the AGM model.

**[Algebraic Group Model]**

AGM (Algebraic Group Model) is an idealized security model that is stronger than the standard model but weaker than the Generic Group Model (GGM).

In AGM, we assume that the adversary algorithm $\mathcal{A}_{alg}$ is "algebraic": that is, whenever $\mathcal{A}_{alg}$ outputs a group element $Z$, it will simultaneously output a representation of $Z$, which includes a vector of field elements $(z_1,...,z_t) \in F^t$ to describe how the group element $Z$ is computed, i.e., $Z = \prod_{i=1}^t g_i^{z_i}$, where $*\{ g_1,...,g_t\}$* is the list of all group elements received by $\mathcal{A}_{alg}$ from the beginning of the protocol until now.

As in the standard model, we also use reductions to prove security relations under AGM.

# **Extractability** under AGM

**[Extractability Definition]**

For any algebraic adversary $\mathcal{A}_{alg}$, if it can output a valid KZG evaluation proof, then there must exist another efficient algorithm $\mathcal{B}_{alg}$ that can extract the public value $f(X)$ of the commitment $C_f$, satisfying $f(z) = v$.

**[q-DLOG Assumption]**

Let $\alpha \in \mathbb{F}$ be a random value. Given the input $([1]_1, [\alpha]_1, [\alpha^2]_1, \ldots, [\alpha^t]_1, [1]_2,[\alpha]_2)$, it is difficult for any adversary $\mathcal{A}$ to compute $\alpha$.

**[Security Proof]**

**Goal:** $Adv_{\mathcal{A}_{alg}}^{Extract} \leq Adv_{\mathcal{B}_{alg}}^{qDL}$, i.e., the extractability of KZG broken by $\mathcal{A}_{alg}$ can be reduced to the q-DLOG problem broken by $\mathcal{B}_{alg}$.

**Proof:** Assume there exists an adversary algorithm $\mathcal{A}_{alg}$ that can provide a valid proof without knowing the correct $f(X)$. Then we can construct an algorithm $\mathcal{B}_{alg}$ that simulates an extractability game with $\mathcal{A}_{alg}$ based on its input q-DLOG problem instance $([1]_1, [\alpha]_1, [\alpha^2]_1, \ldots, [\alpha^D]_1, [1]_2,[\alpha]_2)$:

- $\mathcal{B}_{alg}$ sends the q-DLOG instance as $SRS$ to $\mathcal{A}_{alg}$
  $$
  SRS = ([1]_1,[\alpha]_1,[\alpha^2]_1,\ldots,[\alpha^{D}]_1, [1]_2, [\alpha]_2)
  $$

- According to the assumption, $\mathcal{A}_{alg}$ can output the message $C_f, (z, v, \pi)$ with non-negligible probability in polynomial time, passing verification.

- Since $\mathcal{A}_{alg}$ is an algebraic algorithm, it will simultaneously output the representations of group elements $C_f, \pi$, denoted as $f'(X), q'(X)$, satisfying
  $$
  C_f = [f'(\alpha)]_1, \pi = [q'(\alpha)]_1
  $$

- Meanwhile, since the proof passes verification, $C_f, \pi$ satisfy
  $$
  e(C_f-v\cdot[1]_1, [1]_2) = e(\pi, [\alpha -z]_2)
  $$

- Based on the relationship satisfied by the exponents in the verification equation, $\mathcal{B}_{alg}$ can construct a polynomial $Q(X)$ using $f'(X), q'(X)$
  $$
  Q(X) = f'(X) - v - (X-z)q'(X)
  $$

- If $Q(X) = 0$, then $\mathcal{B}_{alg}$ terminates the algorithm.

- If $Q(X) \neq 0$, $\mathcal{B}_{alg}$ factors the polynomial and finds all its roots.

- Test each root in turn to see if it satisfies the given q-DLOG instance. If a certain $x$ satisfies it, output $x$ as the solution to the q-DLOG problem.

We argue that in the above reduction, if the success probability of $\mathcal{A}_{alg}$ is a non-negligible $\epsilon$, then the success probability of $\mathcal{B}_{alg}$ is $\epsilon+\mathsf{negl}(\lambda)$. Clearly, the event that $\mathcal{B}_{alg}$ cannot output a solution to a q-DLOG problem can occur in two places:

1. $Q(X) = 0$, then $\mathcal{B}_{alg}$ terminates the algorithm. From $Q(X) = 0$, it can be deduced that $f'(X) - v = (X-z)q'(X)$, i.e., $f'(z) = v$, which contradicts the initial assumption.

2. The roots obtained by factoring $Q(X)$ do not satisfy the q-DLOG instance. Since $\mathcal{B}_{alg}$ did not terminate the algorithm in the previous step, it is known that $Q(X) \neq 0$, and the proof output by $\mathcal{A}_{alg}$ can pass verification, i.e., $[f'(\alpha)-v]_T = [(\alpha-z)q'(\alpha)]_T$. Unless $\mathcal{A}_{alg}$ breaks the DL problem in $G_T$, $\alpha$ must be a root of $Q(X)$.

# AGMOS

Recently, Lipmaa et al. proposed AGMOS (Algebraic Group Model with Oblivious Sampling). AGMOS is a more realistic variant of AGM, which gives the adversary the additional ability to sample group elements obliviously without knowing the discrete logarithm (e.g., hash-to-group in practice).

Furthermore, Lipmaa pointed out that there are two different definitions of KZG extractability in practical protocol design:

- The extractor algorithm extracts the polynomial after the **Commit** and **Open** phases, as in Marlin and Sonic.
- The extractor algorithm extracts the polynomial only after the **Commit** phase, as in Plonk and Lunar.

Lipmaa noted in the article that the latter leads to a spurious knowledge assumption that is secure under AGM but insecure in the standard model.

[KZG10] Kate, Aniket, Gregory M. Zaverucha, and Ian Goldberg. "Constant-size commitments to polynomials and their applications." *International conference on the theory and application of cryptology and information security*. Berlin, Heidelberg: Springer Berlin Heidelberg, 2010.

[Sonic] Maller, Mary, et al. "Sonic: Zero-knowledge SNARKs from linear-size universal and updatable structured reference strings." *Proceedings of the 2019 ACM SIGSAC conference on computer and communications security*. 2019.

[Plonk] Gabizon, Ariel, Zachary J. Williamson, and Oana Ciobotaru. "Plonk: Permutations over lagrange-bases for oecumenical noninteractive arguments of knowledge." *Cryptology ePrint Archive* (2019).

[Marlin] Chiesa, Alessandro, et al. "Marlin: Preprocessing zkSNARKs with universal and updatable SRS." *Advances in Cryptology–EUROCRYPT 2020: 39th Annual International Conference on the Theory and Applications of Cryptographic Techniques, Zagreb, Croatia, May 10–14, 2020, Proceedings, Part I 39*. Springer International Publishing, 2020.

[AGMOS] Lipmaa, Helger, Roberto Parisella, and Janno Siim. "Algebraic group model with oblivious sampling." *Theory of Cryptography Conference*. Cham: Springer Nature Switzerland, 2023.

[LPS24] Lipmaa, Helger, Roberto Parisella, and Janno Siim. "Constant-size zk-SNARKs in ROM from falsifiable assumptions." *Annual International Conference on the Theory and Applications of Cryptographic Techniques*. Cham: Springer Nature Switzerland, 2024.