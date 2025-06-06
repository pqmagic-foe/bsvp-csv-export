import os
import csv
import json
import logging
import math
import time
from datetime import datetime
from pytz import utc
from collections import OrderedDict
import traceback

from apscheduler.schedulers.background import BackgroundScheduler
from modules.constants import GENERAL_CONFIG_FILE, MANUFACTURER_ENDING, \
    MANUFACTURER_INFO_ENDING, PRODUCT_ENDING, \
    CONFIGURATOR_NAME, GAMBIO_NAME, SHOP_NAME, PRICE_NAME, COMPLETE_NAME, \
    DATA_DIRECTORY, CUSTOM_NAME
from modules.parser.gpsr import gpsr_load_configs

from modules.parser.prod import parse_product
from modules.parser.ilugg import parse_manufacturer_information
from modules.exporter.configurator import ConfiguratorExporter
from modules.exporter.gambio import GambioExporter
from modules.exporter.complete import CompleteExporter
from modules.exporter.shop import ShopExporter
from modules.exporter.price import PriceExporter
from modules.exporter.custom import CustomExporter
from modules.logger import Logger

def write_skip_log(logger, file, error):
    logger.log(file + ": " + error)


def parse_manufacturers():
    bsvp_directory = DATA_DIRECTORY

    manufacturers = OrderedDict()
    for manufacturer_directory in os.listdir(bsvp_directory):
        if not manufacturer_directory.endswith(MANUFACTURER_ENDING):
            continue

        manufacturer_path = bsvp_directory + manufacturer_directory
        manufacturer_name = manufacturer_directory.split(MANUFACTURER_ENDING)[0]
        manufacturers[manufacturer_name] = {
            "path": manufacturer_path,
            "products": {}
        }

        for product_directory in os.listdir(manufacturer_path):
            if not product_directory.endswith(PRODUCT_ENDING) or product_directory == PRODUCT_ENDING:
                continue
            product_name = product_directory.split(PRODUCT_ENDING)[0]
            product_path = "/".join([
                manufacturer_path,
                product_directory,
                product_directory
            ])
            manufacturers[manufacturer_name]["products"][product_name] = product_path

    return manufacturers

def get_manufacturer_information(manufacturer_path, manufacturer_name):
    ilugg_path = manufacturer_path + "/" + manufacturer_name + MANUFACTURER_INFO_ENDING
    if not os.path.exists(ilugg_path):
        return None, "NICHT_VORHANDEN"
    manufacturer_information = parse_manufacturer_information(ilugg_path)
    if not manufacturer_information:
        return None, "NICHT_AUSWERTBAR"
    return manufacturer_information, None

def get_time():
    return time.strftime("%H:%M:%S", time.localtime())

