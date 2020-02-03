# ddrescue-to-svg
Convert a ddrescue mapfile into a human-readable SVG.

Taken from [GNU ddrescue](https://www.gnu.org/software/ddrescue/) site:
> [GNU ddrescue](https://www.gnu.org/software/ddrescue/) is a data recovery tool. It copies data from one file or block device (hard disc, cdrom, etc) to another, trying to rescue the good parts first in case of read errors.
>
> If you use the mapfile feature of ddrescue, the data are rescued very efficiently, (only the needed blocks are read). Also you can interrupt the rescue at any time and resume it later at the same point. The mapfile is an essential part of ddrescue's effectiveness. Use it unless you know what you are doing.

Being able to pause/resume/skip around in the recovery process is incredibly powerful, I think it one of the best tools for recovering data from damaged media. It works similar to [dd](https://en.wikipedia.org/wiki/Dd_%28Unix%29), but data recovery targeted, and somewhat automated. While viewing the ddrescue output and mapfile is helpful, I still wanted something more visual to get a better picture of the state of the media and recovery process. Hence, this script.

### Usage:

```
python3 ddrescue-svg.py my-map-file.txt [optional-output-filename.svg]
```

### Example output:

![screenshot](screenshot.png)
