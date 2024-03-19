# Ansible2SnipeIT

This repository is a hodgepodge of Python scripts that I use to fill and update my Snipe-IT instance with records.

I'm not a professional developer, so I'm sure there are better ways to do some of this stuff. 
I'm open to suggestions and pull requests.

## Parts of this repository
### ansible2snipe.py
Uses Ansible to create objects in Snipe-IT based on your Ansible playbook

### create_companies.py
Creates a list of companies in your Snipe-IT instance, useful if you have more than 2 or 3 companies to add.

### csv2snipe.py
Imports a CSV file into Snipe-IT and creates logs for people to review.

### dellwarranty2snipe.py
Uses the Dell Warranty API to update objects in Snipe-IT based on your Dell Service Tags.

### ldap2snipe.py
NEEDS REWORKED: Uses LDAP to update OU in Snipe-IT based on your LDAP server.

### medigate2snipe.py
Uses the Medigate API to update objects in Snipe-IT based on your Medigate inventory.

### ndaabanned.py
Finds objects in your Snipe-IT database that are banned by NDAA regulations.

### ordr2snipe.py
NEEDS REWORKED: Uses the Ordr API to create objects in Snipe-IT based on your Ordr inventory.

### sqlsrs2snipe.py
Uses SCCM to create objects in Snipe-IT based on SQL Reporting Services reports. Note these are highly specific
and just intended as an example of how to parse them. You probably need to build a per-report middleware.

## How to run this
I run this in a Python virtual environment on a Cronicle server.

## How well does it work
Approximately 100,000 objects in ~1-2 hours.