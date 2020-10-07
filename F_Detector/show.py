import matplotlib.pyplot as plt
import mysql_handler as mh
from prettytable import PrettyTable
import click


def show_size():
    size = [[1, 9], [10, 19], [20, 29], [30, 39], [40, 49], [50, 59], [60, 69]]
    x_label = ['1-9', '10-19', '20-29', '30-39', '40-49', '50-59', '60-69', '>=70']
    result = []
    for s in size:
        start = s[0]
        end = s[1]
        result.append(len(mh.search_size_between(start, end)))
    result.append(len(mh.search_size_bigger_than(69)))
    # x = range(result)
    plt.ylabel("Count")
    plt.xlabel("Size")
    plt.title("Test Case Size Distribution")
    plt.bar(x_label, result)
    for a, b in zip(x_label, result):
        plt.text(a, b + 1, '%.0f' % b, ha='center', va='bottom')
    plt.show()


def show_size_bigger_than(size=30):
    results = mh.search_size_bigger_than(size)
    print("count: " + str(len(results)))
    table = PrettyTable(['Test Case', 'Path', 'Size'])
    for s in results:
        name = s[0]
        path = s[1]
        size = s[2]
        table.add_row([name, path, size])
    print(table)


def show_size_between(start=30, end=50):
    results = mh.search_size_between(start, end)
    print("count: " + str(len(results)))
    table = PrettyTable(['Test Case', 'Path', 'Size', 'Test Smells'])
    for r in results:
        table.add_row([r[0], r[1], r[2], r[3]])
    print(table)


def show_smell():
    plt.figure(figsize=(10, 10))
    plt.figure(1)
    bar1 = plt.subplot(211)
    bar2 = plt.subplot(223)
    bar3 = plt.subplot(224)

    def show_smell_1():
        smells = len(mh.search_test_smell())
        no_smells = len(mh.search_no_smell())
        x_label = ["Test Cases with Smells", "Test Cases without Smells"]
        size = [smells, no_smells]
        bar1.set_title("Test Case Smell Distribution")
        color = ["blue", "green"]
        patches, l_text, p_text = bar1.pie(size, colors=color, labels=x_label, labeldistance=1.1,
                                           autopct="%1.1f%%", shadow=False, startangle=90, pctdistance=0.6)
        bar1.axis("equal")
        bar1.legend()

    def show_smell_2():
        result = mh.smell_distribution()
        x_label = []
        y_value = []
        for rt in result:
            x_label.append(str(rt[0]))
            y_value.append(rt[1])

        bar2.set_ylabel("Number of Test Cases")
        bar2.set_xlabel("Number of Smells")
        bar2.set_title("Test Smells Distribution")
        bar2.bar(x_label, y_value)
        for a, b in zip(x_label, y_value):
            bar2.text(a, b + 1, '%d' % b, ha='center', va='bottom')

    def show_smell_type():
        result = mh.smell_type()
        x_label = []
        y_value = []
        for rt in result:
            x_label.append(rt[0])
            y_value.append(rt[1])
        bar3.set_xlabel("Test Smell Type")
        bar3.set_ylabel("Count")
        bar3.set_title("Test Smells Type Distribution")
        bar3.bar(x_label, y_value)
        for a, b in zip(x_label, y_value):
            bar3.text(a, b + 1, '%d' % b, ha='center', va='bottom')

    results = mh.search_test_smell()
    table = PrettyTable(['Test Case', 'Path', 'Number of Smells'])
    print("count: " + str(len(results)))
    for r in results:
        table.add_row([r[0], r[1], r[2]])
    print(table)
    show_smell_1()
    show_smell_2()
    show_smell_type()
    plt.show()


def show_smell_details(test_case="all"):
    results = mh.search_smell_details(test_case)
    table = PrettyTable(['Test Case', 'Number of Smells', 'Smell type', 'Tip', 'Location', 'Path'])
    for r in results:
        table.add_row([r[0], r[1], r[2], r[3], r[4], r[5]])
    print(table)


def show_dependency_cover(days=3600):
    dependency_cover_T = len(mh.search_dependency_cover_T(days))
    git_diff_N = len(mh.search_git_diff_N(days))
    dependency_cover_F = len(mh.search_dependency_cover_F(days))
    dependency_cover_F_count = mh.search_dependency_cover_F_count(days)

    def show_bar():
        x_label = ['dependency_cover_T', 'git_diff_N', 'dependency_cover_F&git_diff_Y']
        y_value = [dependency_cover_T, git_diff_N, dependency_cover_F]
        plt.xlabel("Dependency Coverage")
        plt.ylabel("Number of failed tests")
        plt.title("Dependency Coverage Distribution" + " (within " + str(days) + " days)")
        plt.bar(x_label, y_value)
        for a, b in zip(x_label, y_value):
            plt.text(a, b + 1, '%d' % b, ha='center', va='bottom')
        plt.show()

    def show_F_count():
        table = PrettyTable(['Failed Test Case', 'Missing Cover Times', 'Path', 'Last Build'])
        for r in dependency_cover_F_count:
            table.add_row([r[0], r[1], r[2], r[3]])
        print(table)

    show_F_count()
    show_bar()


