from oscDSOX3104A import OSCDSOX3104A


osc=OSCDSOX3104A()
osc.connectOSC()
def binblock_raw(data_in):
        '''
        This function interprets bytes as packed by binary data.
        It is supposed to get the output of the Yokogawa AQ6370C Optical Spectrum Analyser and convert to floats (regard-less of the span).
        '''
        
        #Grab the beginning section of the image file, which will contain the header.
        Header = str(data_in[0:12])
        #print("Header is " + str(Header))
        
        #Find the start position of the IEEE header, which starts with a '#'.
        startpos = Header.find("#")
        #print("Start Position reported as " + str(startpos))
        
        #Check for problem with start position.
        if startpos < 0:
            raise IOError("No start of block found")
            
        #Find the number that follows '#' symbol.  This is the number of digits in the block length.
        Size_of_Length = int(Header[startpos+1])
        #print("Size of Length reported as " + str(Size_of_Length))
        
        ##Now that we know how many digits are in the size value, get the size of the image file.
        Image_Size = int(Header[startpos+2:startpos+2+Size_of_Length])
        #print("Number of bytes in image file are: " + str(Image_Size))
        
        # Get the length from the header
        offset = startpos+Size_of_Length
        
        # Extract the data out into a list.
        data_raw = data_in[offset:offset+Image_Size]
        float_len=2 #A Float takes 4 chars en this packed data
        data_len=int( len(data_raw)/float_len )
        #print('Number of points in data ', data_len)
        
        output_vec=np.zeros(data_len)
        for i in range(data_len):
            output_vec[i]=struct.unpack('>e', data_raw[float_len*i:float_len*(i+1)])[0]
        
        
        return(output_vec)

import struct
osc.osc.write("WAV:DATA?")
data_in = osc.osc.read_raw()
data = binblock_raw(data_in)


laser.setWL(0, 1550):
        if self.laserOK: