# kemono-party-scripts

Varying scripts for pulling from kemono.party. Fortunately kemono.party _does_ have an API, so these scripts are a bit of shorthand for pulling contents.

## notes

Requires Python 3.10.x+, be sure to install the contents in requirements.txt.

* Be aware, there's nothing for tackling the DDoS protection.
* There's some naive assumptions made for accounting for Imgur links which have `?fb` or `?fbplay` parameter to build links.
* Just like bdsmlr-scripts, this dumps aria2 compatible contents (optionally with filenames specified with the `--aria2-format` arg).
* The expectation is to just provide a list of links to varying kemono.party users/services (beta not accounted for, but it'd be trivial to account for it if you want).
* It is _heavily_ advisable that you run something like fdupes to remove duplicates after downloading the attachments. There's a ton of them unfortunately.
