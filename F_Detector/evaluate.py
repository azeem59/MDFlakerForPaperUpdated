import csv

from mysql_handler import *
import json
from sklearn.neighbors import KNeighborsClassifier
from sklearn import metrics
import pandas as pd
import numpy as np
import seaborn as sns

np.random.seed(1)


def save_csv(file_path, headers, rows):
    with open(file_path, 'w', encoding='utf8', newline='') as f:
        f_csv = csv.writer(f)
        f_csv.writerow(headers)
        for row in rows:
            f_csv.writerow(row)
        print('save data to csv done!')


def get_dataset(rerun_history_json_path):
    headers = ['Test Case Name', 'Build ID', 'Flaky Frequency', 'Dependency Coverage',
               'Test Smells', 'Previous State', 'Test Size', 'Flaky or Not']
    csv_name = 'dataset.csv'
    with open(rerun_history_json_path, 'r') as f:
        rerun_history = json.load(f)
        data = []
        for build_id, failed_tests in rerun_history.items():
            for test_name, v in failed_tests.items():
                if test_name not in ['commit_sha', 'previous_state', 'py_file_changes', 'other_file_changes']:
                    smells = 0
                    if v['smell'] is not None:
                        smells = len(v['smell'])
                    size = v['size']

                    if v['diff'] == 'F':
                        dependency = 0
                    else:
                        dependency = 1

                    flaky_frequency = search_flaky_frequency(test_name, build_id)
                    if len(flaky_frequency) == 0:
                        ff = 0.25
                    else:
                        ff = flaky_frequency[0][0]
                    pre_state = search_previous_state(build_id)[0][0]
                    if pre_state == 'passed':
                        previous_state = 0
                    elif pre_state == 'failed':
                        previous_state = 1
                    elif pre_state == 'None':
                        previous_state = 2
                    else:
                        previous_state = 3
                    flaky = 0
                    if v['failed_times'] != 30:
                        flaky = 1
                    res = [test_name, build_id, ff, dependency, smells, previous_state, size, flaky]
                    data.append(res)
        save_csv(csv_name, headers, data)


def get_previous_passed_dataset(rerun_history_json_path):
    headers = ['Test Case Name', 'Build ID', 'Dependency Coverage', 'Flaky or Not']
    csv_name = 'previous_passed_dataset.csv'
    with open(rerun_history_json_path, 'r') as f:
        rerun_history = json.load(f)
        data = []
        for build_id, failed_tests in rerun_history.items():
            if True:
                m = 0
                n = 0
                for test_name, v in failed_tests.items():
                    if test_name not in ['commit_sha', 'previous_state', 'py_file_changes', 'other_file_changes']:
                        flaky = 0
                        n += 1
                        # print(build_id, test_name)
                        if v['failed_times'] != 30:
                            flaky = 1
                            m += 1
                        temp = [test_name, build_id, v['diff'], flaky]
                        data.append(temp)
                print(build_id, n, m, failed_tests['previous_state'])
        # save_csv(csv_name, headers, data)


def read_data(data_path):
    data = pd.read_csv(data_path, header=1)
    # print(data)
    data_array = np.array(data)
    # l = []
    # for d in data_array:
    #     if d[2] == 0:
    #         l.append(d[0])
    # print(len(l))
    x_data = np.array(data_array[1:, 2:7], dtype=int)
    # print(x_data)
    # y_target = [int(i) for i in data_array[1:, 2:3]]
    y_target = np.array(data_array[1:, 7:8], dtype=int)
    y_target = y_target.ravel()
    headers = ['Number of Failures', 'Dependency Coverage',
               'Test Smells', 'Test Size', 'Previous State', 'Flaky or Not']
    # save_csv('spaCy_data.csv', headers, x_data)

    return x_data, y_target


