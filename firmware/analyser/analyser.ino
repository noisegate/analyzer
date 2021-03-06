
/* silviamp
 * using the teensy3.2 + audioshield as pre amp using 
 * transistordyne pcb: 
 * 
 * mixing up some controls: i dont need mid so, back to normal hifi
 * BASS + TREBLE and using mid as treble, treble as width for surround
 * 1 bass = bass
 * 2 mid = treble
 * 3 treble = width
 * 4 loudness = compression
 * 5 vol = vol
 * 
 *
 *This example code is in the public domain
*/

#include <Audio.h>
#include <Wire.h>
#include <SPI.h>
#include <SD.h>
#include <SerialFlash.h>
#include <ADC.h>

#define MODE_FFT 0
#define MODE_SCOPE 1
#define MODE_SWEEP 2
#define MODE_RMS 3


const int myInput = AUDIO_INPUT_LINEIN;
// const int myInput = AUDIO_INPUT_MIC;
const int linelevel[] = {31,30,29,28,27,26,25,24,23,22,21,20,19,18,17,16,15,14,13};
const float vpp[] = {1.16,1.22,1.29,1.37,1.44,1.53,1.62,1.71,1.8,1.91,2.02,2.14,2.26,2.39,2.53,2.67,2.83,2.98,3.16};
// Create the Audio components.  These should be created in the
// order data flows, inputs/sources -> processing -> outputs
//

const int adcVol = A1;//A7
const int adcTreble = A3;
const int adcMid = A2;
const int adcBass = A14;
const int adcLoudness = A6;


int16_t fftResult[1024];

ADC *adc = new ADC();


/*
// GUItool: begin automatically generated code
AudioInputI2S            i2s1;           //xy=96.66666793823242,1655.5556259155273
AudioSynthWaveform       waveform1;      //xy=109.9999771118164,1507.7776927947998
AudioSynthWaveform       waveform2;      //xy=113.33332867092557,1570.0000403722127
AudioAnalyzeFFT256       fft256_1;       //xy=264.44444910685223,1652.2222391764324
AudioOutputI2S           i2s2;           //xy=476.6666145324707,1525.555552482605
AudioConnection          patchCord1(i2s1, 0, fft256_1, 0);
AudioConnection          patchCord2(waveform1, 0, i2s2, 0);
AudioConnection          patchCord3(waveform2, 0, i2s2, 1);
AudioControlSGTL5000     sgtl5000_1;     //xy=438.88888888888886,1861.111111111111
// GUItool: end automatically generated code

// GUItool: begin automatically generated code
AudioInputI2S            i2s1;           //xy=96.66666793823242,1655.5556259155273
AudioSynthWaveform       waveform1;      //xy=109.9999771118164,1507.7776927947998
AudioSynthWaveform       waveform2;      //xy=113.33332867092557,1570.0000403722127
AudioAnalyzeFFT1024      fft1024_1;      //xy=277,1650
AudioOutputI2S           i2s2;           //xy=476.6666145324707,1525.555552482605
AudioConnection          patchCord1(i2s1, 0, fft1024_1, 0);
AudioConnection          patchCord2(waveform1, 0, i2s2, 0);
AudioConnection          patchCord3(waveform2, 0, i2s2, 1);
AudioControlSGTL5000     sgtl5000_1;     //xy=418.8888854980469,1735.111083984375
// GUItool: end automatically generated code
*/
// GUItool: begin automatically generated code
AudioInputI2S            i2s1;           //xy=102.66666793823242,198.55564308166504
AudioSynthWaveform       waveform1;      //xy=115.9999771118164,50.7777099609375
AudioSynthWaveform       waveform2;      //xy=119.33332867092557,113.00005753835035
AudioAnalyzeRMS          rms1;           //xy=277,249.0000171661377
AudioAnalyzeFFT1024      fft1024_1;      //xy=283,193.0000171661377
AudioOutputI2S           i2s2;           //xy=560.6666259765625,78.5555591583252
AudioConnection          patchCord1(i2s1, 0, fft1024_1, 0);
AudioConnection          patchCord2(i2s1, 0, rms1, 0);
AudioConnection          patchCord3(waveform1, 0, i2s2, 0);
AudioConnection          patchCord4(waveform2, 0, i2s2, 1);
AudioControlSGTL5000     sgtl5000_1;     //xy=424.8888854980469,278.1111011505127
// GUItool: end automatically generated code



