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

from unittest.mock import Mock, patch
import unittest

from birthdav.dav import get_client, get_vobjects


class TestClient(unittest.TestCase):
    def test_get_client(self):
        client = get_client({
            "url": "http://foo",
            "user": "foo",
            "pass": "bar"
        })

        self.assertEqual(client.webdav.hostname, "http://foo")
        self.assertEqual(client.webdav.login, "foo")
        self.assertEqual(client.webdav.password, "bar")

    @staticmethod
    def mock_downloader(vobj, tmp):
        with open(tmp, "w") as tmp_file:
            tmp_file.write(vobj)

    @staticmethod
    def mock_parser(tmp):
        with open(tmp.name) as tmp_file:
            return "contents_" + next(tmp_file)

    @patch("vobject.readOne")
    @patch("webdav3.client.Client")
    def test_get_vobjects(self, MockClient, mockReadOne):
        client = MockClient()
        client.list = Mock(return_value=[
            "a.txt", "b.ics", "c.ics", "d.vcf", "e.vcf", "f"
        ])
        client.download = Mock(side_effect=self.mock_downloader)
        mockReadOne.side_effect = self.mock_parser

        self.assertEqual(get_vobjects(client), [
            "contents_b.ics", "contents_c.ics",
            "contents_d.vcf", "contents_e.vcf"
        ])
