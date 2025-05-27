#!/usr/bin/env python3

import time

class BoardController:

    BOARD_POS =
    BOARD_COLUMNS_WIDTH =
    MAGAZINE_POS =

    def dropCoinAt(self, column):
        self.loadCoin()
        self.moveAt(column)
        time.sleep(0.5)

    def moveAt(self, column):
        distance = column * self.BOARD_COLUMNS_WIDTH
        self.move(distance)
        time.sleep(0.5)

    def loadCoin(self):
        self.move()
        #
        self.move()
        time.sleep(0.5)

    def move(self, distance):
        #
        time.sleep(0.5)

    def getColumn(self, index):
        return (index - 1) % 7