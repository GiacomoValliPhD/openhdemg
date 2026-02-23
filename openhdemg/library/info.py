"""
This module contains all the information regarding:

- Data
    - Structures of data
    - How to access data

- Abbreviations

- AboutUs
- Contacts
- Links
- CiteUs
"""

import json
import textwrap
from textwrap import dedent

import numpy as np
import pandas as pd


class info:  # TODO new data structure and more flexibility, also change the SOURCE fields through the repo
    """
    A class used to obtain info.

    Methods
    -------
    data(emgfile)
        Print a description of the emgfile data structure.
    abbreviations()
        Print common abbreviations.
    aboutus()
        Print informations about the library and the authors.
    contacts()
        Print the contacts.
    links()
        Print a collection of useful links.
    citeus()
        Print how to cite the project.
    """

    def __init__(self):
        pass

    def data(self, emgfile):
        """
        Print a description of the emgfile data structure.

        Print a detailed description of the emgfile data structure and of how
        to access the contained elements.

        Parameters
        ----------
        emgfile : dict
            The dictionary containing the emgfile.

        Examples
        --------
        >>> import openhdemg.library as emg
        >>> emgfile = emg.askopenfile(filesource="DEMUSE")
        >>> emg.info().data(emgfile)
        emgfile type is:
        <class 'dict'>
        emgfile keys are:
        dict_keys(['SOURCE', 'FILENAME', 'RAW_SIGNAL', 'REF_SIGNAL', 'ACCURACY', 'IPTS', 'MUPULSES', 'FSAMP', 'IED', 'EMG_LENGTH', 'NUMBER_OF_MUS', 'BINARY_MUS_FIRING', 'EXTRAS'])
        Any key can be acced as emgfile[key].
        'SOURCE':
            str: 'OPENHDEMG'
        'FSAMP':
            float: 2048.0
        .
        .
        .
        """

        MAX_W = 80  # max line width for keys/cols lists etc.

        def _srepr(x, limit=300):
            """Safe repr that never raises and never gets too long."""

            try:
                out = repr(x)
            except Exception as e:
                out = f"<unrepr-able: {type(e).__name__}: {e}>"
            return out if len(out) <= limit else out[:limit] + " …"

        def _wrap_list(
            items,
            *,
            indent=0,
            width=MAX_W,
            max_items=25,
            prefix="",
        ):

            """
            Wrap a list-like preview so lines stay <= `width` (best-effort),
            with nice indentation similar to code formatting.
            """
            pad = " " * indent

            # Safely tokenise items, keeping each token short
            tokens = []
            try:
                seq = list(items)
            except Exception:
                seq = []

            for it in seq[:max_items]:
                tokens.append(_srepr(it, limit=30))

            more = ""
            try:
                if len(seq) > max_items:
                    more = f", ... (+{len(seq) - max_items} more)"
            except Exception:
                pass

            body = ", ".join(tokens) + more
            text = f"{prefix}[{body}]"

            return textwrap.fill(
                text,
                width=width,
                initial_indent=pad,
                subsequent_indent=pad + " " * (len(prefix) + 1),
                break_long_words=False,
                break_on_hyphens=False,
            )

        def _summarise(x, depth=1, indent=0):
            pad = " " * indent

            try:
                # dict
                if isinstance(x, dict):
                    try:
                        keys = list(x.keys())
                    except Exception as e:
                        _name = type(e).__name__
                        return f"{pad}dict (keys unreadable: {_name}: {e})"

                    more = (
                        "" if len(keys) <= 25 else f" (+{len(keys) - 25} more)"
                    )
                    lines = [f"{pad}dict ({len(keys)} keys{more})"]
                    lines.append(
                        _wrap_list(
                            keys,
                            indent=indent,
                            width=MAX_W,
                            max_items=25,
                            prefix="keys=",
                        )
                    )

                    if depth > 0 and keys:
                        for k in keys[:20]:
                            try:
                                v = x[k]
                            except Exception as e:
                                _name = type(e).__name__
                                lines.append(
                                    f"{pad}  {k!r}: <unreadable: {_name}: {e}>"
                                )
                                continue

                            # recurse nicely for nested dicts
                            if isinstance(v, dict) and depth > 0:
                                lines.append(f"{pad}  {k!r}:")
                                lines.append(
                                    _summarise(
                                        v,
                                        depth=depth - 1,
                                        indent=indent + 4,
                                    )
                                )
                            else:
                                child = _summarise(
                                    v, depth=depth - 1, indent=0,
                                ).lstrip()
                                lines.append(f"{pad}  {k!r}: {child}")

                    return "\n".join(lines)

                # DataFrame
                if isinstance(x, pd.DataFrame):
                    try:
                        r, c = x.shape
                        cols = list(x.columns)
                        preview_cols = cols[:12]

                        extra_c = "" if c <= 12 else f" (+{c - 12} cols)"
                        extra_r = "" if r <= 5 else f" (+{r - 5} rows)"

                        head = x.loc[:, preview_cols].head(5)

                        lines = [
                            f"{pad}DataFrame shape={x.shape}{extra_r}{extra_c}"
                        ]
                        lines.append(
                            _wrap_list(
                                preview_cols,
                                indent=indent + 2,
                                width=MAX_W,
                                max_items=12,
                                prefix="columns=",
                            ) + (
                                "" if c <= 12 else " ..."
                            )
                        )
                        lines.append(f"{pad}  head:\n{head}")
                        return "\n".join(lines)
                    except Exception as e:
                        _name = type(e).__name__
                        return f"{pad}DataFrame (summary failed: {_name}: {e})"

                # Series
                if isinstance(x, pd.Series):
                    try:
                        n = len(x)
                        head = x.head(8)
                        extra = "" if n <= 8 else f" (+{n - 8})"
                        _string = (
                            f"{pad}Series len={n}{extra}\n{pad}  head:\n{head}"
                        )
                        return _string
                    except Exception as e:
                        _name = type(e).__name__
                        return f"{pad}Series (summary failed: {_name}: {e})"

                # ndarray
                if isinstance(x, np.ndarray):
                    try:
                        preview = "<preview failed>"
                        try:
                            preview = _srepr(x.ravel()[:10])
                        except Exception:
                            pass
                        return (
                            f"{pad}ndarray shape={getattr(x, 'shape', None)}, "
                            f"dtype={getattr(x, 'dtype', None)}, "
                            f"preview={preview}"
                        )
                    except Exception as e:
                        _name = type(e).__name__
                        return f"{pad}ndarray (summary failed: {_name}: {e})"

                # sequences
                if isinstance(x, (list, tuple, set)):
                    try:
                        seq = list(x) if isinstance(x, set) else x
                        n = len(seq)
                        types = [type(v).__name__ for v in seq[:5]]
                        return _wrap_list(
                            types,
                            indent=indent,
                            width=MAX_W,
                            max_items=5,
                            prefix=f"{type(x).__name__} len={n}, first_types=",
                        )
                    except Exception as e:
                        _string = (
                            f"{pad}{type(x).__name__} "
                            f"(summary failed: {type(e).__name__}: {e})"
                        )
                        return _string

                # scalar fallback
                return f"{pad}{type(x).__name__}: {_srepr(x)}"

            except Exception as e:
                return f"{pad}<summary failed: {type(e).__name__}: {e}>"

        print("\nData structure of the emgfile")
        print("-----------------------------\n")
        print(f"emgfile type is:\n{type(emgfile)}\n")

        if not isinstance(emgfile, dict):
            print("WARNING: emgfile is not a dict. Summarising object:\n")
            print(_summarise(emgfile, depth=2, indent=2))
            return

        # Keys (wrapped to 80 chars)
        try:
            keys = list(emgfile.keys())
            print(f"emgfile keys are ({len(keys)}):")
            print(
                _wrap_list(
                    keys, indent=0, width=MAX_W, max_items=60, prefix="",
                )
            )
            print("")
        except Exception as e:
            _name = type(e).__name__
            print(f"emgfile keys are: <failed to list keys: {_name}: {e}>\n")

        print("Any key can be accessed as emgfile[key].\n")

        # Full inspection (everything)
        print("All fields (full inspection):")
        print("----------------------------")
        try:
            all_keys = list(emgfile.keys())
        except Exception:
            all_keys = []

        for k in all_keys:
            try:
                v = emgfile[k]
            except Exception as e:
                print(f"{k!r}: <failed to access: {type(e).__name__}: {e}>\n")
                continue

            depth = 3 if isinstance(v, dict) else 1
            print(f"{k!r}:")
            print(_summarise(v, depth=depth, indent=2))
            print("")

        print("Done.\n")

    def abbreviations(self):
        """
        Print common abbreviations.

        Returns
        -------
        abbr : dict
            The dictionary containing the abbreviations and their meaning.

        Examples
        --------
        >>> import openhdemg.library as emg
        >>> emg.info().abbreviations()
        "COV": "Coefficient of variation",
        "DERT": "DERecruitment threshold",
        "DD": "Double differential",
        "DR": "Discharge rate",
        "FSAMP": "Sampling frequency",
        "IDR": "Instantaneous discharge rate",
        "IED": "Inter electrode distance",
        "IPTS": "Impulse train (decomposed source)",
        "MU": "Motor units",
        "MUAP": "MUs action potential",
        "PIC": "Persistent inward currents",
        "PNR": "Pulse to noise ratio",
        "RT": "Recruitment threshold",
        "SD": "Single differential",
        "SIL": "Silhouette score",
        "STA": "Spike-triggered average",
        "SVR": "Support Vector Regression",
        "XCC": "Cross-correlation coefficient"
        """

        abbr = {
            "COV": "Coefficient of variation",
            "DERT": "DERecruitment threshold",
            "DD": "Double differential",
            "DR": "Discharge rate",
            "FSAMP": "Sampling frequency",
            "IDR": "Instantaneous discharge rate",
            "IED": "Inter electrode distance",
            "IPTS": "Impulse train (decomposed source)",
            "MU": "Motor units",
            "MUAP": "MUs action potential",
            "PIC": "Persistent inward currents",
            "PNR": "Pulse to noise ratio",
            "RT": "Recruitment threshold",
            "SD": "Single differential",
            "SIL": "Silhouette score",
            "STA": "Spike-triggered average",
            "SVR": "Support Vector Regression",
            "XCC": "Cross-correlation coefficient",
        }

        # Pretty dict printing
        print("\nAbbreviations:\n")
        print(json.dumps(abbr, indent=4))

        return abbr

    def aboutus(self):
        """
        Print informations about the library and the authors.

        Returns
        -------
        about, us : str
            The strings containing the information.

        Examples
        --------
        >>> import openhdemg.library as emg
        >>> emg.info().aboutus()
        The openhdemg project was born in 2022 with the aim to provide a
        free and open-source framework to analyse HIGH-DENSITY EMG
        recordings...
        """

        about = """
            About
            -----

            The openhdemg project was born in 2022 with the aim to provide a
            free and open-source framework to analyse HIGH-DENSITY EMG
            recordings.

            The field of EMG analysis in humans has always be characterised by
            little or no software available for signal post-processing and
            analysis and this forced users to code their own scripts.
            Although coding can be funny, it can lead to a number of problems,
            especially when the utilised scripts are not shared open-source.
            Why?

            - If different users use different scripts, the results can differ.
            - Any code can contain errors, if the code is not shared, the error
                will never be known and it will repeat in the following
                analysis.
            - There is a huge difference between the paper methods and the
                practical implementation of a script. Only rarely it will be
                possible to reproduce a script solely based on words (thus
                making the reproducibility of a study unrealistic).
            - Anyone who doesn't code, will not be able to analyse the
                recordings.

            In order to overcome these (and many other) problems of private
            scripts, we developed a fully transparent framework with
            appropriate documentation to allow all the users to check the
            correctness of the script and to perform reproducible analysis.

            This project is aimed at users that already know the Python
            language, as well as for those willing to learn it and even for
            those not interested in coding thanks to a friendly software.

            Both the openhdemg project and its contributors adhere to the Open
            Science Principles and especially to the idea of public release of
            data and other scientific resources necessary to conduct honest
            research.
            """

        us = """
        Us
        --

        For the full list of contributors and developers visit:
        https://www.giacomovalli.com/openhdemg/about-us/
        """

        # Make Text Bold and Italic with Escape Sequence
        # '\x1B[3m' makes it italic
        # '\x1B[1m' makes it bold
        # '\x1B[1;3m' makes it bold and italic
        # '\x1B[0m' is the closing tag

        # Pretty print indented multiline str
        print(dedent(about))
        print(dedent(us))

        return about, us

    def contacts(self):
        """
        Print the contacts.

        Returns
        -------
        contacts : dict
            The dictionary containing the contact details.

        Examples
        --------
        >>> import openhdemg.library as emg
        >>> emg.info().contacts()
        "Primary contact": "openhdemg@gmail.com",
        "Twitter": "@openhdemg",
        "Maintainer": "Giacomo Valli",
        "Maintainer Email": "giacomo.valli@unibs.it",
        """

        contacts = {
            "Primary contact": "openhdemg@gmail.com",
            "Twitter": "@openhdemg",
            "Maintainer": "Giacomo Valli",
            "Maintainer Email": "giacomo.valli@unibs.it",
        }

        # Pretty dict printing
        print("\nContacts:\n")
        print(json.dumps(contacts, indent=4))

        return contacts

    def links(self):
        """
        Print a collection of useful links.

        Returns
        -------
        links : dict
            The dictionary containing the useful links.

        Examples
        --------
        >>> import openhdemg.library as emg
        >>> emg.info().links()
        """

        links = {
            "Project Website": "https://www.giacomovalli.com/openhdemg/",
            "Release Notes": "https://www.giacomovalli.com/openhdemg/what%27s-new/",
            "Cite Us": "https://www.giacomovalli.com/openhdemg/cite-us/",
            "Discussion Forum": "https://github.com/GiacomoValliPhD/openhdemg/discussions",
            "Report Bugs": "https://github.com/GiacomoValliPhD/openhdemg/issues",
        }

        # Pretty dict printing
        print("\nLinks:\n")
        print(json.dumps(links, indent=4))

        return links

    def citeus(self):
        """
        Print how to cite the project.

        Returns
        -------
        cite : str
            The full citation.

        Examples
        --------
        >>> import openhdemg.library as emg
        >>> emg.info().citeus()
        """

        cite = (
            "Valli G, Ritsche P, Casolo A, Negro F, De Vito G. " +
            "Tutorial: Analysis of central and peripheral motor unit " +
            "properties from decomposed High-Density surface EMG signals " +
            "with openhdemg. J Electromyogr Kinesiol. 2024 Feb;74:102850. " +
            "doi: 10.1016/j.jelekin.2023.102850. Epub 2023 Nov 30."
        )

        # Pretty dict printing
        print("\nCite Us:\n")
        print(cite)
        print("\n")

        return cite
