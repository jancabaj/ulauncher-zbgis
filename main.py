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

        encoded = urllib.parse.quote(query)
        url = f"https://zbgis.skgeodesy.sk/mapka/sk/kataster/search?q={encoded}"

        return RenderResultListAction([
            ExtensionResultItem(
                icon='images/icon.png',
                name=f'Search ZBGIS: {query}',
                description=f'Open {url}',
                on_enter=OpenUrlAction(url)
            )
        ])


if __name__ == '__main__':
    ZbgisExtension().run()
