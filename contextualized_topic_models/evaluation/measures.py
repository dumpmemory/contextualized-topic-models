from gensim.corpora.dictionary import Dictionary
from gensim.models.coherencemodel import CoherenceModel
from gensim.models import KeyedVectors
import gensim.downloader as api

from contextualized_topic_models.evaluation.rbo import rbo
import numpy as np
import itertools


class Measure:

    def __init__(self):
        pass

    def score(self):
        pass


class TopicDiversity(Measure):
    def __init__(self, topics):
        super().__init__()
        self.topics = topics

    def score(self, topk=25):
        """
        :param topk: topk words on which the topic diversity will be computed
        :return:
        """
        if topk > len(self.topics[0]):
            raise Exception('Words in topics are less than topk')
        else:
            unique_words = set()
            for t in self.topics:
                unique_words = unique_words.union(set(t[:topk]))
            td = len(unique_words) / (topk * len(self.topics))
            return td


class CoherenceNPMI(Measure):
    def __init__(self, topics, texts):
        super().__init__()
        self.topics = topics
        self.texts = texts

    def score(self, topk=25):
        """
        :param topics: a list of lists of the top-k words
        :param texts: (list of lists of strings) represents the corpus on which the empirical frequencies of words are
        computed
        :param topk: how many most likely words to consider in the evaluation
        :return:
        """
        if topk > len(self.topics[0]):
            raise Exception('Words in topics are less than topk')
        else:
            dictionary = Dictionary(self.texts)
            npmi = CoherenceModel(topics=self.topics, texts=self.texts, dictionary=dictionary,
                                  coherence='c_npmi', topn=topk)
            return npmi.get_coherence()


class CoherenceWordEmbeddings(Measure):
    def __init__(self, topics, texts, word2vec=None, binary=False):
        super().__init__()
        self.topics = topics
        self.texts = texts
        self.word2vec_path = word2vec
        self.binary = binary

    def score(self, topk=10, binary= False):
        """
        :param topics: a list of lists of the top-n most likely words
        :param topk: how many most likely words to consider in the evaluation
        :param word2vec_file: if word2vec_file is specified, it retrieves the word embeddings file (in word2vec format) to
         compute similarities between words, otherwise 'word2vec-google-news-300' is downloaded
        :param binary: if the word2vec file is binary
        :return: topic coherence computed on the word embeddings similarities
        """
        if topk > len(self.topics[0]):
            raise Exception('Words in topics are less than topk')
        else:
            if self.word2vec is None:
                wv = api.load('word2vec-google-news-300')
            else:
                wv = KeyedVectors.load_word2vec_format(self.word2vec_path, binary=binary)
            arrays = []
            for index, topic in enumerate(self.topics):
                if len(topic) > 0:
                    local_simi = []
                    for word1, word2 in itertools.combinations(topic[0:topk], 2):
                        if word1 in wv.vocab and word2 in wv.vocab:
                            local_simi.append(wv.similarity(word1, word2))
                    arrays.append(np.mean(local_simi))
            return np.mean(arrays)


class RBO(Measure):
    def __init__(self, topics):
        super().__init__()
        self.topics = topics

    def score(self, topk = 10, weight=0.9):
        '''
        :param weight: p (float), default 1.0: Weight of each agreement at depth d:
        p**(d-1). When set to 1.0, there is no weight, the rbo returns to average overlap.
        :param topic_list: a list of lists of words
        :return: rank_biased_overlap over the topics
        '''
        if topk > len(self.topics[0]):
            raise Exception('Words in topics are less than topk')
        else:
            collect = []
            for list1, list2 in itertools.combinations(self.topics, 2):
                rbo_val = rbo.rbo(list1[:topk], list2[:topk], p=weight)[2]
                collect.append(rbo_val)
            return np.mean(collect)
