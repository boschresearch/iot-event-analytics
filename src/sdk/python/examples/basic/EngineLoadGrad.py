##############################################################################
# Copyright (c) 2021 Bosch.IO GmbH
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# SPDX-License-Identifier: MPL-2.0
##############################################################################

import asyncio
import logging

from iotea.core.protocol_gateway import ProtocolGateway
from iotea.core.util.logger import Logger
from iotea.core.util.mqtt_client import MqttProtocolAdapter
from iotea.core.util.talent_io import TalentInput

logging.setLoggerClass(Logger)
logging.getLogger().setLevel(logging.INFO)

# pylint: disable=wrong-import-position
from iotea.core.talent import Talent
from iotea.core.rules import AndRules, Rule, ChangeConstraint, Constraint

class MyTalent(Talent):
    def __init__(self, protocol_gateway_config):
        super().__init__('grad-engine-load-talent', protocol_gateway_config)
        self.prevEv = None
        self.currGrad = 0

    def callees(self):
        return [
            f'risk-index.speedgrad_change',
            f'risk-index.enginegrad_change'
        ]

    def get_rules(self):
        return AndRules([
            Rule(ChangeConstraint('OBD$EngineLoad', 'Vehicle', Constraint.VALUE_TYPE['RAW']))
        ])

    async def on_event(self, ev, evtctx):
        print(f'Raw value {TalentInput.get_raw_value(ev)}')
        if self.prevEv == None:
            self.prevEv = ev
        else:
            deltaV = float(TalentInput.get_raw_value(ev)) - float(TalentInput.get_raw_value(self.prevEv))
            deltaT = float(ev["whenMs"]) - float(self.prevEv["whenMs"])
            self.currGrad = deltaV/deltaT
            self.prevEv = ev
            result = await self.call("risk-index", "speedgrad_change", [str(self.currGrad)], ev["subject"], ev["returnTopic"], 6000)
            print("Result is {}".format(result))


async def main():
    mqtt_config = MqttProtocolAdapter.create_default_configuration(broker_url="mqtt://mosquitto:1883")
    pg_config = ProtocolGateway.create_default_configuration([mqtt_config])
    my_talent = MyTalent(pg_config)
    await my_talent.start()

LOOP = asyncio.get_event_loop()
LOOP.run_until_complete(main())
LOOP.close()
