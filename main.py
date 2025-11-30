import subprocess
import urllib.parse
import csv
import os
from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.OpenUrlAction import OpenUrlAction


class CadastreData:
    """Loads and manages cadastre data from CSV files"""

    def __init__(self):
        self.cadastre_map = {}  # name -> {code, coords}
        self.load_data()

    def load_data(self):
        """Load cadastre codes and coordinates from CSV files"""
        base_dir = os.path.dirname(os.path.abspath(__file__))

        # Load cadastre codes
        code_file = os.path.join(base_dir, 'cadastre_code_name.csv')
        coords_file = os.path.join(base_dir, 'ku_coords.csv')

        # First load codes (IDN5 -> name)
        codes = {}
        try:
            with open(code_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    name = row['NM5'].strip()
                    code = row['IDN5'].strip()
                    codes[name] = code
        except Exception as e:
            print(f"Error loading cadastre codes: {e}")

        # Then load coordinates and merge with codes
        try:
            with open(coords_file, 'r', encoding='utf-8-sig', newline='') as f:
                reader = csv.DictReader(f, delimiter=';')
                for row in reader:
                    name = row['NM5'].strip()
                    x = row['x'].strip()
                    y = row['y'].strip()

                    # Store cadastre data
                    self.cadastre_map[name.lower()] = {
                        'name': name,
                        'code': codes.get(name, ''),
                        'x': x,
                        'y': y
                    }
        except Exception as e:
            print(f"Error loading cadastre coordinates: {e}")

    def find_cadastre(self, query):
        """Find cadastre by partial name match"""
        query_lower = query.lower()

        # Exact match first
        if query_lower in self.cadastre_map:
            return self.cadastre_map[query_lower]

        # Partial match
        for name, data in self.cadastre_map.items():
            if query_lower in name or name.startswith(query_lower):
                return data

        return None


class ZbgisExtension(Extension):

    def __init__(self):
        super(ZbgisExtension, self).__init__()
        self.cadastre_data = CadastreData()
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())


class KeywordQueryEventListener(EventListener):

    def on_event(self, event, extension):
        query = event.get_argument() or ""

        if not query:
            return RenderResultListAction([
                ExtensionResultItem(
                    icon='images/icon.png',
                    name='ZBGIS Search',
                    description='Enter search text or "location parcel_number"',
                    on_enter=None
                )
            ])

        results = []
        encoded = urllib.parse.quote(query)
        query_parts = query.strip().split()

        # Check if query has format "location parcel_number"
        # Parcel numbers can contain digits and slashes (e.g., "143/12")
        def is_parcel_number(s):
            return all(c.isdigit() or c == '/' for c in s) and any(c.isdigit() for c in s)

        if len(query_parts) == 2 and is_parcel_number(query_parts[1]):
            location_query, number = query_parts
            cadastre = extension.cadastre_data.find_cadastre(location_query)

            if cadastre and cadastre['code']:
                # Build direct URLs for both parcel and house number
                cadastre_code = cadastre['code']
                x = cadastre['x']
                y = cadastre['y']
                pos = f"{y},{x},15"

                # URL-encode the number (e.g., "445/2" becomes "445%2F2")
                encoded_number = urllib.parse.quote(number, safe='')

                # Parcel URL
                parcel_url = f"https://zbgis.skgeodesy.sk/mapka/sk/kataster/detail/kataster/parcela-c/{cadastre_code}/{encoded_number}?pos={pos}"

                # House number URL (súpisné číslo - registration number)
                house_url = f"https://zbgis.skgeodesy.sk/mapka/sk/kataster/detail/kataster/budova-sc/{cadastre_code}/{encoded_number}?pos={pos}"

                # Add parcel option
                results.append(
                    ExtensionResultItem(
                        icon='images/icon.png',
                        name=f'Parcel {number} in {cadastre["name"]}',
                        description=f'Open parcel detail (cadastre code: {cadastre_code})',
                        on_enter=OpenUrlAction(parcel_url)
                    )
                )

                # Add house number option
                results.append(
                    ExtensionResultItem(
                        icon='images/icon.png',
                        name=f'House {number} in {cadastre["name"]}',
                        description=f'Open building detail (cadastre code: {cadastre_code})',
                        on_enter=OpenUrlAction(house_url)
                    )
                )

        # If query is a number (digits and/or slashes), show hint
        elif is_parcel_number(query.strip()):
            number = query.strip()

            # Show hints for both parcel and house number search
            results.append(
                ExtensionResultItem(
                    icon='images/icon.png',
                    name=f'Number: {number}',
                    description='Tip: Use "location number" for direct links (e.g., "nitra 143/12")',
                    on_enter=None
                )
            )
            results.append(
                ExtensionResultItem(
                    icon='images/icon.png',
                    name=f'Will search as parcel or house number',
                    description='Both parcel and house number options will be shown',
                    on_enter=None
                )
            )

        # General search (always show as fallback or primary)
        search_url = f"https://zbgis.skgeodesy.sk/mapka/sk/kataster/search?q={encoded}"
        results.append(
            ExtensionResultItem(
                icon='images/icon.png',
                name=f'Search ZBGIS: {query}',
                description='General search in cadastral map',
                on_enter=OpenUrlAction(search_url)
            )
        )

        return RenderResultListAction(results)


if __name__ == '__main__':
    ZbgisExtension().run()
