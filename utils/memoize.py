import pickle

import sys
import hashlib
import datetime
import os


def memoize_fs(cachedir, func_name, lifetime):
    if not os.path.exists(cachedir):
        tb = sys.exc_info()[2]
        raise FileExistsError("where is this fucking directory???").with_traceback(tb)
    else:
        cachedir = os.path.join(cachedir, "cache")

    def decorator(func):
        def _memoize_fs(*args, **kwargs):
            func_hash = hashlib.md5((func_name + args.__str__() + kwargs.__str__()).encode('utf-8'))
            filename = func_hash.hexdigest()
            filepath = os.path.join(cachedir, str(filename))  # type: str
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
                with open(filepath, 'wb') as file:
                    result = func(*args, **kwargs)
                    try:
                        # write die line on cache
                        file.write(bytes(die_line, encoding='utf-8'))
                        pickle.dump(result, file)
                    except RecursionError as error:
                        print("recursion limit")
            return result

        return _memoize_fs

    return decorator
