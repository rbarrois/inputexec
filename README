inputexec
=========

This program aims to handle button/command binding for headless hosts.
It captures all events from an input device (keyboard, mouse, etc.) and runs commands appropriately.

inputexec was born from the need to pass key presses from a remote control to a Music Player Daemon.


Example usage:

.. code-block:: sh

    inputexec --config=actions.ini /dev/input/keyboard


Installation
------------

Distribution packages (recommended)
"""""""""""""""""""""""""""""""""""

Use distribution-specific packages if they are available.
The author knows of the following options:

* None yet


From PyPI
"""""""""

Simply run:

.. code-block:: sh

    pip install inputexec


From source
"""""""""""

You'll need the python-evdev_ library, available from PyPI (https://pypi.python.org/pypi/evdev).

Then, run:

.. code-block:: sh

    git clone https://github.com/rbarrois/evdev.git


Running
-------

inputexec takes a mandatory argument, ``device``: the ``/dev/input/`` device to read from.

Most configuration options can be passed either from the command line or from a configuration file.
Please use ``inputexec --help`` to get a list of available options.


Links
-----

Source code and issues:
  https://github.com/rbarrois/inputexec

PyPI:
  http://pypi.python.org/pypi/inputexec

Documentation:
  http://inputexec.readthedocs.org/en/latest


.. _python-evdev: http://pythonhosted.org/evdev/
