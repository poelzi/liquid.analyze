#!/usr/bin/env python
import gzip
import optparse
import sys
import collections
import random
import os

#import sqlparse
#from sqlparse import engine
#from sqlparse import filters
#from sqlparse import formatter

# make names apear the same on each data set
random.seed(23)

AREAS = {
    "6":  ["UmVeEn", "Umwelt, Verkehr, Energie"],
    "9":  ["Satzung", "Satzung und Parteistruktur"],
    "3":  ["WiSo", "Wirtschaft, Soziales"],
    "11": ["SoAn", "Sonstige innerparteiliche Angelegenheiten"],
    "7":  ["Int", "Sonstige innerparteiliche Angelegenheiten"],
    "5":  ["Gsnd", "Gesundheit und Drogen/Suchtpolitik"],
    "12": ["Sand", "Sandkasten/Spielwiese"],
    "2":  ["Innen", "Innen, Recht, Demokratie, Sicherheit"],
    "1":  ["DigiPat", "Digitales, Urheber-/Patentrecht, Datenschutz"],
    "13": ["Streit", "Streitfragen zu Abstimmungen"],
    "10": ["Liquid", "LiquidFeedback Systembetrieb"],
    "4":  ["FamBild", "Kinder, Jugend, Familie und Bildung"],
    "8":  ["Sonst", "Sonstige politische Themen"]
}

NAMES = set()
NAMES_LOAD = 0

def load_names():
    global NAMES_LOAD
    ifp = gzip.GzipFile(os.path.join(os.path.dirname(__file__), "names.gz"), "r")
    NAMES_LOAD += 1
    for line in ifp:
        line = line[:-1]
        if NAMES_LOAD > 1:
            NAMES.add("%s %s" %(line, NAMES_LOAD))
        else:
            NAMES.add(line)

def anonymize(name):
    if not NAMES:
        load_names()
    name = random.sample(NAMES, 1)[0]
    NAMES.remove(name)
    return name

def main():
    usage = "usage: %prog [options] sqldump"
    parser = optparse.OptionParser(usage)
    parser.add_option("-o", "--output", dest="output", default=sys.stdout,
                      help="output .dot file")
    parser.add_option("-H", "--hide", dest="hide", choices=["issue","area","global"], action="append", default=[],
                      help="hide delegation type [issue,area,global]")
    parser.add_option("-a", "--anonymous", dest="anon", action="store_true", default=False,
                      help="anonymize names")
    parser.add_option("-s", "--style", dest="type", default="neato", choices=["neato"],
                      help="style for rendering [neato]")
    #parser.add_option("-s", "--style", dest="type", default="neato", choices=["neato"],
    #                  help="style for rendering [neato]")
    parser.add_option("--listareas", dest="listareas", default=False, action="store_true",
                      help="list all areas")
    parser.add_option("--showareas", dest="showareas", default=None,
                      help="list of area ids (1,2,3,...) to show, default is all")
    parser.add_option("--showissues", dest="showissues", default=None,
                      help="list of issue ids (1,2,3,...) to show, default is all")
    parser.add_option("--hidelegend", dest="hidelegend", default=False, action="store_true",
                      help="hide the legend in graph")



    (options, args) = parser.parse_args()

    if options.listareas:
        print "ID:\tShortcut      Fullname"
        for i,v in AREAS.iteritems():
            print "%s:\t%s%s%s" %(i,v[0]," "*(14-len(v[0])), v[1])
        sys.exit(0)

    if options.showareas:
        options.showareas = options.showareas.split(",")

    if options.showissues:
        options.showissues = options.showissues.split(",")

    if not len(args):
        parser.error("incorrect number of arguments")
    
    analyze(args[0], options.output, options)

LEGEND_AREA = "".join(["""<TR><TD><FONT POINT-SIZE="9">%s</FONT></TD><TD ALIGN="LEFT"><FONT POINT-SIZE="9">%s</FONT></TD></TR>""" %(x[0],x[1]) for x in AREAS.itervalues()])
LEGEND = """<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0">  <TR><TD><FONT POINT-SIZE="12">Legend:</FONT></TD><TD><font POINT-SIZE="12" color="#D1525C">global</font> <font POINT-SIZE="12" color="#007DD1">area</font> <font POINT-SIZE="12" color="#4CD100">issue</font></TD></TR>%s</TABLE>>"""%LEGEND_AREA

