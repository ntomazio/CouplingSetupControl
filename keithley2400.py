# -*- coding: utf-8 -*-

import visa
import numpy as np


class Keithley2400SM:
    # definitions
    gpib = True 
    eth = False
    usb = False
    gpibAddr = 24
    ip = "192.168.1.2"
    port = 10001
    usbid = "KEITHLEY"
    visarm = None
    visaOK = False
    sm = None
    smOK = False
    smID = ""

    nplc = 1.0
    apply_curr = False
    apply_volt = False
    meas_curr = False
    meas_volt = False
    meas_ohm = False

    # main functions
    def __init__(self):
        try:
            self.visarm = visa.ResourceManager('@ni')
            self.visaOK = True
        except:
            print("Error creating NI VISA Resource Manager! Is the GPIB Card connected?")
            pass
        if not self.visaOK:
            try:
                self.visarm = visa.ResourceManager('@py')
                self.visaOK = True
            except:
                print("Error creating PYVISA Resource Manager! Is the GPIB Card connected?")
                pass

    def __del__(self):
        self.closeSM()
        return 0

    # sm functions

    def connectSM(self, isgpib=True, address=24, iseth=False, ethip="192.168.1.2", ethport=10001, isusb=True):
        if self.visaOK:
            self.gpib = isgpib
            self.gpibAddr = address
            self.eth = iseth
            self.ip = ethip
            self.port = ethport
            self.usb = isusb
            try:
                if self.gpib:
                    smname = "GPIB0::" + str(self.gpibAddr) + "::INSTR"
                    self.sm = self.visarm.open_resource(smname)
                elif self.eth:
                    smname = "TCPIP0::" + self.ip + "::" + str(self.port) + "::SOCKET"
                    self.sm = self.visarm.open_resource(smname, read_termination="\r\n", timeout=5000)
                    self.sm.query('open "' + self.user + '"')
                    self.sm.query(self.passwd)
                elif self.usb:
                    smname = ""
                    all = self.visarm.list_resources()
                    for name in all:
                        if self.usbid in name:
                            smname = name
                    self.sm = self.visarm.open_resource(smname)

                if self.usbid in self.sm.query("*IDN?"):
                    self.smOK = True
                else:
                    print("Error opening source meter! Is it connected?")
            except:
                print("Critical error opening sourcemeter! Is it connected?")
                pass

    def initSM(self):
        if self.smOK:
            pass

    def closeSM(self):
        if self.smOK:
            self.smOK = False
            self.sm.close()

    def conf_apply_current(self):  # Sets up to source current
        if self.smOK:
            self.sm.write(":SOUR:FUNC CURR")
            self.apply_curr = True
            self.apply_volt = False

    def conf_apply_voltage(self):  # Sets up to source voltage
        if self.smOK:
            self.sm.write(":SOUR:FUNC VOLT")   
            self.apply_volt = True
            self.apply_curr = False

    def conf_measure_voltage(self):  # Sets up to measure voltage
        if self.smOK:
            self.sm.write(":SENS:FUNC:OFF:ALL")
            self.sm.write(":SENS:FUNC 'VOLT'")
            self.sm.write(":SENS:VOLT:NPLC " + str(self.nplc))
            self.sm.write(":FORM:ELEM VOLT")
            self.sm.write(":SENS:VOLT:RANG:AUTO 1")

            self.meas_volt = True
            self.meas_curr = False
            self.meas_ohm = False

    def conf_measure_current(self):  # Sets up to measure current
        if self.smOK:
            self.sm.write(":SENS:FUNC:OFF:ALL")
            self.sm.write(":SENS:FUNC 'CURR'")
            self.sm.write(":SENS:VOLT:NPLC " + str(self.nplc))
            self.sm.write(":FORM:ELEM CURR")
            self.sm.write(":SENS:CURR:RANG:AUTO 1")

            self.meas_volt = False
            self.meas_curr = True
            self.meas_ohm = False

    def conf_measure_ohms(self):  # Sets up to measure resistance
        if self.smOK:
            self.sm.write(":SENS:FUNC:OFF:ALL")
            self.sm.write(":SENS:FUNC 'RES'")
            self.sm.write(":SENS:RES:MODE MAN")
            self.sm.write(":SENS:RES:NPLC " + str(self.nplc))
            self.sm.write(":FORM:ELEM RES")
            self.sm.write(":SENS:RES:RANG:AUTO 1")

            self.meas_volt = False
            self.meas_curr = False
            self.meas_ohm = True

    def set_compliance_voltage(self, volt):  # Sets the compliance voltage
        if self.smOK:
            self.sm.write(":SENS:VOLT:PROT " + str(volt))

    def set_compliance_current(self, curr):  # Sets the compliance current
        if self.smOK:
            self.sm.write(":SENS:CURR:PROT " + str(curr))

    def set_source_current(self, curr):  # Sets the source current
        if self.smOK:
            self.sm.write(":SOUR:CURR:LEV " + str(curr))

    def set_source_voltage(self, volt):  # Sets the source voltage
        if self.smOK:
            self.sm.write(":SOUR:VOLT:LEV " + str(volt))

    def enable_output(self):  # Enables the source output
         if self.smOK:
            self.sm.write("OUTPUT ON")

    def disable_output(self):  # Disables the source output
         if self.smOK:
            self.sm.write("OUTPUT OFF")

    def get_voltage(self):  # Get the voltage in Volts
        if self.smOK:
            if not self.meas_volt:
                self.conf_measure_voltage()
            resp = self.sm.query("READ?")
            volt = float(resp)
            return volt
        else:
            return 0

    def get_current(self):  # Get the current in amps
        if self.smOK:
            if not self.meas_curr:
                self.conf_measure_current()
            resp = self.sm.query("READ?")
            curr = float(resp)
            return curr
        else:
            return 0

    def get_ohms(self):  # Get the resistance in Ohms
        if self.smOK:
            if not self.meas_ohm:
                self.conf_measure_ohms()
            resp = self.sm.query("READ?")
            ohms = float(resp)
            return ohms
        else:
            return 0

    def set_nplc(self, nplc):
        self.nplc = nplc

    def use_rear_terminals(self):
        if self.smOK:
            self.write(":ROUT:TERM REAR")

    def use_front_terminals(self):
        if self.smOK:
            self.write(":ROUT:TERM FRON")

    def shutdown(self):  # Sets the source to 0 and disables output
        if self.smOK:
            if self.apply_curr:
                self.set_source_current(0.0)
            else:
                self.set_source_voltage(0.0)
            self.disable_source()