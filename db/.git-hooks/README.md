# Git Hooks

## Before you run the script

---
**NOTE**

Executing the script will
* create symbolic links for those hooks that are located in the `.git-hooks` directory.
* overwrite already existing git hooks in your local `.git/hooks` directory. 
---

If you are using your own hooks and want to keep those,
then you might need to merge the Novo Nordisk provided hooks manually into your existing ones.

## Setup

**Under linux:**

Run the [installation script](./install-git-hooks.sh) once via e.g.:

```shell script
# from the root directory of the repository, run:
./.git-hooks/install-git-hooks.sh
```

That's it, the hook(s) should be installed.
