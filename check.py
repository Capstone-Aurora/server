import os


def dependency_check(fileName):
    dir_path = os.path.dirname(os.path.realpath(__file__))
    data_path = dir_path + "/data"
    my_file_path = os.path.join(data_path, fileName)

    # result_path = dir_path + "/results"
    # if not os.path.isdir(dir_path):
    #     os.mkdir(dir_path)
    # code_file_path = os.path.join(result_path, fileName)

    dependency_list = []
    myfile = open(my_file_path, "r")
    code = myfile.read()
    myfile.close()

    code = code + "hahaha"

    # with open(code_file_path, "w") as codefile:
    #     codefile.write(code)

    return code