def KNN(data_path):
    t1 = time.time()
    x_data, y_target = read_data(data_path)
    print(x_data.shape)
    # print(y_target.shape)
    indices = np.random.permutation(len(x_data))
    x_train = x_data[indices[:-200]]
    y_train = y_target[indices[:-200]]
    print(len(x_train))
    print(len(y_train))
    # print(x_train)
    x_test = x_data[indices[-80:]]
    y_test = y_target[indices[-80:]]
    print(len(x_test))
    print(len(y_test))
    knn = KNeighborsClassifier(8, p=1)
    knn.fit(x_train, y_train)
    y_predict = knn.predict(x_test)
    print("predict = ")
    print(y_predict)
    # neighborpoint = knn.kneighbors(x_test, 5, False)
    # print("latest test sample:", neighborpoint)
    score = knn.score(x_test, y_test, sample_weight=None)

    print("test = ")
    print(y_test)
    # probility = knn.predict_proba(x_test)
    # print("probility: ", probility)

    print("Accuracy: ", score)
    precision = metrics.precision_score(y_test, y_predict, average='micro')
    print("precision: ", precision)
    recall = metrics.recall_score(y_test, y_predict)
    print("recall: ", recall)
    f1 = metrics.f1_score(y_test, y_predict)
    print("F1 score: ", f1)
    confusion_matrix = metrics.confusion_matrix(y_predict, y_test)
    print("confusion_matrix: ")
    print(confusion_matrix)
    # kappa = metrics.cohen_kappa_score(y_test, y_predict)
    # print("kappa score: ", kappa)
    t2 = time.time()
    print(str(t2 - t1))


def dependency_flakiness_relation(csv_dataset_path):
    data = pd.read_csv(csv_dataset_path, header=1)
    data_array = np.array(data)
    size = len(data)
    print("total number: ", size)
    flakiness = 0
    non_flakiness = 0
    flakiness_F = 0
    flakiness_T = 0
    non_flakiness_F = 0
    non_flakiness_T = 0
    for d in data_array:
        if d[3] == 1:
            flakiness += 1
            if d[2] == 'F':
                flakiness_F += 1
            else:
                flakiness_T += 1
        else:
            non_flakiness += 1
            if d[2] == 'F':
                non_flakiness_F += 1
            else:
                non_flakiness_T += 1
    print("total flaky tests: ", flakiness)
    print("flaky tests and dependency cover equals False: ", flakiness_F, float(flakiness_F / flakiness))
    print("flaky tests and dependency cover equals True: ", flakiness_T, float(flakiness_T / flakiness))
    print("total non_flaky tests: ", non_flakiness)
    print("non_flaky tests with dependency cover equals False: ", non_flakiness_F,
          float(non_flakiness_F / non_flakiness))
    print("non_flaky tests with dependency cover equals True: ", non_flakiness_T,
          float(non_flakiness_T / non_flakiness))


def traceback_flakiness_all(csv_path):
    data = pd.read_csv(csv_path, header=1)
    data_array = np.array(data)
    size = len(data)
    print("total number: ", size)
    flakiness = 0
    non_flakiness = 0
    flakiness_F = 0
    flakiness_T = 0
    non_flakiness_F = 0
    non_flakiness_T = 0

    for f in data_array:
        if f[7] == 1:
            flakiness += 1
            if f[2] == 0:
                flakiness_F += 1
            else:
                flakiness_T += 1
        elif f[7] == 0:
            non_flakiness += 1
            if f[2] == 0:
                non_flakiness_F += 1
            else:
                non_flakiness_T += 1

    print("total flaky tests: ", flakiness)
    print("flaky tests and dependency cover equals False: ", flakiness_F, float(flakiness_F / flakiness))
    print("flaky tests and dependency cover equals True: ", flakiness_T, float(flakiness_T / flakiness))
    print("total non_flaky tests: ", non_flakiness)
    print("non_flaky tests with dependency cover equals False: ", non_flakiness_F,
          float(non_flakiness_F / non_flakiness))
    print("non_flaky tests with dependency cover equals True: ", non_flakiness_T,
          float(non_flakiness_T / non_flakiness))


def show_data(data_path):
    x_data, y_target = read_data(data_path)
    sns.set(style="white", color_codes=True)
    data = pd.DataFrame(x_data)
    iris = pd.merge(data, pd.DataFrame(y_target, columns=['species']), left_index=True, right_index=True)
    sns.pairplot(iris, hue='species', height=3, diag_kind='kde')


def compare_rerun_10_30(path10, path30):
    with open(path10, 'r') as f:
        rerun_10 = json.load(f)

    with open(path30, 'r') as f:
        rerun_30 = json.load(f)
    rerun_10_dic = {}
    rerun_30_dic = {}
    if rerun_10 and rerun_30:
        for build, tests in rerun_10.items():
            m = 0
            for test, info in tests.items():
                if test.startswith('test'):
                    m += 1
            rerun_10_dic[build] = m
        for build, tests in rerun_30.items():
            n = 0
            for test, info in tests.items():
                if test.startswith('test'):
                    n += 1
            rerun_30_dic[build] = n
    for build, n in rerun_10_dic.items():
        print(build, n)
        # for k, v in rerun_30_dic.items():
        #     if build == k:
        #         print(n, v)


