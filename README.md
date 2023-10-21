# Ansible2SnipeIT

This repository is a hodgepodge of Python scripts that I use to fill and update my Snipe-IT instance with records.

I'm not a professional developer, so I'm sure there are better ways to do some of this stuff. 
I'm open to suggestions and pull requests.

## Parts of this repository
### create_companies.py
Creates a list of companies in your Snipe-IT instance, useful if you have more than 2 or 3 companies to add.

### ansible2snipe.py
Uses Ansible's Mongo Cache to create objects in Snipe-IT based on your Ansible inventory.

This is based around https://github.com/grokability/jamf2snipe, but I've made some changes to make it work with Ansible.

### sqlsrs2snipe.py
Uses SCCM to create objects in Snipe-IT based on SQL Reporting Services reports. Note these are highly specific
and just intended as an example of how to parse them. You probably need to build a per-report middleware.

## How to run this
I run this in a Python virtual environment on a Cronicle server.