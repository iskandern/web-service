# web-service

input data:
- icao(airport code)
- date
- time

output data:
- detailed weather report for this date at this airport 


you can download Metar library on 
- https://github.com/python-metar/python-metar

and then install with 
- python setup.py install

you can see usage examples in files
METAR and METAR_GET

for local run:
0. скачать web-service

1. установить flask 
$ mkdir myproject
$ cd myproject
$ python3 -m venv venv
$ source source venv/bin/activate

2. скачать библиотеку metar и переместить все файлы из папки python-metar-master в папку web-service так чтобы папка metar из python-metar-master лежала в одной и тоже папке с файлом app.py

(при необходимости)
установить requests
$ pip install requests
установить beautifulsoup4
$ pip install beautifulsoup4

3. запустить приложение с помощью python3 app.py

Либо можно открыть web-service в pycharm
Затем в file-settings-Project Iterpreter проверить наличие библиотек flask, requests, beautifulsoup4 (при необходимости установить через галочку)
И установть metar (для этого после скачивания нужно запустить python setup.py install в папке python-metar-master)
