# -*- coding: utf-8 -*-

"""A module for useful general functions."""

import logging
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from dataclasses import dataclass, field
from itertools import islice, tee
from typing import Iterable, Optional, Tuple, Dict, Union

from pandas import DataFrame


def get_ngrams(
        elements: Iterable,
        ngram_length: int,
        step: Optional[int] = None
) -> Iterable[Tuple]:
    """An efficient ngram iterator based on
    https://github.com/dlazesz/n-gram-benchmark/blob/master/ngram.py

    Args:
        elements: The elements to iterate over.
        ngram_length: The ngram length (e. g. 2 means bigrams).
        step: Optional. The step size between the ngrams.

    Returns:
        An iterable of ngrams.
    """
    return zip(*(islice(it, i, step) for i, it in enumerate(tee(elements, ngram_length))))


def shift_date_by_months(n_months: int) -> date:
    """Add `n_month` to the current date.

    Args:
        n_months: The number of month to add to the current date.

    Returns:
        The calculated future date.
    """
    return date.today() + relativedelta(months=n_months)


def fill_scheme_string(
        scheme: str, *,
        year: Optional[int] = None,
        month: Optional[int] = None,
        day: Optional[int] = None
) -> str:
    """Fill a scheme. The substrings `{year}`, `{month}`
    and `{day}` will be searched for in the input string.
    They will be replaced with the specified year, month
    and day values.

    Args:
        scheme: The scheme string to operate on.
        year: Optional. A number with which all occurrences of the
            substring `{year}` will be replaced.
        month: Optional. A number with which all occurrences of the
            substring `{month}` will be replaced.
        day: Optional. A number with which all occurrences of the
            substring `{day}` will be replaced.

    Returns:
        The string that is the result of replacements. If all arguments
        apart from `scheme` were unspecified, it is the input string.

    Raises:
        `ValueError` for invalid year, month or day values.
        `KeyError` if a year, month or day was specified but the
            corresponding substring is not in the scheme.
    """
    test_year = year if year is not None else 2022
    test_month = month if month is not None else 12
    test_day = day if day is not None else 1
    date(year=test_year, month=test_month, day=test_day)  # Raises ValueError if the date is invalid

    date_marks = ("{year}", "{month}", "{day}")
    for date_element, date_mark in zip((year, month, day), date_marks):
        if date_element is not None:
            if date_mark not in scheme:
                raise KeyError(f"{date_element} for {date_mark} is incompatible "
                               f"with scheme `{scheme}`")
            scheme = scheme.replace(date_mark, str(date_element))
    return scheme


def get_custom_logger(name: str, file_path: Optional[str] = None) -> logging.Logger:
    """Create a custom logger object.

    Args:
        name: The logger name.
        file_path: Optional. Path to a file where the logs will be written.
            If not specified `stdout` will be used.

    Returns:
        The logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    handler = logging.FileHandler(file_path, mode="w", encoding="utf-8") \
        if file_path is not None else logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(name)s:%(levelname)s:%(message)s",)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


@dataclass(frozen=True)
class Room:
    """A dataclass for storing room properties."""
    category: str = field(metadata={"help": "The room category."})
    size: int = field(metadata={"help": "The room size."})
    price: int = field(metadata={"help": "The room price."})
    is_early_booking: bool = field(
        metadata={
            "help": "Specifies if it is an early booking "
                    "(>= 6 months between booking and arrival months)"
        }
    )
    datum: date = field(
        default_factory=datetime.today,
        metadata={
            "help": "The date when the data was requested. Defaults to today."
        }
    )

    def __post_init__(self) -> None:
        """Check attribute values."""
        if len(self.category) == 0:
            raise ValueError("Room category cannot be the empty string.")
        if self.size <= 0:
            raise ValueError(f"Room size must be positive, specified {self.size}")
        if self.price < 0:
            raise ValueError(f"Price size must be non-negative, specified {self.price}")

    def to_dict(self) -> Dict[str, Union[str, int, bool]]:
        """Return the data in a `dict`. The date will be converted to a string."""
        data_dict = self.__dict__.copy()
        data_dict["datum"] = self.datum.strftime("%Y/%m/%d")
        return data_dict

@dataclass
class ThreadResultHolder:
    """A mutable dataclass to store the value of a thread execution."""
    df: Optional[DataFrame] = field(
        default=None, metadata={"help": "A pandas dataframe with room information."}
    )
