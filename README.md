# FlakinessDetector
## 1.Requirements
### Language:
   python>=3.6.7
### Dependency:
    click==7.1.2
    matplotlib==3.3.2
    prettytable==1.0.0
    PyMySQL==0.10.1
    pytest==5.3.5
    requests==2.23.0
## 2.Use
### 2.1 Install
    pip install -r requirements.txt
### 2.2 setup mysql
#### 2.2.1 create mysql database
   Create a database (with any name) in mysql to save data
#### 2.2.2 change connection info
   Change host,user,password(pw),database(db) in mysql_handler.py file to connect your mysql. For example, update the line - connect(host="localhost", user="username", pw="password", db="The name you selected in 2.2.1")
      
#### 2.2.3 Clone Project Under Test
   Clone a project under test, example: git clone https://github.com/apache/incubator-superset.git 

### 2.3 Two ways to load build history
Two of the factors, in this tool, depend on build history. This project facilitates users to load history either from Travis or by manually assigning the JSON file.  
####  2.3.1 Download and Process Build Logs from Travis CI
The Travis build logs of the projects can be accessed through GitHub project. For example, if you visit "https://github.com/apache/incubator-superset" page, you will find ![size](pic/build_link.png) . Click here and it will take you to the build history. The following commands load it automatically.

      command: python initialize.py --i init --p [project_under_test_path] --o [project_under_test_owner] --n [project_under_test_name] --l [NumberOfDays]
      
      --p: project under test local path
      --o: project under test owner on github
      --n: project under test name on github
      --l: opptional, build history in the past [NumberOfDays] days (for example, 180, 365) you want to get from Travis CI, default:0, get all the build history

For example, in the URL: https://github.com/apache/incubator-superset, the project owner is "apache", the project name is "incubator-superset" and local path could be where you cloned the project. 

Note: use "python initialize.py --help" to get details of this command

#### 2.3.2 Init from Json file
      command: python initialize.py --i init_json --p [project_under_test_path] --j [json_file_path]
      
      --p: project under test local path
      --j: path of build hisory json file, only need the name of the json file if the json file is in current dictory

The structure of JSON file is as follows:

    <String: build id>: { 
            "branch_name": <String: branch name>,
            "id": <Integer: build id>,
            "state": <String: build status(passed,failed)>,
            "previous_state": <String: build status of the parent commit of this commit>,
            "commit_sha": <String: commit SHA>,
            "duration": <Integer: how long it takes to finish this build(seconds)>,
            "finished_at": <String: when the build finished at>,
            "failed_info": {  <Dict: it contains the info of failed tests, can be null>
                "commit_sha": <String: commit SHA>,
                "branch": <String: branch name>,
                "build_id": <Integer: build id>,
                "failed_tests": [ <List: it contains multiple Dicts,each Dict contains info of one failed test>
                    {   <Dict: it conatins basic info of each failed test>
                        "test_case": <String: test case name>,
                        "test_class": <String: class of the test case, can be null>,
                        "test_file": <Srting: which test file the test case belong to>,
                        "test_dir": <String: relative directory of the test file>
                    }
                ],
                "traceback": { <Dict: it contains traceback of each failed test, can be null>
                    <String: test case name>: [  <List: it contains detail info of traceback of each failed test>
                        [   <List: it contains 3 main info of traceback>
                            <String: file path>,
                            <String: The line number where the following code is>,
                            <String: the code that caused the test to fail>
                        ], 
                    ]
                }
            }
        }
 JSON example:
 
    "597008875": {
        "branch_name": "master",
        "id": 597008875,
        "state": "passed",
        "previous_state": "failed",
        "commit_sha": "2117d1ef9d0ce041d91a75eba47d0b07dabed8c9",
        "duration": 3850,
        "finished_at": "2019-10-12T15:18:06Z",
        "failed_info": {}
    },
    "596776418": {
        "branch_name": "master",
        "id": 596776418,
        "state": "failed",
        "previous_state": "failed",
        "commit_sha": "03b35b3c1121bb452a7938ed92c6bede657377dd",
        "duration": 3798,
        "finished_at": "2019-10-11T20:52:37Z",
        "failed_info": {
            "commit_sha": "03b35b3c1121bb452a7938ed92c6bede657377dd",
            "branch": "master",
            "build_id": 596776418,
            "failed_tests": [
                {
                    "test_case": "test_load_world_bank_health_n_pop",
                    "test_class": "SupersetDataFrameTestCase",
                    "test_file": "load_examples_test.py",
                    "test_dir": "tests/"
                }
            ],
            "traceback": {
                "test_load_world_bank_health_n_pop": [
                    [
                        "/home/travis/build/apache/incubator-superset/tests/load_examples_test.py",
                        "30",
                        "test_load_world_bank_health_n_pop"
                    ],
                    [
                        "/home/travis/build/apache/incubator-superset/superset/examples/world_bank.py",
                        "51",
                        "load_world_bank_health_n_pop"
                    ],
                    [
                        "/home/travis/build/apache/incubator-superset/superset/examples/helpers.py",
                        "72",
                        "get_example_data"
                    ],
                    [
                        "/opt/python/3.6.7/lib/python3.6/http/client.py",
                        "462",
                        "read"
                    ],
                    [
                        "/opt/python/3.6.7/lib/python3.6/http/client.py",
                        "612",
                        "_safe_read"
                    ],
                    [
                        "/opt/python/3.6.7/lib/python3.6/socket.py",
                        "586",
                        "readinto"
                    ],
                    [
                        "/opt/python/3.6.7/lib/python3.6/ssl.py",
                        "1012",
                        "recv_into"
                    ],
                    [
                        "/opt/python/3.6.7/lib/python3.6/ssl.py",
                        "874",
                        "read"
                    ],
                    [
                        "/opt/python/3.6.7/lib/python3.6/ssl.py",
                        "631",
                        "read"
                    ]
                ]
            }
        }
    },
