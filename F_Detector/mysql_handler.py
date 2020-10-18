import datetime
import time
import traceback
import pymysql
from get_test_smells import get_test_smell_project, get_size_file
from trace_cover import get_all_builds, get_failed_tests, diff_compare


def connect(host="localhost", user="root", pw="root", db="flakiness"):
    return pymysql.connect(host, user, pw, db)  # url,username,password,database


# create tables
def create_tables():
    db = connect()
    cur = db.cursor()
    cur.execute("drop table if exists build_history")
    cur.execute("drop table if exists test_smells")
    cur.execute("drop table if exists test_cases")
    cur.execute("drop table if exists failed_tests")
    cur.execute("drop table if exists total_builds")
    print("creating tables......")
    try:
        create_build_history = """CREATE TABLE build_history(
                                ID INT NOT NULL AUTO_INCREMENT  COMMENT 'id' ,
                                BUILD_ID VARCHAR(64) NOT NULL   COMMENT 'build_id' ,
                                BRANCH VARCHAR(128)    COMMENT 'branch' ,
                                DURATION VARCHAR(64)    COMMENT 'duration' ,
                                CREATED_TIME DATETIME    COMMENT 'CREATED_TIME' ,
                                STATUS INT    COMMENT 'status 0: passed; 1: failed; 2: failed with failed tests' ,
                                PREVIOUS_STATE VARCHAR(32)    COMMENT 'previous_state' ,
                                COMMIT_SHA VARCHAR(128)    COMMENT 'commit_sha' ,
                                PRIMARY KEY (ID)
                            )"""
        create_test_smells = """CREATE TABLE test_smells(
                                ID INT NOT NULL AUTO_INCREMENT  COMMENT 'id' ,
                                TEST_CASE_NAME VARCHAR(128)    COMMENT 'test_case_name' ,
                                TEST_SMELL_TYPE VARCHAR(32)    COMMENT 'test_smell_type' ,
                                TIP VARCHAR(64)    COMMENT 'tip' ,
                                LOCATION INT    COMMENT 'test_smell_location' ,
                                PATH VARCHAR(512)    COMMENT 'path' ,
                                CREATED_TIME DATETIME    COMMENT 'CREATED_TIME' ,
                                UPDATED_TIME DATETIME    COMMENT 'UPDATED_TIME' ,
                                PRIMARY KEY (ID)
                            )"""
        create_test_cases = """CREATE TABLE test_cases(
                                ID INT NOT NULL AUTO_INCREMENT  COMMENT 'id' ,
                                NAME VARCHAR(128)    COMMENT 'test_case_name' ,
                                PATH VARCHAR(512)    COMMENT 'PATH' ,
                                SIZE INT  DEFAULT 0  COMMENT 'size' ,
                                TEST_SMELLS INT  DEFAULT 0  COMMENT 'test_smell_number' ,
                                FLAKINESS_POSSIBILITY DECIMAL(4,2)    COMMENT 'flakiness_possibility' ,
                                CREATED_TIME DATETIME    COMMENT 'CREATED_TIME' ,
                                UPDATED_TIME DATETIME    COMMENT 'UPDATED_TIME' ,
                                ML_SCORE DECIMAL(4,2)  DEFAULT 0  COMMENT 'ML_score machine_learning score
                            Reserved Field' ,
                                PRIMARY KEY (ID)
                            )"""
        create_failed_tests = """CREATE TABLE failed_tests(
                                ID INT NOT NULL AUTO_INCREMENT  COMMENT 'id' ,
                                BUILD_ID VARCHAR(64) NOT NULL   COMMENT 'build_id build_history_fk' ,
                                FAILED_TEST_NAME VARCHAR(128) NOT NULL   COMMENT 'failed_test_name test_cases_fk' ,
                                PATH VARCHAR(512)    COMMENT 'path' ,
                                TRACEBACK TEXT   COMMENT 'traceback' ,
                                DEPENDENCY_COVER VARCHAR(1)    COMMENT 'dependency_cover' ,
                                GIT_DIFF VARCHAR(1)     COMMENT 'successfully got diff from github? Y(yes) or N(not) ',
                                FLAKINESS_POSSIBILITY DECIMAL(4,2)    COMMENT 'flakiness_possibility' ,
                                CREATED_TIME DATETIME    COMMENT 'created_time' ,
                                PRIMARY KEY (ID)
                            )"""
        # create_total_builds = """CREATE TABLE total_builds(
        #                         total INT NOT NULL   COMMENT 'total_builds' ,
        #                         passed INT    COMMENT 'passed_builds' ,
        #                         failed INT    COMMENT 'failed_builds' ,
        #                         failed_test INT    COMMENT 'failed_test_builds' ,
        #                         PRIMARY KEY (total)
        #                     )"""
        cur.execute(create_build_history)
        cur.execute(create_test_cases)
        cur.execute(create_failed_tests)
        cur.execute(create_test_smells)
        # cur.execute(create_total_builds)
        db.commit()
        print("tables created!")
    except Exception as e:
        print("operation error: " + str(e))
        print(traceback.format_exc())
        db.rollback()
        print("rollback!")
    finally:
        cur.close()
        db.close()


