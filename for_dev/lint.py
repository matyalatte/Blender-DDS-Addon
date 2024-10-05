"""Script to run pylint.

Notes:
    Install pylint with "pip install pylint"
    Then, run "python for_dev/lint.py --path=blender_dds_addon"
    You should get no errors.
"""
import argparse
import json
import sys
from pylint.lint import Run


def get_args():
    """Get arguments."""
    parser = argparse.ArgumentParser(prog="LINT")

    parser.add_argument('--path', default='./src', type=str)
    parser.add_argument('--threshold', default=7, type=float)
    parser.add_argument('--file_name', default=None, type=str)
    return parser.parse_args()


if __name__ == '__main__':
    args = get_args()
    path = args.path
    threshold = args.threshold
    file_name = args.file_name

    print('PyLint Starting | '
          f'Path: {path} | '
          f'Threshold: {threshold} ')

    results = Run([path], exit=False)

    score = results.linter.stats.global_note
    score_msg = f'Score: {score} | Threshold: {threshold} '

    if score < threshold:
        message = 'PyLint Failed | ' + score_msg
        raise Exception(message)

    else:
        message = 'PyLint Passed | ' + score_msg
        print(message)
        if file_name is not None:
            if score < 3.0:
                color = "red"
            elif 3.0 <= score < 7.0:
                color = "yellow"
            else:
                color = "brightgreen"
            score = round(score, 2)
            badge_data = {
                "schemaVersion": 1, "label": "pylint",
                "message": str(score), "color": color
            }
            with open(file_name, 'w', encoding='utf-8') as f:
                json.dump(badge_data, f)
        sys.exit()
