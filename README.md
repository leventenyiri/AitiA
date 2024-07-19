# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/leventenyiri/AitiA/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                |    Stmts |     Miss |   Branch |   BrPart |   Cover |   Missing |
|-------------------- | -------: | -------: | -------: | -------: | ------: | --------: |
| app.py              |       98 |       27 |       25 |        8 |     70% |24->exit, 25, 39->38, 58->62, 94-95, 98->97, 124->123, 125-131, 134->133, 135-148, 151-152, 156-173 |
| camera.py           |       39 |       12 |       10 |        3 |     69% |4, 26-27, 32-33, 41-45, 48->47, 49-50 |
| mqtt.py             |       75 |        9 |       14 |        3 |     84% |8-9, 30->33, 39-42, 88->87, 97-99, 102->exit |
| static\_config.py   |       12 |        0 |        0 |        0 |    100% |           |
| tests/appTest.py    |      137 |        0 |       84 |       41 |     81% |13->12, 18->17, 45->50, 60->64, 77->80, 78->77, 87->90, 88->87, 97->100, 98->97, 111->106, 113->116, 114->113, 134->123, 139->142, 144->exit, 170->174, 209->212, 220->222, 221->220, 222->221, 231->233, 232->231, 233->232, 242->244, 243->242, 244->243, 253->255, 254->253, 255->254, 264->266, 265->264, 266->265, 281->283, 282->281, 283->282, 289->exit, 293->295, 294->293, 295->294, 301->exit |
| tests/cameraTest.py |       35 |        0 |       20 |       10 |     82% |20->22, 21->20, 22->21, 30->32, 31->30, 32->31, 40->43, 41->40, 42->41, 43->42 |
| tests/mqttTest.py   |      120 |        0 |       14 |        6 |     96% |14->13, 19->18, 20->exit, 116->118, 129->132, 184->189 |
| tests/utilsTest.py  |       49 |        0 |       16 |        8 |     88% |13->12, 21->exit, 47->exit, 54->53, 67->exit, 70->72, 71->70, 72->71 |
| utils.py            |       75 |        9 |       18 |        9 |     81% |20->19, 29, 44->43, 48, 51->exit, 64->63, 71, 81, 82->84, 86-88, 93->92, 94-95 |
|           **TOTAL** |  **640** |   **57** |  **201** |   **88** | **82%** |           |

2 empty files skipped.


## Setup coverage badge

Below are examples of the badges you can use in your main branch `README` file.

### Direct image

[![Coverage badge](https://raw.githubusercontent.com/leventenyiri/AitiA/python-coverage-comment-action-data/badge.svg)](https://htmlpreview.github.io/?https://github.com/leventenyiri/AitiA/blob/python-coverage-comment-action-data/htmlcov/index.html)

This is the one to use if your repository is private or if you don't want to customize anything.

### [Shields.io](https://shields.io) Json Endpoint

[![Coverage badge](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/leventenyiri/AitiA/python-coverage-comment-action-data/endpoint.json)](https://htmlpreview.github.io/?https://github.com/leventenyiri/AitiA/blob/python-coverage-comment-action-data/htmlcov/index.html)

Using this one will allow you to [customize](https://shields.io/endpoint) the look of your badge.
It won't work with private repositories. It won't be refreshed more than once per five minutes.

### [Shields.io](https://shields.io) Dynamic Badge

[![Coverage badge](https://img.shields.io/badge/dynamic/json?color=brightgreen&label=coverage&query=%24.message&url=https%3A%2F%2Fraw.githubusercontent.com%2Fleventenyiri%2FAitiA%2Fpython-coverage-comment-action-data%2Fendpoint.json)](https://htmlpreview.github.io/?https://github.com/leventenyiri/AitiA/blob/python-coverage-comment-action-data/htmlcov/index.html)

This one will always be the same color. It won't work for private repos. I'm not even sure why we included it.

## What is that?

This branch is part of the
[python-coverage-comment-action](https://github.com/marketplace/actions/python-coverage-comment)
GitHub Action. All the files in this branch are automatically generated and may be
overwritten at any moment.