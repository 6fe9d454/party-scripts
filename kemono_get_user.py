import requests
import argparse
import re
from lxml import html


def main(args):

    links = args.LINKS
    aria_format = args.aria2_format
    start_page = args.start_page * 25
    if args.end_page:
        end_page = args.end_page * 25
        if start_page > end_page:
            raise SystemExit("Start page is beyond end page!")
    else:
        end_page = None

    def get_title(link):
        title = html.fromstring(requests.get(link).content).xpath("//title/text()")[0]
        return re.findall(r"^Posts of (.*) from .*$", title, re.IGNORECASE | re.DOTALL)[
            0
        ]

    def get_hrefs(contents):
        if contents.strip():
            return html.fromstring(contents).xpath("//a/@href")
        return []

    for link in links:

        service, _, user = (
            link.replace("https://kemono.party/", "")
            .replace("http://kemono.party/", "")
            .split("/")
        )
        prefix = f"[{service}, {user}]"
        print(f"{prefix} Pulling pages ...")

        title = get_title(link).replace(" ", "_").strip()
        output_prefix = f"{title}_{user}_{service}"

        o = start_page
        current_page = 0
        done = False
        while not done:
            lep = f"{end_page // 25}" if end_page else "?"
            lprefix = f"{prefix} [{current_page}/{lep}]"
            print(f"{lprefix} Fetching page {current_page}")
            posts = requests.get(
                f"https://kemono.party/api/{service}/user/{user}", params={"o": o}
            ).json()

            # Reached end
            if not posts:
                done = True
                continue

            # Check if reached page limit
            if end_page:
                if o >= end_page:
                    print(f"{prefix} Reached end page!")
                    done = True
                    continue

            o += 25

            post_links = []
            attachments = []
            for post in posts:

                # Collect links from text content, usually links to mega, etc
                post_links.extend(get_hrefs(post["content"]))

                # Collect attachments, depending on format will be dumped differently
                if post["attachments"]:
                    if aria_format:
                        for attachment in post["attachments"]:
                            name, path = attachment["name"], attachment["path"]
                            attachments.append(
                                f'https://kemono.party{path}\n out="{name}"'
                            )
                    else:
                        for attachment in post["attachments"]:
                            attachments.append(f"https://kemono.party{path}")

            # Append to file(s)
            if post_links:
                with open(f"{output_prefix}_links.txt", "a") as f:
                    f.write("\n" + "\n".join(post_links))

            if attachments:
                with open(f"{output_prefix}_attachments.txt", "a") as f:
                    f.write("\n" + "\n".join(attachments))

            if not done:
                current_page += 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("LINKS", nargs="+")
    parser.add_argument(
        "--aria2-format",
        default=False,
        action="store_true",
        help="store attachment links with filename in the format required for aria2, otherwise just dumps links as is",
    )
    parser.add_argument("-s", "--start-page", default=0, type=int, help="start page")
    parser.add_argument("-e", "--end-page", default=None, type=int, help="end page")
    args = parser.parse_args()
    main(args)
