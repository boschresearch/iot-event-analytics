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
import json
import os
import logging

from iotea.core.util.logger import Logger
from iotea.core.util.talent_io import TalentInput
logging.setLoggerClass(Logger)
logging.getLogger().setLevel(logging.INFO)

os.environ['MQTT_TOPIC_NS'] = 'iotea/'

# pylint: disable=wrong-import-position
from iotea.core.talent import Talent
from iotea.core.rules import OrRules, AndRules, Rule, ChangeConstraint, Constraint

class MyTalent(Talent):
    def __init__(self, connection_string):
        super(MyTalent, self).__init__('python-basic-talent', connection_string)
        self.prev = None
        self.prevVal = None

    def callees(self):
        return [
            f'math.fibonacci',
            f'math.sum',
            f'math.multiply',
            f'math.gradient'
        ]
    def get_rules(self):
        return OrRules([
            Rule(ChangeConstraint('Acceleration$Lateral', 'Vehicle', Constraint.VALUE_TYPE['RAW']))
        ])
    
    async def on_event(self, ev, evtctx):
        #print(ev)
        value = { "whenMs": ev["whenMs"], "value": TalentInput.get_raw_value(ev)}
        print(f'Raw value {value}')
        if self.prev != None:
            try:
                self.logger.info(f'Calling function for {ev["value"]}...', extra=self.logger.create_extra(evtctx))
                result = await self.call('math', 'gradient', [self.prev, value], ev['subject'],  ev["returnTopic"], 60000)
                #result = await self.call('math', 'fibonacci', [ev['value']], ev['subject'], ev['returnTopic'], 60000)
                #result = await self.call('math', 'sum', value, ev['subject'], ev['returnTopic'], 60000)
                # result = await self.call(self.id, 'multiply', [ev['value'], ev['value']], ev['subject'], ev['returnTopic'], 60000)

                self.logger.info('Result is {}'.format(result), extra=self.logger.create_extra(evtctx))
            except Exception as err:
                self.logger.error('An error occurred while calling a function', extra=self.logger.create_extra(evtctx))
                self.logger.error(err)

        self.prev = value

async def main():
    my_talent = MyTalent('mqtt://localhost:1883')
    await my_talent.start()

LOOP = asyncio.get_event_loop()
LOOP.run_until_complete(main())
LOOP.close()
