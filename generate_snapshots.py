"""
generate_snapshots.py
Generates realistic, timestamped snapshot datasets for 108 SKUs across 3 categories
and 6 subcategories matching Blinkit's JSON API response format.

Categories & Subcategories:
1. Dairy, Bread & Eggs (Milk & Cream, Bread & Bakery)
2. Snacks & Munchies (Chips & Crisps, Biscuits & Cookies)
3. Cold Drinks & Juices (Soft Drinks & Sodas, Juices & Fruit Drinks)

Generates 3 sequential timestamped snapshots (T1, T2, T3) to support
time-aware analysis, recurring stock-out risk detection, and price tracking.
"""

import os
import json
from datetime import datetime, timedelta

# Base catalog: 108 realistic SKUs across 3 categories and 6 subcategories
CATALOG = [
    # -------------------------------------------------------------
    # Category 1: Dairy, Bread & Eggs | Subcategory 1: Milk & Cream (18 SKUs)
    # -------------------------------------------------------------
    {"id": "1001", "name": "Amul Moti Toned Milk (90 Days Shelf Life)", "brand": "Amul", "cat": "Dairy, Bread & Eggs", "subcat": "Milk & Cream", "ptype": "Toned Milk", "variant": "450 ml", "mrp": 33, "price": 33, "rating": 4.50, "inv": 45, "recurring_oos": False},
    {"id": "1002", "name": "Amul Taaza Homogenised Toned Milk", "brand": "Amul", "cat": "Dairy, Bread & Eggs", "subcat": "Milk & Cream", "ptype": "Toned Milk", "variant": "500 ml", "mrp": 28, "price": 28, "rating": 4.65, "inv": 60, "recurring_oos": False},
    {"id": "1003", "name": "Amul Gold Full Cream Fresh Milk", "brand": "Amul", "cat": "Dairy, Bread & Eggs", "subcat": "Milk & Cream", "ptype": "Full Cream Milk", "variant": "500 ml", "mrp": 34, "price": 34, "rating": 4.75, "inv": 8, "recurring_oos": True},
    {"id": "1004", "name": "Mother Dairy Toned Milk", "brand": "Mother Dairy", "cat": "Dairy, Bread & Eggs", "subcat": "Milk & Cream", "ptype": "Toned Milk", "variant": "500 ml", "mrp": 28, "price": 28, "rating": 4.55, "inv": 35, "recurring_oos": False},
    {"id": "1005", "name": "Mother Dairy Live Lite Cow Milk", "brand": "Mother Dairy", "cat": "Dairy, Bread & Eggs", "subcat": "Milk & Cream", "ptype": "Cow Milk", "variant": "500 ml", "mrp": 30, "price": 30, "rating": 4.40, "inv": 20, "recurring_oos": False},
    {"id": "1006", "name": "Mother Dairy Full Cream Milk", "brand": "Mother Dairy", "cat": "Dairy, Bread & Eggs", "subcat": "Milk & Cream", "ptype": "Full Cream Milk", "variant": "500 ml", "mrp": 34, "price": 34, "rating": 4.60, "inv": 12, "recurring_oos": True},
    {"id": "1007", "name": "Country Delight Pure Cow Milk", "brand": "Country Delight", "cat": "Dairy, Bread & Eggs", "subcat": "Milk & Cream", "ptype": "Cow Milk", "variant": "500 ml", "mrp": 42, "price": 39, "rating": 4.70, "inv": 15, "recurring_oos": False},
    {"id": "1008", "name": "Country Delight Buffalo Milk", "brand": "Country Delight", "cat": "Dairy, Bread & Eggs", "subcat": "Milk & Cream", "ptype": "Buffalo Milk", "variant": "500 ml", "mrp": 48, "price": 45, "rating": 4.60, "inv": 10, "recurring_oos": False},
    {"id": "1009", "name": "Nestle A+ Nourish Toned Milk", "brand": "Nestle", "cat": "Dairy, Bread & Eggs", "subcat": "Milk & Cream", "ptype": "Toned Milk", "variant": "1 L", "mrp": 105, "price": 98, "rating": 4.45, "inv": 25, "recurring_oos": False},
    {"id": "1010", "name": "Nestle A+ Slim Skimmed Milk", "brand": "Nestle", "cat": "Dairy, Bread & Eggs", "subcat": "Milk & Cream", "ptype": "Skimmed Milk", "variant": "1 L", "mrp": 115, "price": 109, "rating": 4.30, "inv": 18, "recurring_oos": False},
    {"id": "1011", "name": "Sudha Dairy Shakti Fresh Milk", "brand": "Sudha Dairy", "cat": "Dairy, Bread & Eggs", "subcat": "Milk & Cream", "ptype": "Fresh Milk", "variant": "500 ml", "mrp": 31, "price": 31, "rating": 4.55, "inv": 30, "recurring_oos": False},
    {"id": "1012", "name": "Sudha Dairy Gold Full Cream Milk", "brand": "Sudha Dairy", "cat": "Dairy, Bread & Eggs", "subcat": "Milk & Cream", "ptype": "Full Cream Milk", "variant": "500 ml", "mrp": 34, "price": 34, "rating": 4.50, "inv": 22, "recurring_oos": False},
    {"id": "1013", "name": "Nandini Toned Fresh Milk", "brand": "Nandini", "cat": "Dairy, Bread & Eggs", "subcat": "Milk & Cream", "ptype": "Toned Milk", "variant": "500 ml", "mrp": 26, "price": 26, "rating": 4.60, "inv": 40, "recurring_oos": False},
    {"id": "1014", "name": "Nandini Special Full Cream Milk", "brand": "Nandini", "cat": "Dairy, Bread & Eggs", "subcat": "Milk & Cream", "ptype": "Full Cream Milk", "variant": "500 ml", "mrp": 32, "price": 32, "rating": 4.52, "inv": 14, "recurring_oos": False},
    {"id": "1015", "name": "Amul Fresh Malai Cream", "brand": "Amul", "cat": "Dairy, Bread & Eggs", "subcat": "Milk & Cream", "ptype": "Fresh Cream", "variant": "250 ml", "mrp": 67, "price": 65, "rating": 4.68, "inv": 28, "recurring_oos": False},
    {"id": "1016", "name": "Mother Dairy Ultimate Curd", "brand": "Mother Dairy", "cat": "Dairy, Bread & Eggs", "subcat": "Milk & Cream", "ptype": "Curd", "variant": "400 g", "mrp": 35, "price": 35, "rating": 4.45, "inv": 32, "recurring_oos": False},
    {"id": "1017", "name": "Amul Masti Dahi Pouch", "brand": "Amul", "cat": "Dairy, Bread & Eggs", "subcat": "Milk & Cream", "ptype": "Curd", "variant": "400 g", "mrp": 35, "price": 35, "rating": 4.50, "inv": 50, "recurring_oos": False},
    {"id": "1018", "name": "Epigamia Greek Yogurt Natural", "brand": "Epigamia", "cat": "Dairy, Bread & Eggs", "subcat": "Milk & Cream", "ptype": "Yogurt", "variant": "90 g", "mrp": 60, "price": 54, "rating": 4.25, "inv": 16, "recurring_oos": False},

    # -------------------------------------------------------------
    # Category 1: Dairy, Bread & Eggs | Subcategory 2: Bread & Bakery (18 SKUs)
    # -------------------------------------------------------------
    {"id": "1019", "name": "Britannia 100% Whole Wheat Bread", "brand": "Britannia", "cat": "Dairy, Bread & Eggs", "subcat": "Bread & Bakery", "ptype": "Wheat Bread", "variant": "400 g", "mrp": 55, "price": 50, "rating": 4.40, "inv": 25, "recurring_oos": False},
    {"id": "1020", "name": "Britannia Daily Fresh White Bread", "brand": "Britannia", "cat": "Dairy, Bread & Eggs", "subcat": "Bread & Bakery", "ptype": "White Bread", "variant": "400 g", "mrp": 45, "price": 42, "rating": 4.35, "inv": 30, "recurring_oos": False},
    {"id": "1021", "name": "Britannia Healthy Slice Brown Bread", "brand": "Britannia", "cat": "Dairy, Bread & Eggs", "subcat": "Bread & Bakery", "ptype": "Brown Bread", "variant": "400 g", "mrp": 50, "price": 48, "rating": 4.30, "inv": 18, "recurring_oos": False},
    {"id": "1022", "name": "Harvest Gold White Bread", "brand": "Harvest Gold", "cat": "Dairy, Bread & Eggs", "subcat": "Bread & Bakery", "ptype": "White Bread", "variant": "400 g", "mrp": 45, "price": 45, "rating": 4.50, "inv": 6, "recurring_oos": True},
    {"id": "1023", "name": "Harvest Gold 100% Atta Bread", "brand": "Harvest Gold", "cat": "Dairy, Bread & Eggs", "subcat": "Bread & Bakery", "ptype": "Atta Bread", "variant": "450 g", "mrp": 60, "price": 55, "rating": 4.45, "inv": 14, "recurring_oos": False},
    {"id": "1024", "name": "Harvest Gold Bombay Pav", "brand": "Harvest Gold", "cat": "Dairy, Bread & Eggs", "subcat": "Bread & Bakery", "ptype": "Pav", "variant": "6 pcs", "mrp": 35, "price": 32, "rating": 4.60, "inv": 9, "recurring_oos": True},
    {"id": "1025", "name": "English Oven 100% Whole Wheat Bread", "brand": "English Oven", "cat": "Dairy, Bread & Eggs", "subcat": "Bread & Bakery", "ptype": "Wheat Bread", "variant": "400 g", "mrp": 60, "price": 55, "rating": 4.55, "inv": 20, "recurring_oos": False},
    {"id": "1026", "name": "English Oven Sandwich White Bread", "brand": "English Oven", "cat": "Dairy, Bread & Eggs", "subcat": "Bread & Bakery", "ptype": "White Bread", "variant": "400 g", "mrp": 50, "price": 48, "rating": 4.45, "inv": 22, "recurring_oos": False},
    {"id": "1027", "name": "English Oven Multigrain Bread", "brand": "English Oven", "cat": "Dairy, Bread & Eggs", "subcat": "Bread & Bakery", "ptype": "Multigrain Bread", "variant": "400 g", "mrp": 70, "price": 65, "rating": 4.62, "inv": 12, "recurring_oos": False},
    {"id": "1028", "name": "English Oven Burger Buns", "brand": "English Oven", "cat": "Dairy, Bread & Eggs", "subcat": "Bread & Bakery", "ptype": "Burger Buns", "variant": "4 pcs", "mrp": 40, "price": 38, "rating": 4.38, "inv": 15, "recurring_oos": False},
    {"id": "1029", "name": "Modern White Bread", "brand": "Modern", "cat": "Dairy, Bread & Eggs", "subcat": "Bread & Bakery", "ptype": "White Bread", "variant": "400 g", "mrp": 40, "price": 38, "rating": 4.10, "inv": 24, "recurring_oos": False},
    {"id": "1030", "name": "Modern 100% Whole Wheat Bread", "brand": "Modern", "cat": "Dairy, Bread & Eggs", "subcat": "Bread & Bakery", "ptype": "Wheat Bread", "variant": "400 g", "mrp": 50, "price": 48, "rating": 4.20, "inv": 17, "recurring_oos": False},
    {"id": "1031", "name": "The Baker's Dozen Wholewheat Sourdough", "brand": "The Baker's Dozen", "cat": "Dairy, Bread & Eggs", "subcat": "Bread & Bakery", "ptype": "Sourdough", "variant": "300 g", "mrp": 149, "price": 139, "rating": 4.70, "inv": 8, "recurring_oos": False},
    {"id": "1032", "name": "The Baker's Dozen Garlic Bread", "brand": "The Baker's Dozen", "cat": "Dairy, Bread & Eggs", "subcat": "Bread & Bakery", "ptype": "Garlic Bread", "variant": "200 g", "mrp": 129, "price": 115, "rating": 4.58, "inv": 11, "recurring_oos": False},
    {"id": "1033", "name": "Britannia Sweet Fruit Bun", "brand": "Britannia", "cat": "Dairy, Bread & Eggs", "subcat": "Bread & Bakery", "ptype": "Bun", "variant": "150 g", "mrp": 25, "price": 25, "rating": 4.25, "inv": 28, "recurring_oos": False},
    {"id": "1034", "name": "Harvest Gold Burger Buns", "brand": "Harvest Gold", "cat": "Dairy, Bread & Eggs", "subcat": "Bread & Bakery", "ptype": "Burger Buns", "variant": "4 pcs", "mrp": 38, "price": 35, "rating": 4.40, "inv": 19, "recurring_oos": False},
    {"id": "1035", "name": "Britannia Bake Toast Rusk", "brand": "Britannia", "cat": "Dairy, Bread & Eggs", "subcat": "Bread & Bakery", "ptype": "Rusk", "variant": "200 g", "mrp": 40, "price": 38, "rating": 4.60, "inv": 45, "recurring_oos": False},
    {"id": "1036", "name": "Britannia Gourmet Pizza Base", "brand": "Britannia", "cat": "Dairy, Bread & Eggs", "subcat": "Bread & Bakery", "ptype": "Pizza Base", "variant": "2 pcs", "mrp": 45, "price": 42, "rating": 4.15, "inv": 14, "recurring_oos": False},

    # -------------------------------------------------------------
    # Category 2: Snacks & Munchies | Subcategory 3: Chips & Crisps (18 SKUs)
    # -------------------------------------------------------------
    {"id": "2001", "name": "Lay's India's Magic Masala Potato Chips", "brand": "Lay's", "cat": "Snacks & Munchies", "subcat": "Chips & Crisps", "ptype": "Potato Chips", "variant": "50 g", "mrp": 20, "price": 20, "rating": 4.70, "inv": 5, "recurring_oos": True},
    {"id": "2002", "name": "Lay's American Style Cream & Onion Chips", "brand": "Lay's", "cat": "Snacks & Munchies", "subcat": "Chips & Crisps", "ptype": "Potato Chips", "variant": "50 g", "mrp": 20, "price": 20, "rating": 4.65, "inv": 55, "recurring_oos": False},
    {"id": "2003", "name": "Lay's Spanish Tomato Tango Chips", "brand": "Lay's", "cat": "Snacks & Munchies", "subcat": "Chips & Crisps", "ptype": "Potato Chips", "variant": "50 g", "mrp": 20, "price": 20, "rating": 4.50, "inv": 40, "recurring_oos": False},
    {"id": "2004", "name": "Lay's Classic Salted Potato Chips", "brand": "Lay's", "cat": "Snacks & Munchies", "subcat": "Chips & Crisps", "ptype": "Potato Chips", "variant": "50 g", "mrp": 20, "price": 20, "rating": 4.45, "inv": 35, "recurring_oos": False},
    {"id": "2005", "name": "Doritos Cheese Supreme Nachos", "brand": "Doritos", "cat": "Snacks & Munchies", "subcat": "Chips & Crisps", "ptype": "Nachos", "variant": "60 g", "mrp": 35, "price": 30, "rating": 4.55, "inv": 28, "recurring_oos": False},
    {"id": "2006", "name": "Doritos Sweet Chilli Flavour Nachos", "brand": "Doritos", "cat": "Snacks & Munchies", "subcat": "Chips & Crisps", "ptype": "Nachos", "variant": "60 g", "mrp": 35, "price": 30, "rating": 4.50, "inv": 24, "recurring_oos": False},
    {"id": "2007", "name": "Pringles Sour Cream & Onion Crisps", "brand": "Pringles", "cat": "Snacks & Munchies", "subcat": "Chips & Crisps", "ptype": "Potato Crisps", "variant": "107 g", "mrp": 125, "price": 115, "rating": 4.75, "inv": 16, "recurring_oos": False},
    {"id": "2008", "name": "Pringles Original Potato Crisps", "brand": "Pringles", "cat": "Snacks & Munchies", "subcat": "Chips & Crisps", "ptype": "Potato Crisps", "variant": "107 g", "mrp": 125, "price": 115, "rating": 4.60, "inv": 18, "recurring_oos": False},
    {"id": "2009", "name": "Too Yumm! Karare Munchy Masala", "brand": "Too Yumm!", "cat": "Snacks & Munchies", "subcat": "Chips & Crisps", "ptype": "Extruded Snacks", "variant": "70 g", "mrp": 20, "price": 18, "rating": 4.30, "inv": 32, "recurring_oos": False},
    {"id": "2010", "name": "Too Yumm! Veggie Stix Cheese & Herbs", "brand": "Too Yumm!", "cat": "Snacks & Munchies", "subcat": "Chips & Crisps", "ptype": "Veggie Stix", "variant": "65 g", "mrp": 25, "price": 22, "rating": 4.20, "inv": 26, "recurring_oos": False},
    {"id": "2011", "name": "Bingo! Mad Angles Tedhe Medhe", "brand": "Bingo!", "cat": "Snacks & Munchies", "subcat": "Chips & Crisps", "ptype": "Triangle Chips", "variant": "90 g", "mrp": 20, "price": 20, "rating": 4.52, "inv": 45, "recurring_oos": False},
    {"id": "2012", "name": "Bingo! Mad Angles Achaari Masti", "brand": "Bingo!", "cat": "Snacks & Munchies", "subcat": "Chips & Crisps", "ptype": "Triangle Chips", "variant": "66 g", "mrp": 20, "price": 20, "rating": 4.40, "inv": 38, "recurring_oos": False},
    {"id": "2013", "name": "Kurkure Masala Munch Crisps", "brand": "Kurkure", "cat": "Snacks & Munchies", "subcat": "Chips & Crisps", "ptype": "Corn Puffs", "variant": "85 g", "mrp": 20, "price": 20, "rating": 4.68, "inv": 50, "recurring_oos": False},
    {"id": "2014", "name": "Kurkure Green Chutney Style", "brand": "Kurkure", "cat": "Snacks & Munchies", "subcat": "Chips & Crisps", "ptype": "Corn Puffs", "variant": "85 g", "mrp": 20, "price": 20, "rating": 4.45, "inv": 30, "recurring_oos": False},
    {"id": "2015", "name": "Uncle Chipps Spicy Treat Potato Chips", "brand": "Uncle Chipps", "cat": "Snacks & Munchies", "subcat": "Chips & Crisps", "ptype": "Potato Chips", "variant": "50 g", "mrp": 20, "price": 20, "rating": 4.62, "inv": 28, "recurring_oos": False},
    {"id": "2016", "name": "Act II Butter Lovers Microwave Popcorn", "brand": "Act II", "cat": "Snacks & Munchies", "subcat": "Chips & Crisps", "ptype": "Popcorn", "variant": "70 g", "mrp": 40, "price": 36, "rating": 4.58, "inv": 22, "recurring_oos": False},
    {"id": "2017", "name": "4700BC Himalayan Salt Caramel Popcorn", "brand": "4700BC", "cat": "Snacks & Munchies", "subcat": "Chips & Crisps", "ptype": "Gourmet Popcorn", "variant": "60 g", "mrp": 99, "price": 85, "rating": 4.65, "inv": 14, "recurring_oos": False},
    {"id": "2018", "name": "Haldiram's Bhujia Sev Namkeen", "brand": "Haldiram's", "cat": "Snacks & Munchies", "subcat": "Chips & Crisps", "ptype": "Namkeen", "variant": "200 g", "mrp": 60, "price": 55, "rating": 4.70, "inv": 42, "recurring_oos": False},

    # -------------------------------------------------------------
    # Category 2: Snacks & Munchies | Subcategory 4: Biscuits & Cookies (18 SKUs)
    # -------------------------------------------------------------
    {"id": "2019", "name": "Parle-G Original Gluco Biscuits", "brand": "Parle", "cat": "Snacks & Munchies", "subcat": "Biscuits & Cookies", "ptype": "Glucose Biscuit", "variant": "250 g", "mrp": 25, "price": 24, "rating": 4.80, "inv": 70, "recurring_oos": False},
    {"id": "2020", "name": "Britannia Good Day Cashew Cookies", "brand": "Britannia", "cat": "Snacks & Munchies", "subcat": "Biscuits & Cookies", "ptype": "Cookies", "variant": "200 g", "mrp": 45, "price": 40, "rating": 4.65, "inv": 48, "recurring_oos": False},
    {"id": "2021", "name": "Britannia Good Day Butter Cookies", "brand": "Britannia", "cat": "Snacks & Munchies", "subcat": "Biscuits & Cookies", "ptype": "Cookies", "variant": "200 g", "mrp": 40, "price": 36, "rating": 4.55, "inv": 40, "recurring_oos": False},
    {"id": "2022", "name": "Britannia Bourbon Chocolate Biscuits", "brand": "Britannia", "cat": "Snacks & Munchies", "subcat": "Biscuits & Cookies", "ptype": "Cream Biscuit", "variant": "150 g", "mrp": 35, "price": 32, "rating": 4.60, "inv": 35, "recurring_oos": False},
    {"id": "2023", "name": "Britannia Marie Gold Tea Biscuits", "brand": "Britannia", "cat": "Snacks & Munchies", "subcat": "Biscuits & Cookies", "ptype": "Tea Biscuit", "variant": "250 g", "mrp": 38, "price": 35, "rating": 4.50, "inv": 55, "recurring_oos": False},
    {"id": "2024", "name": "Sunfeast Dark Fantasy Choco Fills", "brand": "Sunfeast", "cat": "Snacks & Munchies", "subcat": "Biscuits & Cookies", "ptype": "Filled Cookies", "variant": "300 g", "mrp": 160, "price": 139, "rating": 4.75, "inv": 20, "recurring_oos": False},
    {"id": "2025", "name": "Sunfeast Mom's Magic Cashew & Almond", "brand": "Sunfeast", "cat": "Snacks & Munchies", "subcat": "Biscuits & Cookies", "ptype": "Cookies", "variant": "200 g", "mrp": 50, "price": 45, "rating": 4.52, "inv": 30, "recurring_oos": False},
    {"id": "2026", "name": "Oreo Original Vanilla Creme Cookies", "brand": "Oreo", "cat": "Snacks & Munchies", "subcat": "Biscuits & Cookies", "ptype": "Sandwich Cookies", "variant": "120 g", "mrp": 40, "price": 36, "rating": 4.70, "inv": 38, "recurring_oos": False},
    {"id": "2027", "name": "Oreo Double Stuf Chocolate Cookies", "brand": "Oreo", "cat": "Snacks & Munchies", "subcat": "Biscuits & Cookies", "ptype": "Sandwich Cookies", "variant": "130 g", "mrp": 50, "price": 45, "rating": 4.62, "inv": 24, "recurring_oos": False},
    {"id": "2028", "name": "Parle Hide & Seek Chocolate Chip", "brand": "Parle", "cat": "Snacks & Munchies", "subcat": "Biscuits & Cookies", "ptype": "Choco Chip", "variant": "120 g", "mrp": 40, "price": 38, "rating": 4.68, "inv": 29, "recurring_oos": False},
    {"id": "2029", "name": "Parle Monaco Salted Crackers", "brand": "Parle", "cat": "Snacks & Munchies", "subcat": "Biscuits & Cookies", "ptype": "Crackers", "variant": "200 g", "mrp": 35, "price": 32, "rating": 4.45, "inv": 44, "recurring_oos": False},
    {"id": "2030", "name": "Parle Krackjack Sweet & Salty", "brand": "Parle", "cat": "Snacks & Munchies", "subcat": "Biscuits & Cookies", "ptype": "Crackers", "variant": "200 g", "mrp": 35, "price": 32, "rating": 4.40, "inv": 42, "recurring_oos": False},
    {"id": "2031", "name": "Cadbury Chocobakes Choc Layered Cakes", "brand": "Cadbury", "cat": "Snacks & Munchies", "subcat": "Biscuits & Cookies", "ptype": "Layered Cakes", "variant": "126 g", "mrp": 60, "price": 54, "rating": 4.65, "inv": 19, "recurring_oos": False},
    {"id": "2032", "name": "McVitie's Digestive Wholewheat Biscuits", "brand": "McVitie's", "cat": "Snacks & Munchies", "subcat": "Biscuits & Cookies", "ptype": "Digestive", "variant": "250 g", "mrp": 75, "price": 68, "rating": 4.58, "inv": 26, "recurring_oos": False},
    {"id": "2033", "name": "Unibic Choco Chip Cookies", "brand": "Unibic", "cat": "Snacks & Munchies", "subcat": "Biscuits & Cookies", "ptype": "Cookies", "variant": "150 g", "mrp": 60, "price": 49, "rating": 4.42, "inv": 22, "recurring_oos": False},
    {"id": "2034", "name": "Unibic Butter Cookies", "brand": "Unibic", "cat": "Snacks & Munchies", "subcat": "Biscuits & Cookies", "ptype": "Cookies", "variant": "150 g", "mrp": 55, "price": 45, "rating": 4.38, "inv": 18, "recurring_oos": False},
    {"id": "2035", "name": "Britannia Treat Jim Jam Cream Biscuits", "brand": "Britannia", "cat": "Snacks & Munchies", "subcat": "Biscuits & Cookies", "ptype": "Jam Biscuit", "variant": "150 g", "mrp": 35, "price": 33, "rating": 4.55, "inv": 34, "recurring_oos": False},
    {"id": "2036", "name": "Sunfeast Bounce Choco Creme Biscuits", "brand": "Sunfeast", "cat": "Snacks & Munchies", "subcat": "Biscuits & Cookies", "ptype": "Cream Biscuit", "variant": "100 g", "mrp": 20, "price": 19, "rating": 4.28, "inv": 36, "recurring_oos": False},

    # -------------------------------------------------------------
    # Category 3: Cold Drinks & Juices | Subcategory 5: Soft Drinks & Sodas (18 SKUs)
    # -------------------------------------------------------------
    {"id": "3001", "name": "Coca-Cola Original Taste Bottle", "brand": "Coca-Cola", "cat": "Cold Drinks & Juices", "subcat": "Soft Drinks & Sodas", "ptype": "Cola", "variant": "750 ml", "mrp": 45, "price": 45, "rating": 4.70, "inv": 5, "recurring_oos": True},
    {"id": "3002", "name": "Coca-Cola Zero Sugar Soft Drink Can", "brand": "Coca-Cola", "cat": "Cold Drinks & Juices", "subcat": "Soft Drinks & Sodas", "ptype": "Cola", "variant": "300 ml", "mrp": 40, "price": 38, "rating": 4.55, "inv": 25, "recurring_oos": False},
    {"id": "3003", "name": "Thums Up Charged Strong Taste", "brand": "Thums Up", "cat": "Cold Drinks & Juices", "subcat": "Soft Drinks & Sodas", "ptype": "Cola", "variant": "750 ml", "mrp": 45, "price": 45, "rating": 4.75, "inv": 8, "recurring_oos": True},
    {"id": "3004", "name": "Thums Up Toofani Can", "brand": "Thums Up", "cat": "Cold Drinks & Juices", "subcat": "Soft Drinks & Sodas", "ptype": "Cola", "variant": "300 ml", "mrp": 40, "price": 38, "rating": 4.60, "inv": 30, "recurring_oos": False},
    {"id": "3005", "name": "Sprite Crisp Lemon Lime Flavoured Drink", "brand": "Sprite", "cat": "Cold Drinks & Juices", "subcat": "Soft Drinks & Sodas", "ptype": "Lemon Soda", "variant": "750 ml", "mrp": 45, "price": 45, "rating": 4.65, "inv": 42, "recurring_oos": False},
    {"id": "3006", "name": "Diet Coke No Sugar Can", "brand": "Coca-Cola", "cat": "Cold Drinks & Juices", "subcat": "Soft Drinks & Sodas", "ptype": "Diet Cola", "variant": "300 ml", "mrp": 40, "price": 38, "rating": 4.45, "inv": 20, "recurring_oos": False},
    {"id": "3007", "name": "Pepsi Cola Refreshing Taste Bottle", "brand": "Pepsi", "cat": "Cold Drinks & Juices", "subcat": "Soft Drinks & Sodas", "ptype": "Cola", "variant": "750 ml", "mrp": 45, "price": 42, "rating": 4.50, "inv": 35, "recurring_oos": False},
    {"id": "3008", "name": "Pepsi Black Zero Sugar Soda Can", "brand": "Pepsi", "cat": "Cold Drinks & Juices", "subcat": "Soft Drinks & Sodas", "ptype": "Diet Cola", "variant": "300 ml", "mrp": 40, "price": 36, "rating": 4.40, "inv": 22, "recurring_oos": False},
    {"id": "3009", "name": "Limca Fresh Lemoni Fizz Drink", "brand": "Limca", "cat": "Cold Drinks & Juices", "subcat": "Soft Drinks & Sodas", "ptype": "Lemon Soda", "variant": "750 ml", "mrp": 45, "price": 45, "rating": 4.58, "inv": 32, "recurring_oos": False},
    {"id": "3010", "name": "Fanta Orange Fizzy Flavoured Drink", "brand": "Fanta", "cat": "Cold Drinks & Juices", "subcat": "Soft Drinks & Sodas", "ptype": "Orange Soda", "variant": "750 ml", "mrp": 45, "price": 45, "rating": 4.52, "inv": 28, "recurring_oos": False},
    {"id": "3011", "name": "Mountain Dew Darr Ke Aage Jeet Hai", "brand": "Mountain Dew", "cat": "Cold Drinks & Juices", "subcat": "Soft Drinks & Sodas", "ptype": "Citrus Soda", "variant": "750 ml", "mrp": 45, "price": 42, "rating": 4.60, "inv": 36, "recurring_oos": False},
    {"id": "3012", "name": "7UP Nimbooz Real Lemon Juice Soda", "brand": "7UP", "cat": "Cold Drinks & Juices", "subcat": "Soft Drinks & Sodas", "ptype": "Lemon Drink", "variant": "250 ml", "mrp": 20, "price": 20, "rating": 4.42, "inv": 40, "recurring_oos": False},
    {"id": "3013", "name": "Schweppes Indian Tonic Water Can", "brand": "Schweppes", "cat": "Cold Drinks & Juices", "subcat": "Soft Drinks & Sodas", "ptype": "Tonic Water", "variant": "300 ml", "mrp": 60, "price": 55, "rating": 4.48, "inv": 18, "recurring_oos": False},
    {"id": "3014", "name": "Schweppes Ginger Ale Can", "brand": "Schweppes", "cat": "Cold Drinks & Juices", "subcat": "Soft Drinks & Sodas", "ptype": "Ginger Ale", "variant": "300 ml", "mrp": 60, "price": 55, "rating": 4.50, "inv": 16, "recurring_oos": False},
    {"id": "3015", "name": "Red Bull Energy Drink Regular Can", "brand": "Red Bull", "cat": "Cold Drinks & Juices", "subcat": "Soft Drinks & Sodas", "ptype": "Energy Drink", "variant": "250 ml", "mrp": 125, "price": 120, "rating": 4.80, "inv": 25, "recurring_oos": False},
    {"id": "3016", "name": "Monster Energy Drink Green Can", "brand": "Monster Energy", "cat": "Cold Drinks & Juices", "subcat": "Soft Drinks & Sodas", "ptype": "Energy Drink", "variant": "350 ml", "mrp": 125, "price": 115, "rating": 4.68, "inv": 20, "recurring_oos": False},
    {"id": "3017", "name": "Sting Energy Drink Pet Bottle", "brand": "Sting", "cat": "Cold Drinks & Juices", "subcat": "Soft Drinks & Sodas", "ptype": "Energy Drink", "variant": "250 ml", "mrp": 20, "price": 20, "rating": 4.55, "inv": 65, "recurring_oos": False},
    {"id": "3018", "name": "Bisleri Club Soda Pet Bottle", "brand": "Bisleri", "cat": "Cold Drinks & Juices", "subcat": "Soft Drinks & Sodas", "ptype": "Club Soda", "variant": "750 ml", "mrp": 20, "price": 20, "rating": 4.35, "inv": 50, "recurring_oos": False},

    # -------------------------------------------------------------
    # Category 3: Cold Drinks & Juices | Subcategory 6: Juices & Fruit Drinks (18 SKUs)
    # -------------------------------------------------------------
    {"id": "3019", "name": "Real Fruit Power Mixed Fruit Juice", "brand": "Real", "cat": "Cold Drinks & Juices", "subcat": "Juices & Fruit Drinks", "ptype": "Fruit Juice", "variant": "1 L", "mrp": 140, "price": 125, "rating": 4.68, "inv": 7, "recurring_oos": True},
    {"id": "3020", "name": "Real Fruit Power Pomegranate Juice", "brand": "Real", "cat": "Cold Drinks & Juices", "subcat": "Juices & Fruit Drinks", "ptype": "Fruit Juice", "variant": "1 L", "mrp": 150, "price": 135, "rating": 4.60, "inv": 22, "recurring_oos": False},
    {"id": "3021", "name": "Real Fruit Power Alphonso Mango Juice", "brand": "Real", "cat": "Cold Drinks & Juices", "subcat": "Juices & Fruit Drinks", "ptype": "Fruit Juice", "variant": "1 L", "mrp": 130, "price": 115, "rating": 4.55, "inv": 26, "recurring_oos": False},
    {"id": "3022", "name": "Tropicana 100% Real Orange Juice", "brand": "Tropicana", "cat": "Cold Drinks & Juices", "subcat": "Juices & Fruit Drinks", "ptype": "Fruit Juice", "variant": "1 L", "mrp": 150, "price": 130, "rating": 4.65, "inv": 18, "recurring_oos": False},
    {"id": "3023", "name": "Tropicana Mixed Fruit Delight Juice", "brand": "Tropicana", "cat": "Cold Drinks & Juices", "subcat": "Juices & Fruit Drinks", "ptype": "Fruit Juice", "variant": "1 L", "mrp": 130, "price": 110, "rating": 4.48, "inv": 24, "recurring_oos": False},
    {"id": "3024", "name": "Tropicana Apple Delight Juice", "brand": "Tropicana", "cat": "Cold Drinks & Juices", "subcat": "Juices & Fruit Drinks", "ptype": "Fruit Juice", "variant": "1 L", "mrp": 130, "price": 110, "rating": 4.42, "inv": 20, "recurring_oos": False},
    {"id": "3025", "name": "Paper Boat Aamras Mango Drink", "brand": "Paper Boat", "cat": "Cold Drinks & Juices", "subcat": "Juices & Fruit Drinks", "ptype": "Fruit Drink", "variant": "250 ml", "mrp": 35, "price": 32, "rating": 4.70, "inv": 35, "recurring_oos": False},
    {"id": "3026", "name": "Paper Boat Lychee Drink", "brand": "Paper Boat", "cat": "Cold Drinks & Juices", "subcat": "Juices & Fruit Drinks", "ptype": "Fruit Drink", "variant": "250 ml", "mrp": 35, "price": 32, "rating": 4.62, "inv": 28, "recurring_oos": False},
    {"id": "3027", "name": "Paper Boat Anar Pomegranate Juice", "brand": "Paper Boat", "cat": "Cold Drinks & Juices", "subcat": "Juices & Fruit Drinks", "ptype": "Fruit Juice", "variant": "250 ml", "mrp": 40, "price": 36, "rating": 4.50, "inv": 20, "recurring_oos": False},
    {"id": "3028", "name": "Raw Pressery Cold Pressed Valencia Orange", "brand": "Raw Pressery", "cat": "Cold Drinks & Juices", "subcat": "Juices & Fruit Drinks", "ptype": "Cold Pressed Juice", "variant": "250 ml", "mrp": 100, "price": 90, "rating": 4.72, "inv": 12, "recurring_oos": False},
    {"id": "3029", "name": "Raw Pressery Pure Coconut Water", "brand": "Raw Pressery", "cat": "Cold Drinks & Juices", "subcat": "Juices & Fruit Drinks", "ptype": "Coconut Water", "variant": "200 ml", "mrp": 70, "price": 63, "rating": 4.58, "inv": 15, "recurring_oos": False},
    {"id": "3030", "name": "B Natural Mixed Fruit Juice", "brand": "B Natural", "cat": "Cold Drinks & Juices", "subcat": "Juices & Fruit Drinks", "ptype": "Fruit Juice", "variant": "1 L", "mrp": 130, "price": 110, "rating": 4.40, "inv": 25, "recurring_oos": False},
    {"id": "3031", "name": "B Natural Guava Gush Juice", "brand": "B Natural", "cat": "Cold Drinks & Juices", "subcat": "Juices & Fruit Drinks", "ptype": "Fruit Juice", "variant": "1 L", "mrp": 130, "price": 110, "rating": 4.52, "inv": 22, "recurring_oos": False},
    {"id": "3032", "name": "Maaza Mango Pulp Drink", "brand": "Maaza", "cat": "Cold Drinks & Juices", "subcat": "Juices & Fruit Drinks", "ptype": "Mango Drink", "variant": "600 ml", "mrp": 42, "price": 40, "rating": 4.65, "inv": 40, "recurring_oos": False},
    {"id": "3033", "name": "Slice Thickest Mango Drink", "brand": "Slice", "cat": "Cold Drinks & Juices", "subcat": "Juices & Fruit Drinks", "ptype": "Mango Drink", "variant": "600 ml", "mrp": 42, "price": 39, "rating": 4.50, "inv": 34, "recurring_oos": False},
    {"id": "3034", "name": "Frooti Fresh Mango Drink", "brand": "Frooti", "cat": "Cold Drinks & Juices", "subcat": "Juices & Fruit Drinks", "ptype": "Mango Drink", "variant": "600 ml", "mrp": 40, "price": 38, "rating": 4.55, "inv": 45, "recurring_oos": False},
    {"id": "3035", "name": "Minute Maid Pulpy Orange Fruit Drink", "brand": "Minute Maid", "cat": "Cold Drinks & Juices", "subcat": "Juices & Fruit Drinks", "ptype": "Orange Drink", "variant": "1 L", "mrp": 90, "price": 82, "rating": 4.60, "inv": 26, "recurring_oos": False},
    {"id": "3036", "name": "Epigamia Hazelnut Cold Coffee Shake", "brand": "Epigamia", "cat": "Cold Drinks & Juices", "subcat": "Juices & Fruit Drinks", "ptype": "Cold Coffee", "variant": "200 ml", "mrp": 50, "price": 45, "rating": 4.45, "inv": 16, "recurring_oos": False},
]


