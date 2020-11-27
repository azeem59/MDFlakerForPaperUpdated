import csv
import json
import re
import os
import subprocess
import time
from pathlib import Path
from show import save_csv
from mysql_handler import search


def checkout_commit(commit_sha, project_path):
    os.chdir(project_path)
    command = 'git checkout ' + commit_sha  # why it works with ^^, not ^ ???

    # result = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # output = result.stdout.readlines()
    output = subprocess.call(command, shell=False)
    return output


def rerun_tests_spacy(project_path):
    os.chdir(project_path)
    # checkout_commit(project_path, commit_sha)
    # command_create_env = 'virtualenv env2 --python=python2.7'
    # command_use_env = 'source env2/bin/activate'
    # command_update = 'pip install --upgrade pip'
    # command_requirements = 'pip install -r requirements.txt'
    # command_build = 'pip install -e .'
    # command_pytest = 'pip install pytest'
    # command_random_test = 'pip install pytest-randomly'
    # command_list = [command_create_env, command_use_env, command_update, command_requirements, command_build,
    #                 command_pytest, command_random_test]
    # for command in command_list:
    #     subprocess.call(command, shell=True)
    subprocess.call(r'.\env2\Scripts\activate', shell=True)
    command_run_tests = 'pytest --tb=native spacy'
    result = {}
    project_slug = 'explosion/spaCy'
    for i in range(1, 11):
        res = subprocess.Popen(command_run_tests, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        test_log = res.stdout.readlines()
        failed_tests, traceback = failed_test_from_log(test_log, project_slug)
        for f in failed_tests:
            if f['test_case'] not in result.keys():
                temp = {'failed_test': f, 'traceback': traceback[f['test_case']], 'failed_times': 1}
                result[f['test_case']] = temp
            else:
                result[f['test_case']]['failed_times'] += 1
    print(result)
    return result


def dict_to_json(project_name, save_path, res, build_id):
    json_name = project_name + '_rerun_history' + '.csv'
    abs_path = save_path / json_name
    if json_name in os.listdir(save_path):
        with open(abs_path, 'w') as pre:
            temp = json.load(pre)
            temp[build_id] = res
            json.dump(temp, pre, indent=4)
    else:
        with open(abs_path, 'w') as f:
            temp = {build_id: res}
            json.dump(temp, f, indent=4)
    print('save ' + str(build_id) + ' to json file done!')


def build_to_rerun(project_name, save_path):
    t1 = time.time()
    sql = """SELECT ft.FAILED_TEST_NAME,ft.build_id,ft.DEPENDENCY_COVER,bh.previous_state,bh.commit_sha
             FROM failed_tests ft JOIN build_history bh
             ON ft.build_id = bh.build_id
             WHERE git_diff="Y"
             GROUP BY build_id
             ORDER BY bh.created_time"""
    res = search(sql)
    csv_name = project_name + '_rerun_build' + '.csv'
    abs_path = Path(save_path) / csv_name
    headers = ['Failed Test Case', 'Build ID', 'Dependency Cover', 'Previous State',
               'Commit SHA']
    save_csv(abs_path, headers, res)
    t2 = time.time()
    m, s = divmod(t2 - t1, 60)
    h, m = divmod(m, 60)
    print("total cost: %d:%02d:%02d" % (h, m, s))


if __name__ == '__main__':
    # commit = '7b33b2854f99ef531d72e19e6dda773f43a5fe13'
    # path = r'D:\CoursesResources\MasterThesis\Python_projects\spaCy'
    # rerun_tests_spacy(path)
    save_path = r'D:\CoursesResources\MasterThesis\multifactorftdetector\data\rerun_builds'
    project_name = 'spaCy'
    #build_to_rerun(project_name, save_path)

    with open(r'D:\CoursesResources\MasterThesis\multifactorftdetector\data\rerun_builds\spaCy_rerun_builds.csv','r') as f:
        res = csv.reader(f)
        for line in res:
            print(line[0])
