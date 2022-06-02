"""
Pull all of the links/attachments from posts for a particular kemono/coomer party user.

Keep note, that the links pulled from the posts, especially with link discovery on, will most likely require post processing on your own part. Unfortunately, due to the random nature of the different services people use and formatting, sometimes errant text makes its way into links (which may end up doubling the links).
"""


import argparse
import re
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from lxml import html

PARTY_REGEX = re.compile(
    r"(?:beta\.)?(?P<party>coomer|kemono)\.party\/(?P<service>.*)\/user\/(?P<user>.*)$",
    re.IGNORECASE | re.DOTALL,
)
LINK_REGEX = re.compile(r"(?P<url>https?://[^\s]+)")


def main(args):

    links = args.LINKS
    aria_format = args.aria2_format
    link_discovery = args.link_discovery
    start_page = args.start_page * 25
    end_page = args.end_page
    if end_page is not None:
        end_page = args.end_page * 25
        if start_page > end_page:
            raise SystemExit("Start page is beyond end page!")

    def get_title(service, party, user):
        title = html.fromstring(
            requests.get(f"https://{party}.party/{service}/user/{user}").content
        ).xpath("//title/text()")[0]
        return re.findall(r"^Posts of (.*) from .*$", title, re.IGNORECASE | re.DOTALL)[
            0
        ]

    def get_links(contents):
        if contents.strip():
            # Sometimes we get lucky and can just get all of the links easily via xpath since it's HTML
            # Other times we can't, and it's plain text which is obnoxious
            links = set(html.fromstring(contents).xpath("//a/@href"))
            clean_contents = BeautifulSoup(contents.strip(), "lxml").text
            links.update(LINK_REGEX.findall(clean_contents.strip()))
            return list(links)
        return []

    for link in links:

        party, service, user = PARTY_REGEX.search(link).groups()
        prefix = f"[{party}, {service}, {user}]"
        print(f"{prefix} Pulling pages ...")

        title = get_title(service, party, user).replace(" ", "_").strip()
        output_prefix = f"{title}_{user}_{service}"
        total_links = 0
        total_attachments = 0

        o = start_page
        current_page = 1
        done = False
        while not done:
            lep = f"{(end_page // 25) + 1}" if end_page is not None else "?"
            lprefix = f"{prefix} [{current_page}/{lep}]"
            print(f"{lprefix} Fetching page {current_page} ...")
            posts = requests.get(
                f"https://{party}.party/api/{service}/user/{user}", params={"o": o}
            ).json()

            # Reached end
            if not posts:
                done = True
                continue

            # Check if reached page limit
            if end_page is not None:
                if o >= end_page:
                    print(f"{lprefix} Reached end page!")
                    done = True

            o += 25

            post_links = []
            attachments = []
            d_count = 0
            c_count = 0
            for post in posts:

                # Collect links from text content, usually links to mega, etc
                if link_discovery:
                    contents_links = get_links(post["content"])
                    c_count += len(contents_links)
                    post_links.extend(contents_links)

                # Collect attachments, depending on format will be dumped differently
                if post["attachments"]:
                    if aria_format:
                        for attachment in post["attachments"]:
                            name, path = attachment["name"], attachment["path"]
                            attachments.append(
                                f"https://{party}.party{path}\n out={name}"
                            )
                    else:
                        for attachment in post["attachments"]:
                            name, path = attachment["name"], attachment["path"]
                            attachments.append(f"https://{party}.party{path}")

                # Check links if applicable
                if link_discovery:

                    for attachment in post["attachments"]:

                        d_link = None
                        name = attachment["name"]
                        parsed = urlparse(name)
                        parsed_name = parsed.path.lstrip("/")

                        if parsed.scheme:
                            # Imgur specific, fbplay = indicates video thumbnail, fb is thumbnail image
                            if "fbplay" in parsed.query:
                                d_link = (
                                    parsed.scheme
                                    + "://"
                                    + parsed.netloc
                                    + parsed.path.split(".", 1)[:-1][0]
                                    + ".mp4"
                                )
                            else:
                                d_link = (
                                    parsed.scheme + "://" + parsed.netloc + parsed.path
                                )

                            if aria_format:
                                attachments.append(f"{d_link}\n out={parsed_name}")
                            else:
                                attachments.append(d_link)

                            d_count += 1

            print(f"{lprefix} Added an additional {d_count} link(s) from filenames ...")
            print(
                f"{lprefix} Added an additional {c_count} link(s) from post contents ..."
            )

            # Append to file(s)
            if post_links:
                total_links += len(post_links)
                with open(f"{output_prefix}_links.txt", "a") as f:
                    f.write("\n" + "\n".join(post_links))

            if attachments:
                total_attachments += len(attachments)
                with open(f"{output_prefix}_attachments.txt", "a") as f:
                    f.write("\n" + "\n".join(attachments))

            if not done:
                current_page += 1

        print(f"{prefix} Found {total_links} links")
        print(f"{prefix} Found {total_attachments} attachments")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("LINKS", nargs="+")
    parser.add_argument(
        "-a",
        "--aria2-format",
        default=False,
        action="store_true",
        help="store attachment links with filename in the format required for aria2, otherwise just dumps links as is",
    )
    parser.add_argument(
        "-l",
        "--link-discovery",
        default=False,
        action="store_true",
        help="add links born from attachment filename(s) and post contents",
    )
    parser.add_argument("-s", "--start-page", default=0, type=int, help="start page")
    parser.add_argument("-e", "--end-page", default=None, type=int, help="end page")
    args = parser.parse_args()
    main(args)
