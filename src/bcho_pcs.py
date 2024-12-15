#!/usr/bin/env python3

# WARNING: This implementation may contain bugs and has not been audited. 
# It is only for educational purposes. DO NOT use it in production.

from curve import Fr as Field, ec_mul, ec_mul_group2, G1Point as G1, G2Point as G2, ec_pairing_check
from unipoly import UniPolynomial
from random import randint
from utils import is_power_of_two, log_2
from mle2 import MLEPolynomial
from kzg10_non_hiding import Commitment, KZG10_PCS
from merlin.merlin_transcript import MerlinTranscript

class BCHO_PCS:
    """BCHO commitment scheme implementation."""
    params: dict

    def __init__(self, kzg_pcs: KZG10_PCS, debug=False):
        """
        Initialize the BCHO commitment scheme.
    
        Args:
            kzg_pcs: KZG10 PCS instance
        """

        self.kzg_pcs = kzg_pcs
        self.debug = debug

    def setup(self):
        """
        Generate the structured reference string (SRS).
        """
        pass

    def commit(self, f: UniPolynomial) -> Commitment:
        """
        Commit to a polynomial.
        """
        pass

    def prove_eval(self, commitment: Commitment, \
                               polynomial: MLEPolynomial, \
                               point: list[Field], \
                               transcript: MerlinTranscript, \
                               debug=0):
        """
        Prove evaluation argument 

        Args:
            commitment: commitment to the multilinear polynomial
            polynomial: multilinear polynomial
            point: evaluation point
            transcript: transcript
            debug: debug level
        """
        
        k = polynomial.num_var
        n = 2**k
        f_evals = polynomial.evals

        if len(point) != k:
            raise ValueError("Invalid evaluation point, k={}, while len(point)={}".format(k, len(point)))
        if not is_power_of_two(n):
            raise ValueError("Invalid polynomial length")
        
        value = polynomial.evaluate(point)

        transcript.absorb(b"f_commitment", commitment.cm)
        transcript.absorb(b"point", point)
        transcript.absorb(b"value", value)

        # Split and fold the polynomial (in half) continuously until it is a linear polynomial,
        # and store the intermediate polynomials and their commitments
        h_coeffs = polynomial.to_coeffs()
        h_poly_cm_vec = []
        h_poly_vec = [h_coeffs]
        for i in range(k-1):
            f_even = h_coeffs[::2]
            f_odd = h_coeffs[1::2]
            h_coeffs = [f_even[j] + point[i] * f_odd[j] for j in range(len(f_even))]
            h_cm = self.kzg_pcs.commit(UniPolynomial(h_coeffs))

            transcript.absorb(b"h_cm", h_cm)

            h_poly_vec.append(h_coeffs)
            h_poly_cm_vec.append(h_cm)

        if debug > 0: 
            h_coeffs = [h_coeffs[i] + point[k-1] * h_coeffs[i+1] for i in range(0, len(h_coeffs), 2)]
            print("check: fully folded polynomial must be equal to the claimed evaluation: {} = {}".format(h_coeffs[0], value))
            assert (h_coeffs[0] == value)
            assert len(h_coeffs) == 1
            print("coeffs=", h_coeffs)
            print("h_poly_cm_vec=", h_poly_cm_vec)
            print("h_poly_vec=", h_poly_vec)

        # Sample randomness and reply evaluations
        beta: Field = transcript.squeeze(Field, b"beta", 4)
        evals_pos = []
        evals_neg = []    
        evals_sq = []
        for i in range(k):
            poly = h_poly_vec[i]
            poly_at_beta = UniPolynomial.evaluate_at_point(poly, beta)
            poly_at_neg_beta = UniPolynomial.evaluate_at_point(poly, -beta)
            poly_at_beta_sq = UniPolynomial.evaluate_at_point(poly, beta * beta)
            evals_pos.append(poly_at_beta)
            evals_neg.append(poly_at_neg_beta)
            evals_sq.append(poly_at_beta_sq)
            transcript.absorb(b"poly_at_beta", poly_at_beta)
            transcript.absorb(b"poly_at_neg_beta", poly_at_neg_beta)

        transcript.absorb(b"evals_sq", evals_sq[0])

        print("evals_pos=", evals_pos)
        print("evals_neg=", evals_neg)
        print("evals_sq=", evals_sq)

        gamma: Field = transcript.squeeze(Field, b"gamma", 4)
        
        if debug > 0: 
            print("gamma=", gamma)

        h_agg = [0] * n
        for i in range(n):
            for j in range(k):
                poly = h_poly_vec[j]
                if i < len(poly):
                    h_agg[i] += poly[i] * (gamma**j)
        if debug > 1: 
            print("h_agg=", h_agg)
        
        h_agg_poly_at_beta = UniPolynomial.evaluate_at_point(h_agg, beta)
        h_agg_poly_at_neg_beta = UniPolynomial.evaluate_at_point(h_agg, -beta)
        h_agg_poly_at_beta_sq = UniPolynomial.evaluate_at_point(h_agg, beta * beta)

        if debug > 1: 
            print("h_agg_poly_at_beta={}, h_agg_poly_at_neg_beta={}, h_agg_poly_at_beta_sq={}".format(h_agg_poly_at_beta, h_agg_poly_at_neg_beta, h_agg_poly_at_beta_sq))

        # DEBUG: verify h_agg
        if debug > 0:
            print("check: aggregated h(X) must be equal to sum(h_i(X)) at (beta, -beta, beta^2)")
            assert h_agg_poly_at_beta == sum([evals_pos[i]*(gamma**i) for i in range(k)])
            assert h_agg_poly_at_neg_beta == sum([evals_neg[i]*(gamma**i) for i in range(k)])
            assert h_agg_poly_at_beta_sq == sum([evals_sq[i]*(gamma**i) for i in range(k)])

        # DEBUG: verify evaluations
        if debug > 0:
            dbg_evals_sq = evals_sq[:] + [value]
            print("dbg_evals_sq=", dbg_evals_sq)
            for i in range(k):
                print("check: h_{i+1}(r^2) = h_i(r) + h_i(-r))/2 + x_i * (h_i(r) - h_i(-r))/(2*r)")
                print("i={}, {}, {}".format(i, 
                    dbg_evals_sq[i+1], interp_and_eval_line(evals_pos[i], evals_neg[i], point[i], beta)))

        h_agg_poly = UniPolynomial(h_agg)
        interp_poly = UniPolynomial.interpolate([h_agg_poly_at_beta, h_agg_poly_at_neg_beta, h_agg_poly_at_beta_sq], [beta, -beta, beta * beta])
        vanishing_poly = UniPolynomial([-beta, 1])*UniPolynomial([beta, 1]) * UniPolynomial([-beta*beta, 1])
        g_poly = h_agg_poly - interp_poly
        quo_poly, rem = divmod(g_poly, vanishing_poly)

        if debug > 0:
            # assert rem == UniPolynomial([0])
            pass

        if debug > 1:
            print("interp_poly=", interp_poly)
            print("vanishing_poly=", vanishing_poly)    
            print("quo={}, rem={}".format(quo_poly, rem))
            print("quo_poly={}".format(quo_poly))
            print("rem={}".format(rem))
            print("quo={}".format(quo_poly))
        
        Cq = self.kzg_pcs.commit(UniPolynomial(quo_poly.coeffs))
        transcript.absorb(b"q_commitment", Cq)

        zeta: Field = transcript.squeeze(Field, b"zeta", 4)
        print("zeta={}".format(zeta))
        
        interp_at_zeta =interp_poly.evaluate(zeta)
        print("interp_at_zeta={}".format(interp_at_zeta))
        
        r_poly = h_agg_poly - UniPolynomial([interp_at_zeta]) - quo_poly * UniPolynomial([(zeta - beta) * (zeta + beta) * (zeta - beta*beta)])
        print("h_agg_poly - UniPolynomial([interp_at_zeta])=", h_agg_poly - UniPolynomial([interp_at_zeta]))
        print("quo_poly * ((zeta - beta) * (zeta + beta) * (zeta - beta*beta))=", quo_poly * UniPolynomial([(zeta - beta) * (zeta + beta) * (zeta - beta*beta)]))
        print("r_poly=", r_poly)

        print("r(zeta)={}".format(r_poly.evaluate(zeta)))

        Cr = self.kzg_pcs.commit(UniPolynomial(r_poly.coeffs))

        transcript.absorb(b"r_commitment", Cr)

        v, arg_r_poly_at_zeta = self.kzg_pcs.prove_evaluation(UniPolynomial(r_poly.coeffs), zeta)
        assert v == Field.zero(), "r(zeta) must be 0"

        # DEBUG: verify r_poly argument
        if debug > 0:
            print("check: `r(z)=0` argument must hold")
            assert self.kzg_pcs.verify_evaluation(Cr, zeta, Field.zero(), arg_r_poly_at_zeta)

        return value, {
            "h_poly_cm_vec": h_poly_cm_vec,
            "evals_pos_beta": evals_pos,
            "evals_neg_beta": evals_neg,
            "evals_sq_beta": evals_sq[:1],
            "q_commitment": Cq,
            "kzg_arg_r_poly_at_zeta": arg_r_poly_at_zeta
        }


    def verify_eval(self, C, arg, point, v, transcript, debug=0):
        """
        Verify an optimized evaluation argument proof.

        Args:
            C: commitment to f
            arg: argument to be verified (output of prove_eval_arg_opt)
            point: evaluation point
            v: claimed evaluation value
            transcript: proof transcript
        """
        k = len(point)
        n = 1 << k
        
        if debug > 1:
            print("C={}, arg={}, point={}, v={}".format(C, arg, point, v))

        transcript.absorb(b"f_commitment", C.cm)
        transcript.absorb(b"point", point)
        transcript.absorb(b"value", v)

        h_poly_cm_vec = arg["h_poly_cm_vec"]
        evals_pos = arg["evals_pos_beta"]
        evals_neg = arg["evals_neg_beta"]
        evals_sq = arg["evals_sq_beta"]
        Cq = arg["q_commitment"]
        Cw = arg["kzg_arg_r_poly_at_zeta"]

        for i in range(len(h_poly_cm_vec)):
            transcript.absorb(b"h_cm", h_poly_cm_vec[i])
        
        beta = transcript.squeeze(Field, b"beta", 4)
        if debug > 1:
            print("> beta = {}".format(beta))

        for i in range(k):
            transcript.absorb(b"poly_at_beta", evals_pos[i])
            transcript.absorb(b"poly_at_neg_beta", evals_neg[i])
            evals_sq.append(interp_and_eval_line(evals_pos[i], evals_neg[i], point[i], beta))
        transcript.absorb(b"evals_sq", evals_sq[0])

        if debug > 1:
            print("> evals_sq = {}".format(evals_sq))
        
        # 1st check:
        if debug > 0:
            print("🛡️: check if the evaluation f({})={} is correct".format(point, v))
            print("    by computing the folded polynomial h_{}({}^2) ?= {}".format(k, beta, v))
            if (evals_sq[-1] == v): 
                print("😀 ✅")
        if not (evals_sq[-1] == v):
            return False
        
        gamma: Field = transcript.squeeze(Field, b"gamma", 4)
        if debug > 1:
            print("> gamma = {}".format(gamma))

        Ch = C
        for i in range(0, k-1):
            Ch = Ch + h_poly_cm_vec[i].scalar_mul(gamma**(i+1))

        if debug > 1:
            print("> Commitment of h(X): Ch={}".format(Ch))
        
        # Compute h_agg(beta), h_agg(-beta), h_agg(beta^2)
        h_agg_poly_at_beta = sum([evals_pos[i]*(gamma**i) for i in range(k)])
        h_agg_poly_at_neg_beta = sum([evals_neg[i]*(gamma**i) for i in range(k)])
        h_agg_poly_at_beta_sq = sum([evals_sq[i]*(gamma**i) for i in range(k)])

        if debug > 1:
            print("> h_agg_poly_at_beta={}".format(h_agg_poly_at_beta))
            print("> h_agg_poly_at_neg_beta={}".format(h_agg_poly_at_neg_beta))
            print("> h_agg_poly_at_beta_sq={}".format(h_agg_poly_at_beta_sq))

        # Interpolate c(X) from three points: 
        #
        #    [(beta, h_agg(beta)), (-beta, h_agg(-beta)), (beta^2, h_agg(beta^2))]

        interp_poly = UniPolynomial.interpolate(
            [h_agg_poly_at_beta, h_agg_poly_at_neg_beta, h_agg_poly_at_beta_sq], 
            [beta, -beta, beta*beta])

        # h_agg(X) - c(X) = q(X) * (X-beta)(X+beta)(X-beta^2)
        # 
        # Receive Cq = Commit(c(X)) 
        transcript.absorb(b"q_commitment", Cq)

        # Sample randomness
        zeta: Field = transcript.squeeze(Field, b"zeta", 4)

        if debug > 1:
            print("> zeta = {}".format(zeta))
        
        # vanishing_poly_at_zeta= vanishing_poly.evaluate(zeta)
        interp_at_zeta = interp_poly.evaluate(zeta)
        vanishing_poly_at_zeta = ((zeta - beta) * (zeta + beta) * (zeta - beta*beta))

        print("interp_at_zeta={}".format(interp_at_zeta))

        Cr = Ch - self.kzg_pcs.commit(UniPolynomial([interp_at_zeta])) - Cq.scalar_mul(vanishing_poly_at_zeta)

        if debug > 1:
            print("> Cr={}".format(Cr))
            print("> Cq={}".format(Cq))

        transcript.absorb(b"r_commitment", Cr)

        # Verify r_poly argument
        
        # 2. Check if r(z)=0
        Cw_verified = self.kzg_pcs.verify_evaluation(Cr, zeta, Field.zero(), Cw)

        if debug > 0:
            if Cw_verified: print("🛡️: check if r(z)=0 😀 ✅")
            else: print("🛡️: check if r(z)=0 😢 ❌")

        if not Cw_verified:
            return False

        return True

