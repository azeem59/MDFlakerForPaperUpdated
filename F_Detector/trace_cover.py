import datetime
import traceback

import requests
import re
import time
import math
import json
import random
from changes_github import get_diff


class BuildAnalyzer:

    def __init__(self, build):
        self.commit_sha = build['commit']['sha']
        self.branch = build['branch']['name']
        self.author = build['commit']['author']['name']
        self.build_id = build['id']
        self.project_slug = build['repository']['slug']
        self.jobs = build['jobs']
        self.failed_jobs = []
        self.log_with_failed_tests = ''
        self.failed_tests = []
        # self.traceback_list = []
        self.traceback = {}  # {'failed_test': [[path, line, method], ...], ...}

        self.process()

    def process(self):
        self.get_failed_jobs()
        self.get_failed_tests()
        # if self.failed_tests:
        #     self.get_traceback()

    def get_failed_jobs(self):

        for job in self.jobs:
            if job['state'] == 'failed':
                self.failed_jobs.append(job['id'])

    def get_failed_tests(self):

        for job in self.failed_jobs:

            if not self.failed_tests:
                log_url = 'https://api.travis-ci.org/v3/job/' + str(job) + '/log.txt'
                wait = random.uniform(1, 2)
                time.sleep(wait)
                try:
                    log = requests.get(log_url).text
                    # log = r['content']

                    if log is None:
                        continue
                    else:
                        log = re.split(r'\r\n', log)
                        label_error = False
                        temp_failed_test = ''
                        for line in log:
                            line = line.strip()
                            if line.startswith("FAIL:") or line.startswith('[fail]') or line.endswith('FAILED'):
                                # print('1: '+line)
                                failed_test = log_analyzer(line)
                                if failed_test not in self.failed_tests and failed_test['test_case'] != 'NULL':
                                    temp_failed_test = failed_test['test_case']
                                    self.traceback[temp_failed_test] = []
                                    self.failed_tests.append(failed_test)
                                label_error = False

                            elif line.startswith('======') and not (re.findall('[a-zA-z0-9]', line)):
                                # print('2: ' + line)
                                label_error = True

                            elif line.startswith('ERROR:') and label_error and '.' in line:
                                # print('3: ' + line)
                                failed_test = log_analyzer(line)
                                if failed_test not in self.failed_tests and failed_test['test_case'] != 'NULL':
                                    temp_failed_test = failed_test['test_case']
                                    self.traceback[temp_failed_test] = []
                                    self.failed_tests.append(failed_test)
                                label_error = False

                            elif line.startswith(
                                    'FAILED') and 'failures=' not in line and 'errors=' not in line and '::' in line:
                                failed_test = log_analyzer(line)
                                if failed_test not in self.failed_tests and failed_test['test_case'] != 'NULL':
                                    temp_failed_test = failed_test['test_case']
                                    self.traceback[temp_failed_test] = []
                                    self.failed_tests.append(failed_test)
                                label_error = False

                            # get traceback of each failed test
                            elif temp_failed_test != '' and (
                                    re.findall(r'.+[0-9][:][ ]in[ ].+', line) or re.findall(r'.+[0-9][,][ ]in[ ].+',
                                                                                            line)):
                                reaesc = re.compile(r'\x1b[^m]*m')
                                line = reaesc.sub('', line)  # remove ANSI escape code
                                trace = trace_analyzer(line)
                                self.traceback[temp_failed_test].append(trace)
                            else:
                                continue

                        if self.failed_tests:
                            self.log_with_failed_tests = log
                except Exception as e:
                    print("error: " + str(e))
            else:
                break

    '''
    def get_traceback(self):

        log = self.log_with_failed_tests
        failed_tests = []
        for f in self.failed_tests:
            failed_tests.append(f['test_case'])
            # init self.traceback
            if f['test_case']:
                self.traceback[f['test_case']] = []

        failed_tests_number = len(failed_tests)
        m = 1
        temp_failed_test = failed_tests[0]
        next_failed_test = ''
        if failed_tests_number >= 2:
            next_failed_test = failed_tests[1]

        for line in log:
            if next_failed_test and next_failed_test in line:

                temp_failed_test = next_failed_test
                m += 1
                if m < failed_tests_number:
                    next_failed_test = failed_tests[m]

            if re.findall(r'.+[0-9][:][ ]in[ ].+', line) or re.findall(r'.+[0-9][,][ ]in[ ].+', line):
                reaesc = re.compile(r'\x1b[^m]*m')
                line = reaesc.sub('', line)  # remove ANSI escape code

                trace = trace_analyzer(line)
                if trace not in self.traceback[temp_failed_test]:
                    self.traceback[temp_failed_test].append(trace)
    '''


