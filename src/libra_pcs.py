#!/usr/bin/env python3

# WARNING: This implementation may contain bugs and has not been audited. 
# It is only for research purposes. DO NOT use it in production.

# Implementation of Libra-PCS (Variant of Construction 3, Section 4.3, 
#   in the Libra paper [XZZPS19])
#
#  Libra: Succinct Zero-Knowledge Proofs with Optimal Prover Computation
#    - https://eprint.iacr.org/2019/317
#
#  zkVSQL: A Zero-Knowledge Version of vSQL
#    - https://eprint.iacr.org/2017/1146
#

# Some Modifications:
#    - MLE polynomials support only
#    - Security assumption: `Algebraic Group Model` instead of `Knowledge of Exponent`
#    - No support of random polynomials (e.g., R(X) in Construction 3, Section 4.3)

from functools import reduce
import copy

from curve import Fr as Field, ec_mul, ec_mul_group2, G1Point as G1, G2Point as G2, ec_pairing_check
from utils import bits_le_with_width
from merlin.merlin_transcript import MerlinTranscript
from mle2 import MLEPolynomial

class Commitment:

    def __init__(self, cm: G1):
        self.cm = cm

class LIBRA_PCS:

    def __init__(self, debug: int = 0):
        self.debug = debug

    # WARNING: This setup function is only used for testing. Never use it in production.
    # In practice, we should use a trusted setup, e.g., by an MPC-based setup ceremony.
    def setup(self, num_var: int, secret_vec = None, g1_generator = None, g2_generator = None) -> None:
        """
        Generate the structured reference string (SRS).

            G1 : [1]_1, [tau]_1, [tau^2]_1,     ..., [tau^max_degree]_1, [xi]_1
            G2 : [1]_2, [tau]_2, [xi]_2
        
        Args:
            secret_symbol: Secret value for SRS (if None, randomly generated)
            g1_generator, g2_generator: Generators for G1 and G2 (if None, randomly chosen)
        
        Returns:
            Dictionary containing the SRS parameters
        """

        # [1]_1, [1]_2
        if g1_generator is None and not self.debug:
            g = ec_mul(self.G1.ec_gen(), self.Scalar.rand())
            h = ec_mul_group2(self.G2.ec_gen(), self.Scalar.rand())
        elif self.debug:
            g = G1.ec_gen()
            h = G2.ec_gen()
        else:
            g = g1_generator
            h = g2_generator

        if secret_vec is None:
            tau_vec = [Field.rand() for _ in range(num_var)]
        else:
            assert len(secret_vec) == num_var
            tau_vec = secret_vec

        self.max_var_num = num_var

        # xi: randomness used for hiding
        xi = Field.rand()
        # [xi]_1
        xi_g = g.ec_mul(xi)
        # [xi]_2
        xi_h = h.ec_mul(xi)

        powers_of_tau = []
        for i in range(2**num_var):
            bits = bits_le_with_width(i, num_var)
            power_of_tau = reduce(lambda x, y: x * y, [tau_vec[j] ** bits[j] for j in range(num_var)])
            powers_of_tau.append(power_of_tau)
        print(f"powers_of_tau: {powers_of_tau}")

        # [1]_1, [τ]_1, [τ^2]_1, ..., [τ^{max_degree + 1}]_1
        powers_of_tau_g: list[self.G1] = [g.ec_mul(powers_of_tau[i]) for i in range(2**num_var)]

        self.params = {}
        self.params['powers_of_tau_g'] = powers_of_tau_g
        self.params['g'] = g
        self.params['xi_g'] = xi_g
        self.params['tau_g'] = [g.ec_mul(tau_vec[i]) for i in range(num_var)]
        self.params['h'] = h
        self.params['tau_h'] = [h.ec_mul(tau_vec[i]) for i in range(num_var)]
        self.params['xi_h'] = xi_h

        # Compute the list of { 
        #       eqs_over_hypercube(tau_vec[:1]), 
        #       eqs_over_hypercube(tau_vec[:2]), 
        #       eqs_over_hypercube(tau_vec[:3]), 
        #       ..., 
        #       eqs_over_hypercube(tau_vec[:num_var]) 
        # } in one single traverse.
        eqs_of_tau_vec = [[Field.one()]]
        n = 1 << num_var
        evals = [Field(1)] * n
        half = 1
        for k in range(num_var):
            for i in range(half):
                evals[i+half] = evals[i] * tau_vec[k]
                evals[i] = evals[i] - evals[i+half]
            eqs_of_tau_vec.append(evals[:2*half])
            half *= 2
        print(f"eqs_of_tau_vec: {eqs_of_tau_vec}")

        # Commit to the list
        eqs_of_tau_g_vec = []
        for k in range(num_var+1):
            eqs_of_tau_g_vec.append([g.ec_mul(eqs_of_tau_vec[k][i]) for i in range(2**k)])

        self.params['eqs_of_tau_g'] = eqs_of_tau_g_vec

        return self.params

    def setup_multilinear_basis(self, var_num: int) -> list[list[G1]]:
        """
        Compute all multilinear basis sets for the given variable number.

            eq_k:   [eq_k(0, 0, ..., 0, τ0, τ1, ..., τ_{k-1})]
                    [eq_k(1, 0, ..., 0, τ0, τ1, ..., τ_{k-1})]
                    ...
                    [eq_k(1, 1, ..., 1, τ0, τ1, ..., τ_{k-1})]

            eq_{k-1}: [eq_{k-1}(0, 0, ..., 0, τ0, τ1, ..., τ_{k-2})]
                      [eq_{k-1}(1, 0, ..., 0, τ0, τ1, ..., τ_{k-2})]
                      ...
                      [eq_{k-1}(1, 1, ..., 1, τ0, τ1, ..., τ_{k-2})]
            
            ...
            eq_1:   [eq_1(0, τ0)]
                    [eq_1(1, τ0)]

            eq_0:   [1]

        Args:
            var_num: The number of variables.
        
        Returns:
            The multilinear basis sets.
        """
        # TODO: compute SRS_EQS_OVER_HYPERCUBE from SRS_POWERS_OF_TAU without the knowledge of `tau`
        raise NotImplementedError("Setup multilinear basis is not implemented")
    
    #     assert var_num <= self.max_var_num, "Variable number exceeds the maximum allowed"

    #     eqs_of_tau = []
    #     for i in range(2**var_num):
    #         bits = bits_le_with_width(i, var_num)
    #         eq_of_tau = reduce(lambda x, y: x * y, [tau_vec[j] if bits[j]==1 else (Field.one() - tau_vec[j]) for j in range(var_num)])
    #         eqs_of_tau.append(eq_of_tau)

    #     g = self.params['g']
    #     eqs_of_tau_g: list[self.G1] = [g.ec_mul(eqs_of_tau[i]) for i in range(2**var_num)]

    #     return eqs_of_tau_g

    def commit_with_monomial_basis(self, coefficients: list[Field]) -> Commitment:
        # s = Field.rand()
        s = Field.zero()
        f_cm = self.params['xi_g'].ec_mul(s)
        f_cm += msm_basic(self.params['powers_of_tau_g'], coefficients)

        return Commitment(f_cm), s

    def commit_with_multilinear_basis(self, evaluations: list[Field], num_var: int) -> tuple[Commitment, Field]:
        """
        Commit to a polynomial using multilinear basis.

            f(Xs) = a_0 * eq_0(Xs) + a_1 * eq_1(Xs) + ... + a_{2^n-1} * eq_{2^n-1}(Xs)

            where `Xs` is the short for `(X0, X1, ..., X_{n-1})`
            
            and `eq_i(Xs)` is the multilinear polynomial defined as:

                eq_i(X0, X1, ..., X_{n-1}) = \prod_{j=0}^{n-1} (X_j * bits(i)[j] + (1-X_j) * (1-bits(i)[j]))

            Commit(f) = a_0[eq_0(taus)] + a_1[eq_1(taus)] + ... + a_{2^n-1}[eq_{2^n-1}(taus)]
                        + s * [xi]

            here, `Commit(f)` is on G1, and `s` is randomly chosen.

        Args:
            evaluations: The evaluations of the polynomial.
        
        Returns:
            f_cm: A commitment to the polynomial.
            s: The randomness used for hiding.
        """
        assert len(evaluations) == 2**num_var, "Evaluation number does not match the variable number"
        basis_vec = self.params['eqs_of_tau_g']
        assert num_var < len(basis_vec), "Variable number exceeds the maximum allowed"

        f_evals = evaluations

        s = Field.rand()

        basis = basis_vec[num_var]
        f_cm = self.params['xi_g'].ec_mul(s)
        f_cm += msm_basic(basis, f_evals)

        return Commitment(f_cm), s
    
    def commit(self, polynomial: MLEPolynomial) -> tuple[Commitment, Field]:
        evaluations = polynomial.evals
        num_var = polynomial.num_var
        return self.commit_with_multilinear_basis(evaluations, num_var)
    
    def prove_evaluation(self, polynomial: MLEPolynomial, 
                    point: Field, randomness: Field) -> tuple[Field, dict]:
        """
        Prove the evaluation of a polynomial at a given point.

            f(X0, X1, ..., X_{n-1}) = (X0-u0) * q0 
                                + (X1-u1) * q1(X0) 
                                + ... 
                                + (X_{n-1} - u_{n-1}) * q_{n-1}(X0,X1,...,X_{n-2})

            [q0] = commit(q0; s0)
            [q1] = commit(q1; s1)
            ...
            [q_{n-1}] = commit(q_{n-1}; s_{n-1})

            s_cm = s * [1] + (-s0 * [τ0] + (s0 * u0)[1]) 
                           + (-s1 * [τ1] + (s1 * u1)[2]) 
                           + ... 
                           + (-s_{n-1} * [τ_{n-1}] + (s_{n-1} * u_{n-1})[n])
            
        Args:
            polynomial: The polynomial to be evaluated.
            point: The point at which the polynomial is evaluated.
            randomness: The randomness used in the hiding commitment.
        
        Returns:
            v: The evaluation of the polynomial at the given point.
            argument: The argument for verification.
        """
        basis_vec = self.params['eqs_of_tau_g']
        assert len(basis_vec) >= polynomial.num_var, "Variable number exceeds the maximum allowed"

        g = self.params['g']
        xi_g = self.params['xi_g']
        tau_g = self.params['tau_g']
        q_cm_vec = []
        s_vec = []
        s_cm = g.ec_mul(randomness)
        quotients, v = MLEPolynomial.decompose_by_div(polynomial, point)
        for i in range(len(quotients)):
            basis = basis_vec[i]
            q_mle = quotients[i]
            q_cm = msm_basic(basis, q_mle.evals)
            s = Field.rand()
            q_cm += xi_g.ec_mul(s)
            s_vec.append(s)
            s_cm -= tau_g[i].ec_mul(s)
            s_cm += g.ec_mul(s * point[i])
            q_cm_vec.append(q_cm)

        return v, {
            'q_cm_vec': q_cm_vec,
            's_cm': s_cm
        }

    def verify_evaluation(self, commitment: Commitment, point: Field, value: Field, argument: dict) -> bool:
        q_cm_vec = argument['q_cm_vec']
        s_cm = argument['s_cm']

        f_cm = commitment.cm
        g = self.params['g']
        xi_g = self.params['xi_g']
        h = self.params['h']
        tau_h = self.params['tau_h']
        xi_h = self.params['xi_h']

        lhs = [f_cm - g.ec_mul(value)]
        rhs = [-h]
        for i in range(len(q_cm_vec)):
            q_cm = q_cm_vec[i]
            lhs.append(q_cm)
            rhs.append(tau_h[i] - h.ec_mul(point[i]))
        lhs.append(s_cm)
        rhs.append(xi_h)

        checked = ec_pairing_check(lhs, rhs)
        return checked
    
