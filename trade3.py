import os
import re
import json
import math
from urllib import request
from datetime import datetime

log_filename = 'trade3.log'

def clear_file(filename):
    f = open(filename, mode = 'w', encoding = 'utf-8')
    f.close()

def logging(text, tag = 'INFO'):
    with open(log_filename, mode = 'a', encoding = 'utf-8') as f:
        f.write(str(datetime.now()) + ' [' + tag + '] ' + text + '\n')
    f.close()

def get_web_object(url, filename): 
    request.urlretrieve(url, filename=filename)

class CacheData(object):
    """docstring for Cache_Data"""
    def __init__(self):
        super(CacheData, self).__init__()
        #
        self.cd_pr = 'prices'
        self.cd_sm = 'systems'
        self.cd_st = 'stations'
        self.cd_sd = 'systems_distance'
        self.cache_data = {self.cd_pr: {}, self.cd_sm: {}, self.cd_st: {}, self.cd_sd: {}}
        # 
        self.system_data_file = 'System.csv'
        self.system_data_url = 'http://www.davek.com.au/td/System.csv'
        self.station_data_file = 'Station.csv'
        self.station_data_url = 'http://www.davek.com.au/td/station.asp'
        self.station_price_file = 'TradeDangerous.prices'
        self.station_price_url = 'http://www.davek.com.au/td/prices.asp'
        # очищаем лог файл и говорим о начале работы
        clear_file(log_filename)
        logging('Begin work')
        # получаем информацию о системах и станциях
        self.get_systems()
        self.get_stations()
        self.get_price()

    def get_systems(self):
        logging('Begin load systems info')
        # проверяем есть ли у нас файл с информацией о системах, если нет - скачиваем
        if not os.path.exists(self.system_data_file):
            logging('Can\'t find system data file. Load it from www.davek.com.au')
            get_web_object(self.system_data_url, self.system_data_file)
            logging('Load system data file comlete')

        '''
        # параметры разбора строк в System.csv (25.08.2015)
        # --
        # unq:name,pos_x,pos_y,pos_z,name@Added.added_id,modified
        # 1  - system
        # 2  - coord X        (0)
        # 3  - coord Y        (1)
        # 4  - coord Z        (2)
        '''
        systemspattern = re.compile(r"^'(.*)',([\d\.-]+),([\d\.-]+),([\d\.-]+),'.*','.*'$")

        f = open(self.system_data_file, 'r')

        while True:
            # читаем файл построчно
            line = f.readline()
            if not line: break

            # обрезаем перенос строки в конце
            line = line[0:-1]

            if systemspattern.search(line):
                self.cache_data[self.cd_sm][str((systemspattern.search(line).groups())[0].lower())] = (systemspattern.search(line).groups())[1:]

        f.close()
        logging('Finish load systems info')

    def get_stations(self):
        logging('Begin load stations info')

        # проверяем есть ли у нас файл с информацией о системах, если нет - скачиваем
        if not os.path.exists(self.station_data_file):
            logging('Can\'t find station data file. Load it from www.davek.com.au')
            get_web_object(self.station_data_url, self.station_data_file)
            logging('Load station data file comlete')

        ''' параметры разбора строк в Station.csv (25.08.2015)
        # unq:name@System.system_id,unq:name,ls_from_star,blackmarket,max_pad_size,market,shipyard,modified,outfitting,rearm,refuel,repair
        # '1 G. CAELI','Smoot Gateway',4761,'N','L','Y','Y','2015-05-06 17:03:00','Y','Y','Y','Y'
        # 0  - system
        # 1  - station
        # 2  - ls_from_star (0)
        # 3  - blackmarket  (1)
        # 4  - max_pad_size (2)
        # 5  - market       (3)
        # 6  - shipyard     (4)
        # 7  - modified     (5)
        # 8  - outfitting   (6)
        # 9  - rearm        (7)
        # 10 - refuel       (8)
        # 11 - repair       (9)
        '''
        stationpattern = re.compile(r"^'(.*)','(.*)',([\d\.-]+),'(.*)','(.*)','(.*)','(.*)','(.*)','(.*)','(.*)','(.*)','(.*)'$")

        f = open(self.station_data_file, 'r')

        while True:
            # читаем файл построчно
            line = f.readline()
            if not line: break

            # обрезаем перенос строки в конце
            line = line[0:-1]

            if stationpattern.search(line):
                search_result = stationpattern.search(line).groups()

                tmp_system = search_result[0].lower()
                tmp_station = search_result[1].lower()

                if tmp_system not in self.cache_data[self.cd_st]:
                    self.cache_data[self.cd_st][tmp_system] = {}

                self.cache_data[self.cd_st][tmp_system][tmp_station] = search_result[2:]

        f.close()
        logging('Finish load stations info')

    def get_price(self):

        logging('Begin load price info')

        # проверяем есть ли у нас файл с информацией о ценах, если нет - скачиваем
        # TODO: сделать проверку на актуальность файла и перезакачивать, если он протух
        if not os.path.exists(self.station_price_file):
            logging('Can\'t find price data file. Load it from www.davek.com.au')
            get_web_object(self.station_price_url, self.station_price_file)
            logging('Load price data file comlete')

        ''' параметры разбора строк в TradeDangerous.prices (25.08.2015)
        # --
        # 1  - system
        # 2  - station
        # 3  - product
        # 4  - sell         (0)
        # 5  - buy          (1)
        # 6  - demand       (2)
        # 7  - stock        (3)
        # 8  - timestamp    (4)
        '''
        pricepattern = re.compile(r'^\s*(\w[\w \.-]*\w)\s+(\d+)\s+(\d+)\s+([\dHML]+|\?|-|[\d?]+)\s+([\dHML]+|\?|-|[\d?]+)\s+(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s*[#]?.*$')
        system_name = ''
        station_name = ''

        f = open(self.station_price_file, 'r')
        i = 1
        # ----------------------------------------------------------------------------------------------------------
        while True:
            # читаем файл построчно
            line = f.readline()
            if not line: break
            # счетчик строк
            i += 1
            # обрезаем перенос строки в конце
            line = line[0:-1]

            # нахоодим систему и станицю
            # TODO: пересмотреть условия поиска строк. ну кривовато как-то...
            if len(line) > 0 and line[0] == '@':
                # TODO: реализовать это через регулярку
                sep = line.find('/')
                system_name = line[2:sep].lower()
                station_name = line[sep + 1:].lower()

                if system_name not in self.cache_data[self.cd_pr]:
                    self.cache_data[self.cd_pr][system_name] = { }

                if station_name not in self.cache_data[self.cd_pr][system_name]:
                    self.cache_data[self.cd_pr][system_name][station_name] = {}
            # строки содержащие группу продукта
            elif len(line) >= 4 and line[3] == '+':
                # product_group = line[5:-1]
                pass
            # пустые строки и строки комментариев пропускаем
            elif len(line[0:-1]) == 0 or line[0] == '#':
                pass
            # строки содержащие сам продукт
            elif len(line) >= 6:

                if pricepattern.search(line):
                    search_result = pricepattern.search(line).groups()
                    product = search_result[0].lower()
                    product_data = search_result[1:]

                    self.cache_data[self.cd_pr][system_name][station_name][product] = product_data
                else:
                    logging('Price load, unknown product: ' + line, 'WARNING')
            # остальные строки, которые не распознаны
            else:
                logging('Price load, unknown line (' + str(i) + '): ' + line, 'WARNING')
        # ----------------------------------------------------------------------------------------------------------
        f.close()
        logging( 'Finish load price data')

cd = CacheData()

print(cd.cache_data['prices'])

