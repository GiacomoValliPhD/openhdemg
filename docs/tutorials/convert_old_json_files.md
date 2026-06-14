As *openhdemg* evolves and introduces new features, migrating to the latest version becomes essential for leveraging optimized functions and improved capabilities. However, it is not always possible to implement new or optimized functionalities without altering the utilized data structure.

When the data structure is changed, the users of previous versions of *openhdemg* will not be able to access the newer functionalities with the files *they* saved in the older data structure. To overcome this limitation, we created the `convert_json_output` class which facilitates a seamless transition by converting older .json files to the format compatible with the latest *openhdemg* version.

This tutorial guides you through the process, ensuring a smooth upgrade while maintaining data integrity.

Why should you convert your files to the newer *openhdemg* versions?

- Optimized Functionality: Newer *openhdemg* versions come with optimized functions, enhancing performance and providing a more efficient user experience.
- Compatibility: Ensure your data remains compatible with the latest features and improvements introduced in *openhdemg*.

## From v0.1.x JSON files to v0.2.0 modules

Version 0.2.0 keeps the JSON loading functions for compatibility, but the recommended save/load workflow is now based on binary modules and collections.

If your old JSON file can be loaded directly with `emg_from_json()`, you can migrate it to the new module format without using the compatibility converter:

```Python
import openhdemg.library as emg

old_emgfile = emg.emg_from_json(
    filepath="C:/Users/.../Desktop/old_file.json",
)

old_emgfile = emg.standardise_emgfile_dtypes(old_emgfile)

emg.save_openhdemg_module(
    emgfile=old_emgfile,
    path="C:/Users/.../Desktop/openhdemg_modules",
    module_name="old_file_converted",
)
```

You can then load it with:

```Python
converted = emg.load_openhdemg_module(
    path="C:/Users/.../Desktop/openhdemg_modules",
    module_name="old_file_converted",
)
```

Use the compatibility converter below only when a file was saved with an older data structure that cannot be opened directly by the current loaders.

## From 0.1.0-b2 to 0.1.0-b3

The *openhdemg* version 0.1.0-beta.3 introduced noticeable [changes and improvements](../what's-new.md#010-beta3), particularly regarding the speed of saving and loading of .json files. Furthermore, these files are efficiently compressed, so that they occupy less space in your storage. However, to achieve this goal, it was necessary to optimise the default data structure used by *openhdemg* and, as a consequence, the newer *openhdemg* version is not compatible with the files saved from previous *openhdemg* versions.

In this section of the tutorial we explain how to easily convert the files you saved from *openhdemg* version 0.1.0-beta.2 to make them compatible with *openhdemg* version 0.1.0-beta.3.

The class necessary to perform this conversion is stored in the [conversions module](../api_compatibility.md) inside the compatibility subpackage and can be imported as

```Python
# Import the necessary libraries
from openhdemg.compatibility import convert_json_output
```

With this class, we can select different methods for converting our files.

Let's start from the easiest one. Indeed, we can convert one file (or perform a batch conversion of multiple files) with a simple graphical user interface (GUI). If you want to convert one file, select the desired file, if you want to convert more files, select more of them.

```Python
# Import the necessary libraries
from openhdemg.compatibility import convert_json_output

# Convert file/s appending "converted" to the name of the converted file.
convert_json_output(gui=True, append_name="converted")
```

Alternatively, you can perform the tasks without GUI. In the following example you will convert all the files in a folder and save them in the same location with a different name.

```Python
# Import the necessary libraries
from openhdemg.compatibility import convert_json_output

# Specify the path to the folder where the original files are and where the
# converted ones should be.
old = "C:/Users/.../test conversions/"
new = "C:/Users/.../test conversions/"

# Convert them
convert_json_output(
    old=old,
    new=new,
    append_name="converted",
    gui=False,
)
```

For more options, please refer to the documentation of the [convert_json_output](../api_compatibility.md#openhdemg.compatibility.conversions.convert_json_output) class.

## More questions?

We hope that this tutorial was useful. If you need any additional information, do not hesitate to read the answers or ask a question in the [*openhdemg* discussion section](https://github.com/GiacomoValliPhD/openhdemg/discussions){:target="_blank"}. If you are not familiar with GitHub discussions, please read this [post](https://github.com/GiacomoValliPhD/openhdemg/discussions/42){:target="_blank"}. This will allow the *openhdemg* community to answer your questions.