# Pretty sure this wont work for a joiner so dont bother wasting your time 
# For buying a joiner/raider refer to https://www.utilitytoolsv2.store/ . They will be released as soon as we go live on prem tools again

import base64
import json
import random
import time
import os
import sys
import threading
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor
import re
import tls_client
from pystyle import Colors, Colorate
from colorama import Fore, Style, init

init(autoreset=True)
lock = threading.Lock()

class Stats:
    def __init__(self):
        self._lock = threading.Lock()
        self.valid = self.locked = self.errors = self.rate_limited = 0

    def bump(self, key):
        with self._lock:
            setattr(self, key, getattr(self, key) + 1)

stats = Stats()


def set_terminal_size(columns, lines):
    if sys.platform == "win32":
        os.system(f"mode con: cols={columns} lines={lines}")
    else:
        sys.stdout.write(f"\x1b[8;{lines};{columns}t")

def gradient(text):
    return Colorate.Horizontal(Colors.green_to_cyan, text)

class FileHandler:
    def __init__(self):
        self.timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.output_path = f"output/{self.timestamp}"
        self._ready = False

    def _ensure_dir(self):
        if not self._ready:
            with lock:
                os.makedirs(self.output_path, exist_ok=True)
                self._ready = True

    def save_token(self, token, data):
        self._ensure_dir()

        if not data.get("valid"):
            filename = "locked.txt"
        elif data.get("nitro"):
            days = data.get("nitro_days", 0)
            filename = "3monthnitro.txt" if days > 31 else "1monthnitro.txt"
        elif data.get("phone"):
            filename = "phoneverified.txt"
        else:
            filename = "valid.txt"

        with lock:
            with open(f"{self.output_path}/{filename}", "a") as f:
                f.write(f"{token}\n")



_ANSI_RE = re.compile(r'\x1b\[[0-9;]*m')
def ansi_center(text: str, width: int) -> str:
    visible_len = len(_ANSI_RE.sub('', text))
    total_pad = max(0, width - visible_len)
    left_pad  = total_pad // 2
    right_pad = total_pad - left_pad
    return ' ' * left_pad + text + ' ' * right_pad


class Logger:
    def __init__(self):
        self._o     = gradient("[")
        self._c     = gradient("]")
        self._arrow = gradient("~>")

    def brand(self):
        return f"{self._o} {Fore.WHITE}UtilityToolsV2{Style.RESET_ALL} {self._c}"

    def _prompt(self, text_label=""):
        txt = f"{Fore.WHITE}{text_label}{Style.RESET_ALL} " if text_label else ""
        with lock:
            return input(f"      {self.brand()} {txt}{self._arrow} ").strip()

    def input(self, text_label=""):
        return self._prompt(text_label)

    def confirm(self, text_label=""):
        choices = (
            f"{Fore.WHITE}({Fore.GREEN}y{Fore.WHITE}/"
            f"{Fore.RED}n{Fore.WHITE}){Style.RESET_ALL}"
        )
        txt = f"{Fore.WHITE}{text_label}{Style.RESET_ALL} " if text_label else ""
        with lock:
            res = input(
                f"      {self.brand()} {txt}{choices} {self._arrow} "
            ).strip().lower()
        return res == "y"

    def info(self, text, detail=None):
        det = (
            f" {Fore.WHITE}| {Fore.LIGHTCYAN_EX}{detail}{Style.RESET_ALL}"
            if detail else ""
        )
        with lock:
            print(f"      {self.brand()} {Fore.WHITE}{text}{Style.RESET_ALL}{det}")

    def warn(self, text, detail=None):
        det = (
            f" {Fore.WHITE}| {Fore.YELLOW}{detail}{Style.RESET_ALL}"
            if detail else ""
        )
        with lock:
            print(
                f"      {self.brand()} {Fore.YELLOW}{text}{Style.RESET_ALL}{det} "
                f"{self._arrow} {Fore.YELLOW}Warning{Style.RESET_ALL}"
            )

    def error(self, text, detail=None):
        det = (
            f" {Fore.WHITE}| {Fore.LIGHTRED_EX}{detail}{Style.RESET_ALL}"
            if detail else ""
        )
        with lock:
            print(
                f"      {self.brand()} {Fore.WHITE}{text}{Style.RESET_ALL}{det} "
                f"{self._arrow} {Fore.RED}Failed{Style.RESET_ALL}"
            )

    def account_info(self, data):
            email      = data.get("email") or "N/A"
            phone      = data.get("phone") or "N/A"
            nitro_days = data.get("nitro_days", 0)
            has_nitro  = data.get("nitro", False)
            e_col = Fore.GREEN if data.get("email") else Fore.RED
            p_col = Fore.GREEN if data.get("phone") else Fore.RED
            n_col = Fore.GREEN if has_nitro          else Fore.RED
            indent = " " * 6
            box_width = 60 
            border = gradient("─" * box_width)
            nitro_str = f"{nitro_days} Days Remaining" if has_nitro else "None"
            l1 = f"Email {self._arrow} {e_col}{email}{Style.RESET_ALL} | Phone {self._arrow} {p_col}{phone}{Style.RESET_ALL}"
            l2 = f"User {self._arrow} {Fore.WHITE}{data.get('username')}{Style.RESET_ALL} | ID {self._arrow} {Fore.LIGHTBLACK_EX}{data.get('user_id')}{Style.RESET_ALL}"
            l3 = f"Nitro {self._arrow} {n_col}{nitro_str}{Style.RESET_ALL} | Boosts {self._arrow} {Fore.YELLOW}{data.get('boost_slots', 0)}{Style.RESET_ALL}"

            with lock:
                print(f"\n{indent}{gradient('╭')}{border}{gradient('╮')}")
                print(f"{indent}{gradient('│')} {ansi_center(l1, box_width - 2)} {gradient('│')}")
                print(f"{indent}{gradient('│')} {ansi_center(l2, box_width - 2)} {gradient('│')}")
                print(f"{indent}{gradient('│')} {ansi_center(l3, box_width - 2)} {gradient('│')}")
                print(f"{indent}{gradient('╰')}{border}{gradient('╯')}\n")


