

cat commands.src | sed "s#^\([A-Z]\+\)#def \1(#" | \
sed "s#def \([A-Z]\+\)( \+<SP> <\([a-z-]\+\)>#def \1(\2#" | \
sed "s#def \([A-Z]\+\)( *\[<SP> <\([a-z-]\+\)>\]#def \1(\2#" | \
sed "s# *<CRLF>#):#" | \
sed "s#decimal-integer \[<SP> R <SP> <decimal-integer>\]#decimal1, decimal2#" | \
sed "s#def \([A-Z]\+\)(\([^)]*\)):#\
\ndef \1(self, \2):\n\
    "'"""'"\n\
    :type \2: str\n\
    :rtype: str\n\
    \"\"\"\n\
    self.send_cmd('\1 ' + \2)\n\
    resp = self.getresp()\n\
    if resp[:3] not in \1_acceptable:\n\
        raise error.ImpossiburuAnswer(resp)\n\
    return resp#" | \
sed "s#send_cmd(\([^=)]*\)[^)]*)#send_cmd(\1)#" | \
sed "s#(self, )#(self)#" | \
sed "s#:type : str##" | \
sed "s#send_cmd('\([A-Z]*\) ' + )#send_cmd('\1')#" | \
sed "s#\([a-z]\+\)-\([a-z]\+\)#\1_\2#g" | \
sed "s#^#    #" | \
sed "s/^    $//"

echo

cat accpt.src | tr -d "\n" | tr -d " " | tr -d "(" | tr -d ")" | \
sed "s#[A-Z][a-z]\+##g" | \
sed "s%\([A-Z]\)\([0-9]\)%\1_acceptable = [421,\2%g" | \
sed "s%\([0-9,]\)\([A-Z]\)%\1\n\2%g" | \
sed "s%\([0-9][0-9][0-9]\)%'\1',%g" | \
sed "s%,,%,%g" | \
sed "s%,\([0-9]\)%, \1%g" | \
sed "s%,$%]%g"

echo
