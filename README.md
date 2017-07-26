# README

This repo consists of a single app engine service exposing the following services:

* __Article scraper__ - scrape any given article and save contents in GC Datastore
* __Snippet's keywords builder__ - compile a list of relevant N-Grams for every snippet (based on title) and save in GC Datastore
* __Tag Creator__ - compile a list of relevant words for every snippet (based on tags) and save in GC Datastore

## Authors
Logan Horowitz, Arik Liber

Simoti Co.

## Deploy app

`gcloud app deploy`

## Deploy indexes
`gcloud app deploy index.yaml`

## TO DO

- Normalize TF-IDF score
- Process body content, credit lines etc. ???

## FAQ

Q: I get 403 when trying to query the datastore

A: Run `export GOOGLE_APPLICATION_CREDENTIALS=/Users/leoliber/Repos/simoti/ad-server/keyfile.json`

# Notes

## Search engine

Tutorial: https://developers.google.com/custom-search/json-api/v1/overview

Console: Custom search: https://cse.google.com/cse/all

Key: AIzaSyAx_o3OOlY92fsPUfQaUBzUlXG8-a-Zsm0

Engine ID: 000161978559585141097:55s91q7tm4q

Example request: 
https://www.googleapis.com/customsearch/v1?key=AIzaSyAx_o3OOlY92fsPUfQaUBzUlXG8-a-Zsm0&cx=000161978559585141097:55s91q7tm4q&q=ביטקוין



