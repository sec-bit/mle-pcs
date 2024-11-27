from utils import log_2, is_power_of_two

class MMCS:
    hash = None
    compress = None
    default_digest = None
    configured = False

    @classmethod
    def configure(cls, hash, compress, default_digest=0):
        def wrapper(f):
            def wrapped(x, debug=False):
                o = f(x)
                if debug: print(f"{f.__name__}({x}) = {o}")
                return o
            return wrapped
        cls.hash = wrapper(hash)
        cls.compress = wrapper(compress)
        cls.default_digest = default_digest
        cls.configured = True

    @classmethod
    def commit(cls, vecs, debug=False):
        assert cls.configured, "MMCS is not configured"
        for i in range(len(vecs)):
            if i is not 0:
                assert len(vecs[i - 1]) >= len(vecs[i]), f"len(vecs[{i}]) < len(vecs[{i+1}]), {len(vecs[i])}, {len(vecs[i+1])}"
            assert is_power_of_two(len(vecs[i])), f"len(vecs[{i}]) is not a power of two, {len(vecs[i])}"

        min_height = len(vecs[-1])

        # first layer
        layers = [[cls.hash(e) for e in vecs[0]]]

        for i in range(1, len(vecs)):
            layers.append([cls.compress((layers[i-1][j], layers[i-1][j+1]), debug) for j in range(0, len(layers[i-1]), 2)])
            layers[-1] = [cls.compress((layers[-1][j], cls.hash(vecs[i][j])), debug) for j in range(len(layers[-1]))]

        for i in range(log_2(min_height)):
            layers.append([cls.compress((layers[i-1][j], layers[i-1][j+1]), debug) for j in range(0, len(layers[i-1]), 2)])
            layers[-1] = [cls.compress((layers[-1][j], cls.default_digest), debug) for j in range(len(layers[-1]))]

        return {
            'layers': layers,
            'vecs': vecs
        }

    @classmethod
    def open(cls, index, prover_data, debug=False):
        assert cls.configured, "MMCS is not configured"
        layers = prover_data['layers']
        if debug: print(layers)
        vecs = prover_data['vecs']
        if debug: print(vecs)

        height = len(layers)
        openings = [vecs[i][index >> (32 - len(vecs[i]))] for i in range(height)]
        proof = [layers[i][(index >> (32 - len(layers[i]))) ^ 1] for i in range(height - 1)]
        root = layers[-1][0]
        if debug: print(openings, proof, root)
        return openings, proof, root

    @classmethod
    def verify(cls, index, openings, proof, root, debug=False):
        index >>= (32 - (1 << (len(openings) - 1)))
        expected = cls.hash(openings[0])
        index >>= 1
        for i in range(1, len(openings)):
            if index & 1:
                expected = cls.compress((proof[i-1], expected), debug)
            else:
                expected = cls.compress((expected, proof[i-1]), debug)
            expected = cls.compress((expected, cls.hash(openings[i])), debug)
            index >>= 1
        assert expected == root, f"expected {expected}, root {root}"
