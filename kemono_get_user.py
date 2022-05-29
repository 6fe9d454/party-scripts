import argparse
import re
from urllib.parse import urlparse

import requests
from lxml import html


def main(args):

    links = args.LINKS
    aria_format = args.aria2_format
    link_conversion = args.link_conversion
    start_page = args.start_page * 25
    end_page = args.end_page
    if end_page is not None:
        end_page = args.end_page * 25
        if start_page > end_page:
            raise SystemExit("Start page is beyond end page!")

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
                f"https://kemono.party/api/{service}/user/{user}", params={"o": o}
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
            for post in posts:

                # Collect links from text content, usually links to mega, etc
                post_links.extend(get_hrefs(post["content"]))

                # Collect attachments, depending on format will be dumped differently
                if post["attachments"]:
                    if aria_format:
                        for attachment in post["attachments"]:
                            name, path = attachment["name"], attachment["path"]
                            attachments.append(
                                f"https://kemono.party{path}\n out={name}"
                            )
                    else:
                        for attachment in post["attachments"]:
                            attachments.append(f"https://kemono.party{path}")

                # Check links if applicable
                if link_conversion:

                    d_link = None

                    for attachment in post["attachments"]:

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
    parser = argparse.ArgumentParser()
    parser.add_argument("LINKS", nargs="+")
    parser.add_argument(
        "--aria2-format",
        default=False,
        action="store_true",
        help="store attachment links with filename in the format required for aria2, otherwise just dumps links as is",
    )
    parser.add_argument(
        "--link-conversion",
        default=False,
        action="store_true",
        help="optionally add links born from file name; sometimes the filename is the true, full size image or video (with the link in the attachments being a preview image or thumbnail), may or may not work, assumings videos from imgur are mp4",
    )
    parser.add_argument("-s", "--start-page", default=0, type=int, help="start page")
    parser.add_argument("-e", "--end-page", default=None, type=int, help="end page")
    args = parser.parse_args()
    main(args)
