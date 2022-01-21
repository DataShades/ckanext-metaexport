==================
ckanext-metaexport
==================

`ckanext-metaexport` proviedes universal way to export dataset's metadata into different metadata standards.

All formats should be registered before using. In order to do this, perform next steps:

1. Implement `ckanext.metaexport.interfaces.IMetaexport` interface.
2. Add `register_metadata_format`, that returns dictonary with format names as keys and FormatInstances as values.
3. Add dataExtractors - method that provides function for generating data, that'll be passed into templates. It can be done via `register_data_extractors` method, that receives current formatters list and should pick desired format from collection and call `set_data_extractor` of this format. `set_data_extractor` expects to receive one argument - function, that will receive package_id and should return dictonary with template variables.
5. In order to create your own format, you have to create class, inherited from `ckanext.metaexport.formatters.Format`

All export views are available under `/dataset/{id}/metaexport/{format}` URL.

------------
Requirements
------------

For example, you might want to mention here which versions of CKAN this
extension works with.


------------
Installation
------------

.. Add any additional install steps to the list below.
   For example installing any non-Python dependencies or adding any required
   config settings.

To install ckanext-metaexport:

1. Activate your CKAN virtual environment, for example::

     . /usr/lib/ckan/default/bin/activate

2. Install the ckanext-metaexport Python package into your virtual environment::

     pip install ckanext-metaexport

3. Add ``metaexport`` to the ``ckan.plugins`` setting in your CKAN
   config file (by default the config file is located at
   ``/etc/ckan/default/production.ini``).

4. Restart CKAN. For example if you've deployed CKAN with Apache on Ubuntu::

     sudo service apache2 reload


---------------
Config Settings
---------------

Document any optional config settings here. For example::

    # The minimum number of hours to wait before re-checking a resource
    # (optional, default: 24).
    ckanext.metaexport.some_setting = some_default_value


------------------------
Development Installation
------------------------

To install ckanext-metaexport for development, activate your CKAN virtualenv and
do::

    git clone https://github.com/DataShades/ckanext-metaexport.git
    cd ckanext-metaexport
    python setup.py develop
    pip install -r dev-requirements.txt




-----------------
Running the Tests
-----------------

To run the tests, do::

    nosetests --nologcapture --with-pylons=test.ini

To run the tests and produce a coverage report, first make sure you have
coverage installed in your virtualenv (``pip install coverage``) then run::

    nosetests --nologcapture --with-pylons=test.ini --with-coverage --cover-package=ckanext.metaexport --cover-inclusive --cover-erase --cover-tests


---------------------------------
Registering ckanext-metaexport on PyPI
---------------------------------

ckanext-metaexport should be availabe on PyPI as
https://pypi.python.org/pypi/ckanext-metaexport. If that link doesn't work, then
you can register the project on PyPI for the first time by following these
steps:

1. Create a source distribution of the project::

     python setup.py sdist

2. Register the project::

     python setup.py register

3. Upload the source distribution to PyPI::

     python setup.py sdist upload

4. Tag the first release of the project on GitHub with the version number from
   the ``setup.py`` file. For example if the version number in ``setup.py`` is
   0.0.1 then do::

       git tag 0.0.1
       git push --tags


----------------------------------------
Releasing a New Version of ckanext-metaexport
----------------------------------------

ckanext-metaexport is availabe on PyPI as https://pypi.python.org/pypi/ckanext-metaexport.
To publish a new version to PyPI follow these steps:

1. Update the version number in the ``setup.py`` file.
   See `PEP 440 <http://legacy.python.org/dev/peps/pep-0440/#public-version-identifiers>`_
   for how to choose version numbers.

2. Create a source distribution of the new version::

     python setup.py sdist

3. Upload the source distribution to PyPI::

     python setup.py sdist upload

4. Tag the new release of the project on GitHub with the version number from
   the ``setup.py`` file. For example if the version number in ``setup.py`` is
   0.0.2 then do::

       git tag 0.0.2
       git push --tags
