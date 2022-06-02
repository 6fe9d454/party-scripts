# party-scripts

Scripts for pulling from kemono.party and coomer.party. Fortunately these  _do_ have an API, so these script(s) are a bit of shorthand for pulling contents.

## notes

Requires Python 3.10.x+, be sure to install the contents in requirements.txt.

* Be aware, there's nothing for tackling the DDoS protection.
* There's some naive assumptions made for accounting for Imgur links which have `?fb` or `?fbplay` parameter to build links.
* Just like bdsmlr-scripts, this dumps aria2 compatible contents (optionally with filenames specified with the `--aria2-format` arg).
* The expectation is to just provide a list of links to varying kemono.party users/services (beta not accounted for, but it'd be trivial to account for it if you want).
* It is _heavily_ advisable that you run something like fdupes/jdupes to remove duplicates after downloading the attachments. There's a ton of them unfortunately.
* The links collected **will** require some post processing on your part because of the weird formatting differences between all of the services encountered. It should be fairly simple to edit out the weirdness, then run it through a quick `cat links.txt | sort | uniq > new_links.txt` type of deal to remedy that.