# i had this class sitting on my 2024 gen for no reason so i added it here blehhh
class CFClearance:
    CF_CHALLENGE_URL  = "https://discord.com/cdn-cgi/challenge-platform/h/g/orchestrate/jsch/v1"
    CF_BM_REPORT_URL  = "https://discord.com/cdn-cgi/bm/cv/lgFun/answer"
    def __init__(self, logger: Logger):
        self.logger = logger
# i like melted chocolate idk why people like it solid
    def warm_session(self, session: tls_client.Session, headers: dict) -> dict:
        cf_cookies: dict[str, str] = {}
        try:
            warm_headers = {
                "accept":           "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "accept-language":  headers.get("accept-language", "en-US,en;q=0.9"),
                "user-agent":       headers.get("user-agent", ""),
                "sec-fetch-dest":   "document",
                "sec-fetch-mode":   "navigate",
                "sec-fetch-site":   "none",
            }
            if "sec-ch-ua" in headers:
                warm_headers["sec-ch-ua"]        = headers["sec-ch-ua"]
                warm_headers["sec-ch-ua-mobile"] = headers.get("sec-ch-ua-mobile", "?0")
                warm_headers["sec-ch-ua-platform"]= headers.get("sec-ch-ua-platform", '"Windows"')
            r1 = session.get(self.CF_CHALLENGE_URL, headers=warm_headers, allow_redirects=True)
            cf_cookies.update(self._extract_cf_cookies(r1))
            bm_headers = {**warm_headers,
                          "content-type": "application/x-www-form-urlencoded",
                          "origin":        "https://discord.com",
                          "referer":       "https://discord.com/"}
            r2 = session.post(
                self.CF_BM_REPORT_URL,
                headers=bm_headers,
                data="v=3&answer=0&pow=noop",
            )
            cf_cookies.update(self._extract_cf_cookies(r2))
        except Exception as exc:
            self.logger.warn("CF warm-up failed", str(exc)[:60])
        for name, value in cf_cookies.items():
            session.cookies.set(name, value, domain=".discord.com")
        return cf_cookies
    










# so this comment is actually api bypassing :3 skid ts below
# from xritura import *
# xritura.apibypass(discrd.com)
# Done 


















    @staticmethod
    def _extract_cf_cookies(response) -> dict[str, str]:
        found: dict[str, str] = {}
        if response is None:
            return found

        jar = getattr(response, "cookies", {})
        for name in ("__cf_clearance", "cf_bm", "__cflb", "__cfruid"):
            val = jar.get(name)
            if val:
                found[name] = val


        raw_headers = getattr(response, "headers", {})
        set_cookie = raw_headers.get("set-cookie", "")
        if set_cookie:
            for part in set_cookie.split(";"):
                part = part.strip()
                if "=" in part:
                    k, v = part.split("=", 1)
                    k = k.strip()
                    if k in ("__cf_clearance", "cf_bm", "__cflb", "__cfruid"):
                        found[k] = v.strip()

        return found

    @staticmethod
    def inject_cookies(headers: dict, cf_cookies: dict) -> dict:
        if not cf_cookies:
            return headers
        headers = dict(headers)
        existing = headers.get("cookie", "")
        cf_str = "; ".join(f"{k}={v}" for k, v in cf_cookies.items())
        headers["cookie"] = f"{existing}; {cf_str}".lstrip("; ")
        return headers


