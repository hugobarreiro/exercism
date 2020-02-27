class SgfTree:
    def __init__(self, properties=None, children=None):
        self.properties = properties or {}
        self.children = children or []

    def __eq__(self, other):
        if not isinstance(other, SgfTree):
            return False
        for k, v in self.properties.items():
            if k not in other.properties:
                return False
            if other.properties[k] != v:
                return False
        for k in other.properties.keys():
            if k not in self.properties:
                return False
        if len(self.children) != len(other.children):
            return False
        for a, b in zip(self.children, other.children):
            if a != b:
                return False
        return True

    def __ne__(self, other):
        return not self == other


# --------------- lex --------------- #

tokens = (
    'LPAREN', 'RPAREN', 'LBRACKET', 'RBRACKET',
    'SEMICOLON', 'NEWLINE', 'SPACE',
    'NAME', 'ESCAPE'
)

t_LPAREN = r'\('
t_RPAREN = r'\)'
t_LBRACKET = r'\['
t_RBRACKET = r'\]'
t_SEMICOLON = r';'
t_NEWLINE = r'\n'
t_ESCAPE = r'\\.'
t_NAME = r'[a-zA-Z0-9_]+'


def t_SPACE(t):
    r"""[\t ]"""
    t.value = ' '
    return t


from ply import lex
lex.lex()


# --------------- yacc --------------- #

def p_tree(p):
    """tree : LPAREN node RPAREN"""
    p[0] = p[2]


def p_empty(p):
    """empty :"""
    p[0] = ''


def p_escape_value(p):
    """value : ESCAPE"""
    p[0] = p[1][1]


def p_value(p):
    """value : NAME empty
             | value SPACE
             | value NEWLINE
             | value NAME
             | value value"""
    p[0] = p[1]+p[2]


def p_property_value(p):
    """propvalue : LBRACKET value RBRACKET"""
    p[0] = [p[2]]


def p_property_multivalue(p):
    """propvalue : propvalue propvalue"""
    p[0] = p[1]+p[2]


def p_property(p):
    """property : value propvalue"""
    if not str.isupper(p[1]):
        raise ValueError('Property identifier {} is not uppercased'.format(p[1]))
    p[0] = {p[1]: p[2]}


def p_multiproperties(p):
    """property : property property"""
    multiproperties = dict()
    multiproperties.update(p[1])
    multiproperties.update(p[2])
    p[0] = multiproperties


def p_node(p):
    """node : SEMICOLON property"""
    p[0] = SgfTree(properties=p[2])


def p_empty_node(p):
    """node : SEMICOLON empty"""
    p[0] = SgfTree()


def p_node_children(p):
    """node : node tree
            | node node"""
    p[0] = p[1]
    p[0].children.append(p[2])


from ply import yacc
parser = yacc.yacc()


def parse(input_string):

    if not isinstance(input_string, str):
        raise TypeError('The informed input is not a string.')

    result = parser.parse(input_string)
    if result is None:
        raise ValueError('Incorrect syntax.')
    return result
