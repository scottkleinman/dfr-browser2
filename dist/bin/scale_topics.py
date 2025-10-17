"""scale_topics.py.

Compute 2D coordinates for topics using MDS on JSD distances."""
import numpy as np
import pandas as pd
from scipy.spatial.distance import pdist, squareform
from sklearn.manifold import MDS

def read_topic_keys(path, top_n=20):
    topics = []
    vocab = set()
    with open(path, encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) < 3:
                continue
            topic_num = int(parts[0])
            words = parts[2].split()[:top_n]
            topics.append((topic_num, words))
            vocab.update(words)
    vocab = sorted(vocab)
    return topics, vocab

def topic_word_matrix(topics, vocab):
    mat = np.zeros((len(topics), len(vocab)))
    for i, (_, words) in enumerate(topics):
        for rank, word in enumerate(words):
            if word in vocab:
                # Higher rank = higher weight (simulate distribution)
                mat[i, vocab.index(word)] = 1.0 / (rank + 1)
        mat[i] /= mat[i].sum()  # Normalize
    return mat

def jensen_shannon(p, q):
    m = 0.5 * (p + q)
    def kl(a, b):
        mask = a > 0
        return np.sum(a[mask] * np.log(a[mask] / b[mask]))
    return 0.5 * kl(p, m) + 0.5 * kl(q, m)

def jsd_matrix(mat):
    n = mat.shape[0]
    dist = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            dist[i, j] = jensen_shannon(mat[i], mat[j])
    return dist

def compute_mds(dist, n_components=2):
    mds = MDS(n_components=n_components, dissimilarity='precomputed', random_state=42)
    coords = mds.fit_transform(dist)
    return coords

if __name__ == '__main__':
    # Change this to your topic-keys file path
    topic_keys_path = '../data/liu/topic-keys.txt'
    output_csv = '../data/liu/topic_coords2.csv'

    topics, vocab = read_topic_keys(topic_keys_path)
    mat = topic_word_matrix(topics, vocab)
    dist = jsd_matrix(mat)
    coords = compute_mds(dist)

    df = pd.DataFrame({
        'topic': [t[0] for t in topics],
        'x': coords[:, 0],
        'y': coords[:, 1]
    })
    df.to_csv(output_csv, index=False)
    print(f'Coordinates saved to {output_csv}')