def interp_and_eval_line(a, b, r, x):
    """
    Interpolate two points into a polynomial and evaluate it at X=r

        f(X) = [(-x, a), (x, b)] -> (a+b)/2 + ((a-b) / (2*x)) * X

        f(r) = (a+b)/2 + r * (a-b) / (2*x)
    Args:
        a (Field): The evaluation at -x
        b (Field): The evaluation at x
        r (Field): The point at which to evaluate the polynomial
        x (Field): The x-coordinate of the point

    Returns:
        int: The result of evaluating the polynomial at X=r
    """
    return ((a + b) / Field(2) + r * (a - b) / (Field(2) * x))


if __name__ == "__main__":
    a = Field(1)
    b = Field(2)
    r = Field(3)
    x = Field(4)
    print(interp_and_eval_line(a, b, r, x))

    kzg_pcs = KZG10_PCS(G1, G2, Field, 20, debug=True)

    bcho_pcs = BCHO_PCS(kzg_pcs, debug=True)

    f = MLEPolynomial([Field(1), Field(3), Field(2), Field(1)], 2)
    f_coeffs = f.to_coeffs()
    f_cm = kzg_pcs.commit(UniPolynomial(f_coeffs))

    tr = MerlinTranscript(b"test-bcho-pcs")

    point = [Field(2), Field(3)]
    value = f.evaluate(point)
    print(f"value={value}")

    value, arg = bcho_pcs.prove_eval(f_cm, f, 
            point, transcript=tr.fork(b"test"), debug=1)
    print(f"arg={arg}")

    verified = bcho_pcs.verify_eval(f_cm, arg, point, value, tr.fork(b"test"), debug=1)
    assert verified
    print("✅ test_prove_verify() passed")
