################
Primming Backend
################

This is the backend code for the primming extension. It includes:
 - a landing page for the extension (wordpress)
 - a sign up form gathering survey data
 - management interface for the product pages & signup form
 - receive & store the scraped prices from the extensi
 - API to support the extension
 - API to export the gathered data

***************
Getting Started
***************

Checklist:

 #. make sure that you have a reasonably recent version of docker installed & running
 #. make sure you have docker-compose installed
 #. have python 3.9 installed
 #. familiarty with Docker, Python, Django and Linux is assumed

Just like with any other python project setup a virtual environment, use python 3.9 for this. Then
install the requirements using pip:

.. code-block:: shell

    $> pip install -r conf/requirements.txt
    $> pip install -r conf/requirements-dev.txt


Run with Docker
===============

To simple start the entire application stack type:

.. code-block:: shell

   $> docker-compose build
   $> docker-compose up -d

Point your browser to `localhost <https://localhost/>`_ to see the wordpress installation,
or the `Django admin login <https://localhost/obs/bo>`_. You might see a warning about the
SSL certificate since it uses a self-signed one per default.

Import initial data
===================

There are fixtures, located at `conf/fixtures`, you can easily load them from here:

.. code-block:: shell

    (venv) $> PROJECT_ENV=dev PYTHONPATH=src DJANGO_SETTINGS_MODULE=primming.settings fab2 load-fixtures

This will load all the data needed for the basic survey form + the page list and it's scrapers as
needed.

Admin User
==========

You want to create the initial django admin user so that you can access the backoffice tool
located at http://localhost/obs/bo or http://localhost:8000/obs/bo if you run it without docker.

.. code-block:: shell

    $> PROJECT_ENV=dev PYTHONPATH=src DJANGO_SETTINGS_MODULE=primming.settings fab2 createsuperuser

.. note::

    The Django management interface it not located at /admin/ . While we are aware that security through obscurity
    is no security, it at least keeps the many, many, many automated requests to /admin/ that an server in the
    internet experiences out of the log files.

    The actual admin interface is located ad /obs/bo/

Once you've created your super user you should be able to login to Django's admin interface.


Environment variables
======================

You also need to make sure that your environment is set up correctly:

    * PYTHONPATH=src - we're using the default packaging.python.org format with the src folder
    * PRIMMING_ENV=dev - define the config set to be used, based on the environment (dev, stage, prod)
    * DJANGO_SETTINGS_MODULE=primming.settings - required by Django

Export them in your virtualenv's post activation hook to save yourself some typing.

******
Docker
******


This docker-compose.yaml and it's environment specific overrides run a django app in a docker stac
complete with redis cache, celery-queue and a nginx reverse proxy.

The docker-compose files are as commonly used:


* ``docker-compose.yaml`` - the default stack with all the shared services
* ``docker-compose.override.yaml`` - local overrides, will be automatically loaded by
  ``docker-compose``
* ``docker-compose.prod.yaml`` - the overrides for the production environment
* ``docker-compose.test.yaml`` - the overrides for the CI

You can specify which files to load by using multiple ``-f`` parameters. For example, to run the
production stack type ``docker-compose -f docker-compose.yaml -f docker-compose.prod.yaml up -d``

Since ``docker-compose.yaml`` and ``docker-compose.override.yaml`` are automatically loaded if you do
not specify other files with ``-f``\ , you can skip them to run the dev environment and just type
``docker-compose up -d``

For development, you might not always want the uwsgi+nginx stack, but some of the convenience that
Django's runserver command provides (immediately seeing changes to static files & code changes).
This command will run django's development server and exposes it on port 8000:

