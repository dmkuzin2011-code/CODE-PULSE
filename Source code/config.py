import json
import os
import re
from rich.console import Console
console=Console()
CONFIG={}
base_data={
    "user_local_name":None,
    "based_color":"#013220"
}
file_path="config.json"
def start_config_checkout():
    if not os.path.exists(file_path):
        with open(file_path, "w", encoding="utf-8") as file_beta:
            json.dump(base_data, file_beta)
    if os.path.exists(file_path):
        with open(file_path,"r",encoding="utf-8") as file_data:
            loaded=json.load(file_data)
            CONFIG.clear()
            CONFIG.update({**base_data,**loaded})
def save_config():
    global CONFIG
    with open(file_path,"w",encoding="utf-8") as file:
        json.dump(CONFIG,file)
def is_valid_hex(color:str)->bool:
    if not isinstance(color,str):
        return False
    return bool(re.match(r'#[0-9A-Fa-f]{6}$',color))
def config_cmd(args:list[str])->None:
    if not os.path.exists(file_path):
        with open(file_path,"w",encoding="utf-8") as file:
            json.dump(base_data,file)
    if not args:
        console.print(f"[{CONFIG["based_color"]}]Usage:config check[/]")
        return
    if args[0]=="check":
        if os.path.exists(file_path):
            with open(file_path,"r",encoding="utf-8") as file2:
                data=json.load(file2)
                console.print(f"[{CONFIG["based_color"]}]Your local name:{data["user_local_name"]}[/]")
                console.print(f"[{CONFIG["based_color"]}]Your based color:{data["based_color"]}[/]")
    elif args[0].startswith("theme="):
        color=args[0][len("theme="):]
        if not is_valid_hex(color):
            console.print("[red]Color error")
            return
        elif is_valid_hex(color):
            CONFIG["based_color"]=color
            save_config()
            return
    if args[0].startswith("localname="):
        name=args[0][len("localname="):]
        CONFIG["user_local_name"]=name
        save_config()
    else:
        console.print("[red]Unexpected argument[/]")