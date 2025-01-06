#!/usr/bin/env python3

# WARNING: This implementation may contain bugs and has not been audited. 
# It is only for research purposes. DO NOT use it in production.

from curve import Fr as Field, ec_mul,G1Point as G1
from merlin.merlin_transcript import MerlinTranscript

# WARNING:
#   1. For demonstration, we deliberately use an insecure random number
#      generator, random.Random. To generate secure randomness, use
#      the standard library `secrets` instead.
#        
#      See more here: https://docs.python.org/3/library/secrets.html
#
#   2. Challenges are only 1 byte long for simplicity, which is not secure.

import random

class PedersenCommitment:
    pp: tuple[list[G1], G1]

    def __init__(self, pp: tuple[list[G1], G1]):
        vec_G, H = pp
        if not isinstance(vec_G, list):
            raise ValueError("pp.G must be a list of G1Point")
        if not isinstance(H, G1):
            raise ValueError("pp.H must be a G1Point")
        self.pp = pp

    # NOTE: Insecure setup, please DON'T use it in production.
    @classmethod
    def setup(cls, n: int) -> "PedersenCommitment":
        vec_G = []
        rnd_gen = random.Random("vector-pedersen-setup")
        for _ in range(n):
            s = Field.rand(rnd_gen)
            vec_G.append(ec_mul(G1.ec_gen(), s))
        s = Field.rand(rnd_gen)
        H = ec_mul(G1.ec_gen(), s)
        return cls((vec_G, H))

    def commit(self, vs: list[Field], rng: random.Random) -> G1:
        assert len(self.pp[0]) > len(vs)
        assert isinstance(rng, random.Random), f"rng must be a random.Random, but got {type(rng)}"
        cm = G1.zero()
        r = Field.rand(rng)
        for i in range(len(vs)):
            cm += ec_mul(self.pp[0][i], vs[i])
        return cm + ec_mul(self.pp[1], r)
    
    def commit_with_blinder(self, vs: list[Field], r: Field) -> G1:
        assert len(self.pp[0]) > len(vs)
        cm = G1.zero()
        for i in range(len(vs)):
            cm += ec_mul(self.pp[0][i], vs[i])
        return cm + ec_mul(self.pp[1], r)

    def open(self, cm: G1, vs: list[Field], r: Field) -> bool:
        cm2 = self.commit_with_blinder(vs, r)
        return cm == cm2

    def commit_without_blinder(self, vs: list[Field]) -> G1:
        assert len(self.pp[0]) > len(vs)
        cm = G1.zero()
        for i in range(len(vs)):
            cm += ec_mul(self.pp[0][i], vs[i])
        return cm

    def open_without_blinder(self, cm: G1, vs: list[Field]) -> bool:
        cm2 = self.commit_without_blinder(vs)
        return cm == cm2
    
    @classmethod
    def commit_with_pp(cls, new_pp: list[G1], vs: list[Field]) -> G1:
        assert len(new_pp) >= len(vs), f"len(new_pp): {len(new_pp)} < len(vs): {len(vs)}"
        cm = G1.zero()
        for i in range(len(vs)):
            cm += ec_mul(new_pp[i], vs[i])
        return cm

    @classmethod
    def open_with_pp(cls, new_pp: list[G1], cm: G1, vs: list[Field]) -> bool:
        cm2 = cls.commit_with_pp(new_pp, vs)
        return cm == cm2

IPA_Argument = tuple[int, list[tuple[G1,G1]], G1, Field, Field]

