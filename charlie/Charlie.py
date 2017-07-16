#!/usr/bin/env python
# coding=utf8

import snippetsScore

'''
  Run snippet scrore
  Run tags based score
  Apply predefined weights
  If score above predefined treshold - call compiler with article and selected snippet id
  
  IMPORTANT: Log, a lot 
'''

if __name__ == '__main__':
  print(snippetsScore.getScore('martech.zone', 'ecommerce-shipping-options'))