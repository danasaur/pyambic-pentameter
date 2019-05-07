#!/usr/bin/env python3

## SONNETS
# rhyme scheme: abab cdcd efef gg

from functools import wraps
import json
import random

from nltk.corpus import cmudict

from syllables import rhyme_fingerprint, potential_iambic_seed, remaining_scheme, scansion_matches, valid_option, fulfills_scansion

rd = cmudict.dict()


def get_lyrics():
    with open('../data/beatles_lyrics.json', 'r') as f:
        lyrics = json.loads(f.read())
    return lyrics


def build_lyrics_corpus():
    d = {}
    data = get_lyrics()
    word_set = set()

    # we are gonna build a backwards markov, so we can start with a rhyme and
    # fill in the lines from there
    for song, song_data in data.items():
        lyrics = []
        for line in song_data['lyrics']:
            lyrics.extend(line.split())
        
        lyrics = [word.strip('.,()-').lower() for word in lyrics if word.strip('.,()-')]
        word_set.update(lyrics)
        lyrics.reverse()

        for i, word in enumerate(lyrics[:-1]):
            if not word in d:
                d[word] = []
            d[word].append(lyrics[i+1])

    # we can seed off of words that are valid in iambic pentameter - that is, they
    # can end with a stressed syllable - and have at least one matching rhyme
    seeds = {}
    for word in word_set:
        if not potential_iambic_seed(word):
            continue
        rf = rhyme_fingerprint(word)
        if rf is None:
            continue
        if not rf in seeds:
            seeds[rf] = []
        seeds[rf].append(word)

    valid_seeds = {key:value for key, value in seeds.items() if len(value) >= 2}

    return d, valid_seeds


def generate_line(word, d):
    line = [word]
    syl_map = remaining_scheme(word, '01' * 5)
    # we're looking for 10 syllables
    # TODO - iambic syllables !!!!!!
    # may involve backtrack
    while syl_map:
        options = [word for word in d[word] if valid_option(word, syl_map)]
        random.shuffle(options)
        if not options:
            print('oops')
            break
        word = random.choice(options)
        line.append(word)
        syl_map = remaining_scheme(word, syl_map)
    print(' '.join(line[::-1]))
    return ' '.join(line[::-1])


def memoize(f):
    cache = {}

    @wraps(f)
    def retrieve_or_store(a, b, *args, **kwargs):
        if not (a, b) in cache:
            cache[(a, b)] = f(a, b, *args, **kwargs)
        return cache[(a, b)]

    return retrieve_or_store


@memoize
def find_all(word, scansion_pattern, d):
    if fulfills_scansion(word, scansion_pattern):
        # success!
        return [[word]]
    if not valid_option(word, scansion_pattern):
        return None

    options = set([w for w in d[word] if valid_option(w, scansion_pattern)])
    if not options:
        # failure!
        return None

    completes = []
    # otherwise, we need to keep looking
    for option in options:
        need_to_find = remaining_scheme(option, scansion_pattern)
        all_working = find_all(option, need_to_find, d)
        if all_working is not None:
            completes.extend([[word] + c for c in all_working])
    return completes


@memoize
def find_with_backtrack(word, scansion_pattern, d):
    if fulfills_scansion(word, scansion_pattern):
        # success!
        return [[word]]
    if not valid_option(word, scansion_pattern):
        return None

    options = set([w for w in d[word] if valid_option(w, scansion_pattern)])
    if not options:
        # failure!
        return None

    completes = []
    # otherwise, we need to keep looking
    for option in options:
        need_to_find = remaining_scheme(option, scansion_pattern)
        all_working = find_with_backtrack(option, need_to_find, d)
        if all_working is not None:
            completes.extend([[word] + c for c in all_working])
    return completes


def generate_sonnet(d, seeds):
    # start by picking 7 pairs of rhyming words
    # then generate backwards for the right number of syllables

    rhyme_sounds = random.sample(list(seeds.keys()), 7)

    sonnet = []

    for rhyme in rhyme_sounds:
        chosen = random.sample(seeds[rhyme], 2)
        for seed in chosen:
            sonnet.append(generate_line(seed, d))
    
    # now shuffle the lines so the rhyme scheme is right
    sonnet[1], sonnet[2] = sonnet[2], sonnet[1]
    sonnet[5], sonnet[6] = sonnet[6], sonnet[5]
    sonnet[9], sonnet[10] = sonnet[10], sonnet[9]

    return sonnet


def main():
    d, seeds = build_lyrics_corpus()
    sonnet = generate_sonnet(d, seeds)
    print('\n'.join(sonnet))


if __name__ == '__main__':
    main()
