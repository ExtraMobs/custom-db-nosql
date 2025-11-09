import os
import math
import pickle
from pprint import pp
import random
import time

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

    def set_repo(self, repo: Repository):
        self.__db_file.write(CONTEXT_REPO_DEF)

        self.__db_file.write(CONTEXT_REPO_ID)
        self.__last_repo_id += 1
        self.__db_file.write(
            repo_id := with_joker(int_as_byte(self.__last_repo_id))
        )  # id
        self.__db_file.write(CONTEXT_REPO_ID)

        self.__db_file.write(CONTEXT_REPO_NAME)
        self.__db_file.write(with_joker(bytes(repo.name, "utf-8")))  # db_name
        self.__db_file.write(CONTEXT_REPO_NAME)

        self.__db_file.write(CONTEXT_REPO_DEF)

        self.__repo_id[bytes(repo.name, "utf-8")] = repo_id
        self.__repo_obj[repo_id] = repo

    def get_repo_by_name(self, name) -> Repository:
        return self.__repo_id[name]

    def insert_into(self, repo_id: bytes, data_to: list[dict]):
        print(self.__db_file.seek(0, 2))
        for data_item in data_to:
            self.__db_file.write(CONTEXT_REPO_DATA)

            self.__db_file.write(CONTEXT_REPO_OWNER_DEF)
            self.__db_file.write(with_joker(repo_id))

            self.__db_file.write(CONTEXT_IDX_REPO_DATA)
            self.__db_file.write(with_joker(int_as_byte(int(time.time() * 1000))))
            self.__db_file.write(CONTEXT_IDX_REPO_DATA)

            self.__db_file.write(CONTEXT_REPO_OWNER_DEF)

            for name, data in data_item.items():
                self.__db_file.write(CONTEXT_KEY_DEF)
                self.__db_file.write(name)
                self.__db_file.write(CONTEXT_KEY_DEF)
                for idx, item in enumerate(data):
                    self.__db_file.write(CONTEXT_IDX_DEF)
                    self.__db_file.write(with_joker(int_as_byte(idx)))
                    self.__db_file.write(CONTEXT_IDX_DEF)

                    self.__db_file.write(CONTEXT_BLOCK_DATA)
                    self.__db_file.write(DATA_BLOCK_COMPLETE)
                    self.__db_file.write(with_joker(item))
                    self.__db_file.write(CONTEXT_BLOCK_DATA)

            self.__db_file.write(CONTEXT_REPO_DATA)
        self.__db_file.flush()

    def read(self, repo_id):
        to_return = []
        self.__db_file.seek(0)
        awaiting_context = False
        contexts = []
        parsing = []
        is_repo_target = True

        local_return_idx = {}
        data_block_idx = None

        while (read_bytes := self.__db_file.read(1)) != b"":
            if awaiting_context:
                if read_bytes == CONTEXT_REPO_DATA[1:2]:
                    if len(contexts) == 0 or contexts[-1] != CONTEXT_REPO_DATA:
                        contexts.append(CONTEXT_REPO_DATA)
                    else:
                        del contexts[-1]
                elif read_bytes == CONTEXT_REPO_OWNER_DEF[1:2]:
                    if len(contexts) == 0 or contexts[-1] != CONTEXT_REPO_OWNER_DEF:
                        contexts.append(CONTEXT_REPO_OWNER_DEF)
                    else:
                        if parsing[:-1] == repo_id:
                            is_repo_target = True
                        else:
                            is_repo_target = False
                        parsing.clear()
                        del contexts[-1]
                elif read_bytes == CONTEXT_IDX_REPO_DATA[1:2]:
                    if len(contexts) == 0 or contexts[-1] != CONTEXT_IDX_REPO_DATA:
                        contexts.append(CONTEXT_IDX_REPO_DATA)
                    else:
                        register_idx = int(b"".join(parsing[:-1]).hex(), 16)
                        if not register_idx in local_return_idx.keys():
                            local_return_idx[register_idx] = len(to_return)
                            to_return.append({})
                        parsing.clear()
                        del contexts[-1]
                elif read_bytes == CONTEXT_KEY_DEF[1:2]:
                    if len(contexts) == 0 or contexts[-1] != CONTEXT_KEY_DEF:
                        contexts.append(CONTEXT_KEY_DEF)
                    else:
                        current_key = b"".join(parsing[:-1])
                        current_dict = to_return[local_return_idx[register_idx]]
                        if not current_key in current_dict:
                            current_dict[current_key] = []
                        parsing.clear()
                        del contexts[-1]
                elif read_bytes == CONTEXT_IDX_DEF[1:2]:
                    if len(contexts) == 0 or contexts[-1] != CONTEXT_IDX_DEF:
                        contexts.append(CONTEXT_IDX_DEF)
                    else:
                        data_block_idx = int(b"".join(parsing[:-1]).hex(), 16)
                        parsing.clear()
                        print(data_block_idx)
                        del contexts[-1]
                elif read_bytes == CONTEXT_BLOCK_DATA[1:2]:
                    if len(contexts) == 0 or contexts[-1] != CONTEXT_BLOCK_DATA:
                        contexts.append(CONTEXT_BLOCK_DATA)
                    else:
                        current_dict = to_return[local_return_idx[register_idx]][
                            current_key
                        ].append(b"".join(parsing[1:-1]))
                        parsing.clear()
                        del contexts[-1]
            if len(contexts) > 0:
                if not awaiting_context:
                    if contexts[-1] in (
                        CONTEXT_REPO_OWNER_DEF,
                        CONTEXT_IDX_REPO_DATA,
                        CONTEXT_KEY_DEF,
                        CONTEXT_IDX_DEF,
                        CONTEXT_BLOCK_DATA,
                    ):
                        parsing.append(read_bytes)

            if read_bytes == CONTEXT_JOKER and not awaiting_context:
                awaiting_context = True
            else:
                awaiting_context = False

        return to_return

    @classmethod
    def create(cls, path: str, schema: Schema):

        if not schema.__class__ is Schema:
            raise Exception(f"Invalid Schema: {schema}")

        open(path, "x")
        dbm = cls(path)

        for repo in schema.repos.values():
            dbm.set_repo(repo)

        return dbm


schema = Schema(test_repo=Repository())

path = "./test.custom_db"

# db = DatabaseManager.create(path, schema)
# db.insert_into(
#     db.get_repo_by_name(b"test_repo"), [{b"nomes": [bytes(i, 'utf-8') for i in pickle.load(open('string_list_dump', 'rb'))]}]
# )

db = DatabaseManager(path)
pp(
    [str(item, "utf-8") for item in db.read(b"\x01")[0][b"nomes"]]
    == pickle.load(open("string_list_dump", "rb"))
)
# print()

# 00 - Coringa dentro do contexto
# 01 - Bloco de dados completo
# 02 - Bloco de dados incompleto (Sabe que tem alterações mais a frente no arquivo)

# 0001 - Contexto de definição do Repo
# 0002 - Contexto de Id do Repo
# 0003 - Contexto do Nome do Repo
# 0004 - Contexto de bloco de dados
# 0005 - Contexto de definição de chave
# 0006 - Contexto de definição de índice
# 0007 - Contexto de definição de repo dono
# 0008 - Contexto de dados do repositório
# 0009 - Contexte de índice da lista dentro do registro
