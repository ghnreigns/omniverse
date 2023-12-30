from __future__ import annotations

import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Type

import requests


class Vocabulary(ABC):
    # Special tokens as class attributes
    BOS = "<BOS>"
    EOS = "<EOS>"
    PAD = "<PAD>"
    UNK = "<UNK>"

    def __init__(
        self,
        token_to_index: Dict[str, int],
        index_to_token: Dict[int, str],
        num_digits: int,
    ) -> None:
        self.token_to_index = token_to_index
        self.index_to_token = index_to_token
        self.num_digits = num_digits

    @abstractmethod
    def tokenize(self, sequence: str, add_special_tokens: bool = True) -> List[str]:
        """
        Tokenizes a sequence into a sequence (list) of tokens.

        Example
        -------
        >>> tokenizer = Tokenizer()
        >>> tokenizer.tokenize("The quick brown fox jumps over the lazy dog.")
        ["The", "quick", "brown", "fox", "jumps", "over", "the", "lazy", "dog", "."]

        Parameters
        ----------
        sequence : str
            The sequence to tokenize.
        add_special_tokens : bool
            Whether to add special tokens to the sequence of tokens, by default True.

        Returns
        -------
        List[str]
            The sequence of tokens.
        """

    @abstractmethod
    def encode(self, sequence: str, add_special_tokens: bool = True) -> List[int]:
        """
        Encodes a sequence to its corresponding integer index.

        Parameters
        ----------
        sequence : str
            The sequence to encode.

        Returns
        -------
        List[int]
            The integer index corresponding to the token.
        """

    @abstractmethod
    def decode(self, encoded_sequence: List[int], remove_special_tokens: bool = True) -> str:
        """
        Decodes an integer index back to its corresponding token.

        Parameters
        ----------
        index : int
            The integer index to decode.

        Returns
        -------
        str
            The token corresponding to the integer index.
        """

    @abstractmethod
    def __len__(self) -> int:
        """
        Returns the number of tokens in the vocabulary.

        Returns
        -------
        int
            The number of tokens in the vocabulary.
        """

    @property
    @abstractmethod
    def vocab_size(self) -> int:
        """
        Returns the size of the vocabulary.

        Returns
        -------
        int
            The size of the vocabulary.
        """

    @classmethod
    def from_tokens(cls: Type[Vocabulary], tokens: List[str], num_digits: int = 2) -> Vocabulary:
        token_to_index = {token: idx for idx, token in enumerate(tokens)}
        index_to_token = {idx: token for token, idx in token_to_index.items()}
        return cls(token_to_index, index_to_token, num_digits)


class AdderVocabulary(Vocabulary):
    # special tokens
    BOS = "<BOS>"
    EOS = "<EOS>"
    PAD = "<PAD>"
    UNK = "<UNK>"
    ADD = "+"
    EQUAL = "="
    TOKENS = [
        "0",
        "1",
        "2",
        "3",
        "4",
        "5",
        "6",
        "7",
        "8",
        "9",
        "+",
        "*",
        "-",
        "=",
        "<BOS>",
        "<EOS>",
        "<PAD>",
        "<UNK>",
    ]

    def tokenize(self, sequence: str, add_special_tokens: bool = True) -> List[str]:
        tokens = [char for char in sequence]  # noqa: C416
        if add_special_tokens:
            tokens = [AdderVocabulary.BOS] + tokens + [AdderVocabulary.EOS]
        return tokens

    def encode(self, sequence: str, add_special_tokens: bool = True) -> List[int]:
        tokens: List[str] = self.tokenize(sequence, add_special_tokens=add_special_tokens)
        encoded_sequence: List[int] = [
            self.token_to_index.get(token, self.token_to_index[AdderVocabulary.UNK]) for token in tokens
        ]
        return encoded_sequence

    def encode_batch(self, sequences: List[str], add_special_tokens: bool = True) -> List[List[int]]:
        return [self.encode(sequence, add_special_tokens=add_special_tokens) for sequence in sequences]

    def decode(self, encoded_sequence: List[int], remove_special_tokens: bool = True) -> str:
        decoded = "".join([self.index_to_token.get(char, AdderVocabulary.UNK) for char in encoded_sequence])

        if remove_special_tokens:
            decoded = re.sub(
                f"{AdderVocabulary.BOS}|{AdderVocabulary.EOS}|{AdderVocabulary.PAD}|{AdderVocabulary.UNK}",
                "",
                decoded,
            )
        return decoded

    def decode_batch(self, encoded_sequences: List[List[int]], remove_special_tokens: bool = True) -> List[str]:
        return [
            self.decode(encoded_sequence, remove_special_tokens=remove_special_tokens)
            for encoded_sequence in encoded_sequences
        ]

    def __len__(self) -> int:
        return len(self.token_to_index)

    @property
    def vocab_size(self) -> int:
        return len(self)


class TextCharacterVocabulary:
    """
    A vocabulary class for character-level text processing. This class is designed
    to handle the encoding and decoding of characters in text data. It is particularly
    useful for tasks involving character-level models, such as GPT-style language models.

    The vocabulary consists of a set of unique characters found in a given text corpus.
    """

    PAD = "<PAD>"

    def __init__(self, token_to_index: Dict[str, int], index_to_token: Dict[int, str]) -> None:
        self.token_to_index = token_to_index
        self.index_to_token = index_to_token

    @staticmethod
    def _download(url: str, dest_folder: Path | str) -> Path:
        dest_folder_path = Path(dest_folder)
        dest_folder_path.mkdir(parents=True, exist_ok=True)

        local_filename = Path(url).name
        filepath = dest_folder_path / local_filename

        response = requests.get(url, stream=True)
        response.raise_for_status()

        with open(filepath, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        return filepath

    @classmethod
    def from_corpus(cls: Type[TextCharacterVocabulary], corpus: str) -> TextCharacterVocabulary:
        vocabulary = sorted(set(corpus))
        token_to_index = {token: idx for idx, token in enumerate(vocabulary)}
        index_to_token = {idx: token for token, idx in token_to_index.items()}
        return cls(token_to_index, index_to_token)

    @classmethod
    def from_file(cls: Type[TextCharacterVocabulary], file_path: str | Path) -> TextCharacterVocabulary:
        with open(file_path, "r") as f:
            corpus = f.read()
        return cls.from_corpus(corpus)

    @classmethod
    def from_url(
        cls: Type[TextCharacterVocabulary], url: str, dest_folder: str | Path | None = None
    ) -> TextCharacterVocabulary:
        if not dest_folder:
            response = requests.get(url)
            response.raise_for_status()
            corpus = response.text
            return cls.from_corpus(corpus)

        file_path = cls._download(url, dest_folder)
        return cls.from_file(file_path)

    def __len__(self) -> int:
        return len(self.token_to_index)

    @property
    def vocab_size(self) -> int:
        return len(self)
