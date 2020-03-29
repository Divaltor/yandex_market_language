from unittest import mock

from faker import Faker
from unittest import TestCase
from xml.etree import ElementTree as ET
from yandex_market_language import models
from yandex_market_language.exceptions import ValidationError

from .factories import (
    ShopFactory,
    CurrencyFactory,
    CategoryFactory,
    OptionFactory,
)


fake = Faker()


@mock.patch.multiple(models.BaseModel, __abstractmethods__=set())
class BaseModelTestCase(TestCase):
    @mock.patch("yandex_market_language.models.BaseModel.create_xml")
    def test_to_xml_with_parent(self, p):
        parent_el = mock.MagicMock()
        parent_el.append = mock.MagicMock()
        p.return_value = ET.Element("test")
        base = models.BaseModel()
        base.to_xml(parent_el)
        self.assertEqual(p.call_count, 1)
        self.assertEqual(parent_el.append.call_count, 1)

    @mock.patch("yandex_market_language.models.BaseModel.create_dict")
    def test_clean_dict(self, p):
        d = {"a": 1, "b": 2, "c": None}
        p.return_value = d
        base = models.BaseModel()
        cd = base.to_dict(clean=True)
        self.assertEqual(p.call_count, 1)
        self.assertEqual(cd, {"a": 1, "b": 2})


class FeedModelTestCase(TestCase):
    def test_to_dict(self):
        shop = ShopFactory()
        feed = models.Feed(shop)
        feed_dict = feed.to_dict()
        self.assertEqual(sorted(list(feed_dict.keys())), ["date", "shop"])
        self.assertEqual(feed_dict["date"], feed.date)
        self.assertEqual(feed_dict["shop"], feed.shop.to_dict())

    def test_to_xml(self):
        shop = ShopFactory()
        feed = models.Feed(shop)
        feed_el = feed.to_xml()
        self.assertEqual(list(el.tag for el in feed_el), ["shop"])
        self.assertEqual(ET.tostring(feed_el[0]), ET.tostring(shop.to_xml()))
        self.assertEqual(feed_el.tag, "yml_catalog")
        self.assertEqual(feed_el.get("date"), feed.date)


class ShopModelTestCase(TestCase):
    def test_to_dict(self):
        shop = ShopFactory()
        shop_dict = shop.to_dict()
        keys = sorted(list(shop_dict.keys()))
        expected_keys = sorted([
            "name",
            "company",
            "url",
            "platform",
            "version",
            "agency",
            "email",
            "currencies",
            "categories",
            "delivery_options",
            "pickup_options",
            "enable_auto_discounts",
        ])
        self.assertEqual(keys, expected_keys)
        for k in (
            "name",
            "company",
            "url",
            "platform",
            "version",
            "agency",
            "email",
            "enable_auto_discounts",
        ):
            self.assertEqual(shop_dict[k], getattr(shop, k))

    def test_to_xml(self):
        shop = ShopFactory()
        shop_el = shop.to_xml()
        keys = sorted(list(el.tag for el in shop_el))
        expected_keys = sorted([
            "name",
            "company",
            "url",
            "platform",
            "version",
            "agency",
            "email",
            "currencies",
            "categories",
            "delivery-options",
            "pickup-options",
            "enable_auto_discounts",
        ])
        self.assertEqual(keys, expected_keys)
        for el in shop_el:
            if el.tag in (
                "currencies",
                "categories",
                "delivery-options",
                "pickup-options",
            ):
                continue
            elif el.tag == "enable_auto_discounts":
                self.assertEqual(el.text, shop._enable_auto_discounts)
            else:
                self.assertEqual(el.text, getattr(shop, el.tag))

    def test_url_validation_error(self):
        with self.assertRaises(ValidationError) as e:
            ShopFactory(url=fake.pystr(513, 513))
            self.assertEqual(
                str(e), "The maximum url length is 512 characters."
            )

    def test_enable_auto_discounts_validation_error(self):
        msg = (
            "enable_auto_discounts should be True, False or str from available"
            " values: {v}".format(
                v=", ".join(models.shop.ENABLE_AUTO_DISCOUNTS_CHOICES)
            )
        )
        with self.assertRaises(
            models.shop.EnableAutoDiscountsValidationError
        ) as e:
            ShopFactory(enable_auto_discounts="err")
            self.assertEqual(str(e), msg)
        self.assertEqual(
            str(models.shop.EnableAutoDiscountsValidationError()), msg
        )

    def test_enable_auto_discounts_property(self):
        s = ShopFactory()
        for v in ["yes", "true", "1"]:
            s.enable_auto_discounts = v
            self.assertEqual(s.enable_auto_discounts, True)

        for v in ["no", "false", "0"]:
            s.enable_auto_discounts = v
            self.assertEqual(s.enable_auto_discounts, False)

        s.enable_auto_discounts = None
        self.assertEqual(s.enable_auto_discounts, None)

        s.enable_auto_discounts = True
        self.assertEqual(s.enable_auto_discounts, True)

        s.enable_auto_discounts = False
        self.assertEqual(s.enable_auto_discounts, False)


