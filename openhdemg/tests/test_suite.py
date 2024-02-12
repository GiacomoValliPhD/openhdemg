"""
Use this module to run all the tests. This will take a while.

First, you should dowload all the files necessary for the testing. These might
occupy gigabytes and the dowload might be slow. The files are available at:
https://drive.google.com/drive/folders/1suCZSils8rSCs2E3_K25vRCbN3AFDI7F?usp=sharing

IMPORTANT: Do not alter the content of the dowloaded folder!

Since the library's functions perform complex tasks and return complex data
structures, these tests can verify that no critical errors occur, but the
accuracy of each function must be assessed independently upon creation, or at
each revision of the code.
"""


def test_library_modules():
    pass


def test_compatibility_modules():
    pass


def test_gui_modules():
    pass


if __name__ == "__main__":
    # Change the testfiles_dir as needed.
    testfiles_dir = "C:/Users/Giacomo/Desktop/PhD Padova/Papers Unipd/Open_HD-EMG Docs and Extras/openhdemg_testfiles"

    print("\nTest Started, wait for its completition.\n")

    test_library_modules()
    test_compatibility_modules()
    test_gui_modules()

    print("\nTest Finished!\n")
