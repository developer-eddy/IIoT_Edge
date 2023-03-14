import spidev
import RPi.GPIO as GPIO
import time
import paho.mqtt.client as mqtt
import lcd_write_lib as LCD
import pymysql

GPIO.setmode(GPIO.BCM)
spi=spidev.SpiDev()
spi.open(0,0)
spi.max_speed_hz=500000
SOUND=26
SOUND_LED=17
LED=21
VIB_WARN=1
CHECK_ON=0
GPIO.setup(SOUND, GPIO.IN)
GPIO.setup(SOUND_LED, GPIO.OUT)
mgt_client = mqtt.Client("test")
mgt_client.connect("???.???.???.???",1883,60)

def read_spi_adc(adcChannel):
    adcValue=0
    buff=spi.xfer2([1,(8+adcChannel)<<4,0])
    adcValue = ((buff[1]&3<<8)+buff[2])
    return adcValue

conn=pymysql.connect(host="localhost", user="", passwd="", db="raspi_db")
sql="insert into collect_data_dust values(%s,%s,%s)"
sub1="select AVG(value),MIN(value),MAX(value) from collect_data_dust"
sub2="where DATE(collect_time) - DATE(NOW()) < 7"
sql2=sub1+sub2

sql="insert into collect_data_noise values()"
sub1="select dB(value) from collect_data_noise"
sub2="where DATE(collect_time) - DATE(NOW()) < 7"
sql2=sub1+sub2

try:
    with conn.cursor() as cur :
        lcd_device=LCD.lcd()

    while True : 
        adcChannel=0
        chk_vib_flg=0
        adcValue=read_spi_adc(adcChannel)
        if adcValue > VIB_WARN :
            chk_vib_flg=1
        if GPIO.input(SOUND)==CHECK_ON :
            chk_sound_flg=1
        else :
            chk_sound_flg=0
            snd_str=str(chk_vib_flg)+","+str(chk_sound_flg)
            mgt_client.publish("raspberry",snd_str)
        if chk_vib_flg and chk_sound_flg :
            GPIO.output(SOUND_LED,GPIO.LOW)
            time.sleep(0.2)
        else :
            GPIO.output(SOUND_LED,GPIO.LOW)
            time.sleep(1)
        calVoltage = adcValue*(5.0/1024.0)
        dust_data = (0.172*calVoltage-0.01)*1000
        noise_data = (20*calVoltage)
        print("dust %d"%dust_data,"noise %d"%noise_data)

        cur.execute(sql,('dust',time.strftime("%Y-%m-%d %H:%M:%S",time.localtime()),dust_data))
        cur.execute(sql,('noise',time.strftime("%Y-%m-%d %H:%M:%S",time.localtime()),noise_data))

        cur.execute(sql2)
        row=cur.fetchone()
        lcd_device.lcd_display_string("CURRENT DUST:%d"%(dust_data),1)
        lcd_device.lcd_display_string("AVG:%.1f MIN:%d"%(row[0],row[1]),2)
        lcd_device.lcd_display_string("CURRENT NOISE:%d"%(noise_data),1)

        conn.commit()
        time.sleep(2)
        lcd_device.lcd_clear()

except Exception as e :
    print(e)
finally :
    GPIO.cleanup()
    spi.close()
    conn.close()
