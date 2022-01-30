## BirthDAV

A CLI tool to fetch contacts from a CalDAV server and upload the associated birthday events to a CalDAV server.


### Installation

BirthDAV can be packaged and installed like any other Python package:

    $ python -m build .
    $ pip install dist/*.whl


### Usage

BirthDAV does not take any command-line parameters. Before you run it, simply make sure the following environment variables are set:

| Variable             | Description                                                    |
| -------------------- | -------------------------------------------------------------- |
| `BIRTHDAV_CARD_URL`  | URL to the CardDAV address book holding the contacts           |
| `BIRTHDAV_CARD_USER` | *Optional* - Username for CardDAV authentication, if necessary |
| `BIRTHDAV_CARD_PASS` | *Optional* - Password for CardDAV authentication, if necessary |
| `BIRTHDAV_CAL_URL`   | URL to the CalDAV address book holding the contacts            |
| `BIRTHDAV_CAL_USER`  | *Optional* - Username for CalDAV authentication, if necessary  |
| `BIRTHDAV_CAL_PASS`  | *Optional* - Password for CalDAV authentication, if necessary  |
