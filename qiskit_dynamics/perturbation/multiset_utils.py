# This code is part of Qiskit.
#
# (C) Copyright IBM 2022.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.
# pylint: disable=invalid-name

"""
Utility functions for working with multisets.
"""

from typing import List, Optional, Tuple
import itertools

from multiset import Multiset

from qiskit import QiskitError


def _validate_non_negative_ints(multiset: Multiset) -> bool:
    """Validate that a multiset only contains non-negative integers."""

    for elem in multiset.distinct_elements():
        if not isinstance(elem, int) or not elem >= 0:
            raise QiskitError(
                "Only Multisets whose entries are non-negative integers are accepted."
            )


def _multiset_to_sorted_list(multiset: Multiset) -> List:
    """Convert multiset to a sorted list. Assumes elements of multiset can be sorted."""

    distinct_elems = list(multiset.distinct_elements())
    distinct_elems.sort()

    sorted_list = []
    for elem in distinct_elems:
        sorted_list = sorted_list + [elem] * multiset[elem]

    return sorted_list


def _sorted_multisets(multisets: List[Multiset]) -> List[Multiset]:
    """Sort in non-decreasing order according to:

    ms1 <= ms2 if len(ms1) < len(ms2), or if
    len(ms1) == len(ms2) and if
    str(_multiset_to_sorted_list(ms1)) <= str(_multiset_to_sorted_list(ms2)).
    """

    return sorted(multisets, key=lambda x: str(len(x)) + ", " + str(_multiset_to_sorted_list(x)))


def _clean_multisets(multisets: List[Multiset]) -> List[Multiset]:
    """Given a list of multisets, remove duplicates, and sort in non-decreasing order
    according to the _sorted_multisets function.
    """

    unique_multisets = []
    for multiset in multisets:
        multiset = Multiset(multiset)

        if multiset not in unique_multisets:
            unique_multisets.append(multiset)

    return _sorted_multisets(unique_multisets)


def _submultiset_filter(
    multiset_candidates: List[Multiset], multiset_list: List[Multiset]
) -> List[Multiset]:
    """Filter the list of multiset_candidates based on whether they are a
    submultiset of an element in multiset_list.
    """

    filtered_multisets = []
    for candidate in multiset_candidates:
        for multiset in multiset_list:
            if candidate <= multiset:
                filtered_multisets.append(candidate)
                break

    return filtered_multisets


def _submultisets_and_complements(
    multiset: Multiset, submultiset_bound: Optional[int] = None
) -> Tuple[List[Multiset], List[Multiset]]:
    """Return a pair of lists giving all submultisets of size smaller than
    submultiset_bound, and corresponding complements.

    Note: Submultisets and compliments are always strict submultisets.

    Args:
        multiset: The multiset to construct submultisets from.
        submultiset_bound: Strict upper bound on submultiset to include.
                           Defaults to len(multiset).

    Returns:
        Submultisets and corresponding complements.
    """

    if submultiset_bound is None or submultiset_bound > len(multiset):
        submultiset_bound = len(multiset)

    multiset_list = _multiset_to_sorted_list(multiset)

    submultisets = []
    complements = []

    for k in range(1, submultiset_bound):
        location_subsets = itertools.combinations(range(len(multiset_list)), k)
        for location_subset in location_subsets:
            subset = []
            complement = []

            for loc, multiset_entry in enumerate(multiset_list):
                if loc in location_subset:
                    subset.append(multiset_entry)
                else:
                    complement.append(multiset_entry)

            if subset not in submultisets:
                submultisets.append(subset)
                complements.append(complement)

    # convert back to proper dict representation
    formatted_submultisets = [Multiset(submultiset) for submultiset in submultisets]
    formatted_complements = [Multiset(complement) for complement in complements]

    return formatted_submultisets, formatted_complements


def _get_all_submultisets(multisets: List[Multiset]) -> List[Multiset]:
    """Given a list of multisets, return a list of all possible submultisets
    of multisets in the list, including the original multisets.

    This returned list is sorted according to the ordering of the _sorted_multisets function.

    Args:
        multisets: List of multisets (not necessarilly correctly formatted).

    Returns:
        List: Complete list of index multisets generated by the argument.
    """

    if multisets == []:
        return []

    # clean list to unique list of properly formatted terms
    multisets = _clean_multisets(multisets)

    max_order = max(map(len, multisets))

    # partition multisets according to size
    order_dict = {k: [] for k in range(1, max_order + 1)}
    for multiset in multisets:
        order = len(multiset)
        if multiset not in order_dict[order]:
            order_dict[order].append(multiset)

    # loop through orders in reverse order, adding subterms to lower levels if necessary
    for order in range(max_order, 1, -1):
        for multiset in order_dict[order]:
            submultisets = _submultisets_and_complements(multiset, 2)[1]

            for submultiset in submultisets:
                if submultiset not in order_dict[order - 1]:
                    order_dict[order - 1].append(submultiset)

    full_list = []
    for submultisets in order_dict.values():
        full_list += submultisets

    return _sorted_multisets(full_list)
