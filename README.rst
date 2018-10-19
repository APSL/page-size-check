=========
Page Size Check
=========

Page Size Check is an utility to check the size of pages from a sitemap and its resources parsering the HAR file of the
request using Selenium and haralyzer. The execution of this utility produces some files to allow the user to make an
analysis of the number of requests and its size. The execution use ThreadPoolExecutor to launch the browsers in parallel.

Dependencies
------------

* Git.
* Python 3.5 or higher, `pip`_ and virtualenvwrapper.
* System requeriments in requirements-sys.txt

Installation
------------

Nowadays the project is only available on github.

#. Clone project from repo ::

    git clone git@github.com:APSL/page-size-check.git

#. Setup virtualenv Python ::

    cd page_size_check
    mkvirtualenv "page_size_check" -p python3 -a .
    pip install -r requirements.txt

#. Branches ::

    master --> prod env. Bug issues start from here.

#. Download ::

    - Firefox webdriver for selenium: geckodriver
    - Browsermob-proxy

#. Execution ::

    python page_size_check.py --sitemap_url="sitemap.url" [--help]

#. Output ::

    - Resume urls file: a resume of the urls with the number of entries, the page size and the page load times
    - Resources list file: a list of the resources on every page with its mimetype, size and load time
    - Mimetype resources: a resume of the resources grouped by mimetype in each url of the sitemap



Usage
-----
As was showned before, you can execute the script doing :code:`python page_size_check.py --help` to see all the
parameters that you can set:

--browsermob_server_path TEXT  Browsermob Server Path.
--firefox_driver_path TEXT     Firefox Driver Path.
--sitemap_url TEXT             Sitemap to get urls.
--threads INTEGER              Number of threads.
--help                         Show this message and exit.

Contributing
------------

Contributions are very welcome. Please open a `pull request`_ or `file an issue`_.
Tests will be ready as soon as posible, please ensure the coverage at least stays the same
before you submit a pull request.

License
-------

Distributed under the terms of the `MIT`_ license, "page-size-check" is free and open source software


Issues
------

If you encounter any problems, please `file an issue`_ along with a detailed description.

.. _`pip`: https://pypi.python.org/pypi/pip/
.. _`pull request`: https://github.com/APSL/page-size-check/pulls
.. _`file an issue`: https://github.com/APSL/page-size-check/issues
.. _`MIT`: http://opensource.org/licenses/MIT