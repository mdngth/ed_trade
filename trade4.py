import os

import json
import math

#----------------------------
import config as c
#----------------------------

class CacheData(object):
    """docstring for Cache_Data"""
    def __init__(self):
        super(CacheData, self).__init__()
        #
        #c.cd_pr = 'prices'
        #c.cd_sm = 'systems'
        #c.cd_st = 'stations'
        #cd_stsl_ar = 'station_slave_array'
        #td_ar = 'trade_array'
        self.cache_data = {c.cd_pr: {}, c.cd_sm: {}, c.cd_st: {}, c.cd_stsl_ar: {}, c.td_ar: []}
        # TODO: перенести очистку лога в какое-нибудь другое место
        # очищаем лог файл и говорим о начале работы
        c.clear_file(c.log_file_name)
        c.logging('Begin create cache data')
        # получаем информацию о системах, станциях и ценах
        self.get_systems()
        self.get_stations()
        self.get_price()
        self.calc_best_routes()
        #self.process_trade()
        c.logging('End create cache data')

    def get_systems(self):
        c.logging('Begin load systems info')
        # проверяем есть ли у нас файл с информацией о системах, если нет - скачиваем
        if not os.path.exists(c.system_data_file):
            c.logging('Can\'t find system data file. Load it from www.davek.com.au')
            c.get_web_object(c.system_data_url, c.system_data_file)
            c.logging('Load system data file comlete')

        smp = c.systemspattern

        f = open(c.system_data_file, 'r')

        while True:
            # читаем файл построчно
            line = f.readline()
            if not line: break

            # обрезаем перенос строки в конце
            line = line[0:-1]

            if smp.search(line):
                self.cache_data[c.cd_sm][str((smp.search(line).groups())[0].lower())] = (smp.search(line).groups())[1:]

        f.close()
        c.logging('Finish load systems info')

    def get_stations(self):
        c.logging('Begin load stations info')

        # проверяем есть ли у нас файл с информацией о системах, если нет - скачиваем
        if not os.path.exists(c.station_data_file):
            c.logging('Can\'t find station data file. Load it from www.davek.com.au')
            c.get_web_object(c.station_data_url, c.station_data_file)
            c.logging('Load station data file comlete')

        stp = c.stationpattern

        f = open(c.station_data_file, 'r')

        while True:
            # читаем файл построчно
            line = f.readline()
            if not line: break

            # обрезаем перенос строки в конце
            line = line[0:-1]

            if stp.search(line):
                search_result = stp.search(line).groups()

                tmp_system = search_result[0].lower()
                tmp_station = search_result[1].lower()

                if tmp_system not in self.cache_data[c.cd_st]:
                    self.cache_data[c.cd_st][tmp_system] = {}

                self.cache_data[c.cd_st][tmp_system][tmp_station] = search_result[2:]

        f.close()
        c.logging('Finish load stations info')

    def get_price(self):

        c.logging('Begin load price info')

        # проверяем есть ли у нас файл с информацией о ценах, если нет - скачиваем
        # TODO: сделать проверку на актуальность файла и перезакачивать, если он протух
        if not os.path.exists(c.station_price_file):
            c.logging('Can\'t find price data file. Load it from www.davek.com.au')
            c.get_web_object(c.station_price_url, c.station_price_file)
            c.logging('Load price data file comlete')

        pp = c.pricepattern
        ps = c.pricepattern_system_line
        sdp = c.sd_pattern
        system_name = ''
        station_name = ''

        f = open(c.station_price_file, 'r')

        while True:
            # читаем файл построчно
            line = f.readline()
            if not line: break
            # обрезаем перенос строки в конце
            line = line[0:-1]

            if ps.search(line):
                # если строка содержит систему и станцию, парсим ее
                system_name = ((ps.search(line).groups())[0]).lower()
                station_name = ((ps.search(line).groups())[1]).lower()
                # проверяем станцию на размер и наоичие в кеше станций
                if system_name not in self.cache_data[c.cd_st] or \
                   station_name not in self.cache_data[c.cd_st][system_name] or \
                   (self.cache_data[c.cd_st][system_name][station_name])[2] != 'L':
                    # если размер не подходит, оставляем систему и станцию незаполненными. 
                    # это и будет одним из признаком сохранять товар или нет
                    system_name = ''
                    station_name = ''
                else:
                    # если по размеру проходит, создаем структуру в словаре (если ее еще нет)
                    if system_name not in self.cache_data[c.cd_pr]:
                        self.cache_data[c.cd_pr][system_name] = {}
                    if station_name not in self.cache_data[c.cd_pr][system_name]:
                        self.cache_data[c.cd_pr][system_name][station_name] = {}

            elif system_name != '' and station_name != '' and pp.search(line):
                product = ((pp.search(line).groups())[0]).lower()
                sell = (pp.search(line).groups())[1]
                buy = (pp.search(line).groups())[2]
                demand = (pp.search(line).groups())[3]
                stock = (pp.search(line).groups())[4]
                timestamp = (pp.search(line).groups())[5]

                if demand == '?' or demand == '-':
                    demand = -1
                
                if stock == '?' or stock == '-':
                    stock = -1

                if sdp.search(str(demand)):
                    demand = (sdp.search(str(demand)).groups())[0]

                if sdp.search(str(stock)):
                    stock = (sdp.search(str(stock)).groups())[0]

                self.cache_data[c.cd_pr][system_name][station_name][product] = (sell, buy, demand, stock, timestamp)
            else:
                pass
        # ----------------------------------------------------------------------------------------------------------
        f.close()
        c.logging('End load price info')

    def calc_distance(self, system_a, system_b): 

        return round((((float(self.cache_data[c.cd_sm][system_b][0]) - float(self.cache_data[c.cd_sm][system_a][0])) ** 2 + (float(self.cache_data[c.cd_sm][system_b][1]) - float(self.cache_data[c.cd_sm][system_a][1])) ** 2 + (float(self.cache_data[c.cd_sm][system_b][2]) - float(self.cache_data[c.cd_sm][system_a][2])) ** 2) ** 0.5), 2)

    def process_trade(self):
        # находим все станции, где продаются рабы
        for system in self.cache_data[c.cd_pr]:
            for station in self.cache_data[c.cd_pr][system]:
                if c.good_is in self.cache_data[c.cd_pr][system][station] and int((self.cache_data[c.cd_pr][system][station][c.good_is])[3]) > 0:
                    if system not in self.cache_data[c.cd_stsl_ar]:
                        self.cache_data[c.cd_stsl_ar][system] = {}
                    if station not in self.cache_data[c.cd_stsl_ar][system]:
                        self.cache_data[c.cd_stsl_ar][system][station] = {}

                    self.cache_data[c.cd_stsl_ar][system][station][c.good_is] = (self.cache_data[c.cd_pr][system][station][c.good_is])[0:]

        # теперь обходим наши станции с рабами и делаем массив с маршрутами
        for system_a in self.cache_data[c.cd_stsl_ar]:
            for station_a in self.cache_data[c.cd_stsl_ar][system_a]:
                # проверяем на расстояние до станций
                if int((self.cache_data[c.cd_st][system_a][station_a])[0]) <= c.station_distance:
                    # ищем окончание маршрута
                    for system_b in self.cache_data[c.cd_pr]:
                        # проверяем на расстояние между системами
                        if self.calc_distance(system_a, system_b) <= c.system_distance:
                            for station_b in self.cache_data[c.cd_pr][system_b]:
                                # проверяем на расстояние до станций
                                if int((self.cache_data[c.cd_st][system_a][station_a])[0]) <= c.station_distance:
                                    # проверяем что рабы тут покупаются
                                    if c.good_is in self.cache_data[c.cd_pr][system_b][station_b]:
                                        if int((self.cache_data[c.cd_pr][system_b][station_b][c.good_is])[2]) > 0 and int((self.cache_data[c.cd_pr][system_b][station_b][c.good_is])[0]) > 0:
                                            # заполняем основные данные о маршруте
                                            trade_obj = {'system_a': system_a, 'station_a': station_a, 'system_b': system_b, 'station_b': station_b}
                                            # вычислем профит, предложение и спрос за рабов
                                            trade_obj['slave_profit'] = int((self.cache_data[c.cd_pr][system_b][station_b][c.good_is])[0]) - int((self.cache_data[c.cd_stsl_ar][system_a][station_a][c.good_is])[1])
                                            trade_obj['a_slave_stock'] = int((self.cache_data[c.cd_stsl_ar][system_a][station_a][c.good_is])[3])
                                            trade_obj['b_slave_demand'] = int((self.cache_data[c.cd_pr][system_b][station_b][c.good_is])[2])
                                            # вычислем обратный лучший продукт
                                            trade_obj['product'] = ''
                                            trade_obj['product_profit'] = 0

                                            # перебираем продукты на станции б
                                            for product in self.cache_data[c.cd_pr][system_b][station_b]:
                                                # если продукт так же есть на станции а
                                                if product in self.cache_data[c.cd_stsl_ar][system_a][station_a]:
                                                    # если продукт продается и покупается считаем его профит
                                                    if int((self.cache_data[c.cd_pr][system_b][station_b][product])[1]) > 0 and int((self.cache_data[c.cd_stsl_ar][system_a][station_a][product])[0]) > 0:
                                                        if int((self.cache_data[c.cd_stsl_ar][system_a][station_a][product])[0]) - int((self.cache_data[c.cd_pr][system_b][station_b][product])[1]) > trade_obj['product_profit']:
                                                            trade_obj['product_profit'] = int((self.cache_data[c.cd_stsl_ar][system_a][station_a][product])[0]) - int((self.cache_data[c.cd_pr][system_b][station_b][product])[1])
                                                            trade_obj['product'] = product

                                            if trade_obj['product'] != '' and trade_obj['slave_profit'] > 0:
                                                trade_obj['b_product_stock'] = int((self.cache_data[c.cd_pr][system_b][station_b][str(trade_obj['product'])])[3])
                                                trade_obj['a_product_demand'] = int((self.cache_data[c.cd_stsl_ar][system_a][station_a][str(trade_obj['product'])])[2])

                                                (self.cache_data[c.td_ar]).append(trade_obj)

        # отсортируем нащ массив
        self.cache_data[c.td_ar].sort(key = sort_func, reverse = True)

        # и сохраним как json
        with open('trade4.json', mode = 'w', encoding = 'utf-8') as f:
            json.dump(self.cache_data[c.td_ar], f)
        f.close()

    def get_td(self, system_a, system_b, station_a, station_b, direction='d'):
        # проверяем направление
        if direction == 'r':
            system_a, system_b = system_b, system_a
            station_a, station_b = station_b, station_a

        # временный массив с товарами
        product_array = []
        # перебираем товары на станции (a)
        for product in self.cache_data[c.cd_pr][system_a][station_a]:
            # смотрим, чтобы поставка этого товара была больше нуля, и чтобы стоимость покупки была больше нуля
            if int((self.cache_data[c.cd_pr][system_a][station_a][product])[1]) > 0 and int((self.cache_data[c.cd_pr][system_a][station_a][product])[3]) > 0:
                # проверяем есть ли этот товар для продажи на станции b
                if product in self.cache_data[c.cd_pr][system_b][station_b] and int((self.cache_data[c.cd_pr][system_b][station_b][product])[0]) > 0 and int((self.cache_data[c.cd_pr][system_b][station_b][product])[2]) > 0:
                    t_product_data = {}
                    t_product_data['profit'] = int((self.cache_data[c.cd_pr][system_b][station_b][product])[0]) - int((self.cache_data[c.cd_pr][system_a][station_a][product])[1])
                    if int(t_product_data['profit']) > 0:
                        t_product_data['product'] = product
                        t_product_data['sell'] = int((self.cache_data[c.cd_pr][system_b][station_b][product])[0]) 
                        t_product_data['buy'] = int((self.cache_data[c.cd_pr][system_a][station_a][product])[1])
                        t_product_data['stock'] = int((self.cache_data[c.cd_pr][system_a][station_a][product])[3])
                        t_product_data['demand'] = int((self.cache_data[c.cd_pr][system_b][station_b][product])[2])
                        product_array.append(t_product_data)

        route_begin = system_a + '/' + station_a
        route_end = system_b + '/' + station_b
        route_dist = self.calc_distance(system_a, system_b)
        station_a_dist = (self.cache_data[c.cd_st][system_a][station_a])[0]
        station_b_dist = (self.cache_data[c.cd_st][system_b][station_b])[0]

        # отсортируем нащ массив
        product_array.sort(key = c.sort_func, reverse = True)

        # выведем массив
        print('route ({} ly): {} ({} ls) --> {} ({} ls)'.format(route_dist, route_begin, station_a_dist, route_end, station_b_dist))
        for i in product_array:
            print('\t{: <20}: profit {: >5} cr, sell {: >5} cr, buy {: >5} cr, stock {: >9}, demand {: >9}'.format(i['product'],i['profit'],i['sell'],i['buy'],i['stock'],i['demand']))

    def get_trade_data(self, system_a, system_b, station_a, station_b, direction='d'):
        self.get_td(system_a, system_b, station_a, station_b)
        self.get_td(system_a, system_b, station_a, station_b, 'r')

    def get_in_td(self, system_a, system_b, station_a, station_b, direction='d'):
        ''' функция ищет лучший товар для торговли между 2 станциями '''
        # проверяем направление
        if direction == 'r':
            system_a, system_b = system_b, system_a
            station_a, station_b = station_b, station_a

        # временный массив с товарами
        product_array = []
        # перебираем товары на станции (a)
        for product in self.cache_data[c.cd_pr][system_a][station_a]:
            # смотрим, чтобы поставка этого товара была больше нуля, и чтобы стоимость покупки была больше нуля
            if int((self.cache_data[c.cd_pr][system_a][station_a][product])[1]) > 0 and int((self.cache_data[c.cd_pr][system_a][station_a][product])[3]) > 0:
                # проверяем есть ли этот товар для продажи на станции b
                if product in self.cache_data[c.cd_pr][system_b][station_b] and int((self.cache_data[c.cd_pr][system_b][station_b][product])[0]) > 0 and int((self.cache_data[c.cd_pr][system_b][station_b][product])[2]) > 0:
                    t_product_data = {}
                    t_product_data['profit'] = int((self.cache_data[c.cd_pr][system_b][station_b][product])[0]) - int((self.cache_data[c.cd_pr][system_a][station_a][product])[1])
                    if int(t_product_data['profit']) > 0:
                        t_product_data['product'] = product
                        t_product_data['sell'] = int((self.cache_data[c.cd_pr][system_b][station_b][product])[0]) 
                        t_product_data['buy'] = int((self.cache_data[c.cd_pr][system_a][station_a][product])[1])
                        t_product_data['stock'] = int((self.cache_data[c.cd_pr][system_a][station_a][product])[3])
                        t_product_data['demand'] = int((self.cache_data[c.cd_pr][system_b][station_b][product])[2])
                        product_array.append(t_product_data)
        if len(product_array) > 0:
            # отсортируем нащ массив
            product_array.sort(key = c.sort_func, reverse = True)

            (product_array[0])['route_begin'] = system_a + '/' + station_a
            (product_array[0])['route_end'] = system_b + '/' + station_b
            (product_array[0])['route_dist'] = self.calc_distance(system_a, system_b)
            (product_array[0])['station_a_dist'] = (self.cache_data[c.cd_st][system_a][station_a])[0]
            (product_array[0])['station_b_dist'] = (self.cache_data[c.cd_st][system_b][station_b])[0]
            if (product_array[0])['stock'] >= c.min_stock_demand_count and (product_array[0])['demand'] >= c.min_stock_demand_count:
                (product_array[0])['status'] = 1
            else:
                (product_array[0])['status'] = 0
        else:
            product_array.append({'status': 0})

        return product_array[0]

    def calc_best_routes(self):
        c.logging('Begin best route calculation')
        t_best_route_array = []
        t_station_array = []
        i = 0
        # создадим массив для того чтобы были неповторяющиеся отношения
        for system in self.cache_data[c.cd_pr]:
            for station in self.cache_data[c.cd_pr][system]:
                if int((self.cache_data[c.cd_st][system][station])[0]) <= c.station_distance:
                    t_station_array.append({'system': system, 'station': station})
                    i += 1

        # общее кол-во станций в переборе
        i = round(i*i/2)
        print('Общее кол-во станций в переборе: {}'.format(i))
        # для текущего указателя перебора
        y = 0
        # для сохранения текущего прогресса
        z = 0
        # low_system_distance = 0
        # max_system_distance = 30
        print('Построение массива маршрутов: ', end='')
        while len(t_station_array) > 0:
            route_begin = t_station_array.pop()
            for route_end in t_station_array:
                # забыл  проверить на расстояние
                if c.low_system_distance < self.calc_distance(route_begin['system'], route_end['system']) <= c.max_system_distance:
                    t_direct = self.get_in_td(route_begin['system'], route_end['system'], route_begin['station'], route_end['station'])
                    t_reverse = self.get_in_td(route_begin['system'], route_end['system'], route_begin['station'], route_end['station'], 'r')
                    if t_direct['status'] == 1 and t_reverse['status'] == 1:
                        t_best_route_array.append({'direct': t_direct, 'reverse': t_reverse})
                y += 1
                if (round((y/i)*100) % 10) == 0 and round((y/i)*10) != z:
                    z = round((y/i)*10)
                    print('#', end='')
        print()
        t_best_route_array.sort(key = c.best_sort_func, reverse = True)

        c.clear_file(c.output_file_name)
        for route in t_best_route_array:
            with open(c.output_file_name, mode='a') as f:
                f.write('route: {} [{} ls] --> {} [{} ls] ({: >5} ly) profit: {: >5} cr\n'.format(route['direct']['route_begin'], route['direct']['station_a_dist'], route['direct']['route_end'], route['direct']['station_b_dist'], route['direct']['route_dist'], (int(route['direct']['profit']) + int(route['reverse']['profit']))))
                f.write('\t{: <21}: profit {: >5} cr, buy {: >5} cr, sell {: >5} cr, stock {: >9}, demand {: >9}\n'.format(route['direct']['product'], route['direct']['profit'], route['direct']['buy'], route['direct']['sell'], route['direct']['stock'], route['direct']['demand']))
                f.write('\t{: <21}: profit {: >5} cr, buy {: >5} cr, sell {: >5} cr, stock {: >9}, demand {: >9}\n'.format(route['reverse']['product'], route['reverse']['profit'], route['reverse']['buy'], route['reverse']['sell'], route['reverse']['stock'], route['reverse']['demand']))
                f.write('\n')

        c.logging('End best route calculation')

cd = CacheData()
#cd.calc_best_routes()
#cd.get_trade_data('nemehi', 'ehecatl', 'meikle port', 'hackworth orbital')
#print(cd.cache_data[c.cd_stsl_ar])
#profit   3890:  nemehi/meikle port      (198) [(1036013) superconductors (723206)] ehecatl/hackworth orbital(125)
#distance 33    ehecatl/hackworth orbital(125) [(235376 ) imperial slaves (64773 )]  nemehi/meikle port      (198)