def show_build_history(days=3600):
    failed_tests = mh.search_failed_times(days)
    build_status = mh.search_build_status(days)

    def show_status():
        x_label = ['passed', 'failed without failed tests', 'failed with failed tests']
        y_value = []
        for r in build_status:
            y_value.append(r[1])

        plt.xlabel("Status")
        plt.ylabel("Number of builds")
        plt.title("Build History Status Distribution" + " (within " + str(days) + " days)")
        plt.bar(x_label, y_value)
        for a, b in zip(x_label, y_value):
            plt.text(a, b + 1, '%d' % b, ha='center', va='bottom')
        plt.show()

    def show_failed_times():
        table = PrettyTable(['Failed Test Name', 'Failed Times', 'Path'])
        for r in failed_tests:
            table.add_row([r[0], r[1], r[2]])
        print(table)

    show_failed_times()
    show_status()


def show_flakiness_score():
    results = mh.flakiness_score()
    score_dic = {}
    x_label = ['0', '0-1', '1-2', '2-3', '3-5', '5-7', '7-9', '>9']
    y_value = [0, 0, 0, 0, 0, 0, 0, 0]
    for r in results:
        score = r[1] * 0.2 + (r[2] - 29 if r[2] > 30 else 0) * 0.05 + r[3] * 0.4 + (2 if r[4] == 'F' else 0)
        if score == 0:
            y_value[0] += 1
        elif 0 < score <= 1:
            y_value[1] += 1
        elif 1 < score <= 2:
            y_value[2] += 1
        elif 2 < score <= 3:
            y_value[3] += 1
        elif 3 < score <= 5:
            y_value[4] += 1
        elif 5 < score <= 7:
            y_value[5] += 1
        elif 7 < score <= 9:
            y_value[6] += 1
        elif score > 9:
            y_value[7] += 1
        if score > 0:
            score = format(score, '.2f')
            score_dic[r[0]] = {'failed_times': r[1], 'size': r[2], 'test_smells': r[3], 'recent_cover': r[4],
                               'git_diff': r[5], 'build_id': r[6], 'path': r[7], 'score': score}
    plt.xlabel("Flakiness Score")
    plt.ylabel("Number of Test Cases")
    plt.title("Flakiness Score Distribution")
    plt.bar(x_label, y_value)
    for a, b in zip(x_label, y_value):
        plt.text(a, b + 1, '%d' % b, ha='center', va='bottom')

    table = PrettyTable(
        ['Test Case', 'Score', 'Failed Times', 'Size', 'Number of Test Smells', 'Recent Dependency Cover',
         'Recent Failed build_id', 'Path'])
    for key, value in score_dic.items():
        table.add_row(
            [key, value['score'], value['failed_times'], value['size'], value['test_smells'], value['recent_cover'],
             value['build_id'], value['path']])
    print(table.get_string(sortby="Score", reversesort=True))
    plt.show()


@click.command()
@click.option('--type', type=click.Choice(['size', 'size_bigger_than', 'size_between', 'test_smell', 'smell_details',
                                           'dependency_cover', 'build_history', 'flakiness_score']),
              help='the type of data that you want to check')
@click.option('--size', type=int, help='you need set size when you choose size_bigger_than')
@click.option('--between', nargs=2, type=int, help='you need set start and end when you choose size_between')
@click.option('--test_case', default='all',
              help='get test smell details of a test case(default:all) when '
                   'you choose smell_details, all means show the details of all the test cases')
@click.option('--days', type=int, default=3600,
              help='get the data generated within x days(default:3600),'
                   'you can set days when you choose dependency_cover or build_history')
def main(type, size, between, test_case, days):
    if between is None:
        between = [30, 50]
    if type == 'size':
        show_size()
    elif type == 'size_bigger_than':
        show_size_bigger_than(size=size)
    elif type == 'size_between':
        show_size_between(between[0], between[1])
    elif type == 'test_smell':
        show_smell()
    elif type == 'smell_details':
        show_smell_details(test_case)
    elif type == 'dependency_cover':
        show_dependency_cover(days)
    elif type == 'build_history':
        show_build_history(days)
    elif type == 'flakiness_score':
        show_flakiness_score()


if __name__ == '__main__':
    main()
