#!/bin/bash

#T="/scratch/cheidegg/Prod23Jan/"
T="/mnt/t3nfs01/data01/shome/cheidegg/o/2017-01-27_ewkskims80X_M17_MERGED"
O="/afs/cern.ch/user/c/cheidegg/www/heppy/2017-02-11_ewk80X_closureTest"
QUEUE="" #"-q all.q"
LUMI=36.5

##

python susy-interface/plotmaker.py 3l "3lA" $T $O -l $LUMI --make bkgs --plots perCateg --flags '-X blinding -X filters -X trigger --ratioYLabel "Obs./pred." --plotmode closure --numerator _matched_fakes_TT --fixRatioRange --maxRatioRange 0.5 1.5 --neg --perBin --ratioOffset 0.03 --print C,png,pdf,txt -e' --bkgs "_matched_fakes_TT;_appl_fakes_TT" --mca susy-ewkino/3l/mca_closure.txt --plot susy-ewkino/3l/plots_closure.txt --lspam 'Simulation' --noWeight --noCFlags  -o 3lttbar $QUEUE






## OLD CLOSURE TEST PLOTS

##python susy-interface/plotmaker.py 3l "3lA;3lB;3lC;3lD;3lE" $T $O -l 36.5 --make bkgs --plots perCateg --flags '-X blinding -X filters -X trigger --ratioYLabel "Obs./pred." --ratioNum _matched_fakes_TT --ratioDen _appl_fakes_TT --plotmode nostack --fixRatioRange --maxRatioRange 0.5 1.5 --neg --perBin --ratioOffset 0.03 --print C,png,pdf,txt' --bkgs "_matched_fakes_TT;_appl_fakes_TT" --mca susy-ewkino/3l/mca_closure.txt --plot susy-ewkino/3l/plots_closure.txt --lspam 'Simulation' --noWeight --noCFlags  -o 3lttbar $QUEUE
#python susy-interface/plotmaker.py 3l "3lA;3lB;3lC;3lD;3lE" $T $O -l 36.5 --make bkgs --plots lep --flags '-X blinding -X filters -X trigger --ratioYLabel "Obs./pred." --ratioNum _matched_fakes_TT --ratioDen _appl_fakes_TT --plotmode nostack --fixRatioRange --maxRatioRange 0.5 1.5 --neg --perBin --ratioOffset 0.03 --print C,png,pdf,txt' --bkgs "_matched_fakes_TT;_appl_fakes_TT" --mca susy-ewkino/3l/mca_closure.txt --plot susy-ewkino/3l/plots_closure.txt --lspam 'Simulation' --noWeight --noCFlags  -o 3lttbar $QUEUE
#python susy-interface/plotmaker.py 3l "3lA;3lB;3lC;3lD;3lE" $T $O -l 36.5 --make bkgs --plots evt --flags '-X blinding -X filters -X trigger --ratioYLabel "Obs./pred." --ratioNum _matched_fakes_TT --ratioDen _appl_fakes_TT --plotmode nostack --fixRatioRange --maxRatioRange 0.5 1.5 --neg --perBin --ratioOffset 0.03 --print C,png,pdf,txt' --bkgs "_matched_fakes_TT;_appl_fakes_TT" --mca susy-ewkino/3l/mca_closure.txt --plot susy-ewkino/3l/plots_closure.txt  --lspam 'Simulation' --noWeight --noCFlags  -o 3lttbar $QUEUE
#python susy-interface/plotmaker.py 3l "3lA;3lB;3lC;3lD;3lE" $T $O -l 36.5 --make bkgs --plots perCateg --flags '-X blinding -X filters -X trigger -R met met0 "met_pt>0" --ratioYLabel "Obs./pred." --ratioNum _matched_fakes_DY --ratioDen _appl_fakes_DY --plotmode nostack --fixRatioRange --maxRatioRange 0.5 1.5 --neg --perBin --ratioOffset 0.03 --print C,png,pdf,txt' --bkgs "_matched_fakes_DY;_appl_fakes_DY" --mca susy-ewkino/3l/mca_closure.txt --plot susy-ewkino/3l/plots_closure.txt  --lspam 'Simulation' --noWeight --noCFlags  -o 3ldy $QUEUE
#python susy-interface/plotmaker.py 3l "3lA;3lB;3lC;3lD;3lE" $T $O -l 36.5 --make bkgs --plots lep --flags '-X blinding -X filters -X trigger -R met met0 "met_pt>0" --ratioYLabel "Obs./pred." --ratioNum _matched_fakes_DY --ratioDen _appl_fakes_DY --plotmode nostack --fixRatioRange --maxRatioRange 0.5 1.5 --neg --perBin --ratioOffset 0.03 --print C,png,pdf,txt' --bkgs "_matched_fakes_DY;_appl_fakes_DY" --mca susy-ewkino/3l/mca_closure.txt --plot susy-ewkino/3l/plots_closure.txt  --lspam 'Simulation' --noWeight --noCFlags  -o 3ldy $QUEUE
#python susy-interface/plotmaker.py 3l "3lA;3lB;3lC;3lD;3lE" $T $O -l 36.5 --make bkgs --plots evt --flags '-X blinding -X filters -X trigger -R met met0 "met_pt>0" --ratioYLabel "Obs./pred." --ratioNum _matched_fakes_DY --ratioDen _appl_fakes_DY --plotmode nostack --fixRatioRange --maxRatioRange 0.5 1.5 --neg --perBin --ratioOffset 0.03 --print C,png,pdf,txt' --bkgs "_matched_fakes_DY;_appl_fakes_DY" --mca susy-ewkino/3l/mca_closure.txt --plot susy-ewkino/3l/plots_closure.txt --lspam 'Simulation' --noWeight --noCFlags  -o 3ldy $QUEUE

