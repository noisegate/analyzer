import pygame, sys
from pygame.locals import *
import serial
import numpy as np
from scipy.signal import argrelextrema

ser = serial.Serial(
    port='/dev/ttyACM0',
    baudrate=38400,#9600,
    parity=serial.PARITY_ODD,
    stopbits=serial.STOPBITS_TWO,
    bytesize=serial.SEVENBITS
    )


class Const(object):

    W = 640
    H = 480

    margin = 10

    rW = W-margin
    rH = H-margin
    r2W = rW-margin
    r2H = rH-margin

    halfW = W/2
    halfH = H/2
        
    #scaling

    xs = r2W/512.0

    @classmethod
    def rescale(cls):
        pass

class Colors(object):
    red = pygame.Color(255, 0, 0)
    darkred = pygame.Color(80,0,0)
    blue =  pygame.Color(0, 0, 255)
    green  = pygame.Color(0, 255, 0)
    white = pygame.Color(255, 255, 255)
    black = pygame.Color(0,0,0)
    
class Axes(object):

    def __init__(self, surface):
        self.surface = surface
        
    def settext(self, text, x, y, size):
        fontinstance = pygame.font.Font('freesansbold.ttf', size)

        renderinstance = fontinstance.render(text, False, Colors.blue)
        rectinstance = renderinstance.get_rect()
        rectinstance.topleft=(x, y)
        self.surface.blit(renderinstance, rectinstance)

    def draw(self):
        pygame.draw.line(self.surface, Colors.darkred, (Const.margin,Const.margin), (Const.rW,Const.margin), 2)
        pygame.draw.line(self.surface, Colors.darkred, (Const.rW,Const.margin), (Const.rW, Const.rH), 2)
        pygame.draw.line(self.surface, Colors.darkred, (Const.rW, Const.rH), (Const.margin, Const.rH), 2)
        pygame.draw.line(self.surface, Colors.darkred, (Const.margin,Const.rH), (Const.margin, Const.margin), 2)
        for i in range(10):
            pygame.draw.line(self.surface, Colors.darkred, (i*Const.W/10, Const.margin),(i*Const.W/10,Const.rH), 1)

class Main(object):

    def __init__(self):
        pygame.init()
        self.fps = pygame.time.Clock()
        self.Surface = pygame.display.set_mode((Const.W, Const.H))
        pygame.display.set_caption("Teensy Analyser")

        self.red = pygame.Color(255, 0, 0)
        self.blue =  pygame.Color(0, 0, 255)
        self.green  = pygame.Color(0, 255, 0)

        self.axes = Axes(self.Surface)

        self.fourier = np.zeros(512, dtype=np.float)
        self.waveform = np.zeros(512, dtype=np.float)

    def plotfft(self):
        yscale = 0.8 * Const.r2H/np.max(self.fourier)
        offset = -10
        for i in range(511):
            pygame.draw.line(    self.Surface,
                                Colors.red, 
                                (int(10+Const.xs*i), Const.rH-yscale * self.fourier[i] + offset), 
                                (int(10+Const.xs*(i+1)), Const.rH-yscale * self.fourier[i+1]+ offset))

    def plotpeaks(self):
        #http://stackoverflow.com/questions/4624970/finding-local-maxima-minima-with-numpy-in-a-1d-numpy-array
        extrema = argrelextrema(self.fourier, np.greater)
               
        ea=extrema[0]
        peaks = self.fourier[ea]
        harm = 0.0
        fund = 0.0

        for i in range(len(peaks)):
            pygame.draw.circle( self.Surface, 
                                Colors.blue, 
                                (   int(10+Const.xs*ea[i])+1, 
                                     Const.r2H-int(1.0*Const.H*peaks[i])
                                ), 
                                2,
                                0)    
            if i==0:
                fund = peaks[i]
            else:
                harm = harm + peaks[i]**2
            try:
                thd =  np.sqrt(harm)/(fund)*100
            except:
                thd = -1
            self.axes.settext("THD: {0}%".format(thd), Const.halfW, 20, 16)
            try:
                self.axes.settext("fund: {0}kHz".format(ea[0]*44.032), 10, 40, 16)
            except:
                pass
            for i in range(10):
                self.axes.settext(" {0}k ".format(i/10.0*20), i*64, Const.rH, 8)

        return thd                

    def loop(self):
        self.Surface.fill(Colors.black)
        self.axes.draw()
        pygame.display.update()
        while True:
            
            i=0
           
            ser.write('?');#get the fourier data
            msg=[]
            while ser.inWaiting() > 0:
                dummy = ser.read(1)
                msg.append(dummy)
                i=1
            
            if (i>0):
                self.Surface.fill(Colors.black)
                self.axes.draw()
                msgstr = ''.join(msg)
                vals = msgstr.split(':')
                #self.Bassbar.set(float(vals[0]))
                preval =0
                for i, val in enumerate(vals):
                    #the first bytes are header with parameter info
                    if (i==0):
                        #freq
                        try:
                            freq = float(val)
                        except:
                            freq=-1

                        #print "frequency: {0}Hz\n".format(freq)
                        self.axes.settext("freq: {0}Hz".format(freq), 10, 10, 32)

                    #the last 512 bytes are FFT data
                    elif (i<512):                   
                    #print val
                        try:
                            y = int(float(val)*Const.H)
                            self.fourier[i] = float(val)
                            #actual drawing somewhere else pls.
                        except:
                            self.fourier[i] = 0.0
                
                self.plotfft()
                thd = self.plotpeaks()

                pygame.display.update()

            for event in pygame.event.get():
                if event.type == QUIT:
                    pygame.quit()
                    sys.exit()

                if event.type == KEYDOWN:
                    if event.key == K_ESCAPE:
                        pygame.event.post(pygame.event.Event(QUIT))
                    if event.key == K_d:
                        ser.write('d')
                    if event.key == K_i:
                        ser.write('D')


            self.fps.tick(5)

if __name__ == '__main__':
    instance = Main()
    instance.loop()
