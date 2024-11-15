import unittest
from sage.all import *
import sys

sys.path.append('src')
sys.path.append('../src')

from circle import CirclePCS, CFFT, F31, FRI, evaluate_at_point, eval_at_point_raw, extract_lambda, twin_cosets, combine, standard_position_cosets, log_2, deep_quotient_reduce, deep_quotient_reduce_raw, g_30, group_mul, group_inv
from merlin.merlin_transcript import MerlinTranscript

def fold(lde, domain, alpha=3, fold_y=False):
    if fold_y:
        assert len(domain) == len(lde), f'len(domain) != len(lde), {len(domain)}, {len(lde)}'
    else:
        assert len(domain) == len(lde) * 2, f'len(domain) != len(lde) * 2, {len(domain)}, {len(lde) * 2}'
    res = []
    for i in range(len(lde) // 2):
        left = lde[i]
        right = lde[-i - 1]
        t = domain[i][1 if fold_y else 0]
        # print('t:', t)
        f0 = (left + right) / F31(2)
        f1 = (left - right) / (F31(2) * t)
        assert f0 + f1 * t == left
        assert f0 - f1 * t == right
        res += [f0 + f1 * alpha]
    return res

class TestCircle(unittest.TestCase):
    def test_twin_cosets(self):
        # test twin_cosets
        tcs = twin_cosets(2, 4)
        for tc in tcs:
            for t in tc:
                assert t in standard_position_cosets[log_2(8)]
        assert combine(tcs) == standard_position_cosets[log_2(8)], f'combine error, {combine(tcs)}, {standard_position_cosets[log_2(8)]}'

    def test_extrapolate(self):
        evals = [1, 2, 3, 4]
        domain = standard_position_cosets[log_2(len(evals))]
        blowup_factor = 2
        lde = CFFT.extrapolate(evals, domain, blowup_factor)

        assert len(lde) == len(evals) * blowup_factor, f'len(lde) != len(evals) * blowup_factor, {len(lde)}, {len(evals) * blowup_factor}'
        for i, p in enumerate(standard_position_cosets[log_2(len(evals) * blowup_factor)]):
            assert eval_at_point_raw(evals, domain, p) == lde[i], f'evaluate_at_point error, {eval_at_point_raw(evals, domain, p)}, {lde[i]}'

    def test_fold(self):
        evals = [1, 2, 3, 4]
        domain = standard_position_cosets[log_2(len(evals))]
        blowup_factor = 2
        lde = CFFT.extrapolate(evals, domain, blowup_factor)

        domain_lde = standard_position_cosets[log_2(len(evals) * blowup_factor)]
        # print('domain_lde:', domain_lde)
        folded = fold(lde, domain_lde, 3, fold_y=True)
        folded_folded = fold(folded, domain_lde, 3, fold_y=False)
        assert folded_folded[0] == folded_folded[1], f'folded_folded[0] != folded_folded[1], {folded_folded[0]}, {folded_folded[1]}'

    def test_fri_prove(self):
        evals = [1, 2, 3, 4]
        domain = standard_position_cosets[log_2(len(evals))]
        blowup_factor = 2
        lde = CFFT.extrapolate(evals, domain, blowup_factor)

        domain_lde = standard_position_cosets[log_2(len(evals) * blowup_factor)]
        # print('domain_lde:', domain_lde)
        folded = fold(lde, domain_lde, 3, fold_y=True)

        f0 = [lde[0]] + lde[3:5] + [lde[7]]
        f1 = lde[1:3] + lde[5:7]

        tcs = twin_cosets(2, 4)
        assert CFFT.ifft(CFFT.vec_2_poly(f0, tcs[0])) == CFFT.ifft(CFFT.vec_2_poly(f1, tcs[1]))

        transcript = MerlinTranscript(b'TEST')
        FRI.prove(folded, blowup_factor, [x[0] for x in domain_lde[:len(folded)]], transcript, lambda x: None, 1)

    # def test_eval_at_point(self):
    #     evals = [F31(1), F31(2), F31(3), F31(4)]
    #     domain = standard_position_cosets[log_2(len(evals))]
    #     p = evaluate_at_point(evals, domain, g_30 ** 3)
    #     expected = eval_at_point_raw(evals, domain, g_30 ** 3)
    #     assert p == expected, f'evaluate_at_point error, {p}, {expected}'

    def test_deep_quotient_reduce(self):
        evals = [F31(1), F31(2), F31(3), F31(4)]
        domain = standard_position_cosets[log_2(len(evals))]
        alpha = 3
        zeta = g_30 ** 3
        p_at_zeta = eval_at_point_raw(evals, domain, zeta)

        blowup_factor = 2
        lde = CFFT.extrapolate(evals, domain, blowup_factor)
        domain_lde = standard_position_cosets[log_2(len(evals) * blowup_factor)]

        reduced = deep_quotient_reduce(lde, domain_lde, alpha, zeta, p_at_zeta)
        expected = deep_quotient_reduce_raw(lde, domain_lde, alpha, zeta, p_at_zeta)
        assert reduced == expected, f'deep_quotient_reduce error, {reduced}, {expected}'

        coeffs = CFFT.ifft(CFFT.vec_2_poly(reduced, domain_lde))
        for i, c in enumerate(coeffs):
            if i % 2 == 1 and i != 1:
                assert c == F31(0), f'coeffs[{i}] != 0, coeffs: {coeffs}'

    def test_extract_lambda(self):
        evals = [F31(1), F31(2), F31(3), F31(4)]
        lde = CFFT.extrapolate(evals, standard_position_cosets[2], 2)
        domain = standard_position_cosets[3]

        zeta = g_30 ** 3
        p_at_zeta = eval_at_point_raw(evals, standard_position_cosets[2], zeta)

        diff = [group_mul(group_inv(zeta), x) for x in domain]

        v_p = lambda x, y: (1 - x, -y)
        v_p_diff = [v_p(x, y) for x, y in diff]

        v_p_num = [x - y * 5 for x, y in v_p_diff]
        v_p_den = [x*x + y*y for x, y in v_p_diff]

        q_f = lambda f, fp, vp_num, vp_den: (f - fp) * vp_num / vp_den
        q = [q_f(eval, p_at_zeta, num, den) for eval, num, den in zip(lde, v_p_num, v_p_den)]

        new_lde, _ = extract_lambda(q, 1)

        q_interpolated = CFFT.ifft(CFFT.vec_2_poly(new_lde, standard_position_cosets[3]))
        for i, c in enumerate(q_interpolated):
            if i % 2 == 1:
                assert c == F31(0), f'coeffs[{i}] != 0, coeffs: {q_interpolated}'

    def test_circle_pcs(self):
        from random import randint
        evals = [F31(randint(0, 31)) for _ in range(4)]
        domain = CirclePCS.natural_domain_for_degree(len(evals))
        log_blowup = 1

        commitment, lde = CirclePCS.commit(evals, domain, 1 << log_blowup)

        transcript = MerlinTranscript(b'circle pcs')
        transcript.append_message(b'commitment', bytes(str(commitment.root), 'ascii'))

        query_num = 1

        domain = CirclePCS.natural_domain_for_degree(len(lde))
        point = CirclePCS.G5[5]
        proof = CirclePCS.open(lde, commitment, point, log_blowup, transcript, query_num, True)

        transcript = MerlinTranscript(b'circle pcs')
        transcript.append_message(b'commitment', bytes(str(commitment.root), 'ascii'))
        CirclePCS.verify(commitment.root, domain, log_blowup, point, eval_at_point_raw(evals, CirclePCS.natural_domain_for_degree(len(evals)), point), proof, transcript, True)

if __name__ == '__main__':
    unittest.main()
