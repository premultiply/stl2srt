#!/usr/bin/env python
# -*- encoding=utf8 -*-
#
# STL2WebVTT A program to convert EBU STL subtitle files in the more common WebVTT format
#
# Copyright 2014 Yann Coupin
# Copyright 2016 Ulrich Peters
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Import modules for CGI handling 
import cgi, cgitb

import struct
import codecs
import logging
import unicodedata
from xml.etree import ElementTree
import re

import os.path
import sys


class WebVTT:
    '''A class that behaves like a file object and writes an WebVTT file'''
    def __init__(self):
        print codecs.BOM_UTF8 + "WEBVTT"

    def _formatTime(self, timestamp):
        return "%02u:%02u:%02u.%03u" % (
            timestamp / 3600,
            (timestamp / 60) % 60,
            timestamp % 60,
            (timestamp * 1000) % 1000
        )

    def write(self, start, end, text, sn, format):
        text = "\n".join(filter(lambda (x): bool(x), text.split("\n")))
        print "\n%d\n%s --> %s %s\n%s" % (sn, self._formatTime(start), self._formatTime(end), format, text.encode('utf8'))

class iso6937(codecs.Codec):
    '''A class to implement the somewhat exotic iso-6937 encoding which STL files often use'''

    identical = set(range(0x20, 0x7f))
    identical |= set((0xa, 0xa0, 0xa1, 0xa2, 0xa3, 0xa5, 0xa7, 0xab, 0xb0, 0xb1, 0xb2, 0xb3, 0xb5, 0xb6, 0xb7, 0xbb, 0xbc, 0xbd, 0xbe, 0xbf))
    direct_mapping = {
        0x8a: 0x000a, # line break

        0xa8: 0x00a4, # ¤
        0xa9: 0x2018, # ‘
        0xaa: 0x201C, # “
        0xab: 0x00AB, # «
        0xac: 0x2190, # ←
        0xad: 0x2191, # ↑
        0xae: 0x2192, # →
        0xaf: 0x2193, # ↓

        0xb4: 0x00D7, # ×
        0xb8: 0x00F7, # ÷
        0xb9: 0x2019, # ’
        0xba: 0x201D, # ”
        0xbc: 0x00BC, # ¼
        0xbd: 0x00BD, # ½
        0xbe: 0x00BE, # ¾
        0xbf: 0x00BF, # ¿

        0xd0: 0x2015, # ―
        0xd1: 0x00B9, # ¹
        0xd2: 0x00AE, # ®
        0xd3: 0x00A9, # ©
        0xd4: 0x2122, # ™
        0xd5: 0x266A, # ♪
        0xd6: 0x00AC, # ¬
        0xd7: 0x00A6, # ¦
        0xdc: 0x215B, # ⅛
        0xdd: 0x215C, # ⅜
        0xde: 0x215D, # ⅝
        0xdf: 0x215E, # ⅞

        0xe0: 0x2126, # Ohm Ω
        0xe1: 0x00C6, # Æ
        0xe2: 0x0110, # Đ
        0xe3: 0x00AA, # ª
        0xe4: 0x0126, # Ħ
        0xe6: 0x0132, # Ĳ
        0xe7: 0x013F, # Ŀ
        0xe8: 0x0141, # Ł
        0xe9: 0x00D8, # Ø
        0xea: 0x0152, # Œ
        0xeb: 0x00BA, # º
        0xec: 0x00DE, # Þ
        0xed: 0x0166, # Ŧ
        0xee: 0x014A, # Ŋ
        0xef: 0x0149, # ŉ

        0xf0: 0x0138, # ĸ
        0xf1: 0x00E6, # æ
        0xf2: 0x0111, # đ
        0xf3: 0x00F0, # ð
        0xf4: 0x0127, # ħ
        0xf5: 0x0131, # ı
        0xf6: 0x0133, # ĳ
        0xf7: 0x0140, # ŀ
        0xf8: 0x0142, # ł
        0xf9: 0x00F8, # ø
        0xfa: 0x0153, # œ
        0xfb: 0x00DF, # ß
        0xfc: 0x00FE, # þ
        0xfd: 0x0167, # ŧ
        0xfe: 0x014B, # ŋ
        0xff: 0x00AD, # Soft hyphen
    }
    diacritic = {
        0xc1: 0x0300, # grave accent
        0xc2: 0x0301, # acute accent
        0xc3: 0x0302, # circumflex
        0xc4: 0x0303, # tilde
        0xc5: 0x0304, # macron
        0xc6: 0x0306, # breve
        0xc7: 0x0307, # dot
        0xc8: 0x0308, # umlaut
        0xca: 0x030A, # ring
        0xcb: 0x0327, # cedilla
        0xcd: 0x030B, # double acute accent
        0xce: 0x0328, # ogonek
        0xcf: 0x030C, # caron
    }


    def decode(self, input):
        output = []
        state = None
        count = 0
        for char in input:
            char = ord(char)
            # End of a subtitle text
            count += 1
            if not state and char in self.identical:
                output.append(char)
            elif not state and char in self.direct_mapping:
                output.append(self.direct_mapping[char])
            elif not state and char in self.diacritic:
                state = self.diacritic[char]
            elif state:
                combined = unicodedata.normalize('NFC', unichr(char) + unichr(state))
                if combined and len(combined) == 1:
                    output.append(ord(combined))
                state = None
        return (''.join(map(unichr, output)), len(input))

    def search(self, name):
        if name in ('iso6937', 'iso_6937-2'):
            return codecs.CodecInfo(self.encode, self.decode, name='iso_6937-2')

    def encode(self, input):
        pass

