from batch_fri import BatchFRI
from fri import FRI
from group import DummyGroup
from unipolynomial import UniPolynomial
from utils import pow_2, is_power_of_two, log_2
from mle2 import MLEPolynomial
from merlin.merlin_transcript import MerlinTranscript
from kzg10 import KZG10Commitment
from sage.all import *

class ZeroFRI:
    @classmethod
    def periodic_poly(cls, dim, degree):
        """
        Compute the periodic polynomial Phi(X^d)

            Phi_k(X)   = 1 + X   + X^2  + X^3  + ... + X^(2^k-1)
            Phi_k(X^d) = 1 + X^d + X^2d + X^3d + ... + X^(2^(k-1))d

        Args:
            dim: dimension of the space of size 2^k
            degree: degree of X^d

        Returns:
            list: the coefficients of Phi(X^d)
        """
        n = pow_2(dim)
        coeffs = [0] * (n * degree)
        for i in range(n):
            coeffs[i * degree] = 1
        return UniPolynomial(coeffs)

    @classmethod
    def prove_zeromorph_naive(cls, f, rate, point, v, g, g_order, transcript, one=1, debug=0):  
        """
            r(X) = ⟦f_mle⟧_n - v * 𝚽_n(z) - ∑_k(z^{2^k} * 𝚽_{n-k-1}(z^{2^{k+1}}) - uk * 𝚽_{n-k}(z^{2^k})) * ⟦q_k⟧_k
                = f(X) - v * 𝚽_n(z) 
                    - ∑_k (z^{2^k} * 𝚽_{n-k-1}(z^{2^{k+1}}) - uk * 𝚽_{n-k}(z^{2^k})) * q_k(X)
        f: polynomial
        transcript: transcript
        """
        assert isinstance(transcript, MerlinTranscript), "Transcript must be a MerlinTranscript"

        f_domain = [g ** (i * g_order // (len(f) * rate)) for i in range(len(f) * rate)]
        # f_evals = UniPolynomial.compute_evals_from_coeffs_fast(f, f_domain[:len(f)])
        f_evals = [UniPolynomial.evaluate_at_point(f, x) for x in f_domain[:len(f)]]
        f_cm, f_code = FRI.commit(f_evals, rate, f_domain, debug=False)
        if debug > 0: print(f"P> send f_cm={str(f_cm.root)}")
        transcript.append_message(b"f_cm", bytes(str(f_cm.root), encoding='ascii'))

        k = len(point)

        print(f"P> f={f}, point={point}, v={v}")

        quotients_ascending, rem = MLEPolynomial(f, k).decompose_by_div(point)
        # Into length descending order
        quotients_evals_descending = [q.evals for q in reversed(quotients_ascending)]
        print(f"quotients={quotients_evals_descending}, rem={rem}")
        assert rem == v, "Evaluation does not match"
        f_uni = UniPolynomial(f)

        print(f"P> send point={point}")
        print(f"P> send v={v}")
        transcript.append_message(b"point", bytes(str(point), encoding='ascii'))
        transcript.append_message(b"v", bytes(str(v), encoding='ascii'))

        gen = g ** (g_order // ((1 << (len(quotients_evals_descending) - 1)) * rate))
        # Already in length descending order
        domains = [[gen ** (i * (1 << j)) for i in range(len(quotients_evals_descending[j]) * rate)] for j in range(len(quotients_evals_descending))]

        q_uni_vec = [UniPolynomial(q) for q in quotients_evals_descending]
        if debug > 0: print(f"P> q_uni_vec={q_uni_vec}, domains={domains}")
        # quotients_evals_descending = [UniPolynomial.compute_evals_from_coeffs_fast(q_uni_vec[i].coeffs, domains[i][:len(q_uni_vec[i].coeffs)], debug=True) for i in range(len(q_uni_vec))]
        quotients_evals_descending = [[q_uni_vec[i].evaluate(x) for x in domains[i][:len(q_uni_vec[i].coeffs)]] for i in range(len(q_uni_vec))]
        if debug > 0:
            for i in range(len(quotients_evals_descending)):
                if i is not 0:
                    assert len(quotients_evals_descending[i - 1]) >= len(quotients_evals_descending[i]), f"len(quotients[{i}]) < len(quotients[{i+1}]), {len(quotients_evals_descending[i])}, {len(quotients_evals_descending[i+1])}, quotients_evals={quotients_evals_descending}"
                assert is_power_of_two(len(quotients_evals_descending[i])), f"len(quotients[{i}]) is not a power of two, {len(quotients_evals_descending[i])}"
        q_cm, q_code_descending = BatchFRI.batch_commit(evals=quotients_evals_descending, rate=rate, domains=domains, debug=False)
        if debug > 0: 
            print(f"P> q_code={q_code_descending}")
            print(f"P> send q_cm={str(q_cm['layers'][-1][0])}")
            coeffs = UniPolynomial.compute_coeffs_from_evals_fast(q_code_descending[0], [gen ** i for i in range(len(q_code_descending[0]))])
            assert len(coeffs) <= len(q_code_descending[0]) // rate, f"coeffs: {coeffs}, q_code[0]: {q_code_descending[0]}, rate: {rate}"
        transcript.append_message(b"q_cm", bytes(str(q_cm['layers'][-1][0]), encoding='ascii'))

        print(f"P> f_cm={str(f_cm.root)}, q_cm={str(q_cm['layers'][-1][0])}, q_uni_vec={q_uni_vec}")

        gen = g ** (g_order // (len(f) * rate))
        zeta = int.from_bytes(transcript.challenge_bytes(b"zeta", 4), "big") % g_order
        zeta = gen ** zeta * g
        if debug > 0: print(f"P> receive zeta: {zeta} = {gen} ** {zeta} * {g}")

        f_val = UniPolynomial.uni_eval_from_evals(f_evals, zeta, f_domain[:len(f_evals)], one)
        if debug > 1:
            assert f_val == UniPolynomial.evaluate_at_point(f, zeta), f"f_val: {f_val}, UniPolynomial.evaluate_at_point(f, zeta): {UniPolynomial.evaluate_at_point(f, zeta)}"
        f_proof = FRI.prove(f_code, f_cm, f_val, zeta, f_domain, rate, len(f), g ** (g_order // (len(f) * rate)), transcript, debug=True)
        print(f"P> ▶️▶️ f_proof={f_proof}")
        # transcript.append_message(b"f_proof", bytes(str(f_proof), encoding='ascii'))

        gen = g ** (g_order // ((1 << (len(quotients_evals_descending) - 1)) * rate))
        quotients_vals_descending = [UniPolynomial.uni_eval_from_evals(q_code_descending[i], zeta, domains[i][:len(q_code_descending[i])], one) for i in range(len(q_code_descending))]
        quotients_proof = BatchFRI.batch_prove(q_code_descending, q_cm, quotients_vals_descending, zeta, domains, rate, (1 << (len(quotients_evals_descending) - 1)), gen, transcript, debug=True)
        print(f"P> ▶️▶️ quotients_proof={quotients_proof}")
        # transcript.append_message(b"quotients_proof", bytes(str(quotients_proof), encoding='ascii'))

        if debug > 0:
            # compute r(X) = f(X) - v * phi_n(zeta) - ∑_i (c_i * qi(X))
            phi_uni_at_zeta = cls.periodic_poly(k, 1).evaluate(zeta)
            if debug > 1:
                print(f"P> f_uni={f_uni}, v={v}, phi_uni_at_zeta={phi_uni_at_zeta}")

            r_val = f_val - phi_uni_at_zeta * v
            quotients_vals_ascending = list(reversed(quotients_vals_descending))
            if debug > 1:
                print(f"P> quotients_vals={quotients_vals_ascending}")
            for i in range(k):
                c_i = zeta ** (pow_2(i)) * cls.periodic_poly(k-i-1, pow_2(i+1)).evaluate(zeta) \
                        - point[i] * cls.periodic_poly(k-i, pow_2(i)).evaluate(zeta)
                r_val -= c_i * quotients_vals_ascending[i]

            assert r_val == 0, f"Evaluation does not match, {r_val}!=0"
            print(f"P> 👀 r(zeta={zeta}) == 0 ✅")

        if debug > 1:
            print("P> r_val=", r_val)
        
        return (f_proof, f_val, quotients_proof, quotients_vals_descending)
    
    @classmethod
    def verify_zeromorph_naive(cls, f_proof, f_val, quotients_proof, quotients_vals, num_var, rate, point, v, g, g_order, transcript, debug=0):
        """
        Verify an evaluation proof(argument) of the MLE polynomial in Zeromorph+KZG10.

        Args:
            f_cm: commitment to the MLE polynomial
            num_var: number of variables
            point: (u0, u1, ..., u_{k-1})
            v: evaluation value
            prf: proof
        
        Returns:
            bool: True if the proof is valid, False otherwise.
        """
        assert isinstance(transcript, MerlinTranscript), "Transcript must be a MerlinTranscript"

        if debug > 0: print(f"V> receive f_cm={str(f_proof['code_commitment'])}")
        transcript.append_message(b"f_cm", bytes(str(f_proof['code_commitment']), encoding='ascii'))

        k = len(point)
        assert k == num_var, "Number of variables must match the point"

        if debug > 0: print(f"V> receive point={point}")
        if debug > 0: print(f"V> receive v={v}")
        transcript.append_message(b"point", bytes(str(point), encoding='ascii'))
        transcript.append_message(b"v", bytes(str(v), encoding='ascii'))
        if debug > 0: print(f"V> receive q_cm={str(quotients_proof['code_commitment'])}")
        transcript.append_message(b"q_cm", bytes(str(quotients_proof['code_commitment']), encoding='ascii'))

        gen = g ** (g_order // ((1 << num_var) * rate))

        zeta = int.from_bytes(transcript.challenge_bytes(b"zeta", 4), "big") % g_order
        zeta = gen ** zeta * g
        if debug > 0: print(f"V> send zeta: {zeta} = {gen} ** {zeta} * {g}")

        f_domain = [g ** (i * g_order // ((1 << num_var) * rate)) for i in range((1 << num_var) * rate)]
        FRI.verify(1 << num_var, rate, f_proof, zeta, f_val, f_domain, f_domain[1], transcript, debug=True)

        # transcript.append_message(b"f_proof", bytes(str(f_proof), encoding='ascii'))

        gen = g ** (g_order // ((1 << (num_var - 1)) * rate))
        domains = [[gen ** (i * (1 << j)) for i in range((1 << (num_var - 1)) * rate)] for j in range(num_var)]
        if debug > 0: print(f"V> degree_bound={1 << (num_var - 1)}, rate={rate}, proof={quotients_proof}, vals={quotients_vals}, domains={domains}, gen={gen}, shift={g}")
        BatchFRI.batch_verify(1 << (num_var - 1), rate, quotients_proof, zeta, quotients_vals, domains, gen, g, transcript, debug=True)

        # transcript.append_message(b"quotients_proof", bytes(str(quotients_proof), encoding='ascii'))

        phi_uni_at_zeta = cls.periodic_poly(k, 1).evaluate(zeta)
        r_val = f_val - phi_uni_at_zeta * v
        for i in range(k):
            c_i = zeta ** (pow_2(i)) * cls.periodic_poly(k-i-1, pow_2(i+1)).evaluate(zeta) \
                    - point[i] * cls.periodic_poly(k-i, pow_2(i)).evaluate(zeta)
            # query quotients_vals in descending order
            r_val -= c_i * quotients_vals[k - i - 1]
        print(f"V> r_val={r_val}")
        print("V> 👀  r(zeta) == 0 ✅" if r_val == 0 else "👀  r(zeta) == 0 ❌")

        assert r_val == 0, f"Evaluation does not match, {r_val}!=0"
    
if __name__ == "__main__":

    from random import randint

    p = 193
    Fp = GF(p)
    G1 = DummyGroup(Fp)
    G2 = DummyGroup(Fp)
    kzg10 = KZG10Commitment(G1, G2, 24)

    UniPolynomial.set_scalar(int, lambda x: Fp(x))
    
    num_vars = 4
    rate = 4
    # point = [Fp(randint(0, p-1)) for _ in range(num_vars)]
    # mle_poly = [Fp(randint(0, p-1)) for _ in range(1 << num_vars)]
    point = [60, 178, 80, 95]
    point = [Fp(x) for x in point]
    mle_poly = [24, 40, 177, 138, 189, 185, 53, 115, 159, 142, 8, 82, 111, 139, 100, 66]
    mle_poly = [Fp(x) for x in mle_poly]
    v = MLEPolynomial(mle_poly, num_vars).evaluate(point)

    f_proof, f_val, quotients_proof, quotients_vals = ZeroFRI.prove_zeromorph_naive(mle_poly, rate, point, v, Fp.primitive_element(), p-1, MerlinTranscript(b'zeromorph'), one=Fp(1), debug=2)
    ZeroFRI.verify_zeromorph_naive(f_proof, f_val, quotients_proof, quotients_vals, num_vars, rate, point, v, Fp.primitive_element(), p-1, MerlinTranscript(b'zeromorph'), debug=2)
