from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from skill_support import parse_frontmatter, read_skill_text, skill_target


class SkillSupportTests(unittest.TestCase):
    def test_yaml_block_description(self):
        meta = parse_frontmatter('---\nname: csv-profile\ndescription: >\n  Profile a CSV.\n  Use for data checks.\n---\n# Skill')
        self.assertEqual(meta["description"], "Profile a CSV. Use for data checks.")

    def test_invalid_names_and_metadata(self):
        for name in ("../escape", "/tmp/escape", "BadName", "bad_name", "bad--name", "-bad", "a" * 65):
            with self.subTest(name=name), self.assertRaises(ValueError):
                parse_frontmatter(f'---\nname: "{name}"\ndescription: Test\n---\n')
        for text in ("no frontmatter", "---\n[]\n---\n", "---\nname: good\ndescription: []\n---\n"):
            with self.subTest(text=text), self.assertRaises(ValueError):
                parse_frontmatter(text)

    def test_symlink_escape_and_folder_mismatch(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / "skills"
            root.mkdir()
            outside = Path(folder) / "outside"
            outside.mkdir()
            (root / "escape").symlink_to(outside, target_is_directory=True)
            with self.assertRaises(ValueError):
                skill_target(root, "escape")
            target = skill_target(root, "right")
            target.parent.mkdir()
            target.write_text('---\nname: wrong\ndescription: Test\n---\n')
            with self.assertRaises(ValueError):
                read_skill_text(target, root)


if __name__ == "__main__":
    unittest.main()
