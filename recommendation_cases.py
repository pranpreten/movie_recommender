from pathlib import Path
import tempfile
import unittest
from similarity import Recommender


class MovieTests(unittest.TestCase):
    def setUp(self):
        self.model = Recommender(Path(__file__).with_name('catalog.csv'))

    def test_space_query(self):
        results = self.model.recommend(query='우주 화성 탐사 생존', count=3)
        self.assertIn('마션', [row['movie']['title'] for row in results])
        self.assertTrue(all(0 < row['score'] <= 1.000001 for row in results))

    def test_same_movie_excluded(self):
        results = self.model.recommend(index=0, count=50)
        self.assertNotIn(0, [row['index'] for row in results])
        self.assertEqual([row['score'] for row in results], sorted([row['score'] for row in results], reverse=True))

    def test_genre_filter(self):
        results = self.model.recommend(query='우주 가족 사랑', genre='애니메이션')
        self.assertTrue(results)
        self.assertTrue(all('애니메이션' in row['movie']['genres'] for row in results))

    def test_unknown_query(self):
        self.assertEqual(self.model.recommend(query='xyzq9876'), [])

    def test_bad_schema(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'bad.csv'
            path.write_text('name,year\nTest,2020\n', encoding='utf-8')
            with self.assertRaises(ValueError):
                Recommender(path)


if __name__ == '__main__':
    unittest.main()
