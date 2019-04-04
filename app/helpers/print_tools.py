import sys
import math


def print(*data, type='info'):
    colors = {
        'info': ['92', 'I'],
        'warning': ['93', 'W'],
        'error': ['31', '!'],
        'debug': ['36', 'D'],
        'title': ['35', 'T']
    }

    if type not in colors:
        raise ValueError('Wrong type parameter in print')

    START = '\033['
    ENDC = '\033[0m'

    if type == 'title':
        min_size = 50
        data = data[0].replace('_', ' ').capitalize()
        padd = min_size - len(data) - 2
        data = '#' + ' ' * (padd // 2) + data + ' ' * math.ceil(padd/2) + '#'
        sep = '# ' + '=' * (len(data) - 4) + ' #'
        data = sep + '\n' + data + '\n' + sep
        data = [data]

    p = '%s%sm[%s]%s ' % (START, colors[type][0], colors[type][1], ENDC)

    output = (
        p
        + ' '.join([('\n' + p).join(str(d).split('\n')) for d in data])
    )

    if hasattr(print_progress, 'output') and print_progress.output:
        sys.stdout.write('\b' * len(print_progress.output))
        sys.stdout.write(output)
        sys.stdout.write(' ' * max(0, len(print_progress.output)-len(output)))
        sys.stdout.write('\n')
        sys.stdout.write(print_progress.output)

    else:
        sys.stdout.write(output + '\n')


def print_progress(iteration, total, prefix=''):
    if not hasattr(print_progress, 'last_prog'):
        print_progress.last_prog = -1

    iteration += 1
    prog = iteration * 100 / total

    if prog - print_progress.last_prog < 0.01 and iteration != total:
        return

    print_progress.last_prog = prog

    sym = ['-', '\\', '|', '/', '-', '\\', '|', '/']

    decimals = 1
    fill = '#'  # '█'
    length = 50
    color = '\033[34m'
    ENDC = '\033[0m'

    percent = '{0:.2f}'.format(prog)

    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '.' * (length - filledLength)

    if hasattr(print_progress, 'output'):
        sys.stdout.write('\b' * len(print_progress.output))

    print_progress.output = '%s[%s]%s %s [%s] %s%% ' % (
        color,
        sym[int(prog / 10) % len(sym)],
        ENDC,
        prefix,
        bar,
        percent
    )
    sys.stdout.write(print_progress.output)
    sys.stdout.flush()

    if iteration >= total:
        sys.stdout.write('\n')
        print_progress.output = ''


def intro_message():
    sys.stdout.write(
        r'''
   ____        _   _ _             _____       _            _
  / __ \      | | | (_)           |  __ \     | |          | |
 | |  | |_   _| |_| |_  ___ _ __  | |  | | ___| |_ ___  ___| |_ ___  _ __
 | |  | | | | | __| | |/ _ \ '__| | |  | |/ _ \ __/ _ \/ __| __/ _ \| '__|
 | |__| | |_| | |_| | |  __/ |    | |__| |  __/ ||  __/ (__| || (_) | |
  \____/ \__,_|\__|_|_|\___|_|    |_____/ \___|\__\___|\___|\__\___/|_|

  An outlier detection tool''' + '\n\n')
