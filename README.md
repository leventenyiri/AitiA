# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/leventenyiri/AitiA/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name               |    Stmts |     Miss |   Branch |   BrPart |   Cover |   Missing |
|------------------- | -------: | -------: | -------: | -------: | ------: | --------: |
| mqtt.py            |       74 |       38 |       16 |        1 |     43% |8-9, 23-37, 49-65, 76-78, 83->82, 84-94, 97-99 |
| static\_config.py  |       12 |        0 |        0 |        0 |    100% |           |
| tests/mqttTest.py  |       33 |        3 |        6 |        2 |     82% |9->8, 14->13, 15-16, 28 |
| tests/utilsTest.py |       16 |        0 |        4 |        2 |     90% |9->8, 18->exit |
| utils.py           |       75 |       37 |       18 |        6 |     47% |20->19, 21-32, 38-39, 44->43, 45-61, 64->63, 65-71, 81, 82->84, 86-88, 93->92, 94-95 |
|          **TOTAL** |  **210** |   **78** |   **44** |   **11** | **57%** |           |

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