import requests, re, os
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

    def __init__(self):
        try:
            cj = MozillaCookieJar("cookie.txt")
            cj.load(ignore_discard=True, ignore_expires=True)
            self.cookies = cj
        except Exception as e:
            print(e)

        self.headers = {
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "X-Requested-With": "XMLHttpRequest",
            "Origin": self.base_url
        }

    def get_quiet_follows(self):
        p = ps.print_status(text="Fetching quiet follows", status="wait")
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

            p.last(text="Fetched quiet follows", status="ok")
        except Exception as e:
            p.last(text="Could not fetch quiet follows", status="failed")
            print(e)

        return users

    def create_user_directory(self, path=f"{os.getcwd()}/poipiku"):
        p = ps.print_status(text=f"Creating directory for profile ID {self.profile_id}", status="wait")

        if not path.endswith("/"):
            path = f"{path}/"
        self.path = f"{path}{self.profile_id}"

        try:
            if not os.path.exists(self.path):
                os.makedirs(self.path)
                p.last(text=f"Created directry for profile ID {self.profile_id}", status="ok")
            else:
                p.last(text=f"Directory for profile ID {self.profile_id} already exists", status="ok")
        except Exception as e:
            p.last(text="Could not create directory", status="failed")
            print(e)

    def return_user_illustration_pages(self):
        count = 0
        illustration_pages = []
        data = {
            "ID": self.profile_id, 
            "KWD": ""
        }

        try:
            p = ps.print_status(text=f"Fetching posts for profile ID {self.profile_id} (page {count + 1})", status="wait")
            
            while True:
                data["PG"] = str(count)
                resp = requests.post(url=self.profile_url, headers=self.headers, cookies=self.cookies, data=data)

                soup = BeautifulSoup(resp.text, "html.parser")
                pages = soup.find_all("a", class_="IllustInfo")

                if pages:
                    p.update(text=f"Fetching posts for profile ID {self.profile_id} (page {count + 1})", status="wait")
                    count += 1
                    for page in pages:
                        illustration_pages.append(f"{self.base_url}{page['href']}")
                else:
                    break
            p.last(text=f"Fetched posts for profile ID {self.profile_id} (page {count})", status="ok")
        except Exception as e:
            p.last(text=f"Could not fetch posts for profile ID {self.profile_id}", status="failed")
            print(e)

        return illustration_pages

    # This is only a helper-function to "return_illustrations" and will only print the failure-reason to the console
    def append_illustration(self, illust_id, log):
        headers = self.headers
        headers["Referer"] = f"{self.base_url}/{self.profile_id}/{illust_id}.html"
        data = {
            "UID": self.profile_id,
            "IID": illust_id,
            "MD": "0",
            "TWF": "-1",
            "PAS": self.password
        }

        resp = requests.post(url=self.append_url, headers=headers, cookies=self.cookies, data=data).json()
        message = resp["html"].split("<br/>")[0].split("<br>")[0]
        log.last(text=f"Failed to get illustrations for post ID {illust_id}. Reason: {message}", status="failed")

    def return_illustrations(self, illust_id):
        headers = self.headers
        headers["Referer"] = f"{self.base_url}/{self.profile_id}/{illust_id}.html"
        pattern = r"src=\"(.*?)\""
        illustrations = []
        data = {
            "ID": self.profile_id,
            "TD": illust_id,
            "AD": "-1",
            "PAS": self.password
        }

        try:
            p = ps.print_status(text=f"Fetching illustrations from post ID {illust_id} (post {self.illust_pages_counter} of {self.illust_pages_total})", status="wait")
            resp = requests.post(self.illust_url, headers=headers, cookies=self.cookies, data=data).json()
            images = re.findall(pattern, resp["html"])[::-1]

            if not images:
                self.append_illustration(illust_id, p)
            else:
                for image in images:
                    illustrations.append("https:{}".format(image))

                # Update the current console line with the number of posts that have been fetched
                # Values are set in download_user_profile-function
                if self.illust_pages_counter == self.illust_pages_total:
                    p.last(text=f"Fetched illustrations from post ID {illust_id} (post {self.illust_pages_counter} of {self.illust_pages_total})", status="ok")
                else:
                    p.last(text=f"\033[1A", status="ok")
        except Exception as e:
            p.last(text=f"Could not fetch illustrations from post ID {illust_id} (post {self.illust_pages_counter} of {self.illust_pages_total})", status="failed")
            print(e)

        return illustrations

    def save_illustration(self, illust_id, url):
        pattern = r".*\/(.*)"
        filename = re.search(pattern, url).group(1)
        path = f"{self.path}/{filename}"

        try:
            p = ps.print_status(text=f"Downloading {filename}", status="wait")

            if os.path.exists(path):
                p.last(text=f"{filename} already exists", status="ok")
                return
            else:
                headers = self.headers
                headers["Referer"] = f"{self.base_url}/{self.profile_id}/{illust_id}.html"
                resp = requests.get(url=url, headers=headers, cookies=self.cookies, stream=True)

                if resp.status_code == 200:
                    with open(f"{path}.tmp", "wb") as file:
                        for chunk in resp:
                            file.write(chunk)
                    os.rename(f"{path}.tmp", path)
                    p.last(text=f"{filename} downloaded successfully", status="ok")
        except Exception as e:
            p.last(text=f"Could not download {filename}", status="failed")
            print(e)

    def download_user_profile(self, url, password="yes"):
        pattern = r"\/([0-9]+)\/"
        self.password = password
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


def main():
    poipiku = Poipiku()
    users = poipiku.get_quiet_follows()

    for user in users:
        poipiku.download_user_profile(user, password="yes")


if __name__ == "__main__":
    main()