def save_case_and_smells(project_path):
    t1 = time.time()
    db = connect()
    t2 = time.time()
    print("db connected, cost " + str(t2 - t1) + " seconds")

    print("getting test smells......")
    project_smells = get_test_smell_project(project_path)
    t3 = time.time()
    print("get test smells succeed, cost " + str(t3 - t2) + " seconds")

    cur = db.cursor()
    test_file_number = 0
    test_smell_number = 0
    test_case_number = 0
    print("save data into db......")
    try:
        for file_path, smells in project_smells.items():
            size_dic = get_size_file(file_path)
            # save test case size
            dt = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            test_file_number += 1
            file_path = file_path.replace("\\", "\\\\")
            for test, size in size_dic.items():
                test_case_number += 1
                save_size = "INSERT INTO test_cases(NAME,PATH,SIZE,CREATED_TIME) \
                                values ('%s','%s','%d','%s')" % (test, file_path, size, dt)
                cur.execute(save_size)

            # update test smells
            dt2 = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            for smell in smells:
                if smell:
                    for name, smell_list in smell.items():
                        num = 0  # test smell number
                        for sm in smell_list:
                            num += len(sm[3])
                            # insert test smells into table test_smells
                            for location in sm[3]:
                                test_smell_number += 1
                                save_smells = "INSERT INTO test_smells(TEST_CASE_NAME,TEST_SMELL_TYPE,TIP,LOCATION," \
                                              "PATH," \
                                              "CREATED_TIME) values ('%s','%s','%s','%d','%s','%s')" % (
                                                  name, sm[0], sm[1], location, file_path, dt2)
                                cur.execute(save_smells)
                        # update test smell number of table test_cases
                        save_smell_number = "UPDATE test_cases SET TEST_SMELLS='%d' " \
                                            "WHERE NAME='%s' and PATH='%s'" % (num, name, file_path)
                        cur.execute(save_smell_number)
        db.commit()
        t4 = time.time()
        print("save data done!")
        print("detect and save " + str(test_file_number) + " test files")
        print("detect and save " + str(test_case_number) + " test cases")
        print("detect and save " + str(test_smell_number) + " test smells")
        print("cost " + str(t4 - t3) + "seconds")
        print("total cost: " + str(t4 - t1) + " seconds")
    except Exception as e:
        print("operation error: " + str(e))
        print(traceback.format_exc())
        db.rollback()
        print("rollback!")
    finally:
        cur.close()
        db.close()


def save_passed_builds(passed_builds_list):
    db = connect()
    cur = db.cursor()
    print("db connected!")
    print("saving passed builds into db......")
    t1 = time.time()
    try:
        # delete_history = "truncate table build_history"
        # cur.execute(delete_history)
        for build in passed_builds_list:
            if build['branch_name']:
                duration = str(datetime.timedelta(seconds=build['duration']))
                UTC_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
                utc_time = datetime.datetime.strptime(build['finished_at'], UTC_FORMAT)
                save_builds = "INSERT INTO build_history(build_id, branch, duration, created_time, status, PREVIOUS_STATE,commit_sha) " \
                              "VALUES ('%s','%s','%s','%s','%d','%s','%s')" % (
                                  str(build['id']), build['branch_name'], duration,
                                  utc_time, 0, str(build['previous_state']), str(build['commit_sha']))
                # print(save_builds)
                cur.execute(save_builds)
        db.commit()
        t2 = time.time()
        print("save passed builds done!")
        print("cost " + str(t2 - t1) + "seconds")
    except Exception as e:
        db.rollback()
        print("error: " + str(e))
        print(traceback.format_exc())
        print("rollback!")
    finally:
        cur.close()
        db.close()


