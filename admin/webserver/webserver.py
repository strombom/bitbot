
import io
import os
import json
import shutil
import socket
import base64
import random
import hashlib
import datetime
import requests

from flask import Flask, Response
from flask import request
from flask import abort, redirect, url_for, send_file, send_from_directory
from flask import render_template
from jinja2 import Environment, FileSystemLoader
from time import sleep
from operator import itemgetter
from threading import Thread
from string import digits
from .config import ConfigFile

import time

running = True
queues = {}
event_status = {}
config = None
appdata_path = ""
background_images = {}
exit_code = ""
root_path = ""

enabled = True

app = Flask(__name__, static_folder = None) #, static_path = None, static_folder = None)

def getView(product_key = None):
    if product_key is not None:
        for view in config['views'] + config['views_not_activated']:
            if view['product_key'] == product_key:
                return view
    return None

@app.route("/", methods=['GET'])
def root():
    print("a")
    return redirect('/simulation/prediction/btc/usdt')

@app.route('/static/<path:path>', methods=['GET'])
def serve_static(path):
    print("serve_static")
    #data = embedded_files.read("/static/" + path)

    #return send_from_directory('C:\\development\\github\\bitbot\\admin\\webserver\\static', 'css\\app.css')

    static_file_dir = os.path.join(root_path, 'static')
    #os.path.join(os.path.dirname(os.path.realpath(__file__)), 'static')

    print("serve_static ", static_file_dir, path)
    return send_from_directory(static_file_dir, path)

    if ".js" in path:
        data = translate_text(data)
        return Response(data, mimetype='application/javascript')
    elif ".css" in path:
        return Response(data, mimetype='text/css')
    else:
        print("serve static", path)
        return Response(data, mimetype='text/html')

@app.route("/live_view", defaults = {'product_key': None}, methods = ['GET'])
@app.route("/live_view/<product_key>", methods = ['GET'])
def live_view_product_key(product_key):
    print("b")
    view = getView(product_key)
    if view is None:
        if len(config['views']) > 0:
            return redirect("/live_view/" + config['views'][0]['product_key'])
        else:
            return redirect("/setup")
    return render_template("live_view.html", page = "live_view", view = view, product_key = product_key)

@app.route("/simulation/prediction/btc/usdt", methods=['GET'])
def simulation_prediction():

    print("d")

    print("path ", os.path.join(root_path, 'templates'))
    env = Environment(loader=FileSystemLoader(os.path.join(root_path, 'templates')))
    template = env.get_template('base.html')

    return template.render(page = "Simulation", subpage = "Prediction")

if os.name != "nt":
    import fcntl
    import struct

    def get_interface_ip(ifname):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return socket.inet_ntoa(fcntl.ioctl(s.fileno(), 0x8915, struct.pack('256s',
                                ifname[:15]))[20:24])

def get_lan_ip():
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 0))  # connecting to a UDP address doesn't send packets
        return s.getsockname()[0]
    except:
        pass

    ip = socket.gethostbyname(socket.gethostname())
    if ip.startswith("127.") and os.name != "nt":
        interfaces = [
            "wlan0",
            "wlan1",
            "eth0",
            "eth1",
            "eth2",
            "wifi0",
            "ath0",
            "ath1",
            "ppp0",
            ]
        for ifname in interfaces:
            try:
                ip = get_interface_ip(ifname)
                break
            except IOError:
                pass
    return ip

def send_config_thread(queues):
    global running
    while running:
        sleep(1.0)
        #queues['event_receiver'].put(('config', config.config))
        #queues['streamer'].put(('config', config.config))
    logging.info("Webserver: config_thread exiting")

@app.route('/shutdown/<code>', methods=['GET'])
def shutdown(code):
    if code == exit_code:
        request.environ.get('werkzeug.server.shutdown')()
        logging.info("Webserver: Exiting")
        return 'OK'
    else:
        logging.error("Webserver: Wrong exit code")
        return 'FAIL'

def command_thread(queues, config, exit_code):
    while True:
        try:
            command, payload = queues['webserver'].get()
            if command == "exit":
                global running
                running = False
                if enabled:
                    r = requests.get('http://localhost:' + str(config['web_interface']['port']) + '/shutdown/' + exit_code)
                break
            #elif command == "event_status":
            #    global event_status
            #    event_status = payload
            #elif command == "event_logger":
            #    global event_logger
            #    event_logger = payload

        except Exception as e:
            logging.exception("webserver command_thread exception [%s]" % e)

def start_webserver(_queues, _appdata_path, _root_path):
    global queues
    queues = _queues

    global appdata_path
    appdata_path = _appdata_path

    global root_path
    root_path = _root_path

    #global lookup
    #logging.info("lookup directory: %s", os.path.join(root_path, "html"))
    #lookup = TemplateLookup(directories=[os.path.join(root_path, "html")], input_encoding='utf-8')

    global config
    config = ConfigFile(os.path.join(appdata_path, "settings.txt"), 
        default = {'testsetting': 'testvalue'
                  })

    global exit_code
    exit_code = ''.join(random.sample("ABCDEFGHIJKLMNOPQRSTUVWXYZ", 10))



    #queues['event_receiver'].put(('start', config['event_receiver']['port']))
    #queues['desktop_gui'].put(('set_status_address', get_lan_ip() + ":" + str(config['web_interface']['port'])))

    #Thread(target = command_thread, args = (queues, config, exit_code)).start()
    #Thread(target = send_config_thread, args = (queues, )).start()

    #logging.info("Webserver starting")
    if enabled:
        try:
            app.run(port = config['web_interface']['port'], debug = False, use_reloader = False, host='0.0.0.0', )
        except InterruptedError:
            print("Webserver ctrl-c")
            #logging.info("Webserver ctrl-c")

    logging.info("Webserver stopped")
