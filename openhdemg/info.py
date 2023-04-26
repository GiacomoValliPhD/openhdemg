"""
This module contains all the informations regarding:
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
from textwrap import dedent


class info:
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

        Parameters
        ----------
        emgfile : dict
            The dictionary containing the emgfile.
        """

        if emgfile["SOURCE"] in ["DEMUSE", "OTB", "custom"]:
            print("\nData structure of the emgfile loaded with the function emg_from_otb.")
            print("--------------------------------------------------------------------\n")
            print(f"emgfile type is:\n{type(emgfile)}\n")
            print(f"emgfile keys are:\n{emgfile.keys()}\n")
            print("Any key can be acced as emgfile[key].\n")
            print(f"emgfile['SOURCE'] is a {type(emgfile['SOURCE'])} of value:\n{emgfile['SOURCE']}\n")
            print(f"emgfile['FILENAME'] is a {type(emgfile['FILENAME'])} of value:\n{emgfile['FILENAME']}\n")
            print("MUST NOTE: emgfile from OTB has 64 channels, from DEMUSE 65 (includes empty channel).")
            print(f"emgfile['RAW_SIGNAL'] is a {type(emgfile['RAW_SIGNAL'])} of value:\n{emgfile['RAW_SIGNAL']}\n")
            print(f"emgfile['REF_SIGNAL'] is a {type(emgfile['REF_SIGNAL'])} of value:\n{emgfile['REF_SIGNAL']}\n")
            print(f"emgfile['PNR'] is a {type(emgfile['PNR'])} of value:\n{emgfile['PNR']}\n")
            print(f"emgfile['SIL'] is a {type(emgfile['SIL'])} of value:\n{emgfile['SIL']}\n")
            print(f"emgfile['IPTS'] is a {type(emgfile['IPTS'])} of value:\n{emgfile['IPTS']}\n")
            print(f"emgfile['MUPULSES'] is a {type(emgfile['MUPULSES'])} of length depending on total MUs number.")
            if emgfile['NUMBER_OF_MUS'] > 0:  # Manage exceptions
                print("MUPULSES for each MU can be accessed as emgfile['MUPULSES'][MUnumber].\n")
                print(f"emgfile['MUPULSES'][0] is a {type(emgfile['MUPULSES'][0])} of value:\n{emgfile['MUPULSES'][0]}\n")
            print(f"emgfile['FSAMP'] is a {type(emgfile['FSAMP'])} of value:\n{emgfile['FSAMP']}\n")
            print(f"emgfile['IED'] is a {type(emgfile['IED'])} of value:\n{emgfile['IED']}\n")
            print(f"emgfile['EMG_LENGTH'] is a {type(emgfile['EMG_LENGTH'])} of value:\n{emgfile['EMG_LENGTH']}\n")
            print(f"emgfile['NUMBER_OF_MUS'] is a {type(emgfile['NUMBER_OF_MUS'])} of value:\n{emgfile['NUMBER_OF_MUS']}\n")
            print(f"emgfile['BINARY_MUS_FIRING'] is a {type(emgfile['BINARY_MUS_FIRING'])} of value:\n{emgfile['BINARY_MUS_FIRING']}\n")

        elif emgfile["SOURCE"] == "OTB_refsig":
            print("\nData structure of the emgfile loaded with the function refsig_from_otb.")
            print("-----------------------------------------------------------------------\n")
            print(f"emgfile type is:\n{type(emgfile)}\n")
            print(f"emgfile keys are:\n{emgfile.keys()}\n")
            print("Any key can be acced as emgfile[key].\n")
            print(f"emgfile['SOURCE'] is a {type(emgfile['SOURCE'])} of value:\n{emgfile['SOURCE']}\n")
            print(f"emgfile['FILENAME'] is a {type(emgfile['FILENAME'])} of value:\n{emgfile['FILENAME']}\n")
            print(f"emgfile['FSAMP'] is a {type(emgfile['FSAMP'])} of value:\n{emgfile['FSAMP']}\n")
            print(f"emgfile['REF_SIGNAL'] is a {type(emgfile['REF_SIGNAL'])} of value:\n{emgfile['REF_SIGNAL']}\n")

        else:
            raise ValueError(f"Source '{emgfile['SOURCE']}' not recognised")

    def abbreviations(self):
        """
        Print common abbreviations.
        """

        abbr = {
            "COV": "Coefficient of variation",
            "DERT": "DERecruitment threshold",
            "DD": "Double differential",
            "DR": "Discharge rate",
            "FSAMP": "Sampling frequency",
            "IDR": "Instantaneous discharge rate",
            "IED": "Inter electrode distance",
            "IPTS": "Impulse train per second",
            "MU": "Motor units",
            "MUAP": "MUs action potential",
            "PNR": "Pulse to noise ratio",
            "RT": "Recruitment threshold",
            "SD": "Single differential",
            "SIL": "Silhouette score",
            "STA": "Spike-triggered average",
            "XCC": "Cross-correlation coefficient",
        }

        # Pretty dict printing
        print("\nAbbreviations:\n")
        print(json.dumps(abbr, indent=4))

        return abbr

    def aboutus(self):
        """
        Print informations about the library and the authors.
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
            those not interested in coding thanks to a friendly graphical user
            interface (GUI).

            Both the openhdemg project and its contributors adhere to the Open
            Science Principles and especially to the idea of public release of
            data and other scientific resources necessary to conduct honest
            research.
            """

        us = """
        Us
        --

        People that contributed to the development of this project are:

        Mr. Giacomo Valli:
            The creator of the project and the developer of the library.
            \x1B[3m
            Mr. Giacomo Valli obtained a master degree in Sports Science and a
            research fellowship in molecular biology of exercise at the
            University of Urbino (IT).
            He is currently a PhD student at the University of Padova (IT) in
            neuromuscular physiology.
            He is investigating the electrophysiological modifications
            happening during disuse, disease and aging and linking this
            information to the molecular alterations of the muscle.
            \x1B[0m
        Mr. Paul Ritsche:
            The developer of the GUI.
            \x1B[3m
            Mr. Paul Ritsche obtained a master degree in Sports Science at the
            University of Basel (CH).
            He is currently a research associate at the University of Basel
            (CH) focusing on muscle ultrasonography.
            He is investigating automatic ultrasonography image analysis
            methods to evaluate muscle morphological as well architectural
            parameters.
            \x1B[0m
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
        """

        contact = {
            "Name": "Giacomo Valli",
            "Email": "giacomo.valli@phd.unipd.it",
            "Twitter": "@giacomo_valli",
        }

        # Pretty dict printing
        print("\nContacts:\n")
        print(json.dumps(contact, indent=4))

        return contact

    def links(self):
        """
        Print a collection of useful links.
        """

        link = {
            "Topic": "We are working on this! Stay Tuned",
        }

        # Pretty dict printing
        print("\nLinks:\n")
        print(json.dumps(link, indent=4))

        return link

    def citeus(self):
        """
        Print how to cite the project.
        """

        cite = {
            "Journal": "Waiting for publication...",
            "Title": "Thinking about it...",
        }

        # Pretty dict printing
        print("\nCite Us:\n")
        print(json.dumps(cite, indent=4))

        return cite
# TODO complete infos