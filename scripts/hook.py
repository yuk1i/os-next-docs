#!/usr/bin/python3
import os
import git
import subprocess
import mkdocs.plugins

@mkdocs.plugins.event_priority(-100)
def on_env(env, config, files):
    r = git.Repo(".")
    head = r.head.commit
    sha = head.hexsha[:8]
    modified_date = head.committed_date

    env.globals["buildsha"] = sha
    config.extra["social"] = True
    return env
