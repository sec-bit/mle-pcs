# Adapt transcript of [project](https://github.com/NOOMA-42/pylookup)

from merlin.strobe import Strobe128

MERLIN_PROTOCOL_LABEL = b"Merlin v1.0"


class MerlinTranscript:
    def __init__(self, label: bytes) -> None:
        self.strobe: Strobe128 = Strobe128.new(MERLIN_PROTOCOL_LABEL)
        self.append_message(b"dom-sep", label)

    def append_message(self, label: bytes, message: bytes) -> None:
        data_len = len(message).to_bytes(4, "little")
        self.strobe.meta_ad(label, False)
        self.strobe.meta_ad(data_len, True)
        self.strobe.ad(message, False)

    def append_u64(self, label: bytes, x: int) -> None:
        self.append_message(label, x.to_bytes(8, "little"))

    def challenge_bytes(self, label: bytes, length: int) -> bytes:
        data_len = length.to_bytes(4, "little")
        self.strobe.meta_ad(label, False)
        self.strobe.meta_ad(data_len, True)
        return self.strobe.prf(length, False)

    def fork(self, label: bytes) -> 'MerlinTranscript':
        new_transcript = MerlinTranscript(label)
        new_transcript.strobe = Strobe128(self.strobe.state.copy(), self.strobe.pos, self.strobe.pos_begin, self.strobe.cur_flags)
        return new_transcript

    def absorb(self, label: bytes, obj) -> None:
        if obj is None:
            self.append_message(label, b"padding")
        else:
            self.append_message(label, str(obj).encode())

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

