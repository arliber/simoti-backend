#!/usr/bin/env python
# coding=utf8


def getScoredDicionary(snippets):
  snippetsDict = {}
  for i in range(0, len(snippets)):
      for j in range(0, len(snippets[i]['wordPouch'])):
          featureName = snippets[i]['wordPouch'][j]
          snippetsDict[featureName] = snippetsDict.get(featureName, [0] * len(snippets))
          snippetsDict[featureName][i] = snippets[i]['wordPouchScores'][j]

  return snippetsDict


def getScore(snippets, articleContentDict, articleTitleDict):

  # Handle the snippets
  snippetsDict = getScoredDicionary(snippets)

  # Common words between all snippets
  commonWords = [dup for dup in snippetsDict if 0 not in snippetsDict[dup]]
  print('Common words between all {} snippets:'.format(len(snippets)), commonWords)

  # Multiply dictionaries
  scoredSnippets = {}
  for i in range(0, len(snippets)):
    snippetId = snippets[i].key.id

    # Score content
    for key in articleContentDict.keys():
      keyScore = articleContentDict[key] * snippetsDict.get(key, [0] * len(snippets))[i]
      if(keyScore > 0):
        scoredSnippets[snippetId] = scoredSnippets.get(snippetId, {})
        scoredSnippets[snippetId]['contentScore'] = scoredSnippets[snippetId].get('contentScore', 0) + keyScore
        scoredSnippets[snippetId]['commonWords'] = scoredSnippets[snippetId].get('commonWords', set()) | {key}

    # Score title
    for key in articleTitleDict.keys():
      keyScore = articleTitleDict[key] * snippetsDict.get(key, [0] * len(snippets))[i]
      if(keyScore > 0):
        scoredSnippets[snippetId] = scoredSnippets.get(snippetId, {})
        scoredSnippets[snippetId]['titleScore'] = scoredSnippets[snippetId].get('titleScore', 0) + keyScore
        scoredSnippets[snippetId]['commonWords'] = scoredSnippets[snippetId].get('commonWords', set()) | {key}

  return scoredSnippets


if __name__ == '__main__':
  print(getScore('martech.zone', 'randy-stocklin-ecommerce', 'en'))
