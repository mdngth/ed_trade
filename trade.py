import os
import re
import json

trade_data_file = 'TradeDangerous.prices'
trade_data_json = 'TradeDangerous.prices.json'
trade_system_file = 'System.csv'
trade_station_file = 'Station.csv'

if os.path.exists(trade_data_file):
	pass
else:
	print("No price datafile")

if os.path.exists(trade_system_file):
	pass
else:
	print("No system datafile")

if os.path.exists(trade_station_file):
	pass
else:
	print("No station datafile")

#-> загружаем файл с данными по станциям
station_file = open(trade_station_file, 'r')
station_data = {}

#unq:name@System.system_id,unq:name,ls_from_star,blackmarket,max_pad_size,market,shipyard,modified,outfitting,rearm,refuel,repair
#'1 G. CAELI','Smoot Gateway',4761,'N','L','Y','Y','2015-05-06 17:03:00','Y','Y','Y','Y'
# 0  - system
# 1  - station
# 2  - ls_from_star (0)
# 3  - blackmarket	(1)
# 4  - max_pad_size	(2)
# 5  - market		(3)
# 6  - shipyard		(4)
# 7  - modified		(5)
# 8  - outfitting	(6)
# 9  - rearm		(7)
# 10 - refuel		(8)
# 11 - repair		(9)
stationPt = re.compile(r"^'(.*)','(.*)',([\d\.-]+),'(.*)','(.*)','(.*)','(.*)','(.*)','(.*)','(.*)','(.*)','(.*)'$")

while True:
	# читаем файл построчно
	line = station_file.readline()
	if not line: break

	line = line[0:-1]

	if stationPt.search(line):
		search_result = stationPt.search(line).groups()

		tmp_system = search_result[0].lower()
		tmp_station = search_result[1].lower()
		
		if tmp_system not in station_data:
			station_data[tmp_system] = {}

		station_data[tmp_system][tmp_station] = search_result[2:]
	#	system_name = search_result[0].lower()
	#	system_data_coord = search_result[1:]
	#	system_data[system_name] = system_data_coord

station_file.close()

#-> загружаем файл с координатами систем
system_file = open(trade_system_file, 'r')
system_data = {}

systemPt = re.compile(r"^'(.*)',([\d\.-]+),([\d\.-]+),([\d\.-]+),'.*','.*'$")

while True:
	# читаем файл построчно
	line = system_file.readline()
	if not line: break

	line = line[0:-1]

	if systemPt.search(line):
		search_result = systemPt.search(line).groups()
		system_name = search_result[0].lower()
		system_data_coord = search_result[1:]
		system_data[system_name] = system_data_coord

system_file.close()

#-> загружаем данные с ценами
price_file = open(trade_data_file, 'r')
price_data = {}

productPt = re.compile(r'^\s*(\w[\w \.-]*\w)\s+(\d+)\s+(\d+)\s+([\dHML]+|\?|-|[\d?]+)\s+([\dHML]+|\?|-|[\d?]+)\s+(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s*[#]?.*$')

if os.path.exists(trade_data_json):
	print("Load from json")
	with open(trade_data_json, 'r', encoding='utf-8') as f:
		price_data = json.load(f)
else:
	print("Load from file")
	while True:
		# читаем файл построчно
		line = price_file.readline()
		if not line: break
		# нахоодим систему и станицю
		if line[0] == '@':
			sep = line.find('/')
			system_name = line[2:sep].lower()
			station_name = line[sep+1:-1].lower()

			if system_name not in price_data:
				price_data[system_name] = {}

			if station_name not in price_data[system_name]:
				price_data[system_name][station_name] = {}
		# строки содержащие группу продукта
		elif len(line) >= 4 and line[3] == '+':
			product_group = line[5:-1]
		# пустые строки и строки комментариев пропускаем
		elif len(line[0:-1]) == 0 or line[0] == '#':
			pass
		# строки содержащие сам продукт
		elif len(line) >= 6:
			line = line[0:-1]
			if productPt.search(line):
				search_result = productPt.search(line).groups()
				product = search_result[0].lower()
				product_data = search_result[1:]

				if product not in price_data[system_name][station_name]:
					price_data[system_name][station_name][product] = ()

				price_data[system_name][station_name][product] = product_data
			else:
				print(line)
		# остальные строки, которые не распознаны
		else:
			print(str(i) + '  : -' + line[0:-1] + '-')

	with open(trade_data_json, mode='w', encoding='utf-8') as f:
		json.dump(price_data, f)
	f.close()

