#!/usr/bin/env python3
# pylint: disable=anomalous-backslash-in-string

import pydebug
import sys
import svgwrite
import json
import math
from hurry.filesize import size

debug = pydebug.debug("svg")

status_map = {
    "+": "finished",
    "?": "non-tried",
    "*": "non-trimmed",
    "/": "non-scraped",
    "-": "bad sector",
}

fill_map = {
    "+": "green",
    "?": "lightgray",
    "*": "darkgray",
    "/": "yellow",
    "-": "red",
}

CSS_STYLES = """
    .func_g:hover { stroke:black; stroke-width:0.5; cursor:pointer; }
"""

JAVASCRIPT = """
    function init() {
        infoBox1 = document.getElementById('infoBox1').firstChild;
        infoBox2 = document.getElementById('infoBox2').firstChild;
        infoBox3 = document.getElementById('infoBox3').firstChild;
        infoBox4 = document.getElementById('infoBox4').firstChild;
    }

    status_map = {
        "+": "finished",
        "?": "non-tried",
        "*": "non-trimmed",
        "/": "non-scraped",
        "-": "bad sector",
    }

    function bytesToSize(bytes) {
        var sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
        if (bytes == 0) return '0 Byte';
        var i = parseInt(Math.floor(Math.log(bytes) / Math.log(1024)));
        return Math.round(bytes / Math.pow(1024, i), 2) + ' ' + sizes[i];
    }

    function commaSeparateNumber(val){
        while (/(\d+)(\d{3})/.test(val.toString())){
            val = val.toString().replace(/(\d+)(\d{3})/, '$1'+','+'$2');
        }
        return val;
    }

    function s(num, pos, size, status) {
        infoBox1.nodeValue = 'Position: ' + commaSeparateNumber(pos) + " (" + bytesToSize(pos) + ") #" + num;
        end = pos + size - 1;
        infoBox2.nodeValue = 'Ending: ' + commaSeparateNumber(end) + " (" + bytesToSize(end) + ")";
        infoBox3.nodeValue = 'Size: ' + commaSeparateNumber(size) + " (" + bytesToSize(size) + ")";
        infoBox4.nodeValue = 'Status: ' + status_map[status];
    }

    function c(info) {
        infoBox1.nodeValue = 'Hover for more info';
        infoBox2.nodeValue = '';
        infoBox3.nodeValue = '';
        infoBox4.nodeValue = '';
    }
"""

GRAPH_HEIGHT = 80

def parse_file(filename):
    f = "parse_file()"
    debug(f, filename)

    fp = open(filename, "r")
    is_header = True
    ret = {
        "slices": [],
        "totals": {},
        "log": [],
        "current_pos_dec": 0,
        "current_status": 0,
        "current_pass": 0,
    }

    for line in fp:
        # Skip comment lines
        if line[0] == "#":
            continue

        parts = line.split()

        # Status header
        if is_header:
            ret["current_pos_dec"] = int(parts[0], base=0)
            ret["current_status"] = parts[1]
            ret["current_pass"] = parts[2]
            is_header = False
            continue

        row_pos = parts[0]
        row_size = parts[1]
        row_status = parts[2]

        row = {
            # "pos_hex": row_pos,
            "pos_dec": int(row_pos, base=0),
            # "size_hex": row_size,
            "size_dec": int(row_size, base=0),
            "status": row_status,
        }
        row["end_dec"] = row["pos_dec"] + row["size_dec"] - 1

        # Skip if size is unreasonably large, the scan likely didn't know the size of the source
        if row["size_dec"] > 1_000_000_000_000:
            continue

        ret["slices"].append(row)
        if row_status not in ret["totals"]:
            ret["totals"][row_status] = 0
        ret["totals"][row_status] += int(row_size, base=0)

        ret["log"].append("%s" % (line.strip()))

        # debug(f, row_start, row_end, row_status, status_map[row_status])

    fp.close()
    debug(f, ret["totals"])
    return ret

# Slice graph
def draw_slice_graph(dwg, rows, y, denom):
    f = "draw_slice_graph()"
    debug(f)

    # Everything goes into a group
    group = dwg.g(id="slice_graph", font_size=14)

    # Start on the left
    xp = 0

    # Index used for looking up info about the slice
    i = 0

    for row in rows["slices"]:
        # debug(f, row)

        # TEMPORARY
        # if i > 100:
        #     continue

        # JavaScript mouse events
        mouseover = "s(%s, %s, %s, '%s')" % (i, row["pos_dec"], row["size_dec"], row["status"])
        g = dwg.g(
            onmouseover=mouseover,
            # onmouseout="c()"
        )

        # Graph block starting and width percentages
        xp = 100 * row["pos_dec"] / denom
        wp = 100 * row["size_dec"] / denom
        g.add(dwg.rect(
            insert=("%s%%" % xp, y),
            size=("%s%%" % wp, GRAPH_HEIGHT),
            fill=fill_map[row["status"]],
        ))

        # If wider than X%, also add a text label
        if wp > 2:
            # Just fudge the x percent for text
            xpt = "%s%%" % (0.2 + xp)
            text_val = "%2.2f%%" % wp
            g.add(dwg.text(text_val, (xpt, y + 15)))
            text_val = size(int(row["pos_dec"]))
            g.add(dwg.text(text_val, (xpt, y + 35)))
            text_val = size(int(row["size_dec"]))
            g.add(dwg.text(text_val, (xpt, y + 55)))

        # Add the group
        group.add(g)
        debug(xp, y, wp, GRAPH_HEIGHT)
        xp += wp
        i += 1

    dwg.add(group)

