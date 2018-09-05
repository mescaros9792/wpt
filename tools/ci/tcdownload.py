import argparse
import os

import requests

import github


def get_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ref", action="store", default="master",
                        help="Branch (in the GitHub repository) or commit to fetch logs for")
    parser.add_argument("--artifact-name", action="store", default="wpt_report.json.gz",
                        help="Log type to fetch")
    parser.add_argument("--repo-name", action="store", default="web-platform-tests/wpt",
                        help="GitHub repo name in the format owner/repo")
    parser.add_argument("--token-file", action="store",
                        help="File containing GitHub token")
    parser.add_argument("--out-dir", action="store", default=".",
                        help="Path to save the logfiles")
    return parser


def get_json(url, key=None):
    resp = requests.get(url)
    resp.raise_for_status()
    data = resp.json()
    if key:
        data = data[key]
    return data


def get(url, dest, name):
    resp = requests.get(url)
    resp.raise_for_status()
    with open(os.path.join(dest, name), "w") as f:
        f.write(resp.content)


def run(*args, **kwargs):
    if not os.path.exists(kwargs["out_dir"]):
        os.mkdir(kwargs["out_dir"])

    if kwargs["token_file"]:
        with open(kwargs["token_file"]) as f:
            gh = github.Github(f.read().strip())
    else:
        gh = github.Github()

    repo = gh.get_repo(kwargs["repo_name"])
    commit = repo.get_commit(kwargs["ref"])
    statuses = commit.get_statuses()
    taskgroups = set()

    for status in statuses:
        if not status.context.startswith("Taskcluster "):
            continue
        if status.state == "pending":
            continue
        taskgroup_id = status.target_url.rsplit("/", 1)[1]
        taskgroups.add(taskgroup_id)

    if not taskgroups:
        print("No complete TaskCluster runs found for ref %s" % kwargs["ref"])
        return

    for taskgroup in taskgroups:
        taskgroup_url = "https://queue.taskcluster.net/v1/task-group/%s/list"
        artifacts_list_url = "https://queue.taskcluster.net/v1/task/%s/runs/%s/artifacts"
        tasks = get_json(taskgroup_url % taskgroup, "tasks")
        for task in tasks:
            task_id = task["status"]["taskId"]
            for run in task["status"]["runs"]:
                run_id = run["runId"]
                url = artifacts_list_url % (task_id, run_id)
                for artifact in get_json(url, "artifacts"):
                    if artifact["name"].endswith(kwargs["artifact_name"]):
                        filename = "%s-%s-%s" % (task["task"]["metadata"]["name"],
                                                 run_id,
                                                 kwargs["artifact_name"])
                        get("%s/%s" % (url, artifact["name"]), kwargs["out_dir"], filename)


def __main__():
    kwargs = get_parser().parse_args()

    run(None, vars(kwargs))