HEADER = {"neato": """
digraph graphname {
graph [bgcolor=white, outputMode="breadthfirst", overlap="orthoyx" %(legend)s];
edge [fontsize=10, fontname="famd", arrowhead="vee", arrowsize="0.5", labelangle="10"];
node [fontname="famd", style=filled,fillcolor="#ffcb05", fixedsize=false, fontsize=13, width=0.5, height=0.35, margin=0.01];
"""
}


FOOTER = """
 }
"""


def analyze(infile, output, options=None):
    ifp = gzip.GzipFile(infile, "r")
    i = 0
    mode = None
    DEL = 1
    MEM = 2
    AREA = 3

    areas = []

    data = collections.defaultdict(dict)
    i = 0
    for line in ifp:
        #print repr(line)
        #rl = line.strip()
        if line == "COPY delegation (id, truster_id, trustee_id, scope, area_id, issue_id) FROM stdin;\n":
            mode = DEL
            continue
        elif line == """COPY member (id, created, last_login, login, password, active, admin, notify_email, notify_email_unconfirmed, notify_email_secret, notify_email_secret_expiry, notify_email_lock_expiry, password_reset_secret, password_reset_secret_expiry, name, identification, organizational_unit, internal_posts, realname, birthday, address, email, xmpp_address, website, phone, mobile_phone, profession, external_memberships, external_posts, statement, text_search_data) FROM stdin;\n""":
            mode = MEM
            continue
        #elif line == """COPY area (id, active, name, description, direct_member_count, member_weight, autoreject_weight, text_search_data) FROM stdin;\n""":
        #    mode = AREA
        #    continue
        elif line == "\\.\n":
            mode = None
            continue

        if mode == DEL:
            #print "delegate", line
            ld = line.split()
            data[ld[1]][ld[2]] = ld[3:]

        if mode == MEM:
            #print "mem", line
            ld = line.split()
            #print ld
            name = []
            if ld[15] != '\\N':
                name.append(ld[15])
            if ld[16] != '\\N':
                name.append(ld[16])
            if options and options.anon:
                data[ld[0]]["name"] = anonymize(" ".join(name))
            else:
                data[ld[0]]["name"] = (" ".join(name)).replace('"', "")

    if isinstance(output, basestring):
        fp = open(output, "w")
    else:
        fp = output

    if options:
        header = HEADER[options.type]
    else:
        header = HEADER["neato"]

    if options and options.hidelegend:
        header = header %{"legend":""}
    else:
        header = header %{"legend":", label="+LEGEND}

    fp.write(header)

    # edges
    for iid, member in data.iteritems():
        linkcount = member.get("linkcount", 0)
        for target, edge in member.iteritems():
            if not isinstance(edge, (list, tuple)):
                continue

            # hide type of delegate
            if options and edge[0] in options.hide:
                continue

            if edge[0] == "issue":
                if options and options.showissues and edge[2] not in options.showissues:
                    continue
                fp.write("""%s -> %s [label="%s",  color="#4CD100", fontcolor="#276C00"];\n""" %(iid, target, edge[2]))
            elif edge[0] == "area":
                if options and options.showareas and edge[1] not in options.showareas:
                    continue
                area = AREAS.get(edge[1], edge[1])
                if isinstance(area, list):
                    area = area[0]
                fp.write("""%s -> %s [label="%s", color="#007DD1", fontcolor="#00416E"];\n""" %(iid, target, area))
            elif edge[0] == "global":
                fp.write("""%s -> %s [color="#D1525C"];\n""" %(iid, target))
            else:
                continue
            linkcount += 1
            data[target]["linkcount"] = data[target].get("linkcount", 0) + 1

        member["linkcount"] = linkcount

    # members
    for iid, item in data.iteritems():
        if item["linkcount"] > 0:
            fp.write("""%s [label="%s"];\n""" %(iid, item["name"]))

    
    fp.write(FOOTER)
        
    #for stmt in stack.run(ifp):
    #    print stmt
    #for data in sqlparse.split(ifp):
    #    print data



if __name__ == "__main__":
    main()