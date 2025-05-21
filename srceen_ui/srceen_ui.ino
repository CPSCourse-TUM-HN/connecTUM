/*
    Autoscroll.ino
    2013 Copyright (c) Seeed Technology Inc.  All right reserved.

    Author:Loovee
    2013-9-18

    Grove - Serial LCD RGB Backlight demo.

    This library is free software; you can redistribute it and/or
    modify it under the terms of the GNU Lesser General Public
    License as published by the Free Software Foundation; either
    version 2.1 of the License, or (at your option) any later version.

    This library is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
    Lesser General Public License for more details.

    You should have received a copy of the GNU Lesser General Public
    License along with this library; if not, write to the Free Software
    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
*/

#include <Wire.h>
#include "rgb_lcd.h"

rgb_lcd lcd;
int pot = A0;
int value = 0;
int new_value = 0;

void setup() {
    // Serial.begin(9600);
    // set up the LCD's number of columns and rows:
    lcd.begin(16, 2);
}

void loop() {
    // set the cursor to (0,0):
    new_value = analogRead(pot);

    if (abs(new_value - value) >= 3) {
        lcd.setCursor(new_value / 68, 0);
        // Serial.print(new_value % 16);
        // Serial.print("\n");
    }
    else {
        lcd.setCursor(value, 0);
    }

    lcd.print('X');
    
    delay(500);
    lcd.clear();
}

/*********************************************************************************************************
    END FILE
*********************************************************************************************************/