def msm_basic(bases, scalars):
    """
    Basic implementation of multi-scalar multiplication using big integers.
    
    Args:
        bases: List of group elements
        bigints: List of big integers
    
    Returns:
        Group element representing the result of the multi-scalar multiplication
    """
    result = G1.zero()
    for base, scalar in zip(bases, scalars):
        result += base.ec_mul(scalar)
    return result

def product_and_sum(vec_a: list[Field], vec_b: list[Field]) -> Field:
    n = len(vec_a)
    assert len(vec_b) == n
    return sum(a * b for a, b in zip(vec_a, vec_b))

def test_commit_eq():
    pcs = LIBRA_PCS(debug=1)
    tau_vec = [Field(2), Field(3), Field(4)]
    pcs.setup(3, secret_vec=tau_vec)

    powers_of_tau = MLEPolynomial.compute_monomials(tau_vec)
    g = pcs.params['g']
    xi_g = pcs.params['xi_g']
    h = pcs.params['h']
    tau_h = pcs.params['tau_h']
    xi_h = pcs.params['xi_h']

    f1 = MLEPolynomial([Field(1), Field(2), Field(3), Field(4)], 2)
    f1_coeffs = MLEPolynomial.compute_coeffs_from_evals(f1.evals)
    print(f"f1_coeffs: {f1_coeffs}")
    f1_evals = MLEPolynomial.compute_evals_from_coeffs(f1_coeffs)
    print(f"f1_evals: {f1_evals}")

    cm1, s1 = pcs.commit_with_monomial_basis(f1_coeffs)
    print(f"cm1: {cm1.cm}")
    print(f"s1: {s1}")
    cm2, s2 = pcs.commit_with_multilinear_basis(f1_evals, 2)
    print(f"cm2: {cm2.cm}")
    print(f"s2: {s2}")

    assert cm1.cm - pcs.params['xi_g'].ec_mul(s1) == g.ec_mul(product_and_sum(powers_of_tau[:4], f1_coeffs))
    assert cm2.cm - pcs.params['xi_g'].ec_mul(s2) == g.ec_mul(product_and_sum(MLEPolynomial.eqs_over_hypercube(tau_vec[:2]), f1_evals))

    assert cm1.cm - pcs.params['xi_g'].ec_mul(s1) == cm2.cm - pcs.params['xi_g'].ec_mul(s2)

    assert msm_basic(pcs.params['powers_of_tau_g'][:4], f1_coeffs) == msm_basic(pcs.params['eqs_of_tau_g'][2], f1_evals)
    print("✅ test commit eq passed")
    
