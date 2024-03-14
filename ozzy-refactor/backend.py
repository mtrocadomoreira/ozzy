import os


class Backend:
    def __init__(self, file_type, as_series, axes_lims=None, *args, **kwargs):
        self.as_series = as_series
        self.axes_lims = axes_lims
        match file_type:
            case "osiris":
                from . import osiris_backend

                self.name = "osiris"
                self.parse = osiris_backend.read_osiris
                # TODO define:
                #   - self.find_quants()
            case "lcode":
                from . import lcode_backend

                self.name = "lcode"
                self.parse = lcode_backend.read_lcode
                # TODO define:
                #   - self.find_quants()
            case "ozzy":
                pass
                # ds = read_ozzy(filepaths, as_series)
            case _:
                raise ValueError(
                    'Invalid input for "file_type" keyword. Available options are "osiris", "lcode", or "ozzy".'
                )

    # TODO: define function to set attributes of standard quantities like t, x1, etc

    def parse_data(self, files):
        print("\nReading the following files:")
        ods = self.parse(files, self.as_series)

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

        return ods
