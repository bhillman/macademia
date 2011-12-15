import collections
import logging
import math
import pprint
import random
import sys

import utils

LOGGER = logging.getLogger(__name__)

SAMPLE_SIZE = 500
POW_SIM = 2.0
POW_DIVERSITY = 2.0
POW_POP = 1.0
DEBUG = False

def sigmoid(x):
    return 1.0 / (1.0 + math.exp(-x))

def make_interest_graph(root):
    LOGGER.debug('building graph for %s', root)

    candidates = set(root.get_similar()[20:])   # ignore the very closest items
    cluster_roots = set()
    while candidates and len(cluster_roots) < 4:
        LOGGER.debug('doing iteration %d', len(cluster_roots))
        candidates, cluster_roots = pick_subcluster_root(root, candidates, cluster_roots)

    cluster_map = { 'root' : root, 'map' : {} }
    for cr in cluster_roots:
        cluster = pick_cluster_elems(cr, cluster_roots)
        cluster_map['map'][cr] = cluster

    return cluster_map

def pick_subcluster_root(root, candidates, current_roots):
    current_top = set()
    for i in current_roots:
        current_top.update(i.get_similar()[:30])

    debug = []

    top_match = None
    top_score = -1.0
    for i in candidates:
        candidate_top = set(i.get_similar()[:30])
        n_new = len(candidate_top.difference(current_top))
        s = (
                (root.get_similarity(i) ** POW_SIM) *
                (n_new ** POW_DIVERSITY) *
                (math.log(i.count + 1) ** POW_POP) 
        )
        if LOGGER.isEnabledFor(logging.DEBUG):
            debug.append([s, root.get_similarity(i), n_new, math.log(i.count + 1), i])
        if s >= top_score:
            top_score = s
            top_match = i

    if LOGGER.isEnabledFor(logging.DEBUG):
        debug.sort()
        debug.reverse()
        for i in range(len(debug)):
            LOGGER.debug('\t%s', debug[i])

    candidates.remove(top_match)
    current_roots.add(top_match)

    return candidates, current_roots

def pick_cluster_elems(root, other_roots):
    candidates = set(root.get_similar())

    # prune out candidates closer to some other root
    for i in list(candidates):
        for other in other_roots:
            if i.get_similarity(root) < i.get_similarity(other):
                candidates.remove(i)
                break

    cluster_elems = set()
    while candidates and len(cluster_elems) < 7:
        LOGGER.debug('\tdoing iteration %d', len(cluster_elems))
        candidates, cluster_elems = pick_subcluster_root(root, candidates, cluster_elems)

    return cluster_elems


def describe_gold_standard(gold):
    triples = []
    for i1 in gold:
        for (i2, n) in gold[i1].items():
            triples.append((n, i1, i2))
    triples.sort()
    triples.reverse()
    for (n, i1, i2) in triples:
        print i1, i2, n

def grid_evaluation(gold):
    global POW_SIM, POW_DIVERSITY, POW_POP

    options = [0.25, 0.5, 1.0, 2.0, 4.0]
    for POW_SIM in options:
        for POW_DIVERSITY in options:
            for POW_POP in options:
                evaluate(gold)


def evaluate(gold):
    sys.stdout.write('sim=%.2f, diversity=%.2f, pop=%.2f '
            % (POW_SIM, POW_DIVERSITY, POW_POP))

    hits = 0
    weights = 0
    total = 0
    for i in random.sample(utils.getAllInterests(), SAMPLE_SIZE):
        g = make_interest_graph(i)
        for j in g['sub_clusters']:
            total += 1
            if gold[i][j]:
                hits += 1
                weights += math.log(1.0 + hits)

    sys.stdout.write('hits: %.3f%% weight=%.3f (%d of %d)\n'
                    % (100.0 * hits / total, weights / total, hits, total))
        

def print_interest_subclusters():
    for i in utils.getAllInterests():
        print i
        g = make_interest_graph(i)
        for j in g['map']:
            print '\t\t%s:' % j
            for k in g['map'][j]:
                print '\t\t\t%s' % k
        print

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    utils.init()
    print_interest_subclusters()
    #gold = utils.read_gold_standard('../dat/interest_navs2.txt')
    #grid_evaluation(gold)
    #describe_gold_standard(gold)
