import csv
import sys
from os import path, walk

df_path = "datafiles"
e2e_df_path = "e2e_datafiles"
paths_to_skip = ["datafiles/mockup/exported", "e2e_datafiles/mockup/exported"]


def sort_and_ignore_json(files):
    new_files = [file for file in files if not file.endswith(".json")]
    new_files.sort()
    return new_files


def read_header_csv(root, file):
    with open(root + "/" + file) as f:
        reader = csv.reader(f)
        header = next(reader)
        for i in range(len(header)):
            header[i] = header[i].replace("'", "")
    return header


def check_no_diff_in_file(path1, path2, skip_paths):
    print("------------------- Test Started -------------------------")
    list_of_new_files = []
    list_of_changed_files = []
    list_of_missing_files = []
    for (root1, dirs1, files1), (root2, dirs2, files2) in zip(
        walk(path1, topdown=True), walk(path2, topdown=True)
    ):
        print(f"Comparing: {root1} <> {root2} ")
        dirs1[:] = [
            d
            for d in dirs1
            if not any(path.join(root1, d).startswith(p) for p in skip_paths)
        ]
        dirs2[:] = [
            d
            for d in dirs2
            if not any(path.join(root2, d).startswith(p) for p in skip_paths)
        ]
        dirs1set = set(dirs1)
        dirs2set = set(dirs2)
        if dirs1set != dirs2set:
            print(
                f"-> ERROR: Difference in sub-directories detected between {root1} and {root2}"
            )
            if dirs1set - dirs2set:
                print(f'-> Missing folder in {root2}: {", ".join(dirs1set-dirs2set)}')
            if dirs2set - dirs1set:
                print(f'-> Missing folder in {root1}: {", ".join(dirs2set-dirs1set)}')
            return False
        else:
            files1 = sort_and_ignore_json(files1)
            files2 = sort_and_ignore_json(files2)
            list_of_new_files.extend(set(files1).difference(set(files2)))
            list_of_missing_files.extend(set(files2).difference(set(files1)))
            for file in set(files1) - set(files2):
                print(f'-> New file "{file}" detected')
            for file in set(files2) - set(files1):
                print(f'-> File "{file}" missing')
            files1_c = set(files1).intersection(files2)
            files2_c = set(files2).intersection(files1)
            for file1, file2 in zip(files1_c, files2_c):
                if file1 == file2:
                    if file1.endswith(".csv"):
                        if read_header_csv(root1, file1) != read_header_csv(
                            root2, file2
                        ):
                            print(f'-> Change in "{file1}" detected')
                            list_of_changed_files.append(file1)
                else:
                    print("-> FAILURE: Something is wrong with the test...")
                    return False
    print("-------------------- Test Output ------------------------")

    if not list_of_new_files and not list_of_changed_files:
        print("Test completed successfully")
        print("--------------------- Test Complete ------------------------")
        return True
    elif list_of_new_files or list_of_changed_files or list_of_missing_files:
        if list_of_new_files:
            print(f"-> ERROR: File(s) missing in e2e_datafiles: {list_of_new_files}")
        if list_of_changed_files:
            print(
                f"-> ERROR: Changes in the following CSV file(s): {list_of_changed_files}"
            )
        if list_of_missing_files:
            print(f"-> ERROR: File(s) missing in datafiles: {list_of_missing_files}")
        return False
    else:
        print("-> FAILURE: Something is wrong with the test...")
        return False


def run_check_e2e_sync_test(path1, path2, skip_path):
    if not check_no_diff_in_file(path1, path2, skip_path):
        print(
            'ERROR: Ensure that the directories "datafiles" and "e2e_datafiles" are in sync!'
        )
        sys.exit(1)


if __name__ == "__main__":
    run_check_e2e_sync_test(df_path, e2e_df_path, paths_to_skip)
