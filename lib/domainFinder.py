#!/usr/bin/env python3

import os
from sty import fg, bg, ef, rs, RgbFg
from python_hosts.hosts import Hosts, HostsEntry
import re
from lib import nmapParser
from subprocess import call


class DomainFinder:
    def __init__(self, target):
        self.target = target
        self.hostnames = []

    def Scan(self):
        np = nmapParser.NmapParserFunk(self.target)
        np.openPorts()
        ssl_ports = np.ssl_ports
        ignore = [
            ".nse",
            ".php",
            ".html",
            ".png",
            ".js",
            ".org",
            ".versio",
            ".com",
            ".gif",
            ".asp",
            ".aspx",
            ".jpg",
            ".jpeg",
            ".txt",
        ]
        dns = []
        with open(
            f"{self.target}-Report/nmap/tcp-scripts-{self.target}.nmap", "r"
        ) as nm:
            for line in nm:
                new = (
                    line.replace("=", " ")
                    .replace("/", " ")
                    .replace("commonName=", "")
                    .replace("/organizationName=", " ")
                )
                # print(new)
                matches = re.findall(
                    r"(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,6}",
                    new,
                )
                # print(matches)
                for x in matches:
                    if not any(s in x for s in ignore):
                        dns.append(x)
        # print(dns)
        sdns = sorted(set(dns))
        # print(sdns)
        tmpdns = []
        for x in sdns:
            tmpdns.append(x)
        ################# SSLSCAN #######################
        if len(ssl_ports) == 0:
            tmpdns2 = []
            for x in tmpdns:
                tmpdns2.append(x)

            unsortedhostnames = []
            for x in tmpdns2:
                unsortedhostnames.append(x)
            allsortedhostnames = sorted(set(tmpdns2))
            allsortedhostnameslist = []
            for x in allsortedhostnames:
                allsortedhostnameslist.append(x)
        else:
            if not os.path.exists(f"{self.target}-Report/web"):
                os.makedirs(f"{self.target}-Report/web")
            https_string_ports = ",".join(map(str, ssl_ports))
            # print(https_string_ports)
            for sslport in ssl_ports:
                sslscanCMD = f"sslscan https://{self.target}:{sslport} | tee {self.target}-Report/web/sslscan-color-{self.target}-{sslport}.log"
                green_plus = fg.li_green + "+" + fg.rs
                cmd_info = "[" + green_plus + "]"
                print(cmd_info, sslscanCMD)
                call(sslscanCMD, shell=True)
                if not os.path.exists(
                    f"{self.target}-Report/web/sslscan-color-{self.target}-{sslport}.log"
                ):
                    pass
                else:
                    sslscanFile = f"{self.target}-Report/web/sslscan-color-{self.target}-{sslport}.log"
                    # print(sslscanFile)
                    domainName = []
                    altDomainNames = []
                    with open(sslscanFile, "rt") as f:
                        for line in f:
                            if "Subject:" in line:
                                n = line.lstrip("Subject:").rstrip("\n")
                                # print(n)
                                na = n.lstrip()
                                # print(na)
                                domainName.append(na)
                            if "Altnames:" in line:
                                alnam = line.lstrip("Altnames:").rstrip("\n")
                                alname = alnam.lstrip()
                                alname1 = alname.lstrip("DNS:")
                                alname2 = (
                                    alname1.replace("DNS:", "").replace(",", "").split()
                                )
                                for x in alname2:
                                    altDomainNames.append(x)
                    # print(domainName)
                    # print(altDomainNames)
                    # print(alname2)
                    both = []
                    for x in domainName:
                        both.append(x)
                    for x in altDomainNames:
                        both.append(x)

                    tmpdns2 = []
                    for x in both:
                        tmpdns2.append(x)
                    for x in tmpdns:
                        tmpdns2.append(x)

                    unsortedhostnames = []
                    for x in tmpdns2:
                        unsortedhostnames.append(x)
                    allsortedhostnames = sorted(set(tmpdns2))
                    allsortedhostnameslist = []
                    for x in allsortedhostnames:
                        allsortedhostnameslist.append(x)

        dnsPort = np.dns_ports
        if len(dnsPort) == 0:
            if len(allsortedhostnameslist) != 0:
                for x in allsortedhostnameslist:
                    self.hostnames.append(x)
                hosts = Hosts(path="/etc/hosts")
                new_entry = HostsEntry(
                    entry_type="ipv4", address=self.target, names=allsortedhostnameslist
                )
                hosts.add([new_entry])
                hosts.write()

        else:
            if not os.path.exists(f"{self.target}-Report/dns"):
                os.makedirs(f"{self.target}-Report/dns")
            ######## Check For Zone Transfer: Running dig ###############
            if len(allsortedhostnameslist) != 0:
                alldns = " ".join(map(str, allsortedhostnameslist))
                # print(alldns)
                dig_command = f"dig axfr @{self.target} {alldns} | tee {self.target}-Report/dns/dig-zonexfer-{self.target}.log"
                print(cmd_info, dig_command)
                call(dig_command, shell=True)
                filterZoneTransferDomainsCMD = (
                    f"grep -v ';' {self.target}-Report/dns/dig-zonexfer-{self.target}.log "
                    + "| grep -v -e '^[[:space:]]*$' "
                    + "| awk '{print $1}' "
                    + f"| sed 's/.$//' | sort -u >{self.target}-Report/dns/zonexfer-domains.log"
                )
                zxferFile = f"{self.target}-Report/dns/zonexfer-domains.log"
                if os.path.exists(zxferFile):
                    zonexferDns = []
                    with open(zxferFile, "r") as zf:
                        for line in zf:
                            zonexferDns.append(line.rstrip())
                    if len(allsortedhostnameslist) != 0:
                        for x in allsortedhostnameslist:
                            zonexferDns.append(x)
                    sortedAllDomains = sorted(set(zonexferDns))
                    sortedAllDomainsList = []
                    for x in sortedAllDomains:
                        sortedAllDomainsList.append(x)
                        self.hostnames.append(x)
                    if len(zonexferDns) != 0:
                        hosts = Hosts(path="/etc/hosts")
                        new_entry = HostsEntry(
                            entry_type="ipv4",
                            address=self.target,
                            names=sortedAllDomainsList,
                        )
                        hosts.add([new_entry])
                        hosts.write()
