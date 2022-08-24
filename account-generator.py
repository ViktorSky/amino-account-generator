# made by V¡ktor
# Account Generator

parameters = {
    "community-link": None,
    "save-path": "accounts-generared.json",
    "proxies-path": "https-proxy.txt"
}

import os
from random import randint, choice, shuffle
from hmac import new
from json import dumps, loads, dump
from pathlib import Path
from hashlib import sha1
from string import ascii_letters, digits
from bs4 import BeautifulSoup
from threading import Thread
from contextlib import suppress
from uuid import uuid4 as uuid_generator
from base64 import b64encode
from time import (
    time as timestamp,
    sleep
)

try: os.system("pip install -r requirements.txt")
finally:
    from flask import Flask
    import names
    from requests import Session
    from secmail import SecMail


signatureKey="f8e7a61ac3f725941e3ac7cae2d688be97f30b93"
deviceKey="02b258c63559d8804321c5d5065af320358d366f"


#-----------------FLASK-APP-----------------
flask_app = Flask(__name__)
@flask_app.route('/')
def home(): return "Account Generator is on! :b"
ht = '0.0.0.0'
pt = randint(2000, 9000)
def run(): flask_app.run(host=ht, port=pt)
#----------------------------------------------------


class LimitationError(Exception): pass
class TooManyRequests(Exception): pass


full_path = lambda filename: os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        filename
    )
)
clear = lambda: os.system('cls' if os.name=='nt' else 'clear')

RED = lambda *text: "\033[1;31m" + " ".join(i for i in text) + "\033[0m"
GREEN = lambda *text: "\033[1;32m" + " ".join(i for i in text) + "\033[0m"
YELLOW = lambda *text: "\033[1;33m" + " ".join(i for i in text) + "\033[0m"

class Client:
    
    sid: str = None
    uid: str = None
    device = None
    session = None
    proxies = None
    uuid = None

    def __init__(
        self: object,
        device: str = None,
        proxies: dict = None
    ) -> None:

        self.session: object = Session()
        self.device: str = device or self.device_gen()
        self.proxies: dict = proxies or {}
        self.uuid = str(uuid_generator())


    def device_gen(
        self: object,
        device_info: bytes = bytes.fromhex("42") + os.urandom(20)
    ) -> str:

        new_device: str = (
            device_info + new(
                bytes.fromhex(deviceKey),
                device_info,
                sha1
            ).digest()
        ).hex().upper()
        return new_device


    def sig(
        self: object,
        data: str = None
    ) -> str:

        signature: str = b64encode(
            bytes.fromhex("42") + new(
                bytes.fromhex(signatureKey),
                data.encode("utf-8"),
                sha1
            ).digest()
        ).decode("utf-8")
        return signature


    def headers(
        self: object,
        data: str = None
    ) -> dict:

        headers = {
            "NDCDEVICEID": self.device,
            "SMDEVICEID": self.uuid,
            "Accept-Language": "en-EN",
            "Content-Type":
                "application/json; charset=utf-8",
            "User-Agent":
                'Dalvik/2.1.0 (Linux; U; Android 7.1; LG-UK495 Build/MRA58K; com.narvii.amino.master/3.3.33180)', 
            "Host": "service.narvii.com",
            "Accept-Encoding": "gzip",
            "Connection": "keep-alive"
        }
        if data is not None:
            headers["Content-Length"] = str(len(data))
            headers["NDC-MSG-SIG"] = self.sig(data)
        if self.sid is not None:
            headers["NDCAUTH"] = "sid=%s" % self.sid
        return headers


    def request(
        self: object,
        method: ["DELETE", "GET", "POST", "PUT"],
        url: str = "",
        data: str = None,
        **kwargs: dict
    ) -> object:
        kwargs = {
            "data": data,
            "headers": self.headers(data = data),
            "method": method.upper(),
            "proxies": self.proxies or {},
            "url": "https://service.narvii.com/api/v1/%s" % url
        }
        with self.session.request(**kwargs) as response:
            if response.status_code != 200:
                if response.status_code in [403]:
                    raise LimitationError(response.text)
                elif response.status_code in [400]:
                    if "3 accounts" in response.json()["api:message"]:
                        raise LimitationError(response.json())
                    raise TooManyRequests(response.json())
                raise Exception([response.status_code, response.text])
            return response


    def register(
        self: object,
        email: str,
        password: str,
        nickname: str,
        code: str
    ) -> dict:

        data = dumps({
            "address": None,
            "clientCallbackURL": "narviiapp://relogin",
            "clientType": 100,
            "deviceID": self.device,
            "email": email,
            "identity": email,
            "latitude": 0,
            "longitude": 0,
            "nickname": nickname,
            "secret": "0 %s" % password,
            "timestamp": int(timestamp() * 1000),
            "type": 1,
            "validationContext": {
                "data": {
                    "code": str(code)
                },
                "type": 1,
                "identity": email
            }
        })

        return self.request(
            method = "POST",
            url = "g/s/auth/register",
            data = data
        ).json()


    def request_verify_code(
        self: object,
        email: str,
        password: bool = False
    ) -> dict:

        data = {
            "deviceID": self.device,
            "identity": email,
            "type": 1
        }

        if password is not False:
            data["level"] = 2
            data["purpose"] = "reset-password"

        data = dumps(data)

        return self.request(
            method = "POST",
            url = "g/s/auth/request-security-validation",
            data=data
        ).json()


    def login(
        self: object,
        email: str,
        password: str
    ) -> dict:

        data = dumps({
            "email": email,
            "v": 2,
            "secret": f"0 {password}",
            "deviceID": self.device,
            "clientType": 100,
            "action": "normal",
            "timestamp": int(timestamp() * 1000)
        })

        login = self.request(
            method = "POST",
            url = "g/s/auth/login",
            data = data
        ).json()

        self.sid = login["sid"]
        self.uid = login["account"]["uid"]
        self.secret = login["secret"]
        
        return login