void setup() {
  // Audio connections require memory to work.  For more
  // detailed information, see the MemoryAndCpuUsage example
  AudioMemory(12);
  // Enable the audio shield and set the output volume.
  sgtl5000_1.enable();
  sgtl5000_1.inputSelect(myInput);
  sgtl5000_1.volume(0.8);
  // just enable it to use default settings.
  sgtl5000_1.audioPreProcessorEnable();
  sgtl5000_1.audioPostProcessorEnable();
  
  
  sgtl5000_1.eqSelect(2);//tone control mode 
  
  sgtl5000_1.eqBands(0.0, 0.0);
  sgtl5000_1.lineInLevel(5);//def
  sgtl5000_1.lineOutLevel(13);//def 29=def
  sgtl5000_1.dacVolume(1.0);
  sgtl5000_1.unmuteHeadphone();
  

  waveform2.begin(WAVEFORM_ARBITRARY);
  waveform2.frequency(128.0);
  waveform2.amplitude(1.0);

  fft1024_1.windowFunction(AudioWindowHanning1024);

  for (int16_t i=0; i<512;i++){
    fftResult[i]=(int16_t)(i*255);
  }
  waveform2.arbitraryWaveform(fftResult, 172.0);
  waveform1.begin(0.4, 1000, WAVEFORM_SINE);//level, freq, waveform
  
  //ADC stuff
  pinMode(adcVol, INPUT);
  pinMode(adcTreble, INPUT);
  pinMode(adcMid, INPUT);
  pinMode(adcBass, INPUT);
  pinMode(adcLoudness, INPUT);
  
  adc->setReference(ADC_REF_3V3, ADC_0);
  adc->setAveraging(32);
  adc->setResolution(10);
  adc->setConversionSpeed(ADC_LOW_SPEED);
  adc->setSamplingSpeed(ADC_LOW_SPEED);
  
  //serial comm
  Serial.begin(38400);
  
}

elapsedMillis chgMsec=0;

float diff;
float sign;
int inByte;
int step;
int level=2;//default 
int freq=1000;
int modeofoperation = MODE_FFT;//default

float peakval=0.0;

//performance
float ACPU;
float AMEM;
float CPU;
float MEM;
float myvolume = 0.4;
float oldvol =0.0;
float currfreq = 0.0;

void loop() {
  
  // every 10 ms, check for adjustment
  if (chgMsec > 50) { // more regular updates for actual changes seems better.
    
    float vol1=analogRead(15)/1023.0;

    if (1/*modeofoperation == MODE_FFT*/)
      if (vol1!=oldvol){
        currfreq = vol1*20000;
        waveform1.frequency(currfreq);
        oldvol = vol1;
      }
    
    if (Serial.available()>0){
      inByte = Serial.read();
      if (inByte=='f'){
        modeofoperation = MODE_FFT;
        goto exitif;
      }
      if (inByte=='+'){
        currfreq +=1.0;
      }
      if (inByte=='-'){
        currfreq -=1.0;
      }
      if (inByte=='r'){
        modeofoperation = MODE_RMS;
      }
      if (inByte=='s'){
        modeofoperation = MODE_SWEEP;
        goto exitif;
      }
      if (inByte=='d'){
          myvolume-=0.1;
          waveform1.amplitude(myvolume);
       }
      if (inByte=='D'){
          myvolume+=0.1;
          waveform1.amplitude(myvolume);
        //sgtl5000_1.audioProcessorDisable();
      }
      if (inByte=='e'){

        //sgtl5000_1.audioPostProcessorEnable();
      }

      if (inByte == 'B'){

      }
      //sgtl5000_1.eqBands(bass, midbass, mid, midtreble, treble);

      //Some of the extra stuff
      
      ACPU = AudioProcessorUsage();
      AMEM = AudioMemoryUsage();
//      CPU = peak1.processorUsage();

      if (modeofoperation == MODE_RMS){
        waveform1.frequency(currfreq);
        Serial.print(currfreq, 4);
        Serial.print(":");
        if(rms1.available()){
          float rms = rms1.read();
          Serial.print(rms,6);
        }
        Serial.println();
      }

      if (modeofoperation == MODE_SWEEP){
        freq = Serial.parseInt();
        waveform1.frequency(freq);
        Serial.print(freq);
        Serial.print(":");
        float rms = 0.0;
        for (int count=0; count<10; count++){
          if(rms1.available()){
            rms += rms1.read();
          }
        }
        Serial.print(rms/10.0, 4);  
        Serial.println();
      }

      if (modeofoperation == MODE_FFT){
        
        if (fft1024_1.available()){
          Serial.print(vol1*20000);
          Serial.print(":");
          Serial.print(myvolume);
          Serial.print(":");
          for (int i=0; i<512;i++){
            float res = fft1024_1.read(i);
            Serial.print(res,4);
            Serial.print(":");
            
            //fftResult[i] = (int16_t)(32768.0*res);
          }
  
          Serial.println();          
          //waveform2.arbitraryWaveform(fftResult, 172.0);
        }
      }
    
     //Serial.print(bass);     //0

    }//end if serial
exitif:
    
    chgMsec = 0;
    

  }//ifms
}//loop

