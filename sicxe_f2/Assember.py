import re
import instfile


class Entry:
    def __init__(self, string, token, attribute):
        self.string = string
        self.token = token
        self.att = attribute


symtable = []

# print(symtable[12].string + ' ' + str(symtable[12].token) + ' ' + str(symtable[12].att))


def lookup(s):
    for i in range(0, symtable.__len__()):
        if s == symtable[i].string:
            return i
    return -1


def insert(s, t, a):
    symtable.append(Entry(s, t, a))
    return symtable.__len__() - 1


def init():
    for i in range(0, instfile.inst.__len__()):
        insert(instfile.inst[i], instfile.token[i], instfile.opcode[i])
    for i in range(0, instfile.directives.__len__()):
        insert(instfile.directives[i], instfile.dirtoken[i], instfile.dircode[i])
    # in case of extension of the architecture
    for i in range(0, instfile.inst_ex.__len__()):
        insert(
            instfile.inst_ex[i], instfile.inst_token_ex[i], instfile.inst_ex_opcode[i]
        )
    for i in range(0, instfile.dir_ex.__len__()):
        insert(instfile.dir_ex[i], instfile.dir_ex_token[i], instfile.dir_ex_code[i])

file = open("input.sic", "r")  # open the user input file (here called input.sic)
#with open("input.sic", "r") as file:
 #   file.read()
    # open the user input file (here called input.sic)
filecontent = []  # the input file will be parsed to
bufferindex = 0
tokenval = 0
lineno = 1
pass1or2 = 1
locctr = 0
lookahead = ""
startLine = True

Xbit4set = 0x800000
Bbit4set = 0x400000
Pbit4set = 0x200000
Ebit4set = 0x100000

Nbitset = 2
Ibitset = 1

Xbit3set = 0x8000
Bbit3set = 0x4000
Pbit3set = 0x2000
Ebit3set = 0x1000


def is_hex(s):
    if s[0:2].upper() == "0X":
        try:
            int(s[2:], 16)
            return True
        except ValueError:
            return False
    else:
        return False


def lexan():
    global filecontent, tokenval, lineno, bufferindex, locctr, startLine

    while True:
        # if filecontent == []:
        if len(filecontent) == bufferindex:
            return "EOF"
        elif filecontent[bufferindex] == "\n":
            startLine = True
            # del filecontent[bufferindex]
            bufferindex = bufferindex + 1
            lineno += 1
        else:
            break
    if filecontent[bufferindex].isdigit():
        tokenval = int(
            filecontent[bufferindex]
        )  # all number are considered as decimals
        # del filecontent[bufferindex]
        bufferindex = bufferindex + 1
        return "NUM"
    elif is_hex(filecontent[bufferindex]):
        tokenval = int(
            filecontent[bufferindex][2:], 16
        )  # all number starting with 0x are considered as hex
        # del filecontent[bufferindex]
        bufferindex = bufferindex + 1
        return "NUM"
    elif filecontent[bufferindex] in ["+", "#", ",", "@"]:
        c = filecontent[bufferindex]
        # del filecontent[bufferindex]
        bufferindex = bufferindex + 1
        return c
    else:
        # check if there is a string or hex starting with C'string' or X'hex'
        if (filecontent[bufferindex].upper() == "C") and (
            filecontent[bufferindex + 1] == "'"
        ):
            bytestring = ""
            bufferindex += 2
            while (
                filecontent[bufferindex] != "'"
            ):  # should we take into account the missing ' error?
                bytestring += filecontent[bufferindex]
                bufferindex += 1
                if filecontent[bufferindex] != "'":
                    bytestring += " "
            bufferindex += 1
            bytestringvalue = "".join("%02X" % ord(c) for c in bytestring)
            bytestring = "1_" + bytestring
            p = lookup(bytestring)
            if p == -1:
                p = insert(
                    bytestring, "STRING", bytestringvalue
                )  # should we deal with literals?
            tokenval = p
        elif (
            filecontent[bufferindex] == "'"
        ):  # a string can start with C' or only with '
            bytestring = ""
            bufferindex += 1
            while (
                filecontent[bufferindex] != "'"
            ):  # should we take into account the missing ' error?
                bytestring += filecontent[bufferindex]
                bufferindex += 1
                if filecontent[bufferindex] != "'":
                    bytestring += " "
            bufferindex += 1
            bytestringvalue = "".join("%02X" % ord(c) for c in bytestring)
            bytestring = "1_" + bytestring
            p = lookup(bytestring)
            if p == -1:
                p = insert(
                    bytestring, "STRING", bytestringvalue
                )  # should we deal with literals?
            tokenval = p
        elif (filecontent[bufferindex].upper() == "X") and (
            filecontent[bufferindex + 1] == "'"
        ):
            bufferindex += 2
            bytestring = filecontent[bufferindex]
            bufferindex += 2
            # if filecontent[bufferindex] != '\'':# should we take into account the missing ' error?

            bytestringvalue = bytestring
            if len(bytestringvalue) % 2 == 1:
                bytestringvalue = "0" + bytestringvalue
            bytestring = "2_" + bytestring
            p = lookup(bytestring)
            if p == -1:
                p = insert(
                    bytestring, "HEX", bytestringvalue
                )  # should we deal with literals?
            tokenval = p
        else:
            p = lookup(filecontent[bufferindex].upper())
            if p == -1:
                if startLine == True:
                    p = insert(
                        filecontent[bufferindex].upper(), "ID", locctr
                    )  # should we deal with case-sensitive?
                else:
                    p = insert(
                        filecontent[bufferindex].upper(), "ID", -1
                    )  # forward reference
            else:
                if (symtable[p].att == -1) and (startLine == True):
                    symtable[p].att = locctr
            tokenval = p
            # del filecontent[bufferindex]
            bufferindex = bufferindex + 1
        return symtable[p].token


