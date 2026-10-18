"""Frozen lexical anchors and matrix-based alignment for experiment 2."""
from collections import Counter
from .alignment import features,similarity_features
from .lexicon import predict


def lexical_agreement(predictions, source_words):
    emitted=Counter(p['prediction'] for p in predictions if p['prediction'] is not None)
    return sum((emitted & Counter(source_words)).values()) / sum(emitted.values()) if emitted else .5


def score_matrices(fl, source, baseline, lexical, lexicon, rules):
    af,bf=list(map(features,fl)),list(map(features,source))
    predictions=[predict(s,lexicon,rules) for s in fl]
    structural=[[similarity_features(a,b,baseline['weights']) for b in bf] for a in af]
    anchors=[[lexical_agreement(p,[t.normalized for t in s.tokens]) for s in source] for p in predictions]
    blended=[[lexical['structural_weight']*s+lexical['lexical_weight']*a for s,a in zip(sr,ar)] for sr,ar in zip(structural,anchors)]
    return {'structural':structural,'lexical':blended},predictions


def align_matrix(matrix,config):
    n=len(matrix);m=len(matrix[0]) if n else 0
    trace=[[0]*(m+1) for _ in range(n+1)]; scores=[[0.]*(m+1) for _ in range(n+1)]
    best=(0.,0,0)
    floor,gap=config['match_floor'],config['gap_penalty']
    for i in range(1,n+1):
        row,prev=scores[i],scores[i-1]
        for j in range(1,m+1):
            sim=matrix[i-1][j-1]
            choices=(0.,prev[j-1]+sim-floor if sim>floor else -1.,prev[j]-gap,row[j-1]-gap)
            move=max(range(4),key=choices.__getitem__)
            row[j]=choices[move];trace[i][j]=move
            if row[j]>best[0]:best=(row[j],i,j)
    value,i,j=best;links=[];gaps=[]
    while i and j and scores[i][j]>0:
        move=trace[i][j]
        if move==1:
            links.append({'fl_index':i-1,'source_index':j-1,'similarity':matrix[i-1][j-1]});i-=1;j-=1
        elif move==2:gaps.append({'side':'fl','index':i-1});i-=1
        elif move==3:gaps.append({'side':'source','index':j-1});j-=1
        else:break
    return {'strength':value/max(n,1),'links':list(reversed(links)),'gaps':list(reversed(gaps)),
            'minimum_links_met':len(links)>=config['minimum_links']}


def without_work(candidates,work,groups):
    return {key:value for key,value in candidates.items() if groups[key]!=work}


def edge_metrics(predicted,reference):
    proposed={(l['fl_index'],l['source_index']) for l in predicted}
    expected={(l['fl_index'],l['source_index']) for l in reference}
    correct=len(proposed & expected)
    return {'correct_edges':correct,'proposed_edges':len(proposed),'reference_edges':len(expected),
            'precision':correct/len(proposed) if proposed else 0.,'recall':correct/len(expected) if expected else 0.}