### 2.4 Generate Output in Tables and Graphs
    There are 2 ways to show data: charts and tables. Tables provide detailed information including test case names, paths, name of test smells and other information whereas charts provides high level quantitative information.

    use "python show.py --help" to get details

#### 2.4.1 test smells

##### (1) show test smells distribution
      command: python show.py --type smell
      output: 1. table ['Test Case', 'Number of Smells', 'Path']
              2. 3 charts
   example output:
   ![smells](pic/smells.png)
##### (2) show test smell details

      command: python show.py --type smell_details 

 The above command will provides information for all test cases. In case, you want to limit to one specific test case, run the following command:

      command: python show.py --type smell_details --test_case [TestCaseName]
      
      output: table ['Test Case', 'Number of Smells', 'Smell type', 'Tip', 'Location', 'Path']

#### 2.4.2 dependency coverage (Think about other name -- I will also think)

show latest failed build with failed tests: 

      command: python show.py --type dc_one
      
 ************     output: a table ['Failed Test Case', 'Coverage status (F/T)', 'Build ID', 'Build Finished Time', 'Path']******************
show dependency coverage of a certain build:

      command: python show.py --type dc_one --build_id [build id]
      
      output: a table ['Failed Test Case', 'Coverage status', 'Build ID', 'Build Finished Time', 'Path']

The below command used all build history from DB.

      command: python show.py --type dc_all ******* can we write python show.py --type all/**** Just stay persistant in command structure********
      
      output: table ['Failed Test Case Name', 'NT-FDUC', 'Path', 'Last Failed Build ID']
      
      note: NT-FDUC = Number of Times, It failed due to unrelated changes in past
   
If you want to limit the number of days, use the following command:

      command: python show.py --type dc_all --days [Number Of Days]

       output: table ['Failed Test Case Name', 'NT-FDUC', 'Path', 'Last Failed Build ID']

#### 2.4.3 Test case history

**** We need two tables so does two commands. One tables should only present test cases failed in the last build. The other table should present all test cases in the repo.****

 *********output: 1. table ['Failed Test Name', 'Number of Times, It failed due to unrelated changes in past', 'Path']**********

 One command only give information of test cases from the last failed build in NumberOfDays (whatever user enter), other command give information of all test cases in repo in NumberOfDays (whatever user enter)

        command: python show.py --type testcase_history --days NumberOfDays . . *** can we rename "build_histroy" tp "testcase_history"
        
        --days is opptional, days means get the data generated whin X days; default 3600
        
       
                2. chart
   example output:
   ![build history](pic/build_history.png)
   
#### 2.4.1 test case size
##### (1) show test case size distribution
      command: python show.py --type size
      
   example output:
   ![size](pic/size.png)
##### (2) show test cases that their size bigger than x
      command: python show.py --type size_bigger_than --size [x]
      
      output: a table ['Test Case', 'Path', 'Size']
##### (3) show size between x and y
      command: python show.py --type size_between --between [x] [y]
      
      output: a table ['Test Case', 'Path', 'Size', 'Test Smells']


#### 2.4.5 flakiness score

get flakiness score and other info of one build, default get latest failed build

        command: python show.py --tyoe fs_one --build_id [build id]
        
        output: table ['Build ID', 'Test Case', 'Score', 'NT-FDUC', 'Size', 'Number of Test Smells', 'Dependency Cover', 'Path']
        
get all flakiness score of all the failed tests.
        
        command: python show.py --type fs_all
        
        How to get flakiness score:
            score = falied_times*0.2 + (size > 30 ?size - 29 : 0) * 0.05
                    + test_smell_numver * 0.4 + (dependency_cover == 'F'?2 : 0)
        output: 1. table ['Test Case', 'Score', 'NT-FDUC', 'Size', 'Number of Test Smells', 'Latest Dependency Cover', 'Latest Failed build_id', 'Path']
                2. chart
   example output:
   ![flakiness score](pic/flakiness_score.png)    