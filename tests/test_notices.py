"""tools/gen_notices.py: the list of third-party components is read from the dist-info folders that are shipped."""
import importlib.util
import os
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('gen_notices', os.path.join(os.path.dirname(HERE), 'tools', 'gen_notices.py'))
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)


def package(root, folder, meta):
    d = os.path.join(root, folder)
    os.makedirs(d)
    with open(os.path.join(d, 'METADATA'), 'w', encoding='utf-8') as f:
        f.write(meta)


class NoticesTests(unittest.TestCase):
    def test_the_licence_comes_from_the_best_field(self):
        root = tempfile.mkdtemp(prefix='ytg_notices_')
        package(root, 'alpha-1.0.dist-info', 'Name: alpha\nVersion: 1.0\nLicense-Expression: MIT\nProject-URL: Homepage, https://a.example\n\nbody')
        package(root, 'beta-2.1.dist-info', 'Name: beta\nVersion: 2.1\nLicense: ' + 'long licence text ' * 10 +
                '\nClassifier: License :: OSI Approved :: Apache Software License\nHome-page: https://b.example\n\nbody')
        os.makedirs(os.path.join(root, 'not_a_package'))
        rows = gen.read_packages(root)
        self.assertEqual(rows, [('alpha', '1.0', 'MIT', 'https://a.example'),
                                ('beta', '2.1', 'Apache Software License', 'https://b.example')])

    def test_the_page_lists_everything_and_the_warning(self):
        text = gen.render([('alpha', '1.0', 'MIT', 'https://a.example')])
        self.assertIn('| alpha | 1.0 | MIT | <https://a.example> |', text)
        self.assertIn('FFmpeg', text)
        self.assertIn('GPL', text)
        self.assertTrue(text.endswith('\n') and not text.endswith('\n\n'))


if __name__ == '__main__':
    unittest.main()
