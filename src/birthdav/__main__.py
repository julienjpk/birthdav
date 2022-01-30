#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# birthdav - A tool to synchronise CardDAV birth dates to a CalDAV calendar
# Copyright (C) 2022 Julien JPK <mail@jjpk.me>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

from birthdav.dav import get_client
from birthdav.sync import sync_birthdays

from webdav3.exceptions import ResponseErrorCode
from urllib.parse import urlparse
import sys
import os


class ConfigurationError(Exception):
    """
    Raised when an configuration environment variable is missing
    """
    pass


def get_config():
    """
    Fetches configuration from the environment
    """
    try:
        return {
            "card": {
                "url": urlparse(os.environ["BIRTHDAV_CARD_URL"]).geturl(),
                "user": os.environ.get("BIRTHDAV_CARD_USER"),
                "pass": os.environ.get("BIRTHDAV_CARD_PASS"),
            },
            "cal": {
                "url": urlparse(os.environ["BIRTHDAV_CAL_URL"]).geturl(),
                "user": os.environ.get("BIRTHDAV_CAL_USER"),
                "pass": os.environ.get("BIRTHDAV_CAL_PASS"),
            }
        }
    except ValueError as e:
        msg = "URL parsing error: %s" % str(e)
        raise ConfigurationError(msg)
    except KeyError as e:
        msg = "missing environment variable: %s" % e.args[0]
        raise ConfigurationError(msg)


def main():  # pragma: no cover
    try:
        config = get_config()
        card_client = get_client(config["card"])
        cal_client = get_client(config["cal"])
        sync_birthdays(card_client, cal_client)
    except (ConfigurationError, ResponseErrorCode) as e:
        print(str(e), file=sys.stderr)
        exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()