def test_setup():
    pcs = LIBRA_PCS(debug=1)
    num_var = 3
    tau_vec = [Field(2), Field(3), Field(4)]

    pcs.setup(num_var, secret_vec=tau_vec)

    g = pcs.params['g']

    powers_of_tau = MLEPolynomial.compute_monomials(tau_vec)
    srs_powers_of_tau = pcs.params['powers_of_tau_g']
    srs_eqs_of_tau = pcs.params['eqs_of_tau_g']

    for i in range(len(srs_powers_of_tau)):
        assert srs_powers_of_tau[i] == g.ec_mul(powers_of_tau[i])

    for k in range(num_var):
        eqs_of_tau = MLEPolynomial.eqs_over_hypercube(tau_vec[:k])
        for i in range(len(srs_eqs_of_tau[k])):
            assert srs_eqs_of_tau[k][i] == g.ec_mul(eqs_of_tau[i])

    f1 = MLEPolynomial([Field(1), Field(2), Field(3), Field(4)], 2)
    f1_coeffs = MLEPolynomial.compute_coeffs_from_evals(f1.evals)
    f1_evals = f1.evals
    print(f"f1_evals: {f1_evals}")
    print(f"f1_coeffs: {f1_coeffs}")

    f1_cm1 = msm_basic(srs_powers_of_tau, f1_coeffs)
    f1_cm2 = msm_basic(srs_eqs_of_tau[2], f1_evals)

    assert f1_cm1 == f1_cm2
    print("✅ test setup passed")
    
