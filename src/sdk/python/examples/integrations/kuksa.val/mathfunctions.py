##############################################################################
# Copyright (c) 2021 Bosch.IO GmbH
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
#
# SPDX-License-Identifier: MPL-2.0
##############################################################################

import random
import os
import asyncio
import logging

from iotea.core.util.logger import Logger
from iotea.core.util.talent_io import TalentInput
logging.setLoggerClass(Logger)
logging.getLogger().setLevel(logging.INFO)

from iotea.core.util.time_ms import time_ms

os.environ['MQTT_TOPIC_NS'] = 'iotea/'

# pylint: disable=wrong-import-position
from iotea.core.talent_func import FunctionTalent
from iotea.core.talent import Talent
from iotea.core.rules import OrRules, AndRules, Rule, ChangeConstraint, Constraint

class MathFunctions(FunctionTalent):
    def __init__(self, connection_string):
        super(MathFunctions, self).__init__('math', connection_string)
        self.register_function('multiply', self.__multiply)
        self.register_function('fibonacci', self.__fibonacci)
        self.register_function('sum', self.__sum)
        self.register_function('gradient', self.__gradient)

    def callees(self):
        return [
            f'{self.id}.fibonacci'.format(self.id),
            f'{self.id}.sum'.format(self.id),
            f'{self.id}.multiply'.format(self.id),
            f'{self.id}.gradient'.format(self.id)
        ]
        
    async def __gradient(self, operand_a,  operand_b, ev, evtctx, timeout_ms):
        i = 0
        while i<3000000:
            i+=1
        print(operand_a)
        print(operand_b)
        deltaVal = operand_a["value"] - operand_b["value"] 
        deltaT = operand_a["whenMs"] - operand_b["whenMs"]
        return  deltaVal/deltaT

    # pylint: disable=unused-argument
    async def __multiply(self, operand_a, operand_b, ev, evtctx, called_at_ms, timeout_ms):
        await asyncio.sleep(random.randint(0, 2))
        return operand_a * operand_b

    # pylint: disable=unused-argument
    async def __sum(self, operand, ev, evtctx, timeout_at_ms):
        if operand == 1:
            return 1

        return operand + await self.call(self.id, 'sum', [operand - 1], ev['subject'], ev['returnTopic'], timeout_at_ms - time_ms())

    async def __fibonacci(self, nth, ev, evtctx, timeout_at_ms):
        self.logger.info(f'Calculating {nth}th fibonacci number...', extra=self.logger.create_extra(evtctx))

        if nth <= 1:
            self.logger.info(f'Result for {nth}th fibonacci number is {nth}', extra=self.logger.create_extra(evtctx))
            return nth

        return await self.call(self.id, 'fibonacci', [nth - 1], ev['subject'], ev['returnTopic'], timeout_at_ms - time_ms()) + await self.call(self.id, 'fibonacci', [nth - 2], ev['subject'], ev['returnTopic'], timeout_at_ms - time_ms())

async def main():
    my_talent = MathFunctions('mqtt://localhost:1883')
    await my_talent.start()

LOOP = asyncio.get_event_loop()
LOOP.run_until_complete(main())
LOOP.close()
