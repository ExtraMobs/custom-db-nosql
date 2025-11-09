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


class Repository:
    def __init__(self, name=None):
        self.name = name


class Schema:
    def __init__(self, *repos_iter, **repos_d: dict[str | Repository]):
        for key, value in repos_d.items():
            value.name = key
        self.repos = repos_d


class DatabaseManager:
    def __init__(self, path: str):
        path = os.path.abspath(path)
        if not os.path.exists(path):
            raise Exception("File not found.")

        if not os.path.isfile(path):
            raise Exception("Path is a folder.")

        self.__db_file = open(path, "rb+")
        self.__last_repo_id = 0
        self.__repo_id = {}
        self.__repo_obj = {}

