# -*- coding: utf-8 -*-

import visa
import numpy as np


class OSCDSO9404A:
    # definitions
    gpib = False
    eth = False
    usb = True
    gpibAddr = 1
    ip = "192.168.1.2"
    port = 10001
    usbid = "MY53060106"
    visarm = None
    visaOK = False
    osc = None
    oscOK = False
    oscID = ""
    binary = False
    traceLength = 0
    trace = "trace1"
    tracen = 0

    # main functions
    def __init__(self):
        try:
            self.visarm = visa.ResourceManager('@ni')
            self.visaOK = True
        except:
            print("Error creating VISA Resource Manager! Is the GPIB Card connected?")
            pass
        if not self.visaOK:
            try:
                self.visarm = visa.ResourceManager('@py')
                self.visaOK = True
            except:
                print("Error creating VISA Resource Manager! Is the GPIB Card connected?")
                pass

    def __del__(self):
        self.closeOSC()
        return 0

    # OSC functions

    def connectOSC(self, isgpib=False, address=18, iseth=False, ethip="192.168.1.2", ethport=10001, isusb=True):
        if self.visaOK:
            self.gpib = isgpib
            self.gpibAddr = address
            self.eth = iseth
            self.ip = ethip
            self.port = ethport
            self.usb = isusb
            try:
                if self.gpib:
                    oscname = "GPIB0::" + str(self.gpibAddr) + "::INSTR"
                    self.osc = self.visarm.open_resource(oscname)
                # elif self.eth:
                #     osaname = "TCPIP0::" + self.ip + "::" + str(self.port) + "::SOCKET"
                #     self.osc = self.visarm.open_resource(osaname, read_termination="\r\n", timeout=5000)
                #     self.osc.query('open "' + self.user + '"')
                #     self.osc.query(self.passwd)
                elif self.usb:
                    oscname = ""
                    all = self.visarm.list_resources()
                    for name in all:
                        if self.usbid in name:
                            oscname = name
                    self.osc = self.visarm.open_resource(oscname)

                if self.usbid in self.osc.query("*IDN?"):
                    self.oscOK = True
                else:
                    print("Error opening Oscilloscope! Is it connected?")
            except:
                print("Critical error opening Oscilloscope! Is it connected?")
                pass

    def initOSC(self, binarymode=True):
        if self.oscOK:
            self.binary = binarymode

            #self.osc.write("DISP:PERS MIN")
            #self.osc.write("ACQ:MODE RTIM")
            #self.osc.write("ACQ:INT ON")
            #self.osc.write("ACQ:SRAT AUTO")

            if self.binary:
                self.osc.write("WAV:FORM WORD")
            else:
                self.osc.write("WAV:FORM ASC")
            self.traceLength = self.getTraceLength()

    def closeOSC(self):
        if self.oscOK:
            # self.single()
            self.oscOK = False
            self.osc.close()

    def run(self):
        if self.oscOK:
            self.osc.write(":RUN")

    def stop(self):
        if self.oscOK:
            self.osc.write(":STOP")

    def single(self):
        if self.oscOK:
            self.osc.write(":SING")

    def getStartTime(self):
        if self.oscOK:
            resp = self.osc.query("TIM:POS?")
            start= float(resp)
            return start
        else:
            return 0

    def setStartTime(self, t):
        if self.oscOK:
            self.osc.write("TIM:POS " + str(t))

    def getTimeScale(self):
        if self.oscOK:
            resp = self.osc.query("TIM:SCAL?")
            scale = float(resp)
            return scale
        else:
            return 0

    def setTimeScale(self, s):
        if self.oscOK:
            self.osc.write("TIM:SCAL " + str(s))

    def getStopTime(self):
        if self.oscOK:
            t0 = self.getStartTime()
            scale = self.getTimeScale()
            stop = t0 + scale * 10
            return stop
        else:
            return 0

    def setStopTime(self, t):
        if self.oscOK:
            t0 = self.getStartTime()
            scale = (t - t0)/10
            self.setTimeScale(scale)

    def getTraceLength(self):
        if self.oscOK:
            resp = self.osc.query("ACQ:POIN?")
            length = int(resp)
            self.traceLength = length
            return length
        else:
            return 0
    
    def setTraceLength(self, length):
        if self.oscOK:
            self.osc.write("ACQ:POIN " + str(length))
        self.traceLength = length
    
    def getSampRate(self):
        if self.oscOK:
            resp = self.osc.query("ACQ:SRAT?")
            srat = float(resp)
            self.samprate = srat
            return srat
        else:
            return 0

    def setSampRate(self, srat):
        if self.oscOK:
            self.osc.write("ACQ:SRAT " + str(srat))
        self.samprate = srat

    def setAvrg(self, avg):
        if self.oscOK:
            self.osc.write("ACQ:AVER:COUN " + str(avg))

    def getAvrg(self):
        if self.oscOK:
            resp = self.osc.query("ACQ:AVER:COUN?")
            avgs = int(resp)
            return avgs
        else:
            return 0

    def switchAvrg(self, status):
        nstatus = int(status)
        if self.oscOK:
            self.osc.write("ACQ:AVER " + str(nstatus))

    def getAvrgState(self):
        if self.oscOK:
            isavg = int(self.osc.query("ACQ:AVER?"))
            return isavg
        else:
            return 0

    def getCurAvrg(self, chan):
        if self.oscOK:
            self.osc.write("WAV:SOUR CHAN" + str(chan))
            curavg = int(self.osc.query("WAV:COUNT?"))
            return curavg
        else:
            return 0

    def singleFinished(self, chan):
        self.osc.write("WAV:SOUR CHAN" + str(chan))
        # ader = int(self.osc.query("ADER?"))
        # opc = int(self.osc.query("*OPC?"))
        pder = int(self.osc.query("PDER?"))
        # avs = int(self.osc.query("WAV:COUNT?"))
        # if ader and opc and ((self.getAvrgState() and avs >= self.getAvrg()) or not self.getAvrgState()):
        if pder:
            return True
        else:
            return False

    def setChannel(self, chan, state):
        s = int(state)
        self.osc.write("CHAN" + str(chan) + ":DISP " + str(s))

    def measPhase(self, chan1, chan2, freq):
        self.osc.write(":MEAS:DELT:DEF RIS,1,MIDD,RIS,1,MIDD")
        deltat = float(self.osc.query(f"MEAS:DELT? CHAN{chan1},CHAN{chan2}"))
        phas = 2*deltat*freq*1e6*180
        return phas

    def getData(self, chan):
        data = []
        if self.binary:
            data = self.getBinTrace(chan)
        else:
            data = self.getASCIITrace(chan)
        return data

    def getBinTrace(self, chan):
        if self.oscOK:
            nchan = int(np.mod(chan, 4))
            if nchan == 0:
                nchan = 4
            self.osc.write("WAV:SOUR CHAN" + str(nchan))
            rawdata = self.osc.query_binary_values("WAV:DATA?", datatype="h", is_big_endian=True)
            scale = float(self.osc.query("CHAN" + str(nchan) + ":SCAL?"))
            off = float(self.osc.query("CHAN" + str(nchan) + ":OFFS?"))
            conv = scale*4/30720
            data = off + np.array(rawdata)*conv
            return data
        else:
            return np.zeros(self.traceLength)

    def getASCIITrace(self, chan):
        if self.oscOK:
            nchan = int(np.mod(chan, 4))
            if nchan == 0:
                nchan = 4
            self.osc.write("WAV:SOUR CHAN" + str(nchan))
            off = float(self.osc.query("CHAN" + str(nchan) + ":OFFS?"))
            data = self.osc.query("WAV:DATA?")
            stringlist = data.split(",")
            numlist = []

            for i in range(0, len(stringlist) - 1):
                numlist.append(float(stringlist[i]))
            numlist = off + np.array(numlist)
            return numlist
        else:
            return np.zeros(self.traceLength)

    def setEdgeTrigger(self, chan, slope="POS", level=200e-3):
        if self.oscOK:
            self.osc.write("TRIGger:EDGE:SOURce CHAN"+str(chan)) 
            self.osc.write("TRIGger:EDGE:SLOPe "+slope)
            self.osc.write("TRIGger:LEVel CHAN"+str(chan)+","+str(level))

    # Get the waveform type
    def getWaveformType(self):
        if self.oscOK:
            qresult = self.osc.query(":WAVeform:TYPE?")
            print("Waveform type: %s" % qresult)