codecs.register(iso6937().search)

class RichText:

    def __init__(self, use_html_tags):
        self.tag_stack = []
        self.opened_tags = set()
        self.output = []
        self.add_html_tags = use_html_tags

    def write(self, string):
        self.output.append(string)

#    def write(self, string, fg, bg):
#        if len(string) > 0:
#            if self.fg_color !== fg | self.bg_color !== bg:
#                self.closeTag('c')
#                output.openTag('c', '<c.%s.%s>' % (colorCodes[fg], 'bg_' + colorCodes[bg])
#                self.fg_color = fg
#                self.bg_color = bg
#            self.output.append(string)

    def openTag(self, tag_name, tag_html=None):
        if not tag_html:
            tag_html = '<%s>' % tag_name
        if tag_name not in self.opened_tags:
            self.tag_stack.append((tag_name, tag_html))
            self.opened_tags.add(tag_name)
            if not self.add_html_tags:
                self.output.append(' ')
            else:
                self.output.append(tag_html)

    def closeTag(self, tag):
        if not self.add_html_tags:
            return
        tag_html = '</%s>' % tag
        if tag in self.opened_tags:
            reopen_stack = []
            while self.tag_stack:
                tag_to_close = self.tag_stack.pop()
                if tag_to_close[0] == tag:
                    self.output.append(tag_html)
                    self.opened_tags.remove(tag)
                    break
                else:
                    reopen_stack += tag_to_close
            for tag_to_reopen in reopen_stack:
                self.output.append(tag_to_reopen[1])
                self.tag_stack.append(tag_to_reopen)

    def __str__(self):
        if not self.add_html_tags:
            return ''.join(self.output)

        closing_tags = []
        # Close all the tags still open
        for tag in self.tag_stack[::-1]:
            closing_tags.append('</%s>' % tag[0])
        return ''.join(self.output + closing_tags)

