inputexec
=========

This program aims to handle button/command binding for headless hosts.
It captures all events from an input device (keyboard, mouse, etc.) and runs commands appropriately.

inputexec was born from the need to pass key presses from a remote control to a Music Player Daemon.


Example usage:

.. code-block:: sh

    inputexec --action-commands=actions.ini --source-file=/dev/input/keyboard

The ``--action-commands`` file contains action to map to each keypress:

.. code-block:: ini

    [commands]
    keypress.KEY_PLAYPAUSE = mpc toggle
    keypress.KEY_PREVIOUSSONG = mpc prev
    keypress.KEY_NEXTSONG = mpc next
    keypress.KEY_STOPCD = mpc stop


Installation
------------

inputexec is distributed under the 2-clause BSD license, and needs Python 2.6-3.3

Distribution packages (recommended)
"""""""""""""""""""""""""""""""""""

Use distribution-specific packages if they are available.
The author knows of the following options:

* None yet


From PyPI, the Python package index
"""""""""""""""""""""""""""""""""""

Simply run:

.. code-block:: sh

    pip install inputexec


From source
"""""""""""

You'll need the python-evdev_ library, available from PyPI (https://pypi.python.org/pypi/evdev).

Then, run:

.. code-block:: sh

    git clone https://github.com/rbarrois/evdev.git


Launcing and configuration
--------------------------

inputexec uses only optional arguments; the full list is available through ``inputexec --help``.

All options may also been read from a configuration file passed as ``inputexec --config /path/to/example.ini``.
The list of valid options for the configuration files are available through ``inputexec --dump-config``.


Configuring actions
-------------------

Finding the symbol associated with each key press may be complicated; to solve that problem,
inputexec can run in ``print`` mode:

.. code-block:: sh

    inputexec --source-file=/dev/input/event0 --action-mode=print


Now, each keypress will be displayed on stdout:

.. code-block:: ini

    keypress.KEY_PLAYPAUSE
    keypress.KEY_PREVIOUSSONG
    keypress.KEY_NEXTSONG
    keypress.KEY_STOPCD


Executing actions
-----------------

Three action modes are available, configured through ``--action-mode``:

* ``print``: described above, simply print event lines to stdout
* ``run_sync``: whenever an event occurs, the related command is called;
  this blocks the program
* ``run_async``: One or more threads are started (the number is defined by
  ``--action-jobs``) and commands to run are dispatched between those threads.


Input
-----

inputexec can read from stdin, from a file or from a character device.

For stdin, simply pass ``--source-file=-``

If another file path is provided, inputexec will look at its type and,
if the file is a device node with major 13 (i.e an input device on linux),
use the ``evdev`` reader.
A linux input device can be opened either in ``shared`` mode
(events are propagated to all other readers) or in ``exclusive`` mode;
this behaviour is controlled by the ``--source-mode=exclusive|shared`` flag.

Otherwise, events will be generated from the lines of the file.


Logging and debug
-----------------

inputexec provides a few options for logging, controlled by the ``--logging-target`` flag:

Syslog
  With ``--logging-target=syslog``, all messages are sent to syslog

stderr
  With ``--logging-target=stderr``, data is written to stderr

file
  With ``--logging-target=file --logging-file=FILE``, logs are appended to FILE


Logging verbosity can be adjusted through ``--logging-level=``.
The ``--traceback`` option enables dumping full (Python) stack upon exceptions.


Running as non-root daemon
--------------------------

By default, input devices in ``/dev/input`` can only be accessed by ``root:root``.

Users are advised to setup a dedicated user/group for inputexec, and to give
read/write to the target device to that user.

Giving access to the device is often a ``udev`` configuration task.

First, find the ID of your device; look at ``/dev/input/by-id`` and ``/dev/input/by-path``,
which provide stabler names than ``/dev/input/event3``.

Once you've found your device (you may also look at ``lsusb``, kernel logs when plugging/unplugging, etc.),
you'll need some rules for udev to find it:

.. code-block:: sh

    $ udevadm info --attribute-walk --name=/dev/input/by-id/usb-13ec_0006-event-kbd

You'll get lots of lines, focus on the 2-3 first blocks, and try to find attributes
specific to your device; for me, this was::

      SUBSYSTEMS=="input"
      ATTRS{idVendor}=="13ec"
      ATTRS{idProduct}=="0006"


You can now write the udev rule, for instance into ``/etc/udev/rules.d/80_setup_inputexec.rules``:

.. code-block:: sh

    # Include the matching attributes first (with ==), then force mode and group.
    SUBSYSTEM=="input", ATTRS{idVendor}=="13ec", ATTRS{idProduct}=="0006", MODE="660", GROUP="rcinput"

Now, unplug/replug your device and check that permissions on the target ``/dev/input/eventX``
match your expectations.


Contributing, reporting issues
------------------------------

If you find an issue or have suggestions for improvements, feel free to contact me:

* Open an issue on `GitHub <https://github.com/rbarrois/inputexec/issues>`_
* Send me an email at raphael.barrois+inputexec@polytechnique.org
* Ping me on IRC, I'm Xelnor on irc.freenode.net


TODO
----

This section lists features, improvements and other ideas to implement.

* Port to BSD kernel
* Add exhaustive unit testing
* Write man page and init.d service definitions


Links
-----

Source code and issues:
  https://github.com/rbarrois/inputexec

PyPI:
  http://pypi.python.org/pypi/inputexec

Documentation:
  http://inputexec.readthedocs.org/en/latest (not yet)


.. _python-evdev: http://pythonhosted.org/evdev/