class BULLETPROOF_IPA_PCS:

    def __init__(self, pcs: PedersenCommitment):
        """
        Args:
            pcs: the PedersenCommitment instance to use for the proof
        """
        self.pcs = pcs
        self.rnd_gen = random.Random("ipa-pcs")

    def commit(self, vec_c: list[Field]) -> tuple[G1, Field]:
        """
        Commit to a vector of coefficients.
        """
        blinder = Field.rand()
        return self.pcs.commit_with_blinder(vec_c, blinder), blinder
    
    def inner_product_prove(self,
            a_cm: G1, vec_a: list[Field], rho_a: Field, vec_b: list[Field], c: Field, 
            tr: MerlinTranscript,
            debug=False) -> IPA_Argument:
        """
        Prove the inner product of two vectors.

            <(a0, a1,...,a_{n-1}), (b0, b1,...,b_{n-1})> = c
        
        Args:
            a_cm: the commitment to the vector a
            vec_b: the vector b
            c: the challenge scalar
            vec_a: the vector a
            rho_a: the blinding factor for the commitment to vec_a
            tr: the Merlin transcript to use for the proof
            debug: whether to print debug information
        Returns:
            an IPA_Argument tuple
        """
        n = len(vec_a)
        assert len(self.pcs.pp[0]) >= 2 * n + 1, f"EROR: len(pcs.pp) = {len(self.pcs.pp[0])}, while len(vec_a) = {len(vec_a)}"
        assert len(vec_b) == n, f"EROR: len(vec_b) = {len(vec_b)}, while len(vec_a) = {len(vec_a)}"

        if debug:
            print(f"prove> n: {n}")
        
        rng = random.Random(b"schnorr-1folding-commit")

        G = self.pcs.pp[0][:n]
        U = self.pcs.pp[0][-1]
        H = self.pcs.pp[1]

        tr.append_message(b"a_cm", str(a_cm).encode())
        tr.append_message(b"vec_b", str(vec_b).encode())
        tr.append_message(b"c", str(c).encode())

        # Round 1:   gamma <~ Fr 

        # WARN: challenge should be 32 bytes long, here we use 1 byte for debugging
        gamma = Field.from_bytes(tr.challenge_bytes(b"gamma", 1))

        Ugamma = ec_mul(U, gamma)
        P = a_cm + ec_mul(Ugamma, c)
        PLR = []
        rho = rho_a

        # Round 2:   PL, PR, ->
        round = 0
        half = n // 2

        while half > 0:
            if debug:
                print(f"prove> round: {round}")
            round += 1
            G1 = G[:half]
            G2 = G[half:]
            as1 = vec_a[:half]
            as2 = vec_a[half:]
            bs1 = vec_b[:half]
            bs2 = vec_b[half:]
            rho_L, rho_R = Field.rands(rng, 2)

            sum_as2_bs1 = sum([as2[i] * bs1[i] for i in range(half)])
            sum_as1_bs2 = sum([as1[i] * bs2[i] for i in range(half)])
            PL = self.pcs.commit_with_pp(G1, as2) + ec_mul(Ugamma, sum_as2_bs1) + ec_mul(H, rho_L)
            PR = self.pcs.commit_with_pp(G2, as1) + ec_mul(Ugamma, sum_as1_bs2) + ec_mul(H, rho_R)
            PLR.insert(0, (PL, PR))

            tr.append_message(b"PL", str(PL).encode())
            tr.append_message(b"PR", str(PR).encode())

            # Round 3:   mu <~ Fr
            mu = Field.from_bytes(tr.challenge_bytes(b"mu", 1))
            if debug:
                print(f"prove> mu: {mu}")
            vec_a = [as1[i] + as2[i] * mu for i in range(half)]
            vec_b = [bs1[i] + bs2[i] * mu.inv() for i in range(half)]
            rho += rho_L * mu + rho_R * mu.inv()

            G = [G1[i] + ec_mul(G2[i], mu.inv()) for i in range(half)]

            # Debug
            if debug:
                sum_a_b = sum([vec_a[i] * vec_b[i] for i in range(half)])
                lhs = self.pcs.commit_with_pp(G, vec_a) + ec_mul(Ugamma, sum_a_b) + ec_mul(H, rho)
                P += ec_mul(PL, mu) + ec_mul(PR, mu.inv())
                if lhs == P:
                    print(f"prove> [vec_a]_(G) + [<vec_a, vec_b>]_(H) == P + mu*PL + mu^(-1)*PR ok ")
                else:
                    print(f"prove> [vec_a]_(G) + [<vec_a, vec_b>]_(H) == P + mu*PL + mu^(-1)*PR failed ")
            half = half // 2

        assert len(vec_a) == len(vec_b) == len(G) == 1, "EROR: len(vec_a) and len(vec_b) should be 1"
        a0 = vec_a[0]
        b0 = vec_b[0]
        G0 = G[0]

        # Round 4:  R -> 
        G_new = G0 + ec_mul(Ugamma, b0)
        r, rho_r = Field.rands(rng, 2)
        R = ec_mul(G_new, r) + ec_mul(H, rho_r)
        tr.append_message(b"R", str(R).encode())

        # Round 5:  zeta <~ Fr
        zeta = Field.from_bytes(tr.challenge_bytes(b"zeta", 1))
        if debug:
            print(f"prove> zeta: {zeta}")

        # Round 6:  z ->  
        z = r + zeta * a0
        z_r = rho_r + zeta * rho
    
        # Debug
        if debug:
            lhs = self.pcs.commit_with_pp([G_new], [z])
            rhs = P + ec_mul(G_new, r) + ec_mul(P, zeta)
            if lhs == rhs:
                print(f"prove> [z]_(G_new) == pcs.commit_with_pp(G, vec_z) ok ")
            else:
                print(f"prove> Z == pcs.commit_with_pp(G, vec_z) failed ")

        return (n, PLR, R, z, z_r)

    def inner_product_verify(self, a_cm: G1, vec_b: list[Field], c: Field, 
                             arg: IPA_Argument, tr: MerlinTranscript, debug=False) -> bool:
        """
        Verify an inner product argument.

            <(a0, a1,...,a_{n-1}), (b0, b1,...,b_{n-1})> = c

        Args:
            a_cm: the commitment to the vector a
            vec_b: the vector b
            c: the challenge scalar
            arg: the IPA_UNI_Argument (proof transcript)
            tr: the Merlin transcript to use for the proof
            debug: whether to print debug information
        """

        n, PLR, R, z, z_r = arg

        tr.append_message(b"a_cm", str(a_cm).encode())
        tr.append_message(b"vec_b", str(vec_b).encode())
        tr.append_message(b"c", str(c).encode())

        G = self.pcs.pp[0][:n]
        U = self.pcs.pp[0][-1]
        H = self.pcs.pp[1]

        # Round 1:   gamma <~ Fr 

        # WARN: challenge should be 32 bytes long, here we use 1 byte for debugging
        gamma = Field.from_bytes(tr.challenge_bytes(b"gamma", 1))
        if debug:
            print(f"verify> gamma: {gamma}")

        Ugamma = ec_mul(U, gamma)
        P = a_cm + ec_mul(Ugamma, c)

        # Round 2:   PL, PR, ->
        round = 0
        half = n // 2
        while half > 0:
            PL, PR = PLR.pop()

            tr.append_message(b"PL", str(PL).encode())
            tr.append_message(b"PR", str(PR).encode())

            # Round 3:   mu <~ Fr
            mu = Field.from_bytes(tr.challenge_bytes(b"mu", 1))
            if debug:
                print(f"verify> mu: {mu}")

            G1 = G[:half]
            G2 = G[half:]
            bs1 = vec_b[:half]
            bs2 = vec_b[half:]
            G = [G1[i] + ec_mul(G2[i], mu.inv()) for i in range(half)]
            vec_b = [bs1[i] + mu.inv() * bs2[i] for i in range(half)]
            
            # print(f"verify> G[{round}]: {G}")

            # Z_1 ?= Z + x * AL + x^{-1} * AR
        
            P += ec_mul(PL, mu) + ec_mul(PR, mu.inv())
            half = half // 2
            round += 1
        
        assert len(G) == len(vec_b) == 1, "EROR: len(vec_a) and len(vec_b) should be 1"
        G0 = G[0]
        b0 = vec_b[0]

        # Round 4:  R -> 
        tr.append_message(b"R", str(R).encode())

        # Round 5:  zeta <~ Fr
        zeta = Field.from_bytes(tr.challenge_bytes(b"zeta", 1))
        if debug:
            print(f"verify> zeta: {zeta}")

        # Round 6:  z ->  
        
        G_new = G0 + ec_mul(Ugamma, b0)
        rhs = R + ec_mul(P, zeta)
        lhs = self.pcs.commit_with_pp([G_new, H], [z, z_r])

        return lhs == rhs

    def univariate_poly_eval_prove(self, 
                f_cm: G1, x: Field, y: Field, coeffs: list[Field], rho: Field, 
                tr: MerlinTranscript, debug=False) -> IPA_Argument:
        """
        Prove that a polynomial f(x) = y.

            f(X) = c0 + c1 * X + c2 * X^2 + ... + cn * X^n

        Args:
            f_cm: the commitment to the polynomial f(X)
            x: the challenge point
            y: the evaluation of f(x)
            vec_c: the coeffcient vector of the polynomial f(X)
            rho_c: the blinding factor for the commitment to vec_c
            tr: the Merlin transcript to use for the proof
            debug: whether to print debug information
        Returns:
            an IPA_PCS_Argument tuple
        """
        n = len(coeffs)
        vec_x = [x**i for i in range(n)]
        arg = self.inner_product_prove(f_cm, coeffs, rho, vec_x, y, tr, debug)
        return arg

    def univariate_poly_eval_verify(self, f_cm: G1, x: Field, y: Field, 
                arg: IPA_Argument, 
                tr: MerlinTranscript, 
                debug=False) -> bool:
        """
        Verify an evaluation argument for a polynomial f, st. f(x) = y.

            f(X) = c0 + c1 * X + c2 * X^2 + ... + cn * X^n

        Args:
            f_cm: the commitment to the polynomial f(X)
            x: the challenge point
            y: the evaluation of f(x)
            arg: the IPA_PCS_Argument (proof transcript)
            tr: the Merlin transcript to use for the proof
            debug: whether to print debug information
        """
        n = arg[0]
        vec_x = [x**i for i in range(n)]
        return self.inner_product_verify(f_cm, vec_x, y, arg, tr, debug)