class STL:
    '''A class that behaves like a file object and reads an STL file'''

    GSIfields = 'CPN DFC DSC CCT LC OPT OET TPT TET TN TCD SLR CD RD RN TNB TNS TNG MNC MNR TCS TCP TCF TND DSN CO PUB EN ECD UDA'.split(' ')
    TTIfields = 'SGN SN EBN CS TCIh TCIm TCIs TCIf TCOh TCOm TCOs TCOf VP JC CF TF'.split(' ')

    def __init__(self, pathOrFile, richFormatting=False, startTimecode=0.0):
        self.file = open(pathOrFile, 'rb')

        self.richFormatting = richFormatting
        self.startTimecode = startTimecode

        self._readGSI()

        print "\nNOTE"
        print "Code Page Number: "  + self.GSI['CPN']
        print "Disk Format Code: "  + self.GSI['DFC']
        print "Display Standard Code: "  + self.GSI['DSC']
        print "Character Code Table number: "  + self.GSI['CCT']
        print "Language Code: "  + self.GSI['LC']
        print "Original Programme Title: "  + self.GSI['OPT'].decode(self.gsiCodePage).encode('utf-8')
        print "Original Episode Title: "  + self.GSI['OET'].decode(self.gsiCodePage).encode('utf-8')
        print "Translated Programme Title: "  + self.GSI['TPT'].decode(self.gsiCodePage).encode('utf-8')
        print "Translated Episode Title: "  + self.GSI['TET'].decode(self.gsiCodePage).encode('utf-8')
        print "Translator's Name: "  + self.GSI['TN'].decode(self.gsiCodePage).encode('utf-8')
        print "Translator's Contact Details: "  + self.GSI['TCD'].decode(self.gsiCodePage).encode('utf-8')
        print "Subtitle List Reference Code: "  + self.GSI['SLR']
        print "Creation Date: "  + self.GSI['CD']
        print "Revision Date: "  + self.GSI['RD']
        print "Revision number: "  + self.GSI['RN']
        print "Total Number of Text and Timing Information (TTI) blocks: "  + self.GSI['TNB']
        print "Total Number of Subtitles: "  + self.GSI['TNS']
        print "Total Number of Subtitle Groups: "  + self.GSI['TNG']
        print "Maximum Number of Displayable Characters in any text row: "  + self.GSI['MNC']
        print "Maximum Number of Displayable Rows: "  + self.GSI['MNR']
        print "Time Code: Status: "  + self.GSI['TCS']
        print "Time Code: Start-of-Programme: "  + self.GSI['TCP']
        print "Time Code: First In-Cue: "  + self.GSI['TCF']
        print "Total Number of Disks: "  + self.GSI['TND']
        print "Disk Sequence Number: "  + self.GSI['DSN']
        print "Country of Origin: "  + self.GSI['CO']
        print "Publisher: "  + self.GSI['PUB'].decode(self.gsiCodePage).encode('utf-8')
        print "Editor's Name: "  + self.GSI['EN'].decode(self.gsiCodePage).encode('utf-8')
        print "Editor's Contact Details: "  + self.GSI['ECD'].decode(self.gsiCodePage).encode('utf-8')
        #print "User-Defined Area: "  + self.GSI['UDA'].decode(self.gsiCodePage).encode('utf-8')

    def __bcdTimestampDecode(self, timestamp):
        # Special case for people that can't bother to read a spec
        if timestamp == '________':
            return 0.0

        # BCD coded time with limited significant bits as per EBU Tech. 3097-E
        safe_bytes = map(lambda x: x[0]&x[1], zip((0x2, 0xf, 0x7, 0xf, 0x7, 0xf, 0x3, 0xf), struct.unpack('8B', timestamp)))
        return sum(map(lambda x: x[0]*x[1], zip((36000, 3600, 600, 60, 10, 1, 10.0 / self.fps, 1.0 / self.fps), safe_bytes)))

    def _readGSI(self):
        self.GSI = dict(zip(
            self.GSIfields,
            struct.unpack('3s8sc2s2s32s32s32s32s32s32s16s6s6s2s5s5s3s2s2s1s8s8s1s1s3s32s32s32s75x576s', self.file.read(1024))
        ))
        GSI = self.GSI
        logging.debug(GSI)
        self.gsiCodePage = 'cp%s' % GSI['CPN']
        if GSI['DFC'] == 'STL24.01':
            self.fps = 24
        elif GSI['DFC'] == 'STL25.01':
            self.fps = 25
        elif GSI['DFC'] == 'STL30.01':
            self.fps = 30
        else:
            raise Exception('Invalid DFC')
        self.codePage = {
            '00': 'iso_6937-2',
            '01': 'iso-8859-5',
            '02': 'iso-8859-6',
            '03': 'iso-8859-7',
            '04': 'iso-8859-8',
        }[GSI['CCT']]
        self.numberOfTTI = int(GSI['TNB'])
        #if GSI['TCS'] == '1':
            # BCD coded time with limited significant bits

        #    self.startTime = self.__bcdTimestampDecode(GSI['TCP'])
        #else:
        self.startTime = self.startTimecode
        logging.debug(self.__dict__)

    def __timecodeDecode(self, h, m, s, f):
        return 3600 * h + 60 * m + s + float(f) / self.fps

    def __parseFormatting(self, text, addHtmlTags):
        colorCodes = [
            'black',       # black
            'red',         # red
            'green',       # green
            'yellow',      # yellow
            'blue',        # blue
            'magenta',     # magenta
            'cyan',        # cyan
            'white',       # white
            'transparent', # transparent
        ]
        currentColor   = 0x7 # White is the default color
        currentBgColor = 0x0 # Black is the default background color
        output = RichText(addHtmlTags)
        self.outEnabled = False
        output.write('<c.box>')

        for char in text:
            ochar = ord(char)
            #print hex(ochar) + "\t" + char
            if ((ochar >= 0x20) & (ochar < 0x7f)) | (ochar >= 0xa1):
                if self.outEnabled:
                    output.write(char)
            elif ochar in (0x00,0x01,0x02,0x03,0x04,0x05,0x06,0x07): #TTX alpha
                if self.outEnabled:
                    output.write(' ')
                if currentColor != ochar:
                    currentColor = ochar
                    output.closeTag('c')
                    output.openTag('c', '<c.%s.%s>' % (colorCodes[currentColor], 'bg_' + colorCodes[currentBgColor]))
            #elif ochar == 0x08: #TTX flash
            #elif ochar == 0x09: #TTX steady *@
            elif ochar == 0x0a: #TTX box end *@
                self.outEnabled = False
            elif ochar == 0x0b: #TTX box start
                self.outEnabled = True
            #elif ochar == 0x0c: #TTX normal height
            #elif ochar == 0x0d: #TTX double height
            #elif ochar == 0x0e: #TTX double width
            #elif ochar == 0x0f: #TTX double size
            elif ochar == 0x1c: #TTX black background *@
                currentBgColor = 0x0
                output.closeTag('c')
                output.openTag('c', '<c.%s.%s>' % (colorCodes[currentColor], 'bg_' + colorCodes[currentBgColor]))
                if self.outEnabled:
                    output.write(' ')
            elif ochar == 0x1d: #TTX new background @
                currentBgColor = currentColor
                currentColor = 0x7
                output.closeTag('c')
                output.openTag('c', '<c.%s.%s>' % (colorCodes[currentColor], 'bg_' + colorCodes[currentBgColor]))
                if self.outEnabled:
                    output.write(' ')
            elif ochar == 0x80: #STL italics on (open)
                if self.outEnabled:
                    output.write(' ')
                output.openTag('i')
            elif ochar == 0x81: #STL italics off (open)
                output.closeTag('i')
                if self.outEnabled:
                    output.write(' ')
            elif ochar == 0x82: #STL underline on (open)
                if self.outEnabled:
                    output.write(' ')
                output.openTag('u')
            elif ochar == 0x83: #STL underline off (open)
                output.closeTag('u')
                if self.outEnabled:
                    output.write(' ')
            #elif ochar == 0x84: #STL boxing on (open)
            #elif ochar == 0x85: #STL boxing off (open)
            elif ochar == 0x8a: #STL CR/LF (new line)
                output.closeTag('c')
                output.write("\n")
                currentColor = 0x7
                currentBgColor = 0x0
                self.outEnabled = False
            elif ochar == 0x8f: #unused space
                self.outEnabled = False
                break
            elif self.outEnabled:
                output.write(' ')

        output.write('</c>')
        return str(output)

    def _readTTI(self):
        justificationCodes = [
            'size:80%',             # unchanged presentation
            'position:10% align:start size:80%',  # left-justified text
            'position:50% align:middle size:80%', # centred text
            'position:90% align:end size:80%',    # right-justified text
        ]

        while (True):
            tci = None
            tco = None
            txt = []

            while (True):
                data = self.file.read(128)
                if not data:
                    raise StopIteration()
                TTI = dict(zip(
                    self.TTIfields,
                    struct.unpack('<BHBBBBBBBBBBBBB112s', data)
                ))
                logging.debug(TTI)
                # if comment skip
                if TTI['CF']:
                    continue
                if not tci:
                    tci = self.__timecodeDecode(TTI['TCIh'], TTI['TCIm'], TTI['TCIs'], TTI['TCIf']) - self.startTime
                    tco = self.__timecodeDecode(TTI['TCOh'], TTI['TCOm'], TTI['TCOs'], TTI['TCOf']) - self.startTime
                text = TTI['TF']
                text = self.__parseFormatting(TTI['TF'], self.richFormatting)
                text = text.decode(self.codePage)
                txt += text
                if TTI['EBN'] == 255:
                    # skip empty subtitles and those before the start of the show
                    if txt and tci >= 0:
                        return (tci, tco, ''.join(txt), TTI['SN'], justificationCodes[TTI['JC']])
                    break

    def __iter__(self):
        return self
 
    def next(self):
        return self._readTTI()

if __name__ == '__main__':

    print "Content-Type: text/vtt; charset=utf-8\n"

    # Create instance of FieldStorage 
    form = cgi.FieldStorage()

    # Get data from fields
    file = form.getvalue('file')
    stc = float(form.getvalue('starttc'))

    logging.basicConfig(level=logging.ERROR)

    if os.path.isfile(file):
        c = WebVTT()
        input = STL(file, True, stc)
        for sub in input:
            (tci, tco, txt, sn, format) = sub
            c.write(tci, tco, txt, sn, format)
