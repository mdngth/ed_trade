import os
import re
import json
import math
from datetime import datetime

c_p = 'prices'
c_s = 'systems'
c_st = 'stations'
c_sd = 'systems_distance'
c_ls = 'lstations'
c_r = 'routes'
cachedata = { 'prices': { }, 'systems': { }, 'stations': { }, 'systems_distance': { }, 'lstations': { }, 'routes': [ ] }


class tradeRoute(object):
    """object for route"""

    def __init__(self, system_a, station_a, system_b, station_b):
        super(tradeRoute, self).__init__()
        self.smA = system_a
        self.smB = system_b
        self.stA = station_a
        self.stB = station_b
        global c_p
        global c_s
        global c_st
        global c_sd
        global c_ls
        global c_r
        global cachedata
        # --
        (self.profit_a, self.product_a, self.stock_a, self.demand_b) = self.get_profit( self.smA, self.smB, self.stA,
                                                                                        self.stB )
        (self.profit_b, self.product_b, self.stock_b, self.demand_a) = self.get_profit( self.smB, self.smA, self.stB,
                                                                                        self.stA )
        self.profit = self.profit_a + self.profit_b
        self.dist_station_a = self.get_dist_station( self.smA, self.stA )
        self.dist_station_b = self.get_dist_station( self.smB, self.stB )
        self.dist_systems = self.get_dist_systems( self.smA, self.smB )

    def get_dist_systems( self, system_a, system_b ):
        global c_sd
        global cachedata
        return int(cachedata[c_sd][system_a][system_b])

    def get_dist_station(self, system, station):
        global c_st
        global cachedata
        return int((cachedata[c_st][system][station])[0])

    def get_profit(self, s_a, s_b, st_a, st_b):

        global c_p
        global c_s
        global c_st
        global c_sd
        global c_ls
        global c_r
        global cachedata

        s_profit = 0
        s_best_good = ''

        # перебираем товар на станции отправления
        for good in cachedata[c_p][s_a][st_a]:
            # проверяем что он присутствует на станции назначения
            if good in cachedata[c_p][s_b][st_b]:
                # проверяем что его стоимость покупки на станции назначения больше нуля и что стоимость его продажи на
                # станции отправления больше нуля
                if int((cachedata[c_p][s_b][st_b][good])[0]) > 0 and int((cachedata[c_p][s_a][st_a][good])[1]) > 0:
                    # вычисляем маржу с продажи
                    profit_tmp = int((cachedata[c_p][s_b][st_b][good])[0]) - int((cachedata[c_p][s_a][st_a][good])[1])
                    # если она больше чем у предыдущего товара, сохраняем
                    if profit_tmp > s_profit:
                        s_profit = profit_tmp
                        s_best_good = good

        # demand - требуется купить, stock - в наличии
        if s_best_good != '':
            v_s_demand = str((cachedata[c_p][s_b][st_b][s_best_good])[2])
            v_s_stock = str((cachedata[c_p][s_a][st_a][s_best_good])[3])
        else:
            v_s_demand = ''
            v_s_stock = ''

        return s_profit, s_best_good, v_s_stock, v_s_demand

    def get_str_eq_left(self, str1, str2):
        if len(str1) >= len(str2):
            str2 = (' ' * (len(str1) - len(str2))) + str2
        else:
            str1 = (' ' * (len(str2) - len(str1))) + str1
        return str1, str2

    def get_str_eq_right(self, str1, str2):
        if len(str1) >= len(str2):
            str2 = str2 + (' ' * (len(str1) - len(str2)))
        else:
            str1 = str1 + (' ' * (len(str2) - len(str1)))
        return str1, str2

    def get_string_view(self):
        (str_start_system, str_end_system) = self.get_str_eq_left(self.smA, self.smB)
        (str_start_station, str_end_station) = self.get_str_eq_right(self.stA, self.stB)
        (str_dist_start_station, str_dist_end_station) = self.get_str_eq_left(str(self.dist_station_a), str(self.dist_station_b))

        str_start_route = '{}/{}({})'.format(str_start_system, str_start_station, str_dist_start_station)
        str_end_route = '{}/{}({})'.format(str_end_system, str_end_station, str_dist_end_station)

        (str_profit, str_dist) = self.get_str_eq_right(str(self.profit), str(self.dist_systems))

        (str_product_a, str_product_b) = self.get_str_eq_right(self.product_a, self.product_b)

        (str_stock_a, str_stock_b) = self.get_str_eq_right(str(self.stock_a), str(self.stock_b))
        (str_demand_b, str_demand_a) = self.get_str_eq_right(str(self.demand_b), str(self.demand_a))

        str1 = 'profit   {}: {} [({}) {} ({})] {}\n'.format(str_profit, str_start_route, str_stock_a, str_product_a, str_demand_b, str_end_route)
        str2 = 'distance {}  {} [({}) {} ({})] {}\n'.format(str_dist, str_end_route, str_stock_b, str_product_b, str_demand_a, str_start_route)

        rstr = str1 + str2 + '\n'
        return rstr

    @staticmethod
    def sortByProfit( route ):
        return route.profit


