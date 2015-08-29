import re
from urllib import request
from datetime import datetime
# variables:
#version
trade_versoion = 4
# in ly
low_system_distance = 0
max_system_distance = 20
# in ls
station_distance = 600
# 
station_size = 'L'
#
min_stock_demand_count = 10000
#
log_file_name = 'trade' + str(trade_versoion) + '.log'
output_file_name = 'trade' + str(trade_versoion) + '.out'
#
system_data_file = 'System.csv'
system_data_url = 'http://www.davek.com.au/td/System.csv'
station_data_file = 'Station.csv'
station_data_url = 'http://www.davek.com.au/td/station.asp'
station_price_file = 'TradeDangerous.prices'
station_price_url = 'http://www.davek.com.au/td/prices.asp'
#
cd_pr = 'prices'
cd_sm = 'systems'
cd_st = 'stations'
cd_stsl_ar = 'station_slave_array'
td_ar = 'trade_array'
good_is = 'imperial slaves'
#
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
#
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
#
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
# паттерн для парсинга строк с системами/танциями
#@ 1 G. CAELI/Smoot Gateway
#   + Chemicals
#      Explosives                  399       0     75124M         -  2015-02-06 13:07:29
pricepattern_system_line = re.compile(r'^@\s+(.*)/(.*)$')
# паттерн для парсинга stock и demand
sd_pattern = re.compile(r'^(\d+).*$')
# functions:
def clear_file(filename):
    f = open(filename, mode = 'w', encoding = 'utf-8')
    f.close()

def logging(text, tag = 'INFO'):
    with open(log_file_name, mode = 'a', encoding = 'utf-8') as f:
        f.write(str(datetime.now()) + ' [' + tag + '] ' + text + '\n')
    f.close()

def get_web_object(url, filename): 
    request.urlretrieve(url, filename=filename)

# функции сортировки
def sort_func(trade_object):
    return int(trade_object['profit'])

def best_sort_func(best_sort):
	#t_best_route_array.append({'direct': t_direct, 'reverse': t_reverse})
	return int(best_sort['direct']['profit']) + int(best_sort['reverse']['profit'])