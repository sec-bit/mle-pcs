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
