
import copy
import json
import time
import shutil
from threading import Lock


# TODO: Consider replacing this with a sqlite database
class ConfigFile:
    def __init__(self, filename, read_only = False, default = {}):
        self.lock = Lock()
        self._lock = Lock()
        self.read_only = read_only
        self.filename = filename

        # Check if file exists
        try:
            open(filename, 'r')
        except:
            # Use backup
            try:
                shutil.copyfile(filename + ".backup", filename)
                open(filename, 'r')
            except:
                # If no backup, use default config
                self.config = copy.copy(default)
                self.save()

        try:
            f = open(filename, 'r')
            self.config = json.loads(f.read())
            f.close()
        except:
            self.config = None

    def __setitem__(self, index, value):
        self.config[index] = value

    def __getitem__(self, index):
        return self.config[index]

    def save(self):
        with self._lock:
            print("Config save")
            self.config['update_timestamp'] = time.time()

            if self.config is None:
                return
            try:
                # TODO: This scheme doesn't prevent corruption if aborted halfway through saving.
                with open(self.filename + '.backup', 'w') as f:
                    f.write(json.dumps(self.config, sort_keys=True, indent=2, separators=(',', ': ')))

                with open(self.filename, 'w') as f:
                    f.write(json.dumps(self.config, sort_keys=True, indent=2, separators=(',', ': ')))

            except:
                pass

if __name__ == "__main__":
    print("test")
    config = ConfigFile("settings.txt", default = {'update_timestamp': time.time()
                                                  })
    config.save()

