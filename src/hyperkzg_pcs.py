#!/usr/bin/env python3

# WARNING: This implementation may contain bugs and has not undergone auditing. 
# It is intended for educational and research purposes only with insecure randomness. 
# DO NOT use it in a production environment.

from curve import Fr as Field, G1Point as G1, G2Point as G2
from unipoly2 import UniPolynomial
from random import randint
from utils import is_power_of_two
from mle2 import MLEPolynomial
from kzg10_non_hiding2 import Commitment, KZG10_PCS
from merlin.merlin_transcript import MerlinTranscript


# POC Implementation of HYPERKZG-PCS from Nova's code
#
#   https://github.com/microsoft/Nova/blob/main/src/provider/hyperkzg.rs
#

# NOTE: this HyperKZG-POC is almost identical to the BCHO-PCS implementation.
#       The only difference is the folding function, as defined in `interp_and_eval_line()`.

class HYPERKZG_PCS:
    """HYPERKZG commitment scheme implementation."""
    params: dict

    def __init__(self, kzg_pcs: KZG10_PCS, debug=False):
        """
        Initialize the HYPERKZG commitment scheme.
    
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

    def commit(self, f: MLEPolynomial) -> Commitment:
        """
        Commit to a polynomial.
        """
        
        f_evals = f.evals
        f = UniPolynomial(f_evals)

        assert f.degree < self.kzg_pcs.max_degree, \
            "f.degree must be less than max_degree of the KZG10 PCS"
        
        f_cm = self.kzg_pcs.commit(f)
        return f_cm

    def prove_eval(self, 
                   f_cm: Commitment, 
                   f_mle: MLEPolynomial, 
                   us: list[Field], 
                   tr: MerlinTranscript) -> tuple[Field, dict]:
        """
        Prove evaluation argument 

        Args:
            f_cm: commitment to the multilinear polynomial
            f_mle: multilinear polynomial
            us: evaluation point
            tr: transcript
        """
        
        k = f_mle.num_var
        n = 2**k
        f_evals = f_mle.evals

        if len(us) != k:
            raise ValueError("Invalid evaluation point, k={}, while len(point)={}".format(k, len(us)))
        if not is_power_of_two(n):
            raise ValueError("Invalid polynomial length")
        
        value = f_mle.evaluate(us)

        # > Round 0

        tr.absorb(b"polynomial", f_cm.cm)
        tr.absorb(b"point", us)
        tr.absorb(b"value", value)

        # > Round 1

        # Split and fold the polynomial (in half) continuously until it is a linear polynomial,
        # and store the intermediate polynomials and their commitments        
        #
        #   (1 - ui) * a_{2i} + ui * a_{2i+1}
        #   = a_{2i} + ui * (a_{2i+1} - a_{2i})
        
        h_poly_cm_vec = []
        h_poly_vec = [f_evals]
        for i in range(k-1):
            h_even = f_evals[::2]
            h_odd = f_evals[1::2]
            h_evals = [h_even[j] + us[i] * (h_odd[j] - h_even[j]) for j in range(len(h_even))]
            h_cm = self.kzg_pcs.commit(UniPolynomial(h_evals))
            h_poly_vec.append(h_evals)
            h_poly_cm_vec.append(h_cm)

        for i in range(len(h_poly_cm_vec)):
            tr.absorb(b"h_cm", h_poly_cm_vec[i])

        if self.debug > 0:
            print("P> send h_poly_cm_vec=", h_poly_cm_vec)

        if self.debug > 1: 
            print("P> check: folded polynomial")
            h_evals = [h_evals[i] + us[k-1] * (h_evals[i+1] - h_evals[i]) for i in range(0, len(h_evals), 2)]
            print("P> check: fully folded polynomial must be equal to the claimed evaluation: {} = {}".format(h_evals[0], value))
            assert (h_evals[0] == value)
            assert len(h_evals) == 1
            print("P> check: folded polynomial passed")

        # > Round 2

        # Sample randomness and reply evaluations
        beta: Field = tr.squeeze(Field, b"beta", 4)
        if self.debug > 0:
            print("P> beta = {}".format(beta))

        # Compute evaluations of h_i(X) at beta, -beta, beta^2
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

        # Send evaluations
        for i in range(k):
            tr.absorb(b"poly_at_beta", evals_pos[i])
            tr.absorb(b"poly_at_neg_beta", evals_neg[i])
        tr.absorb(b"evals_sq", evals_sq[0])

        if self.debug > 0:
            print("P> send evals_pos=", evals_pos)
            print("P> send evals_neg=", evals_neg)
            print("P> send evals_sq=", evals_sq)

        # > Round 3

        gamma: Field = tr.squeeze(Field, b"gamma", 4)
        
        if self.debug > 0: print("P> gamma=", gamma)

        # Compute h(X)
        #
        #    h(X) = h_0(X) + gamma * h_1(X) + gamma^2 * h_2(X) + ... + gamma^{n-1} * h_{n-1}(X)
        #
        h_agg = [0] * n
        for i in range(n):
            for j in range(k):
                poly = h_poly_vec[j]
                if i < len(poly):
                    h_agg[i] += poly[i] * (gamma**j)
        
        h_agg_poly_at_beta = UniPolynomial.evaluate_at_point(h_agg, beta)
        h_agg_poly_at_neg_beta = UniPolynomial.evaluate_at_point(h_agg, -beta)
        h_agg_poly_at_beta_sq = UniPolynomial.evaluate_at_point(h_agg, beta * beta)

        if self.debug > 1:
            print("P> check: h(X) must be equal to sum(h_i(X)) at (beta, -beta, beta^2)")
            assert h_agg_poly_at_beta == sum([evals_pos[i]*(gamma**i) for i in range(k)])
            assert h_agg_poly_at_neg_beta == sum([evals_neg[i]*(gamma**i) for i in range(k)])
            assert h_agg_poly_at_beta_sq == sum([evals_sq[i]*(gamma**i) for i in range(k)])
            print("P> check: h(X) passed")

        if self.debug > 1:
            print("P> check: hi(X) evaluations")
            dbg_evals_sq = evals_sq[:] + [value]
            print("P> dbg_evals_sq=", dbg_evals_sq)
            for i in range(k):
                print("P> check: h_{i+1}(r^2) = (1-x_i) * (h_i(r) + h_i(-r))/2) + x_i * (h_i(r) - h_i(-r))/(2*r)")
                print("P> i={}, {}, {}".format(i, 
                    dbg_evals_sq[i+1], interp_and_eval_line(evals_pos[i], evals_neg[i], point[i], beta)))
            print("P> check: hi(X) evaluations passed")

        # Interpolate h*(X) from three points: 
        #
        #    [(beta, h_agg(beta)), (-beta, h_agg(-beta)), (beta^2, h_agg(beta^2))]
        #
        #   h*(X) = h(beta) * (X+beta)(X-beta^2)  / (2*beta*(beta-beta^2)) + 
        #           h(-beta) * (X-beta)(X-beta^2) / (2*beta*(beta^2-beta)) + 
        #           h(beta^2) * (X+beta)(X-beta)  / (beta^4-beta^2)
        #
        interp_poly = UniPolynomial.interpolate([h_agg_poly_at_beta, h_agg_poly_at_neg_beta, 
                                                 h_agg_poly_at_beta_sq], [beta, -beta, beta * beta])

        # Compute q(X)
        #
        #    q(X) = (h(X) - h*(X)) / (X^2-beta^2)(X-beta^2)
        #
        h_agg_poly = UniPolynomial(h_agg)
        vanishing_poly = UniPolynomial([-beta, 1]) * UniPolynomial([beta, 1]) * UniPolynomial([-beta*beta, 1])
        g_poly = h_agg_poly - interp_poly
        quo_poly, rem = divmod(g_poly, vanishing_poly)

        if self.debug > 1: 
            print("P> check: g(X) divisibility")
            assert rem == UniPolynomial([0])
            print("P> check: g(X) divisibility passed")
        
        # Commit to q(X)
        q_cm = self.kzg_pcs.commit(UniPolynomial(quo_poly.coeffs))

        # Send Cq
        tr.absorb(b"q_commitment", q_cm)

        if self.debug > 0:
            print("P> send q_cm=", q_cm)

        # > Round 4

        zeta: Field = tr.squeeze(Field, b"zeta", 4)

        if self.debug > 0: print("P> zeta={}".format(zeta))
        
        # Compute r(X)
        #
        #    r(X) = h(X) - h*(zeta) - (zeta^2-beta^2)(zeta-beta^2) * q(X)
        #
        interp_at_zeta =interp_poly.evaluate(zeta)
        r_poly = h_agg_poly - UniPolynomial([interp_at_zeta]) - quo_poly * UniPolynomial([(zeta - beta) * (zeta + beta) * (zeta - beta*beta)])

        # Commit to r(X)
        r_cm = self.kzg_pcs.commit(UniPolynomial(r_poly.coeffs))

        # Compute [w(tau)]_1 which is a commitment of w(X)
        #
        #    w(X) = r(X) / (X-zeta)
        #
        v, arg_r_poly_at_zeta = self.kzg_pcs.prove_evaluation(UniPolynomial(r_poly.coeffs), zeta)
        if self.debug > 1: 
            print("P> check: r(zeta)=0")
            assert v == Field.zero(), "r(zeta) must be 0"
            print("P> check: r(zeta)=0 passed")
        
        if self.debug > 0:
            print("P> send the proof of `r(zeta)=0`", arg_r_poly_at_zeta)

        if self.debug > 1:
            assert self.kzg_pcs.verify_evaluation(r_cm, zeta, Field.zero(), arg_r_poly_at_zeta), "kzg10 verify r_poly failed"

        return value, {
            "h_poly_cm_vec": h_poly_cm_vec,
            "evals_pos_beta": evals_pos,
            "evals_neg_beta": evals_neg,
            "evals_sq_beta": evals_sq[:1],
            "q_commitment": q_cm,
            "kzg_arg_r_poly_at_zeta": arg_r_poly_at_zeta
        }


    def verify_eval(self, 
                    f_cm: Commitment, 
                    us: list[Field], 
                    v: Field, 
                    arg: dict, 
                    tr: MerlinTranscript):
        """
        Verify an optimized evaluation argument proof.

        Args:
            C: commitment to f
            point: evaluation point
            v: claimed evaluation value
            arg: argument to be verified (output of prove_eval_arg_opt)
            tr: proof transcript
        """
        k = len(us)
        n = 1 << k
        
        if self.debug > 1:
            print("V> C={}, arg={}, point={}, v={}".format(C, arg, point, v))

        # > Round 0

        tr.absorb(b"polynomial", f_cm.cm)
        tr.absorb(b"point", us)
        tr.absorb(b"value", v)

        h_poly_cm_vec = arg["h_poly_cm_vec"]
        evals_pos = arg["evals_pos_beta"]
        evals_neg = arg["evals_neg_beta"]
        evals_sq = arg["evals_sq_beta"]
        Cq = arg["q_commitment"]
        Cw = arg["kzg_arg_r_poly_at_zeta"]

        # > Round 1

        for i in range(len(h_poly_cm_vec)):
            tr.absorb(b"h_cm", h_poly_cm_vec[i])
        
        # > Round 2

        beta = tr.squeeze(Field, b"beta", 4)
        if self.debug > 0:
            print("V> beta = {}".format(beta))

        for i in range(k):
            tr.absorb(b"poly_at_beta", evals_pos[i])
            tr.absorb(b"poly_at_neg_beta", evals_neg[i])
            evals_sq.append(interp_and_eval_line(evals_pos[i], evals_neg[i], us[i], beta))
        tr.absorb(b"evals_sq", evals_sq[0])

        if self.debug > 1:
            print("V> evals_sq = {}".format(evals_sq))
        
        # 1st check: if h_n(beta^2) = v
        if not (evals_sq[-1] == v):
            return False
        
        # > Round 3

        gamma: Field = tr.squeeze(Field, b"gamma", 4)
        if self.debug > 0:
            print("V> gamma = {}".format(gamma))

        Ch = f_cm
        for i in range(0, k-1):
            Ch = Ch + h_poly_cm_vec[i].scalar_mul(gamma**(i+1))

        if self.debug > 1:
            print("V> Commitment of h(X): Ch={}".format(Ch))
        
        # Compute h(beta), h(-beta), h(beta^2)
        h_agg_poly_at_beta = sum([evals_pos[i]*(gamma**i) for i in range(k)])
        h_agg_poly_at_neg_beta = sum([evals_neg[i]*(gamma**i) for i in range(k)])
        h_agg_poly_at_beta_sq = sum([evals_sq[i]*(gamma**i) for i in range(k)])

        if self.debug > 1:
            print("V> h_agg_poly_at_beta={}".format(h_agg_poly_at_beta))
            print("V> h_agg_poly_at_neg_beta={}".format(h_agg_poly_at_neg_beta))
            print("V> h_agg_poly_at_beta_sq={}".format(h_agg_poly_at_beta_sq))

        # h(X) - h*(X) = q(X) * (X^2-beta^2)(X-beta^2)
        #
        # Receive Cq = Commit(c(X)) 
        tr.absorb(b"q_commitment", Cq)

        # > Round 4

        # Sample randomness
        zeta: Field = tr.squeeze(Field, b"zeta", 4)

        if self.debug > 0: print("V> zeta = {}".format(zeta))
        
        # Evaluate h*(zeta) by barycentric evaluation: 
        interp_poly_at_zeta = UniPolynomial.evaluate_from_evals(
                [h_agg_poly_at_beta, h_agg_poly_at_neg_beta, h_agg_poly_at_beta_sq],
                zeta, [beta, -beta, beta*beta])
        
        if self.debug > 1:
            print("V> interp_poly_at_zeta={}".format(interp_poly_at_zeta))
            interp_poly = UniPolynomial.interpolate(
                [h_agg_poly_at_beta, h_agg_poly_at_neg_beta, h_agg_poly_at_beta_sq], 
                [beta, -beta, beta*beta])
            assert interp_poly_at_zeta == interp_poly.evaluate(zeta)

        vanishing_poly_at_zeta = (zeta - beta) * (zeta + beta) * (zeta - beta*beta)

        # Compute Cr = Ch - [h*(zeta)] - (zeta^2-beta^2)(zeta-beta^2) * Cq
        Cr = Ch - self.kzg_pcs.commit(UniPolynomial([interp_poly_at_zeta])) - Cq.scalar_mul(vanishing_poly_at_zeta)

        if self.debug > 1:
            print("V> Cr={}".format(Cr))
            print("V> Cq={}".format(Cq))

        # Verify r_poly argument
        
        # 2nd check: if r(z)=0
        Cw_verified = self.kzg_pcs.verify_evaluation(Cr, zeta, Field.zero(), Cw)

        if self.debug > 0:
            if Cw_verified: print("V> check if r(z)=0 😀 ✅")
            else: print("V> check if r(z)=0 😢 ❌")

        if not Cw_verified:
            return False

        return True

def interp_and_eval_line(a, b, r, x):
    """
    Interpolate two points into a polynomial and evaluate it at X=r

        f(X) = [(-x, a), (x, b)] -> (a+b)/2 + ((a-b) / (2*x)) * X

        f(r) = (1-r) * (a+b)/2 + r * (a-b) / (2*x)
    Args:
        a (Field): The evaluation at -x
        b (Field): The evaluation at x
        r (Field): The point at which to evaluate the polynomial
        x (Field): The x-coordinate of the point

    Returns:
        int: The result of evaluating the polynomial at X=r
    """
    return ((1-r) * (a + b) / Field(2) + r * (a - b) / (Field(2) * x))

if __name__ == "__main__":
    a = Field(1)
    b = Field(2)
    r = Field(3)
    x = Field(4)
    # print(interp_and_eval_line(a, b, r, x))

    kzg_pcs = KZG10_PCS(G1, G2, Field, 20, debug=True)

    hyperkzg_pcs = HYPERKZG_PCS(kzg_pcs, debug=True)

    f = MLEPolynomial([Field(1), Field(3), Field(2), Field(1)], 2)
    f_evals = f.evals
    f_cm = kzg_pcs.commit(UniPolynomial(f_evals))

    tr = MerlinTranscript(b"test-hyperkzg-pcs")

    point = [Field(2), Field(3)]
    value = f.evaluate(point)
    print(f"value={value}")

    value, arg = hyperkzg_pcs.prove_eval(f_cm, f, 
            point, tr.fork(b"hyperkzg_pcs"))
    print(f"arg={arg}")

    verified = hyperkzg_pcs.verify_eval(f_cm, point, value, arg, tr.fork(b"hyperkzg_pcs"))
    assert verified
    print("✅ test_prove_verify() passed")