def save_failed_builds_and_tests(failed_build_list, failed_test_dic, project_path):
    db = connect()
    cur = db.cursor()
    print("db connected!")
    print("saving failed builds into db......")
    t1 = time.time()
    try:
        # delete_tests = "truncate table failed_tests"
        # cur.execute(delete_tests)
        # save failed builds
        for build in failed_build_list:
            if build['branch_name']:
                duration = str(datetime.timedelta(seconds=build['duration']))
                UTC_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
                utc_time = datetime.datetime.strptime(build['finished_at'], UTC_FORMAT)
                status = 1
                save_builds = "INSERT INTO build_history(build_id, branch, duration, created_time, status,PREVIOUS_STATE, commit_sha) " \
                              "values ('%s','%s','%s','%s','%d','%s','%s')" % (
                                  build['id'], build['branch_name'], duration,
                                  utc_time, status, str(build['previous_state']), build['commit_sha'])
                cur.execute(save_builds)
        db.commit()

        t2 = time.time()
        print("save failed builds done!")
        print("cost " + str(t2 - t1) + "seconds")
        print("\n\n")
        print("saving failed tests into db......")
        # save failed tests
        count = 0
        for build_id, failed_test in failed_test_dic.items():
            print("processing " + str(count) + " " + "build id: " + build_id)
            update_status = "update build_history set STATUS=2 where BUILD_ID='%s'" % build_id
            cur.execute(update_status)  # update build status to failed with failed tests
            get_time = "select CREATED_TIME from build_history where BUILD_ID='%s'" % build_id
            cur.execute(get_time)
            created_time = cur.fetchall()[0][0]
            diff_dic = diff_compare(project_path, failed_test['commit_sha'], failed_test['traceback'])
            count += 1
            if failed_test['failed_tests']:
                for test in failed_test['failed_tests']:
                    path = test['test_dir'] + test['test_file']
                    path.replace('\'', '')
                    test_name = test['test_case']
                    tracebacks = ''
                    cover = diff_dic[test_name]
                    if failed_test['traceback'][test_name]:
                        for trace in failed_test['traceback'][test_name]:
                            for t in trace:
                                t.replace('\'', '')
                                tracebacks += t + " "
                    save_failed_tests = "insert into failed_tests(build_id, failed_test_name, path, traceback, dependency_cover, git_diff,created_time) VALUES " \
                                        "('%s','%s','%s','%s','%s','%s','%s')" % (
                                            build_id, test_name, pymysql.escape_string(path), tracebacks, cover,
                                            diff_dic['diff'],
                                            created_time)
                    cur.execute(save_failed_tests)
        t3 = time.time()
        db.commit()
        print("save failed tests done!")
        print("cost " + str(t3 - t2) + "seconds")

    except Exception as e:
        db.rollback()
        print("error: " + str(e))
        print(traceback.format_exc())
        print("rollback!")

    finally:
        cur.close()
        db.close()


def update_flakiness_possibility():
    db = connect()
    cur = db.cursor()


def search(sql):
    db = connect()
    cur = db.cursor()
    results = []
    try:
        cur.execute(sql)
        results = cur.fetchall()
    except Exception as e:
        print(e)
    finally:
        cur.close()
        db.close()
        return results


# factor 1: test case size
def search_size_bigger_than(size):
    sql = "SELECT tc.`NAME`, `size`, path FROM test_cases tc WHERE `size`>%s order by size desc " % size
    return search(sql)


