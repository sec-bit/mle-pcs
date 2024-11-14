import unittest
from sage.all import *
import sys

sys.path.append('src')
sys.path.append('../src')

from circle import CFFT, F31, C31, FRI, eval_at_point_raw, twin_cosets, combine, standard_position_cosets, log_2, deep_quotient_reduce, deep_quotient_reduce_raw, g_30
from merlin.merlin_transcript import MerlinTranscript

def fold(lde, domain, chunk_size, fold_y=False):
    if fold_y:
        assert len(domain) == len(lde), f'len(domain) != len(lde), {len(domain)}, {len(lde)}'
    else:
        assert len(domain) == len(lde) * 2, f'len(domain) != len(lde) * 2, {len(domain)}, {len(lde) * 2}'
    res = []
    for j in range(len(lde) // chunk_size):
        for i in range(chunk_size // 2):
            left = lde[j * chunk_size + i]
            right = lde[(j + 1) * chunk_size - i - 1]
            t = domain[i][1 if fold_y else 0]
            # print('t:', t)
            f0 = (left + right) / F31(2)
            f1 = (left - right) / (F31(2) * t)
            assert f0 + f1 * t == left
            assert f0 - f1 * t == right
            res += [f0 + f1 * 3]
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
        folded = fold(lde, domain_lde, len(lde), fold_y=True)
        folded_folded = fold(folded, domain_lde, len(lde) // 2, fold_y=False)
        assert folded_folded[0] == folded_folded[1], f'folded_folded[0] != folded_folded[1], {folded_folded[0]}, {folded_folded[1]}'

    def test_fri_prove(self):
        evals = [1, 2, 3, 4]
        domain = standard_position_cosets[log_2(len(evals))]
        blowup_factor = 2
        lde = CFFT.extrapolate(evals, domain, blowup_factor)

        domain_lde = standard_position_cosets[log_2(len(evals) * blowup_factor)]
        # print('domain_lde:', domain_lde)
        folded = fold(lde, domain_lde, len(lde), fold_y=True)

        f0 = [lde[0]] + lde[3:5] + [lde[7]]
        f1 = lde[1:3] + lde[5:7]

        tcs = twin_cosets(2, 4)
        assert CFFT.ifft(CFFT.vec_2_poly(f0, tcs[0])) == CFFT.ifft(CFFT.vec_2_poly(f1, tcs[1]))

        transcript = MerlinTranscript(b'TEST')
        _fri_proof = FRI.prove(folded, blowup_factor, [x[0] for x in domain_lde[:len(folded)]], transcript, lambda x: None, 1)

    def test_deep_quotient_reduce(self):
        evals = [C31(1), C31(2), C31(3), C31(4)]
        domain = standard_position_cosets[log_2(len(evals))]
        alpha = 3
        zeta = g_30 ** 6
        p_at_zeta = eval_at_point_raw(evals, domain, zeta)

        reduced = deep_quotient_reduce(evals, domain, alpha, zeta, p_at_zeta)
        expected = deep_quotient_reduce_raw(evals, domain, alpha, zeta, p_at_zeta)
        assert reduced == expected, f'deep_quotient_reduce error, {reduced}, {expected}'

if __name__ == '__main__':
    unittest.main()
