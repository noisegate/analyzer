import pygame, sys
import getopt
from pygame.locals import *
import serial   
import numpy as np
from scipy.signal import argrelextrema
import time
import socket
import subprocess

ser = serial.Serial(
    port='/dev/ttyACM0',
    baudrate=38400,#9600,
    parity=serial.PARITY_ODD,
    stopbits=serial.STOPBITS_TWO,
    bytesize=serial.SEVENBITS
    )

MODE_FFT = 0
MODE_SWEEP = 2
MODE_THD = 4
MODE_RMS = 3

class Gnuplotter(object):
    
    script = """set logscale x 10
                set logscale y 10
                set grid mxtics mytics xtics ytics lt 1 lc rgb 'gray70', lt 1 lc rgb 'gray90'
                set mxtics 10
                set mytics 5

                set boxwidth 8

                set title "{title}" 
                set xlabel "freq[Hz]"
                set ylabel "amp[rel.]"

                set xrange [10:50000]
                set yrange [0.001: 1]
                
                plot {plot}

                set size 1.0, 1.0
                #set terminal postscript portrait enhanced mono dashed lw 1 "Helvetica" 14 
                #set terminal pngcairo  transparent enhanced font "arial,10" fontscale 1.0 size 500,500; set zeroaxis;
                #set terminal pngcairo  enhanced font "arial,20" fontscale 1.0 size 1500,1500; 
                #set output "my-plot.png"
                #set terminal pdf
                #set output "my-plot.pdf"
                set term svg enhanced font "arial,20" mouse size 1500,1200
                set output "./tmp/my-plot.svg"
                replot
                set terminal x11
                set size 1,1

                #pause -1
            """

    def __init__(self, plotfiles):
        myfile = open("./tmp/gnuplot.scr","w")
        string = ''
        for name in plotfiles:
            string += '"{name}" using 1:2 smooth csplines title "{title}" with lines,'.format(name=name, title=name) 
        
        script = self.script.format(
                    title = 'frequency sweep',
                    plot =  string
                )   
        
        myfile.write(script)
        myfile.close()

    def plot(self):
        subprocess.Popen("gnuplot ./tmp/gnuplot.scr", shell=True, stdout=subprocess.PIPE).stdout.read()
 
class Const(object):

    #W = 1280#640
    #H = 800#480
    #W = 1366
    #H = 768
    W = 640
    H = 480

    FULLSCREEN = True

    margin = 10

    rW = W-margin
    rH = H-margin
    r2W = rW-margin
    r2H = rH-margin

    halfW = W/2
    halfH = H/2
        
    #ip = socket.gethostbyname(socket.gethostname())
    #scaling
    ip = "NIY"
    xs = r2W/512.0

    linewidth = 2	

    @classmethod
    def rescale(cls):
        pass

    @classmethod
    def raspi(cls):
        cls.W = 1280
        cls.H = 800

    @classmethod
    def desktop(cls):
        cls.W = 1280
        cls.H = 1024

    @classmethod
    def laptop(cls):
        cls.W = 1366
        cls.H = 768

    @classmethod
    def window(cls):
        cls.W = 640
        cls.H = 480
        cls.FULLSCREEN = False

class Colors(object):
    red = pygame.Color(255, 0, 0)
    darkred = pygame.Color(150,0,0)
    darkerred = pygame.Color(80,0,0)
    blue =  pygame.Color(0, 0, 255)
    green  = pygame.Color(0, 255, 0)
    white = pygame.Color(255, 255, 255)
    black = pygame.Color(0,0,0)
    darkgrey = pygame.Color(100,100,100)
    background = black

class Handleargs(object):
    #http://www.tutorialspoint.com/python/python_command_line_arguments.htm
    def __init__(self, argv):
        self.argv = argv
        self.device = ""

    def process(self):
        try:
            opts, args = getopt.getopt(self.argv,"hd:",["ifile=","ofile="])
        except getopt.GetoptError:
             print 'analyzer.py -d <device> '
             sys.exit(2)
        for opt, arg in opts:
            if opt == '-h':
                f=open('help.txt', 'r')
                for line in f.readlines():
                    print line,
                f.close()
                sys.exit()
            if opt == '-d':
                self.device = arg
                if arg == 'raspi':
                    Const.raspi()
                if arg == 'desktop':
                    Const.desktop()
                if arg == 'laptop':
                    Const.laptop()
                if arg == 'window':
                    Const.window()

