import gzip
import io
import tarfile
import unittest
from fl_decipher.source_version_v40 import date_witnesses, inventory


def bundle(name, content=b'\\documentclass{revtex4}\n\\date{\\today}\n', link=False):
    stream = io.BytesIO()
    with tarfile.open(fileobj=stream, mode='w') as archive:
        member = tarfile.TarInfo(name)
        member.size = len(content)
        if link:
            member.type = tarfile.SYMTYPE
            member.linkname = '/tmp/outside'
            archive.addfile(member)
        else:
            archive.addfile(member, io.BytesIO(content))
    return gzip.compress(stream.getvalue())


class SourceVersionTests(unittest.TestCase):
    def test_archive_and_single_gzip_tex(self):
        status, files = inventory(bundle('main.tex'))
        self.assertTrue(status['available'])
        self.assertIn('main.tex', files)
        status, files = inventory(gzip.compress(b'\\documentclass{article}'))
        self.assertEqual(status['format'], 'gzip-single-tex')
        self.assertIn('single_source.tex', files)

    def test_traversal_links_and_html_are_unavailable(self):
        for raw in [bundle('../main.tex'), bundle('/main.tex'), bundle('main.tex', link=True), b'<html>error</html>']:
            status, files = inventory(raw)
            self.assertFalse(status['available'])
            self.assertEqual(files, {})

    def test_expansion_bound(self):
        from unittest.mock import patch
        with patch('fl_decipher.source_version_v40.EXPANDED_LIMIT', 16):
            self.assertFalse(inventory(gzip.compress(b'x' * 17))[0]['available'])

    def test_comments_and_exact_witness_offsets(self):
        text = '% \\date{\\today}\n\\date{25 Sep 2018} % \\today\n\\% visible \\today\n'
        rows = date_witnesses(text)
        self.assertEqual([r['command'] for r in rows], ['\\date', '\\today'])
        for row in rows:
            self.assertEqual(text[slice(*row['span'])], row['command'])
            self.assertEqual(text[slice(*row['line_span'])], row['line_text'])


if __name__ == '__main__':
    unittest.main()