def trace_analyzer(line):
    if re.findall(r'.+[0-9][:][ ]in[ ].+', line):
        trace = re.split(r'[:]|[: ]| ', line)
        trace = [i for i in trace if i != '' and i != 'in']
        return trace  # a list: [path, line, method]

    else:
        trace = re.split(r'[:]|["]|[,]| ', line)
        trace = [i for i in trace if i != '' and i != 'in' and i != 'File' and i != 'line']
        return trace


def log_analyzer(line):
    test_case = 'NULL'
    test_class = 'NULL'
    test_file = 'NULL'
    test_dir = ''
    # format: 'ERROR: test_locust_client_error (locust.test.test_locust_class.TestWebLocustClass)'
    if '(' in line and '__' not in line:
        if re.findall(r' (.+?) ', line):
            test_case = re.findall(r' (.+?) ', line)[0]
        test_path_and_class = re.findall(r'[(](.+?)[)]', line)
        if len(test_path_and_class) > 0:
            test_list = re.split(r'[.]', test_path_and_class[0])
            if re.match('[A-Z]', test_list[len(test_list) - 1]):
                test_class = test_list[len(test_list) - 1]
                test_file = test_list[len(test_list) - 2] + '.py'
                for i in range(len(test_list) - 2):
                    test_dir += test_list[i] + '/'
            else:
                test_file = test_list[len(test_list) - 1] + '.py'
                for i in range(len(test_list) - 1):
                    test_dir += test_list[i] + '/'
    # format: 'FAIL: IPython.core.tests.test_oinspect.test_render_signature_long'
    elif '__' not in line and '(' not in line and '[' not in line and '::' not in line and '.' in line:
        test_list = re.split(r'[.]', re.split(r'[ ]', line)[1])
        test_list_len = len(test_list)

        if re.match('[A-Z]', test_list[test_list_len - 2]) and test_list_len > 2:
            test_case = test_list[test_list_len - 1]
            test_class = test_list[test_list_len - 2]
            test_file = test_list[test_list_len - 3] + '.py'
            for i in range(test_list_len - 3):
                test_dir += test_list[i] + '/'
        elif test_list_len > 1:
            test_case = test_list[test_list_len - 1]
            test_file = test_list[test_list_len - 2] + '.py'

            for i in range(test_list_len - 2):
                test_dir += test_list[i] + '/'
    # format: 'FAILED pandas/tests/plotting/test_frame.py::TestDataFramePlots::test_hist_plot_by_argument[A-by1]'
    # format: 'FAILED IPython/extensions/tests/test_autoreload.py::TestAutoreload::test_smoketest_autoreload'
    elif '::' in line and '%' not in line and '__' not in line and line.startswith('FAILED'):
        if '[' in line:
            test_info = re.findall('[ ](.+?)[[]', line)[0]
        elif ' - ' in line:
            test_info = re.findall('[ ](.+?) -', line)[0]
        else:
            test_info = re.findall('[ ](.+)', line)[0]
        test_list = re.split(r'[:][:]|[/]', test_info)
        test_list_len = len(test_list)
        if test_info.count(':') == 4 and test_list_len > 2:
            test_case = test_list[test_list_len - 1]
            test_class = test_list[test_list_len - 2]
            test_file = test_list[test_list_len - 3]
            for i in range(test_list_len - 3):
                test_dir += test_list[i] + '/'
        elif test_list_len > 1:
            test_case = test_list[test_list_len - 1]
            test_file = test_list[test_list_len - 2]
            for i in range(test_list_len - 2):
                test_dir += test_list[i] + '/'
    # format: '[fail] 2.53% tests_pandas.test_pandas_leave: 0.2674s'
    elif '%' in line and '[fail]' in line:
        test_info = re.findall('% (.+?)[:]', line)[0]
        test_list = re.split(r'[.]', test_info)
        test_case = test_list[1]
        test_file = test_list[0] + 'py'
    # format: '__________ CrawlerRunnerTestCase.test_spider_manager_verify_interface __________'
    elif '___' in line and '[' not in line:
        test_info = re.findall(' (.+?) ', line)[0]
        test_list = re.split(r'[.]', test_info)
        test_case = test_list[1]
        test_class = test_list[0]
    # format: '_____________ test_stacking_with_sample_weight[StackingClassifier] _____________'
    elif '___' in line and '[' in line:
        test_case = re.findall('[ ](.+?)[[]', line)[0]
        test_class = re.findall('[[](.+?)[]]', line)[0]
    # format: 'test/augmenters/test_weather.py::TestSnowflakes::test_very_roughly_no_channels FAILED'
    elif '::' in line and line.endswith('FAILED'):
        test_info = re.split(r'[ ]', line)[0]
        test_list = re.split(r'[/]|[:][:]', test_info)
        test_list_len = len(test_list)
        test_case = test_list[test_list_len - 1]
        if re.findall('[A-Z]', test_list[test_list_len - 2]) and test_list_len > 2:
            test_class = test_list[test_list_len - 2]
            test_file = test_list[test_list_len - 3]
            for i in range(test_list_len - 3):
                test_dir += test_list[i] + '/'
        elif test_list_len > 1:
            test_file = test_list[test_list_len - 2]
            for i in range(test_list_len - 2):
                test_dir += test_list[i] + '/'
    failed_test = {'test_case': test_case, 'test_class':
        test_class, 'test_file': test_file, 'test_dir': test_dir}
    return failed_test


