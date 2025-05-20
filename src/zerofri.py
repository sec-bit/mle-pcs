from batch_fri import BatchFRI
from fri import FRI
from group import DummyGroup
from unipoly2 import UniPolynomialWithFft
from utils import pow_2, is_power_of_two, log_2
from mle2 import MLEPolynomial
from merlin.merlin_transcript import MerlinTranscript
from kzg10 import KZG10Commitment
from babybear import BabyBear, BabyBearExtElem
# from sage.all import *
import sys

sys.path.append('finite-field')

class ZeroFRI:
    @classmethod
    def periodic_poly(cls, dim, degree, one=1):
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
        coeffs = [one - one] * (n * degree)
        for i in range(n):
            coeffs[i * degree] = one
        return UniPolynomialWithFft(coeffs)

    @classmethod
    def prove_zerofri(cls, f, rate, point, v, g, g_order, transcript, one=1, debug=0, batch=True):  
        """
            r(X) = ⟦f_mle⟧_n - v * 𝚽_n(z) - ∑_k(z^{2^k} * 𝚽_{n-k-1}(z^{2^{k+1}}) - uk * 𝚽_{n-k}(z^{2^k})) * ⟦q_k⟧_k
                = f(X) - v * 𝚽_n(z) 
                    - ∑_k (z^{2^k} * 𝚽_{n-k-1}(z^{2^{k+1}}) - uk * 𝚽_{n-k}(z^{2^k})) * q_k(X)
        f: polynomial
        transcript: transcript
        """
        assert isinstance(transcript, MerlinTranscript), "Transcript must be a MerlinTranscript"
        UniPolynomialWithFft.set_field_type(BabyBear)

        f_domain = [g ** (i * g_order // (len(f) * rate)) for i in range(len(f) * rate)]
        assert f_domain[1] == g ** (g_order // (len(f) * rate)), f"f_domain[1]: {f_domain[1]}, g ** (g_order // (len(f) * rate)): {g ** (g_order // (len(f) * rate))}"
        assert len(f_domain) == len(f) * rate, f"len(f_domain): {len(f_domain)}, len(f): {len(f)}, rate: {rate}"
        # f_evals = UniPolynomial.compute_evals_from_coeffs_fast(f, f_domain[:len(f)])
        # f_evals = [UniPolynomial.evaluate_at_point(f, x) for x in f_domain[:len(f)]]
        f_evals = UniPolynomialWithFft.fft(f, log_2(len(f)), g ** (g_order // len(f)))
        f_cm, f_code, f_coeffs = FRI.commit(f_evals, rate, f_domain, debug=False)
        if debug > 0:
            if debug > 1:
                print(f"P> send f_cm={str(f_cm.root)}")
            assert f == f_coeffs, f"f: {f}, f_coeffs: {f_coeffs}"
            assert len(f_code) == len(f_evals) * rate, f"len(f_code): {len(f_code)}, len(f_evals): {len(f_evals)}, rate: {rate}"
            for i in range(len(f_evals)):
                assert f_code[i * rate] == f_evals[i], f"f_code[{i * rate}]={f_code[i * rate]}, f_evals[{i}]={f_evals[i]}"
        transcript.append_message(b"f_cm", bytes(str(f_cm.root), encoding='ascii'))

        k = len(point)

        if debug > 1: print(f"P> f={f}, point={point}, v={v}")

        quotients_ascending, rem = MLEPolynomial(f, k).decompose_by_div(point)
        # Into length descending order
        quotients_evals_descending = [q.evals for q in reversed(quotients_ascending)]
        if debug > 1: print(f"quotients={quotients_evals_descending}, rem={rem}")
        if debug > 0:
            assert rem == v, "Evaluation does not match"
        f_uni = UniPolynomialWithFft(f)

        if debug > 1: print(f"P> send point={point}")
        if debug > 1: print(f"P> send v={v}")
        transcript.append_message(b"point", bytes(str(point), encoding='ascii'))
        transcript.append_message(b"v", bytes(str(v), encoding='ascii'))

        gen = g ** (g_order // ((1 << (len(quotients_evals_descending) - 1)) * rate))
        # Already in length descending order
        domains = [[gen ** (i * (1 << j)) for i in range(len(quotients_evals_descending[j]) * rate)] for j in range(len(quotients_evals_descending))]

        q_uni_vec = [UniPolynomialWithFft(q) for q in quotients_evals_descending]
        if debug > 1: print(f"P> q_uni_vec={q_uni_vec}, domains={domains}")

        # quotients_evals_descending = [[q_uni_vec[i].evaluate(x) for x in domains[i][::rate]] for i in range(len(q_uni_vec))]
        quotients_evals_descending = [UniPolynomialWithFft.fft(q.coeffs, log_2(len(q.coeffs)), g ** (g_order // len(q.coeffs))) for q in q_uni_vec[:-1]] + [q_uni_vec[-1].coeffs]
        if debug > 0:
            expected = [[q_uni_vec[i].evaluate(x) for x in domains[i][::rate]] for i in range(len(q_uni_vec))]
            for q, e in zip(q_uni_vec, expected):
                assert len(q.coeffs) == len(e), f"len(q)={len(q)}, len(e)={len(e)}"
            for i, q in enumerate(expected):
                omega = g ** (g_order // len(q))
                evals = [q_uni_vec[i].evaluate(omega ** j) for j in range(len(q))]
                assert evals == q, f"evals={evals}, q={q}"

            for i in range(len(quotients_evals_descending)):
                if i != 0:
                    assert len(quotients_evals_descending[i - 1]) >= len(quotients_evals_descending[i]), f"len(quotients[{i}]) < len(quotients[{i+1}]), {len(quotients_evals_descending[i])}, {len(quotients_evals_descending[i+1])}, quotients_evals={quotients_evals_descending}"
                assert is_power_of_two(len(quotients_evals_descending[i])), f"len(quotients[{i}]) is not a power of two, {len(quotients_evals_descending[i])}"
                assert quotients_evals_descending[i] == expected[i], f"quotients_evals_descending[{i}]={quotients_evals_descending[i]}, expected[{i}]={expected[i]}"

        q_cm = None
        q_code_descending = None
        if batch:
            q_cm, q_code_descending = BatchFRI.batch_commit(evals=quotients_evals_descending, rate=rate, domains=domains, one=one, debug=False)
            if debug > 0:
                if debug > 1:
                    print(f"P> q_code={q_code_descending}")
                    print(f"P> send q_cm={str(q_cm['layers'][-1][0])}")
                # coeffs = UniPolynomial.compute_coeffs_from_evals_fast(q_code_descending[0], [gen ** i for i in range(len(q_code_descending[0]))])
                coeffs = UniPolynomialWithFft.ifft(q_code_descending[0], log_2(len(q_code_descending[0])), domains[0][1])
                new_coeffs = []
                for i in range(len(coeffs)):
                    if coeffs[i] != one - one:
                        new_coeffs.append(coeffs[i])
                coeffs = new_coeffs
                assert len(coeffs) <= len(q_code_descending[0]) // rate, f"coeffs: {coeffs}, q_code[0]: {q_code_descending[0]}, rate: {rate}"
            transcript.append_message(b"q_cm", bytes(str(q_cm['layers'][-1][0]), encoding='ascii'))

            if debug > 1:
                print(f"P> f_cm={str(f_cm.root)}, q_cm={str(q_cm['layers'][-1][0])}, q_uni_vec={q_uni_vec}")
        else:
            q_cm = []
            q_code_descending = []
            for i in range(len(quotients_evals_descending) - 1): # last one is not verified
                if debug > 1: print(f"P> FRI.commit quotients_evals_descending[{i}]={quotients_evals_descending[i]}")
                # assert rate < len(domains[i]), f"i: {i}, rate: {rate}, domains: {domains}"
                comm, code, coeffs = FRI.commit(quotients_evals_descending[i], rate, domains[i], debug=debug > 1)
                q_cm.append(comm)
                q_code_descending.append(code)
                if debug > 0:
                    # coeffs = UniPolynomial.compute_coeffs_from_evals_fast(code, domains[i][:len(code)])
                    coeffs = UniPolynomialWithFft.ifft(code, log_2(len(code)), domains[i][1])
                    new_coeffs = []
                    for i in range(len(coeffs)):
                        if coeffs[i] != one - one:
                            new_coeffs.append(coeffs[i])
                    coeffs = new_coeffs
                    assert len(coeffs) <= len(code) // rate, f"coeffs: {coeffs}, code: {code}, rate: {rate}"
                    if debug > 1: print(f"P> send q_cm={str(comm.root)}")
                transcript.append_message(b"q_cm", bytes(str(comm.root), encoding='ascii'))

        gen = g ** (g_order // (len(f) * rate))
        zeta = BabyBearExtElem([BabyBear(int.from_bytes(transcript.challenge_bytes(b"zeta", 4), "big")), \
                                BabyBear(int.from_bytes(transcript.challenge_bytes(b"zeta", 4), "big")), \
                                    BabyBear(int.from_bytes(transcript.challenge_bytes(b"zeta", 4), "big")), \
                                        BabyBear(int.from_bytes(transcript.challenge_bytes(b"zeta", 4), "big"))])
        if debug > 1: print(f"P> receive zeta: {zeta} = {gen} ** {zeta} * {g}")

        f_evals = [BabyBearExtElem([e, BabyBear.zero(), BabyBear.zero(), BabyBear.zero()]) for e in f_evals]
        f_domain = [BabyBearExtElem([d, BabyBear.zero(), BabyBear.zero(), BabyBear.zero()]) for d in f_domain]

        UniPolynomialWithFft.set_field_type(BabyBearExtElem)
        f_val = UniPolynomialWithFft.evaluate_from_evals(f_evals, zeta, f_domain[::rate])
        # f_code = [BabyBearExtElem([e, BabyBear.zero(), BabyBear.zero(), BabyBear.zero()]) for e in f_code]
        domains = [[BabyBearExtElem([d, BabyBear.zero(), BabyBear.zero(), BabyBear.zero()]) for d in domain] for domain in domains]
        q_code_descending_ext = [[BabyBearExtElem([e, BabyBear.zero(), BabyBear.zero(), BabyBear.zero()]) for e in q] for q in q_code_descending]
        point = [BabyBearExtElem([p, BabyBear.zero(), BabyBear.zero(), BabyBear.zero()]) for p in point]
        if debug > 0:
            f_copy = [BabyBearExtElem([e, BabyBear.zero(), BabyBear.zero(), BabyBear.zero()]) for e in f]
            assert f_val == UniPolynomialWithFft.evaluate_at_point(f_copy, zeta), f"f_val: {f_val}, UniPolynomial.evaluate_at_point(f, zeta): {UniPolynomialWithFft.evaluate_at_point(f_copy, zeta)}"
        f_proof = FRI.prove(f_code, f_cm, f_val, zeta, f_domain, rate, len(f), f_domain[1].elems[0], transcript, BabyBearExtElem.one(), debug=debug > 1)
        if debug > 1: print(f"P> ▶️▶️ f_proof={f_proof}")

        quotients_vals_descending = [UniPolynomialWithFft.evaluate_from_evals(q_code_descending_ext[i], zeta, domains[i][:len(q_code_descending[i])]) for i in range(len(q_code_descending))]
        if not batch:
            quotients_vals_descending.append(quotients_evals_descending[-1][0]) # last one is not verified
        quotients_proof = None
        if batch:
            gen = g ** (g_order // ((1 << (len(quotients_evals_descending) - 1)) * rate))
            quotients_proof = BatchFRI.batch_prove(q_code_descending, q_cm, quotients_vals_descending, zeta, domains, rate, (1 << (len(quotients_evals_descending) - 1)), BabyBearExtElem([gen, BabyBear.zero(), BabyBear.zero(), BabyBear.zero()]), transcript, BabyBearExtElem.one(), debug=debug > 0)
            if debug > 1: print(f"P> ▶️▶️ quotients_proof={quotients_proof}")
        else:
            quotients_proof = []
            for i in range(len(quotients_evals_descending) - 1):
                gen = g ** (g_order // ((1 << (len(quotients_evals_descending) - 1 - i)) * rate))
                if debug > 0:
                    domain = [gen ** j for j in range((1 << (len(quotients_evals_descending) - 1 - i)) * rate)]
                    domain = [BabyBearExtElem([d, BabyBear.zero(), BabyBear.zero(), BabyBear.zero()]) for d in domain]
                    assert domain == domains[i], f"domain: {domain}, domains[i]: {domains[i]}"
                    if debug > 1:
                        print(f"P> FRI.prove domain={domain}")
                        print(f"P> FRI.prove q_cm={str(q_cm[i].root)}, domain={domains[i]}")
                quotients_proof.append(FRI.prove(q_code_descending[i], q_cm[i], quotients_vals_descending[i], zeta, domains[i], rate, (1 << (len(quotients_evals_descending) - 1 - i)), gen, transcript, BabyBearExtElem.one(), debug=debug > 1))

        if debug > 0:
            # compute r(X) = f(X) - v * phi_n(zeta) - ∑_i (c_i * qi(X))
            phi_uni_at_zeta = cls.periodic_poly(k, 1, BabyBearExtElem.one()).evaluate(zeta)
            if debug > 1:
                print(f"P> f_uni={f_uni}, v={v}, phi_uni_at_zeta={phi_uni_at_zeta}")

            r_val = f_val - phi_uni_at_zeta * v
            quotients_vals_ascending = list(reversed(quotients_vals_descending))
            if debug > 1:
                print(f"P> quotients_vals={quotients_vals_ascending}")
            for i in range(k):
                c_i = zeta ** (pow_2(i)) * cls.periodic_poly(k-i-1, pow_2(i+1), BabyBearExtElem.one()).evaluate(zeta) \
                        - point[i] * cls.periodic_poly(k-i, pow_2(i), BabyBearExtElem.one()).evaluate(zeta)
                r_val -= c_i * quotients_vals_ascending[i]

            assert r_val == BabyBearExtElem.zero(), f"Evaluation does not match, {r_val}!=0"
            if debug > 1:
                print(f"P> 👀 r(zeta={zeta}) == 0 ✅")
                print("P> r_val=", r_val)
        
        return (f_proof, f_val, quotients_proof, quotients_vals_descending)
    
    @classmethod
    def verify_zerofri(cls, f_proof, f_val, quotients_proof, quotients_vals, num_var, rate, point, v, g, g_order, transcript, one = 1, debug=0, batch=True):
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

        if debug > 1: print(f"V> receive f_cm={str(f_proof['proof']['first_oracle'])}")
        transcript.append_message(b"f_cm", bytes(str(f_proof['proof']['first_oracle']), encoding='ascii'))

        k = len(point)
        assert k == num_var, "Number of variables must match the point"

        if debug > 1: print(f"V> receive point={point}")
        if debug > 1: print(f"V> receive v={v}")
        transcript.append_message(b"point", bytes(str(point), encoding='ascii'))
        transcript.append_message(b"v", bytes(str(v), encoding='ascii'))
        if batch:
            if debug > 1: print(f"V> receive q_cm={str(quotients_proof['code_commitment'])}")
            transcript.append_message(b"q_cm", bytes(str(quotients_proof['code_commitment']), encoding='ascii'))
        else:
            for i in range(len(quotients_proof)):
                if debug > 1: print(f"V> receive q_cm={str(quotients_proof[i]['proof']['first_oracle'])}")
                transcript.append_message(b"q_cm", bytes(str(quotients_proof[i]['proof']['first_oracle']), encoding='ascii'))

        gen = g ** (g_order // ((1 << num_var) * rate))

        zeta = BabyBearExtElem([BabyBear(int.from_bytes(transcript.challenge_bytes(b"zeta", 4), "big")), \
                                BabyBear(int.from_bytes(transcript.challenge_bytes(b"zeta", 4), "big")), \
                                    BabyBear(int.from_bytes(transcript.challenge_bytes(b"zeta", 4), "big")), \
                                        BabyBear(int.from_bytes(transcript.challenge_bytes(b"zeta", 4), "big"))])
        if debug > 1: print(f"V> send zeta: {zeta} = {gen} ** {zeta} * {g}")
        point = [BabyBearExtElem([p, BabyBear.zero(), BabyBear.zero(), BabyBear.zero()]) for p in point]

        f_domain = [g ** (i * g_order // ((1 << num_var) * rate)) for i in range((1 << num_var) * rate)]
        FRI.verify(1 << num_var, rate, f_proof, zeta, f_val, f_domain, f_domain[1], transcript, BabyBearExtElem.one(), debug=debug > 1)

        gen = g ** (g_order // ((1 << (num_var - 1)) * rate))
        domains = [[gen ** (i * (1 << j)) for i in range((1 << (num_var - 1)) * rate)] for j in range(num_var)]
        if batch:
            if debug > 1: print(f"V> degree_bound={1 << (num_var - 1)}, rate={rate}, proof={quotients_proof}, vals={quotients_vals}, domains={domains}, gen={gen}, shift={g}")
            BatchFRI.batch_verify(1 << (num_var - 1), rate, quotients_proof, zeta, quotients_vals, gen, one, transcript, debug=debug > 0)
        else:
            for i in range(num_var - 1): # last one is not verified
                if debug > 1: 
                    print(f"V> degree_bound={1 << (num_var - 1 - i)}, rate={rate}, proof={quotients_proof[i]}, vals={quotients_vals[i]}, domain={domains[i]}, gen={gen}, shift={g}")
                    # print(f"V> FRI.verify q_cm={str(quotients_proof[i]['code_commitment'])}")
                FRI.verify(1 << (num_var - 1 - i), rate, quotients_proof[i], zeta, quotients_vals[i], domains[i], gen ** (1 << i), transcript, BabyBearExtElem.one(), debug=debug > 1)

        phi_uni_at_zeta = cls.periodic_poly(k, 1, BabyBearExtElem.one()).evaluate(zeta)
        r_val = f_val - phi_uni_at_zeta * v
        for i in range(k):
            c_i = zeta ** (pow_2(i)) * cls.periodic_poly(k-i-1, pow_2(i+1), BabyBearExtElem.one()).evaluate(zeta) \
                    - point[i] * cls.periodic_poly(k-i, pow_2(i), BabyBearExtElem.one()).evaluate(zeta)
            # query quotients_vals in descending order
            r_val -= c_i * quotients_vals[k - i - 1]
        if debug > 1:
            print(f"V> r_val={r_val}")
            print("V> 👀  r(zeta) == 0 ✅" if r_val == 0 else "👀  r(zeta) == 0 ❌")

        assert r_val == BabyBearExtElem.zero(), f"Evaluation does not match, {r_val}!=0"
