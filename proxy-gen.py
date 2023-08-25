# made by V¡ktor
# proxy-gen.py
from requests import get
from contextlib import suppress
from threading import Thread
import os


##########################
save_path_name = "https-proxy.txt"
######################

__path__ = __file__
full_path = lambda filename: os.path.abspath(
    os.path.join(
        os.path.dirname(__path__),
        filename
    )
)

RED = lambda *text: "\033[1;31m" + " ".join(str(x) for x in text) + "\033[0m"
GREEN = lambda *text: "\033[1;32m" + " ".join(str(x) for x in text) + "\033[0m"


def proxy_gen() -> str:
    return get("https://api.proxyscrape.com/?request=displayproxies&proxytype=https&timeout=7000&country=ALL&anonymity=elite&ssl=no").text.split()


def check(proxy) -> bool:
    proxy_url = "http://" + proxy if not proxy.startswith(("http://", "https://")) else proxy
    proxies = {"https": proxy_url}
    with suppress(Exception):
        response = get(
            "https://api.ipify.org?format=json",
            proxies = proxies,
            timeout = 10
        ).json()
        if response["ip"] in proxy:
            return True
    return False


def verify_task(proxy) -> bool:
    isvalid = check(proxy)
    print("%r : %s" % (proxy, GREEN(isvalid) if isvalid else RED(isvalid)))
    if isvalid is True:
        with open(full_path(save_path_name), "a+") as save_path:
            if proxy not in save_path.read():
                save_path.write("https://%s\n" % proxy)
    return isvalid


def main() -> None:
    proxies: list = proxy_gen()
    for proxy in proxies:
        Thread(target=verify_task, args=(proxy,)).start()


if __name__ == "__main__":
    main()