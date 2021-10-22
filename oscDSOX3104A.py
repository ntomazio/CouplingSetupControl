# -*- coding: utf-8 -*-

import visa
import numpy as np


class OSCDSOX3104A:
    # definitions
    gpib = False
    eth = False
    usb = True
    gpibAddr = 1
    ip = "192.168.1.2"
    port = 10001
    usbid = "MY52490398"
    visarm = None
    visaOK = False
    osc = None
    oscOK = False
    oscID = ""
    binary = True
    traceLength = 0
    trace = "trace1"
    tracen = 0

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
            # self.osc.timeout = 10000

            # self.osc.write("DISP:PERS MIN")
            # self.osc.write("ACQ:MODE RTIM")
            # self.osc.write("ACQ:INT ON")
            # self.osc.write("ACQ:SRAT AUTO")

            if self.binary:
                self.osc.write("WAV:FORM WORD")
                self.osc.write("WAV:BYT MSBF")
            else:
                self.osc.write("WAV:FORM ASC")
            self.traceLength = self.getTraceLength()

    def closeOSC(self):
        if self.oscOK:
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

    def setRang(self, chan, rang):
        if self.oscOK:
            self.osc.write(f"CHAN{chan}:RANG {rang}")

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
            self.osc.write("ACQ:COUN " + str(avg))

    def getAvrg(self):
        if self.oscOK:
            resp = self.osc.query("ACQ:COUN?")
            avgs = int(resp)
            return avgs
        else:
            return 0

    def switchAvrg(self, status):
        nstatus = int(status)
        if nstatus:
            if self.oscOK:
                self.osc.write("ACQ:TYPE AVER")
        else:
            if self.oscOK:
                self.osc.write("ACQ:TYPE NORM")

    def getAvrgState(self):
        if self.oscOK:
            acqtype = self.osc.query("ACQ:TYPE?")
            isavg = acqtype == "AVER"
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
        opc = int(self.osc.query("*OPC?"))
        # avs = int(self.osc.query("WAV:COUNT?"))
        # pder = int(self.osc.query("PDER?"))
        # if ader and opc and ((self.getAvrgState() and avs >= self.getAvrg()) or not self.getAvrgState()):
        # if ader and opc:
        if opc:
        # if pder:
            return True
        else:
            return False

    def setChannel(self, chan, state):
        s = int(state)
        self.osc.write("CHAN" + str(chan) + ":DISP " + str(s))

    def getData(self, chan):
        data = []
        if self.binary:
            data = self.getBinTrace(chan)
        else:
            data = self.getASCIITrace(chan)
        return data

    def getBinTrace(self, chan):
        if self.oscOK:
            # nchan = int(np.mod(chan, 4))
            # if nchan == 0:
            #     nchan = 4
            self.osc.write("WAV:SOUR CHAN" + str(nchan))
            rawdata = self.osc.query_binary_values("WAV:DATA?", datatype="H", is_big_endian=True)
            data = np.array(rawdata)
            # scale = float(self.osc.query("CHAN" + str(nchan) + ":SCAL?"))
            off = float(self.osc.query("CHAN" + str(nchan) + ":OFFS?"))
            yref = float(self.osc.query("WAV:YREF?"))
            # yor = float(self.osc.query("WAV:YOR?"))
            yincr = float(self.osc.query("WAV:YINC?"))
            # print(yor, off, yref)
            # volt = yor + off + (data + yref)*yincr
            volt = (data - yref)*yincr + off
            # volt = data*yincr - off

            return volt
        else:
            return np.zeros(self.traceLength)

    def getASCIITrace(self, chan):
        if self.oscOK:
            nchan = int(np.mod(chan, 4))
            if nchan == 0:
                nchan = 4
            self.osc.write("WAV:SOUR CHAN" + str(nchan))
            # self.osc.write(":WAVeform:FORMAT ASCii")
            off = float(self.osc.query("CHAN" + str(nchan) + ":OFFS?"))

            data = self.osc.query("WAV:DATA?")
            stringlist = data.split(",")
            numlist = []

            for i in range(0, len(stringlist)):
                if "#" in stringlist[i]:
                    firstitem = stringlist[i][10:]
                    firstitem.replace(" ", "")
                    numlist.append(float(firstitem))
                else:
                    numlist.append(float(stringlist[i]))
            numlist = off + np.array(numlist)
            return numlist
        else:
            return np.zeros(self.traceLength)

    def getBinFFT(self):
        if self.oscOK:
            self.osc.write("WAV:SOUR FUNC")
            rawdata = self.osc.query_binary_values("WAV:DATA?", datatype="h", is_big_endian=True)
            scale = float(self.osc.query("FUNC:SCAL?"))
            off = float(self.osc.query("FUNC:OFFS?"))
            conv = scale*4/30720
            data = off + np.array(rawdata)*conv

            fftspan = float(self.osc.query("FUNC:SPAN?"))
            fftcenter = float(self.osc.query("FUNC:CENT?"))
            start = fftcenter - fftspan/2
            stop = fftcenter + fftspan/2
            fftx = np.linspace(start, stop, len(data))
            return data
        else:
            return np.zeros(self.traceLength), np.zeros(self.traceLength)

    def setEdgeTrigger(self, chan, slope="POS", level=1000e-3):
        if self.oscOK:
            self.osc.write("TRIGger:EDGE:SOURce CHAN"+str(chan)) 
            self.osc.write("TRIGger:EDGE:SLOPe "+slope)
            self.osc.write("TRIGger:LEVel CHAN"+str(chan)+","+str(level))