def rerun_30(path30):
    with open(path30, 'r') as f:
        rerun = json.load(f)
    rerun_30_dic = {}
    n = 0
    flakiness = 0
    for build, tests in rerun.items():

        for test, info in tests.items():
            if test.startswith('test') and len(info['traceback']) == 1:
                if info['failed_times'] != 30:
                    flakiness += 1
                else:
                    n += 1
    print(flakiness, n)


def multi_factor_flakiness_relation(csv_path):
    data = pd.read_csv(csv_path, header=1)
    data_array = np.array(data)
    flaky_smells = 0
    non_flaky_smells = 0
    flaky_tests = 0
    non_flaky_tests = 0
    flaky_size = 0
    non_flaky_size = 0
    flaky_failure = 0
    flaky_failure_count = 0
    non_flaky_failure = 0
    non_flaky_failure_count = 0
    flaky_size_list = []
    non_flaky_size_list = []
    for d in data_array:
        if d[7] == 1:
            flaky_smells += d[4]
            if d[2] != 0:
                flaky_failure += d[2]
                flaky_failure_count += 1
            flaky_size += d[6]
            flaky_size_list.append(d[6])
            flaky_tests += 1
        else:
            non_flaky_smells += d[4]
            if d[2] != 0:
                non_flaky_failure += d[2]
                non_flaky_failure_count += 1
            non_flaky_size += d[6]
            non_flaky_size_list.append(d[6])
            non_flaky_tests += 1
    # print("flaky size list: ", flaky_size_list)
    # print("non-flaky size list: ", non_flaky_size_list)
    print("flaky tests: ", flaky_tests)
    print("flaky smells: ", flaky_smells)
    print("flaky size: ", flaky_size)
    print("flaky failures: ", flaky_failure)
    print("\n")
    print("non-flaky tests: ", non_flaky_tests)
    print("non-flaky smells: ", non_flaky_smells)
    print("non-flaky size: ", non_flaky_size)
    print("non-flaky failures: ", non_flaky_failure)
    print("\n")
    print("avg flaky size: ", float(flaky_size / flaky_tests))
    print("avg flaky smells: ", float(flaky_smells / flaky_tests))
    print("avg flaky failure: ", float(flaky_failure / flaky_failure_count))
    print("\n")
    print("avg non-flaky size: ", float(non_flaky_size / non_flaky_tests))
    print("avg non-flaky smells: ", float(non_flaky_smells / non_flaky_tests))
    print("avg non-flaky failures: ", float(non_flaky_failure / non_flaky_failure_count))


def find_new_failure(csv_path):
    data = pd.read_csv(csv_path, header=1)
    data_array = np.array(data)
    new_failure = 0
    for d in data_array:
        failed_test = d[0]
        if len(get_failed_test(failed_test)) == 0:
            new_failure += 1
            if d[7] != 1:
                print("not flaky")

    print(new_failure)


if __name__ == '__main__':
    path = r'D:\CoursesResources\MasterThesis\multifactorftdetector\data\spaCy_rerun_history.json'
    slug = 'explosion/spaCy'
    dataset_path = r'D:\CoursesResources\MasterThesis\multifactorftdetector\F_Detector\spaCy_dataset.csv'
    previous_passed_path = r'D:\CoursesResources\MasterThesis\multifactorftdetector\data\spaCy_rerun_history.json'
    dfr = r'D:\CoursesResources\MasterThesis\multifactorftdetector\F_Detector\previous_passed_dataset.csv'
    get_dataset(path)
    KNN(dataset_path)
    # read_date(dataset_path)
    # show_data(dataset_path)
    # get_previous_passed_dataset(previous_passed_path)
    # dependency_flakiness_relation(dfr)
    # traceback_flakiness_all(dataset_path)
    # rerun_30(previous_passed_path)
    # compare_rerun_10_30(path, previous_passed_path)
    # multi_factor_flakiness_relation(dataset_path)
    # find_new_failure(dataset_path)