def build_snippet(item, snapshot_num, timestamp_str):
    """
    Builds a Blinkit JSON snippet format matching the real API response.
    Simulates inventory depletion, recurring stockouts, and price shifts across T1, T2, T3.
    """
    mrp = item["mrp"]
    base_price = item["price"]
    inv = item["inv"]
    rating = item["rating"]
    is_recurring = item["recurring_oos"]

    if snapshot_num == 1:
        # Baseline snapshot (T1): High availability, normal baseline prices
        current_inv = inv
        price = base_price
    elif snapshot_num == 2:
        # T2 (High demand period): Recurring OOS items drop to 0, some discounts introduced
        if is_recurring:
            current_inv = 0
        else:
            current_inv = max(0, inv - 10)
        
        # Apply promotional discount on select snacks & juices
        if item["cat"] in ["Snacks & Munchies", "Cold Drinks & Juices"] and int(item["id"]) % 3 == 0:
            price = max(10, int(base_price * 0.90))  # 10% promotional flash sale
        else:
            price = base_price
    else:
        # T3 (Restock & assortment shift period):
        # Chronic OOS items stay 0 or low; others restock or fluctuate
        if is_recurring:
            current_inv = 0 if int(item["id"]) % 2 == 1 else 2  # Chronic stockout pattern
        else:
            current_inv = inv + 5  # Restocked
        
        # Slight price adjustment
        if int(item["id"]) % 5 == 0:
            price = max(10, int(base_price * 0.95))
        else:
            price = base_price

    is_sold_out = (current_inv == 0)
    state = "out_of_stock" if is_sold_out else "available"

    snippet = {
        "widget_type": "product_card",
        "layout_config": {"section_count": 2, "layout_type": "grid"},
        "data": {
            "identity": {"id": item["id"]},
            "name": {"text": item["name"]},
            "display_name": {"text": item["name"]},
            "variant": {"text": item["variant"]},
            "is_sold_out": is_sold_out,
            "merchant_type": "express",
            "product_state": state,
            "rating": {"value": str(rating)}
        },
        "tracking": {
            "common_attributes": {
                "product_id": item["id"],
                "name": item["name"],
                "brand": item["brand"],
                "mrp": mrp,
                "price": price,
                "rating": str(rating),
                "inventory": current_inv,
                "currency": "INR",
                "ptype": item["ptype"],
                "quantity": 1,
                "state": state,
                "l0_category": item["cat"],
                "l1_category": item["subcat"],
                "l2_category": item["ptype"],
                "product_position": int(item["id"]) % 30 + 1,
                "widget_position": (int(item["id"]) % 10) + 1,
                "widget_variation_id": "global_product_listing"
            }
        }
    }
    return snippet


