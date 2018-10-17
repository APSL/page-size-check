=========
Page Size Check
=========

Dependencies
------------

* Git.
* Python 3.5 or higher, pip and virtualenvwrapper.
* System requeriments in requirements-sys.txt

Installation and run
--------------------

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

