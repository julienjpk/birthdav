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

from birthdav.dav import get_vobjects

from datetime import datetime, timedelta
from tempfile import NamedTemporaryFile
from webdav3.client import Client
import vobject
import uuid


def get_born_contacts(card_client: Client):
    """
    Fetches objects from a CardDAV client and returns contacts with birthdays
    """
    return {c.uid.value: c for
            c in get_vobjects(card_client) if
            hasattr(c, "bday")}


def get_events(cal_client: Client, card_client: Client):
    """
    Fetches birthdav birthdays from a CalDAV client
    """
    return {e.x_birthdav_card_uid.value: e for e in get_vobjects(cal_client) if
            hasattr(e, "x-birthdav-card-uid") and
            hasattr(e, "x-birthdav-card-url") and
            e.x_birthdav_card_url.value == card_client.webdav.hostname}


def contact_matches_event(contact, event):
    """
    Determines whether or not an event still matches a contact's details
    """
    birth_date = datetime.strptime(contact.bday.value, "%Y-%m-%d").date()
    event_date = event.vevent.dtstart.value.date()
    return birth_date == event_date


def triage_events(contacts: dict, events: dict):
    """
    Compares contacts and events to determine what to add, edit or remove
    """
    contacts_idset = set(contacts.keys())
    events_idset = set(events.keys())

    new_idset = contacts_idset - events_idset
    lost_idset = events_idset - contacts_idset
    updated_idset = {uid for uid in events_idset if
                     uid in contacts_idset and
                     not contact_matches_event(contacts[uid], events[uid])}

    new_contacts = [contacts[uid] for uid in new_idset]
    updated_contacts = [{
        "contact": contacts[uid],
        "event": events[uid]
    } for uid in updated_idset]
    lost_events = [events[uid].uid.value for uid in lost_idset]

    return new_contacts, lost_events, updated_contacts


def create_birthday_event(cal_client: Client, card_client: Client,
                          new_contact):
    """
    Creates a CalDAV event for a new contact
    """
    vobj_name = new_contact.n.value
    vobj_names = [vobj_name.given, vobj_name.additional, vobj_name.family]
    name = ' '.join(n.strip() for n in vobj_names if len(n) > 0)
    birthdate = datetime.strptime(new_contact.bday.value, "%Y-%m-%d")
    event_time = birthdate.replace(hour=8, minute=0, microsecond=0)
    uid = str(uuid.uuid4())

    vobj = vobject.iCalendar()
    vobj.add("uid").value = uid
    vobj.add("x-birthdav-card-uid").value = new_contact.uid.value
    vobj.add("x-birthdav-card-url").value = card_client.webdav.hostname

    vobj.add("vevent")
    vobj.vevent.add("summary").value = name
    vobj.vevent.add("dtstart").value = event_time
    vobj.vevent.add("rrule").value = "FREQ=YEARLY"

    for trigger in (0, 7):
        alarm = vobj.vevent.add("valarm")
        alarm.add("action").value = "DISPLAY"
        alarm.add("trigger").value = timedelta(days=-trigger)
        alarm.add("description").value = name

    with NamedTemporaryFile("w") as tmp_file:
        tmp_file.write(vobj.serialize())
        tmp_file.flush()
        cal_client.upload("%s.ics" % uid, tmp_file.name)

    return vobj


def apply_diffs(cal_client: Client, card_client: Client,
                new: dict, lost: dict, updated: dict):
    """
    Applies contact changes to the associated CalDAV birthday events
    """
    for new_contact in new:
        create_birthday_event(cal_client, card_client, new_contact)
    for lost_contact in lost:
        cal_client.clean("%s.ics" % lost_contact)
    for updated_entry in updated:
        contact, event = updated_entry["contact"], updated_entry["event"]
        birthdate = datetime.strptime(contact.bday.value, "%Y-%m-%d")
        event_time = birthdate.replace(hour=8, minute=0, microsecond=0)

        event.vevent.dtstart.value = event_time
        with NamedTemporaryFile("w") as tmp_file:
            tmp_file.write(event.serialize())
            tmp_file.flush()
            cal_client.upload("%s.ics" % event.uid.value, tmp_file.name)


def sync_birthdays(card_client: Client, cal_client: Client):  # pragma: no cover
    """
    Fetches contacts and events and syncs them
    """
    contacts = get_born_contacts(card_client)
    events = get_events(cal_client, card_client)
    new, lost, updated = triage_events(contacts, events)
    apply_diffs(cal_client, card_client, new, lost, updated)
