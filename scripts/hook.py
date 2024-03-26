#!/usr/bin/python3
import os
import pytz
import git
import subprocess
import mkdocs.plugins

@mkdocs.plugins.event_priority(-100)
def on_env(env, config, files):
    r = git.Repo(".")
    head = r.head.commit
    sha = f"{head.hexsha[:8]}, {head.committed_datetime.astimezone(pytz.timezone('Asia/Shanghai'))}"
    modified_date = head.committed_date

    env.globals["buildsha"] = sha
    config.extra["social"] = True
    return env