class tradeCache( object ):
    """docstring for tradeCache"""

    def __init__( self ):
        super( tradeCache, self ).__init__( )
        # --
        self.log_file = 'trade.log'
        self.price_file = 'TradeDangerous.prices'
        self.system_file = 'System.csv'
        self.station_file = 'Station.csv'
        self.cache_json_file = 'cache.json'
        # --
        self.dist_to_stationA = 300
        self.dist_to_stationB = 400
        self.dist_to_systemA = 0
        self.dist_to_systemB = 17
        self.profit_border = 2500
        # --
        global c_p
        global c_s
        global c_st
        global c_sd
        global c_ls
        global c_r
        global cachedata
        # --
        # -- for test period TODO: вынести в отдельную функцию инициализацию файлов
        with open( 'test_output.log', mode = 'w', encoding = 'utf-8' ) as f:
            pass
        f.close( )
        with open( self.log_file, mode = 'w', encoding = 'utf-8' ) as f:
            pass
        f.close( )
        # --
        self.logging( '------------------------- Begin work -------------------------' )
        if not self.json_load( ):
            self.loading_systems( )
            self.loading_stations( )
            self.loading_price( )
            self.calc_distance( )
            self.json_save( )

    def logging( self, text, tag = 'INFO' ):
        with open( self.log_file, mode = 'a', encoding = 'utf-8' ) as f:
            f.write( str( datetime.now( ) ) + ' [' + tag + '] ' + text + '\n' )
        f.close( )

    def loading_systems( self ):

        global c_p
        global c_s
        global c_st
        global c_sd
        global c_ls
        global c_r
        global cachedata

        # --
        # unq:name,pos_x,pos_y,pos_z,name@Added.added_id,modified
        # 1  - system
        # 2  - coord X        (0)
        # 3  - coord Y        (1)
        # 4  - coord Z        (2)
        systemspattern = re.compile( r"^'(.*)',([\d\.-]+),([\d\.-]+),([\d\.-]+),'.*','.*'$" )

        if os.path.exists( self.system_file ):
            self.logging( 'Begin load: ' + self.system_file )

            f = open( self.system_file, 'r' )

            while True:
                # читаем файл построчно
                line = f.readline( )
                if not line: break

                # обрезаем перенос строки в конце
                line = line[ 0:-1 ]

                if systemspattern.search( line ):
                    cachedata[ 'systems' ][ str( (systemspattern.search( line ).groups( ))[ 0 ].lower( ) ) ] = (
                                                                                                                   systemspattern.search(
                                                                                                                       line ).groups( ))[
                                                                                                               1: ]

            f.close( )
            self.logging( 'Finish load: ' + self.system_file )
        else:
            self.logging( 'Load error. Can\'t find: ' + self.system_file, 'ERROR' )

    def loading_stations( self ):

        global c_p
        global c_s
        global c_st
        global c_sd
        global c_ls
        global c_r
        global cachedata

        # --
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
        stationpattern = re.compile(
            r"^'(.*)','(.*)',([\d\.-]+),'(.*)','(.*)','(.*)','(.*)','(.*)','(.*)','(.*)','(.*)','(.*)'$" )

        if os.path.exists( self.station_file ):
            self.logging( 'Begin load: ' + self.station_file )

            f = open( self.station_file, 'r' )

            while True:
                # читаем файл построчно
                line = f.readline( )
                if not line: break

                # обрезаем перенос строки в конце
                line = line[ 0:-1 ]

                if stationpattern.search( line ):
                    search_result = stationpattern.search( line ).groups( )

                    tmp_system = search_result[ 0 ].lower( )
                    tmp_station = search_result[ 1 ].lower( )

                    if tmp_system not in cachedata[ 'stations' ]:
                        cachedata[ 'stations' ][ tmp_system ] = { }

                    cachedata[ 'stations' ][ tmp_system ][ tmp_station ] = search_result[ 2: ]

            f.close( )
            self.logging( 'Finish load: ' + self.station_file )
        else:
            self.logging( 'Load error. Can\'t find: ' + self.station_file, 'ERROR' )

    def loading_price( self ):

        global c_p
        global c_s
        global c_st
        global c_sd
        global c_ls
        global c_r
        global cachedata

        # --
        # 1  - system
        # 2  - station
        # 3  - product
        # 4  - sell         (0)
        # 5  - buy          (1)
        # 6  - demand       (2)
        # 7  - stock        (3)
        # 8  - timestamp    (4)
        pricepattern = re.compile(
            r'^\s*(\w[\w \.-]*\w)\s+(\d+)\s+(\d+)\s+([\dHML]+|\?|-|[\d?]+)\s+([\dHML]+|\?|-|[\d?]+)\s+(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s*[#]?.*$' )
        system_name = ''
        station_name = ''

        if os.path.exists( self.price_file ):
            self.logging( 'Begin load: ' + self.price_file )

            f = open( self.price_file, 'r' )
            i = 1
            # ----------------------------------------------------------------------------------------------------------
            while True:
                # читаем файл построчно
                line = f.readline( )
                if not line: break
                # счетчик строк
                i += 1
                # обрезаем перенос строки в конце
                line = line[ 0:-1 ]

                # нахоодим систему и станицю
                if len( line ) > 0 and line[ 0 ] == '@':
                    sep = line.find( '/' )
                    system_name = line[ 2:sep ].lower( )
                    station_name = line[ sep + 1: ].lower( )

                    if system_name not in cachedata[ 'prices' ]:
                        cachedata[ 'prices' ][ system_name ] = { }

                    if station_name not in cachedata[ 'prices' ][ system_name ]:
                        cachedata[ 'prices' ][ system_name ][ station_name ] = { }
                # строки содержащие группу продукта
                elif len( line ) >= 4 and line[ 3 ] == '+':
                    # product_group = line[5:-1]
                    pass
                # пустые строки и строки комментариев пропускаем
                elif len( line[ 0:-1 ] ) == 0 or line[ 0 ] == '#':
                    pass
                # строки содержащие сам продукт
                elif len( line ) >= 6:

                    if pricepattern.search( line ):
                        search_result = pricepattern.search( line ).groups( )
                        product = search_result[ 0 ].lower( )
                        product_data = search_result[ 1: ]

                        cachedata[ 'prices' ][ system_name ][ station_name ][ product ] = product_data
                    else:
                        self.logging( 'Price load, unknown product: ' + line, 'WARNING' )
                # остальные строки, которые не распознаны
                else:
                    self.logging( 'Price load, unknown line (' + str( i ) + '): ' + line, 'WARNING' )
            # ----------------------------------------------------------------------------------------------------------
            f.close( )
            self.logging( 'Finish load: ' + self.price_file )
        else:
            self.logging( 'Load error. Can\'t find: ' + self.price_file, 'ERROR' )

    def json_save( self ):

        global c_p
        global c_s
        global c_st
        global c_sd
        global c_ls
        global c_r
        global cachedata

        self.logging( 'Begin cache save: ' + self.cache_json_file )
        with open( self.cache_json_file, mode = 'w', encoding = 'utf-8' ) as f:
            json.dump( cachedata, f )
        f.close( )
        self.logging( 'Finish cache save: ' + self.cache_json_file )
        return 1

    def json_load( self ):

        global c_p
        global c_s
        global c_st
        global c_sd
        global c_ls
        global c_r
        global cachedata

        if os.path.exists( self.cache_json_file ):
            self.logging( 'Begin cache load: ' + self.cache_json_file )

            with open( self.cache_json_file, 'r', encoding = 'utf-8' ) as f:
                cachedata = { }
                cachedata = json.load( f )
            f.close( )

            self.logging( 'Finish cache load: ' + self.cache_json_file )
            return 1
        else:
            return 0

    def calc_distance( self ):
        self.logging( 'Begin distance calculation. Find system with L station size.' )

        global c_p
        global c_s
        global c_st
        global c_sd
        global c_ls
        global c_r
        global cachedata

        for system in cachedata[ 'stations' ]:
            for station in cachedata[ 'stations' ][ system ]:
                if str( cachedata[ 'stations' ][ system ][ station ][ 2 ] ) == 'L':
                    cachedata[ 'systems_distance' ][ system ] = { }
                    if system not in cachedata[ 'lstations' ]:
                        cachedata[ 'lstations' ][ system ] = { }
                        cachedata[ 'lstations' ][ system ][ station ] = cachedata[ 'stations' ][ system ][ station ]
                    else:
                        cachedata[ 'lstations' ][ system ][ station ] = cachedata[ 'stations' ][ system ][ station ]

        self.logging( ' Find system with L station size end. Start calculate distance.' )

        for s_system in cachedata[ 'systems_distance' ]:
            for e_system in cachedata[ 'systems_distance' ]:

                dist = round( (((float( cachedata[ 'systems' ][ e_system ][ 0 ] ) - float(
                    cachedata[ 'systems' ][ s_system ][ 0 ] )) ** 2 + (
                                    float( cachedata[ 'systems' ][ e_system ][ 1 ] ) - float(
                                        cachedata[ 'systems' ][ s_system ][ 1 ] )) ** 2 + (
                                    float( cachedata[ 'systems' ][ e_system ][ 2 ] ) - float(
                                        cachedata[ 'systems' ][ s_system ][ 2 ] )) ** 2) ** 0.5), 2 )
                if dist < 100:
                    cachedata[ 'systems_distance' ][ s_system ][ e_system ] = round( dist, 2 )

        self.logging( 'End distance calculation' )

    def calc_bestroutes( self ):
        self.logging( 'Begin best routes calculation.' )

        global c_p
        global c_s
        global c_st
        global c_sd
        global c_ls
        global c_r
        global cachedata

        # начинаем перебор станций. находим текущую систему и станцию
        for s_sm in cachedata[ c_ls ]:
            # проверяем что система есть в кеше цен и кеше расстояний
            if s_sm in cachedata[ c_p ] and s_sm in cachedata[ c_sd ]:
                for s_st in cachedata[ c_ls ][ s_sm ]:
                    # проверяем что станция есть в кеше цен
                    if s_st in cachedata[ c_p ][ s_sm ]:
                        # ищем конечную точку маршрута
                        for e_sm in cachedata[ c_ls ]:
                            # проверяем что система есть в кеше цен и кеше расстояний
                            if e_sm in cachedata[ c_p ] and e_sm in cachedata[c_sd][ s_sm ]:
                                for e_st in cachedata[ c_ls ][ e_sm ]:
                                    # проверяем что станция есть в кеше цен
                                    if e_st in cachedata[ c_p ][ e_sm ]:
                                        # проверяем на условие дальности полета между системами и до станции в системах
                                        if self.dist_to_systemA < cachedata[c_sd][s_sm][e_sm] <= self.dist_to_systemB and \
                                                        int((cachedata[c_ls][s_sm][s_st])[0]) <= self.dist_to_stationA and \
                                                        int((cachedata[c_ls][e_sm][e_st])[0]) <= self.dist_to_stationB:
                                            # дабавляем наш маршрут в кеш в виде объекта, если его профит нам подходит
                                            tr = tradeRoute(s_sm, s_st, e_sm, e_st)
                                            if tr.profit >= self.profit_border:
                                                (cachedata[c_r]).append(tr)

        self.logging( 'End best routes calculation.' )


x = tradeCache()
x.calc_bestroutes()
cachedata[c_r].sort(key = tradeRoute.sortByProfit, reverse = True)

for i in range(0, 10):
    if cachedata[c_r][i]:
        print((cachedata[c_r][i]).get_string_view())
# TODO: добавить в подбор нужных систем фильтры на присутствующие системы в prices и пр
# TODO: создать под найденный маршрут отдельный объект. Потом создавать список с этими объектами чтобы можно было сортировать и пр.