def search_size_between(start, end):
    sql = "SELECT `NAME`,`SIZE`,`TEST_SMELLS`,`PATH` FROM test_cases " \
          "WHERE `SIZE` BETWEEN %s AND %s order by `SIZE` desc " % (start, end)
    return search(sql)


# factor 2: test smell
def search_test_smell():
    sql = """SELECT `NAME`,test_smells AS test_smell_number,PATH 
             FROM test_cases 
             WHERE test_smells>0 
             ORDER BY test_smell_number DESC"""
    return search(sql)


def search_smell_details(test_case):
    if test_case == "all":
        sql = """SELECT `NAME`, tc.`TEST_SMELLS`,ts.`TEST_SMELL_TYPE`,ts.`TIP`,ts.`LOCATION`,tc.`PATH`
                 FROM test_cases tc,test_smells ts 
                 WHERE tc.`NAME`=ts.`TEST_CASE_NAME`
                 ORDER BY tc.`TEST_SMELLS` DESC"""
        return search(sql)
    else:
        sql = """SELECT `NAME`, tc.`TEST_SMELLS`,ts.`TEST_SMELL_TYPE`,ts.`TIP`,ts.`LOCATION`,tc.`PATH`
                 FROM test_cases tc,test_smells ts 
                 WHERE tc.`NAME`=ts.`TEST_CASE_NAME` and tc.`NAME`='%s'""" % test_case
        return search(sql)


def search_no_smell():
    sql = """SELECT * FROM test_cases WHERE test_smells=0"""
    return search(sql)


def smell_distribution():
    sql = """SELECT test_smells,COUNT(test_smells) AS test_smell_count 
             FROM test_cases GROUP BY test_smells ORDER BY test_smells"""
    return search(sql)


def smell_type():
    sql = """SELECT TEST_SMELL_TYPE,COUNT(*) FROM test_smells GROUP BY TEST_SMELL_TYPE"""
    return search(sql)


# factor 3: dependency coverage
def search_dependency_cover_T(days):
    sql = """SELECT FAILED_TEST_NAME 
             FROM failed_tests 
             WHERE DEPENDENCY_COVER='T' and DATE_SUB(CURDATE(),INTERVAL %d DAY) <=CREATED_TIME""" % days
    return search(sql)


def search_git_diff_N(days):
    sql = """SELECT FAILED_TEST_NAME 
             FROM failed_tests 
             WHERE git_diff='N' and DATE_SUB(CURDATE(),INTERVAL %d DAY) <=CREATED_TIME""" % days
    return search(sql)


def search_dependency_cover_F(days):
    sql = """SELECT FAILED_TEST_NAME 
             FROM failed_tests 
             WHERE DEPENDENCY_COVER="F" AND git_diff="Y" AND DATE_SUB(CURDATE(),INTERVAL %d DAY) <=CREATED_TIME""" % days
    return search(sql)


def search_dependency_cover_F_count(days):
    sql = """SELECT FAILED_TEST_NAME,COUNT(*) AS times,path,build_id AS last_build
             FROM failed_tests 
             WHERE DEPENDENCY_COVER="F" AND git_diff="Y" AND DATE_SUB(CURDATE(),INTERVAL %d DAY) <=CREATED_TIME
             GROUP BY FAILED_TEST_NAME 
             ORDER BY times DESC""" % days
    return search(sql)


def search_latest_failed_build(build_id):
    if build_id == 0:
        sql = """SELECT failed_test_name,DEPENDENCY_COVER, build_id,CREATED_TIME,path 
                 FROM failed_tests 
                 WHERE build_id = (SELECT build_id FROM build_history 
                 WHERE STATUS=2 ORDER BY CREATED_TIME DESC LIMIT 1)"""
    else:
        sql = """SELECT failed_test_name,DEPENDENCY_COVER, build_id,CREATED_TIME,path 
                 FROM failed_tests 
                 WHERE build_id = %d""" % build_id
    return search(sql)


# factor 4: build history
def search_failed_times(days):
    sql = """SELECT FAILED_TEST_NAME,COUNT(*) AS failed_times, path
             FROM failed_tests 
             WHERE DATE_SUB(CURDATE(),INTERVAL %d DAY) <=CREATED_TIME
             GROUP BY FAILED_TEST_NAME 
             HAVING failed_times>0
             ORDER BY failed_times DESC""" % days
    return search(sql)


