import requests, re, os, argparse, yaml
from http.cookiejar import MozillaCookieJar
from bs4 import BeautifulSoup
from itertools import chain
from functions import print_status as ps


class Poipiku:
    base_url = "https://poipiku.com"
    follow_url = f"{base_url}/f/FollowListF.jsp"
    profile_url = f"{base_url}/IllustListPcV.jsp"
    append_url = f"{base_url}/f/ShowAppendFileF.jsp"
    illust_url = f"{base_url}/f/ShowIllustDetailF.jsp"

    def __init__(self, cookies, directory, quiet):
        try:
            if cookies is not None:
                cj = MozillaCookieJar(cookies)
                cj.load(ignore_discard=True, ignore_expires=True)
                self.cookies = cj
        except Exception as e:
            print(e)

        self.headers = {
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "X-Requested-With": "XMLHttpRequest",
            "Origin": self.base_url
        }

        if directory is not None:
            if not directory.endswith("/"):
                self.path = f"{directory}/poipiku/"
            else:
                self.path = directory
        else:
            self.path = f"{os.getcwd()}/poipiku/"

        self.quiet = quiet

    def get_quiet_follows(self):
        p = ps.print_status(text="No URL specified. Fetching quiet follows", status="wait") if self.quiet == False else None
        users = []
        count = 0
        data = {
            "MD": "0", 
            "MAX": "30"
        }

        try:
            while True:
                """
                Poipiku returns max 30 users no matter what, so
                we need to loop over all follow-pages until no
                result is returned, indicating a complete list
                """
                data["PG"] = str(count)
                resp = requests.post(url=self.follow_url, headers=self.headers, cookies=self.cookies, data=data)

                if resp.text.strip(): # Strip away whitespace and empty lines, then check if there is any text
                    count += 1
                    soup = BeautifulSoup(resp.text, "html.parser")
                    for a in soup.find_all("a", href=True):
                        users.append(f"{self.base_url}{a['href']}")
                else:
                    break

            p.last(text="Fetched quiet follows", status="ok") if self.quiet == False else None
        except Exception as e:
            p.last(text="Could not fetch quiet follows", status="failed") if self.quiet == False else None
            print(e)

        return users

    def create_user_directory(self):
        p = ps.print_status(text=f"Creating directory for profile ID {self.profile_id}", status="wait") if self.quiet == False else None

        self.outdir = f"{self.path}{self.profile_id}"

        try:
            if not os.path.exists(self.outdir):
                os.makedirs(self.outdir)
                p.last(text=f"Created directry for profile ID {self.profile_id}", status="ok") if self.quiet == False else None
            else:
                p.last(text=f"Directory for profile ID {self.profile_id} already exists", status="ok") if self.quiet == False else None
        except Exception as e:
            p.last(text="Could not create directory", status="failed") if self.quiet == False else None
            print(e)

    def return_user_illustration_pages(self):
        count = 0
        illustration_pages = []
        data = {
            "ID": self.profile_id, 
            "KWD": ""
        }

        try:
            p = ps.print_status(text=f"Fetching posts for profile ID {self.profile_id} (page {count + 1})", status="wait") if self.quiet == False else None
            
            while True:
                data["PG"] = str(count)
                resp = requests.post(url=self.profile_url, headers=self.headers, cookies=self.cookies, data=data)

                soup = BeautifulSoup(resp.text, "html.parser")
                pages = soup.find_all("a", class_="IllustInfo")

                if pages:
                    p.update(text=f"Fetching posts for profile ID {self.profile_id} (page {count + 1})", status="wait") if self.quiet == False else None
                    count += 1
                    for page in pages:
                        illustration_pages.append(f"{self.base_url}{page['href']}")
                else:
                    break
            p.last(text=f"Fetched posts for profile ID {self.profile_id} (page {count})", status="ok") if self.quiet == False else None
        except Exception as e:
            p.last(text=f"Could not fetch posts for profile ID {self.profile_id}", status="failed") if self.quiet == False else None
            print(e)

        return illustration_pages   

    def return_illustrations(self, illust_id):
        headers = self.headers
        headers["Referer"] = f"{self.base_url}/{self.profile_id}/{illust_id}.html"
        pattern = r"src=\"(.*?)\""
        illustrations = []

        a_count = 0
        p_count = len(self.passwords) - 1

        # Loop through all provided passwords until post is loaded
        while a_count <= p_count:
            data = {
                "ID": self.profile_id,
                "TD": illust_id,
                "AD": "-1",
                "PAS": self.passwords[a_count]
            }

            try:
                p = ps.print_status(text=f"Fetching illustrations from post ID {illust_id} (post {self.illust_pages_counter} of {self.illust_pages_total})", status="wait") if self.quiet == False else None
                resp = requests.post(self.illust_url, headers=headers, cookies=self.cookies, data=data).json()
                images = re.findall(pattern, resp["html"])[::-1]

                if not images:
                    data = {
                        "UID": self.profile_id,
                        "IID": illust_id,
                        "MD": "0",
                        "TWF": "-1",
                        "PAS": self.passwords[a_count]
                    }

                    # Need to make a different request to get the error message
                    resp = requests.post(url=self.append_url, headers=headers, cookies=self.cookies, data=data).json()
                    message = resp["html"].split("<br/>")[0].split("<br>")[0]

                    if "Password is incorrect" in message:
                        if a_count >= p_count:
                            p.last(text=f"Failed to get illustrations for post ID {illust_id}. Reason: {message}", status="failed") if self.quiet == False else None
                            break
                        else:
                            a_count += 1
                            continue
                    else:
                        if "IllustItemThumbText" in message:
                            p.last(text=f"Failed to get illustrations for post ID {illust_id}. Reason: Post only includes text.", status="failed") if self.quiet == False else None
                        else:
                            p.last(text=f"Failed to get illustrations for post ID {illust_id}. Reason: {message}", status="failed") if self.quiet == False else None
                        
                        break
                else:
                    for image in images:
                        illustrations.append("https:{}".format(image))

                    # Update the current console line with the number of posts that have been fetched
                    # Values are set in download_user_profile-function
                    if self.illust_pages_counter == self.illust_pages_total:
                        p.last(text=f"Fetched illustrations from post ID {illust_id} (post {self.illust_pages_counter} of {self.illust_pages_total})", status="ok") if self.quiet == False else None
                    else:
                        p.last(text=f"\033[1A", status="ok") if self.quiet == False else None

                    break

            except Exception as e:
                p.last(text=f"Could not fetch illustrations from post ID {illust_id} (post {self.illust_pages_counter} of {self.illust_pages_total})", status="failed") if self.quiet == False else None
                print(e)
                break

        return illustrations

    def save_illustration(self, illust_id, url):
        pattern = r".*\/(.*)"
        filename = re.search(pattern, url).group(1)
        imgpath = f"{self.outdir}/{filename}"

        try:
            p = ps.print_status(text=f"Downloading {filename}", status="wait") if self.quiet == False else None

            if os.path.exists(imgpath):
                p.last(text=f"{filename} already exists", status="ok") if self.quiet == False else None
                return
            else:
                headers = self.headers
                headers["Referer"] = f"{self.base_url}/{self.profile_id}/{illust_id}.html"
                resp = requests.get(url=url, headers=headers, cookies=self.cookies, stream=True)

                if resp.status_code == 200:
                    with open(f"{imgpath}.tmp", "wb") as file:
                        for chunk in resp:
                            file.write(chunk)
                    os.rename(f"{imgpath}.tmp", imgpath)
                    p.last(text=f"{filename} downloaded successfully", status="ok") if self.quiet == False else None
        except Exception as e:
            p.last(text=f"Could not download {filename}", status="failed") if self.quiet == False else None
            print(e)

    def download_user_profile(self, url, passwords):
        pattern = r"\/([0-9]+)"
        self.passwords = passwords
        self.profile_id = re.search(pattern, url).group(1)
        self.create_user_directory()
        urls = []

        illust_pages = self.return_user_illustration_pages()
        self.illust_pages_total = len(illust_pages)
        self.illust_pages_counter = 1

        pattern = r"\/([0-9]+)\.html"
        for page in illust_pages:
            illust_id = re.search(pattern, page).group(1)
            urls.append(self.return_illustrations(illust_id))
            self.illust_pages_counter += 1

        urls = list(chain.from_iterable(urls[::-1]))
        for url in urls:
            self.save_illustration(illust_id, url)

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("-u", dest="url", type=str, required=False, help="url to profile")
    p.add_argument("-q", dest="quiet", action="store_true", required=False, help="disable output")
    args = p.parse_args()

    return args

def main():
    args = parse_args()

    passwords = ["yes"]

    yamlfile = f"{os.path.dirname(os.path.realpath(__file__))}/config.yml"
    with open(yamlfile, "r") as cfgfile:
        config = yaml.safe_load(cfgfile)
        
    if "passwords" in config is not None:
        passwords.append([str(s).strip() for s in config["passwords"]])

    if "cookies" in config is not None:
        cookies = config["cookies"]
    else:
        cookies = None

    if "directory" in config is not None:
        directory = config["directory"]
    else:
        directory = None


    poipiku = Poipiku(cookies, directory, args.quiet)

    # If a URL is supplied, only fetch that profile
    if args.url is not None:
        users = [args.url]
    else:
        users = poipiku.get_quiet_follows()

    for user in users:
        poipiku.download_user_profile(user, passwords=passwords)


if __name__ == "__main__":
    main()
