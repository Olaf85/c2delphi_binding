import sys
from optparse import OptionParser
from spark import GenericScanner, GenericParser

################################################################################

T_KEY = 0
T_ID = 1
T_SEP = 2

keywords = ["FUNCTION", "PROCEDURE"]

class Token:

    _types = ["KEY", "ID", "SEP"]

    def __init__(self, type, value):
        self.type = type
        self.value = value

    def __eq__(self, other):
        if self.type == T_KEY:
            return self.value == other.upper()
        elif self.type == T_ID:
            return other == "ID"
        elif self.type == T_SEP:
            return self.value == other

    def __repr__(self):
        return "%s(%r)" %(self._types[self.type], self.value)

class Scanner(GenericScanner):

    def __init__(self):
        GenericScanner.__init__(self)
        self.tokens = []
        self._pos = 1

    def t_keyword(self, token):
        r"[a-zA-Z_]\w*"
        token = token.upper()
        if token in keywords:
            token = Token(T_KEY, token)
        else:
            token = Token(T_ID, token)
        self.tokens.append(token)

    def t_sep(self, token):
        r"[();:,]"
        self.tokens.append(Token(T_SEP, token))

    def t_comment(self, token):
        r"\#.*\n"
        self._pos += token.count("\n")

    def t_space(self, token):
        r"\s+"
        self._pos += token.count("\n")

    def t_default(self, token):
        r"[\s\S]+"
        raise SyntaxError, "unknown symbol \"%s\" in line %d" \
              %(token.split()[0], self._pos)

################################################################################

class Procedure:

    def __init__(self):
        self.type = ""
        self.name = ""
        self.params = []
        self.ret = None
        self.directives = []

class Parser(GenericParser):

    def __init__(self):
        GenericParser.__init__(self, start="proc_file")
        self.procedures = []

    def p_proc_file(self, args):
        """ proc_file ::= procedure_declarations
        """
        self.procedures = args[0]

    def p_procedure_declarations(self, args):
        """ procedure_declarations ::= procedure_declaration
            procedure_declarations ::= procedure_declaration procedure_declarations
        """
        if len(args) == 1:
            ret = [args[0]]
        else:
            if type(args[0]) == list:
                ret = args[0]
            else:
                ret = [args[0]]
            ret += args[1]
        return ret

    def p_procedure_declaration(self, args):
        """ procedure_declaration ::= procedure ;
            procedure_declaration ::= procedure ; directives
        """
        p = args[0]
        if len(args) == 3:
            p.directives = [i.value for i in args[2]]
        return p

    def p_directive(self, args):
        """ directives ::= ID ;
            directives ::= directives ID ;
        """
        if len(args) == 2:
            ret = args[0]
        else:
            if type(args[0]) == list:
                ret = args[0]
            else:
                ret = [args[0]]
            ret += [args[1]]
        return ret

    def p_procedure(self, args):
        """ procedure ::= PROCEDURE ID params_list
            procedure ::= FUNCTION ID params_list : ID
        """
        p = Procedure()
        p.type = args[0].value
        p.name = args[1].value
        p.params = [[i[0].value, i[1].value] for i in args[2]]
        if p.type == "FUNCTION":
            p.ret = args[4].value
        return p

    def p_params_list(self, args):
        """ params_list ::= ( )
            params_list ::= ( params )
        """
        if len(args) == 3:
            return args[1]
        return []

    def p_params(self, args):
        """ params ::= param
            params ::= params ; param
        """
        ret = args[0]
        if len(args) == 3:
            ret += args[2]
        return ret
        

    def p_param(self, args):
        """ param ::= id_list : ID
        """
        if type(args[0]) == list:
            ret = []
            for i in args[0]:
                ret.append([i, args[2]])
        else:
            ret = [[args[0], args[2]]]
        return ret

    def p_id_list(self, args):
        """ id_list ::= id_list , ID
            id_list ::= ID
        """
        if len(args) == 1:
            ret = args[0]
        else:
            if type(args[0]) == list:
                ret = args[0]
            else:
                ret = [args[0]]
            ret += [args[2]]
        return ret

################################################################################

if __name__ == "__main__":

    parser = OptionParser()
    parser.add_option("-p", "--project", dest="project_name",
                      help="project name")
    parser.add_option("-f", "--file", dest="file_path",
                      help="path to the processing file")
    (options, args) = parser.parse_args()

    try:
        in_file = open(options.file_path)
    except IOError:
        raise IOError("no such file: %s" %options.file_path)

    try:
        out_file = open("./%s_procs.inc" %options.project_name, "w")
    except IOError:
        raise IOError("can't create file: %s" %options.file_path)

    print "Processing..."

    scanner = Scanner()
    scanner.tokenize(in_file.read())
    parser = Parser()
    parser.parse(scanner.tokens)
    procedures = parser.procedures

    out = "{This file is autogenerated. Don't edit it!}\n\n"
    for procedure in procedures:
        out += "%s " %procedure.type.lower()
        out += "%s(" %procedure.name.lower()

        if len(procedure.params) > 0:
            out += "%s: %s" %(procedure.params[0][0].lower(), procedure.params[0][1].lower())
            if len(procedure.params) > 1:
                for param in procedure.params[1: ]:
                    out += "; %s: %s" %(param[0].lower(), param[1].lower())
        out += ")"

        if procedure.type == "FUNCTION":
            out += ": %s;" %procedure.ret.lower()
        else:
            out += ";"

        procedure.directives.append("cdecl")
        procedure.directives.append("external")

        for directive in procedure.directives:
            out += " %s;" %directive.lower()
        out += "\n"

    out_file.write(out)
    out_file.close()

    print "Done."
