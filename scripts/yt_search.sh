#!/bin/bash
# usage: yt_search.sh "<tag>" "<query>" [n]
n=${3:-6}
timeout 120 yt-dlp --no-warnings --flat-playlist "ytsearch$n:$2" --print "$1	%(id)s	%(duration)s	%(channel)s	%(title)s" 2>/dev/null
