import os
import yaml
from modules.constants import CONFIGS_DIRECTORY

gpsr_configs = {}

def gpsr_load_configs():
    global gpsr_configs
    gpsr_configs = []
    gpsr_dir = os.path.join(CONFIGS_DIRECTORY, "GPSR")
    if os.path.exists(gpsr_dir):
        for filename in os.listdir(gpsr_dir):
            if filename.endswith(".yml") and not os.path.isdir(os.path.join(gpsr_dir, filename)):
                with open(os.path.join(gpsr_dir, filename), "r") as file:
                    config = yaml.safe_load(file)
                    gpsr_configs.append(config)
    return gpsr_configs

def gpsr_get_configs():
    global gpsr_configs
    if not gpsr_configs:
        gpsr_load_configs()
    return gpsr_configs

def gpsr_load_template(template_name):
    template_path = os.path.join(CONFIGS_DIRECTORY, "GPSR", "Templates", template_name + ".txt")
    if os.path.exists(template_path):
        with open(template_path, "r") as file:
            return file.read()
    return ""

def gpsr_process_template(template_name, template_data):
    template_content = gpsr_load_template(template_name)
    html_content = template_content
    for key, value in template_data.items():
        placeholder = "{" + key + "}"
        html_content = html_content.replace(placeholder, value)
    return html_content
