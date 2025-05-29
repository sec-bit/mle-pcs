from unittest import TestCase, main
from sys import path

path.append('../src')
path.append('src')

from fri import FRIBigField, FRIBFCommitment, FRIBFProof, bit_reverse_inplace, eval_over_fft_field, batch_invert_inplace
from curve import Fr
from unipoly2 import UniPolynomialWithFft
from merlin.merlin_transcript import MerlinTranscript

class TestFRIBigField(TestCase):
    def setUp(self):
        self.log_n = 10
        self.log_blowup = 3
        FRIBigField.set_field_type(Fr)
        FRIBigField.precompute_twiddles(self.log_n + self.log_blowup)
        FRIBigField.query_num = 67

    def test_setup(self):
        for i in range(1, self.log_n + self.log_blowup):
            twiddles_cp = FRIBigField.twiddles[i].copy()
            bit_reverse_inplace(twiddles_cp)
            assert twiddles_cp == FRIBigField.twiddles_reversed[i]
            batch_invert_inplace(twiddles_cp, Fr)
            assert twiddles_cp == FRIBigField.twiddles_reversed_inv[i]
            for j in range(1 << i):
                assert FRIBigField.twiddles_reversed[i][j] * FRIBigField.twiddles_reversed_inv[i][j] == Fr.one()

    def test_eval_from_fft_field(self):
        evals = [Fr.random() for _ in range(1 << self.log_n)]
        coeffs = UniPolynomialWithFft.ifft(evals, self.log_n, Fr.nth_root_of_unity(1 << self.log_n))
        assert len(coeffs) == 1 << self.log_n
        coeffs_padded = coeffs + [Fr.zero()] * ((1 << (self.log_n + self.log_blowup)) - (1 << self.log_n))
        assert len(coeffs_padded) == 1 << (self.log_n + self.log_blowup)
        expected_code = UniPolynomialWithFft.fft(coeffs_padded, self.log_n + self.log_blowup, Fr.nth_root_of_unity(1 << (self.log_n + self.log_blowup)))

        bit_reverse_inplace(coeffs)
        code = eval_over_fft_field(coeffs, self.log_blowup, FRIBigField.twiddles, Fr, debug=1)
        assert code == expected_code

    def test_commit(self):
        evals = [Fr.random() for _ in range(1 << self.log_n)]
        commitment: FRIBFCommitment = FRIBigField.commit(evals, self.log_blowup, debug=1)
        
        assert commitment.data == evals
        assert commitment.log_n == self.log_n
        assert commitment.log_blowup == self.log_blowup

        coeffs = UniPolynomialWithFft.ifft(evals, self.log_n, Fr.nth_root_of_unity(1 << self.log_n))
        assert len(coeffs) == 1 << self.log_n
        coeffs_padded = coeffs + [Fr.zero()] * ((1 << (self.log_n + self.log_blowup)) - (1 << self.log_n))
        assert len(coeffs_padded) == 1 << (self.log_n + self.log_blowup)
        expected_code = UniPolynomialWithFft.fft(coeffs_padded, self.log_n + self.log_blowup, Fr.nth_root_of_unity(1 << (self.log_n + self.log_blowup)))
        bit_reverse_inplace(expected_code)
        assert commitment.code == expected_code

        assert commitment.tree.root == commitment.root

    def test_open(self):
        evals = [Fr.random() for _ in range(1 << self.log_n)]
        point = Fr.random()
        value = UniPolynomialWithFft.evaluate_from_evals(evals, point, FRIBigField.twiddles[self.log_n])
        coeffs = UniPolynomialWithFft.ifft(evals, self.log_n, Fr.nth_root_of_unity(1 << self.log_n))
        assert UniPolynomialWithFft.evaluate_at_point(coeffs, point) == value
        commitment: FRIBFCommitment = FRIBigField.commit(evals, self.log_blowup, debug=1)
        transcript = MerlinTranscript(b"test")
        transcript.append_message(b"commitment", commitment.root.encode())
        FRIBigField.open(commitment, point, value, transcript.fork(b"prove"), debug=1)

    def test_verify(self):
        evals = [Fr.random() for _ in range(1 << self.log_n)]
        point = Fr.random()
        value = UniPolynomialWithFft.evaluate_from_evals(evals, point, FRIBigField.twiddles[self.log_n])
        coeffs = UniPolynomialWithFft.ifft(evals, self.log_n, Fr.nth_root_of_unity(1 << self.log_n))
        assert UniPolynomialWithFft.evaluate_at_point(coeffs, point) == value
        commitment: FRIBFCommitment = FRIBigField.commit(evals, self.log_blowup, debug=1)

        transcript = MerlinTranscript(b"test")
        transcript.append_message(b"commitment", commitment.root.encode())

        proof: FRIBFProof = FRIBigField.open(commitment, point, value, transcript.fork(b"prove"), debug=2)

        commitment = FRIBFCommitment(None, commitment.log_n, commitment.log_blowup, None, None, commitment.root)
        FRIBigField.verify(commitment, point, value, proof, transcript.fork(b"prove"), debug=2)

    def test_zero_evals(self):
        evals = [Fr.zero() for _ in range(1 << self.log_n)]
        point = Fr.random()
        value = UniPolynomialWithFft.evaluate_from_evals(evals, point, FRIBigField.twiddles[self.log_n])
        coeffs = UniPolynomialWithFft.ifft(evals, self.log_n, Fr.nth_root_of_unity(1 << self.log_n))
        assert UniPolynomialWithFft.evaluate_at_point(coeffs, point) == value
        commitment: FRIBFCommitment = FRIBigField.commit(evals, self.log_blowup, debug=1)

        transcript = MerlinTranscript(b"test")
        transcript.append_message(b"commitment", commitment.root.encode())

        proof: FRIBFProof = FRIBigField.open(commitment, point, value, transcript.fork(b"prove"), debug=1)

        commitment = FRIBFCommitment(None, commitment.log_n, commitment.log_blowup, None, None, commitment.root)
        FRIBigField.verify(commitment, point, value, proof, transcript.fork(b"prove"), debug=1)

    def test_zero_length(self):
        try:
            FRIBigField.commit([], self.log_blowup, debug=1)
            assert False, "Should raise an error"
        except Exception as e:
            assert str(e) == "Length of evals should be greater than 1", f"e={e}"

    def test_zero_log_blowup(self):
        try:
            FRIBigField.commit([Fr.random() for _ in range(1 << self.log_n)], 0, debug=1)
            assert False, "Should raise an error"
        except Exception as e:
            assert str(e) == "log_blowup should be greater than 0", f"e={e}"

    def test_zero_point(self):
        evals = [Fr.random() for _ in range(1 << self.log_n)]
        point = Fr.zero()
        value = UniPolynomialWithFft.evaluate_from_evals(evals, point, FRIBigField.twiddles[self.log_n])
        coeffs = UniPolynomialWithFft.ifft(evals, self.log_n, Fr.nth_root_of_unity(1 << self.log_n))
        assert UniPolynomialWithFft.evaluate_at_point(coeffs, point) == value
        commitment: FRIBFCommitment = FRIBigField.commit(evals, self.log_blowup, debug=1)
        transcript = MerlinTranscript(b"test")
        transcript.append_message(b"commitment", commitment.root.encode())
        FRIBigField.open(commitment, point, value, transcript.fork(b"prove"), debug=1)

    def test_kaput_commitment(self):
        evals = [Fr.random() for _ in range(1 << self.log_n)]
        point = Fr.random()
        value = UniPolynomialWithFft.evaluate_from_evals(evals, point, FRIBigField.twiddles[self.log_n])
        coeffs = UniPolynomialWithFft.ifft(evals, self.log_n, Fr.nth_root_of_unity(1 << self.log_n))
        assert UniPolynomialWithFft.evaluate_at_point(coeffs, point) == value
        commitment: FRIBFCommitment = FRIBigField.commit(evals, self.log_blowup, debug=1)
        commitment = FRIBFCommitment(None, commitment.log_n, commitment.log_blowup, None, None, commitment.root)
        transcript = MerlinTranscript(b"test")
        transcript.append_message(b"commitment", commitment.root.encode())
        try:
            FRIBigField.open(commitment, point, value, transcript.fork(b"prove"), debug=1)
            assert False, "Should raise an error"
        except Exception as e:
            assert str(e) == "commitment should contain data", f"e={e}"

    def test_kaput_proof(self):
        evals = [Fr.random() for _ in range(1 << self.log_n)]
        point = Fr.random()
        value = UniPolynomialWithFft.evaluate_from_evals(evals, point, FRIBigField.twiddles[self.log_n])
        coeffs = UniPolynomialWithFft.ifft(evals, self.log_n, Fr.nth_root_of_unity(1 << self.log_n))
        assert UniPolynomialWithFft.evaluate_at_point(coeffs, point) == value
        commitment: FRIBFCommitment = FRIBigField.commit(evals, self.log_blowup, debug=1)

        transcript = MerlinTranscript(b"test")
        transcript.append_message(b"commitment", commitment.root.encode())

        proof: FRIBFProof = FRIBigField.open(commitment, point, value, transcript.fork(b"prove"), debug=2)

        commitment = FRIBFCommitment(None, commitment.log_n, commitment.log_blowup, None, None, commitment.root)
        proof = FRIBFProof(None, None, None, None)
        try:
            FRIBigField.verify(commitment, point, value, proof, transcript.fork(b"prove"), debug=2)
            assert False, "Should raise an error"
        except Exception as e:
            assert str(e) == "proof should contain intermediate_commitments", f"e={e}"


if __name__ == "__main__":
    main()
