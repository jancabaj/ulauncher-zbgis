import subprocess
import urllib.parse
from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.OpenUrlAction import OpenUrlAction


class ZbgisExtension(Extension):

    def __init__(self):
        super(ZbgisExtension, self).__init__()
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())


class KeywordQueryEventListener(EventListener):

    def on_event(self, event, extension):
        query = event.get_argument() or ""

        if not query:
            return RenderResultListAction([
                ExtensionResultItem(
                    icon='images/icon.png',
                    name='ZBGIS Search',
                    description='Enter search text for ZBGIS cadastral map',
                    on_enter=None
                )
            ])

        results = []
        encoded = urllib.parse.quote(query)

        # General search (always show)
        search_url = f"https://zbgis.skgeodesy.sk/mapka/sk/kataster/search?q={encoded}"
        results.append(
            ExtensionResultItem(
                icon='images/icon.png',
                name=f'Search ZBGIS: {query}',
                description=f'General search in cadastral map',
                on_enter=OpenUrlAction(search_url)
            )
        )

        # Check if query looks like a parcel number or has parcel format
        query_parts = query.strip().split()

        # If query is purely numeric, offer parcel search
        if query.strip().isdigit():
            parcel_search_url = f"https://zbgis.skgeodesy.sk/mapka/sk/kataster/search?q=parcela%20{encoded}"
            results.append(
                ExtensionResultItem(
                    icon='images/icon.png',
                    name=f'Search parcel number: {query}',
                    description=f'Search for parcel (parcela) #{query}',
                    on_enter=OpenUrlAction(parcel_search_url)
                )
            )

        # If query has format "location parcel_number", provide specialized search
        elif len(query_parts) == 2 and query_parts[1].isdigit():
            location, parcel_num = query_parts
            location_encoded = urllib.parse.quote(location)
            parcel_encoded = urllib.parse.quote(parcel_num)

            # Search for location first, then parcel
            combined_search = f"https://zbgis.skgeodesy.sk/mapka/sk/kataster/search?q={location_encoded}%20parcela%20{parcel_encoded}"
            results.append(
                ExtensionResultItem(
                    icon='images/icon.png',
                    name=f'Search parcel in {location}: #{parcel_num}',
                    description=f'Search for parcel {parcel_num} in {location}',
                    on_enter=OpenUrlAction(combined_search)
                )
            )

        # If query contains "parcela" or "parcel", emphasize it
        elif 'parcela' in query.lower() or 'parcel' in query.lower():
            results[0].description = 'Search for parcel in cadastral map'

        return RenderResultListAction(results)


if __name__ == '__main__':
    ZbgisExtension().run()
