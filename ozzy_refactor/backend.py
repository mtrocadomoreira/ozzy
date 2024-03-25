import collections
import glob
import os
import re

from .grid_methods import GridMixin
from .ozdataset import OzzyDatasetBase
from .part_methods import PartMixin

# -----------------------------------------------------------------------
# Backend class
# -----------------------------------------------------------------------


class Backend:
    def __init__(self, file_type, axes_lims=None, *args, **kwargs):
        self.name = file_type
        self.axes_lims = axes_lims

        match file_type:
            case "osiris":
                from .backends import osiris_backend as backend_mod
            case "lcode":
                from .backends import lcode_backend as backend_mod
            case "ozzy":
                from .backends import ozzy_backend as backend_mod
            case _:
                raise ValueError(
                    'Invalid input for "file_type" keyword. Available options are "osiris", "lcode", or "ozzy".'
                )

        self.parse = backend_mod.read
        self.mixin = backend_mod.Methods

        self._quant_files = None
        self._regex_pattern = backend_mod.general_regex_pattern
        self._file_endings = backend_mod.general_file_endings
        self._quants_ignore = backend_mod.quants_ignore

    def find_quants(self, path, dirs_runs, quants):
        if quants is None:
            quants = [""]
        if isinstance(quants, str):
            quants = [quants]

        # Define search strings for glob
        searchterms = []
        for q in quants:
            if "." not in q:
                term = []
                for fend in self._file_endings:
                    term.append("**/" + q + "*." + fend)
                searchterms = searchterms + term

        # Search files matching mattern
        filenames = []
        for run, run_dir in dirs_runs.items():
            searchdir = os.path.join(path, run_dir)
            for term in searchterms:
                query = sorted(glob.glob(term, recursive=True, root_dir=searchdir))
                filenames = filenames + [os.path.basename(f) for f in query]

        # Look for clusters of files matching pattern
        pattern = re.compile(self._regex_pattern)
        matches = (
            (pattern.fullmatch(f), f)
            for f in filenames
            if pattern.fullmatch(f) is not None
        )

        # Build output dictionary
        quants_dict = collections.defaultdict(list)
        for m, f in matches:
            label = m.group(1).strip("_-")
            if f not in quants_dict[label]:
                quants_dict[label].append(f)

        # Drop quantities that should be ignored
        if self._quants_ignore is not None:
            for q in self._quants_ignore:
                if q in quants_dict:
                    del quants_dict[q]

        return quants_dict

    def _load_quant_files(self, *args, **kwargs):
        self._quant_files = self.find_quants(*args, **kwargs)
        return self._quant_files

    def parse_data(self, files, *args, **kwargs):
        print("\nReading the following files:")
        ods = self.parse(files, *args, **kwargs)

        # Set metadata
        ods = ods.assign_attrs(
            {
                "file_backend": self.name,
                "source": os.path.commonpath(files),
                "file_prefix": os.path.commonprefix(
                    [os.path.basename(f) for f in files]
                ),
            }
        )

        NewClass = dataset_cls_factory(self, ods.pic_data_type)

        return NewClass(ods)


# -----------------------------------------------------------------------
# Class factory for each dataset subtype
# -----------------------------------------------------------------------


def dataset_cls_factory(
    backends: Backend | list[Backend] | None = None, pic_data_type: str | None = None
):
    # Sort out backend input

    if backends is Backend:
        backends = [backends]
    elif backends is None:
        backends = []

    backends_mixin = [bknd.mixin for bknd in backends]

    if len(backends) > 1:
        dorigin_str = "mixed"
    elif len(backends):
        dorigin_str = backends[0].name
    elif len(backends) == 0:
        dorigin_str = "ozzy"

    # Sort out data type input

    dtype_key = {"grid": GridMixin, "part": PartMixin}

    try:
        dtype_str = pic_data_type.title()
    except AttributeError:
        dtype_str = ""

    try:
        dtype_mixin = [dtype_key[pic_data_type]]
    except KeyError:
        dtype_mixin = []

    # Define new class

    from_classes = [OzzyDatasetBase] + backends_mixin + dtype_mixin

    cls_name = dorigin_str.title() + dtype_str.title() + "Dataset"

    NewClass = type(
        cls_name,
        tuple(from_classes),
        {"pic_data_type": dtype_str, "data_origin": dorigin_str},
    )

    return NewClass
