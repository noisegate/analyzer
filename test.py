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


class Constants(object):

    W = 640
    H = 480

    #scaling

    xs = 620.0/512.0

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
        pygame.draw.line(self.surface, Colors.darkred, (10,10),(630,10),2)
        pygame.draw.line(self.surface, Colors.darkred, (630,10),(630,470),2)
        pygame.draw.line(self.surface, Colors.darkred, (630,470),(10,470),2)
        pygame.draw.line(self.surface, Colors.darkred, (10,470),(10,10),2)
        for i in range(10):
            pygame.draw.line(self.surface, Colors.darkred, (i*64, 10),(i*64,470),1)

class Main(object):

    def __init__(self):
        pygame.init()
        self.fps = pygame.time.Clock()
        self.Surface = pygame.display.set_mode((640,480))
        pygame.display.set_caption("Teensy Analyser")

        self.red = pygame.Color(255, 0, 0)
        self.blue =  pygame.Color(0, 0, 255)
        self.green  = pygame.Color(0, 255, 0)

        self.axes = Axes(self.Surface)

        self.fourier = np.zeros(512, dtype=np.float)

    def loop(self):
        self.Surface.fill(Colors.black)
        self.axes.draw()
        pygame.display.update()
        while True:
            
            i=0
           
            ser.write('?');
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
                    if (i==0):
                        #freq
                        try:
                            freq = float(val)
                        except:
                            freq=-1

                        #print "frequency: {0}Hz\n".format(freq)
                        self.axes.settext("freq: {0}Hz".format(freq), 10, 10, 32)


                    elif (i<512):                   
                    #print val
                        try:
                            y = int(float(val)*480)
                            self.fourier[i] = float(val)

                            pygame.draw.line(   self.Surface, 
                                                Colors.red, 
                                                (int(10+Constants.xs*i), 460-preval), 
                                                (int(10+Constants.xs*(i+1)), 460-y))
                            preval = y
                        except:
                            pass
                #http://stackoverflow.com/questions/4624970/finding-local-maxima-minima-with-numpy-in-a-1d-numpy-array
                extrema = argrelextrema(self.fourier, np.greater)
                
                ea=extrema[0]
                peaks = self.fourier[ea]
                harm = 0.0
                fund = 0.0
                for i in range(len(peaks)):
                     pygame.draw.circle(self.Surface, Colors.blue, (int(10+Constants.xs*ea[i])+1, 460-int(480.0*peaks[i])), 2,0)    
                     if i==0:
                        fund = peaks[i]
                     else:
                        harm = harm + peaks[i]**2
                
                try:
                    thd =  np.sqrt(harm)/(fund)*100
                except:
                    thd = -1
                self.axes.settext("THD: {0}%".format(thd), 320, 20, 16)
                try:
                    self.axes.settext("fund: {0}kHz".format(ea[0]*44.032), 10, 40, 16)
                except:
                    pass
                for i in range(10):
                    self.axes.settext(" {0}k ".format(i/10.0*20), i*64,470, 8)

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
