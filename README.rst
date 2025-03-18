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


------------------------
Development Installation
------------------------

To install ckanext-metaexport for development, activate your CKAN virtualenv and
do::

    git clone https://github.com/DataShades/ckanext-metaexport.git
    cd ckanext-metaexport
    python setup.py develop
    pip install -r dev-requirements.txt