``docker-compose run -p 8000:8000 webapp bin/python src/ciuvo/portal/manage.py runserver 0.0.0.0:8000```

Services
========

The docker file defines 6 services:

    * database - custom image based the latest MariaDB docker image, some tweaks to the config
    * cache - the latest Redis docker image
    * webapp - custom image containing the python sources for the Django app
    * taskqueue - same image as the webapp, but runs the celery task queue
    * database-wordpress - mysql database backend for wordpress
    * wordpress - a Wordpress image
    * proxy - a nginx reverse proxy, routes everything below the paths `obs`, `survey` and `watcher` to the Django server, everything else to Wordpress. Also terminates HTTPS.

Database service(s)
-------------------

On the ``database`` network, uses ``mysql-pass.txt``\ , ``mysql-rootpw.txt``.

If you do not want a docker-database in production but something like AWS Aurora instead, remove
the service from the ``docker-compose.yaml`` and just have it in the override file.

In the override.yaml it exposes the port ``13306`` so that you can access your database more easily.

Built as a separate image instead of just using a bind mound for the configuration file to allow
deployment with a service like AWS ECS.


Cache
-----

A standard redis image. If you want to use a external cache (like AWS' Elasticache service) in
production, move the service to the override file.

On the ``cache`` network.

WebApp
------

Runs a Django uwsgi instance. You might want to look at ``docker/contexts/webapp/run-django.sh``
to see how it actually starts the server. The image takes the ``$PROJECT_ENV`` environment variable
- if set to ``dev`` it will automatically restart after code changes.

Django 3.2 does not support the ASGI Lifespan protocol. You'll see an exception
in the logs, but it is safe to ignore.

Connected to the ``database``\ , ``cache`` and ``frontend`` network.

Taskqueue
---------

The same as the ``Webapp``\ , but executes ``docker/contexts/webapp/run-celery.sh`` instead.

Connected to the ``database``\ , ``cache`` and ``frontend`` network.

Proxy
-----

Reverse proxy with a custom config file. To allow production deployments without the config files
we used a custom image.

Built as a separate image instead of just using a bind mound for the configuration file to allow
deployment with a service like AWS ECS.

Connected to the ``frontend`` network.

Build contexts
==============

The ``Dockerfile`` build instructions for the custom images are located in the ``docker/contexts/``
directory. For production the images are uploaded to our amazon registry.

The ``.dockerignore`` file specifies directories / files which should not be included in the images.

Secrets
=======

Secrets are stored in the ``docker/secrets`` directory.

Volumes
=======


* ``static-files`` : shared between ``webapp`` and ``nginx`` to allow nginx to serve static files.
   TODO: in development mode the static files should be served by django so that ``manage.py collectstatic``
  is not necessary
* ``certbot-www`` : a volume from which nginx services it's SSL certs. Use ``certbot`` or a similar tool to update the actual SSL certs in production
* ``mysql-db`` : the mysql data volume.

If you want to persist data from the redis-cache, consider using a volume for it as well.


Images
======

To (re)build the images simply type:

.. code-block:: shell

 $> fab2 build-images

If a docker registry is set-up, push the images to it with this command:

.. code-block:: shell

  $> fab2 push-images

You can specify the registry in the ``conf/localsettings.yaml`` file by setting ``DOCKER_REGISTRY``
key to the domain, e.g.  ``DOCKER_REGISTRY: XXXXXXXXX.dkr.ecr.eu-central-1.amazonaws.com``

*****************************
Run the webapp without Docker
*****************************

Install & run Redis and Mysql locally. Create a database for the webapp:

.. code-block:: SQL

    CREATE DATABASE if not exists primmingweb CHARACTER SET utf8 COLLATE utf8mb4;
    CREATE USER if not exists 'primmingweb'@'localhost' IDENTIFIED BY 'primmingw3b';
    GRANT ALL PRIVILEGES ON primmingweb.* TO 'primmingweb'@'localhost';
    GRANT ALL PRIVILEGES ON test_primmingweb.* TO 'primmingweb'@'localhost';


Then add a settings.py override file under ``conf/localsettings.yaml`` containing this:

.. code-block:: yaml

    DATABASES:
      default:
        NAME: 'primmingweb'
        ENGINE: 'django.db.backends.mysql'
        USER: 'primmingweb'
        PASSWORD: 'primmingw3b'
        HOST: '127.0.0.1'
        PORT: '3306'
        TEST:
           CHARSET: 'utf8'
           SERIALIZE: false
        OPTIONS:
            init_command: "SET sql_mode='STRICT_TRANS_TABLES'"


The file is in ignored by git via ``.gitignore``, so you can change settings locally as you like
using this file.

Run the webapp:

.. code-block:: bash

    (venv) $> PYTHONPATH=src DJANGO_SETTINGS_MODULE=primming.settings hypercorn primming.asgi:application -k uvloop --reload
    # Or if you want to make use of the automatic restart feature:
    (venv) $> PYTHONPATH=src DJANGO_SETTINGS_MODULE=primming.settings src/restart.py primming.asgi:application -k uvloop

Import data & create the superuser:

.. code-block:: bash

    (venv) $> PYTHONPATH=src DJANGO_SETTINGS_MODULE=primming.settings fab2 load-fixtures --no-docker
    (venv) $> PYTHONPATH=src DJANGO_SETTINGS_MODULE=primming.settings fab2 createsuperuser --no-docker

Run the tests locally:

.. code-block:: bash

    (venv) $> PYTHONPATH=src DJANGO_SETTINGS_MODULE=primming.settings fab2 test
    # code quality tools
    (venv) $> black src
    (venv) $> isort src
    (venv) $> flake8 src


*******************************
Django Apps / Project Structure
*******************************

 * primming.registration: handle user registration
 * primming.pricewatcher: API for the extension


Registration - App
==================

Specify survey questions, answers. Follow up questions can even rely on previous answers. The
fixtures already load a complex survey-form showcasing all these features.

The survey can be found here ``https://localhost/survey/<UUID-4>`` where the UUID-4 is generated by
the extension and links the extension with the survey form. Example:
``https://localhost/survey/D49BE467-5F3A-4249-A08D-F3C922C77CB4``

The current template loads iframes for header & footers from the wordpress page.
Header: ``https://localhost/jhj/``, Footer: ``https://localhost/jkj/``. Your local Wordpress wizard
must make these pages.


Pricewatcher - App
==================

Specify a list of pages to watch & scrapers to extract price and product title. It also containts
the API endpoints to supply the extension with a list of URLs to visit & the scrapers to use. The
URL-list and the scraper are two separate API calls since initialy the scraper was supplied by the
Ciuvo API.

``https://localhost/survey/D49BE467-5F3A-4249-A08D-F3C922C77CB4``

**********
Production
**********

Some notes on deploying it to produciton in an AWS environment.

AWS Container registry
======================

To work with AWS you need to configure the ``compose-cli`` to work with your credentials.


~/.aws/config:
.. code-block:: ini

    [default]
    ...

    [primming]
    region = eu-central-1

~/.aws/credentials:


.. code-block:: ini

    [default]
    ...

    [primming]
    aws_access_key_id = ******
    aws_secret_access_key = *****

Login to the AWS ECR (Elastic Container Registry) docker registry

.. code-block:: shell

        $> aws ecr get-login --profile primming --no-include-email --region eu-central-1
        # copy & paste the output

If you rebuild images you tag & push images like this:

.. code-block:: shell

    (venv) $> docker tag primming/webapp:2021.02.11.1234 XXXXXXXXX.dkr.ecr.eu-central-1.amazonaws.com/primming/webapp:2021.02.11.1234
    (venv) $> docker push XXXXXXXXXXX.dkr.ecr.eu-central-1.amazonaws.com/primming/webapp:2021.02.11.1234

(Replace the ``XXXXXXXXXXX.dkr.ecr.eu-central-1.amazonaws.com`` with the docker registry you're
using.)

However the fabric2 task also does the trick:

.. code-block:: shell

    (venv) $> PRIMMING_ENV=prod fab2 build-images --push


Deployment & Updates
====================

Build a debian package (not supported by external partners, as it relies on a private repo)

.. code-block:: shell

    (venv) $> PRIMMING_ENV=prod fab2 build -H ubuntu@stage01.int.kjuvo.com


Install on the host:

.. code-block:: shell

    (venv) $> sudo apt-get update && sudo apt-get install primming-backend

Even if you're not using the debian package for deployment useful systemd unit files & crontab
settings can be found in the `debian` directory.


***********************
Ciuvo Scraping Language
***********************

The Ciuvo Scraping Language (CSL) is a domain specific language designed for
client-side web page scraping. The language provides scraping facilities such
as XPath, CSS3 selectors (via jQuery/sizzle),
regular expressions and programmatic primitives such as loops,
conditional statements, arithmetic and logical expressions.

Here is an example of how CSL looks like::

  $price = sizzle('td > *.priceLarge')
  $isbn = re('<li><b>ISBN-13:</b>(.+)<')
  $title = sizzle('span#btAsinTitle', 'textContent')

  require $title, $price
  return $title, $price, $isbn


Program structure
=================

CSL comprises three basic symbols:

  * **Statements** which modify (global) state.
  * **Expressions** which are evaluated to yield values.
  * **Literals** which represent constants.

A CSL program is basically a list of statements with a mandatory return statement
at the end.

.. productionlist::
   program: statement+ return_stmt
   statement: assignment_stmt | for_in_stmt | if_stmt | require_stmt | stmt_expr | noop_stmt
   return_stmt: "return" variable_expr ("," variable_expr)*
   variable_expr: "$" name
   name: (letter|"_")+

Statements
==========

CSL provides the following `statements`.

Assignment Statement
--------------------

An assignment statement evaluates the expression on the right-hand-side and
assigns the result to the variable. The expression on the right-hand-side can
be any expression or literal. There are numeric and string literals, strings can
be either single quote or double quote.

.. productionlist::
   assignment_stmt: variable_expr assignment_op logical_or_expr
   assignment_op: "=" | "+=" | "-=" | "*=" | "/=" | "%="

Expressions build a recursive production structure to allow operator
priorities (e.g. logical before equality before relational before arithmetic).
The same rules as in JavaScript operator priority apply.
``logical_or_expr`` is the root of this recursive structure.

For In Statement
----------------

A for loop that can be used to loop over the elements in a collection:

.. productionlist::
   for_in_stmt: "for" "(" variable_expr "in" expression ")" (statement | block)
   block: "{" statement+ "}"

Here is a simple CLS example::

  $price = ''
  for($i in '012345') {
    $price += $i
  }

If Statement
------------

Conditional if then else statement.

.. productionlist::
   if_stmt: "if" "(" expression ")" (statement | block)
          : ["else" (statement | block)]


Here is a simple CLS example::

  $price = ''
  if($price) {
    $price += 'never happens'
  }

Require Statement
-----------------

A require statement is used to check whether a list of variable
expressions is defined (similar to an assert statement). If one
variable is not defined it will throw an exception with name
`'RequiredError'`.

.. productionlist::
   require_stmt: "require" variable_expr ["," variable_expr]+

Expressions
===========

Variable Expression
-------------------

Variable expressions are simply variables (i.e. when you evaluate a variable
expression you get its value).

Recursive Expression Structure
------------------------------

Expressions build a recursive production structure to allow operator
priorities.

.. note:: Parsing priority and evaluation priority are reversed.
          I.e. the parser first tries to parse logical operator expressions
          than arithemtic which means that arithmetic operators are evaluted
          _before_ logical ones.

The parser first tries to parse (binary) operator expressions starting with
logical expression (``or`` or ``and``).
The next level is equality (``==``).

.. warning:: Unfortunately, not equals ``!=`` is _not_ supported yet (CSL 2.0).

.. NOTE:: You can emulate ``!=`` easily with "not ($lhs == $rhs)".

The next level are relational expressions (``<=``, ``>=``, ``<``, ``>``).

The next level are arithmetic expressions - first additive (``+``, ``-``)
than multiplicative (``*``, ``/``).

Next, unary operator expressions are parsed (``+``, ``-``, ``~``, ``not``).

.. warning:: Operators are a Javascript/Python mix - we support Python's ``not``
          instead of JS' ``!`` - I appoligize for that! BTW: Nowbody knows
          what ``~`` is good for - please, don't use it.

Next are accessor expressions (``[ ]``) which are used for accessing array
elements.

.. note:: We support indexing via negative indices ala Python. E.g. ``foo[-1]``
          gives you the last element of ``foo``.

The final level is ``expr`` which is either a ``call_expr``, a ``variable_expr``
or a ``literal``.
Call expressions (``()``) implement functions calls. Functions are stored
in a dedicated function table.

Here are the production rules of the grammer for parsing expressions.

.. productionlist::
   logical_or_expr: logical_and_expr ("or" logical_and_expr)*
   logical_and_expr: equals_expr ("and" equals_expr)*
   equals_expr: relational_expr ("==" relational_expr)*
   relational_expr: add_expr (">" | "<" | ">=" | "<=" add_expr)*
   add_expr: mul_expr ("+" | "-" mul_expr)*
   mul_expr: unary_expr ("*" | "/" | "%" unary_expr)*
   unary_expr: access_expr
             : | expr
             : | "+" | "-" | "~" | "not" expr
   access_expr: expr "[" logical_or_expr  "]"
   expr: call_expr
       : | variable_expr
       : | literal
   call_expr: name "(" expr* ")"
   literal: numeric_literal
          : | string_literal
          : | re_literal
          : | array_literal
          : | bool_literal
          : | null_literal
   numeric_literal: float_literal | integer_literal
   string_literal: double_quote_literal | single_qoute_literal
   re_literal: "/" [^/]* "/"


More detailed information about some of the expressions can be found below.


Arithmetic Expression
---------------------

Basic arithmetic expressions - the Javascript rules apply (multiplication
is evaluated before addition).

Here is an example::

  $price = 1.0 + 2.0 * 3.0

Call Expressions
----------------

Call expressions are generic function calls.

Example::

  $title = sizzle('title')

This calls the function ``sizzle`` with the string literal ``'title'`` as parameter.


CSL Functions
=============

CSL support the following functions:

atLeastVersion
--------------

.. parsed-literal:: atLeastVersion(version)

Returns True if interpreter version is at least ``version``.

const
-----

.. parsed-literal:: const(val)

Return the constant ``val``.

debug
-----

.. parsed-literal:: debug(arg, ...)

debug() logs output to `com.ciuvo.log` (usually the browsers debug
console). It accepts any number of arguments.

httpGet
-------

.. parsed-literal:: httpGet(url)

Async HTTP GET request, returns response text on status code 200.

join
----

.. parsed-literal:: join(values, joiner)

Join array ``values`` with string ``joiner``.

re
--

.. parsed-literal:: re(regex, flags[, text])

Evaluate a JS regular expression on the HTML content of the scraped page.

This function directly uses javascripts builtin regular expression
functionality.

.. seealso:: http://www.w3schools.com/jsref/jsref_obj_regexp.asp

**Parameters:**

regex (str or regex)
   The regular expression to use.
flags (str)
   Regular expression flags. Either ``i``, ``g`` or ``gi``, we do **not**
   support the ``m`` flag:

   ``i``
      Case insensitive match
   ``g``
      Return all matches (instead of just the first one).
text (str, optional)
   The text of interest. If not present, use the HTML of the current document.

**Production list:**

.. productionlist::
   regex_expr: "re" "(" (string_literal | regex_literal) ("," flags)? ("," html)? ")"
   regex_literal: "/" [^"/"]* "/"
   flags: "i" | "g" | "gi"
   html: variable_expr | string_literal

refresh
-------

.. parsed-literal:: refresh(interval)

Periodically re-run interpreter every ``interval`` seconds.

.. NOTE:: The result of the scraper is usually only displayed in the console
   (and sent to the server) if the result changes.

replace
-------

.. parsed-literal:: replace(str, pattern, sub, ...)

Replace ``pattern`` in ``str`` with ``sub``. Can have more than one (pattern,
sub) pair.

sizzle
------

.. parsed-literal:: sizzle(selector[, attribute])

Evaluates a CSS3 selector expression on the DOM using `Sizzle <http://sizzlejs.com/>`_ .

