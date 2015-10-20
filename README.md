# Python TI83 BASIC converter

A program to convert between source code and TI83/TI84/TI84+/TI84s programs (in
.8xp format).

This is the work of user darkspork from the TI-Basic Developer forums. The
instructions and source code are based on a [forum post from 26 September
2009][0].

## Instructions
This program is written in Python. You'll need that to run this.

 1. Get Python from https://www.python.org
 2. Save these two files in the same directory
 3. Open IDLE (it comes with Python)
 4. Open parse8xp.py
 5. Run it
 6. Type into the command window, to compile or decompile:

    decompile('path/to/FILE.8xp', 'path/to/output/file.txt')
    recompile('path/to/SOURCE',   'path/to/output/file.8xp')

You can also get help on anything by typing

    gethelp('COMMAND YOU WANT HELP ON')

Basically, the point of this is so you can use any text editor to modify your
programs

## License
Citing [the forum post][0]:

    You're free to modify, use, and distribute this code for whatever you want.

Note that parse8xp.py also specifies the "GNU" license, whatever that means.

 [0]: http://tibasicdev.wikidot.com/forum/t-184793/python-ti83-basic-converter.