def generate_all_snapshots():
    os.makedirs("data/raw", exist_ok=True)
    base_time = datetime.now() - timedelta(days=2)
    
    generated_files = []

    # Generate 3 sequential snapshots (e.g., Day 1 10:00 AM, Day 2 10:00 AM, Day 3 10:00 AM)
    for i, day_offset in enumerate([0, 1, 2], start=1):
        snapshot_time = base_time + timedelta(days=day_offset, hours=2)
        timestamp_str = snapshot_time.strftime("%Y-%m-%d_%H-%M-%S")
        
        snippets = [build_snippet(item, i, timestamp_str) for item in CATALOG]
        
        output_data = {
            "scrape_timestamp": snapshot_time.isoformat(),
            "snapshot_sequence": i,
            "product_count": len(snippets),
            "categories_covered": 3,
            "subcategories_covered": 6,
            "response": {
                "snippets": snippets
            }
        }

        filename = f"data/raw/blinkit_snapshot_{timestamp_str}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2)
        
        print(f"Generated Snapshot T{i}: {filename} with {len(snippets)} SKUs")
        generated_files.append(filename)

    print(f"\nSuccessfully generated {len(generated_files)} timestamped snapshots across 108 SKUs, 3 categories, and 6 subcategories.")
    return generated_files


if __name__ == "__main__":
    generate_all_snapshots()