# ---------------------------------------------------------------------------
# PASS 2 additions
#   Pass 1 (pass1or2 == 1): give addresses to labels (same as the pass1 folder)
#   Pass 2 (pass1or2 == 2): every label now has its address, so we can build
#                           the object code of every line and print it.
# ---------------------------------------------------------------------------
objectProgram = True  # True: print H/T/E records, False: print a listing (address + object code)
errorcount = 0        # number of errors found (no object code if > 0)
inst = 0              # object code of the current instruction (built in pass 2)
startAddr = 0         # starting address of the program
progsize = 0          # program length (computed at the end of pass 1)
progname = ""         # program name (for the H record)

# the T record that is being filled
textStart = -1        # address of the first byte in the current T record (-1 = empty)
textCodes = []        # object codes inside the current T record (hex strings)
textLength = 0        # number of bytes inside the current T record


def error(s):
    global lineno, errorcount
    errorcount += 1
    print("line " + str(lineno) + ": " + s)


def match(token):
    global lookahead
    if lookahead == token:
        lookahead = lexan()
    else:
        error("Syntax error")


def index():
    global bufferindex, symtable, tokenval, inst
    if lookahead == ",":
        match(",")
        if symtable[tokenval].att != 1:
            error("index regsiter should be X")
        elif pass1or2 == 2:
            inst += Xbit3set  # pass2: set the x bit (0x8000) for indexed addressing
        match("REG")
        return True
    return False


# ---------------- object program output (pass 2 only) ----------------
def flushText():
    """Print the current T record (if it has something) and empty it."""
    global textStart, textCodes, textLength
    if textLength > 0 and objectProgram:
        print("T^{:06X}^{:02X}^{}".format(textStart, textLength, "^".join(textCodes)))
    textStart = -1
    textCodes = []
    textLength = 0


def emit(code, address):
    """Add the object code `code` (hex string) of the line at `address`."""
    global textStart, textCodes, textLength
    if not objectProgram:
        print("{:04X}  {}".format(address, code))
        return
    size = len(code) // 2
    if textLength + size > 30:  # a T record holds at most 30 (0x1E) bytes
        flushText()
    if textLength == 0:
        textStart = address
    textCodes.append(code)
    textLength += size


# lab2
def header():
    global lookahead, locctr, startAddr, progname
    lookahead = lexan()
    tok = tokenval
    match("ID")
    match("START")
    # FIX: use tok (the program name's position), not tokenval (that's the NUM now)
    startAddr = symtable[tok].att = locctr = tokenval
    progname = symtable[tok].string
    match("NUM")
    if pass1or2 == 2 and objectProgram:
        # H^name (6 chars)^start address^program length  (length comes from pass 1)
        print("H^{:<6}^{:06X}^{:06X}".format(progname[:6], startAddr, progsize))


# lab3
def rest1():
    if lookahead in ("F1", "F2", "F3"):  # SIC/XE: a label can be followed by any instruction
        stmt()
    elif lookahead in ("WORD", "BYTE", "RESW", "RESB"):
        DATA()
    else:
        error("Syntax error")


# lab3 + pass2
def rest2():
    global locctr
    if lookahead not in ("STRING", "HEX"):
        error("Syntax error")
        return
    address = locctr
    code = symtable[tokenval].att  # lexan() already stored the bytes as hex: C'EOF' -> 454F46
    locctr += len(code) // 2
    if pass1or2 == 2:
        emit(code, address)
    match(lookahead)


