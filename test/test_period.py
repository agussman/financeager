# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import unittest

import xml.etree.ElementTree as ET
from tinydb import database
from financeager.period import XmlPeriod, TinyDbPeriod
from financeager.model import Model
from financeager.entries import BaseEntry
from financeager.items import CategoryItem
import os

def suite():
    suite = unittest.TestSuite()
    tests = [
            'test_default_name'
            ]
    suite.addTest(unittest.TestSuite(map(CreateEmptyPeriodTestCase, tests)))
    tests = [
            'test_expenses_entry_exists',
            'test_expenses_category_sum'
            ]
    suite.addTest(unittest.TestSuite(map(AddExpenseEntryTestCase, tests)))
    tests = [
            'test_period_name',
            'test_earnings_category_sum',
            'test_expenses_category_sum'
            ]
    suite.addTest(unittest.TestSuite(map(XmlConversionTestCase, tests)))
    suite.addTest(unittest.TestSuite(map(PeriodOnlyXmlConversionTestCase, tests)))
    tests = [
            'test_find_entry',
            'test_remove_entry'
            ]
    suite.addTest(unittest.TestSuite(map(TinyDbPeriodTestCase, tests)))
    return suite

class CreateEmptyPeriodTestCase(unittest.TestCase):
    def test_default_name(self):
        period = XmlPeriod()
        self.assertEqual(period.name, "2016")

class AddExpenseEntryTestCase(unittest.TestCase):
    def setUp(self):
        self.period = XmlPeriod()
        self.period.add_entry(name="Pineapple", value="-5", category="Fruits")

    def test_expenses_entry_exists(self):
        self.assertIsNotNone(
                self.period._expenses_model.find_name_item(
                    name="Pineapple", category="Fruits"))

    def test_expenses_category_sum(self):
        self.assertAlmostEqual(
                self.period._expenses_model.category_sum("Fruits"),
                5, places=5)

class XmlConversionTestCase(unittest.TestCase):
    def setUp(self):
        earnings_model = Model(name="earnings")
        earnings_model.add_entry(BaseEntry("Paycheck", 456.78))
        expenses_model = Model(name="expenses")
        # expenses_model.add_entry(BaseEntry("Citroën", 24999), category="Car")
        expenses_model.add_entry(BaseEntry("Citroen", 24999), category="Car")
        self.period = XmlPeriod(models=(earnings_model, expenses_model), name="1st Quartal")
        xml_element = self.period.convert_to_xml()
        self.parsed_period = XmlPeriod(xml_element=xml_element)

    def test_period_name(self):
        self.assertEqual(self.parsed_period.name, "1st Quartal")

    def test_earnings_category_sum(self):
        self.assertAlmostEqual(self.parsed_period._earnings_model.category_sum(
            CategoryItem.DEFAULT_NAME), 456.78, places=5)

    def test_expenses_category_sum(self):
        self.assertAlmostEqual(self.parsed_period._expenses_model.category_sum(
            "Car"), 24999, places=5)

class PeriodOnlyXmlConversionTestCase(unittest.TestCase):
    def setUp(self):
        self.period = XmlPeriod(name="1st Quartal")
        self.period.add_entry(name="Paycheck", value=456.78)
        self.period.add_entry(name="Citroen", value="-24999", category="Car")
        xml_element = self.period.convert_to_xml()
        self.parsed_period = XmlPeriod(xml_element=xml_element)

    def test_period_name(self):
        self.assertEqual(self.parsed_period.name, "1st Quartal")

    def test_earnings_category_sum(self):
        self.assertAlmostEqual(self.parsed_period._earnings_model.category_sum(
            CategoryItem.DEFAULT_NAME), 456.78, places=5)

    def test_expenses_category_sum(self):
        self.assertAlmostEqual(self.parsed_period._expenses_model.category_sum(
            "Car"), 24999, places=5)

class TinyDbPeriodTestCase(unittest.TestCase):
    def setUp(self):
        self.filepath = "678.json"
        self.period = TinyDbPeriod(self.filepath)
        self.period.add_entry(name="Bicycle", value=999.99)

    def test_find_entry(self):
        self.assertIsInstance(self.period.find_entry(name="Bicycle")[0],
                database.Element)

    def test_remove_entry(self):
        self.period.remove_entry(category=None)
        self.assertEqual(0, len(self.period))

    def tearDown(self):
        os.remove(self.filepath)

if __name__ == '__main__':
    unittest.main()
