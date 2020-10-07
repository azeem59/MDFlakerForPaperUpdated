import time
import re
import os
import subprocess


def get_diff(commit_sha, project_path):
    os.chdir(project_path)
    diff_command = 'git diff ' + commit_sha + "^^!"  # why it works with ^^, not ^ ???

    result = subprocess.Popen(diff_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output = result.stdout.readlines()
    m = 0
    change_dic = {}
    temp_file = ''
    py_found = True
    change_dic['diff'] = 'Y'
    if not output:
        change_dic['diff'] = 'N'

    for line in output:
        line = str(line, encoding="utf-8")
        line.strip()
        # line.replace('\n', '')
        # print(line)
        m += 1

        if line.startswith('+++') and line.endswith('.py\n'):
            # print(line)
            temp_file = re.findall(r'[/](.+?[.]py)', line)[0]
            change_dic[temp_file] = []
            py_found = True

        elif line.startswith('@@') and py_found:
            change_list = []
            num = re.findall(r'[+](.+?[ ])', line)[0]
            num_list = re.split(r'[,]', num)
            start = int(num_list[0])
            end = int(num_list[0]) + int(num_list[1])
            change_list.append(start)
            change_list.append(end)
            change_dic[temp_file].append(change_list)

        elif line.startswith('+++') or line.startswith('---') and not line.endswith('.py\n'):
            py_found = False

    return change_dic


if __name__ == '__main__':
    sha = 'd0d28e3a04f0d17fed90dc59fc634bffe4f3ac79'
    path = r'D:\CoursesResources\MasterThesis\Python_projects\incubator-superset'
    get_diff(sha, path)