# lab3 + pass2
def DATA():
    global locctr
    address = locctr
    if lookahead == "WORD":
        match("WORD")
        locctr += 3
        if pass1or2 == 2:
            emit("{:06X}".format(tokenval & 0xFFFFFF), address)  # a word = 3 bytes
        match("NUM")
    elif lookahead == "RESW":
        match("RESW")
        locctr += 3 * tokenval
        if pass1or2 == 2:
            flushText()  # reserved space has no object code -> start a new T record
        match("NUM")
    elif lookahead == "RESB":
        match("RESB")
        locctr += tokenval
        if pass1or2 == 2:
            flushText()
        match("NUM")
    elif lookahead == "BYTE":
        match("BYTE")
        rest2()
    else:
        error("Syntax error")


# SIC/XE  rest5 -> , REG {inst += regcode} | e
# register codes (from instfile): A=0 X=1 L=2 B=3 S=4 T=5 F=6
def rest5():
    global inst
    if lookahead == ",":
        match(",")
        if lookahead == "REG":
            inst += symtable[tokenval].att  # r2 in the low half of byte 2
        match("REG")


# lab3 + pass2
def stmt():
    global locctr, startLine, inst
    startLine = False
    # SIC/XE  STMT -> F1 {locctr += 1} {pass2: print the opcode over 1 byte}
    if lookahead == "F1":
        address = locctr
        opcode = symtable[tokenval].att  # save it: match() changes tokenval
        locctr += 1  # BEFORE match: F1 is the last token of the line
        match("F1")
        if pass1or2 == 2:
            emit("{:02X}".format(opcode), address)  # format 1 = opcode only, 1 byte
    #         | F2 {locctr += 2} {inst = opcode << 8} REG {inst += regcode << 4} rest5
    elif lookahead == "F2":
        address = locctr
        inst = symtable[tokenval].att << 8  # opcode in the first byte
        locctr += 2  # BEFORE matching the last REG of the line
        match("F2")
        if lookahead == "REG":
            inst += symtable[tokenval].att << 4  # r1 in the high half of byte 2
        match("REG")
        rest5()
        if pass1or2 == 2:
            emit("{:04X}".format(inst), address)  # format 2 = 2 bytes
    #         | F3 ID INDEX
    elif lookahead == "F3":
        address = locctr
        if pass1or2 == 2:
            inst = symtable[tokenval].att << 16  # opcode in the first byte
        match("F3")
        # FIX: add 3 BEFORE matching the last token of the line, otherwise the
        # label on the next line (read by this match) gets an address 3 too low
        locctr += 3
        if pass1or2 == 2 and lookahead == "ID":
            if symtable[tokenval].att == -1:  # used but never defined as a label
                error("undefined symbol " + symtable[tokenval].string)
            else:
                inst += symtable[tokenval].att  # operand address in the last 2 bytes
        match("ID")
        index()  # adds 0x8000 if ",X"
        if pass1or2 == 2:
            emit("{:06X}".format(inst), address)


# lab3
def body():
    global startLine
    if lookahead == "ID":
        startLine = False
        # FIX: duplicate label check -- lexan() keeps the old address of an
        # already-defined label, so its att won't equal the current locctr
        if pass1or2 == 1 and symtable[tokenval].att != locctr:
            error("duplicate symbol " + symtable[tokenval].string)
        match("ID")
        rest1()
        body()
    elif lookahead in ("F1", "F2", "F3"):  # SIC/XE: STMT BODY
        stmt()
        body()
    elif lookahead == "END":
        pass
    else:
        error("Syntax error")


# lab3 + pass2
def tail():
    global progsize, startLine
    startLine = False  # the name after END is an operand, not a new label
    match("END")
    firstInst = symtable[tokenval].att  # END prog -> execution starts at prog's address
    if firstInst == -1:  # name after END was never defined (e.g. "P1 start 0 ... end prog")
        firstInst = startAddr
    match("ID")
    if pass1or2 == 1:
        progsize = locctr - startAddr
    elif objectProgram:
        flushText()  # print the last T record
        print("E^{:06X}".format(firstInst))


def parse():
    header()
    body()
    tail()


def main():
    global filecontent, locctr, pass1or2, bufferindex, lineno
    init()
    w = file.read()
    filecontent = re.split("([\W])", w)
    i = 0
    while True:
        while (
            (filecontent[i] == " ")
            or (filecontent[i] == "")
            or (filecontent[i] == "\t")
        ):
            del filecontent[i]
            if len(filecontent) == i:
                break
        i += 1
        if len(filecontent) <= i:
            break
    if (
        filecontent[len(filecontent) - 1] != "\n"
    ):  # to be sure that the content ends with new line
        filecontent.append("\n")

    for pass1or2 in range(1, 3):
        if pass1or2 == 2 and errorcount > 0:
            print("Pass 1 found errors: no object code generated")
            break
        parse()
        bufferindex = 0
        locctr = 0
        lineno = 1

    file.close()


main()