class Axes(object):

    def __init__(self, surface):
        self.surface = surface
        
    def settext(self, text, x, y, size,center):
        fontinstance = pygame.font.Font('freesansbold.ttf', size)

        renderinstance = fontinstance.render(text, False, Colors.blue)
        rectinstance = renderinstance.get_rect()

        if (center):
            rectinstance.centerx = x
            rectinstance.centery = y
        else:
            rectinstance.topleft=(x, y)
        self.surface.blit(renderinstance, rectinstance)

    def frame(self):
        pygame.draw.line(self.surface, Colors.darkred, (Const.margin,Const.margin), (Const.rW,Const.margin), 2)
        pygame.draw.line(self.surface, Colors.darkred, (Const.rW,Const.margin), (Const.rW, Const.rH), 2)
        pygame.draw.line(self.surface, Colors.darkred, (Const.rW, Const.rH), (Const.margin, Const.rH), 2)
        pygame.draw.line(self.surface, Colors.darkred, (Const.margin,Const.rH), (Const.margin, Const.margin), 2)


    def draw(self):
        self.frame()
        for i in range(10):
            pygame.draw.line(self.surface, Colors.darkred, (i*Const.W/10, Const.margin),(i*Const.W/10,Const.rH), 1)

    def drawlog(self):
        self.frame()
        self.settext('ip {0}'.format(Const.ip),1100,10,18, False)
        logrange =  [1, 10.0,100.0,1000.0,10000.0]

        for i in [0,1,2,3]:
            currX = int(np.log10(logrange[i])*Const.r2W/4.0)+Const.margin
            self.settext(" {0}Hz ".format(logrange[i+1]), currX, Const.rH, 10, False)
 
            for j in np.arange(logrange[i], logrange[i+1], logrange[i], dtype=np.float):
                
                pygame.draw.line(   self.surface, 
                                    Colors.darkred, 
                                    (int(1.0*np.log10(j)*Const.r2W/4.0)+Const.margin, Const.margin),
                                    (int(1.0*np.log10(j)*Const.r2W/4.0)+Const.margin, Const.rH), 
                                    1)

            pygame.draw.line(   self.surface, 
                                Colors.darkred, 
                                (currX, Const.margin),
                                (currX,Const.rH), 
                                1)



class Stats(object):

    def __init__(self, wav):
        self.wav = wav
        self.max = None
        self.min = None
        self.rms = None
        self.std = None

        self.dostats()

    def dostats(self):
        self.max = np.nanmax(self.wav)        
        self.min = np.nanmin(self.wav)
        self.std = np.nanstd(self.wav)