def search_build_status(days):
    sql = """SELECT `status` ,COUNT(*) AS times 
             FROM build_history 
             WHERE DATE_SUB(CURDATE(),INTERVAL %d DAY) <=CREATED_TIME
             GROUP BY `status`""" % days
    return search(sql)


# flakiness score
def flakiness_score(test_case):
    if test_case == 'all':
        sql = """SELECT tc.`NAME`,COUNT(ft.`FAILED_TEST_NAME`) AS failed_times,tc.`SIZE`,tc.`TEST_SMELLS`, 
                 ft.`DEPENDENCY_COVER` AS recent_cover, ft.git_diff,ft.`BUILD_ID` AS recent_failed_build_id,tf.`PATH`
                 FROM test_cases tc LEFT JOIN (SELECT * FROM failed_tests WHERE DEPENDENCY_COVER='F') ft 
                 ON tc.`NAME`=ft.`FAILED_TEST_NAME`
                 GROUP BY tc.`NAME`
                 ORDER BY failed_times DESC"""
    else:
        sql = """SELECT tc.`NAME`,COUNT(ft.`FAILED_TEST_NAME`) AS failed_times,tc.`SIZE`,tc.`TEST_SMELLS`, 
                 ft.`DEPENDENCY_COVER` AS recent_cover, ft.git_diff,ft.`BUILD_ID` AS recent_failed_build_id,ft.`PATH`
                 FROM test_cases tc right JOIN (SELECT * FROM failed_tests WHERE DEPENDENCY_COVER='F') ft 
                 ON tc.`NAME`=ft.`FAILED_TEST_NAME`
                 where ft.`FAILED_TEST_NAME` = '%s'
                 GROUP BY tc.`NAME`
                 ORDER BY failed_times DESC""" % test_case
    return search(sql)


def flakiness_score_one(build_id):
    failed_tests = search_latest_failed_build(build_id)
    flakiness_list = []
    if failed_tests:
        for f in failed_tests:
            score_dic = {}
            r = flakiness_score(f[0])
            if r:
                size_score = 0
                smell_score = 0
                if r[0][2]:
                    size_score = r[0][2] - 29 if r[0][2] > 30 else 0
                if r[0][3]:
                    smell_score = r[0][3] * 0.4
                score = r[0][1] * 0.2 + size_score + smell_score + (2 if r[0][4] == 'F' else 0)
                score_dic[f[0]] = {'failed_times': r[0][1], 'size': r[0][2], 'test_smells': r[0][3],
                                   'dependency_cover': f[1], 'build_id': f[2], 'path': r[0][7], 'score': score}
                flakiness_list.append(score_dic)

    return flakiness_list


'''
def save_total_builds():
    db = connect()
    cur = db.cursor()
    total_builds = "select count(*) from build_history"
    cur.execute(total_builds)
    total = cur.fetchall()[0][0]

    failed_builds = "select count(*) from build_history where STATUS=1 or STATUS=2"
    cur.execute(failed_builds)
    failed = cur.fetchall()[0][0]
    
    passed_builds = "select count(*) from build_history where STATUS=0"
    cur.execute(passed_builds)
    passed = cur.fetchall()[0][0]
'''

if __name__ == '__main__':
    path = r'D:\CoursesResources\MasterThesis\Python_projects\incubator-superset'
    # time1 = time.time()
    # smell_project = get_test_smell_project(path)
    # for key, value in smell_project.items():
    #     print(key, value)
    # time2 = time.time()
    # print('cost time: ' + str(time2 - time1))
    # print(connect())
    # save_case_and_smells(path)

    project_owner = "apache"
    project_name = "incubator-superset"

    # passed_builds = get_all_builds(project_owner, project_name, "passed", 10)
    # save_passed_builds(passed_builds)

    failed_test_list = get_all_builds(project_owner, project_name, "failed", 8)
    failed_test_dic = get_failed_tests(failed_test_list)
    save_failed_builds_and_tests(failed_test_list, failed_test_dic, path)

    # create_tables()
