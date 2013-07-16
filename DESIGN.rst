Code design
===========


This project, besides its actual usefulness, is also an exercise in conceiving
a versatile and configurable project.


Components
----------

Each atomic feature (reading lines, filtering them, running commands, ...)
should be handled by a dedicated component.


Configuring components
""""""""""""""""""""""

All configuration should be passed exclusively through keyword arguments.
This avoids ambiguous arguments meaning (depending on the called component), etc.


Dependency injection
""""""""""""""""""""

Favor composing over inheritance: inheritance is strictly reserved to
"provide an alternative implementation of the base class", and should never
exceed two levels.

If a component needs a feature that is not exactly is role, or may be used
by its sibling, create a new component for that feature and that.


Module layout
-------------

The idea is to have one module per component, with all variations in the same
module.

The more complex layout of:

.. code-block:: sh

    components/
        __init__.py
        base.py
        back1.py
        back2.py

should only be used when some components have additional, non-stdlib dependencies.
