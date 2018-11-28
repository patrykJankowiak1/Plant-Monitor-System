#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import sys
import logging
import sqlite3
from time import sleep
import spidev
from utility import read_config, get_timestamp, deep_get
import Adafruit_DHT

VERSION = "1.0.0"

class PlantMonitorSystem(object):
    def __init__(self):
        self.db_name = deep_get(CFG, 'database_name', default = "pms.db")
        self.adc_init()
        self.database_init()
        self.date = {
            "timestamp": 0,
            "light_intensity": 0,
            "soil_moisture": 0,
            "air_humidity": 0,
            "temperature": 0
        }

    def database_init(self):
        con = None
        if os.path.exists(self.db_name):
            logging.info("Database %s exist", self.db_name)
        else:
            try:
                con = sqlite3.connect(self.db_name)
                logging.info("Database %s created", self.db_name)
                cur = con.cursor()
                cur.execute('''
                    CREATE TABLE pms (
                        id integer primary key autoincrement,
                        timestamp text,
                        light_intensity real,
                        soil_moisture real,
                        air_humidity real,
                        temperature real)
                ''')
                con.commit()
            except Exception as exc:
                logging.exception(exc)
                if con:
                    logging.debug("Database rollback")
                    con.rollback()
            finally:
                if con:
                    logging.debug("Database closed")
                    con.close()

    def insert_to_db(self):
        logging.debug("insert_to_database")
        con = None
        if not os.path.exists("pms.db"):
            logging.debug("Database %s not exist", self.db_name)
        else:
            try:
                con = sqlite3.connect("pms.db")
                logging.debug("Connected to %s", self.db_name)
                cur = con.cursor()
                cur.execute(
                    '''INSERT INTO pms(timestamp, light_intensity, soil_moisture, air_humidity, temperature ) VALUES(?,?,?,?,?)''', (
                        self.date["timestamp"],
                        self.date["light_intensity"],
                        self.date["soil_moisture"],
                        self.date["air_humidity"],
                        self.date["temperature"]
                    ))
                con.commit()
            except Exception as exc:
                logging.exception(exc)
                if con:
                    logging.debug("Database rollback")
                    con.rollback()
            finally:
                if con:
                    logging.debug("Database closed")
                    con.close()

    def get_sensor_date(self):
        self.date["timestamp"] = get_timestamp()
        self.date["light_intensity"] = self.get_light_intensity()
        self.date["soil_moisture"]  = self.get_soil_moisture()
        self.date["air_humidity"] = self.get_air_humidity()
        self.date["temperature"] = self.get_temperature()

    def adc_init(self):
        """Initialization SPI protocol from analog-digital converter mcp3008"""
        logging.info("Initialization SPI protocol for ADC mcp3008")
        self.spi = spidev.SpiDev()
        self.spi.open(0, 0)

    def get_adc_with_channel(self, channel):
        if (channel > 7) or (channel < 0):
            logging.error("Not corrected channel: %d", channel)
            return None
        adc = self.spi.xfer2([1, (8 + channel) << 4, 0])
        data = ((adc[1] & 3) << 8) + adc[2]
        percent = int(round(data / 10.24))
        return 100 - percent

    def get_temperature(self):
        return Adafruit_DHT.read_retry(Adafruit_DHT.DHT11, 4)[1]

    def get_air_humidity(self):
        return Adafruit_DHT.read_retry(Adafruit_DHT.DHT11, 4)[0]

    def get_soil_moisture(self):
        return self.get_adc_with_channel(deep_get(CFG, "adc_channel", "soil_moisture", default = 1))

    def get_light_intensity(self):
        return self.get_adc_with_channel(deep_get(CFG, "adc_channel", "light_intensity", default = 0))

if __name__ == "__main__":

    logging.basicConfig(level = logging.INFO, stream = sys.stderr, format = "[%(levelname)s] %(message)s")
    logging.info("Started %s v.%s", sys.argv[0], VERSION)

    if len(sys.argv) < 2:
        logging.error("Configuration file is requirements")
        sys.exit(1)
    else:
        CFG = read_config(sys.argv[1])

    PMS = PlantMonitorSystem()

    while True:
        PMS.get_sensor_date()
        logging.info(PMS.date)
        PMS.insert_to_db()
        sleep(deep_get(CFG, "sleep", default = 5))
