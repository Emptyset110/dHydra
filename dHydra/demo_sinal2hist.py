# -*- coding: utf8 -*-
import dHydra
import sinaFinance

stock = dHydra.Stock()
sina = sinaFinance.SinaFinance()

sina.l2_hist( stock.codeList )