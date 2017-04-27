import pickle

import sys
import hashlib
import datetime
import os

already_check_dir = False


def _get_file_path(cachedir, func_name: str, *args, **kwargs):
    global already_check_dir
    if not already_check_dir:
        already_check_dir = True
        if not os.path.exists(cachedir):
            tb = sys.exc_info()[2]
            raise FileExistsError("where is this fucking directory???").with_traceback(tb)

    func_hash = hashlib.md5((func_name + args.__str__() + kwargs.__str__()).encode('utf-8'))
    filename = func_hash.hexdigest()
    return os.path.join(os.path.join(cachedir, "cache"), str(filename))


def memoize_fs(cachedir: str, func_name: str, lifetime: int):
    def decorator(func):
        def _memoize_fs(*args, **kwargs):
            filepath = _get_file_path(cachedir, func_name, *args, **kwargs)
            now = int(datetime.datetime.now().timestamp())
            die_line = str(now + lifetime)  # type: str
            if os.path.exists(filepath):
                with open(filepath, 'rb') as file:
                    # check how old cache
                    die_line_file = file.read(10)
                    if now > int(die_line_file.decode('utf-8')):
                        # close and remove file and recursive call of function
                        file.close()
                        os.remove(filepath)
                        result = _memoize_fs(*args, **kwargs)
                    else:
                        result = pickle.load(file)
            else:
                result = func(*args, **kwargs)
                if result:
                    with open(filepath, 'wb') as file:
                        try:
                            # write die line on cache
                            file.write(bytes(die_line, encoding='utf-8'))
                            pickle.dump(result, file)
                        except RecursionError:
                            print("recursion limit")
            return result

        return _memoize_fs

    return decorator


def check_in_cache(cachedir: str, func_name: str, *args, **kwargs):
    filepath = _get_file_path(cachedir, func_name, *args, **kwargs)
    now = int(datetime.datetime.now().timestamp())
    if os.path.exists(filepath):
        with open(filepath, 'rb') as file:
            # check how old cache
            die_line_file = file.read(10)
            if now < int(die_line_file.decode('utf-8')):
                return True
    return False
