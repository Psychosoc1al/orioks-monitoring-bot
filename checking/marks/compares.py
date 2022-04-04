from utils import exeptions
import aiogram.utils.markdown as md


def file_compares(old_file: list, new_file: list) -> list:
    if len(old_file) != len(new_file):
        raise exeptions.FileCompareError

    diffs = []
    for old, new in zip(old_file, new_file):
        if old['subject'] != new['subject']:
            raise exeptions.FileCompareError
        if len(old['tasks']) != len(new['tasks']):
            raise exeptions.FileCompareError
        diffs_one_subject = []
        for old_task, new_task in zip(old['tasks'], new['tasks']):
            if old_task['max_grade'] != new_task['max_grade']:
                raise exeptions.FileCompareError
            if old_task['alias'] != new_task['alias']:
                raise exeptions.FileCompareError

            old_grade = old_task['current_grade']
            new_grade = new_task['current_grade']
            if old_grade != new_grade:
                old_grade = 0 if old_grade == '-' or old_grade == 'н' else old_grade
                new_grade = 0 if new_grade == '-' or new_grade == 'н' else new_grade
                diffs_one_subject.append({
                    'task': new_task['alias'],
                    'ball': {
                        'abs_difference': round(abs(old_grade - new_grade), 2),
                        'is_new_bigger': new_grade - old_grade >= 0,
                        'current_ball': new_grade,
                        'old_ball': old_grade,
                        'max_grade': new_task['max_grade'],
                    }
                })
        if len(diffs_one_subject) != 0:
            diffs.append({
                'subject': new['subject'],
                'tasks': diffs_one_subject,
                'final_grade': {
                    'current_ball': new['ball']['current'],
                    'might_be': new['ball']['might_be'],
                },
            })
    return diffs


def get_msg_from_diff(diffs: list) -> str:
    message = ''
    for diff_subject in diffs:
        for diff_task in diff_subject['tasks']:
            message += md.text(
                md.text(
                    md.text('📓'),
                    md.hbold(diff_task['task']),
                    md.text('по'),
                    md.text(f"«{diff_subject['subject']}»"),
                    sep=' '
                ),
                md.hbold(
                    md.text(diff_task['ball']['old_ball']),
                    md.text('—>'),
                    md.text(diff_task['ball']['current_ball']),
                    md.text(
                        md.text('('),
                        md.text('из'),
                        md.text(' '),
                        md.text(diff_task['ball']['max_grade']),
                        md.text(')'),
                        sep='',
                    ),
                    md.text(
                        md.text('('),
                        md.text('+' if diff_task['ball']['is_new_bigger'] else '-'),
                        md.text(' '),
                        md.text(diff_task['ball']['abs_difference']),
                        md.text(')'),
                        sep='',
                    ) if diff_task['ball']['abs_difference'] != 0 else md.text(''),
                    sep=' ',
                ),
                md.text(
                    md.hcode('🧯 Внимание: балл изменён на 0, возможно, преподаватель поставил временную '
                             '«оценку-заглушку»\n') if diff_task['ball']['abs_difference'] == 0 else md.text(''),
                    md.text('Изменён балл за контрольное мероприятие.'),
                    sep='',
                ),
                md.text(),
                md.text(
                    md.hitalic('Общая сумма баллов:'),
                    md.hitalic(' '),
                    md.hitalic(diff_subject['final_grade']['current_ball']),
                    md.hitalic(' '),
                    md.hitalic('из'),
                    md.hitalic(' '),
                    md.hitalic(diff_subject['final_grade']['might_be']),
                    sep='',
                ),
                md.text(),
                md.text(),
                md.text(),
                sep='\n',
            )
    return message