class DiscordTokenChecker:
    BASE_URL  = "https://discord.com/api/v9"
    BUILD_NUM = 270000
    PROFILES = [
        {
            "id": "chrome_120", "os": "Windows", "browser": "Chrome", "bv": "120.0.0.0",
            "ua": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
            "sec_ch_ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            "ja3": (
                "771,4865-4866-4867-49195-49199-49196-49200-52393-52392-"
                "49171-49172-156-157-47-53,"
                "0-23-65281-10-11-35-16-5-13-18-51-45-43-27-21,29-23-24,0"
            ),
            "h2": {
                "HEADER_TABLE_SIZE": 65536, "MAX_CONCURRENT_STREAMS": 1000,
                "INITIAL_WINDOW_SIZE": 6291456, "MAX_FRAME_SIZE": 16384,
                "MAX_HEADER_LIST_SIZE": 262144,
            },
        },
        {
            "id": "firefox_117", "os": "Windows", "browser": "Firefox", "bv": "117.0",
            "ua": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:117.0) "
                "Gecko/20100101 Firefox/117.0"
            ),
            "sec_ch_ua": None,                          
            "ja3": (
                "771,4865-4866-4867-49195-49199-49196-49200-52393-52392,"
                "0-23-65281-10-11-35-16-5-13-18,29-23-24,0"
            ),
            "h2": {
                "HEADER_TABLE_SIZE": 65536, "INITIAL_WINDOW_SIZE": 131072,
                "MAX_FRAME_SIZE": 16384,
            },
        },
    ]

    def __init__(self, logger: Logger):
        self.logger = logger
        self.cf     = CFClearance(logger)


    def _make_session(self, profile: dict, proxy: str | None) -> tls_client.Session:
        sess = tls_client.Session(
            client_identifier=profile["id"],
            random_tls_extension_order=True,
            ja3_string=profile["ja3"],
            h2_settings=profile["h2"],
            supported_versions=["GREASE", "1.3", "1.2"],
            key_share_curves=["GREASE", "X25519"],
            cert_compression_algo="brotli",
            pseudo_header_order=[":method", ":authority", ":scheme", ":path"],
            connection_flow=15663105,
        )
        if proxy:
            p = f"http://{proxy}" if not proxy.startswith("http") else proxy
            sess.proxies = {"http": p, "https": p}
        return sess

    def _build_headers(self, token: str, profile: dict) -> dict:
        props_payload = {
            "os": profile["os"],
            "browser": profile["browser"],
            "device": "",
            "system_locale": "en-US",
            "browser_user_agent": profile["ua"],
            "browser_version": profile["bv"],      
            "os_version": "10",
            "referrer": "",
            "referring_domain": "",
            "referrer_current": "",
            "referring_domain_current": "",
            "release_channel": "stable",
            "client_build_number": self.BUILD_NUM,
            "client_event_source": None,
            "design_id": 0,
        }
        props = base64.b64encode(
            json.dumps(props_payload, separators=(",", ":")).encode()
        ).decode()

        headers = {
            "authority":          "discord.com",
            "accept":             "*/*",
            "accept-encoding":    "gzip, deflate, br",
            "accept-language":    "en-US,en;q=0.9",
            "authorization":      token,
            "content-type":       "application/json",
            "origin":             "https://discord.com",
            "referer":            "https://discord.com/channels/@me",
            "sec-ch-ua-platform": f'"{profile["os"]}"',
            "sec-fetch-dest":     "empty",
            "sec-fetch-mode":     "cors",
            "sec-fetch-site":     "same-origin",
            "user-agent":         profile["ua"],
            "x-debug-options":    "bugReporterEnabled",
            "x-discord-locale":   "en-US",
            "x-super-properties": props,
        }

        if profile["sec_ch_ua"]:
            headers["sec-ch-ua"]        = profile["sec_ch_ua"]
            headers["sec-ch-ua-mobile"] = "?0"

        return headers

    def _get_boost_slots(self, session, headers) -> int:
        try:
            r = session.get(
                f"{self.BASE_URL}/users/@me/guilds/premium/subscription-slots",
                headers=headers,
            )
            if r.status_code == 200:
                slots = r.json()
                return len([s for s in slots if not s.get("cancelled")])
        except Exception:
            pass
        return 0
    def check_token(self, token: str, proxy: str | None = None, retries: int = 2) -> dict:
        profile = random.choice(self.PROFILES)
        session = self._make_session(profile, proxy)
        headers = self._build_headers(token, profile)

        cf_cookies = self.cf.warm_session(session, headers)
        if cf_cookies:
            headers = CFClearance.inject_cookies(headers, cf_cookies)
            self.logger.info("CF clearance obtained", list(cf_cookies.keys()))

        for attempt in range(retries + 1):
            try:
                session.get(f"{self.BASE_URL}/experiments", headers=headers)
                res = session.get(f"{self.BASE_URL}/users/@me", headers=headers)
                if res.status_code == 429:
                    retry_after = res.headers.get("Retry-After", "?")
                    self.logger.warn("Rate limited", f"retry_after={retry_after}s")
                    return {"valid": False, "rate_limited": True}
                if res.status_code == 403:
                    if attempt < retries:
                        self.logger.warn("403 on @me — re-fetching CF", token[:20])
                        cf_cookies = self.cf.warm_session(session, headers)
                        headers    = CFClearance.inject_cookies(headers, cf_cookies)
                        time.sleep(1)
                        continue
                    return {"valid": False}

                if res.status_code != 200:
                    return {"valid": False}

                user_data = res.json()
                nitro_days, has_nitro = 0, False
                sub_res = session.get(
                    f"{self.BASE_URL}/users/@me/billing/subscriptions",
                    headers=headers,
                )
                if sub_res.status_code == 200:
                    subs = sub_res.json()
                    has_nitro = len(subs) > 0
                    for sub in subs:
                        end_str = sub.get("current_period_end")
