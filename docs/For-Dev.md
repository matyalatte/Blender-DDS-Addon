# Tools for development

## Python Scripts

In [`for_dev`](../for_dev) folder, there are some python scripts to test the addon.  

- [`regist_without_installing.py`](../for_dev/regist_without_installing.py): Script to use the addon without installing it in Blender.
- [`lint.py`](../for_dev/lint.py): Script to run pylint

## Flake8

[Flake8](https://flake8.pycqa.org/en/latest/) is a tool for style guide enforcement.  
It will check if you are following [PEP8](https://peps.python.org/pep-0008/).  
Install it with `pip install flake8`.  
Then, type `flake8` in `./Blender-DDS-Addon`.  
You should get no messages from flake8.  

## Pylint

[Pylint](https://pylint.pycqa.org/en/latest/) is a static code analyser.  
It can rate your scripts.  
Install it with `pip install pylint`.  
Then, type `python for_dev\lint.py --path=addons\blender_dds_addon` in `./Blender-DDS-Addon`.  
You will get results like `PyLint Passed | Score:...`.  
The score should be more than 7.  

## Codespell

[Codespell](https://github.com/codespell-project/codespell) is a spell checker for source codes.  
Install it with `pip install codespell`.  
Then, type `codespell -S ".git,.pytest_cache,external,htmlcov"`.  
You should get no messages from codespell.  

## pytest-blender

[pytest-blender](https://github.com/mondeja/pytest-blender) is a pytest plugin for Blender testing.  
You can use bpy with pytest.  
First, install requirements in your python environment like this.  

```
pip install pytest pytest-blender
```

Then, install pytest in Blender's python environment like this.  

```
REM This is for Windows. See pytest-blender's document for linux and mac.
set BLENDER=C:\Program Files\Blender Foundation\Blender 3.0
set PYTHON_PATH=%BLENDER%\3.0\python\bin\python.exe
set SITE_PACK=%BLENDER%\3.0\python\lib\site-packages

"%PYTHON_PATH%" -m ensurepip
"%PYTHON_PATH%" -m pip install pytest -t "%SITE_PACK%" --upgrade
```

And then, you can use pytest with bpy.  

```
set BLENDER_EXE=C:\Program Files\Blender Foundation\Blender 3.0\blender.exe
pytest tests\ -svv --blender-executable "%BLENDER_EXE%"
```

## Github Actions

[Github Actions](https://docs.github.com/en/actions) is an automation tool for development workflows.  
You can run scripts on remote servers for your repositories.  
There are 2 workflows for the addon.  

- Test: Run flake8, pylint, and pytest to check your codes.
- Build: Build Texconv and zip it with python scripts.

See here if you want to use the workflows.  
[How to Build With Github Actions · matyalatte/Blender-Uasset-Addon Wiki](https://github.com/matyalatte/Blender-Uasset-Addon/wiki/How-to-Build-with-Github-Actions)  
