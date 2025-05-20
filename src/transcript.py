# from merkle import MerkleTree
from queue import Queue
from textwrap import wrap
from hashlib import sha256

def queue_from_vec(vec):
  queue = Queue(len(vec))
  for e in vec:
    queue.put(e)
  return queue

class Transcript:
    def __init__(self):
        self.msg = []
        self.queue = Queue()
        self.hash = None

    def write_field_element(self, element):
        self.msg.append(element)

    def write_field_elements(self, elements):
        self.msg += elements

    def squeeze_byte_challenge(self):
        assert len(self.msg) > 0 or self.hash != None
        if self.queue.empty():
            if len(self.msg) == 0:
                self.msg = self.hash
            self.hash = sha256(str(self.msg).encode()).digest()
            self.queue = queue_from_vec(self.hash)
            self.finalize()
        return self.queue.get()

    def finalize(self):
        self.msg = []


class MerlinTranscript:
    def __init__(self, label: bytes) -> None:
        self.state: int = 0
        self.absorb(b"init", label)

    def absorb_seed(self, additional_seed: int) -> None:
        """Absorb an additional seed to alter the internal state."""
        self.state ^= additional_seed  # XOR to combine seeds

    def generate_random_int(self, min_value: int, max_value: int) -> int:
        """Generate a deterministic random integer within a given range."""
        self.state = (self.state * 6364136223846793005 + 1) & ((1 << 64) - 1)  # Linear congruential generator
        return min_value + (self.state % (max_value - min_value + 1))

    def absorb(self, label: bytes, obj) -> None:
        """Absorb an object by encoding it and altering the internal state."""
        
        for byte in label:
            self.state ^= byte

        encoded_obj = str(obj).encode()  # Convert the object to a string and encode it to bytes
        for byte in encoded_obj:
            self.state ^= byte  # XOR each byte with the current state

    def challenge_bytes(self, label: bytes, length: int) -> bytes:
        """Generate a new random bytes whose length is `n`."""
        for byte in label:
            self.state ^= byte
        
        random_bytes = bytearray()
        for _ in range(length):
            random_byte = self.generate_random_int(0, 255)
            random_bytes.append(random_byte)
        return bytes(random_bytes)

    def fork(self, label: bytes) -> 'MerlinTranscript':
        new_transcript = MerlinTranscript(label)
        new_transcript.state = self.state
        return new_transcript

    def squeeze(self, _class, label: bytes, length: int) -> bytes:
        """
        Squeeze a value from the transcript.

        Args:
            _class: The class of the value to squeeze.
            label: The label of the value to squeeze.
            length: The length of the value to squeeze.

        Returns:
            The value squeezed from the transcript.
        """
        return _class.from_bytes(self.challenge_bytes(label, length))

if __name__ == "__main__":
    tr = MerlinTranscript(b"test")
    print(tr.challenge_bytes(b"test", 4))
    print(tr.challenge_bytes(b"test", 4))
    tr.absorb(b"test", [1,2])
    print(tr.squeeze(int, b"test", 4))
    tr.absorb(b"test2", [4,4])
    print(tr.squeeze(int, b"test2", 12))