def test_ipa_pcs():

    # initialize the PedersenCommitment and the IPA_PCS
    pcs = PedersenCommitment.setup(20)
    ipa_pcs = BULLETPROOF_IPA_PCS(pcs)
    tr = MerlinTranscript(b"ipa-pcs")

    # A simple instance f(x) = y
    coeffs = [Field(2), Field(3), Field(4), Field(5), Field(6), Field(7), Field(8), Field(9)]
    x = Field(4)
    vec_x = [x**i for i in range(len(coeffs))]
    y = sum([coeffs[i] * vec_x[i] for i in range(len(coeffs))])

    # commit to the polynomial
    rho = Field.rand()
    f_cm = pcs.commit_with_blinder(coeffs, rho)

    # fork the transcript for both prover and verifier
    tr_prover = tr.fork(b"xx")
    tr_verifier = tr.fork(b"xx")

    # prover proves f(x) = y and sends an argument to the verifier
    arg = ipa_pcs.univariate_poly_eval_prove(f_cm, x, y, coeffs, rho, tr_prover, debug=True)
    print(f"arg: {arg}")

    # verifier verifies the argument
    verified = ipa_pcs.univariate_poly_eval_verify(f_cm, x, y, arg, tr_verifier, debug=True)
    assert verified, "univariate polynomial evaluation verification failed"
    print(f"verified: {verified}")

if __name__ == "__main__":
    test_ipa_pcs()