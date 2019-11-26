# encoding: utf-8
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#

from __future__ import absolute_import, division, unicode_literals

import sys

import requests

from mo_dots import wrap, Data, set_default
from mo_files import URL
from mo_json import value2json
from mo_kwargs import override
from mo_logs import Log, CR
from mo_math import rsa_crypto
from mo_threads import Till
from mo_times import Date, Timer
from mo_times.dates import parse
from pyLibrary.convert import text2QRCode

DEBUG = False


class Auth0Client(object):
    @override
    def __init__(self, kwargs=None):
        # GENERATE PRIVATE KEY
        self.config = kwargs
        self.session_id = None
        with Timer("generate {{bits}} bits rsa key", {"bits": self.config.rsa.bits}):
            Log.note("This will take a while....")
            self.public_key, self.private_key = rsa_crypto.generate_key(bits=self.config.rsa.bits)

    def login(self, please_stop=None):
        """
        WILL REGISTER THIS DEVICE, AND SHOW A QR-CODE TO LOGIN
        WILL POLL THE SERVICE ENDPOINT UNTIL LOGIN IS COMPLETED, OR FAILED

        :param please_stop: SIGNAL TO STOP EARLY
        :return: SESSION THAT CAN BE USED TO SEND AUTHENTICATED REQUESTS
        """
        # SEND PUBLIC KEY
        now = Date.now().unix
        login_session = requests.session()        signed = rsa_crypto.sign(
            Data(public_key=self.public_key, timestamp=now),
            self.private_key
        )
        DEBUG and Log.note("register (unsigned)\n{{request|json}}", request=rsa_crypto.verify(signed, self.public_key))
        DEBUG and Log.note("register (signed)\n{{request|json}}", request=signed)
        try:
            response = login_session.request(
                "POST",
                str(URL(self.config.service) / self.config.endpoints.register),
                data=value2json(signed)
            )
        except Exception as e:
            raise Log.error("problem registering device", cause=e)

        device = wrap(response.json())
        DEBUG and Log.note("response:\n{{response}}", response=device)
        device.interval = parse(device.interval).seconds
        expires = Till(till=parse(device.expires).unix)
        session_id = self.session_id = device.session_id
        if not session_id:
            Log.error("expecting a session cookie")

        # SHOW URL AS QR CODE
        image = text2QRCode(device.url)

        sys.stdout.write("\n\nLogin using thie URL:\n")
        sys.stdout.write(device.url+CR)
        sys.stdout.write(image)

        while not please_stop and not expires:
            Log.note("waiting for login...")
            try:
                now = Date.now()
                signed = rsa_crypto.sign(
                    Data(
                        timestamp=now,
                        session_id=session_id
                    ),
                    self.private_key
                )
                url = URL(self.config.service) / self.config.endpoints.status
                DEBUG and Log.note(
                    "ping (unsigned) {{url}}\n{{request|json}}",
                    url=url,
                    request=rsa_crypto.verify(signed, self.public_key)
                )
                response = login_session.request(
                    "POST",
                    url,
                    data=value2json(signed)
                )
                ping = wrap(response.json())
                DEBUG and Log.note("response\n{{response|json}}", response=ping)
                if ping.status == "verified":
                    return self
                if not ping.try_again:
                    Log.note("Failed to login {{reason}}", reason=ping.status)
                    return
            except Exception as e:
                Log.warning(
                    "problem calling {{url}}",
                    url=URL(self.config.service)/ self.config.endpoints.status,
                    cause=e,
                )
            (Till(seconds=device.interval) | please_stop | expires).wait()
        return self

    def request(self, method, url, **kwargs):
        """
        ENSURE THE SESSION IS USED (SO THAT COOKIE IS ATTACHED)
        """
        set_default(kwargs, {"headers": {"Authorization": self.session_id}})

        return requests.request(method, url, **kwargs)
