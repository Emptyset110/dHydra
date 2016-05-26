# -*- coding: utf-8 -*-
import click
import dHydra.core.util as util
import time
import os
import sys

@click.command()
@click.argument('profit', nargs = 1)
@click.argument('amount', nargs = 1)
@click.argument('threshold', nargs = 1)
@click.argument('variety', nargs = 1)
def buy(profit = None, amount = None, threashold = None, variety = None):
    print(type(profit), amount, threshold, variety)

@click.command()
def discount():
    while True:
        discount_tier = util.read_config( os.getcwd()+"/data/discount_tier.json" )
        print( "利润率\t品种\t卖1贡献总金额" )
        print( "> 0.0%\t{}".format( discount_tier["> 0.0%"] ) )
        print( "> 0.1%\t{}".format( discount_tier["> 0.1%"] ) )
        print( "> 0.2%\t{}".format( discount_tier["> 0.2%"] ) )
        print( "> 0.3%\t{}".format( discount_tier["> 0.3%"] ) )
        print( "> 0.4%\t{}".format( discount_tier["> 0.4%"] ) )
        print( "> 0.5%\t{}".format( discount_tier["> 0.5%"] ) )
        print( "> 0.6%\t{}".format( discount_tier["> 0.6%"] ) )
        time.sleep(3)