def one_build(build_id):
    url = 'https://api.travis-ci.org/build/' + str(build_id)
    params = {'include': 'build.jobs,build.commit'}
    r = requests.get(url, headers={'Travis-API-Version': '3'}, params=params)
    build_history = r.json()
    # print(build_history)
    time1 = time.time()
    if build_history['state'] == 'passed':
        print('This build passed!')
        return 'passed'

    elif build_history['state'] == 'started':
        print('This build has not finished!!')
        return 'started'

    else:

        build = BuildAnalyzer(build_history)
        print(build.failed_tests)
        print(build.traceback)
        time2 = time.time()
        print('time:', str(time2 - time1))
        return build_history
        # for k, v in build.failed_jobs.items():
        #     print(k)
        #     print(v)


def diff_compare(project_path, sha, traceback):
    changes_dic = get_diff(sha, project_path)
    diff_dic = {}
    if changes_dic['diff'] == 'Y':
        diff_dic['diff'] = 'Y'
    else:
        diff_dic['diff'] = 'N'
    for test, trace in traceback.items():
        diff_dic[test] = 'F'
        for file, changes in changes_dic.items():
            for i in range(len(trace)):
                if file in trace[i][0] or trace[i][0] in file:
                    for change in changes:

                        if int(trace[i][1]) - change[0] >= 0 and int(trace[i][1]) - change[1] <= 0:
                            diff_dic[test] = 'T'

    return diff_dic


def get_all_builds(project_owner, project_name, interval=0):
    url = 'https://api.travis-ci.org/repo/' + project_owner + '%2F' + \
          project_name + '/builds'
    offset = 0
    now = datetime.datetime.now()
    date = now + datetime.timedelta(days=-interval)
    builds_list = []
    param1 = {'include': 'build.jobs,build.commit', 'limit': 1, 'build.event_type': 'push', 'build.branch': 'master'}
    first_build = requests.get(url, headers={'Travis-API-Version': '3'}, params=param1).json()
    count = first_build['@pagination']['count'] - 1  # if limit is 0, set limit max builds

    # build_number = 200
    t1 = time.time()
    print("getting build history from Travis ci......")
    UTC_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
    finish = False
    for _ in range(int(math.ceil(count / 100))):
        response = requests.session()
        response.keep_alive = False

        params = {'include': 'build.jobs,build.commit', 'limit': 100, 'offset': offset,
                  'build.event_type': 'push', 'build.branch': 'master'}
        if not finish:
            try:
                builds = response.get(url, headers={'Travis-API-Version': '3'}, params=params).json()
                for build in builds['builds']:
                    finish_at = datetime.datetime.strptime(build['finished_at'], UTC_FORMAT)
                    if finish_at >= date:
                        builds_list.append(build)
                    else:
                        finish = True
                        break
                # builds_list.extend(builds['builds'])
                offset += 100
                print("finish " + str(len(builds_list)) + " " + " builds")
            except Exception as e:
                print("error info: " + str(e))
                print(traceback.format_exc())

            finally:
                response.close()
                time.sleep(2)
        else:
            break

    t2 = time.time()
    print("got " + str(len(builds_list)) + " " + " builds")
    print("cost " + str(t2 - t1) + "seconds")

    build_dic = {}
    m = 1
    for build in builds_list:
        t1 = time.time()
        build_res = {'branch_name': build['branch']['name'], 'id': build['id'], 'state': build['state'],
                     'previous_state': build['previous_state'], 'commit_sha': build['commit']['sha'],
                     'duration': build['duration'], 'finished_at': build['finished_at'], 'failed_info': {}}

        if build['state'] == 'failed':

            build_ = BuildAnalyzer(build)
            if build_.failed_tests:
                build_info = {'commit_sha': build_.commit_sha, 'branch': build_.branch, 'build_id': build_.build_id,
                              'failed_tests': build_.failed_tests, 'traceback': build_.traceback}
                build_res['failed_info'] = build_info

        build_dic[str(build['id'])] = build_res

        t2 = time.time()
        print('extract build info, finish: ', m)
        m += 1
        print('time consumption: ', str(t2 - t1))

    return build_dic