class Runner:
    def setup(self):
        self.manufacturers = parse_manufacturers()
        with open(GENERAL_CONFIG_FILE, "r", encoding="utf-8") as config_file:
            config = json.load(config_file)
            self.max_products_per_file = config["max-articles-per-file"]

        gpsr_load_configs()

        self.exporters = {
            "configurator": {
                "module": ConfiguratorExporter(self.manufacturers),
                "scheduled": False,
                "running": False,
                "log": [],
                "name": CONFIGURATOR_NAME
            },
            "gambio": {
                "module": GambioExporter(self.manufacturers),
                "scheduled": False,
                "running": False,
                "log": [],
                "name": GAMBIO_NAME
            },
            "shop": {
                "module": ShopExporter(self.manufacturers),
                "scheduled": False,
                "running": False,
                "log": [],
                "name": SHOP_NAME
            },
            "price": {
                "module": PriceExporter(self.manufacturers),
                "scheduled": False,
                "running": False,
                "log": [],
                "name": PRICE_NAME
            },
            "complete": {
                "module": CompleteExporter(self.manufacturers),
                "scheduled": False,
                "running": False,
                "log": [],
                "name": COMPLETE_NAME
            },
            "custom": {
                "module": CustomExporter(self.manufacturers),
                "scheduled": False,
                "running": False,
                "log": [],
                "name": CUSTOM_NAME
            }
        }

        self.scheduler = BackgroundScheduler(timezone=utc)
        self.scheduler.add_job(
            func=self.check_tasks,
            trigger="interval",
            seconds=8,
            timezone="Europe/Berlin"
        )
        self.tasks = []
        self.scheduler.start()
        logging.getLogger('apscheduler').setLevel("ERROR")

        self.reloading = False

    def reload(self):
        self.reloading = True
        self.setup()

    def __init__(self):
        self.setup()

    def get_manufacturers(self):
        return list(self.manufacturers.keys())

    def get_exporters(self):
        # Module entfernen, kann (und soll) nicht mitgeschickt werden
        sendable_exporters = {}
        for exporter_key, exporter_values in self.exporters.items():
            last_export_date = exporter_values["module"].last_export_date(exporter_values["running"])
            if last_export_date != None:
                last_export_date = datetime.utcfromtimestamp(last_export_date).strftime("%d.%m.%Y")
            sendable_exporters[exporter_key] = {
                "name": exporter_values["name"],
                "scheduled": exporter_values["scheduled"],
                "running": exporter_values["running"],
                "log": exporter_values["log"],
                "last": last_export_date
            }
        return sendable_exporters

    def is_running(self):
        is_running = False
        for exporter_name, exporter_values in self.exporters.items():
            is_running = is_running or exporter_values["running"]
        return is_running

    def check_tasks(self):
        if not self.is_running() and len(self.tasks) > 0:
            self.run(self.tasks.pop(0))

    def add_task(self, exporter, selected_manufacturers):
        if self.reloading:
            return "RELOADING"
        if self.exporters[exporter]["scheduled"]:
            return "SCHEDULED"
        if self.exporters[exporter]["running"]:
            return "RUNNING"

        self.tasks.append({
            "exporter": exporter,
            "selected_manufacturers": selected_manufacturers
        })
        self.exporters[exporter]["scheduled"] = True
        self.exporters[exporter]["log"] = ["Export um {} zur Warteschlange hinzugefügt".format(get_time())]

        # Wenn Hersteller eingeschränkt werden können, sollen diese
        # angezeigt werden
        exporter_module = self.exporters[exporter]["module"]
        show_selected_manufacturers = exporter_module.skip_manufacturer("Not a manufacturer", selected_manufacturers)
        if show_selected_manufacturers:
            self.exporters[exporter]["log"].append(
                "Ausgewählte Hersteller: {}".format(", ".join(selected_manufacturers))
            )
        return None

    def split_large_result(self, exporter_module):
        output_directory = exporter_module.output_directory()
        for file_name in os.listdir(output_directory):
            with exporter_module.open_file(os.path.join(output_directory, file_name)) as file:
                csv_reader = exporter_module.get_csv_handler(
                    file, csv.DictReader)
                products = list(csv_reader)
                product_count = len(products)
                if product_count > self.max_products_per_file:
                    current_product_index = 0
                    while current_product_index < product_count:
                        current_product = products[current_product_index]
                        current_file_number = math.ceil(
                            (current_product_index + 1) / self.max_products_per_file)
                        current_file_name = file_name.replace(
                             ".csv", "_{}.csv".format(current_file_number))
                        current_file_path = os.path.join(
                            output_directory, current_file_name)
                        opening_mode = "a" if os.path.exists(
                            current_file_path) else "w"
                        with exporter_module.open_file(current_file_path, opening_mode) as current_file:
                            csv_writer = exporter_module.get_csv_handler(
                                current_file, csv.writer)
                            if opening_mode == "w":
                                csv_writer.writerow(current_product.keys())
                            csv_writer.writerow(current_product.values())
                        current_product_index += 1

    def run(self, task):
        exporter_id = task["exporter"]
        selected_manufacturers = task["selected_manufacturers"]
        exporter = self.exporters[exporter_id]
        exporter_module = exporter["module"]
        logger = Logger()
        logger.set_path(exporter_id)
        if not exporter["running"]:
            exporter["scheduled"] = False
            exporter["running"] = True

            start_text = "Export gestartet um {}".format(get_time())
            exporter["log"].append(start_text)
            logger.log("\n".join(exporter["log"]))
            exporter_module.setup()

            # Variablen für Log
            current_manufacturer = None
            current_product_number = None
            current_product_skips = None

            for manufacturer_name, manufacturer in self.manufacturers.items():
                # Log Variablen anpassen
                current_manufacturer = manufacturer_name
                current_product_number = 0
                current_product_skips = 0

                manufacturer_path = manufacturer["path"]
                if exporter_module.skip_manufacturer(manufacturer_name, selected_manufacturers):
                    continue

                logger.log("\n{}".format(current_manufacturer))
                exporter["log"].append(current_manufacturer)

                manufacturer_information = None
                if exporter_module.uses_manufacturer_information:
                    manufacturer_information, error_code = get_manufacturer_information(
                        manufacturer_path,
                        manufacturer_name
                    )
                    if error_code != None:
                        exporter["log"][-1] = "{} übersprungen, ILUGG Datei konnte nicht gelesen werden".format(current_manufacturer)
                        write_skip_log(logger, "ILUGG", error_code)
                        continue

                for product_name, product_path in manufacturer["products"].items():
                    current_product_number += 1
                    exporter["log"][-1] = "{} ({})".format(
                        current_manufacturer,
                        current_product_number
                    )
                    if not os.path.exists(product_path):
                        current_product_skips += 1
                        write_skip_log(logger, product_name, "PROD_UNTERSCHIEDLICH")
                        continue

                    fields, attribute_names, attribute_types, error_code = parse_product(product_path)
                    if error_code != None:
                        current_product_skips += 1
                        write_skip_log(logger, product_name, error_code)
                        continue

                    skip_product, error_code = exporter_module.skip_product(fields)
                    if error_code != None:
                        current_product_skips += 1
                        write_skip_log(logger, product_name, error_code)
                        continue
                    if skip_product:
                        continue

                    try:
                        error_code = exporter_module.write_to_csv({
                            "fields": fields,
                            "attribute_names": attribute_names,
                            "attribute_types": attribute_types,
                            "manufacturer_name": manufacturer_name,
                            "manufacturer_information": manufacturer_information
                        })
                    except Exception as exception:
                        print(traceback.format_exc(), flush=True)
                        error_code = str(exception)

                    if error_code != None:
                        current_product_skips += 1
                        write_skip_log(logger, product_name, error_code)

                manufacturer_summary = "{} gesamt, {} Fehler".format(
                    current_product_number,
                    current_product_skips
                )
                exporter["log"][-1] = "{} ({})".format(current_manufacturer, manufacturer_summary)
                logger.log(manufacturer_summary)

            # Export abschließen
            self.split_large_result(exporter_module)
            end_text = "Export beended um {}".format(get_time())
            exporter["log"].append(end_text)
            logger.log("\n" + end_text)
            exporter["running"] = False