class CurrencyModelTestCase(TestCase):
    def test_to_dict(self):
        c = CurrencyFactory()
        d = c.to_dict()
        keys = sorted(list(d.keys()))
        expected_keys = sorted(["id", "rate", "plus"])
        self.assertEqual(keys, expected_keys)
        self.assertEqual(c.currency, d["id"])
        self.assertEqual(c.rate, d["rate"])
        self.assertEqual(c.plus, d["plus"])

    def test_to_xml(self):
        c = CurrencyFactory()
        el = c.to_xml()
        expected_xml = ET.Element("currency", c.to_dict())
        self.assertEqual(ET.tostring(el), ET.tostring(expected_xml))

    def test_to_xml_none_plus_attr(self):
        c = CurrencyFactory(plus=None)
        el = c.to_xml()
        expected_attribs = {"id": c.currency, "rate": c.rate}
        expected_xml = ET.Element("currency", expected_attribs)
        self.assertEqual(ET.tostring(el), ET.tostring(expected_xml))

    def test_currency_validation_error(self):
        msg = "Price data is accepted only in: (formatted_choices)".format(
            formatted_choices=", ".join(models.currency.CURRENCY_CHOICES)
        )
        with self.assertRaises(
            models.currency.CurrencyChoicesValidationError
        ) as e:
            CurrencyFactory(currency="UAN")
            self.assertEqual(str(e), msg)

        self.assertEqual(
            str(models.currency.CurrencyChoicesValidationError()), msg
        )

    def test_rate_validation_error(self):
        msg = (
            "The rate parameter can have the following values: "
            "number (int or float), (rate_choices)".format(
                rate_choices=', '.join(models.currency.RATE_CHOICES)
            )
        )
        with self.assertRaises(ValidationError) as e:
            CurrencyFactory(rate="err")
            self.assertEqual(str(e), msg)

        self.assertEqual(str(models.currency.RateValidationError()), msg)

    def test_plus_validation_error(self):
        with self.assertRaises(ValidationError) as e:
            CurrencyFactory(plus="err")
            self.assertEqual(str(e), "The plus parameter only can be int.")


class CategoryModelTestCase(TestCase):
    def test_to_dict(self):
        c = CategoryFactory()
        d = c.to_dict()
        self.assertEqual(sorted(d.keys()), sorted(["id", "name", "parent_id"]))
        self.assertEqual(d["id"], c.category_id)
        self.assertEqual(d["name"], c.name)
        self.assertEqual(d["parent_id"], c.parent_id)

    def test_to_xml(self):
        c = CategoryFactory(parent_id=None)
        el = c.to_xml()
        expected_el = ET.Element("category", {"id": c.category_id})
        expected_el.text = c.name
        self.assertEqual(ET.tostring(el), ET.tostring(expected_el))


class OptionModelTestCase(TestCase):
    def test_to_dict(self):
        o = OptionFactory()
        d = o.to_dict()
        self.assertEqual(
            sorted(d.keys()), sorted(["cost", "days", "order_before"])
        )
        self.assertEqual(d["cost"], o.cost)
        self.assertEqual(d["days"], o.days)
        self.assertEqual(d["order_before"], o.order_before)

    def test_to_xml(self):
        o = OptionFactory(order_before=None)
        el = o.to_xml()
        expected_el = ET.Element("option", {"cost": o.cost, "days": o.days})
        self.assertEqual(ET.tostring(el), ET.tostring(expected_el))
