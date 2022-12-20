import csv
from typing import List


def normalize_curies(map_path: str, entries: List) -> List:
    """Given a SSSOM map file defining one or more mappings between
        subject_id and object_id,
        take a list of dicts
        and produce an identical list with the ids replaced
        with their equivalents, as per the map.
        Items without mappings retain their original id values.
    :param map_path: path to the mapping file
    :param entries: list of entries (dicts) to normalize
                    with ids as prefix:value
    """

    new_entries = []

    # Load the map
    with open(map_path) as map_file:

        # Load map, skip header
        for n in range(11):
            next(map_file)
        norm_map = csv.DictReader(map_file, delimiter="\t")

        # Filter map to ids
        norm_id_map = {row["subject_id"]: row["object_id"] for row in norm_map}

    # Convert those input ids
    for entry in entries:
        new_entry = entry
        try:  # Input ID may not be in map
            new_id = norm_id_map[entry["id"]]
            if new_id != "":  # Empty value if there isn't a mapping
                new_entry["id"] = new_id
        except KeyError:
            pass
        new_entries.append(new_entry)

    return new_entries


def load_ids_from_map(map_path: str, prefix: str) -> List:
    """Given a SSSOM map file defining one or more mappings between
        subject_id and object_id,
        retrieve a list of all ids
        with a given prefix.
    :param map_path: path to the mapping file
    :param prefix: desired id prefix, without the colon
    """

    new_ids = []

    # Load the map
    with open(map_path) as map_file:

        # Load map, skip header
        for n in range(11):
            next(map_file)
        norm_map = csv.DictReader(map_file, delimiter="\t")

        # Filter map to ids
        for row in norm_map:
            if (row["subject_id"].split(":"))[0] == prefix:
                new_ids.append(row["subject_id"])

    return new_ids
