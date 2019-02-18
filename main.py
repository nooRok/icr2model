# coding: utf-8
import argparse

from model import Model


class Arguments(argparse.ArgumentParser):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_argument('input', help='input .3do filepath')
        self.add_argument('output', help='output .3do filepath')
        self.add_argument('-no-opt', '--no-optimize-flavors',
                          dest='no_opt',
                          action='store_false',
                          help='do not optimize .3do flavors '
                               '(sorting and removing duplicates)')


def get_def(model, optimize=True):
    """

    :param Model model:
    :param bool optimize:
    :return: {'vertex': VERTEX.DEF, 'flavor': FLAVOR.DEF}
    :rtype: dict[str, str]
    """
    files = (model.header.files['mip'],
             model.header.files['pmp'],
             model.header.files['3do'])
    f_def = ['NUM {} {} {}'.format(*map(len, files))]
    for list_ in files:
        f_def.extend(map('FIL {}'.format, list_))
    flavors = [f for _, f in
               sorted(model.body.get_remapped_flavors(optimize).items())]
    f_def.extend(f.format() for f in flavors if f.type != 0)
    v_def = ['TYP 1']
    v_def.extend(sorted((f.format() for f in flavors if f.type == 0),
                        key=lambda f: (f.vtype, f.offset)))
    return {'vertex': '\n'.join(v_def), 'flavor': '\n'.join(f_def)}


if __name__ == '__main__':
    args_ = Arguments().parse_args()
    m = Model(args_.input)
    m.read()
    m.write(args_.output, args_.no_opt)
