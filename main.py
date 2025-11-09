CONTEXT_JOKER = b"\x00"
DATA_BLOCK_COMPLETE = b"\01"
DATA_BLOCK_INCOMPLETE = b"\02"

CONTEXT_REPO_DEF = CONTEXT_JOKER + b"\x01"
CONTEXT_REPO_ID = CONTEXT_JOKER + b"\x02"
CONTEXT_REPO_NAME = CONTEXT_JOKER + b"\x03"
CONTEXT_BLOCK_DATA = CONTEXT_JOKER + b"\x04"
CONTEXT_KEY_DEF = CONTEXT_JOKER + b"\x05"
CONTEXT_IDX_DEF = CONTEXT_JOKER + b"\x06"
CONTEXT_REPO_OWNER_DEF = CONTEXT_JOKER + b"\x07"
CONTEXT_REPO_DATA = CONTEXT_JOKER + b"\x08"
CONTEXT_IDX_REPO_DATA = CONTEXT_JOKER + b"\x09"


def with_joker(data: bytes):
    j = CONTEXT_JOKER
    return data.replace(j, j + j)


def int_as_byte(number: int, byteorder="big"):
    if number == 0:
        return b"\x00"
    return number.to_bytes(int(math.log(number, 8)) + 1, byteorder)