def draw_total_graph(dwg, rows, y, denom):
    f = "draw_total_graph()"
    debug(f)

    # Everything goes into a group
    group = dwg.g(id="total_graph", font_size=14)

    # Start on the left
    xp = 0

    for status in status_map:
        if status not in rows["totals"]:
            continue
        # print("value:", rows["totals"][status])
        wp = 100 * rows["totals"][status] / denom
        # print(status, wp, rows["totals"][status], xp)
        fill = fill_map[status]
        group.add(dwg.rect(
            insert=("%s%%" % xp, y),
            size=("%s%%" % wp, GRAPH_HEIGHT),
            fill=fill,
        ))
        # If wider than X%, also add a text label
        if wp > 2:
            # Just fudge the x percent for text
            xpt = "%s%%" % (0.2 + xp)
            text_val = "%s (%s)" % (status_map[status], status)
            group.add(dwg.text(text_val, (xpt, y + 15)))
            text_val = "%2.2f%%" % wp
            group.add(dwg.text(text_val, (xpt, y + 35)))
            text_val = size(rows["totals"][status])
            group.add(dwg.text(text_val, (xpt, y + 55)))

        xp += wp

    dwg.add(group)

def draw_info_fields(dwg, rows, y, denom):
    # Everything goes into a group
    group = dwg.g(id="info_fields")

    group.add(dwg.text("Hover for more info", (10, y + 15), id="infoBox1"))
    group.add(dwg.text(" ", (10, y + 35), id="infoBox2"))
    group.add(dwg.text(" ", (10, y + 55), id="infoBox3"))
    group.add(dwg.text(" ", (10, y + 75), id="infoBox4"))

    # group.add(dwg.text(" ", (10, y + 95), id="logBox1"))
    # group.add(dwg.text(" ", (10, y + 115), id="logBox2"))
    # group.add(dwg.text(" ", (10, y + 135), id="logBox3"))
    # group.add(dwg.text(" ", (10, y + 155), id="logBox4"))
    # group.add(dwg.text(" ", (10, y + 175), id="logBox5"))

    # GRAPH_HEIGHT = GRAPH_HEIGHT * 2 + 90 + 25
    # for line in rows["log"]:
    #     debug(row)
    #     dwg.add(dwg.text(line, (10, GRAPH_HEIGHT)))
    #     GRAPH_HEIGHT += 20

    dwg.add(group)

def draw_current_marker(dwg, rows, y, denom):
    f = "draw_current_marker()"
    debug(f)

    # Everything goes into a group
    group = dwg.g(id="current_marker", stroke="black")

    # Percent of graph
    current_percent = 100 * rows["current_pos_dec"] / denom

    # Draw triangle
    point_1 = ("%2.2f%%" % (current_percent), y)
    point_2 = ("%2.2f%%" % (current_percent + .3), y + 10)
    point_3 = ("%2.2f%%" % (current_percent - .3), y + 10)
    group.add(dwg.line(start=point_1, end=point_2))
    group.add(dwg.line(start=point_2, end=point_3))
    group.add(dwg.line(start=point_3, end=point_1))
    dwg.add(group)

def main():
    f = "main()"
    debug(f)

    # Read mapfile file name
    if len(sys.argv) < 2:
        print("Usage: %s map-file.txt" % sys.argv[0])
        sys.exit(1)

    rows = parse_file(sys.argv[1])

    dwg = svgwrite.Drawing(
        'test.svg',
        profile='full',
        onload="init()"
    )

    # Add CSS and JS data to SVG
    MAPDATA_JS = "var logData=%s" % json.dumps(rows["log"], indent = 2)
    dwg.defs.add(dwg.style(content=CSS_STYLES))
    dwg.defs.add(dwg.script(content=JAVASCRIPT))
    dwg.defs.add(dwg.script(content=MAPDATA_JS))

    # Get max value for use in percentage denominator
    denom = rows["slices"][-1]["end_dec"]
    debug("%s denom: %s" % (f, denom))

    # Initial height start point
    y = 10

    draw_slice_graph(dwg=dwg, rows=rows, y=y, denom=denom)
    y += GRAPH_HEIGHT

    draw_current_marker(dwg=dwg, rows=rows, y=y, denom=denom)
    y += 20

    draw_total_graph(dwg=dwg, rows=rows, y=y, denom=denom)
    y += GRAPH_HEIGHT + 10

    draw_info_fields(dwg=dwg, rows=rows, y=y, denom=denom)

    dwg.save(pretty=True)


if __name__ == "__main__":
    main()
