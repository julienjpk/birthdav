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

from tempfile import NamedTemporaryFile
from webdav3.client import Client
import platform
import vobject
import ssl
import os


def get_requests_verify():
    """
    Identifies the path to the system's certificate authority bundle

    By default, the requests package (for webdavclient3) enforces the use of
    Mozilla's certificate bundle, provided by the certifi package. It does not
    take the system's bundle into account at any moment. On an internal network
    with internal certificate authorities, this obviously breaks everything.

    Why that's considered good practice is beyond me, but:
    https://github.com/psf/requests/issues/2966
    """

    # First things first, if they got us into this mess...
    if platform.system() == "Windows":
        return True  # ... they can have fun with whatever bundle they get

    ssl_verify_paths = ssl.get_default_verify_paths()
    hard_openssl_file = ssl_verify_paths.openssl_cafile_env
    hard_openssl_path = ssl_verify_paths.openssl_capath_env
    bundle_paths = (
        os.environ.get("REQUESTS_CA_BUNDLE"),
        os.environ.get("CURL_CA_BUNDLE"),
        None if hard_openssl_file is None else os.getenv(hard_openssl_file),
        None if hard_openssl_path is None else os.getenv(hard_openssl_path),
        ssl_verify_paths.cafile,
        ssl_verify_paths.capath,
        ssl_verify_paths.openssl_cafile,
        ssl_verify_paths.openssl_capath,
    )

    try:
        return next(p for p in bundle_paths if p is not None)
    except StopIteration:
        return True


def get_client(config: dict):
    """
    Builds and returns a WebDAV client
    """
    client = Client({
        "webdav_hostname": config["url"],
        "webdav_login": config["user"],
        "webdav_password": config["pass"],
    })

    client.verify = get_requests_verify()
    return client


def get_vobjects(client: Client):
    """
    Fetches all .ics and .vcf files from a WebDAV server
    """
    vfiles = [vcf for vcf in client.list() if vcf[-4:] in (".vcf", ".ics")]
    vobjects = []
    for vcf_file in vfiles:
        tmp_file_w = NamedTemporaryFile("w", delete=False)
        client.download(vcf_file, tmp_file_w.name)
        tmp_file_w.close()
        with open(tmp_file_w.name) as tmp_file_r:
            vobjects.append(vobject.readOne(tmp_file_r))
        os.unlink(tmp_file_w.name)
    return vobjects
