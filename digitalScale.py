import time
import board
import busio
from analogio import AnalogIn
import digitalio

LCD_ADDR = 0x72
BTN_ADDR = 0x6f

#               scl0(GP5)      sda0(GP4)      100kHz
i2c = busio.I2C(scl=board.GP5, sda=board.GP4, frequency=100000)

scalePin = AnalogIn(board.A2)
potPin = AnalogIn(board.A1)
guagePin = AnalogIn(board.A0)

zeroLevel = 0

def getVoltage(pin):
    # 65535 is the max value for the pin
    # 3V3 is the max voltage.
    return (pin.value / 65535) * 3.3

# @brief    check if the button has been pressed
# @return   whether or not the button has been pressed
def readBtnStatus():
    while not i2c.try_lock():
        time.sleep(0.1)
    data = bytearray(1)
    i2c.writeto(BTN_ADDR, bytearray([0x03])) # 0x03 => button_status register
    i2c.readfrom_into(BTN_ADDR, data)
    i2c.unlock()
    return (bool) (data[0] & 0x04)

# @brief        set the button LED Brightness
# @param[in]    brightness (0-255) desired brightness the button LED
# @param[in]    reg_addr address to write to
def writeBtnLED(brightness):
    while not i2c.try_lock():
        time.sleep(0.1)
    i2c.writeto(BTN_ADDR, bytearray([0x19, brightness]))
    i2c.unlock()

# @brief    clear the LCD
def clearLCD():
    while not i2c.try_lock():
        time.sleep(0.1)
    i2c.writeto(LCD_ADDR, bytearray([0x7C, 0x2D]))
    i2c.unlock()

# @brief        print stuff to the LCD
# @param[in]    pressed - whether the button is pressed or not
# @param[in]    temp - current temperature in Celsius as a floating point number
# @return       whether or not the button has been pressed
def printLCD(message):
    while not i2c.try_lock():
        time.sleep(0.1)
    i2c.writeto(LCD_ADDR, message)
    i2c.unlock()

# @brief        clear the LCD
# @param[in]    r (0-255) red color mix
# @param[in]    g (0-255) red color mix
# @param[in]    b (0-255) red color mix
def setBackLight(r, g, b):
    while not i2c.try_lock():
        time.sleep(0.1)
    i2c.writeto(LCD_ADDR, bytearray([0x7C, 0x2B, r, g, b]))
    i2c.unlock()

def convertVoltageToWeight(voltage):
    return (voltage * 1) - zeroLevel

counter = 0
isCalibrating = False
while True:
    clearLCD()
    setBackLight(255, 255, 255)
    pressed = readBtnStatus()

    weight = convertVoltageToWeight(getVoltage(scalePin))

    text = f'{weight:.2f}V'

    if pressed:
        writeBtnLED(100)
        zeroLevel = weight
        text += '\rScaled Tared'
        counter += 1
        if counter >= 4:
            isCalibrating = True
        print(counter, isCalibrating)
        if counter == 1 and isCalibrating:
            isCalibrating = False
            setBackLight(0, 0, 0)
    else:
        writeBtnLED(0)
        counter = 0

    if isCalibrating:
        text = f'Calibrating:\r'
        potVolt = getVoltage(potPin)
        guageVolt = getVoltage(guagePin)
        text += f'{potVolt:0.2f}V {guageVolt:0.2f}V'

    printLCD(text)

    time.sleep(0.5)

i2c.deinit()
