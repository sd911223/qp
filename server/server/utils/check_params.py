import yaml


class ParamsCheck:
    """参数检查类"""

    def __init__(self, check_yml_path):
        print(check_yml_path)
        self.__check_ = self.__init_func(yaml.load(open(check_yml_path),Loader=yaml.FullLoader))

    def __init_func(self, check_params):
        result = {}
        for interface_name, interface_content in check_params.items():
            result_cell = {}
            if interface_content is None:
                result[interface_name] = result_cell
                continue

            for params_name, conf in interface_content.items():
                if not result_cell.get(params_name):
                    result_cell[params_name] = {}

                if type(conf) is str:
                    result_cell[params_name]["type"] = eval(conf)

                elif type(conf) is dict:
                    trans_type = conf.get("type")
                    if type:
                        result_cell[params_name]["type"] = eval(trans_type)

            result[interface_name] = result_cell

        return result

    def check_params(self, parmas_name, data):
        result = {}

        params_list = self.__check_.get(parmas_name)
        if params_list is None:
            print("WARN:" + parmas_name + " not config check information!")
            return True, result

        if not params_list:
            return not data, result

        is_correct = True
        for name, conf in params_list.items():
            value = data.get(name)
            if value is None:
                continue

            try:
                result[name] = conf["type"](value)
            except TypeError as error_info:
                print(error_info)
                break

        return is_correct, result

