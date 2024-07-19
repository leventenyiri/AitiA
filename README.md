# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/leventenyiri/AitiA/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                |    Stmts |     Miss |   Branch |   BrPart |   Cover |   Missing |
|-------------------- | -------: | -------: | -------: | -------: | ------: | --------: |
| app.py              |       99 |       16 |       25 |        8 |     79% |24->exit, 25, 39->38, 58->62, 94-95, 98->97, 124->123, 134->133, 152-153, 157-174 |
| camera.py           |       39 |       12 |       10 |        3 |     69% |4, 26-27, 32-33, 41-45, 48->47, 49-50 |
| mqtt.py             |       75 |        9 |       14 |        3 |     84% |8-9, 30->33, 39-42, 88->87, 97-99, 102->exit |
| static\_config.py   |       12 |        0 |        0 |        0 |    100% |           |
| tests/appTest.py    |      141 |        0 |       82 |       35 |     84% |15->14, 20->19, 47->52, 62->66, 79->82, 80->79, 89->92, 90->89, 99->102, 100->99, 113->108, 115->118, 116->115, 136->125, 141->144, 146->exit, 172->176, 211->214, 222->230, 223->222, 224->223, 230->224, 246->254, 247->246, 248->247, 254->248, 264->exit, 275->285, 276->275, 277->276, 278->277, 279->278, 285->279, 296->exit, 307->exit |
| tests/cameraTest.py |       35 |        0 |       20 |       10 |     82% |20->22, 21->20, 22->21, 30->32, 31->30, 32->31, 40->43, 41->40, 42->41, 43->42 |
| tests/mqttTest.py   |      120 |        0 |       14 |        6 |     96% |14->13, 19->18, 20->exit, 116->118, 129->132, 184->189 |
| tests/utilsTest.py  |       49 |        0 |       16 |        8 |     88% |13->12, 21->exit, 47->exit, 54->53, 67->exit, 70->72, 71->70, 72->71 |
| utils.py            |       75 |        9 |       18 |        9 |     81% |20->19, 29, 44->43, 48, 51->exit, 64->63, 71, 81, 82->84, 86-88, 93->92, 94-95 |
|           **TOTAL** |  **645** |   **46** |  **199** |   **82** | **84%** |           |

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