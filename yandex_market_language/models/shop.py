import inspect
from typing import List, Iterator

from yandex_market_language import models, exceptions
from yandex_market_language.models import fields
from yandex_market_language.models.abstract import XMLElement, XMLSubElement

from yandex_market_language.exceptions import ValidationError


class Shop(
    fields.EnableAutoDiscountField,
    fields.DeliveryOptionsField,
    fields.PickupOptionsField,
    models.AbstractModel
):
    """
    Shop model.

    Docs:
    https://yandex.ru/support/partnermarket/elements/shop.html
    """

    __slots__ = [
        '_url',
        'name',
        'company',
        'currencies',
        'categories',
        'offers',
        'platform',
        'version',
        'agency',
        'email',
        '_delivery_options',
        '_pickup_options',
        '_enable_auto_discounts',
        'gifts',
        'promos'
    ]

    def __init__(
        self,
        name: str,
        company: str,
        currencies: List["models.Currency"],
        categories: List["models.Category"],
        offers: List["models.offers.AbstractOffer"],
        url: str = None,
        platform: str = None,
        version: str = None,
        agency: str = None,
        email: str = None,
        delivery_options: List["models.Option"] = None,
        pickup_options: List["models.Option"] = None,
        enable_auto_discounts=None,
        gifts: List["models.Gift"] = None,
        promos: List["models.Promo"] = None,
    ):
        self.name = name
        self.company = company
        self.url = url
        self.platform = platform
        self.version = version
        self.agency = agency
        self.email = email
        self.currencies = currencies
        self.categories = categories
        self.delivery_options = delivery_options
        self.pickup_options = pickup_options
        self.enable_auto_discounts = enable_auto_discounts
        self.offers = offers
        self.gifts = gifts
        self.promos = promos

    @property
    def url(self):
        return self._url

    @url.setter
    def url(self, value: str):
        self._url = value

    def create_dict(self, **kwargs) -> dict:
        return dict(
            name=self.name,
            company=self.company,
            url=self.url,
            platform=self.platform,
            version=self.version,
            agency=self.agency,
            email=self.email,
            currencies=[c.to_dict() for c in self.currencies],
            categories=[c.to_dict() for c in self.categories],
            delivery_options=[o.to_dict() for o in self.delivery_options],
            pickup_options=[o.to_dict() for o in self.pickup_options],
            enable_auto_discounts=self.enable_auto_discounts,
            offers=[o.to_dict() for o in self.offers],
            gifts=[g.to_dict() for g in self.gifts] if self.gifts else [],
            promos=[p.to_dict() for p in self.promos] if self.promos else [],
        )

    def create_xml(self, **kwargs) -> XMLElement:
        shop_el = XMLElement("shop")

        # Add simple elements
        for tag in (
            "name",
            "company",
            "url",
            "platform",
            "version",
            "agency",
            "email",
        ):
            value = getattr(self, tag)
            if value:
                el = XMLSubElement(shop_el, tag)
                el.text = value

        # Add currencies
        currencies_el = XMLSubElement(shop_el, "currencies")
        for c in self.currencies:
            c.to_xml(currencies_el)

        # Add categories
        categories_el = XMLSubElement(shop_el, "categories")
        for c in self.categories:
            c.to_xml(categories_el)

        # Add delivery options
        if self.delivery_options:
            delivery_options_el = XMLSubElement(shop_el, "delivery-options")
            for o in self.delivery_options:
                o.to_xml(delivery_options_el)

        # Add pickup options
        if self.pickup_options:
            pickup_options_el = XMLSubElement(shop_el, "pickup-options")
            for o in self.pickup_options:
                o.to_xml(pickup_options_el)

        # Add enable_auto_discounts
        if self._enable_auto_discounts:
            enable_auto_discounts_el = XMLSubElement(
                shop_el, "enable_auto_discounts"
            )
            enable_auto_discounts_el.text = self._enable_auto_discounts

        # Add offers
        offers_el = XMLSubElement(shop_el, "offers")
        for o in self.offers:
            o.to_xml(offers_el)

        # Add gifts
        if self.gifts:
            gifts_el = XMLSubElement(shop_el, "gifts")
            for g in self.gifts:
                g.to_xml(gifts_el)

        # Add promos
        if self.promos:
            promos_el = XMLSubElement(shop_el, "promos")
            for p in self.promos:
                p.to_xml(promos_el)

        return shop_el

    @staticmethod
    def from_xml(shop_el: XMLElement) -> "Shop":
        kwargs = {}

        for el in shop_el:
            if el.tag == "currencies":
                currencies = []
                for currency_el in el:
                    currencies.append(models.Currency.from_xml(currency_el))
                kwargs["currencies"] = currencies
            elif el.tag == "categories":
                categories = []
                for category_el in el:
                    categories.append(models.Category.from_xml(category_el))
                kwargs["categories"] = categories
            elif el.tag == "delivery-options":
                delivery_options = []
                for option_el in el:
                    delivery_options.append(models.Option.from_xml(option_el))
                kwargs["delivery_options"] = delivery_options
            elif el.tag == "pickup-options":
                pickup_options = []
                for option_el in el:
                    pickup_options.append(models.Option.from_xml(option_el))
                kwargs["pickup_options"] = pickup_options
            elif el.tag == "offers":
                offers = []
                for offer_el in el:
                    offer_type = offer_el.attrib.get("type")
                    if offer_type is None:
                        offer = models.SimplifiedOffer.from_xml(offer_el)
                    elif offer_type == "vendor.model":
                        offer = models.ArbitraryOffer.from_xml(offer_el)
                    elif offer_type == "book":
                        offer = models.BookOffer.from_xml(offer_el)
                    elif offer_type == "audiobook":
                        offer = models.AudioBookOffer.from_xml(offer_el)
                    elif offer_type == "artist.title":
                        offer = models.MusicVideoOffer.from_xml(offer_el)
                    elif offer_type == "medicine":
                        offer = models.MedicineOffer.from_xml(offer_el)
                    elif offer_type == "event-ticket":
                        offer = models.EventTicketOffer.from_xml(offer_el)
                    elif offer_type == "alco":
                        offer = models.AlcoholOffer.from_xml(offer_el)
                    else:
                        raise exceptions.ParseError(
                            "Got unexpected offer type: {0}".format(offer_type)
                        )
                    offers.append(offer)
                kwargs["offers"] = offers
            elif el.tag == "gifts":
                gifts = []
                for gift_el in el:
                    gifts.append(models.Gift.from_xml(gift_el))
                if gifts:
                    kwargs["gifts"] = gifts
            elif el.tag == "promos":
                promos = []
                for promo_el in el:
                    promos.append(models.Promo.from_xml(promo_el))
                if promos:
                    kwargs["promos"] = promos
            else:
                kwargs[el.tag] = el.text

        if 'currencies' not in kwargs:
            kwargs['currencies'] = []

        args = inspect.getfullargspec(Shop.__init__).args[1:]
        args = {*args}
        kwargs = {key: value for (key, value) in kwargs.items() if key in args}

        return Shop(**kwargs)

    @staticmethod
    def from_iterator(iterator: Iterator) -> "Shop":
        kwargs = {}

        el: XMLElement
        for event, el in iterator:
            if el.tag == 'currencies' and event == 'start':
                currencies = []
                currency_el: XMLElement
                for event, currency_el in iterator:
                    if event == 'end' and currency_el.tag == 'currencies':
                        break

                    if event == 'end':
                        currencies.append(models.Currency.from_xml(currency_el))

                kwargs['currencies'] = currencies

            elif el.tag == 'categories' and event == 'start':
                categories = []
                category_el: XMLElement
                for event, category_el in iterator:
                    if event == 'end' and category_el.tag == 'categories':
                        break

                    if event == 'end':
                        categories.append(models.Category.from_xml(category_el))

                kwargs['categories'] = categories

            elif el.tag == 'delivery-options' and event == 'start':
                delivery_options = []
                option_el: XMLElement
                for event, option_el in iterator:
                    if event == 'end' and option_el.tag == 'delivery-options':
                        break

                    if event == 'end':
                        delivery_options.append(models.Option.from_xml(option_el))

                kwargs['delivery_options'] = delivery_options

            elif el.tag == 'pickup-options':
                pickup_options = []
                option_el: XMLElement
                for event, option_el in iterator:
                    if event == 'end' and option_el.tag == 'pickup-options':
                        break

                    if event == 'end':
                        pickup_options.append(models.Option.from_xml(option_el))

                kwargs['pickup_options'] = pickup_options

            elif el.tag == 'offers' and event == 'start':
                offers = []
                offer_el: XMLElement
                for event, offer_el in iterator:
                    if event == 'end' and offer_el.tag == 'offers':
                        break

                    if event == 'start' and offer_el.tag == 'offer':
                        offer_type = offer_el.attrib.get('type')
                        if offer_type is None:
                            offer = models.SimplifiedOffer.from_iterator(iterator, offer_el)
                        elif offer_type == "vendor.model":
                            offer = models.ArbitraryOffer.from_iterator(iterator, offer_el)
                        elif offer_type == "book":
                            offer = models.BookOffer.from_iterator(iterator, offer_el)
                        elif offer_type == "audiobook":
                            offer = models.AudioBookOffer.from_iterator(iterator, offer_el)
                        elif offer_type == "artist.title":
                            offer = models.MusicVideoOffer.from_iterator(iterator, offer_el)
                        elif offer_type == "medicine":
                            offer = models.MedicineOffer.from_iterator(iterator, offer_el)
                        elif offer_type == "event-ticket":
                            offer = models.EventTicketOffer.from_iterator(iterator, offer_el)
                        elif offer_type == "alco":
                            offer = models.AlcoholOffer.from_iterator(iterator, offer_el)
                        else:
                            raise exceptions.ParseError(
                                'Got unexpected offer type: {0}'.format(offer_type)
                            )
                        offers.append(offer)
                kwargs['offers'] = offers
            elif el.tag == 'gifts' and event == 'start':
                gifts = []
                gift_el: XMLElement
                for gift_el in iterator:
                    if event == 'end' and gift_el.tag == 'gifts':
                        break

                    if event == 'end':
                        gifts.append(models.Gift.from_xml(gift_el))

                if gifts:
                    kwargs['gifts'] = gifts

            elif el.tag == 'promos' and event == 'start':
                promos = []
                promo_el: XMLElement
                for promo_el in iterator:
                    if event == 'end' and promo_el.tag == 'promos':
                        break

                    if event == 'end':
                        promos.append(models.Promo.from_xml(promo_el))

                if promos:
                    kwargs['promos'] = promos

            else:
                if event == 'end':
                    kwargs[el.tag] = el.text

        if 'currencies' not in kwargs:
            kwargs['currencies'] = []

        args = inspect.getfullargspec(Shop.__init__).args[1:]
        args = {*args}
        kwargs = {key: value for (key, value) in kwargs.items() if key in args}

        return Shop(**kwargs)
