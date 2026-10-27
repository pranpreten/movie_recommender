from collections import Counter
from pathlib import Path
import csv
import math
import re


def tokenize(text):
    words = re.findall(r'[가-힣a-z0-9]+', text.lower())
    tokens = []
    for word in words:
        tokens.append(word)
        if len(word) > 2:
            tokens.extend(word[i:i+2] for i in range(len(word)-1))
    return tokens


class Recommender:
    def __init__(self, path):
        with Path(path).open(encoding='utf-8-sig', newline='') as file:
            reader = csv.DictReader(file)
            required = {'title', 'year', 'genres', 'keywords', 'description'}
            if not required.issubset(reader.fieldnames or []):
                raise ValueError('CSV에 title, year, genres, keywords, description 열이 필요합니다.')
            self.movies = []
            seen = set()
            for line, row in enumerate(reader, 2):
                movie = {key: (row.get(key) or '').strip() for key in required}
                if not movie['title']:
                    continue
                if not movie['year'].isdigit():
                    raise ValueError(f'{line}행의 year를 숫자로 입력하세요.')
                key = (movie['title'], movie['year'])
                if key not in seen:
                    self.movies.append(movie)
                    seen.add(key)
        if len(self.movies) < 2:
            raise ValueError('서로 다른 영화가 두 편 이상 필요합니다.')
        documents = []
        for movie in self.movies:
            text = ' '.join([movie['genres']] * 3 + [movie['keywords']] * 2 + [movie['description']])
            documents.append(Counter(tokenize(text)))
        frequency = Counter(token for doc in documents for token in doc)
        self.idf = {token: math.log((1+len(documents))/(1+count))+1 for token, count in frequency.items()}
        self.vectors = [self.vector(doc) for doc in documents]

    def vector(self, counts):
        weights = {token: (1+math.log(count))*self.idf[token] for token, count in counts.items() if token in self.idf}
        norm = math.sqrt(sum(value*value for value in weights.values()))
        return {token: value/norm for token, value in weights.items()} if norm else {}

    def recommend(self, index=None, query='', genre='전체', count=5):
        if index is not None:
            vector = self.vectors[index]
        else:
            if not query.strip():
                return []
            vector = self.vector(Counter(tokenize(query)))
        if not vector:
            return []
        results = []
        for i, movie in enumerate(self.movies):
            if i == index or (genre != '전체' and genre not in movie['genres'].split('|')):
                continue
            score = sum(weight * self.vectors[i].get(token, 0) for token, weight in vector.items())
            if score <= 0:
                continue
            overlap = sorted((token for token in vector if token in self.vectors[i]), key=lambda token: vector[token]*self.vectors[i][token], reverse=True)
            results.append({'index': i, 'movie': movie, 'score': score, 'terms': overlap[:5]})
        return sorted(results, key=lambda row: (-row['score'], row['movie']['title']))[:count]
