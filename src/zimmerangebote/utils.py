# -*- coding: utf-8 -*-

"""A module for useful general functions."""

from datetime import date
from itertools import islice, tee
from typing import Iterable, Optional, Tuple

from dateutil.relativedelta import relativedelta


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
