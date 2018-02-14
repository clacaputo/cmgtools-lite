'''
Script for doing the full unfolding analysis.

Created by Pietro Vischia -- pietro.vischia@cern.ch
'''
import os
import copy

import argparse
import utils
import ROOT
from array import array

#from abc import ABCMeta, abstractmethod
# 
#class AbstractTSpline(object):
#    __metaclass__ = ABCMeta
#     
#    @abstractmethod
#    def run(self):
#        pass

class ResponseComputation:

    def __init__(self, inputFiles):
        print('Initialization')
        print('Input for matrix creation: %s' % inputFiles)
        self.inputFiles=inputFiles
        
        
        


        
class AcceptanceComputer:

    def __init__(self, inputFiles):
        print('Initialization')
        print('Input files are: %s' % inputFiles)

### End class AcceptanceCounter

class Unfolder(object):

    def __init__(self, args, var):
        print('Initialization')
        self.var=var
        self.unfold=None
        self.response_nom=None
        self.response_alt=None
        self.response_inc=None
        self.data=None
        self.dataTruth_nom=None
        self.dataTruth_alt=None
        self.dataTruth_inc=None
        self.mc=None
        self.bkg=None
        self.verbose=args.verbose
        self.combineInput=args.combineInput
        self.nScan=20
        # Automatic L-curve scan: start with taumin=taumax=0.0
        self.tauMin=0.0
        self.tauMax=0.0
        self.iBest=None # Best value
        self.logTauX=ROOT.TSpline3() # TSpline*
        self.logTauY=ROOT.TSpline3() # TSpline*
        self.lCurve=ROOT.TGraph(0) # TGraph*
        self.gHistInvEMatrix=ROOT.TH2D() # store the inverse of error matrix
        self.gHistInvJEMatrix=None
        self.inputDir=args.inputDir
        self.outputDir=args.outputDir
        self.responseAsPdf=args.responseAsPdf
        self.histmap=ROOT.TUnfold.kHistMapOutputVert
        self.regmode=ROOT.TUnfold.kRegModeNone
        self.constraint=ROOT.TUnfold.kEConstraintNone
        self.densitymode=ROOT.TUnfoldDensity.kDensityModeeNone
        self.load_data(args.data, args.mc, args.gen)

        # Make sure histogram errors are ON
        ROOT.TH1.SetDefaultSumw2()


    def load_data(self, dataFName, mcFName, genFName, treeName=['tree']):
        folder=self.inputDir
        dataFile=None
        mcFile=None
        #genFile=None # Taken from a separate file  
        print('Opening file %s.' % utils.get_file_from_glob(os.path.join(folder, 'incl_fitWZonly_%s/%s' % (self.var, self.combineInput) ) if folder else self.combineInput) )
        file_handle = ROOT.TFile.Open(utils.get_file_from_glob(os.path.join(folder,  'incl_fitWZonly_%s/%s' % (self.var, self.combineInput)) if folder else self.combineInput))
        # gdata=file_handle.Get('x_data')
        # gdata.Draw('AP')
        # hdata=self.get_graph_as_hist(gdata, ('recodata','recodata',4,0,4))
        # data   = copy.deepcopy(ROOT.TH1F(hdata))
        data   = copy.deepcopy(file_handle.Get('x_data'))
        signal = copy.deepcopy(file_handle.Get('x_prompt_WZ'))
        bkg    = copy.deepcopy(self.get_total_bkg_as_hist(file_handle, 'list'))   
        # bkg    = copy.deepcopy(self.get_total_bkg_as_hist(file_handle, 'sum'))
        # Subtraction is done by the TUnfoldDensityClass
        # Scheme 1: subtraction
        # print('Before subtraction. Data: %f, Bkg: %f, Signal: %f' % (data.Integral(), bkg.Integral(), signal.Integral()))  
        #data.Add(bkg, -1)
        self.data=data
        self.mc=signal
        self.bkg=bkg

        print('bins of input data: %d' % self.data.GetNbinsX() ) 
        print('bins of input signal: %d' % self.mc.GetNbinsX() ) 
        #print('bins of input bkg: %d' % self.bkg.GetNbinsX()   ) 
        print('bins of input bkg: %d' % self.bkg[0].GetNbinsX()   ) 

        
        # print('Subtraction completed. Data-bkg: %f, Signal: %f' % (self.data.Integral(), self.mc.Integral() ))
        # print('Expected mu=(data-bkg)/NLO: %f' % (self.data.Integral()/self.mc.Integral()) )
            
        #genFile  = utils.get_file_from_glob(os.path.join(folder, genFName)  if folder else genFName)

        # Add reading gen file to build response matrix
        self.get_responses()
        #self.rebin_all(4)
        # Pass through numpy arrays?
        print('Data correctly loaded.')
        #return data, mc, response
        
    def rebin_all(self,n):
        self.data.Rebin(n/2)
        self.mc.Rebin(n/2)
        for i in range(1,len(self.bkg)):
            self.bkg[i].Rebin(n/2)
        self.response_nom.RebinX(n/2)
        self.response_alt.RebinX(n/2)
        self.response_inc.RebinX(n/2)
        self.response_nom.RebinY(n/2)
        self.response_alt.RebinY(n/2)
        self.response_inc.RebinY(n/2)
        self.dataTruth_nom.RebinY(n/2)
        self.dataTruth_alt.RebinY(n/2)
        self.dataTruth_inc.RebinY(n/2)

    def study_responses(self):
        self.compute_stability_and_purity()

        for matrix in [self.response_nom, self.response_alt, self.response_inc]:
            profX=matrix.ProfileX('%s_profX'%matrix.GetName(), 0, matrix.GetNbinsY(),'s')
            profY=matrix.ProfileY('%s_profY'%matrix.GetName(), 0, matrix.GetNbinsX(),'s')
            print(profX)
            print(profY)
            c = ROOT.TCanvas('matrix', 'Response Matrix', 2000, 1000)
            # Margin not being applied somehow. Must do it via gStyle?
            ROOT.gStyle.SetPadTopMargin(0.1)
            ROOT.gStyle.SetPadBottomMargin(0.1)
            ROOT.gStyle.SetPadLeftMargin(0.1)
            ROOT.gStyle.SetPadRightMargin(0.1)
            ROOT.gStyle.SetOptStat('uo')
            c.Divide(2,1)
            c.cd(1)
            ROOT.gPad.SetGrid()
            profX.SetMarkerStyle(ROOT.kFullSquare)
            profX.SetTitle('Response (gen profiled)')
            profX.Draw("PE")
            c.cd(2)
            ROOT.gPad.SetGrid()
            profY.SetMarkerStyle(ROOT.kFullSquare)
            profY.SetTitle('Response (reco profiled)')
            profY.Draw("PE")
            utils.saveCanva(c, os.path.join(self.outputDir, '1_responseProfiled_%s_%s' % (matrix.GetName(), self.var)))            
            
    def get_responses(self):
        print('Acquiring response matrices.')
        folder=os.path.join(self.inputDir, 'response/%s_response_WZ_' % self.var)
        file_handle_nom = ROOT.TFile.Open('%s%s.root' % (folder, 'Pow'))
        file_handle_alt = ROOT.TFile.Open('%s%s.root' % (folder, 'aMC'))
        file_handle_inc = ROOT.TFile.Open('%s%s.root' % (folder, 'Inc'))

        self.response_nom = copy.deepcopy(ROOT.TH2D(file_handle_nom.Get('%s_response_canvas' % self.var).GetPrimitive('%s_response_WZ_%s' %(self.var, 'Pow'))))
        self.response_alt = copy.deepcopy(ROOT.TH2D(file_handle_alt.Get('%s_response_canvas' % self.var).GetPrimitive('%s_response_WZ_%s' %(self.var, 'aMC'))))
        self.response_inc = copy.deepcopy(ROOT.TH2D(file_handle_inc.Get('%s_response_canvas' % self.var).GetPrimitive('%s_response_WZ_%s' %(self.var, 'Inc'))))

        self.dataTruth_nom = copy.deepcopy(ROOT.TH1D(self.response_nom.ProjectionY('dataTruth_nom', 0, self.response_nom.GetNbinsX())))
        self.dataTruth_alt = copy.deepcopy(ROOT.TH1D(self.response_alt.ProjectionY('dataTruth_alt', 0, self.response_alt.GetNbinsX())))
        self.dataTruth_inc = copy.deepcopy(ROOT.TH1D(self.response_inc.ProjectionY('dataTruth_inc', 0, self.response_inc.GetNbinsX())))

        for ibin in range(0, self.response_nom.GetNbinsX()+2):
            for jbin in range(0, self.response_nom.GetNbinsY()+2):
                if ibin==0 or jbin==0 or ibin>self.response_nom.GetNbinsX() or jbin>self.response_nom.GetNbinsY():
                    self.response_nom.SetBinContent(ibin, jbin, 0)
                    self.response_alt.SetBinContent(ibin, jbin, 0)
                    self.response_inc.SetBinContent(ibin, jbin, 0)
                    self.response_nom.SetBinError(ibin, jbin, 0)
                    self.response_alt.SetBinError(ibin, jbin, 0)
                    self.response_inc.SetBinError(ibin, jbin, 0)
                    



    def print_responses(self):
        c = ROOT.TCanvas('matrix', 'Response Matrix', 2000, 2000)
        c.cd()
        # Margin not being applied somehow. Must do it via gStyle?
        ROOT.gStyle.SetPadTopMargin(0.1)
        ROOT.gStyle.SetPadBottomMargin(0.1)
        ROOT.gStyle.SetPadLeftMargin(0.1)
        ROOT.gStyle.SetPadRightMargin(0.1)
        ROOT.gStyle.SetOptStat('uo')
        if self.responseAsPdf:
            resp_nom=copy.deepcopy(ROOT.TH2D(self.response_nom))
            resp_alt=copy.deepcopy(ROOT.TH2D(self.response_alt))
            resp_inc=copy.deepcopy(ROOT.TH2D(self.response_inc))

            resp_nom.Scale(1./resp_nom.Integral())
            resp_alt.Scale(1./resp_alt.Integral())
            resp_inc.Scale(1./resp_inc.Integral())

            # Compute stability
            diagonalSum_nom=0
            diagonalSum_alt=0
            diagonalSum_inc=0
            odbN_nom=0
            odbN_alt=0
            odbN_inc=0
            for ibin in range(0, resp_nom.GetNbinsX()+2):
                # Am I taking the overflow diagonal one as well? Must check
                diagonalSum_nom+= resp_nom.GetBinContent(ibin, ibin)
                diagonalSum_alt+= resp_alt.GetBinContent(ibin, ibin)
                diagonalSum_inc+= resp_inc.GetBinContent(ibin, ibin)
                
                for jbin in range(0, resp_nom.GetNbinsY()+2):
                    if ibin != jbin:
                        if resp_nom.GetBinContent(ibin, jbin) != 0: odbN_nom+=1
                        if resp_alt.GetBinContent(ibin, jbin) != 0: odbN_alt+=1
                        if resp_inc.GetBinContent(ibin, jbin) != 0: odbN_inc+=1

            oodFraction_nom=(1-diagonalSum_nom) 
            oodFraction_alt=(1-diagonalSum_alt)
            oodFraction_inc=(1-diagonalSum_inc)
            odbFraction_nom = odbN_nom/(resp_nom.GetNbinsX()*resp_nom.GetNbinsY())
            odbFraction_alt = odbN_alt/(resp_alt.GetNbinsX()*resp_alt.GetNbinsY())
            odbFraction_inc = odbN_inc/(resp_inc.GetNbinsX()*resp_inc.GetNbinsY())
            print('Overall fraction of out-of-diagonal events | Fraction of out-of-diagonal filled bins:')
            print('\t nom: %0.3f | %0.3f = %d/%d' % (oodFraction_nom, odbFraction_nom, odbN_nom, (resp_nom.GetNbinsX()*resp_nom.GetNbinsY())))
            print('\t alt: %0.3f | %0.3f = %d/%d' % (oodFraction_alt, odbFraction_alt, odbN_alt, (resp_alt.GetNbinsX()*resp_alt.GetNbinsY())))
            print('\t inc: %0.3f | %0.3f = %d/%d' % (oodFraction_inc, odbFraction_inc, odbN_inc, (resp_inc.GetNbinsX()*resp_inc.GetNbinsY())))
            resp_nom.Draw('COLZ')
            utils.saveCanva(c, os.path.join(self.outputDir, '1_responseMatrixAsPdf_%s_Nom' % self.var))
            c.Clear()
            resp_alt.Draw('COLZ')
            utils.saveCanva(c, os.path.join(self.outputDir, '1_responseMatrixAsPdf_%s_Alt' % self.var))
            c.Clear()
            resp_inc.Draw('COLZ')
            utils.saveCanva(c, os.path.join(self.outputDir, '1_responseMatrixAsPdf_%s_Inc' % self.var))

        self.response_nom.Draw('COLZ')
        utils.saveCanva(c, os.path.join(self.outputDir, '1_responseMatrix_%s_Nom' % self.var))
        c.Clear()
        self.response_alt.Draw('COLZ')
        utils.saveCanva(c, os.path.join(self.outputDir, '1_responseMatrix_%s_Alt' % self.var))
        c.Clear()
        self.response_inc.Draw('COLZ')
        utils.saveCanva(c, os.path.join(self.outputDir, '1_responseMatrix_%s_Inc' % self.var))

    def compute_stability_and_purity(self):

        purity_nom=self.response_nom.ProjectionX('%s_purity'%self.response_nom.GetName(), 0, self.response_nom.GetNbinsY())
        purity_alt=self.response_alt.ProjectionX('%s_purity'%self.response_alt.GetName(), 0, self.response_alt.GetNbinsY())
        purity_inc=self.response_inc.ProjectionX('%s_purity'%self.response_inc.GetName(), 0, self.response_inc.GetNbinsY())
        stability_nom=self.response_nom.ProjectionY('%s_stability'%self.response_nom.GetName(), 0, self.response_nom.GetNbinsX())
        stability_alt=self.response_alt.ProjectionY('%s_stability'%self.response_alt.GetName(), 0, self.response_alt.GetNbinsX())
        stability_inc=self.response_inc.ProjectionY('%s_stability'%self.response_inc.GetName(), 0, self.response_inc.GetNbinsX())
        
        purity_nom.Reset("ICE")
        purity_alt.Reset("ICE")
        purity_inc.Reset("ICE")
        stability_nom.Reset("ICE")
        stability_alt.Reset("ICE")
        stability_inc.Reset("ICE")

        puritydenom_nom=copy.deepcopy(ROOT.TH1D(purity_nom))
        puritydenom_alt=copy.deepcopy(ROOT.TH1D(purity_alt))
        puritydenom_inc=copy.deepcopy(ROOT.TH1D(purity_inc))
        stabilitydenom_nom=copy.deepcopy(ROOT.TH1D(stability_nom))
        stabilitydenom_alt=copy.deepcopy(ROOT.TH1D(stability_alt))
        stabilitydenom_inc=copy.deepcopy(ROOT.TH1D(stability_inc))

        # Fill purity
        for xbin in range(0, self.response_nom.GetNbinsX()+2):
            recobinevts_nom=0
            recobinevts_alt=0
            recobinevts_inc=0
            for ybin in range(0, self.response_nom.GetNbinsY()+2):
                recobinevts_nom += self.response_nom.GetBinContent(xbin, ybin)
                recobinevts_alt += self.response_alt.GetBinContent(xbin, ybin)
                recobinevts_inc += self.response_inc.GetBinContent(xbin, ybin)


            purity_nom.SetBinContent(xbin, self.response_nom.GetBinContent(xbin,xbin))
            purity_alt.SetBinContent(xbin, self.response_alt.GetBinContent(xbin,xbin))
            purity_inc.SetBinContent(xbin, self.response_inc.GetBinContent(xbin,xbin))
            puritydenom_nom.SetBinContent(xbin, recobinevts_nom)
            puritydenom_alt.SetBinContent(xbin, recobinevts_alt)
            puritydenom_inc.SetBinContent(xbin, recobinevts_inc)

        # Fill stability
        for ybin in range(0, self.response_nom.GetNbinsY()+2):
            recobinevts_nom=0
            recobinevts_alt=0
            recobinevts_inc=0
            for xbin in range(0, self.response_nom.GetNbinsX()+2):
                recobinevts_nom += self.response_nom.GetBinContent(xbin, ybin)
                recobinevts_alt += self.response_alt.GetBinContent(xbin, ybin)
                recobinevts_inc += self.response_inc.GetBinContent(xbin, ybin)

                    
            stability_nom.SetBinContent(ybin, self.response_nom.GetBinContent(ybin,ybin))
            stability_alt.SetBinContent(ybin, self.response_alt.GetBinContent(ybin,ybin))
            stability_inc.SetBinContent(ybin, self.response_inc.GetBinContent(ybin,ybin))
            stabilitydenom_nom.SetBinContent(ybin, recobinevts_nom)
            stabilitydenom_alt.SetBinContent(ybin, recobinevts_alt)
            stabilitydenom_inc.SetBinContent(ybin, recobinevts_inc)


        purity_nom.Divide(puritydenom_nom)
        purity_alt.Divide(puritydenom_alt)
        purity_inc.Divide(puritydenom_inc)
        stability_nom.Divide(stabilitydenom_nom)
        stability_alt.Divide(stabilitydenom_alt)
        stability_inc.Divide(stabilitydenom_inc)

        # Paint them
        c = ROOT.TCanvas('matrix', 'Response Matrix', 3000, 1000)
        # Margin not being applied somehow. Must do it via gStyle?
        ROOT.gStyle.SetPadTopMargin(0.1)
        ROOT.gStyle.SetPadBottomMargin(0.1)
        ROOT.gStyle.SetPadLeftMargin(0.1)
        ROOT.gStyle.SetPadRightMargin(0.1)
        ROOT.gStyle.SetOptStat('uo')
        c.Divide(3,1)
        c.cd(1)
        purity_nom.SetMarkerColor(ROOT.kRed)
        purity_nom.SetMarkerStyle(ROOT.kFullSquare)
        stability_nom.SetMarkerColor(ROOT.kBlue)
        stability_nom.SetMarkerStyle(ROOT.kFullCircle)
        purity_nom.Draw("PE")
        stability_nom.Draw("PESAME")
        leg_1 = ROOT.TLegend(0.5,0.5,0.9,0.9)
        leg_1.SetTextSize(0.06)
        leg_1.AddEntry(purity_nom, 'Purity', 'p')
        leg_1.AddEntry(stability_nom, 'Stability', 'p')
        leg_1.Draw()
        c.cd(2)
        purity_alt.SetMarkerColor(ROOT.kRed)
        purity_alt.SetMarkerStyle(ROOT.kFullSquare)
        stability_alt.SetMarkerColor(ROOT.kBlue)
        stability_alt.SetMarkerStyle(ROOT.kFullCircle)
        purity_alt.Draw("PE")
        stability_alt.Draw("PESAME")
        leg_1.Draw()
        c.cd(3)
        purity_inc.SetMarkerColor(ROOT.kRed)
        purity_inc.SetMarkerStyle(ROOT.kFullSquare)
        stability_inc.SetMarkerColor(ROOT.kBlue)
        stability_inc.SetMarkerStyle(ROOT.kFullCircle)
        purity_inc.Draw("PE")
        stability_inc.Draw("PESAME")
        leg_1.Draw()
        utils.saveCanva(c, os.path.join(self.outputDir, '1_checkBinning_%s' % self.var))

    def get_total_bkg_as_hist(self, file_handle, action):
        totbkg = []
        totbkg.append(copy.deepcopy(file_handle.Get('x_prompt_ZZH')))
        totbkg.append(copy.deepcopy(file_handle.Get('x_fakes_appldata')))
        totbkg.append(copy.deepcopy(file_handle.Get('x_convs')))
        totbkg.append(copy.deepcopy(file_handle.Get('x_rares_ttX')))
        totbkg.append(copy.deepcopy(file_handle.Get('x_rares_VVV')))
        totbkg.append(copy.deepcopy(file_handle.Get('x_rares_tZq')))
        if 'sum' in action:
            for i in range(1,len(totbkg)):
                totbkg[0].Add(totbkg[i])
            return totbkg[0]
        return totbkg

    def get_graph_as_hist(self, g, args):
        h = ROOT.TH1F(args[0], args[1], args[2], args[3], args[4])

        for ibin in range(0,args[2]):
            x=0
            y=0
            g.GetPoint(ibin, ROOT.Double(x), ROOT.Double(y))
            h.Fill(x,y)
        print('h bins: %d; g bin: %d' %(h.GetNbinsX(), g.GetN()))
        #g.Draw('PAE')
        #print('h bins: %d; g bin: %d' %(h.GetNbinsX(), g.GetN()))
        #h=copy.deepcopy(ROOT.TH1F(g.GetHistogram()))
        print('h bins: %d; g bin: %d' %(h.GetNbinsX(), g.GetN()))
        return h

    def print_histo(self,h,key,label,opt=''):
        c = ROOT.TCanvas(h.GetName(), h.GetTitle(), 2000, 2000)
        c.cd()
        h.Draw(opt)
        utils.saveCanva(c, os.path.join(args.outputDir, '2_unfoldResults_%s_%s_%s_%s' % (label, key, self.var, h.GetName()) ))

    def do_unfolding(self, key):

        self.histmap=ROOT.TUnfold.kHistMapOutputVert
        # kHistMapOutputHoriz (truth is in X axis), kHistMapOutputVert (truth is in Y axis)
        self.regmode=ROOT.TUnfold.kRegModeNone
        # kRegModeNone (no reg), kRegModeSize (reg amplitude of output), kRegModeDerivative (reg 1st derivative of output), kRegModeCurvature (reg 2nd derivative of output),  kRegModeMixed (mixed reg patterns)
        self.constraint=ROOT.TUnfold.kEConstraintArea
        # kEConstraintNone (no extra constraint), kEConstraintArea (enforce preservation of area)
        self.densitymode= ROOT.TUnfoldDensity.kDensityModeBinWidth
        # kDensityModeNone (no scale factors, matrix L is similar to unity matrix), kDensityModeBinWidth (scale factors from multidimensional bin width), kDensityModeUser (scale factors from user function in TUnfoldBinning), kDensityModeBinWidthAndUser (scale factors from multidimensional bin width and user function)


        # First do it with no regularization
        label='noreg'
        self.set_unfolding(key)
        self.do_scan()
        self.print_unfolding_results(key, label)
     


        # Now add simple regularization on the amplitude
        self.logTauX=ROOT.TSpline3() # TSpline*
        self.logTauY=ROOT.TSpline3() # TSpline*
        self.lCurve=ROOT.TGraph(0) # TGraph*
        self.logTauCurvature=ROOT.TSpline3() # TSpline*
        self.regmode=ROOT.TUnfold.kRegModeCurvature
        label='regamp'
        self.set_unfolding(key)
        self.do_scan()
        self.print_unfolding_results(key, label)

     
    def set_unfolding(self, key):

        if   key == 'nom':
            self.unfold = ROOT.TUnfoldDensity(self.response_nom, self.histmap, self.regmode, self.constraint, self.densitymode)
        elif key == 'alt':
            self.unfold = ROOT.TUnfoldDensity(self.response_alt, self.histmap, self.regmode, self.constraint, self.densitymode)
        elif key == 'inc':
            self.unfold = ROOT.TUnfoldDensity(self.response_inc, self.histmap, self.regmode, self.constraint, self.densitymode)
        else:
            print('ERROR: the response matrix you asked for (%s) does not exist' % key)
        # Check if the input data points are enough to constrain the unfolding process
        check = self.unfold.SetInput(self.data)
        if check>=10000:
            print('TUnfoldDensity error %d! Unfolding result may be wrong (not enough data to constrain the unfolding process)' % check)
        # Now I should do subtraction using the class. I assign a 10% error on each background. This will have to be set automatically
        scale_bgr=1.0
        dscale_bgr=0.1
        for iBkg in self.bkg:
            self.unfold.SubtractBackground(iBkg,iBkg.GetName(),scale_bgr,dscale_bgr);
        # Add systematic error
        # unfold.AddSysError(histUnfoldMatrixSys,"signalshape_SYS", TUnfold::kHistMapOutputHoriz, TUnfoldSys::kSysErrModeMatrix)

            

    def do_scan(self):
        # Scan the L-curve and find the best point
        
        # Set verbosity
        oldinfo=ROOT.gErrorIgnoreLevel
        if self.verbose:
            ROOT.gErrorIgnoreLevel=kInfo

        # Scan the parameter tau, finding the kink in the L-curve. Finally, do the unfolding for the best choice of tau
        if self.regmode == ROOT.TUnfold.kRegModeNone:
            self.unfold.DoUnfold(0.0)
            self.iBest=0.0
        else:
            self.iBest=self.unfold.ScanLcurve(self.nScan, self.tauMin, self.tauMax, self.lCurve, self.logTauX, self.logTauY)
            
        # Reset verbosity
        if self.verbose:
            ROOT.gErrorIgnoreLevel=oldInfo

        # Here do something for the error
        ### 

    def print_unfolding_results(self, key, label):
        # Print results
        print('Best tau: %d' % self.unfold.GetTau())
        print('chi^2: %d+%d/%d' %(self.unfold.GetChi2A(), self.unfold.GetChi2L(), self.unfold.GetNdf() ) )
        print('chi^2(syst): %d' % self.unfold.GetChi2Sys())
        
        print('ibest: %d, type %s' % ( self.iBest, type(self.iBest)))
        # Visualize best choice of tau

        bestLcurve = None
        bestLogTauLogChi2 = None
        if self.regmode is not ROOT.TUnfold.kRegModeNone:
            t=ROOT.Double(0)
            x=ROOT.Double(0)
            y=ROOT.Double(0)
            self.logTauX.GetKnot(self.iBest, t, x)
            self.logTauY.GetKnot(self.iBest, t, y)
            vt =array('d')
            vx =array('d')
            vy =array('d')
            vt.append(t)
            vx.append(x)
            vy.append(y)
            bestLcurve = ROOT.TGraph(1, vx, vy)
            bestLogTauLogChi2 = ROOT.TGraph(1, vt, vx);
        
        # Retrieve results as histograms
        histMunfold=self.unfold.GetOutput('%s(unfold,stat+bgrerr)' %self.var) # Unfolded result
        histMdetFold=self.unfold.GetFoldedOutput('FoldedBack') # Unfolding result, folded back
        histEmatStat=self.unfold.GetEmatrixInput('Error matrix (stat errors only)') # Error matrix (stat errors only)
        histEmatTotal=self.unfold.GetEmatrixTotal('Error matrix (total errors)') # Total error matrix. Migration matrix uncorrelated and correlated syst errors added in quadrature to the data statistical errors
        
        
        #TH1 *histDetNormBgr1=unfold.GetBackground("bgr1 normalized",
        #                                          "background1");
        histDetNormBgrTotal=self.unfold.GetBackground("Total background (normalized)")

        nDet=self.response_nom.GetNbinsX()
        nGen=self.response_nom.GetNbinsY()
        xminDet=self.response_nom.GetXaxis().GetBinLowEdge(1)
        xmaxDet=self.response_nom.GetXaxis().GetBinUpEdge(self.response_nom.GetNbinsX())
        xminGen=self.response_nom.GetYaxis().GetBinLowEdge(1)
        xmaxGen=self.response_nom.GetYaxis().GetBinUpEdge(self.response_nom.GetNbinsY())
        #histUnfoldTotal = ROOT.TH1D('%s(unfold,toterr)' % self.var,';%s(gen)' % self.var, nGen, xminGen, xmaxGen) # Unfolded data histogram with total errors
        histUnfoldTotal = copy.deepcopy(ROOT.TH1D(self.dataTruth_nom)) # Unfolded data histogram with total errors
        histUnfoldTotal.Reset('ICE')
        histUnfoldTotal.SetName('%s(unfold,toterr)' % self.var)
        histUnfoldStat = copy.deepcopy(ROOT.TH1D(self.dataTruth_nom)) # Unfolded data histogram with statistical errors only
        histUnfoldStat.Reset('ICE')
        histUnfoldStat.SetName('%s(unfold,staterr)' % self.var)
        for ibin in range(0,nGen+2):
            c=histMunfold.GetBinContent(ibin)
            histUnfoldStat.SetBinContent(ibin, c)
            histUnfoldStat.SetBinError(ibin, ROOT.TMath.Sqrt(histEmatStat.GetBinContent(ibin,ibin)))
            histUnfoldTotal.SetBinContent(ibin, histMunfold.GetBinContent(ibin))
            histUnfoldTotal.SetBinError(ibin, ROOT.TMath.Sqrt(histEmatTotal.GetBinContent(ibin,ibin)))


        print('Now get global correlation coefficients')
        # get global correlation coefficients
        # for this calculation one has to specify whether the
        # underflow/overflow bins are included or not
        # default: include all bins
        # here: exclude underflow and overflow bins

        #self.gHistInvEMatrix=copy.deepcopy(self.response_nom)
        #self.gHistInvEMatrix.SetName('gHistInvEMatrix')
        #self.gHistInvEMatrix.Print()
        #histRhoi=self.unfold.GetRhoItotal('rho_I',
        #                                  '', # use default title
        #                                  '', # all distributions
        #                                  "*[UO]", # discard underflow and overflow bins on all axes
        #                                  ROOT.kTRUE, # use original binning
        #                                  self.gHistInvEMatrix # store inverse of error matrix
        #                                  )

        # other try self.gHistInvJEMatrix=self.unfold.GetRhoIJtotal('rho_I',
        # other try                                     '', # use default title
        # other try                                     '', # all distributions
        # other try                                     "*[UO]", # discard underflow and overflow bins on all axes
        # other try                                     ROOT.kTRUE, # use original binning
        # other try                                     )
        #  
        #  #======================================================================
        #  # fit Breit-Wigner shape to unfolded data, using the full error matrix
        #  # here we use a "user" chi**2 function to take into account
        #  # the full covariance matrix
        #  
        #  #gFitter=TVirtualFitter::Fitter(histMunfold)
        #  #gFitter.SetFCN(chisquare_corr)
        #  
        #  bw=TF1("bw",bw_func,xminGen,xmaxGen,3)
        #  bw.SetParameter(0,1000.)
        #  bw.SetParameter(1,3.8)
        #  bw.SetParameter(2,0.2)
        #  
        #  # for (wrong!) fitting without correlations, drop the option "U"
        #  # here.
        #  histMunfold.Fit(bw,"UE")

        # =====================================================================
        #  plot some histograms
        output=ROOT.TCanvas('out', 'out', 2000, 2000)
        output.Divide(4,2)

        # Show the matrix which connects input and output
        # There are overflow bins at the bottom, not shown in the plot
        # These contain the background shape.
        # The overflow bins to the left and right contain
        # events which are not reconstructed. These are necessary for proper MC
        # normalisation
        #output.cd(1)
        ##histMdetGenMC.Draw("BOX")

        output.cd(1)
        # Data, MC prediction, background
        self.data.SetMinimum(0.0)
        self.data.Draw("E")
        self.mc.SetMinimum(0.0)
        self.mc.SetLineColor(ROOT.kBlue)
        self.mc.SetLineWidth(3)
        bkgStacked=copy.deepcopy(histDetNormBgrTotal)
        bkgStacked.Add(self.mc)
        bkgStacked.SetLineColor(ROOT.kRed)
        bkgStacked.SetLineWidth(3)
        #histDetNormBgr1.SetLineColor(kCyan);
        self.mc.Draw("SAME HIST")
        #histDetNormBgr1.Draw("SAME HIST");
        bkgStacked.Draw("SAME HIST")

        leg_1 = ROOT.TLegend(0.5,0.7,0.9,0.9)
        leg_1.SetTextSize(0.06)
        leg_1.AddEntry(self.data, 'Data', 'p')
        leg_1.AddEntry(self.mc, 'Exp. signal', 'la')
        leg_1.AddEntry(bkgStacked, 'Exp. signal+background', 'l')
        leg_1.Draw()

        print(self.data.GetNbinsX())
        print(self.mc.GetNbinsX())
        print(histDetNormBgrTotal.GetNbinsX())
        
        # draw generator-level distribution:
        #   data (red) [for real data this is not available]
        #   MC input (black) [with completely wrong peak position and shape]
        #   unfolded data (blue)
        output.cd(2)
        # Unfolded data with total error
        histUnfoldTotal.SetMarkerColor(ROOT.kBlue)
        histUnfoldTotal.SetLineColor(ROOT.kBlue)
        histUnfoldTotal.SetLineWidth(1)
        histUnfoldTotal.SetMarkerStyle(ROOT.kFullCircle)
        # Outer error: total error
        histUnfoldTotal.Draw('PE')
        # Middle error: stat+bgr
        histMunfold.SetLineColor(ROOT.kBlue+2)
        histMunfold.SetLineWidth(2)
        histMunfold.Draw('SAME E1')
        # Inner error: stat only
        histUnfoldStat.SetLineColor(ROOT.kBlue+4)
        histUnfoldStat.SetLineWidth(3)
        histUnfoldStat.Draw('SAME E1')
        # Data truth
        self.dataTruth_nom.SetLineColor(ROOT.kRed+1)
        self.dataTruth_nom.SetLineWidth(2)
        self.dataTruth_nom.Draw("SAME E HIST")
        ###histDensityGenData.SetLineColor(kRed)
        ##histDensityGenData.Draw("SAME")
        ##histDensityGenMC.Draw("SAME HIST")
        leg_2 = ROOT.TLegend(0.5,0.7,0.9,0.9)
        leg_2.SetTextSize(0.06)
        leg_2.AddEntry(histUnfoldTotal, 'Unfolded data', 'pel')
        leg_2.AddEntry(self.dataTruth_nom, 'Truth', 'la')
        leg_2.Draw()
        
        # show detector level distributions
        #    data (red)
        #    MC (black) [with completely wrong peak position and shape]
        #    unfolded data (blue)
        output.cd(3)
        # MC folded back
        histMdetFold.SetLineColor(ROOT.kBlack-3)
        histMdetFold.SetLineWidth(2)
        histMdetFold.Draw()
        # Original folded MC
        #self.mc.Draw("SAME HIST")
        bkgStacked.Draw("SAME HIST")
        #histInput=self.unfold.GetInput("Minput",";mass(det)")
        #histInput.SetLineColor(ROOT.kRed)
        #histInput.SetLineWidth(3)
        #histInput.Draw("SAME")
        # Data
        self.data.Draw('PESAME')
        leg_3 = ROOT.TLegend(0.5,0.7,0.9,0.9)
        leg_3.SetTextSize(0.06)
        leg_3.AddEntry(self.data, 'Data', 'l')
        leg_3.AddEntry(histMdetFold, 'MC folded back', 'l')
        leg_3.AddEntry(bkgStacked, 'Exp. signal+background', 'l')
        #leg_3.AddEntry(histInput, 'Input', 'la')
        leg_3.Draw()


        output.cd(4) 
        # show correlation coefficients
        # #histRhoi.Draw()
        # Data-bkg by hand
        subdata=self.sub_bkg_by_hand()
        subdata.SetLineColor(ROOT.kBlack-3)
        subdata.SetLineWidth(3)
        subdata.Draw('histsame')
        self.mc.Draw('SAME HIST')
        histInput=self.unfold.GetInput("Minput",";mass(det)")
        histInput.SetLineColor(ROOT.kRed)
        histInput.SetLineWidth(3)
        histInput.Draw("SAME")
        leg_4 = ROOT.TLegend(0.5,0.7,0.9,0.9)
        leg_4.SetTextSize(0.06)
        leg_4.AddEntry(self.mc, 'Exp. signal', 'pe')
        leg_4.AddEntry(subdata, 'Data-bkg by hand', 'la')
        leg_4.AddEntry(histInput, 'Data-bkg by tool', 'la')
        leg_4.Draw()

        if self.regmode is not ROOT.TUnfold.kRegModeNone:

            # from v610# # Show logTauCurvature (should be peaked similarly to a Gaussian)
            # from v610# output.cd(4)
            # from v610# self.logTauCurvature.SetLineWidth(3)
            # from v610# self.logTauCurvature.Draw()
            # show tau as a function of chi**2
            output.cd(5)
            self.logTauX.Draw()
            bestLogTauLogChi2.SetMarkerColor(ROOT.kRed)
            bestLogTauLogChi2.SetMarkerStyle(ROOT.kFullSquare)
            bestLogTauLogChi2.SetMarkerSize(2)
            bestLogTauLogChi2.Draw("P")
            # show the L curve
            output.cd(6)
            self.lCurve.GetXaxis().SetTitle('log#chi_{A}^{2}')
            self.lCurve.GetYaxis().SetTitle('log#chi_{L}^{2}')
            self.lCurve.Draw("AL")
            bestLcurve.SetMarkerColor(ROOT.kRed)
            bestLcurve.SetMarkerStyle(ROOT.kFullSquare)
            bestLcurve.SetMarkerSize(2)
            bestLcurve.Draw("P")
            
        output.SaveAs(os.path.join(self.outputDir, '2_unfold_%s_%s_%s.png' % (label, key, self.var)))

        # # Individual saving.
        # self.print_histo(histMunfold, key, label)
        # self.print_histo(histMdetFold, key, label)
        # self.print_histo(histEmatStat, key, label, 'colz')
        # self.print_histo(histEmatTotal, key, label, 'colz')
        # self.print_histo(histUnfoldTotal, key, label)

    def sub_bkg_by_hand(self):
        subdata=copy.deepcopy(ROOT.TH1D(self.data))
        for i in range(1,len(self.bkg)):
            subdata.Add(self.bkg[i], -1)
        return subdata



