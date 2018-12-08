import logging
import os
import sys

import cffi


ffi = cffi.FFI()


def as_str(ffistr):
    return str(ffi.string(ffistr), 'utf-8')


class NitroKeyError(Exception):
    pass


class WrongModelError(NitroKeyError):
    pass


class NotConnectedError(NitroKeyError):
    pass


def require_connected(fn):
    def wrapper(self, *args, **kwargs):
        if not self.connected:
            raise NotConnectedError()
        return fn(self, *args, **kwargs)
    return wrapper


class NitroKey:
    MODEL_STORAGE = 'S'
    MODEL_PRO = 'P'

    def __init__(self, model=None):
        self.model = model
        self._connected = False
        self._encrypted_volume_mounted = False
        self._lib = get_library()
        self._lib.NK_set_debug(False)

    @property
    def connected(self):
        return self._connected

    def login(self, model):
        return 1 == self._lib.NK_login(model)

    def serial_number(self):
        return as_str(self._lib.NK_device_serial_number())

    @require_connected
    def lock(self):
        self._lib.NK_lock_device()

    @require_connected
    def logout(self):
        self._connected = False
        self._lib.NK_logout()

    def login_auto(self):
        return 1 == self._lib.NK_login_auto()

    def do_connect(self):
        if self.model is None:
            self._connected = self.login_auto()
            if self._connected:
                self.model = self._lib.NK_get_device_model()
        else:
            self._connected = self.login(self.model)

    def __enter__(self):
        self.do_connect()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.lock()
        self.logout()

    @require_connected
    def unlock_encrypted_volume(self, password):
        if self.model != NitroKey.MODEL_STORAGE:
            raise WrongModelError()
        return self._lib.NK_unlock_encrypted_volume(password)

    @require_connected
    def lock_encrypted_volume(self):
        return self._lib.NK_lock_encrypted_volume()


def get_library(paths=None, libpaths=None):
    fn = 'NK_C_API.h'

    if paths is None:
        paths = ['/usr/include', '/usr/local/include']
    if libpaths is None:
        libpaths = ['/lib', '/usr/lib', '/usr/local/lib']

    declarations = []
    for basepath in paths:
        path = os.path.join(basepath, "libnitrokey", fn)
        if not os.path.exists(path):
            continue
        with open(path, 'r') as f:
            declarations = f.readlines()
            break

    cnt = 0
    a = iter(declarations)
    for declaration in a:
        if declaration.strip().startswith('NK_C_API'):
            declaration = declaration.replace('NK_C_API', '').strip()
            while ';' not in declaration:
                declaration += (next(a)).strip()
            ffi.cdef(declaration, override=True)
            cnt +=1
    logging.debug(f'Imported {cnt} declarations')


    C = None
    libpath = None
    libnames = ["libnitrokey.so", "libnitrokey.dylib",
                "libnitrokey.dll", "nitrokey.dll"]
    for path in libpaths:
        for ln in libnames:
            if os.path.exists(os.path.join(path, ln)):
                libpath = os.path.join(path, ln)

    if libpath is None:
        logging.debug('No library found')
        return None

    return ffi.dlopen(libpath)
