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

from ssl import DefaultVerifyPaths
import os

from birthdav.dav import get_requests_verify


class TestDAVSSL(unittest.TestCase):
    @patch("platform.system")
    def test_ssl_windows(self, system_mock):
        system_mock.return_value = "Windows"
        verify = get_requests_verify()
        self.assertTrue(system_mock.called)
        self.assertIs(verify, True)

    @patch.dict(os.environ, {"REQUESTS_CA_BUNDLE": "/requests_ca_bundle"})
    def test_ssl_requests_ca_bundle(self):
        self.assertEqual(get_requests_verify(), "/requests_ca_bundle",
                         msg="ignored REQUESTS_CA_BUNDLE")

    @patch.dict(os.environ, {"CURL_CA_BUNDLE": "/curl_ca_bundle"})
    def test_ssl_curl_ca_bundle(self):
        self.assertEqual(get_requests_verify(), "/curl_ca_bundle",
                         msg="ignored CURL_CA_BUNDLE")

    @staticmethod
    def get_dummy_verify_paths(cafile="/cafile.pem", capath="/capath",
                               openssl_cafile="/openssl_cafile.pem",
                               openssl_capath="/openssl_capath"):
        return DefaultVerifyPaths(
            cafile, capath,
            "OPENSSL_CAFILE", openssl_cafile,
            "OPENSSL_CAPATH", openssl_capath
        )

    @patch("platform.system")
    @patch("ssl.get_default_verify_paths")
    @patch.dict(os.environ, {"OPENSSL_CAFILE": "/openssl_cafile_env.pem"})
    def test_ssl_verify_openssl_cafile_env(self, ssl_mock, system_mock):
        system_mock.return_value = "linux"
        ssl_mock.return_value = self.get_dummy_verify_paths()
        self.assertEqual(get_requests_verify(), "/openssl_cafile_env.pem",
                         msg="ignored OPENSSL_CAFILE")

    @patch("platform.system")
    @patch("ssl.get_default_verify_paths")
    @patch.dict(os.environ, {"OPENSSL_CAPATH": "/openssl_capath_env"})
    def test_ssl_verify_openssl_capath_env(self, ssl_mock, system_mock):
        system_mock.return_value = "linux"
        ssl_mock.return_value = self.get_dummy_verify_paths()
        self.assertEqual(get_requests_verify(), "/openssl_capath_env",
                         msg="ignored OPENSSL_CAPATH")

    @patch("platform.system")
    @patch("ssl.get_default_verify_paths")
    def test_ssl_verify_cafile(self, ssl_mock, system_mock):
        system_mock.return_value = "linux"
        ssl_mock.return_value = self.get_dummy_verify_paths()
        self.assertEqual(get_requests_verify(), "/cafile.pem",
                         msg="ignored DefaultVerifyPaths.cafile")

    @patch("platform.system")
    @patch("ssl.get_default_verify_paths")
    def test_ssl_verify_capath(self, ssl_mock, system_mock):
        system_mock.return_value = "linux"
        ssl_mock.return_value = self.get_dummy_verify_paths(cafile=None)
        self.assertEqual(get_requests_verify(), "/capath",
                         msg="ignored DefaultVerifyPaths.capath")

    @patch("platform.system")
    @patch("ssl.get_default_verify_paths")
    def test_ssl_verify_openssl_cafile(self, ssl_mock, system_mock):
        system_mock.return_value = "linux"
        ssl_mock.return_value = self.get_dummy_verify_paths(
            cafile=None, capath=None
        )
        self.assertEqual(get_requests_verify(), "/openssl_cafile.pem",
                         msg="ignored DefaultVerifyPaths.openssl_cafile")

    @patch("platform.system")
    @patch("ssl.get_default_verify_paths")
    def test_ssl_verify_openssl_capath(self, ssl_mock, system_mock):
        system_mock.return_value = "linux"
        ssl_mock.return_value = self.get_dummy_verify_paths(
            cafile=None, capath=None, openssl_cafile=None
        )
        self.assertEqual(get_requests_verify(), "/openssl_capath",
                         msg="ignored DefaultVerifyPaths.openssl_capath")

    @patch("platform.system")
    @patch("ssl.get_default_verify_paths")
    def test_ssl_verify_last_resort(self, ssl_mock, system_mock):
        system_mock.return_value = "linux"
        ssl_mock.return_value = self.get_dummy_verify_paths(
            cafile=None, capath=None, openssl_cafile=None, openssl_capath=None
        )
        self.assertIs(get_requests_verify(), True,
                      msg="did not default to requests default")