class Main(object):

    def __init__(self):
        pygame.init()
        self.fps = pygame.time.Clock()
        if (Const.FULLSCREEN):
            self.Surface = pygame.display.set_mode((Const.W, Const.H), pygame.FULLSCREEN)
        else:
            self.Surface = pygame.display.set_mode((Const.W, Const.H))
	pygame.display.set_caption("Teensy Analyser")

        self.red = pygame.Color(255, 0, 0)
        self.blue =  pygame.Color(0, 0, 255)
        self.green  = pygame.Color(0, 255, 0)

        self.axes = Axes(self.Surface)

        self.fourier = np.zeros(512, dtype=np.float)
        self.waveformx = np.zeros(1024, dtype=np.int)
        self.waveformy = np.zeros(1024, dtype=np.float)
        self.calibrate = np.ones(1024, dtype=np.float)
        self.modeofoperation = MODE_FFT
        
        self.loadcalibration()


    def loadcalibration(self):
        file = open("./cal.dat", 'r')

        lines = file.readlines()

        for i, line in enumerate(lines):
            l=line.split(' ')
            self.calibrate[i] = float(l[1])

    def scaleme(self):
        yscale = 0.8 * Const.r2H/np.max(self.fourier)
        return yscale

    def plotsweep(self, points, scale):
        #points should be less than 2000
        yscale= Const.r2H/1.0;
        xscale= Const.r2W/4;
        offset = -Const.halfH
        xoffset=xscale
        self.Surface.fill(Colors.background)
        self.axes.drawlog()
        self.axes.settext("Sweep mode", 10, 10, 32, False)

        if scale:
            pass

        for i in range(points):
            if i>2:
                if np.log10(self.waveformx[i])>0:
                    x1 = np.log10(self.waveformx[i])
                else:
                    x1 = 0
                if np.log10(self.waveformx[i+1])>0:
                    x2 = np.log10(self.waveformx[i+1])
                else:
                    x2 = 0
                pygame.draw.line(   self.Surface,
                                    Colors.red,
                                 (  int(10+xscale*x1)-xoffset, 
                                    int(1.0*Const.rH-yscale*0.1*np.log10(self.calibrate[i]*self.waveformy[i])+offset)),
                                 (  int(10+xscale*x2)-xoffset, 
                                    int(1.0*Const.rH-yscale*0.1*np.log10(self.calibrate[i+1]*self.waveformy[i+1])+offset)),
                                    Const.linewidth)
        pygame.display.update()

    def plotfft(self, bins, withpeaks):
        yscale = self.scaleme()
        offset = -10

        xscale = 1.0 * Const.r2W/bins

        for i in range(bins-1):
            try:
                pygame.draw.line(    self.Surface,
                                    Colors.red, 
                                    (int(10+xscale*i), Const.rH-yscale * self.fourier[i] + offset), 
                                    (int(10+xscale*(i+1)), Const.rH-yscale * self.fourier[i+1]+ offset))
            except:
                pass

        if withpeaks:
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
                                        int(Const.rH-yscale*peaks[i] + offset)
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
                self.axes.settext("THD: {0}%".format(thd), Const.halfW, 20, 16, False)
                try:
                    self.axes.settext("fund: {0}kHz".format(ea[0]*44.032), 10, 40, 16, False)
                except:
                    pass
                for i in range(10):
                    self.axes.settext(" {0}k ".format(i/10.0*20), i*64, Const.rH, 10, False)
    
            return thd                

    def rms(self):
        i=0
        self.Surface.fill(Colors.background)
        self.axes.frame()
        ser.write('?')
        msg =[]
        while ser.inWaiting() > 0:
            dummy = ser.read(1)
            msg.append(dummy)
            i=1
        
        if (i>0):
            self.Surface.fill(Colors.background)
            self.axes.frame()
            msgstr = ''.join(msg)
            vals = msgstr.split(':')
            for i, val in enumerate(vals):
                try:
                    if (i==0):
                        freq = float(val)
                    if (i==1):
                        rms = float(val)
                except:
                    rms = -1
                    freq=-1
            self.axes.settext("RMS @ {0:04d}Hz = {1:.2f}V".format(int(freq), rms), Const.halfW ,Const.halfH, 32, True)
        pygame.display.update()

    def fft(self):
        i=0
        ser.write('?');#get the fourier data
        msg=[]
        while ser.inWaiting() > 0:
            dummy = ser.read(1)
            msg.append(dummy)
            i=1
        
        if (i>0):
            self.Surface.fill(Colors.background)
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
                    self.axes.settext("freq: {0}Hz".format(freq), 10, 10, 32, False)
                elif (i==1):
                    try:
                        vol = float(val)
                    except:
                        vol = -1
                    self.axes.settext("level: {0}".format(vol), 300,10,32, False)    
                #the last 512 bytes are FFT data
                elif (i<512):                   
                #print val
                    try:
                        self.fourier[i] = float(val)
                    except:
                        self.fourier[i] = 0.0
        
            thd = self.plotfft(512, False)
    
            pygame.display.update()

    def sweep(self): 
        N=128
        s=''
        for i, fr in enumerate(np.logspace(1.3, 4.3, N)):
            ser.write("?{0}".format(int(fr)))
            msg=[]
            #print "{0} % done".format(1.0*i/N)
            time.sleep(.05)
            while ser.inWaiting()>0:
                dummy = ser.read(1)
                msg.append(dummy)
            
            msgstr = ''.join(msg)
            vals = msgstr.split(':')
            try:
                f = int(vals[0])
                a = float(vals[1])
                self.waveformx[i] = f
                self.waveformy[i] = a
            except:
                pass
            if (i & 10 == 0):
                self.plotsweep(i, False)
            s = self.eventhandler()
            if s == 'f':
                break
            if s == 'r':
                break

        stats = Stats(self.waveformy)
        print stats.max
        print stats.min
        print stats.std

        if s=='':
            file = open('./tmp/sweep.dat', 'w')
            for i, j in enumerate(self.waveformx):
               file.write("{0} {1}\r\n".format(j, self.calibrate[i]*self.waveformy[i]))
            file.close()
            self.axes.settext("select: s=sweep, c=save calibration, f=back to fft mode", Const.halfW, Const.r2H, 16, True)
            pygame.display.update()
            plotje = Gnuplotter(['./tmp/sweep.dat'])
            plotje.plot()
            while s=='':
                s = self.eventhandler()

        if (s=='c'):
            file = open('cal.dat', 'w')
            for i, j  in enumerate(self.waveformx):
                if self.waveformy[i]!=0.0:
                    self.calibrate[i] = 1.0/self.waveformy[i]
                else:
                    self.calibrate[i]=1.0
                file.write("{0} {1}\r\n".format(j, self.calibrate[i]))
            file.close()

    def eventhandler(self):
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
                if event.key == K_s:
                    #got to sweep mode
                    ser.write('s')
                    self.modeofoperation = MODE_SWEEP

                if event.key == K_r:
                    ser.write('r')
                    self.modeofoperation = MODE_RMS
                    return 'r'

                if event.key == K_f:
                    #go to fft mode
                    ser.write('f')
                    self.modeofoperation = MODE_FFT
                    return 'f'
        return ''

    def loop(self):
        self.Surface.fill(Colors.black)
        self.axes.draw()
        self.axes.settext("Initializing...", 10,10,32, False)
        pygame.display.update()

        ser.write('f')#make sure we are in default FFT modus

        print "Initializing..."

        time.sleep(5)
        
        while True:
            
            if (self.modeofoperation == MODE_RMS):
                self.rms()

            if (self.modeofoperation == MODE_THD):
                pass

            if (self.modeofoperation == MODE_FFT):
                self.fft()
           
            if (self.modeofoperation == MODE_SWEEP):
                self.sweep()

            self.eventhandler()
            self.fps.tick(5)

if __name__ == '__main__':
    arghandler = Handleargs(sys.argv[1:])
    arghandler.process()
    instance = Main()
    instance.loop()
