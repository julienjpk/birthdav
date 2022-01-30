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

from unittest.mock import patch
import unittest

import os

from birthdav.__main__ import get_config, ConfigurationError


class TestEntryPoint(unittest.TestCase):
    def test_missing_card_url(self):
        msg = "did not fail on missing BIRTHDAV_CARD_URL"
        with self.assertRaisesRegex(ConfigurationError,
                                    "missing environment variable",
                                    msg=msg):
            get_config()

    @patch.dict(os.environ, {"BIRTHDAV_CARD_URL": "http://foo"})
    def test_missing_cal_url(self):
        msg = "did not fail on missing BIRTHDAV_CAL_URL"
        with self.assertRaisesRegex(ConfigurationError,
                                    "missing environment variable",
                                    msg=msg):
            get_config()

    @patch.dict(os.environ, {
        "BIRTHDAV_CARD_URL": "http://invalid[url/foo",
        "BIRTHDAV_CAL_URL": "http://invalid[url/foo",
    })
    def test_invalid_card_url(self):
        msg = "did not fail on invalid BIRTHDAV_CARD_URL"
        with self.assertRaisesRegex(ConfigurationError,
                                    "URL parsing error",
                                    msg=msg):
            get_config()

    @patch.dict(os.environ, {
        "BIRTHDAV_CARD_URL": "http://invalid[url/foo",
        "BIRTHDAV_CAL_URL": "http://invalid[url/foo",
    })
    def test_invalid_cal_url(self):
        msg = "did not fail on invalid BIRTHDAV_CAL_URL"
        with self.assertRaisesRegex(ConfigurationError,
                                    "URL parsing error",
                                    msg=msg):
            get_config()

    @patch.dict(os.environ, {
        "BIRTHDAV_CARD_URL": "http://foo",
        "BIRTHDAV_CAL_URL": "http://foo"
    })
    def test_ok_no_auth(self):
        try:
            config = get_config()
        except ConfigurationError:
            self.fail("failed even though the URLs were supplied")

        expectations = (
            ("card", "url", "http://foo"),
            ("card", "user", None),
            ("card", "pass", None),
            ("cal", "url", "http://foo"),
            ("cal", "user", None),
            ("cal", "pass", None),
        )

        for k1, k2, v in expectations:
            if v is None:
                self.assertIs(
                    config[k1][k2], None,
                    msg="unexpected value for %s %s: %s" % (k1, k2, v)
                )
            else:
                self.assertEqual(
                    config[k1][k2], v,
                    msg="wrong value for %s %s: %s" % (k1, k2, v)
                )

    @patch.dict(os.environ, {
        "BIRTHDAV_CARD_URL": "http://foo",
        "BIRTHDAV_CARD_USER": "foo",
        "BIRTHDAV_CARD_PASS": "bar",
        "BIRTHDAV_CAL_URL": "http://baz",
        "BIRTHDAV_CAL_USER": "qux",
        "BIRTHDAV_CAL_PASS": "quux",
    })
    def test_ok_auth(self):
        try:
            config = get_config()
        except ConfigurationError:
            self.fail("failed even though the URLs were supplied")

        expectations = (
            ("card", "url", "http://foo"),
            ("card", "user", "foo"),
            ("card", "pass", "bar"),
            ("cal", "url", "http://baz"),
            ("cal", "user", "qux"),
            ("cal", "pass", "quux"),
        )

        for k1, k2, v in expectations:
            if v is None:
                self.assertIs(
                    config[k1][k2], None,
                    msg="unexpected value for %s %s: %s" % (k1, k2, v)
                )
            else:
                self.assertEqual(
                    config[k1][k2], v,
                    msg="wrong value for %s %s: %s" % (k1, k2, v)
                )
