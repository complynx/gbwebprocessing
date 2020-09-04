import sys
import json
import urllib.request


# это мой личный проект, так что имею право использовать.
try:
    import pyvklogin
except ImportError:
    import subprocess
    ret = subprocess.run([sys.executable, "-m", "pip", "install", "pyvklogin", "PyQtWebEngine", "PyQt5"])
    if ret.returncode != 0:
        exit(ret.returncode)
    ret = subprocess.run([sys.executable, __file__] + sys.argv[1:])
    exit(ret.returncode)

app_id = 4527090
api_version = "5.122"


if __name__ == "__main__":
    file = sys.stdout
    if len(sys.argv) > 1:
        file = open(sys.argv[2], "w+")

    auth = pyvklogin.get_token_gui(app_id=app_id, api_ver=api_version, storage="""vkstorage""")

    req = urllib.request.Request(f'https://api.vk.com/method/users.get?access_token={auth["access_token"]}&v={api_version}')
    with urllib.request.urlopen(req) as res:
        res = json.load(res)
        json.dump(res, file, indent=4)


