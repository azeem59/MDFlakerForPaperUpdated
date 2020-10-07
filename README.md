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

      command: python initialize.py --i init --p [project_path] --o [project_owner] --n [project_name] --l [limit]
      
      --p: project local path
      --o: project owner on github
      --n: project name on github
      --l: opptional, build history in the past [limit] days you want to get from Travis CI, default:0, get all the build history

For example, in the URL: https://github.com/apache/incubator-superset, the project owner is "apache", the project name is "incubator-superset" and local path could be where you cloned the project. 

Note: use "python initialize.py --help" to get details of this command

#### 2.3.2 Init from Json file
      command: python initialize.py --i init_json --p [project_path] --j [json file path]
      
      --p: project local path
      --j: path of build hisory json file, only need the name of the json file if the json file is in current dictory
### 2.4 show data
    use "python show.py --help" to get details
    There are 2 ways to show data: charts and tables
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
#### 2.4.2 test smells
##### (1) show test smell distribution
      command: python show.py --type test_smell
      
      output: 1. table ['Test Case', 'Path', 'Number of Smells']
              2. 3 charts
   example output:
   ![smells](pic/smells.png)
##### (2) show test smell details
      command: python show.py --type smell_details --test_case [name]
      
      --test_case is opptional, you can choose one test case; default is "all", which means show details of all the test cases
      
      output: table ['Test Case', 'Number of Smells', 'Smell type', 'Tip', 'Location', 'Path']
#### 2.4.3 dependency coverage
       command: python show.py --type dependency_cover --days [days]
       
       --days is opptional, days means get the data generated whin X days; default 3600
       
       output: 1. table ['Failed Test Case', 'Missing Cover Times', 'Path', 'Last Build']
               2. chart
                  dependency_cover_T: test case failed and the traceback covered code changes
                  git_diff_N: can not get code changes from github, corrasponding dependency_cover is F(False)
                  dependency_cover_F&git_diff_Y: traceback did not cover code changes and successfully got code changes from github
   example output:
   ![dependency coverage](pic/dependency_cover.png)
#### 2.4.4 build history
        command: python show.py --type build_history --days[days]
        
        --days is opptional, days means get the data generated whin X days; default 3600
        
        output: 1. table ['Failed Test Name', 'Failed Times', 'Path']
                2. chart
   example output:
   ![build history](pic/build_history.png)
#### 2.4.5 flakiness score
        command: python show.py --type flakiness_score
        
        How to get flakiness score:
            score = falied_times*0.2 + (size > 30 ?size - 29 : 0) * 0.05
                    + test_smell_numver * 0.4 + (dependency_cover == 'F'?2 : 0)
        output: 1. table ['Test Case', 'Score', 'Failed Times', 'Size', 'Number of Test Smells', 'Recent Dependency Cover', 'Path']
                2. chart
   example output:
   ![flakiness score](pic/flakiness_score.png)    