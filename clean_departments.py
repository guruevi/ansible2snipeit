#!/usr/bin/env python3
"""
Clean department names in Snipe-IT by replacing HTML entities and ampersands:
  '&amp;' -> 'and'
  '&'     -> 'and'
"""
from configparser import RawConfigParser
import logging

from snipeit_api.api import SnipeITApi

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

CONFIG = RawConfigParser()
CONFIG.read("settings.conf")
snipeit_apiurl = CONFIG.get('snipe-it', 'url')
snipeit_apikey = CONFIG.get('snipe-it', 'apikey')

snipe_api = SnipeITApi(snipeit_apiurl, snipeit_apikey)


def clean_name(name: str) -> str:
    return name.replace("&amp;", "and").replace("&", "and").strip()


def get_all_departments() -> list[dict]:
    page_size = 500
    offset = 0
    all_depts = []

    while True:
        data = snipe_api.call("departments", payload={"limit": page_size, "offset": offset})
        if not data or "rows" not in data:
            logging.error(f"Unexpected response: {data}")
            break

        rows = data["rows"]
        all_depts.extend(rows)
        logging.info(f"Fetched {len(all_depts)} / {data['total']} departments")

        if len(all_depts) >= data["total"]:
            break

        offset += page_size

    return all_depts


def main():
    departments = get_all_departments()
    updated = 0
    deleted = 0
    skipped = 0

    for dept in departments:
        dept_id = dept["id"]
        original = dept["name"]
        can_delete = dept.get("available_actions", {}).get("delete", False)

        if can_delete:
            logging.info(f"  Deleting [{dept_id}] '{original}'")
            result = snipe_api.call(f"departments/{dept_id}", method="DELETE")
            if result.get("status") == "success":
                deleted += 1
                logging.info(f"  Deleted")
            else:
                logging.error(f"  Failed to delete department {dept_id}: {result}")
            continue

        cleaned = clean_name(original)
        if cleaned == original:
            skipped += 1
            continue

        logging.info(f"  Renaming [{dept_id}] '{original}' -> '{cleaned}'")
        result = snipe_api.call(
            f"departments/{dept_id}",
            method="PATCH",
            payload={"name": cleaned}
        )
        if result.get("status") == "success":
            updated += 1
            logging.info(f"  OK")
        else:
            logging.error(f"  Failed to update department {dept_id}: {result}")

    print(f"\nDone — {deleted} deleted, {updated} renamed, {skipped} unchanged.")


if __name__ == "__main__":
    main()


