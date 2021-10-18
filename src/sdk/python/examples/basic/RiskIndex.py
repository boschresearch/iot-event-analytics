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
import math

from iotea.core.protocol_gateway import ProtocolGateway
from iotea.core.util.logger import Logger
from iotea.core.util.mqtt_client import MqttProtocolAdapter
import paho.mqtt.client as mqtt
from iotea.core.util.talent_io import TalentInput

logging.setLoggerClass(Logger)
logging.getLogger().setLevel(logging.CRITICAL)

# pylint: disable=wrong-import-position
from iotea.core.talent_func import FunctionTalent
from iotea.core.rules import AndRules, Rule, ChangeConstraint, Constraint

class MyTalent(FunctionTalent):
    def __init__(self, connection_string):
        super().__init__('risk-index', connection_string)
        self.register_function("speedgrad_change", self._speedgrad_change)
        self.register_function("enginegrad_change", self._enginegrad_change)
        self.riskIndex = 0
        self.speedGrad = 0
        self.engineGrad = 0
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.connect("mosquitto")

    def callees(self):
        return [
            f'{self.id}.speedgrad_change'.format(self.id),
            f'{self.id}.enginegrad_change'.format(self.id)
        ]


    async def _speedgrad_change(self, new_speed_grad, ev, evtctx, timeout_ms):
        self.speedGrad = float(new_speed_grad)
        index = await self._calc_risk_index()
        return index

    async def _enginegrad_change(self, new_engine_grad, ev, evtctx, timeout_ms):
        self.engineGrad = float(new_engine_grad)
        index = await self._calc_risk_index()
        return index

    async def _calc_risk_index(self):
        self.riskIndex = math.ceil((400 * abs(self.speedGrad) + 300 * abs(self.engineGrad)) * 32)
        if self.riskIndex > 100: 
            self.riskIndex = 100
        elif self.riskIndex < 0:
            self.riskIndex = 0
        print("Risk Index: " + str(self.riskIndex))
        await self.mqtt_client.publish('nodered/riskindex', self.riskIndex)
        return self.riskIndex

async def main():    
    mqtt_config = MqttProtocolAdapter.create_default_configuration(broker_url="mqtt://mosquitto:1883")
    pg_config = ProtocolGateway.create_default_configuration([mqtt_config])
    my_talent = MyTalent(pg_config)
    await my_talent.start()

LOOP = asyncio.get_event_loop()
LOOP.run_until_complete(main())
LOOP.close()
