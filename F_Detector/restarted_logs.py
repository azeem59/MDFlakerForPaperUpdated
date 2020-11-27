import os
from pathlib import Path

import pymongo
from trace_cover import log_analyzer, trace_analyzer
from show import save_csv
import re


def connect_MG(db_name):
    myclient = pymongo.MongoClient("mongodb://localhost:27017/")
    dblist = myclient.list_database_names()
    mydb = myclient["local"]
    restarted_logs = mydb[db_name]
    return restarted_logs


def get_failed_tests(log):
    label_error = False
    failed_tests = []
    traceback = {}
    temp_failed_test = ''
    log = re.split(r'[\r\n]', log)

    for line in log:
        reaesc = re.compile(r'\x1b[^m]*m')
        line = reaesc.sub('', line)  # remove ANSI escape code
        line = line.strip()
        # print(line)
        if line.startswith("FAIL:") or line.startswith('[fail]') or line.endswith('FAILED'):
            # print('1: '+line)
            failed_test = log_analyzer(line)
            if failed_test not in failed_tests and failed_test['test_case'] != 'NULL':
                temp_failed_test = failed_test['test_case']
                traceback[temp_failed_test] = []
                failed_tests.append(failed_test)
            label_error = False
        elif line.startswith('======') and not (re.findall('[a-zA-z0-9]', line)):
            # print('2: ' + line)
            label_error = True
        elif line.startswith('ERROR:') and label_error:
            # print('3: ' + line)
            failed_test = log_analyzer(line)
            if failed_test not in failed_tests and failed_test['test_case'] != 'NULL':
                temp_failed_test = failed_test['test_case']
                traceback[temp_failed_test] = []
                failed_tests.append(failed_test)
            label_error = False
        elif line.startswith('FAILED') and 'failures=' not in line and 'errors=' not in line and '::' in line:
            failed_test = log_analyzer(line)
            if failed_test not in failed_tests and failed_test['test_case'] != 'NULL':
                temp_failed_test = failed_test['test_case']
                traceback[temp_failed_test] = []
                failed_tests.append(failed_test)
            label_error = False
        elif temp_failed_test != '' and (
                re.findall(r'.+[0-9][:][ ]in[ ].+', line) or re.findall(r'.+[0-9][,][ ]in[ ].+', line)):
            reaesc = re.compile(r'\x1b[^m]*m')
            line = reaesc.sub('', line)  # remove ANSI escape code
            trace = trace_analyzer(line)
            traceback[temp_failed_test].append(trace)

    return failed_tests, traceback


def get_flaky_tests():
    query_flaky_jobs = {'old.repoLanguage': 'Python', 'old.state': 'failed', 'new.state': 'passed'}
    restarted_jobs = connect_MG('restarted_jobs')
    jobs = restarted_jobs.find(query_flaky_jobs)
    restarted_logs = connect_MG('restarted_logs')
    failed_tests_count = 0
    failed_jobs_count = 0
    flaky_jobs_list = []
    repo = set()
    failed_tests = set()
    for job in jobs:
        flaky_job_dic = job['old']
        # print(job['id'])
        query_flaky_log = {'id': job['id']}
        flaky_job = restarted_logs.find(query_flaky_log)
        if flaky_job.count() > 0 and 'logDiff' in flaky_job[0].keys() and flaky_job[0]['logDiff']:
            failed_jobs_count += 1
            flaky_log = flaky_job[0]['logDiff']
            failed_tests_list, traceback = get_failed_tests(flaky_log)
            if failed_tests_list and failed_tests_list[0]['test_case'] != 'NULL':
                for f in failed_tests_list:
                    failed_tests.add(str(flaky_job_dic['repository_id']) + f['test_case'])
                repo.add(flaky_job_dic['repository_slug'])
                flaky_job_dic['failed_tests'] = failed_tests_list
                flaky_job_dic['traceback'] = traceback
                flaky_jobs_list.append(flaky_job_dic)
                failed_tests_count += len(failed_tests_list)
                print(failed_tests_count)
    headers = ['Job Id', 'Flaky Test Case Name', 'Path', 'Repository Id', 'Repository Slug', 'Commit SHA', 'Traceback']
    file_path = Path(os.path.abspath(os.path.join(os.getcwd(), ".."))) / 'data' / 'flaky_tests.cvs'
    results = []
    for f in flaky_jobs_list:
        for flaky_test in f['failed_tests']:
            path = flaky_test['test_dir'] + flaky_test['test_file']
            temp = [f['id'], flaky_test['test_case'], path, f['repository_id'], f['repository_slug'], f['commit'],
                    str(f['traceback'])]
            results.append(temp)
    save_csv(file_path, headers, results)

    print("failed tests: " + str(len(failed_tests)))
    print("flaky repo: " + str(len(repo)))
    print("failed jobs: " + str(failed_jobs_count))
    print("flaky jobs: " + str(len(flaky_jobs_list)))
    print("flaky tests: " + str(failed_tests_count))


if __name__ == '__main__':
    get_flaky_tests()
    # query = {"id": 597319722}
    # restarted_logs = connect_MG('restarted_logs')
    # log = restarted_logs.find(query)
    # print(log.count())
    # failed_log = log[0]['logDiff']
    # failed_tests_list = get_failed_tests(failed_log)
    # print(failed_tests_list)
