# import typer

# from clearconf.utils.file import find_cconf_config, load_cconf_config, save_cconf_config
# from clearconf.utils.stdout import print_dict

# app = typer.Typer()

# @app.command()
# def add(script: str, config: str):
#     if config[-3:] != '.py':
#         print('Failed: Configurations have to be python files')
#         return

#     config = config[:-3]

#     cconf_conf_path = find_cconf_config()
#     cconf_conf = load_cconf_config(cconf_conf_path)

#     cconf_conf['defaults'][script] = config
#     save_cconf_config(cconf_conf, cconf_conf_path)


# @app.command()
# def remove(script):
#     cconf_conf_path = find_cconf_config()
#     cconf_conf = load_cconf_config(cconf_conf_path)

#     cconf_conf['defaults'].pop(script)
#     save_cconf_config(cconf_conf, cconf_conf_path)


# @app.command()
# def list():
#     cconf_conf_path = find_cconf_config()
#     cconf_conf = load_cconf_config(cconf_conf_path)

#     print_dict(cconf_conf['defaults'])