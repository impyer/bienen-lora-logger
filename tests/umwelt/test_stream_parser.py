# SPDX-License-Identifier: GPL-3.0-or-later
import hashlib
import io
import tracemalloc
import unittest

from support import SOIL_HEADER, soil_row
from umwelt.parser import parse_csv, parse_stream, CsvHeader, Record, Issue, SourceFormatError


class StreamParserTests(unittest.TestCase):
    def parse(self, lines, **extra):
        return parse_stream(lines,'boden',expected_stand='synthetic',expected_device='synthetic-soil',**extra)

    def test_stream_is_lazy_and_handles_more_than_32_mib_with_bounded_memory(self):
        consumed=[0]
        suffix=';'+'x'*4096+'\n'
        def lines():
            yield SOIL_HEADER.rstrip()+';unknown_blob\n'
            for i in range(8500):
                consumed[0]+=1
                yield soil_row(ident=f'large-{i}').rstrip()+suffix
        # New streaming API, not the retained small-string compatibility collector.
        tracemalloc.start()
        try:
            records=self.parse(lines())
            self.assertIsInstance(next(records),CsvHeader)
            self.assertEqual(consumed[0],0)
            self.assertIsInstance(next(records),Record)
            self.assertEqual(consumed[0],1)
            self.assertEqual(sum(isinstance(x,Record) for x in records),8499)
            peak=tracemalloc.get_traced_memory()[1]
        finally:
            tracemalloc.stop()
        self.assertLess(peak,2*1024*1024)
        self.assertGreater(8500*len(suffix),32*1024*1024)

    def test_crlf_multiline_bom_and_record_hash_are_preserved(self):
        header='\ufeff'+SOIL_HEADER.rstrip()+';note\r\n'
        raw=soil_row().rstrip()+';"first\r\nsecond"\r\n'
        result=list(self.parse(io.StringIO(header+raw,newline='')))
        record=result[1]
        self.assertEqual(record.raw['note'],'first\r\nsecond')
        self.assertEqual(record.sha256,hashlib.sha256(raw.encode()).hexdigest())
        self.assertEqual(record.line,2)

    def test_suffix_line_number_and_header_are_explicit(self):
        header=SOIL_HEADER.rstrip().split(';')
        result=list(self.parse([soil_row(),soil_row(ident='next')],header=header,first_line=451))
        self.assertEqual([x.line for x in result if isinstance(x,Record)],[451,452])

    def test_oversize_record_is_refused_and_bad_numbers_are_not_guessed(self):
        with self.assertRaisesRegex(SourceFormatError,'64_kib'):
            list(self.parse([SOIL_HEADER.rstrip()+';note\n',soil_row().rstrip()+';'+('x'*65536)+'\n']))
        result=list(self.parse([SOIL_HEADER,soil_row(values='1,25;NaN;0')]))
        record=result[1]
        self.assertIsNone(record.values['temp_5cm']);self.assertIsNone(record.values['temp_20cm'])
        self.assertEqual(record.values['temp_50cm'],0)
        self.assertEqual(len(record.quality),2)

    def test_legacy_collector_and_stream_agree_on_issues(self):
        text=SOIL_HEADER+soil_row()+soil_row('invalid-time',ident='bad')+soil_row(ident='partial').rstrip()
        stream=list(self.parse(io.StringIO(text,newline='')))
        old=parse_csv(text,'boden',expected_stand='synthetic',expected_device='synthetic-soil')
        self.assertEqual([x for x in stream if isinstance(x,Record)],old.records)
        self.assertEqual([x for x in stream if isinstance(x,Issue)],old.errors)
