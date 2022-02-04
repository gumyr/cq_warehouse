############
Installation
############
Install from github:

.. code-block:: bash

	python3 -m pip install git+https://github.com/gumyr/cq_warehouse.git#egg=cq_warehouse

Note that cq_warehouse requires the development version of cadquery (see
`Installing CadQuery <https://cadquery.readthedocs.io/en/latest/installation.html>`_). Also
note that cq_warehouse uses the pydantic package for input validation which
requires keyword arguments (e.g. ``num_teeth=16``).