price_file.close()

#for key in cars:
#    print "%s -> %s" % (key, cars[key])

if 1==1:
	#-> перебираем системы
	for l_system in price_data:
		#-> в системе перебираем станции
		for l_station in price_data[l_system]:
			#-> на станции перебираем товары
			for l_product in price_data[l_system][l_station]:
				#== print(d_product, price_data[d_system][d_station][d_product][0], sep = ' ---> ')
				if float(price_data[l_system][l_station][l_product][1]) > 0:
					#-> для каждого продукта перебираем все остальные системы (ох бл* и долго это все крутиться будет... но с другой стороны нужно же все перебрать)
					for r_system in price_data:
						#-> проверям что не выбрали туже систему
						if r_system != l_system:
							if r_system in system_data and l_system in system_data:
								dist = ((float(system_data[r_system][0]) - float(system_data[l_system][0])) ** 2 + (float(system_data[r_system][1]) - float(system_data[l_system][1])) ** 2 + (float(system_data[r_system][2]) - float(system_data[l_system][2])) ** 2) ** 0.5
								if dist > 0 and dist < 15.51:
									#-> перебираем станции
									for r_station in price_data[r_system]:
										#-> если изначальный продукт есть на станции считаем профит с его продажи
										if l_product in price_data[r_system][r_station]:
											# если профит с продажи больше 3000, выводим
											l_profit = float(price_data[r_system][r_station][l_product][0]) - float(price_data[l_system][l_station][l_product][1])
											if l_profit >= 150 and l_profit <= 5000:
												#print('=' * 30)
												#print(price_data[r_system][r_station][l_product])
												#print('-' * 30)
												#print(price_data[l_system][l_station][l_product])
												#print('-' * 30)
												#print(l_system + '/' + l_station + ':(' + price_data[l_system][l_station][l_product][0] + ') --- ' + l_product + ' ---> ' + r_system + '/' + r_station + ':(' + price_data[r_system][r_station][l_product][1] + ') = profit = ' + str(l_profit))
												#print('=' * 30)
												#-> считаем обратный профит
												for r_product in price_data[r_system][r_station]:
													if float(price_data[r_system][r_station][r_product][1]) > 0:
														if r_product in price_data[l_system][l_station]:
															r_profit = float(price_data[l_system][l_station][r_product][0]) - float(price_data[r_system][r_station][r_product][1])
															if r_profit >= 150 and r_profit <= 3000:
																profit = l_profit + r_profit
																if profit >= 1500:

																	if l_system in station_data:
																		if l_station in station_data[l_system]:
																			ls_from_star_l = int(station_data[l_system][l_station][0])
																			station_size_l = str(station_data[l_system][l_station][2])
																		else:
																			ls_from_star_l = -1
																			station_size_l = 'ND'
																	if r_system in station_data:
																		if r_station in station_data[l_system]:
																			ls_from_star_r = int(station_data[r_system][r_station][0])
																			station_size_r = str(station_data[r_system][r_station][2])
																		else:
																			ls_from_star_r = -1
																			station_size_r = 'ND'

																	if int(ls_from_star_r) > 0 and int(ls_from_star_r) < 100 and int(ls_from_star_l) > 0 and int(ls_from_star_l) < 100 and station_size_r == 'L' and station_size_l == 'L':
																		print('-' * 30)
																		print(l_system + '/' + l_station + ':(' + str(price_data[l_system][l_station][l_product][1]) + ') [' + ls_from_star_l + ':' + station_size_l + '] --- ' + l_product + ' ---> ' + r_system + '/' + r_station + ':(' + str(price_data[r_system][r_station][l_product][0]) + ') = profit = ' + str(l_profit))
																		print(r_system + '/' + r_station + ':(' + str(price_data[r_system][r_station][r_product][1]) + ') [' + ls_from_star_r + ':' + station_size_r + '] --- ' + r_product + ' ---> ' + l_system + '/' + l_station + ':(' + str(price_data[l_system][l_station][r_product][0]) + ') = profit = ' + str(r_profit))
																		print('profit: ' + str(profit))
																		#
																		print('distance: ' + str(dist))
																		#
																		print('-' * 30)