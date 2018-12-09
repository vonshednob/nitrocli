import logging
import os
import warnings

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
                self.model = self.get_model()
        else:
            self._connected = self.login(self.model)

    def __enter__(self):
        self.do_connect()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.logout()

    @require_connected
    def get_model(self):
        warnings.simplefilter('ignore', UserWarning)
        model = self._lib.NK_get_device_model()
        warnings.simplefilter('default', UserWarning)
        if model == 1:
            model = NitroKey.MODEL_PRO
        elif model == 2:
            model = NitroKey.MODEL_STORAGE
        return model

    @require_connected
    def get_status(self):
        status = ffi.new('struct NK_storage_status*')
        if self._lib.NK_get_status_storage(status) == 0:
            return status
        return None

    @require_connected
    def unlock_encrypted_volume(self, password):
        if self.model != NitroKey.MODEL_STORAGE:
            raise WrongModelError()
        pwdkeeper = ffi.new('char[]', bytes(password, 'utf-8'))
        return self._lib.NK_unlock_encrypted_volume(pwdkeeper)

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
            cnt += 1
    logging.debug(f'Imported {cnt} declarations')

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

    ffi.cdef('''struct NK_storage_ProductionTest{
    uint8_t FirmwareVersion_au8[2];
    uint8_t FirmwareVersionInternal_u8;
    uint8_t SD_Card_Size_u8;
    uint32_t CPU_CardID_u32;
    uint32_t SmartCardID_u32;
    uint32_t SD_CardID_u32;
    uint8_t SC_UserPwRetryCount;
    uint8_t SC_AdminPwRetryCount;
    uint8_t SD_Card_ManufacturingYear_u8;
    uint8_t SD_Card_ManufacturingMonth_u8;
    uint16_t SD_Card_OEM_u16;
    uint16_t SD_WriteSpeed_u16;
    uint8_t SD_Card_Manufacturer_u8;
  };
  struct NK_storage_status {
    bool unencrypted_volume_read_only;
    bool unencrypted_volume_active;
    bool encrypted_volume_read_only;
    bool encrypted_volume_active;
    bool hidden_volume_read_only;
    bool hidden_volume_active;
    uint8_t firmware_version_major;
    uint8_t firmware_version_minor;
    bool firmware_locked;
    uint32_t serial_number_sd_card;
    uint32_t serial_number_smart_card;
    uint8_t user_retry_count;
    uint8_t admin_retry_count;
    bool new_sd_card_found;
    bool filled_with_random;
    bool stick_initialized;
  };''')

    return ffi.dlopen(libpath)