def get_failed_tests(failed_builds_list):
    build_dic = dict()
    t1 = time.time()
    num = 0
    for build in failed_builds_list:
        num += 1
        print("finish " + str(num) + " builds: " + str(build['id']))
        build_ = BuildAnalyzer(build)
        if build_.failed_tests:
            build_info = {'commit_sha': build_.commit_sha, 'branch': build_.branch, 'build_id': build_.build_id,
                          'author': build_.author, 'failed_tests': build_.failed_tests, 'traceback': build_.traceback}
            build_dic[str(build_.build_id)] = build_info
    t2 = time.time()
    print("cost " + str(t2 - t1) + " seconds")
    return build_dic


def builds_to_json(project_owner, project_name, limit=0):
    # url = 'https://api.travis-ci.org/repo/' + project_owner + '%2F' + \
    #       project_name + '/builds'
    # offset = 0
    # builds_list = []
    # n = limit
    # param1 = {'include': 'build.jobs,build.commit', 'limit': 1, 'build.event_type': 'push'}
    # first_build = requests.get(url, headers={'Travis-API-Version': '3'}, params=param1).json()
    # if limit == 0:
    #     limit = first_build['@pagination']['count'] - 1  # if limit is 0, set limit max builds
    # if limit > 100:
    #     n = 100
    # for _ in range(int(math.ceil(limit / 100))):
    #     params = {'include': 'build.jobs,build.commit',
    #               'limit': n, 'offset': offset,
    #               'build.event_type': 'push'}  # only get the previous passed and now passed builds
    #     try:
    #         r = requests.get(url, headers={'Travis-API-Version': '3'}, params=params)
    #         builds_history = r.json()
    #         builds_list += builds_history['builds']  # change the data type to list
    #         offset += 100
    #         print("finish: " + str(len(builds_list)))
    #     except Exception as e:
    #         print("error info: " + str(e))
    #     finally:
    #         time.sleep(2)
    #
    # build_dic = {}
    # m = 1
    # for build in builds_list:
    #     t1 = time.time()
    #     build_res = {'branch_name': build['branch']['name'], 'id': build['id'], 'state': build['state'],
    #                  'previous_state': build['previous_state'], 'commit_sha': build['commit']['sha'],
    #                  'duration': build['duration'], 'finished_at': build['finished_at'], 'failed_info': {}}
    #
    #     if build['state'] == 'failed':
    #
    #         build_ = BuildAnalyzer(build)
    #         if build_.failed_tests:
    #             build_info = {'commit_sha': build_.commit_sha, 'branch': build_.branch, 'build_id': build_.build_id,
    #                           'failed_tests': build_.failed_tests, 'traceback': build_.traceback}
    #             build_res['failed_info'] = build_info
    #
    #     build_dic[str(build['id'])] = build_res
    #
    #     t2 = time.time()
    #     print('extract build info finish: ', m)
    #     m += 1
    #     print('time consumption: ', str(t2 - t1))
    build_dic = get_all_builds(project_owner, project_name, limit)
    json_name = project_name + '_build_history' + '.json'
    with open(json_name, 'w') as f:
        json.dump(build_dic, f, indent=4)


# def main():
#     parser = argparse.ArgumentParser()
#     parser.add_argument('integer', type=int, help='display an integer')
#     args = parser.parse_args()


if __name__ == '__main__':
    owner = 'apache'
    name = 'incubator-superset'
    build_id = '672776651'

    # build = one_build(build_id)
    # print(build)

    time1 = time.time()
    builds_to_json(owner, name, 100)
    time2 = time.time()
    print('total time: ', str(time2 - time1))