**Parameters:**

selector (str)
   A fully CSS3 compliant selector.
attribute (str, optional)
   Do not return full node, but only the given attribute. If ``textContent`` is
   passed, it returns the text content - but not any child elements.

**Returns:**

If the given expression matches more than once a match array is returned,
otherwise a string is returned.

**Examples:**

.. code-block:: html

   <h1 class="foo">some title<span class="bar">nested span</span></h1>

.. code-block:: javascript

   sizzle('h1', 'class')
   // out: foo

   sizzle('h1')
   // out: some title<span class="bar">nested span</span>

   sizzle('h1', 'textContent')
   // out: some title

We also support `CSS3 attribute selectors
<http://www.impressivewebs.com/css3-attribute-selectors-substring-matching/>`_,
and most other CSS3 features, for example:

.. code-block:: html

   <div>
       <a href="https://maps.google.com/...."></a>
       <a href="https://maps.google.com/...."></a>
   </div>

.. code-block:: javascript

   > sizzle('a[href^="https://maps.google.com"]', 'href')
   ['https://maps.google.com/...', 'https://maps.google.com/...']

   > sizzle('a[href^="https://maps.google.com"]:first', 'href')
   https://maps.google.com/...

Here is an example::

  $price = sizzle('td > *[class="priceLarge"]')
  $asin = sizzle('input[id="ASIN"]', 'value')

**Production list:**

.. productionlist::
   css_expr: "sizzle" "(" string_literal ("," val_selector_expr) ")"
   val_selector_expr: variable_expr | string_literal

trim
----

.. parsed-literal:: trim(str)

Trims whitespaces (left and right).

url
---

.. parsed-literal:: url()

Returns document.location.href.

urlParam
--------

.. parsed-literal:: urlParam(param)

Returns the value of the HTTP GET parameter ``param``.

.. WARNING:: This method currently does not handle anchors.

   .. code-block:: javascript

      // url = https://example.com/path?param1=value1&param2=value2#anchor-text
      urlParam('param1')
      // value1
      urlParam('param2')
      // value2#anchor-text

version
-------

.. parsed-literal:: version()

Return the CSL version.

wait
----

.. parsed-literal:: wait(delay)

Waits ``delay`` milli seconds.

xpath
-----

.. parsed-literal:: xpath(xpath_expr)

.. WARNING:: We generally don't use this any more, because Internet Explorer has
   no proper XPATH engine.

Evaluate a XPath expression on the DOM of the scraped page.

.. productionlist::
   xpath_expr: "xpath" "(" string_literal ")"

Returns the string value of the first match of the XPath expression or an empyt string.