### End class Unfolder
def main(args): 
    print('start')
    #for var in ['Zpt', 'ZconePt', 'nJet30']: # Must build correct gen matrix for nJet30 (need friend trees). Also, don't study conePt for now
    for var in ['Zpt']:
        u = Unfolder(args,var)
        u.print_responses()
        u.study_responses()
        u.do_unfolding('nom')
        u.do_unfolding('alt')
        u.do_unfolding('inc')

### End main

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--inputDir',     help='Input directory', default=None)
    parser.add_argument('-o', '--outputDir',    help='Output directory', default='./')
    parser.add_argument('-c', '--combineInput', help='Data and postfit from combine output', default=None)
    parser.add_argument('-d', '--data',         help='File containing data histogram', default=None)
    parser.add_argument('-m', '--mc',           help='File containing mc reco histogram', default=None)
    parser.add_argument('-g', '--gen',          help='File containing gen info for matrix', default=None)
    parser.add_argument('-l', '--lepCat',       help='Lepton multiplicity (1 or 2)', default=1, type=int)
    parser.add_argument('-e', '--epochs',       help='Number of epochs', default=100, type=int)
    parser.add_argument('-s', '--splitMode',    help='Split mode (input or random)', default='input')
    parser.add_argument('-v', '--verbose',      help='Verbose printing of the L-curve scan', action='store_true')
    parser.add_argument('-r', '--responseAsPdf', help='Print response matrix as pdf', action='store_true') 
    args = parser.parse_args()
    # execute only if run as a script
    ROOT.gROOT.SetBatch()
    main(args)
