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

from webdav3.client import WebDAVSettings
from unittest.mock import Mock, patch
from datetime import datetime
import unittest
import vobject
import uuid

from birthdav.sync import \
    get_born_contacts, \
    get_events, \
    contact_matches_event, \
    triage_events, \
    create_birthday_event, \
    apply_diffs


class TestSync(unittest.TestCase):
    @staticmethod
    def dummy_client(MockClient):
        client_settings = WebDAVSettings({"hostname": "http://foo"})
        mock_client = MockClient()
        mock_client.webdav = client_settings
        return mock_client

    @staticmethod
    def dummy_contact(bday=None):
        vobj = vobject.vCard()
        vobj.add("uid").value = str(uuid.uuid4())
        if bday is not None:
            vobj.add("bday").value = bday
        return vobj

    @staticmethod
    def dummy_event(contact_uid, when=None):
        vobj = vobject.iCalendar()
        vobj.add("uid").value = str(uuid.uuid4())
        vobj.add("vevent")
        vobj.vevent.add("dtstart").value = when or datetime.now()
        if contact_uid is not None:
            vobj.add("x-birthdav-card-uid").value = contact_uid
            vobj.add("x-birthdav-card-url").value = "http://foo"
        return vobj

    @patch("birthdav.sync.get_vobjects")
    @patch("webdav3.client.Client")
    def test_get_born_contacts(self, MockClient, mock_get_vobjects):
        mock_client = self.dummy_client(MockClient)
        mock_get_vobjects.return_value = [
            self.dummy_contact(datetime.now()),
            self.dummy_contact(datetime.now()),
            self.dummy_contact(None),
        ]

        contacts = get_born_contacts(mock_client)

        self.assertTrue(mock_get_vobjects.called)
        self.assertEqual(len(contacts), 2)

    @patch("birthdav.sync.get_vobjects")
    @patch("webdav3.client.Client")
    def test_get_events(self, MockClient, mock_get_vobjects):
        mock_client = self.dummy_client(MockClient)
        mock_get_vobjects.return_value = [
            self.dummy_event(str(uuid.uuid4())),
            self.dummy_event(str(uuid.uuid4())),
            self.dummy_event(None),
        ]

        events = get_events(mock_client, mock_client)

        self.assertTrue(mock_get_vobjects.called)
        self.assertEqual(len(events), 2)

    def test_contact_matches_event(self):
        self.assertTrue(contact_matches_event(
            self.dummy_contact("1970-01-01"),
            self.dummy_event("uid", datetime(1970, 1, 1))
        ))

    def test_triage_events(self):
        new_contact = self.dummy_contact(datetime.now())
        updated_contact = self.dummy_contact("1970-01-01")
        updated_event = self.dummy_event(updated_contact.uid.value,
                                         datetime(1980, 1, 1))
        deleted_event = self.dummy_event("foo")

        new, lost, updated = triage_events({
            new_contact.uid.value: new_contact,
            updated_contact.uid.value: updated_contact,
        }, {
            updated_contact.uid.value: updated_event,
            "foo": deleted_event
        })

        self.assertTrue(
            len(new) == 1 and new[0].uid.value == new_contact.uid.value,
            msg="missing new contact"
        )
        self.assertTrue(
            len(updated) == 1 and
            updated[0]["contact"].uid.value == updated_contact.uid.value,
            msg="missing updated contact"
        )
        self.assertTrue(
            len(lost) == 1 and deleted_event.uid.value in lost,
            msg="missing lost contact"
        )

    @patch("webdav3.client.Client")
    def test_create_birthday_events(self, MockClient):
        mock_client = self.dummy_client(MockClient)
        new_contact = self.dummy_contact("1970-01-01")
        new_contact.add("n")
        new_contact.n.value.given = "Foo"
        new_contact.n.value.additional = "Bar"
        new_contact.n.value.family = "Baz"
        vobj = create_birthday_event(mock_client, mock_client, new_contact)

        expected_name = "Foo Bar Baz"
        self.assertEqual(vobj.x_birthdav_card_uid.value, new_contact.uid.value,
                         msg="invalid contact reference in event")
        self.assertEqual(vobj.x_birthdav_card_url.value, "http://foo",
                         msg="invalid CalDAV URL in event")
        self.assertEqual(vobj.x_birthdav_card_uid.value, new_contact.uid.value,
                         msg="invalid contact reference in event")
        self.assertEqual(vobj.vevent.summary.value, expected_name,
                         msg="invalid event summary")
        self.assertEqual(vobj.vevent.dtstart.value, datetime(1970, 1, 1, 8, 0),
                         msg="invalid event start")
        self.assertEqual(vobj.vevent.rrule.value, "FREQ=YEARLY",
                         msg="invalid recurrence rule")

        alarms = vobj.vevent.valarm_list
        self.assertEqual(len(alarms), 2, msg="invalid alarm count")
        self.assertTrue(all(a.action.value == "DISPLAY" for a in alarms),
                        msg="invalid alarm actions")
        self.assertTrue(all(a.description.value == expected_name
                            for a in alarms),
                        msg="invalid alarm descriptions")

        triggers = sorted([int(a.trigger.value.total_seconds())
                           for a in alarms])
        self.assertEqual(triggers, [-604800, 0], msg="invalid alarm triggers")

    @patch("birthdav.sync.create_birthday_event")
    @patch("webdav3.client.Client")
    def test_apply_diffs(self, MockClient, mock_create_event):
        mock_client = self.dummy_client(MockClient)
        mock_client.upload = Mock()
        mock_client.clean = Mock()

        new_contact = self.dummy_contact("1970-01-01")
        updated_contact = self.dummy_contact("1970-01-01")
        updated_event = self.dummy_event(updated_contact.uid.value,
                                         datetime(1970, 1, 1, 8, 0))
        lost_event = self.dummy_event("foo")

        apply_diffs(
            mock_client, mock_client,
            [new_contact], [lost_event.uid.value],
            [{
                "contact": updated_contact,
                "event": updated_event
            }]
        )

        mock_create_event.assert_called_once_with(mock_client, mock_client,
                                                  new_contact)
        mock_client.upload.assert_called_once()
        self.assertEqual(mock_client.upload.call_args[0][0],
                         "%s.ics" % updated_event.uid.value,
                         msg="missing updating call")
        mock_client.clean.assert_called_once_with(
            "%s.ics" % lost_event.uid.value
        )
