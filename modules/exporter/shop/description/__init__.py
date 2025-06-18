from .general import export_general_description
from .details import export_details
from .downloads import export_downloads
from modules.constants import TECHDATA
from modules.parser.gpsr import gpsr_get_configs, gpsr_process_template

def unescape_bsvp(text, prod_fields):
    text = text.replace("$Artikelname$", prod_fields["NAME"])
    text = text.replace("$Artikelnumber$", prod_fields["ARTNR"])
    text = text.replace("$LP$", prod_fields["PRICE"])
    return text

def export_description(parameters):
    prod_fields = parameters["prod_fields"]
    ilugg_fields = parameters["ilugg_fields"]

    description = "<!--description-->"
    description += export_general_description(parameters)
    description += "<!--/description-->"
    description += "<!--details-->"
    if (TECHDATA in prod_fields and prod_fields[TECHDATA]):
        description += export_details(parameters)
    description += "<!--/details-->"
    description += "<!--downloads-->"
    description += export_downloads(prod_fields, ilugg_fields)
    description += "<!--/downloads-->"

    description += gpsr_render_description(prod_fields)

    return unescape_bsvp(description, prod_fields)


def gpsr_render_description(prod_fields):
    tech_data = prod_fields.get("TECHDATA", {})
    gpsr = tech_data.get("0000435", "").lower()
    if gpsr != "ja":
        return ""

    result = {}

    # Sort configs by priority (higher number, higher priority).
    # Templates with higher priority overwrite templates with lower.
    sorted_configs = sorted(gpsr_get_configs(), 
                           key=lambda config: config.get("Priority", 0))
    
    for config in sorted_configs:
        conditions_met = True
        conditions = config.get("Conditions", {})
        for field, value in conditions.items():
            field_value = tech_data.get(field, "")
            if str(field_value).lower() != str(value).lower():
                conditions_met = False
                break
        if conditions_met:
            for name, data in config.get("Templates", {}).items():
                result[name] = gpsr_process_template(name, data)

    if len(result) == 0:
        return ""

    description = "<!--gpsr-->"
    description += result.get("Lieferant", "")
    description += result.get("Hersteller", "")
    description += result.get("Download", "")
    description += "<!--/gpsr-->"

    return description.replace('\n', '').replace('\r', '')
