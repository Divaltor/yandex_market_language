from datetime import datetime

from .abstract import AbstractModel, XMLElement
from .shop import Shop
from ..exceptions import ValidationError

DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
ALT_DATE_FORMAT = "%Y-%m-%d %H:%M"


class Feed(AbstractModel):
    """
    YML Feed model.

    Docs:
    https://yandex.ru/support/partnermarket/export/yml.html
    """
    def __init__(self, shop: Shop, date: datetime.date = None):
        self.shop = shop
        self.date = date

    @property
    def date(self) -> datetime:
        try:
            dt = datetime.strptime(self._date, DATE_FORMAT)
        except (ValidationError, ValueError):
            dt = datetime.strptime(self._date, ALT_DATE_FORMAT)

        if dt is None:
            dt = datetime.now().strftime(DATE_FORMAT)

        return dt

    @date.setter
    def date(self, dt):
        try:
            dt = self._is_valid_datetime(dt, DATE_FORMAT, "date", True)
        except (ValidationError, ValueError):
            dt = self._is_valid_datetime(dt, ALT_DATE_FORMAT, "date", True)
        if dt is None:
            dt = datetime.now().strftime(DATE_FORMAT)
        self._date = dt

    def create_dict(self, **kwargs) -> dict:
        return dict(
            shop=self.shop.to_dict(),
            date=self.date,
        )

    def create_xml(self, **kwargs) -> XMLElement:
        feed_el = XMLElement("yml_catalog", {"date": self._date})
        self.shop.to_xml(feed_el)
        return feed_el

    @staticmethod
    def from_xml(el: XMLElement) -> "Feed":
        shop = Shop.from_xml(el[0])
        date = el.attrib.get("date")
        return Feed(shop, date=date)
