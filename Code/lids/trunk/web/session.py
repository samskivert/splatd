import os
import cPickle as pickle

class SessionError(ValueError): pass
class Session(dict):

    def __init__(self, tempdir = None, id = None):
        dict.__init__(self)
        import time, random
        self.tempdir = tempdir
        t = time.time()
        
        # Generate the session id
        if id:
            self.id = id
        else: 
            self.id = hex(int(time.time()*1000))[2:] + \
                    hex(random.randint(0, 0x7FFFFFFF))[2:]

        self.filename = os.path.join(self.tempdir, self.id)
        
        # If the session file exists, check its time
        if self.exists():
            #if (self["time"] + 3600) < t:
            #    self.destroy()
            #    raise ValueError, "This session has expired"
            #else:
            #    self._depickle()
            self._depickle()
        else:
            self._create()
            # Then start storing information
            self["id"] = self.id
            self["time"] = t
            # Pickle it again
            self._pickle()

    def _create(self):
        f = open(self.filename, 'w')
        f.close()
        # Set the mode
        # XXX: Secure the file in other ways as well, anything else
        # run by this httpd can read this file
        os.chmod(self.filename, 0600)

    def exists(self):
        if os.path.exists(self.filename):
            return True
        return False

    def __setitem__(self, key, value):
        if self.exists():
            self._depickle()
            dict.__setitem__(self, key, value)
            self._pickle()

    def __delitem__(self, key, value):
        if self.exists():
            self._depickle()
            dict.__delitem__(self, key, value)
            self._pickle()

    #def __getitem__(self, key):
    #    dict.__getitem__(self, key)

    def _pickle(self):
        if self.exists():
            f = open(self.filename, 'w')
            pickle.dump(self, f)
            f.close()

    def _depickle(self):
        if self.exists():
            f = open(self.filename, 'r')
            p = pickle.load(f)
            self.update(p)
            f.close()

    def destroy(self):
        if self.exists():
            os.remove(self.filename)
            del self


