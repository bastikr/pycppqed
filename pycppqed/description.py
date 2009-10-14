import utils
import quantumsystem


class Description:
    """
    A class for working with the comment section of a C++QED output file.

    *Arguments*
        * *commentstr*
            A string following the style of the comment section of C++QED
            output files.
    """
    def __init__(self, commentstr):
        self.commentstr = commentstr
        sections = commentstr.split("\n\n")
        self.head = sections[0]
        self.quantumsystem = QuantumSystem(sections[1:-1])
        self.expvalues = ExpectationValues(sections[-1])


QUANTUMSYSTEMS = {}
for sys in quantumsystem.SYSTEMS:
    QUANTUMSYSTEMS[sys.__name__] = sys


class QuantumSystem:
    def __init__(self, buf):
        buf[0] = buf[0][buf[0].find("# Subsystem Nr."):]
        self.subsystems = subs = []
        for s in buf:
            if not s.startswith("# Subsystem Nr."):
                break
            subs.append(eval(s.split("\n")[1].strip("# "), QUANTUMSYSTEMS))


class ExpectationValues:
    """
    A class representing the datakey section of C++QED output files.
    """
    def __init__(self, datakeystr):
        sectionstrs = datakeystr.split("\n# ")[1:]
        self.subsystems = subsystems = []
        for sectionstr in sectionstrs:
            if sectionstr.find(".") == -1: # No Expectation Values!
                continue
            subsystems.append(ExpectationValuesSubsection(sectionstr))


class ExpectationValuesSubsection:
    """
    A class representing a single set of keys in the datakey section.
    """
    def __init__(self, sectionstr):
        self.name, keystr = sectionstr.split(" ", 1)
        self.entrys = entrys = utils.OrderedDict()
        pos_dot = keystr.find(".")
        if pos_dot == -1:
            raise ValueError("Bad formatted Expectation Value String: %s" % \
                             sectionstr)
        pos_start = 0
        while True:
            pos_nextdot = keystr.find(".", pos_dot+1)
            if pos_nextdot == -1:
                key = int(keystr[pos_start:pos_dot]) - 1
                value = keystr[pos_dot+1:].strip()
                entrys[key] = value
                break
            pos_nextstart = keystr.rfind(" ", 0, pos_nextdot)
            key = int(keystr[pos_start:pos_dot]) - 1
            value = keystr[pos_dot+1:pos_nextstart].strip()
            entrys[key] = value
            pos_start, pos_dot = pos_nextstart, pos_nextdot


