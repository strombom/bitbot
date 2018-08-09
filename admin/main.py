
import os
import sys
from multiprocessing import Process, Queue


def get_appdata_path():
    APPNAME = "Visualiser"
    if sys.platform == 'darwin':
        from AppKit import NSSearchPathForDirectoriesInDomains
        # http://developer.apple.com/DOCUMENTATION/Cocoa/Reference/Foundation/Miscellaneous/Foundation_Functions/Reference/reference.html#//apple_ref/c/func/NSSearchPathForDirectoriesInDomains
        # NSApplicationSupportDirectory = 14
        # NSUserDomainMask = 1
        # True for expanding the tilde into a fully qualified path
        appdata_path = path.join(NSSearchPathForDirectoriesInDomains(14, 1, True)[0], APPNAME)
    elif sys.platform == 'win32':
        appdata_path = path.join(environ['APPDATA'], APPNAME)
    else:
        appdata_path = path.expanduser(path.join("~", "." + APPNAME))

    if not os.path.exists(appdata_path):
        os.makedirs(appdata_path)

    return appdata_path

def get_root_path():
    return os.path.dirname(os.path.abspath(__file__))


if __name__ == '__main__':
    import signal
    try:
        import winpaths
    except:
    	pass
    
    import logging

    import subprocess
    from os import path, environ

    from webserver import start_webserver
    
    queues = {'webserver': Queue(),
              'streamer': Queue(),
              'main': Queue()}

    def signal_handler(signal, frame):
        queues['main'].put(("exit", None))

    restart = False
    signal.signal(signal.SIGINT, signal_handler)

    # Find program application data path
    appdata_path = get_appdata_path()
    root_path = get_root_path()

    launchers = [("webserver", start_webserver),
                 ]
    
    servers = []
    for (name,launcher) in launchers:
        server = Process(target = launcher, args = (queues, appdata_path, root_path), name = name)
        server.daemon = True
        server.start()
        servers.append(server)

    while True:
        try:
            command, payload = queues['main'].get()
            if command == "exit":
                restart = False
                break
            elif command == "restart":
                restart = True
                break
            elif command == "error":
                logging.error("Main got error: %s", payload)
        except KeyboardInterrupt:
            print("Main function ctrl-c")
            restart = False
            break