class AccountGenerator:
    # Class to Generate One Account
    account: dict = {}
    email = None
    password = None
    device = None

    def __init__(
        self: object,
        proxies: dict = None
    ) -> None:

        amino: object = Client(proxies=proxies)
        email = self.get_new_email(1)
        print(GREEN("\n~ Generating account for:"), email)
        sleep(1)
        password = self.get_new_password(10)
        print(GREEN("~ Password:"), "*" * len(password))
        nickname = self.get_new_nickname()
        amino.request_verify_code(email=email)
        sleep(3.3)
        captcha = self.get_captcha(email)
        print(GREEN("~ Captcha:"), captcha)
        code = self.captcha_solver(captcha)
        print(GREEN("~ Code:"), code)
        sleep(2)
        account = amino.register(
            email=email,
            password=password,
            nickname=nickname,
            code=code
        )
        
        with suppress(Exception):
            amino.login(email, password)
        
        self.account = {
            "email": email,
            "password": password,
            "secret": amino.secret,
            "device": amino.device,
            "sid": amino.sid,
            "uid": amino.uid
        }
        print(YELLOW("~ Account saved!"))


    def get_new_email(
        self: object,
        count: int=None
    ) -> str:
        return SecMail().generate_email(
            count = count or 1
        )


    def get_new_password(
        self: object,
        length: int = 6,
        characters = list(ascii_letters + digits + "@#&"*2)
    ) -> str:

        shuffle(characters)
        return "".join(choice(characters) for _ in range(int(length)))


    def get_new_nickname(
        self: object
    ) -> str:

        return names.get_full_name(
            gender = choice(["male", "female"])
        )


    def get_captcha(
        self: object,
        email: str
    ) -> str:

        inbox = SecMail().get_messages(email = email)
        for id in inbox.id:
            with suppress(Exception):
                msg = SecMail().read_message(
                    email = email, id = id
                ).htmlBody
                images = BeautifulSoup(
                    msg, "html.parser"
                ).find_all("a")[0]
                url = images['href']
                if url is not None:
                    return url


    def captcha_solver(
        self: object,
        captcha: str,
        session: object = Session()
    ) -> str:
        return session.post(
            "https://captchasolver.neodouglas.repl.co/predict",
            data = {"image": captcha}
        ).json()['captcha'][0]



def get_proxies() -> object:
    if not (path := parameters.get("proxies-path", False)):
        raise Exception("Invalid proxies-path: %r" % path)

    try:
        proxy_path_name = full_path(parameters["proxies-path"])
        with open(proxy_path_name, "r") as proxy_path:
            yield from [{
                    "https": proxy.replace("https://", "")
                } for proxy in proxy_path.read().split()
            ]
    except FileNotFoundError:
        print(GREEN(
            "\n~ %r file isn't in this this generator path."
            "Run `proxy-gen.py`."
            ) % parameters["proxies-path"]
        ); exit(1)



if __name__ == "__main__":
    Thread(target=run).start()
    sleep(2); clear()
    save_path_name = full_path(parameters["save-path"])
    try: accounts: list = loads(open(save_path_name).read())
    except: accounts: list = []
    proxies: object = get_proxies()
    proxy = None
    while True:
        try:
            accounts.append(AccountGenerator(proxies=proxy).account)
            with open(save_path_name, "w") as save_path:
                dump(accounts, save_path, indent=4, sort_keys=True)
        except LimitationError:
            try: proxy: str = next(proxies)
            except StopIteration:
                proxies: object = get_proxies()
                proxy: str = next(proxies)
        except TooManyRequests as Error:
            print(RED("~ Error %d:" % Error.args[0]["api:statuscode"], Error.args[0]["api:message"]))
            sleep(5)
        except Exception as Error:
            print(RED("~ Error:" % Error.args[0]))
            sleep(3)
                
