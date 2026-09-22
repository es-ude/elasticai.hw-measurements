def pytest_sessionstart(session):
    from elasticai.hw_measurements import get_path_to_project
    from shutil import rmtree

    folder_names = ["build_sim", "temp_build", "temp_config", "temp_files", "temp_main", "temp_new", "temp_new", "temp_reports", "temp_test"]
    for name in folder_names:
        path2temp = get_path_to_project() / name
        if path2temp.exists():
            rmtree(path2temp, ignore_errors=True)


def pytest_sessionfinish(session, exitstatus):
    from elasticai.hw_measurements import get_path_to_project
    from shutil import rmtree

    folder_names = ["build_sim", "temp_build", "temp_config", "temp_files", "temp_main", "temp_new", "temp_new",
                    "temp_reports", "temp_test"]
    for name in folder_names:
        path2temp = get_path_to_project() / name
        if path2temp.exists():
            rmtree(path2temp, ignore_errors=True)