# this if block worked first try and that scares me
                        if end_str:
                            end_dt     = datetime.fromisoformat(end_str.replace("Z", "+00:00"))
                            nitro_days = max(
                                0,
                                (end_dt - datetime.now(timezone.utc)).days,
                            )
                boost_slots = self._get_boost_slots(session, headers)
                report = {
                    "valid":       True,
                    "user_id":     user_data.get("id"),
                    "username":    user_data.get("username"),
                    "email":       user_data.get("email"),
                    "phone":       user_data.get("phone"),
                    "nitro":       has_nitro,
                    "nitro_days":  nitro_days,
                    "boost_slots": boost_slots,
                }
                self.logger.account_info(report)
                return report

            except Exception as exc:
                if attempt < retries:
                    time.sleep(0.5 * (attempt + 1))
                    continue
                self.logger.error("Exception during check", str(exc)[:60])
                return {"valid": False}

        return {"valid": False}


def worker(token: str, proxy, checker: DiscordTokenChecker,
           file_handler: FileHandler, logger: Logger, save_choice: bool):
    result = checker.check_token(token, proxy)
    if result.get("rate_limited"):
        logger.error("Rate limited", token[:20] + "...")
        stats.bump("rate_limited")
        return
    if result.get("valid"):
        stats.bump("valid")
    else:
        stats.bump("locked")
    if save_choice:
        file_handler.save_token(token, result)

if __name__ == "__main__":
    os.system("cls" if os.name == "nt" else "clear")
    set_terminal_size(124, 30)
    logger       = Logger()
    file_handler = FileHandler()
    checker      = DiscordTokenChecker(logger)
    for folder in ["input", "output"]:
        os.makedirs(folder, exist_ok=True)
    for fname in ["tokens.txt", "proxies.txt"]:
        path = f"input/{fname}"
        if not os.path.exists(path):
            open(path, "w").close()

    with open("input/tokens.txt",  "r") as f:
        tokens  = [l.strip() for l in f if l.strip()]
    with open("input/proxies.txt", "r") as f:
        proxies = [l.strip() for l in f if l.strip()]

    if not tokens:
        logger.error("No tokens found", "Add them to input/tokens.txt")
        sys.exit(1)

    logger.info(f"Loaded {len(tokens)} tokens, {len(proxies)} proxies")

    try:
        t_input      = logger.input("Threads (default 3)")
        thread_count = int(t_input) if t_input.isdigit() else 3
    except Exception:
        thread_count = 3

    save_choice = logger.confirm("Save results to output?")

    with ThreadPoolExecutor(max_workers=thread_count) as pool:
        for i, token in enumerate(tokens):
            proxy = proxies[i % len(proxies)] if proxies else None
            pool.submit(worker, token, proxy, checker, file_handler, logger, save_choice)

    logger.info(
        "Done",
        f"Valid={stats.valid} | Locked={stats.locked} | "
        f"RateLimited={stats.rate_limited} | Errors={stats.errors}",
    )
    input(f"\n      {logger.brand()} Press Enter to exit...")