def test_prove_verify():
    pcs = LIBRA_PCS(debug=1)
    tau_vec = [Field(2), Field(3), Field(4)]
    pcs.setup(3, secret_vec=tau_vec)

    f1 = MLEPolynomial([Field(1), Field(2), Field(3), Field(4)], 2)
    f1_cm, r1 = pcs.commit(f1)
    f1_coeffs = MLEPolynomial.compute_coeffs_from_evals(f1.evals)
    print(f"f1_coeffs: {f1_coeffs}")
    print(f"f1_evals: {f1.evals}")

    point = [Field(1), Field(1)]

    v1, arg1 = pcs.prove_evaluation(f1, point, r1)
    print(f"v1: {v1}")
    print(f"arg1: {arg1}")

    checked = pcs.verify_evaluation(f1_cm, point, v1, arg1)
    print(f"checked: {checked}")
    assert checked, "Verification failed"
    print("✅ test prove verify passed")


if __name__ == "__main__":
    # pcs = LIBRA_PCS(G1, G2, Field, debug=True)

    # pcs.setup(3)

    # f1 = MLEPolynomial([Field(1), Field(2), Field(3), Field(4)], 2)
    # f1_cm, r1 = pcs.commit(f1)

    # point = [Field(1), Field(1)]
    # v1, arg1 = pcs.prove(f1, point, r1)
    # checked = pcs.verify(f1_cm, point, v1, arg1)
    # print(f"checked: {checked}")

    test_setup()

    test_commit_eq()

    test_prove_verify()
